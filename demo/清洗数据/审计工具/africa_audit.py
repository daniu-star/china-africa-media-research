# -*- coding: utf-8 -*-
"""Africa-China news corpus: local, privacy-preserving audit.

Usage:
  py -3 africa_audit.py --input "C:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\清洗数据"

Produces aggregated JSON/Markdown plus a ZIP. Does NOT upload any data.
Requires only Python 3.9+ for CSV/TSV/JSONL; optional openpyxl/pyarrow for XLSX/Parquet,
optional numpy/pandas/statsmodels for conditional descriptive OLS/mediation checks.
"""
import argparse
import collections
import csv
import datetime
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
import re
import statistics
import sys
import time
import traceback
import unicodedata
import zipfile

VERSION = '1.2.0'
EXPECTED_N = 22646
EXPECTED_REGION = {'东非': 72.26, '中非': 21.88, '南非': 3.49, '北非': 1.42, '西非': 0.95}
READABLE = ('.csv','.tsv','.txt','.json','.jsonl','.ndjson','.xlsx','.parquet','.csv.gz','.tsv.gz','.json.gz','.jsonl.gz','.ndjson.gz')
SYNONYMS = {
 'text':['content','article_text','text','full_text','body','news_content','cleaned_text','clean_text','新闻内容','正文','报道全文','内容','清洗文本','文本'],
 'title':['title','headline','news_title','标题','新闻标题'],
 'url':['url','link','article_url','news_url','原文链接','新闻链接','网址'],
 'article_id':['article_id','news_id','doc_id','id','文章id','报道id','新闻id'],
 'date':['publish_date','published_at','publication_date','pub_date','published_date','date','publication_time','time','发布时间','发布日期','发表日期','时间'],
 'year':['year','pub_year','publish_year','time_index','年份','发布年份'],
 'region':['region','area','africa_region','source_region','region_name','报道来源区域','来源区域','非洲区域','地区','区域'],
 'outlet':['media','outlet','news_site','website','source','source_name','media_name','publisher','site_name','domain','媒体','媒体名称','新闻网站','来源媒体','网站'],
 'country':['country','country_name','source_country','国家','来源国家','报道国家','所在国家'],
 'identity':['community_identity','identity_score','community_identification','identification','identity','recognition_score','community_recognition','共同体认同度','共同体认同','认同度','认同得分','共同体认知'],
 'development':['development_demand_pca','development_demand','development_need','development_perception','dev_demand','development_score','发展需求感知强度','发展需求感知','发展需求','发展感知'],
 'cooperation':['cooperation_willingness','cooperation_intention','cooperation_score','collaboration_willingness','合作意愿','合作期待','合作强度'],
 'emotion':['emotion_intensity','emotion_strength','sentiment_intensity','affective_intensity','overall_emotion','emotion_score','情感强度','情绪强度'],
 'sentiment':['normalized_sentiment','sentiment_value','sentiment_score','sentiment_polarity','sentiment','情感倾向','情感值','情感极性'],
 'semantic':['semantic_similarity','semantic_relevance','discourse_proximity','cosine_similarity','semantic_score','语义关联度','语义相似度','话语接近度','话语一致性'],
 'word_count':['total_words_count','word_count','words_count','total_words','article_length','text_length','字数','文章字数','词数','文章长度'],
 'cluster':['cluster_label','cluster','kmeans_cluster','group_label','聚类','簇群','类别编号','群体类型'],
 'trust':['trust','trust_score','信任'],
 'expectation':['expectation','anticipation','hope','expected','期待','期望'],
 'joy':['joy','happiness','喜悦'],
 'pride':['pride','自豪'],
 'worry':['worry','concern','anxiety','担忧','忧虑'],
 'confusion':['confusion','puzzlement','困惑'],
 'anger':['anger','愤怒'],
 'sadness':['sadness','悲伤'],
 'fear':['fear','恐惧'],
 'surprise':['surprise','惊讶'],
 'human_label':['human_label','manual_label','gold_label','annotator_label','人工标签','人工编码'],
 'model_label':['predicted_label','model_label','bert_label','prediction','模型标签','机器标签'],
 'pca_term_weight':['development_term_weight','dev_term_weight','发展术语权重'],
 'pca_keyword_count':['development_keyword_count','dev_keyword_count','发展关键词计数','发展关键词数量'],
 'pca_keyword_density':['development_keyword_density','dev_keyword_density','发展关键词密度'],
}
MAIN_NUMERIC = ('identity','development','cooperation','emotion','sentiment','semantic','word_count',
                'trust','expectation','joy','pride','worry','confusion','anger','sadness','fear','surprise',
                'pca_term_weight','pca_keyword_count','pca_keyword_density')
CORE = ('identity','development','cooperation','emotion','sentiment','semantic')
MANDATORY = ('identity','development','cooperation','emotion','region','outlet','year')
MISSING = {'', 'na','n/a','nan','null','none','missing','未知','不详','无','--','-'}

def norm(s):
    return ''.join(ch for ch in unicodedata.normalize('NFKC',str(s)).strip().lower() if ch.isalnum())

NAMES = {role:[norm(s) for s in vals] for role,vals in SYNONYMS.items()}
def detect_columns(columns, overrides=None):
    normalized = {c:norm(c) for c in columns}
    mapping, proposed, conflicts = {}, {}, []
    for role, synonyms in NAMES.items():
        if overrides and overrides.get(role) in columns:
            mapping[role] = overrides[role]; proposed[role] = [overrides[role]]; continue
        scored=[]
        for col, nc in normalized.items():
            if not nc: continue
            exact = [i for i,s in enumerate(synonyms) if nc == s]
            if exact: scored.append((1000-exact[0],col)); continue
            # Match bounded names and safely allow suffixes such as _centered / _norm / _v2.
            approx = [s for s in synonyms if len(s)>=5 and (nc.startswith(s+'centered') or nc.startswith(s+'normalized') or nc.endswith(s+'score'))]
            if approx: scored.append((600+max(map(len,approx)),col))
        scored.sort(key=lambda p:(-p[0],str(p[1])))
        proposed[role] = [c for _,c in scored[:5]]
        if scored and (len(scored)==1 or scored[0][0] > scored[1][0]):
            mapping[role] = scored[0][1]
    inverse=collections.defaultdict(list)
    for role,col in mapping.items(): inverse[col].append(role)
    for col,roles in inverse.items():
        if len(roles)>1:
            conflicts.append({'column':col,'roles':roles})
            for role in roles: mapping.pop(role,None)
    return mapping,proposed,conflicts

def is_missing(v):
    if v is None:return True
    if isinstance(v,str):return v.strip().lower() in MISSING
    try:return math.isnan(v)
    except (ValueError,TypeError):return False

def number(v):
    if is_missing(v):return None
    try:
        if isinstance(v,str):
            v=v.strip().replace(',','')
            if v.endswith('%'):v=float(v[:-1])/100.0
        r=float(v)
        return r if math.isfinite(r) else None
    except (ValueError, TypeError, OverflowError):return None

def extract_year(v):
    if is_missing(v):return None
    if isinstance(v,datetime.datetime):return v.year
    if isinstance(v,datetime.date):return v.year
    s=str(v).strip()
    match=re.search(r'(?<!\d)(19\d{2}|20\d{2}|2100)(?!\d)',s)
    if match:return int(match.group(1))
    n=number(v)
    if n is not None and n.is_integer() and 1990<=n<=2100:return int(n)
    return None

def region_norm(v):
    if is_missing(v):return None
    val=str(v).strip(); low=val.lower().replace('-',' ').replace('_',' ')
    if any(s in low for s in ['east africa','eastern africa','东非']):return '东非'
    if any(s in low for s in ['central africa','middle africa','中非']):return '中非'
    if any(s in low for s in ['southern africa','south africa','南非']):return '南非'
    if any(s in low for s in ['north africa','northern africa','北非']):return '北非'
    if any(s in low for s in ['west africa','western africa','西非']):return '西非'
    return '未识别区域'

def read_text_open(path, enc, comp=False):
    return gzip.open(path,'rt',encoding=enc,newline='',errors='replace') if comp else open(path,'r',encoding=enc,newline='',errors='replace')

def detect_encoding(path):
    opener=gzip.open if path.name.lower().endswith('.gz') else open
    with opener(path,'rb') as f:head=f.read(32768)
    if head.startswith(b'\xef\xbb\xbf'):return 'utf-8-sig'
    if head.startswith(b'\xff\xfe') or head.startswith(b'\xfe\xff'):return 'utf-16'
    for e in ('utf-8','gb18030'):
        try:head.decode(e);return e
        except UnicodeDecodeError:pass
    return 'latin-1'

class _JsonIncrementalReader:
    """Read a large JSON document a value at a time; memory ~ largest element."""
    def __init__(self, f, chunk=262144):
        self.f=f;self.chunk=chunk;self.buf='';self.pos=0;self.eof=False
        self.decoder=json.JSONDecoder()
        self.depth_limit=16
    def _refill(self):
        if self.pos>0:
            self.buf=self.buf[self.pos:];self.pos=0
        more=self.f.read(self.chunk)
        if more:self.buf+=more
        else:self.eof=True
    def peek(self):
        while True:
            while self.pos<len(self.buf) and self.buf[self.pos].isspace():self.pos+=1
            if self.pos<len(self.buf):return self.buf[self.pos]
            if self.eof:return None
            self._refill()
    def eat(self,c):
        actual=self.peek()
        if actual!=c:raise ValueError('Malformed JSON: expected '+repr(c)+', found '+repr(actual))
        self.pos+=1
    def value(self):
        if self.peek() is None:raise ValueError('Unexpected end of JSON')
        while True:
            try:out,end=self.decoder.raw_decode(self.buf,self.pos)
            except json.JSONDecodeError as e:
                if self.eof:raise ValueError('Invalid JSON near position '+str(self.pos)+': '+str(e))
                self._refill();continue
            # Ensure that an unfinished numeric literal cannot be parsed prematurely.
            if end>=len(self.buf) and not self.eof:
                self._refill();continue
            if end<len(self.buf) and self.buf[end] not in ',]}: \t\r\n':
                if self.eof:raise ValueError('JSON token not separated by delimiter')
                self._refill();continue
            self.pos=end
            return out

def _iter_records_from_json_stream(reader,depth=0,in_array=False):
    """Supports root list, wrapper object {data:[...]}, nested wrappers and id->record mappings.

    Unknown nested metadata is ignored; raw article text is never emitted to report.
    """
    if depth>reader.depth_limit:raise ValueError('JSON nesting exceeds safe limit')
    tag=reader.peek()
    if tag=='[':
        reader.eat('[')
        if reader.peek()==']':reader.eat(']');return
        while True:
            yield from _iter_records_from_json_stream(reader,depth+1,True)
            nxt=reader.peek()
            if nxt==']':reader.eat(']');break
            reader.eat(',')
    elif tag=='{':
        reader.eat('{');scalar={};nested=False
        if reader.peek()=='}':reader.eat('}');return
        while True:
            key=reader.value()
            if not isinstance(key,str):raise ValueError('JSON object key must be string')
            reader.eat(':')
            nextc=reader.peek()
            if nextc in ('[','{'):
                nested=True
                yield from _iter_records_from_json_stream(reader,depth+1,False)
            else:
                val=reader.value()
                # Keep only normal scalar feature columns; do not accumulate arrays.
                scalar[key]=val
            nxt=reader.peek()
            if nxt=='}':reader.eat('}');break
            reader.eat(',')
        mapped=detect_columns(list(scalar))[0] if scalar else {}
        evidence=('title' in mapped or 'text' in mapped or len(set(mapped).intersection(('date','year','identity','development','cooperation','outlet','region','article_id','url')))>=2)
        if scalar and (evidence or (in_array and len(scalar)>=2 and not nested)):
            yield scalar
    else:
        reader.value()

def json_document_rows(path,enc,compressed):
    with read_text_open(path,enc,compressed) as stream:
        reader=_JsonIncrementalReader(stream)
        for row in _iter_records_from_json_stream(reader):
            yield row
        if reader.peek() is not None:
            raise ValueError('Unexpected data after end of JSON document')

def open_rows(path):
    lower=path.name.lower(); compressed=lower.endswith('.gz')
    suffix=lower[:-3] if compressed else lower
    if suffix.endswith(('.csv','.tsv','.txt')):
        enc=detect_encoding(path)
        with read_text_open(path,enc,compressed) as f:
            sample=f.read(8192); f.seek(0) if not compressed else None
        # Need a fresh handle: gzip text streams are seekable, but reopen always.
        default_delim='\t' if suffix.endswith('.tsv') else ','
        try:dialect=csv.Sniffer().sniff(sample,delimiters=',\t;|'); delim=dialect.delimiter
        except csv.Error:delim=default_delim
        if suffix.endswith('.tsv'):delim='\t'
        with read_text_open(path,enc,compressed) as f:
            reader=csv.DictReader(f,delimiter=delim)
            if not reader.fieldnames:raise ValueError('CSV/TSV has no header')
            columns=[str(c).strip('\ufeff') for c in reader.fieldnames if c is not None]
            yield ('HEADER',columns,{'encoding':enc,'delimiter':repr(delim)})
            for row in reader:
                if None in row:row.pop(None,None)
                yield ('ROW',row,None)
    elif suffix.endswith('.json'):
        enc=detect_encoding(path)
        header=None;first=[];count=0
        # Discover fields across the first 50 records; stream remaining records.
        for obj in json_document_rows(path,enc,compressed):
            if not isinstance(obj,dict):continue
            if header is None:
                first.append(obj)
                if len(first)<50:continue
                header=list(dict.fromkeys(k for row in first for k in row.keys()))
                yield ('HEADER',header,{'encoding':enc,'format':'json-streaming'})
                for row in first:yield ('ROW',row,None)
                first.clear()
            else:
                yield ('ROW',obj,None)
            count+=1
        if header is None:
            header=list(dict.fromkeys(k for row in first for k in row.keys()))
            yield ('HEADER',header,{'encoding':enc,'format':'json-streaming'})
            for row in first:yield ('ROW',row,None)
    elif suffix.endswith(('.jsonl','.ndjson')):
        enc=detect_encoding(path)
        with read_text_open(path,enc,compressed) as f:
            header=None
            for line_no,line in enumerate(f,1):
                if not line.strip():continue
                try:obj=json.loads(line)
                except json.JSONDecodeError as e:
                    yield ('ERROR',str(e)[:140]+' at line '+str(line_no),None);continue
                if not isinstance(obj,dict):
                    yield ('ERROR','not an object at line '+str(line_no),None);continue
                if header is None:
                    header=list(obj.keys())
                    yield ('HEADER',header,{'encoding':enc})
                yield ('ROW',obj,None)
            if header is None:yield ('HEADER',[],{'encoding':enc})
    elif suffix.endswith('.xlsx'):
        try:import openpyxl
        except ImportError:raise RuntimeError('openpyxl missing: pip install openpyxl')
        wb=openpyxl.load_workbook(str(path),read_only=True,data_only=True)
        try:
            for sheet in wb:
                iterator=sheet.iter_rows(values_only=True)
                first=next(iterator,None)
                if not first:continue
                header=[str(c) if c is not None else 'column'+str(i) for i,c in enumerate(first)]
                yield ('HEADER',header,{'sheet':sheet.title})
                for cells in iterator:
                    yield ('ROW',dict(zip(header,cells)),None)
        finally:wb.close()
    elif suffix.endswith('.parquet'):
        try:import pyarrow.parquet as pq
        except ImportError:raise RuntimeError('pyarrow missing: pip install pyarrow')
        pqf=pq.ParquetFile(path)
        cols=list(pqf.schema_arrow.names)
        yield ('HEADER',cols,{'format':'parquet'})
        for batch in pqf.iter_batches(batch_size=1000):
            d=batch.to_pydict()
            for i in range(batch.num_rows):yield ('ROW',{col:d[col][i] for col in cols},None)
    else:raise RuntimeError('unsupported extension')

class SampleStat:
    def __init__(self,seed=17,cap=10000):
        self.n=0;self.zero=0;self.minimum=None;self.maximum=None;self.s=0.;self.s2=0.;self.samples=[];self.rng=random.Random(seed);self.cap=cap
    def add(self,v):
        self.n+=1;self.s+=v;self.s2+=v*v
        self.minimum=v if self.minimum is None else min(self.minimum,v)
        self.maximum=v if self.maximum is None else max(self.maximum,v)
        self.zero+=int(v==0)
        if len(self.samples)<self.cap:self.samples.append(v)
        else:
            j=self.rng.randrange(self.n)
            if j<self.cap:self.samples[j]=v
    def result(self):
        if not self.n:return {'n':0}
        mean=self.s/self.n;std=math.sqrt(max(0.,self.s2/self.n-mean*mean))
        ss=sorted(self.samples)
        def p(q):return round(ss[min(len(ss)-1,max(0,round(q*(len(ss)-1))))],5)
        out={'n':self.n,'mean':round(mean,6),'std':round(std,6),'min':round(self.minimum,6),'max':round(self.maximum,6),'zero_pct':round(self.zero/self.n*100,3), 'p01':p(.01),'p25':p(.25),'median':p(.5),'p75':p(.75),'p99':p(.99)}
        if len(ss)>2 and std>1e-12:
            m3=sum(((x-mean)/std)**3 for x in ss)/len(ss)
            m4=sum(((x-mean)/std)**4 for x in ss)/len(ss)-3
            out.update({'skew_approx':round(m3,4),'excess_kurtosis_approx':round(m4,4),'quantile_sample_n':len(ss)})
        return out

class PairStat:
    def __init__(self):self.n=0;self.sx=self.sy=self.sxx=self.syy=self.sxy=0.
    def add(self,a,b):
        self.n+=1;self.sx+=a;self.sy+=b;self.sxx+=a*a;self.syy+=b*b;self.sxy+=a*b
    def result(self):
        n=self.n;den=(n*self.sxx-self.sx*self.sx)*(n*self.syy-self.sy*self.sy)
        r=(n*self.sxy-self.sx*self.sy)/math.sqrt(den) if n>2 and den>1e-10 else None
        return {'n':n,'pearson_r':round(max(-1,min(1,r)),6) if r is not None else None}

class Family:
    def __init__(self,columns,mapping,sample_cap,seed):
        self.columns=columns;self.mapping=mapping;self.files=[];self.rows=0;self.missing=collections.Counter();self.invalid_num=collections.Counter()
        self.region=collections.Counter();self.outlet=collections.Counter();self.years=collections.Counter()
        self.stats={k:SampleStat(seed+i*101) for i,k in enumerate(MAIN_NUMERIC)}
        self.pairs={x:PairStat() for x in [('identity','emotion'),('identity','sentiment'),('identity','semantic'),('development','emotion'),('emotion','sentiment'),('worry','confusion'),('trust','expectation'),('development','identity'),('cooperation','identity')]}
        self.dup={'title':0,'text':0,'article_id':0};self.seen={k:set() for k in self.dup};self.max_dedup=1000000;self.dedup_partial=set()
        self.bad_year=0;self.before2000=0;self.before2013=0;self.after2025=0;self.empty_text=0
        self.out_of_range=collections.Counter()
        self.sample=[];self.sample_seen=0;self.sample_cap=sample_cap;self.rng=random.Random(seed)
        self.formula_count=0;self.formula_sums={'raw':0.,'norm':0.};self.formula_near={'raw':0,'norm':0}
        self.label_pairs=collections.Counter();self.anomaly_issues=[]
    def update(self,row):
        self.rows+=1
        raw=lambda role:row.get(self.mapping[role]) if role in self.mapping else None
        for role in self.mapping:
            if is_missing(raw(role)):self.missing[role]+=1
        year=extract_year(raw('year') if 'year' in self.mapping else raw('date'))
        if year is not None:
            self.years[str(year)]+=1
            if year<2000:self.before2000+=1
            if year<2013:self.before2013+=1
            if year>2025:self.after2025+=1
        else:self.bad_year+=1
        r=region_norm(raw('region'))
        if r:self.region[r]+=1
        outlet=raw('outlet')
        if not is_missing(outlet):self.outlet[str(outlet).strip()[:80]]+=1
        vals={}
        for role in MAIN_NUMERIC:
            if role not in self.mapping:continue
            v=raw(role);num=number(v)
            if num is None and not is_missing(v):self.invalid_num[role]+=1
            if num is not None:
                vals[role]=num;self.stats[role].add(num)
                if role in ('identity','cooperation','semantic') and not 0<=num<=1:self.out_of_range[role]+=1
                if role in ('emotion','sentiment') and not -1<=num<=1:self.out_of_range[role]+=1
                if role=='word_count' and num<0:self.out_of_range[role]+=1
        for (a,b),tracker in self.pairs.items():
            if a in vals and b in vals:tracker.add(vals[a],vals[b])
        if all(s in vals for s in ('identity','sentiment','semantic')):
            self.formula_count+=1
            y,s,sem=vals['identity'],vals['sentiment'],vals['semantic']
            for name,est in [('raw',(s+sem)/2),('norm',((s+1)/2+sem)/2)]:
                diff=abs(y-est);self.formula_sums[name]+=diff;self.formula_near[name]+=int(diff<.01)
        if 'text' in self.mapping:
            txt=raw('text')
            if is_missing(txt):self.empty_text+=1
        for key in self.dup:
            if key not in self.mapping:continue
            rawval=raw(key)
            if is_missing(rawval):continue
            v=str(rawval).strip()
            if key!='article_id':v=re.sub(r'\s+',' ',v).casefold()
            digest=hashlib.blake2b(v.encode('utf-8',errors='replace'),digest_size=12).digest()
            seen=self.seen[key]
            if digest in seen:self.dup[key]+=1
            elif len(seen)<self.max_dedup:seen.add(digest)
            else:self.dedup_partial.add(key)
        if 'human_label' in self.mapping and 'model_label' in self.mapping:
            h,m=raw('human_label'),raw('model_label')
            if not is_missing(h) and not is_missing(m):self.label_pairs[(str(h)[:60],str(m)[:60])]+=1
        # Small analysis-only subset, no article text, URLs, titles, IDs or raw metadata.
        if {'identity','development','emotion'}.issubset(vals):
            sm={k:vals.get(k) for k in MAIN_NUMERIC if k in vals}
            sm.update({'year':year,'outlet':str(outlet)[:80] if not is_missing(outlet) else None,'region':r,
                       'cluster':str(raw('cluster'))[:60] if not is_missing(raw('cluster')) else None})
            self.sample_seen+=1
            if len(self.sample)<self.sample_cap:self.sample.append(sm)
            else:
                j=self.rng.randrange(self.sample_seen)
                if j<self.sample_cap:self.sample[j]=sm
    def summary(self):
        n=self.rows
        regions={k:{'count':v,'pct':round(100*v/n,3)} for k,v in self.region.most_common()}
        years={k:v for k,v in sorted(self.years.items(),key=lambda it:it[0])}
        metrics={k:v.result() for k,v in self.stats.items() if v.n}
        pairs={a+'__'+b:c.result() for (a,b),c in self.pairs.items() if c.n}
        result={'rows':n,'files':self.files,'columns':self.columns,'detected_field_mapping':self.mapping,
                'missing_role_pct':{k:round(self.missing[k]*100/n,3) for k in self.mapping} if n else {},
                'non_numeric_values_by_role':dict(self.invalid_num),
                'regional_distribution':regions,'year_counts':years,'missing_or_invalid_years':self.bad_year,
                'before_2000_count':self.before2000,'before_2013_count':self.before2013,'after_2025_count':self.after2025,
                'out_of_declared_range_by_role':dict(self.out_of_range),
                'outlets_n':len(self.outlet),'outlet_counts_top40':dict(self.outlet.most_common(40)),
                'numeric_descriptive':metrics,'correlations':pairs,
                'potential_duplicate_counts':self.dup,'duplicate_check_first_million_only':sorted(self.dedup_partial),
                'eligible_model_rows':self.sample_seen,'model_sample_rows':len(self.sample),
                'model_uses_sample':self.sample_seen>len(self.sample)}
        if self.formula_count:
            result['identity_reconstruction']={'n':self.formula_count,**{x:{'mae':round(self.formula_sums[x]/self.formula_count,7),'within_0.01_pct':round(100*self.formula_near[x]/self.formula_count,3)} for x in self.formula_sums}}
        if self.label_pairs:
            count=sum(self.label_pairs.values());same=sum(n for (h,m),n in self.label_pairs.items() if h==m)
            hm=collections.Counter(); mm=collections.Counter();labels=set()
            for (h,m),num in self.label_pairs.items():
                hm[h]+=num;mm[m]+=num;labels.update((h,m))
            pe=sum(hm[label]*mm[label] for label in labels)/(count*count)
            po=same/count
            kappa=(po-pe)/(1-pe) if pe<1 else None
            f1=[]; metrics={}
            for label in sorted(labels):
                tp=self.label_pairs.get((label,label),0)
                prec=tp/mm[label] if mm[label] else 0.
                recall=tp/hm[label] if hm[label] else 0.
                f=2*prec*recall/(prec+recall) if prec+recall else 0.
                f1.append(f)
                metrics[label]={'n_true':hm[label],'precision':round(prec,5),'recall':round(recall,5),'f1':round(f,5)}
            result['manual_vs_model_label']={'n':count,'raw_agreement_pct':round(100*po,3),
                'cohens_kappa':round(kappa,5) if kappa is not None else None,
                'macro_f1':round(sum(f1)/len(f1),5) if f1 else None,
                'per_class':metrics,
                'confusion_counts_aggregated':{h+' -> '+m:n for (h,m),n in self.label_pairs.items()}}
        return result

def schema_key(columns):
    return hashlib.sha256('|'.join(sorted(norm(c) for c in columns)).encode()).hexdigest()[:12]

def analyze_model(family):
    """Associational diagnostics only, not causal mediation. Optional dependencies."""
    data=family.sample
    if not data:return {'status':'skipped','reason':'No rows with identity, development, emotion as valid numerics'}
    try:
        import pandas as pd
        import numpy as np
        import statsmodels.api as sm
    except ImportError:
        return {'status':'skipped','reason':'Install numpy pandas statsmodels for optional exploratory regression (py -m pip install numpy pandas statsmodels)'}
    df=pd.DataFrame(data)
    result={'status':'conditional','sample_n':len(df),'sampling':'reservoir sample' if family.sample_seen>len(df) else 'all eligible rows',
            'caution':'Associational diagnostic; not causal mediation; text-computed identity may mechanically share sentiment with emotion.'}
    df=df.dropna(subset=['identity','development','emotion'])
    if len(df)<100:return {'status':'skipped','reason':'Fewer than 100 rows with required numerical values'}
    basic=['development'];extras=[]
    if 'cooperation' in df and df['cooperation'].notna().sum()>=len(df)*0.85:extras.append('cooperation')
    if 'word_count' in df and df['word_count'].notna().sum()>=len(df)*0.85:
        df['log_word_count']=np.log1p(pd.to_numeric(df['word_count'],errors='coerce').clip(lower=0))
        extras.append('log_word_count')
    keep=['identity','emotion']+basic+extras
    d=df.dropna(subset=keep).copy()
    if len(d)<100:return {'status':'skipped','reason':'Insufficient complete cases'}
    for k in ['identity','development','emotion']:
        if d[k].std()<1e-10:return {'status':'skipped','reason':k+' has no variance'}
    controls=d[['development']+extras].copy()
    fixed=[]
    if 'outlet' in d and d['outlet'].notna().mean()>.95 and 2<=d['outlet'].nunique()<=180:
        fixed.append('outlet')
    if 'year' in d and d['year'].notna().mean()>.95 and 2<=d['year'].nunique()<=40:
        fixed.append('year')
    if 'outlet' not in fixed and 'region' in d and d['region'].notna().mean()>.9 and 2<=d['region'].nunique()<=6:
        fixed.append('region')
    result['controls']=['development']+extras
    result['fixed_effect_dummies']=fixed
    result['warning_fe']='Outlet FE + year FE' if fixed==['outlet','year'] else 'Not the requested two-way outlet+year FE. Missing/out-of-range field(s).'
    for role in fixed:
        tmp=pd.get_dummies(d[role].astype(str),prefix=role,drop_first=True,dtype=float)
        controls=pd.concat([controls,tmp],axis=1)
    controls=sm.add_constant(controls.astype(float),has_constant='add')
    if controls.shape[1]>350:return {'status':'skipped','reason':'Too many dummy variables; simplify dataset'}
    cluster=(d['outlet'] if 'outlet' in fixed and d['outlet'].nunique()>=10 else None)
    def fit(y,X):
        if cluster is not None:
            return sm.OLS(d[y].astype(float),X).fit(cov_type='cluster',cov_kwds={'groups':cluster},use_t=False)
        return sm.OLS(d[y].astype(float),X).fit(cov_type='HC1',use_t=False)
    try:
        m=fit('emotion',controls)
        ydirect=fit('identity',pd.concat([controls,d[['emotion']].astype(float)],axis=1))
        ytotal=fit('identity',controls)
        a,b,cprime,c=m.params['development'],ydirect.params['emotion'],ydirect.params['development'],ytotal.params['development']
        ab=a*b
        result.update({'complete_n':len(d),'standard_errors':'clustered by outlet' if cluster is not None else 'HC1 (outlet cluster unavailable / too few groups)',
              'outlet_clusters':int(cluster.nunique()) if cluster is not None else None,
              'a_development_to_emotion':round(float(a),6),
              'b_emotion_to_identity':round(float(b),6),
              'direct_cprime':round(float(cprime),6),
              'total_c':round(float(c),6),
              'a_times_b':round(float(ab),6),
              'decomposition_residual_c_minus_cprime_minus_ab':round(float(c-cprime-ab),10),
              'indirect_ratio_pct':round(float(100*ab/c),3) if abs(c)>1e-8 else None,
              'coeff_table': {name: {'coef':round(float(ydirect.params[name]),6),'se':round(float(ydirect.bse[name]),6),'p':round(float(ydirect.pvalues[name]),8)} for name in ['development','emotion']+(['cooperation'] if 'cooperation' in extras else [])},
              'r2_identity_direct':round(float(ydirect.rsquared),6),
              'claim_a_0.6989_diff':round(float(a-.6989),6),
              'claim_b_0.8421_diff':round(float(b-.8421),6),
              'claim_cprime_0.0440_diff':round(float(cprime-.0440),6),
              'claim_indirect_ratio_93.04_diff_pct':round(float(100*ab/c-93.04),3) if abs(c)>1e-8 else None,
              'note':'The manuscript coefficients are compared descriptively only; exact matching requires identical preprocessing, sample and specification; no bootstrap CI or causal inference is claimed.'})
        return result
    except Exception as e:
        return {'status':'skipped','reason':'Model numerical issue: '+str(e)[:300]}

def optional_pca_cluster(family):
    out={}
    if not family.sample:return {'status':'skipped','reason':'No eligible numeric-only sampled rows'}
    try:
        import numpy as np
        import pandas as pd
    except ImportError:return {'status':'skipped','reason':'numpy/pandas unavailable'}
    frame=pd.DataFrame(family.sample)
    fields=['pca_term_weight','pca_keyword_count','pca_keyword_density']
    if set(fields).issubset(frame.columns):
        d=frame[fields].apply(pd.to_numeric,errors='coerce').dropna()
        if len(d)>=50 and (d.std()>1e-10).all():
            z=(d-d.mean())/d.std(ddof=1)
            cov=np.cov(z.to_numpy(),rowvar=False)
            vals,vec=np.linalg.eigh(cov)
            order=np.argsort(vals)[::-1]
            eig=vals[order];vec=vec[:,order]
            if vec[:,0].sum()<0:vec[:,0]*=-1  # Sign convention for readable comparison only.
            out['pca']={'status':'calculated','n':int(len(d)),
                        'standardization':'z-score within sampled analytical data',
                        'eigenvalues':np.round(eig,6).tolist(),
                        'explained_variance_ratio':np.round(eig/eig.sum(),6).tolist(),
                        'first_component_loadings_eigenvector':dict(zip(fields,np.round(vec[:,0],6).tolist())),
                        'target_first_component_variance_pct':69.45,
                        'difference_first_component_pct_points':round(float(100*eig[0]/eig.sum()-69.45),3)}
    if 'cluster' in frame.columns and frame['cluster'].notna().any():
        clustered=frame[frame['cluster'].notna()].copy()
        clustered['cluster']=clustered['cluster'].astype(str)
        sizes=clustered['cluster'].value_counts()
        means=clustered.groupby('cluster')[[x for x in ('development','cooperation','emotion','identity') if x in clustered.columns]].mean(numeric_only=True)
        out['clusters']={'status':'observed','n':int(len(clustered)),'k':int(len(sizes)),
                         'sizes':{str(k):int(v) for k,v in sizes.items()},
                         'feature_means':{str(k):{key:round(float(v),6) for key,v in means.loc[k].items() if pd.notna(v)} for k in sizes.index}}
        needed=['development','cooperation','emotion']
        if len(sizes)>=2 and set(needed).issubset(clustered.columns):
            try:
                from sklearn.preprocessing import StandardScaler
                from sklearn.metrics import silhouette_score
                tmp=clustered[['cluster']+needed].dropna().copy()
                if len(tmp)>1800:tmp=tmp.sample(n=1800,random_state=42)
                labels=tmp['cluster']
                if 2<=labels.nunique()<len(tmp):
                    scaled=StandardScaler().fit_transform(tmp[needed].to_numpy())
                    out['clusters']['silhouette_approx']=round(float(silhouette_score(scaled,labels)),5)
                    out['clusters']['silhouette_sample_n']=len(tmp)
                    out['clusters']['silhouette_note']='Sampled K-means silhouette from pre-existing labels, not an optimal K evaluation.'
            except (ImportError,ValueError) as e:out['clusters']['silhouette_note']='Unable to calculate silhouette: '+str(e)[:100]
    return out if out else {'status':'skipped','reason':'No PCA component triplet or cluster labels available'}

def assess(fam, summary, model):
    flags=[];n=fam.rows
    def add(severity,subject,evidence,next_step):flags.append({'severity':severity,'issue':subject,'evidence':evidence,'action':next_step})
    if n==0:add('P0','Dataset has no readable records','0 rows','Check file format and headers')
    if n!=EXPECTED_N:add('P1','Valid corpus does not match manuscript N','Current schema family '+str(n)+' vs manuscript '+str(EXPECTED_N),'Confirm whether this family is raw, cleaned or analytical; document selection funnel')
    for role in MANDATORY:
        if role == 'year' and 'date' in fam.mapping:continue
        if role not in fam.mapping:add('P0' if role in ('identity','development','emotion') else 'P1','Field mapping missing: '+role, 'Cannot find unambiguous header','Edit field_mapping.json override then rerun')
    for role in CORE:
        if role in fam.mapping and fam.missing[role]/max(1,n)>.05:
            add('P1', 'Missing '+role,'missing '+str(round(100*fam.missing[role]/n,2))+'%','Check cleaning and missingness pattern before modelling')
    if 'identity_reconstruction' in summary:
        recon=summary['identity_reconstruction']
        if max(recon['raw']['within_0.01_pct'],recon['norm']['within_0.01_pct'])>80:
            add('P0','Outcome formula includes sentiment','Formula reconstruction matches >80% of observations','Replace identity outcome with independently annotated support stance; exclude shared emotion ingredient')
    if 'identity' in fam.mapping and 'sentiment' in fam.mapping:
        add('P0','Potential part-whole measurement overlap','Identity and sentiment both present; article states identity=(sentiment+semantic)/2','Explicitly isolate outcome from mediator; validate annotation definition even when formula does not match')
    if 'worry__confusion' in summary['correlations']:
        cc=summary['correlations']['worry__confusion'].get('pearson_r')
        if cc is not None and abs(cc)>.9:add('P1','Worry and confusion near-collinear','Pearson r='+str(cc),'Check dimension label leakage; report correlation matrix and VIF; sensitivity analysis')
    if fam.outlet and len(fam.outlet)<44:add('P1','Fewer than 44 distinct outlets','Found '+str(len(fam.outlet))+'; manuscript 44','Cross-check outlet master list, aliases, missing outlet names')
    if fam.before2013:add('P1','Pre-2013 corpus uses later diplomatic concept','Rows before 2013: '+str(fam.before2013),'Separate historical China-news frame from post-proposal community identification measure')
    if n and '东非' in summary['regional_distribution']:
        p=summary['regional_distribution']['东非']['pct']
        if abs(p-72.26)>2:add('P1','East Africa sampling share mismatch','Data '+str(p)+'%; manuscript 72.26%','Check filtering and regional assignment table')
    if model.get('status')=='conditional' and model.get('warning_fe')!='Outlet FE + year FE':
        add('P1','Two-way fixed effects cannot be confirmed',model.get('warning_fe',''),'Ensure genuine outlet/year identifiers and rerun grouped-SE specification')
    for role,num in summary.get('out_of_declared_range_by_role',{}).items():
        if num:
            add('P0' if role=='identity' else 'P1',role+' outside declared measurement range',str(num)+' records','Check scaling/formula, clipping and variable definitions')
    if n and summary.get('before_2000_count',0):
        add('P1','Records before coverage starts','before 2000: '+str(summary['before_2000_count']),'Verify 2000–2025 filter or correct manuscript scope')
    if n and summary['after_2025_count']:
        add('P1','Records after manuscript coverage end','after 2025 '+str(summary['after_2025_count']),'Verify date parsing and article eligibility')
    if summary['potential_duplicate_counts'].get('text',0):
        pct=round(100*summary['potential_duplicate_counts']['text']/max(n,1),3)
        if pct>1:add('P1','Exact duplicate article text',str(summary['potential_duplicate_counts']['text'])+' ('+str(pct)+'%)','Check syndication/replication and deduplication policy')
    if not flags:add('INFO','No obvious failures in automated checks','Not a validity guarantee','Still inspect manual coding, original model logs and sampling decisions')
    return flags

def markdown_report(payload):
    fam=payload['selected_family']; s=payload['families'][fam];model=payload['conditional_model']
    out=['# 非洲媒体论文原始数据：本地诊断报告','','> 生成时间：'+payload['generated_at']+' ｜ 审计脚本：'+VERSION,
         '> **无新闻正文、标题、网址或逐条记录写入报告。** 本报告为代码自动诊断，不等于专家核验或因果识别。','',
         '## 1. 文件与分析数据集识别',
         '- 扫描文件数：'+str(payload['total_files'])+'；已读取：'+str(payload['read_files'])+'；失败或跳过：'+str(len(payload['errors'])),
         '- 检出字段结构：'+str(len(payload['families']))+'组（文件结构不同时不能直接相加为论文样本）。',
         '- 选定主要分析结构：`'+fam+'`，共 '+str(s['rows'])+' 条；可能用于模型的完整主变量观测 '+str(s['eligible_model_rows'])+' 条。',
         '- 论文声称：'+str(EXPECTED_N)+'条有效报道、44家新闻网站、2000—2025年。',
         '','## 2. 变量匹配及缺失','| 角色 | 匹配列名 | 缺失率 |','|---|---|---:|']
    for role in MANDATORY+('sentiment','semantic','trust','expectation','worry','confusion','word_count','cluster'):
        col=s['detected_field_mapping'].get(role,'（未识别）')
        p=s['missing_role_pct'].get(role,None)
        out.append('| '+role+' | '+str(col).replace('|','/')+' | '+(str(p)+'%' if p is not None else '—')+' |')
    out.extend(['','## 3. 各区域样本','| 区域 | N | 占比 | 论文报告 |','|---|---:|---:|---:|'])
    for r,record in s['regional_distribution'].items():
        out.append(f'| {r} | {record["count"]} | {record["pct"]}% | {EXPECTED_REGION.get(r,"—")}% |')
    out.extend(['','## 4. 数值统计（在全部有效数值上计算均值/标准差；分位数及偏度为抽样估计）',
                '| 指标 | N | 均值 | 标准差 | 最小值 | 中位数* | 最大值 |','|---|---:|---:|---:|---:|---:|---:|'])
    for role,t in s['numeric_descriptive'].items():
        out.append('| '+role+' | '+str(t.get('n',''))+' | '+str(t.get('mean',''))+' | '+str(t.get('std',''))+' | '+str(t.get('min',''))+' | '+str(t.get('median',''))+' | '+str(t.get('max',''))+' |')
    out.extend(['','## 5. 与论文核心主张相关的核验','### 5.1 因变量公式复算'])
    if 'identity_reconstruction' in s:
        rr=s['identity_reconstruction'];out.append('有效三变量观测：'+str(rr['n']))
        for formula,desc in [('raw','(情感值+语义关联度)/2'),('norm','((情感值+1)/2+语义关联度)/2')]:
            t=rr[formula];out.append(f'- {desc}: 平均绝对差 {t["mae"]}，误差小于0.01比例 {t["within_0.01_pct"]}%')
    else:out.append('无法复算：没有同时匹配认同、情感值、语义关联度列。')
    out.append('### 5.2 关键相关系数')
    for k,v in s['correlations'].items():out.append('- '+k+': r='+str(v['pearson_r'])+' (N='+str(v['n'])+')')
    out.append('### 5.3 历史年分与数据粒度')
    out.extend(['- 2013年前记录数：'+str(s['before_2013_count']),'- 2025年后记录数：'+str(s['after_2025_count']),
                '- 无法解析年份数：'+str(s['missing_or_invalid_years']),
                '- 新闻文本精确重复候选：'+str(s['potential_duplicate_counts']['text'])+'；标题重复候选：'+str(s['potential_duplicate_counts']['title'])+'；ID重复候选：'+str(s['potential_duplicate_counts']['article_id']),
                '- 媒体机构识别数量：'+str(s['outlets_n'])])
    out.append('- 超出论文声明取值范围的条数：'+str(s.get('out_of_declared_range_by_role',{})))
    out.extend(['','### 5.4 可选描述性回归（非因果）','- 状态：'+str(model.get('status','skipped'))])
    if model.get('status')=='conditional':
        for k in ('complete_n','fixed_effect_dummies','standard_errors','a_development_to_emotion','b_emotion_to_identity','direct_cprime','total_c','a_times_b','indirect_ratio_pct','decomposition_residual_c_minus_cprime_minus_ab','r2_identity_direct'):
            out.append('- '+k+': '+str(model.get(k)))
        out.append('- 注意：回归只是对样本和字段映射的初步复核；没有控制未观测混杂，没有置信区间中介检验。')
    else:out.append('- 跳过原因：'+str(model.get('reason')))
    out.extend(['','## 6. 按优先级排列的自动警报'])
    for i,flag in enumerate(payload['findings'],1):
        out.append(f'{i}. **[{flag["severity"]}] {flag["issue"]}** — 证据：{flag["evidence"]}；下一步：{flag["action"]}')
    pca_cluster=payload.get('pca_cluster_diagnostics',{})
    out.extend(['','## 6.1 PCA和聚类附加核查'])
    if 'pca' in pca_cluster:
        out.append('- PCA第一主成分解释率：'+str(round(100*pca_cluster['pca']['explained_variance_ratio'][0],3))+'%，与论文69.45%的差异：'+str(pca_cluster['pca']['difference_first_component_pct_points'])+'个百分点（受样本/标准化影响）')
    if 'clusters' in pca_cluster:
        out.append('- 聚类标签数：'+str(pca_cluster['clusters']['k'])+'；簇大小：'+str(pca_cluster['clusters']['sizes']))
        if 'silhouette_approx' in pca_cluster['clusters']:out.append('- 抽样轮廓系数：'+str(pca_cluster['clusters']['silhouette_approx']))
    if 'pca' not in pca_cluster and 'clusters' not in pca_cluster:out.append('- 无法执行：当前文件中缺乏匹配的PCA三个源指标或已有聚类标签。')
    if 'manual_vs_model_label' in s:
        a=s['manual_vs_model_label'];out.append('- 人工标签 vs 模型标签: N='+str(a['n'])+'，Kappa='+str(a['cohens_kappa'])+'，macro-F1='+str(a['macro_f1']))
    out.extend(['','## 7. 当前数据不能单独证明的事项','- “媒体机构认同”是否能由文章文本推及：需要理论定义与人工效标。',
                '- BERT 是否真在5万条标注语料上训练、87.3%何种准确率：需要训练日志、完整类别指标及500条人工双人复核。',
                '- PCA是否确为第一主成分69.45%：需要原始3个成分、标准化方式、载荷及特征值。',
                '- 词库是否相互独立且关键词重叠率<5%：需要词表和构造代码。',
                '- 因果“发展→情感→认同”：横截面文本的回归/Bootstrap本身不解决反向因果或遗漏变量。',
                '- K=6聚类是否合理：需要聚类输入的标准化、选择K理由、稳定性和簇中心。',
                '','## 8. 数据安全和再次反馈',
                '- 请**只上传**同目录下 `africa_audit_result.zip`，不要上传原始新闻正文。',
                '- `field_mapping_suggestions.json` 包含列名以帮助识别字段；如列名涉及敏感信息，请先检查后上传。',
                '- 如自动识别错误，在 `field_mapping.json` 中人工指定角色→列名，重新运行。',
                ''])
    return '\n'.join(out)

def main():
    ap=argparse.ArgumentParser(description='Local aggregated audit; original text stays on this computer.')
    ap.add_argument('--input',required=True,help='A cleaned-data folder or individual data file')
    ap.add_argument('--output',default=None,help='Output folder; defaults to sibling folder 非洲_诊断输出')
    ap.add_argument('--max-files',type=int,default=2000)
    ap.add_argument('--model-sample-cap',type=int,default=40000,help='Max rows kept in RAM for optional regression')
    ap.add_argument('--skip-model',action='store_true',help='Scan only (fastest)')
    args=ap.parse_args()
    path=Path(args.input).expanduser()
    if not path.exists():raise SystemExit('ERROR: input path not found: '+str(path))
    out=Path(args.output) if args.output else (path.parent / '非洲_诊断输出')
    out.mkdir(parents=True,exist_ok=True)
    # Mapping optional; manual override only, do not overwrite.
    override_path=out/'field_mapping.json'
    if override_path.exists():
        with open(override_path,'r',encoding='utf-8') as f:overrides=json.load(f)
    else:overrides={}
    if path.is_file():files=[path]
    else:files=sorted([p for p in path.rglob('*') if p.is_file() and any(p.name.lower().endswith(e) for e in READABLE) and out not in p.parents],key=lambda x:str(x).lower())
    if len(files)>args.max_files:raise SystemExit('More than --max-files. Increase explicitly after confirming expected file list.')
    print('Scanned data files:',len(files),'\nAggregated report output:',out,flush=True)
    families={};file_log=[];errors=[];suggestions={}
    for idx,f in enumerate(files,1):
        display=str(f.relative_to(path)) if path.is_dir() else f.name
        print(f'[{idx}/{len(files)}] {display}',flush=True)
        rowcount=0;parse_errors=0;family=None;details={};cols=[];multiple_sheets=False
        try:
            for typ,item,info in open_rows(f):
                if typ=='HEADER':
                    cols=item; details.update(info or {})
                    mapping,proposed,conflicts=detect_columns(cols,overrides)
                    signature=schema_key(cols)
                    # A worksheet may differ within an Excel file.
                    if signature not in families:families[signature]=Family(cols,mapping,max(1000,args.model_sample_cap),42)
                    family=families[signature]
                    if display not in family.files:family.files.append(display)
                    if signature not in suggestions:suggestions[signature]={'files':[display], 'detected_field_mapping':mapping,'candidate_headers':proposed,'ambiguous_mappings':conflicts}
                    elif display not in suggestions[signature]['files']:suggestions[signature]['files'].append(display)
                elif typ=='ROW':
                    if family is None:continue
                    family.update(item);rowcount+=1
                    if rowcount%50000==0:print('    read',rowcount,'rows...',flush=True)
                elif typ=='ERROR':
                    parse_errors+=1
            file_log.append({'file':display,'bytes':f.stat().st_size,'rows':rowcount,'parse_errors':parse_errors,'schema_key':schema_key(cols) if cols else None,**details})
        except Exception as e:
            errors.append({'file':display,'problem':type(e).__name__+': '+str(e)[:500]})
            file_log.append({'file':display,'bytes':f.stat().st_size,'rows_read_before_error':rowcount,'status':'error'})
            print('   WARNING:',str(e)[:200],flush=True)
    if not families:
        print('ERROR: No successfully parsed data; check file formats or JSON structure.',flush=True)
        print('Scanned files:',[str(q.name) for q in files],flush=True)
        for e in errors[:3]:print('Error detail:',e,flush=True)
    scores=[]
    for key,fam in families.items():
        m=fam.mapping; score=20*sum(k in m for k in ('identity','development','emotion'))+8*sum(k in m for k in ('cooperation','outlet','year'))+math.log1p(fam.rows)
        scores.append((score,key))
    selected=max(scores)[1] if scores else None
    family_summaries={k:fam.summary() for k,fam in families.items()}
    model=analyze_model(families[selected]) if selected and not args.skip_model else {'status':'skipped','reason':'User skipped regression or no suitable family'}
    pca_cluster=optional_pca_cluster(families[selected]) if selected and not args.skip_model else {'status':'skipped','reason':'User skipped optional extras or no suitable family'}
    findings=assess(families[selected],family_summaries[selected],model) if selected else [{'severity':'P0','issue':'No dataset successfully loaded','evidence':str(len(errors))+' errors','action':'Check input types and install file format dependencies'}]
    result={'script_version':VERSION,'generated_at':datetime.datetime.now().isoformat(timespec='seconds'),
            'input_folder_exists':True,'input_kind':'single_file' if path.is_file() else 'folder',
            'total_files':len(files),'read_files':len(files)-len(errors),'files':file_log,'errors':errors,
            'selected_family':selected,'families':family_summaries,
            'conditional_model':model,'pca_cluster_diagnostics':pca_cluster,'findings':findings,
            'paper_reference':{'effective_news_rows':EXPECTED_N,'websites':44,'period':'2000-2025','regional_pct':EXPECTED_REGION},
            'privacy_note':'This report contains aggregate numbers, column/file names and outlet labels only. No article text/title/URL/IDs.'}
    with open(out/'audit_report.json','w',encoding='utf-8') as fo:json.dump(result,fo,ensure_ascii=False,indent=2,default=str)
    with open(out/'field_mapping_suggestions.json','w',encoding='utf-8') as fo:json.dump(suggestions,fo,ensure_ascii=False,indent=2)
    if not override_path.exists():
        # Blank template: automatic mapping remains unless user fills role with literal header.
        with open(override_path,'w',encoding='utf-8') as fo:json.dump({},fo,ensure_ascii=False,indent=2)
    with open(out/'audit_report.md','w',encoding='utf-8') as fo:
        fo.write(markdown_report(result) if selected else '# No readable records\n'+json.dumps(errors,ensure_ascii=False,indent=2))
    archive=out/'africa_audit_result.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for fn in ('audit_report.json','audit_report.md','field_mapping_suggestions.json'):
            z.write(out/fn,arcname=fn)
    if not selected or family_summaries[selected]['rows']==0:
        print('\nAUDIT FAILED: no article records were recognized; report contains diagnostic errors only.',flush=True)
        raise SystemExit(2)
    print('\nCOMPLETED: data records were read',flush=True)
    print('UPLOAD ONLY:',archive,flush=True)
    print('Key warnings:',flush=True)
    for f in findings[:10]:print(' - ['+f['severity']+']',f['issue'],flush=True)
    if errors: print('File errors:',len(errors),'(see audit_report.json)',flush=True)

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:raise SystemExit('Stopped by user; no data were uploaded.')
