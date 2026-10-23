#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能新闻来源分析脚本
优先级：URL > source > 智能推断
"""

import json
import re
import os
from urllib.parse import urlparse
from collections import defaultdict, Counter
import tldextract

class IntelligentNewsSourceAnalyzer:
    def __init__(self):
        # 域名到来源的映射字典
        self.domain_to_source_map = {
            # 中国媒体
            'yidaiyilu.gov.cn': '中国一带一路网',
            'xinhuanet.com': '新华网',
            'cgtn.com': 'CGTN',
            'people.cn': '人民网',
            'chinadaily.com.cn': '中国日报',
            'globaltimes.cn': '环球时报',
            'china.org.cn': '中国网',
            'cri.cn': '国际在线',
            'china-embassy.org': '中国大使馆',
            'mofcom.gov.cn': '商务部',
            
            # 非洲媒体
            'english.ahram.org.eg': 'Ahram Online',
            'ahram.org.eg': 'Ahram Online',
            'allafrica.com': 'AllAfrica',
            'africa.cgtn.com': 'CGTN非洲',
            'africanews.com': '非洲新闻',
            'modernghana.com': '现代加纳',
            'punchng.com': '尼日利亚Punch',
            'nation.co.ke': '肯尼亚国家报',
            'dailynews.co.tz': '坦桑尼亚每日新闻',
            'zambianwatchdog.com': '赞比亚观察家',
            
            # 国际媒体
            'bbc.com': 'BBC',
            'cnn.com': 'CNN',
            'reuters.com': '路透社',
            'apnews.com': '美联社',
            'bloomberg.com': '彭博社',
            'aljazeera.com': '半岛电视台',
            'dw.com': '德国之声',
            'france24.com': '法国24',
            'theguardian.com': '卫报',
            'nytimes.com': '纽约时报'
        }
        
        # 关键词到来源的映射（用于智能推断）
        self.keyword_to_source_map = {
            '一带一路': '中国一带一路网',
            '中非合作': '中国一带一路网',
            '新华网': '新华网',
            '新华社': '新华网',
            'CGTN': 'CGTN',
            '中国国际电视台': 'CGTN',
            '人民网': '人民网',
            '人民日报': '人民网',
            '中国日报': '中国日报',
            '环球时报': '环球时报',
            'Ahram': 'Ahram Online',
            '金字塔报': 'Ahram Online',
            'AllAfrica': 'AllAfrica',
            'BBC': 'BBC',
            'CNN': 'CNN',
            '路透社': '路透社',
            '美联社': '美联社',
            '彭博社': '彭博社'
        }
        
        # 来源分类
        self.source_categories = {
            '中国媒体': ['中国一带一路网', '新华网', 'CGTN', '人民网', '中国日报', '环球时报', '中国网', '国际在线'],
            '非洲媒体': ['Ahram Online', 'AllAfrica', 'CGTN非洲', '非洲新闻', '现代加纳', '尼日利亚Punch', '肯尼亚国家报', '坦桑尼亚每日新闻', '赞比亚观察家'],
            '国际媒体': ['BBC', 'CNN', '路透社', '美联社', '彭博社', '半岛电视台', '德国之声', '法国24', '卫报', '纽约时报']
        }
    
    def extract_domain_from_url(self, url):
        """从URL中提取域名"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return None
    
    def get_source_from_url(self, url):
        """根据URL确定来源"""
        if not url:
            return None
        
        # 提取域名
        domain = self.extract_domain_from_url(url)
        if not domain:
            return None
        
        # 使用tldextract进行更精确的域名解析
        extracted = tldextract.extract(url)
        full_domain = f"{extracted.domain}.{extracted.suffix}"
        
        # 查找域名映射
        if full_domain in self.domain_to_source_map:
            return self.domain_to_source_map[full_domain]
        
        # 查找子域名映射
        for known_domain, source in self.domain_to_source_map.items():
            if domain.endswith(known_domain):
                return source
        
        return None
    
    def intelligent_source_inference(self, article):
        """智能推断来源（当URL和source都缺失时）"""
        # 基于标题和内容的关键词分析
        text = f"{article.get('title', '')} {article.get('summary', '')}"
        
        # 检查关键词匹配
        for keyword, source in self.keyword_to_source_map.items():
            if keyword in text:
                return source
        
        # 基于内容特征推断
        if '中国' in text and ('投资' in text or '合作' in text):
            return '中国媒体（推断）'
        elif '非洲' in text and ('发展' in text or '经济' in text):
            return '非洲媒体（推断）'
        elif any(keyword in text for keyword in ['美国', '欧洲', '国际']):
            return '国际媒体（推断）'
        
        return '未知来源'
    
    def determine_source(self, article):
        """确定新闻来源（优先级：URL > source > 智能推断）"""
        # 1. 优先使用URL
        url = article.get('url')
        if url:
            source_from_url = self.get_source_from_url(url)
            if source_from_url:
                return source_from_url, 'URL'
        
        # 2. 使用source字段
        source = article.get('source')
        if source:
            return source, 'source字段'
        
        # 3. 智能推断
        inferred_source = self.intelligent_source_inference(article)
        return inferred_source, '智能推断'
    
    def analyze_news_files(self):
        """分析所有新闻数据文件"""
        files_to_analyze = [
            ('清洗数据.json', '清洗数据'),
            ('china_articles.json', '中国相关文章'),
            ('all_unique_news_data.json', '唯一新闻数据')
        ]
        
        total_stats = {
            'total_articles': 0,
            'sources_by_file': {},
            'determination_methods': defaultdict(int),
            'source_categories': defaultdict(int)
        }
        
        for filename, description in files_to_analyze:
            filepath = os.path.join(os.path.dirname(__file__), filename)
            if not os.path.exists(filepath):
                print(f"警告：文件 {filename} 不存在")
                continue
            
            print(f"\n正在分析 {description} ({filename})...")
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    articles = json.load(f)
                
                file_stats = self.analyze_single_file(articles, description)
                total_stats['total_articles'] += file_stats['total_articles']
                total_stats['sources_by_file'][description] = file_stats['sources']
                
                # 合并统计信息
                for method, count in file_stats['determination_methods'].items():
                    total_stats['determination_methods'][method] += count
                
                for category, count in file_stats['source_categories'].items():
                    total_stats['source_categories'][category] += count
                
            except Exception as e:
                print(f"分析文件 {filename} 时出错: {e}")
        
        return total_stats
    
    def analyze_single_file(self, articles, description):
        """分析单个文件"""
        sources = defaultdict(int)
        determination_methods = defaultdict(int)
        source_categories = defaultdict(int)
        
        url_count = 0
        source_count = 0
        inferred_count = 0
        
        for i, article in enumerate(articles):
            source, method = self.determine_source(article)
            sources[source] += 1
            determination_methods[method] += 1
            
            # 统计方法使用情况
            if method == 'URL':
                url_count += 1
            elif method == 'source字段':
                source_count += 1
            else:
                inferred_count += 1
            
            # 分类统计
            category = self.categorize_source(source)
            source_categories[category] += 1
        
        return {
            'total_articles': len(articles),
            'sources': dict(sources),
            'determination_methods': dict(determination_methods),
            'source_categories': dict(source_categories),
            'url_coverage': url_count / len(articles) if articles else 0,
            'source_coverage': source_count / len(articles) if articles else 0,
            'inferred_coverage': inferred_count / len(articles) if articles else 0
        }
    
    def categorize_source(self, source):
        """对来源进行分类"""
        for category, sources in self.source_categories.items():
            if source in sources:
                return category
        
        if '中国' in source or '新华' in source or '人民' in source:
            return '中国媒体'
        elif '非洲' in source or 'Ahram' in source:
            return '非洲媒体'
        elif '推断' in source:
            return '推断来源'
        else:
            return '其他来源'
    
    def generate_report(self, stats):
        """生成详细的分析报告"""
        report = []
        report.append("=" * 80)
        report.append("                   智能新闻来源分析报告")
        report.append("=" * 80)
        report.append(f"\n总新闻数量: {stats['total_articles']:,} 条")
        
        # 方法使用统计
        report.append("\n" + "-" * 40)
        report.append("来源判定方法统计")
        report.append("-" * 40)
        for method, count in stats['determination_methods'].items():
            percentage = (count / stats['total_articles']) * 100
            report.append(f"{method}: {count:,} 条 ({percentage:.2f}%)")
        
        # 来源分类统计
        report.append("\n" + "-" * 40)
        report.append("来源类型分布")
        report.append("-" * 40)
        for category, count in stats['source_categories'].items():
            percentage = (count / stats['total_articles']) * 100
            report.append(f"{category}: {count:,} 条 ({percentage:.2f}%)")
        
        # 各文件详细分析
        report.append("\n" + "=" * 80)
        report.append("各文件详细分析")
        report.append("=" * 80)
        
        for file_desc, file_stats in stats['sources_by_file'].items():
            report.append(f"\n{file_desc}:")
            report.append("-" * 40)
            
            # 按数量排序
            sorted_sources = sorted(file_stats.items(), key=lambda x: x[1], reverse=True)
            
            for source, count in sorted_sources:
                percentage = (count / sum(file_stats.values())) * 100
                report.append(f"  {source}: {count:,} 条 ({percentage:.2f}%)")
        
        # 数据质量评估
        report.append("\n" + "=" * 80)
        report.append("数据质量评估")
        report.append("=" * 80)
        
        url_coverage = stats['determination_methods'].get('URL', 0) / stats['total_articles'] * 100
        source_coverage = stats['determination_methods'].get('source字段', 0) / stats['total_articles'] * 100
        inferred_coverage = stats['determination_methods'].get('智能推断', 0) / stats['total_articles'] * 100
        
        report.append(f"URL覆盖率: {url_coverage:.2f}%")
        report.append(f"source字段覆盖率: {source_coverage:.2f}%")
        report.append(f"智能推断覆盖率: {inferred_coverage:.2f}%")
        
        if url_coverage < 10:
            report.append("⚠️  警告: URL覆盖率过低，建议补充URL信息")
        if inferred_coverage > 20:
            report.append("⚠️  警告: 智能推断比例较高，可能存在来源识别不准确")
        
        return "\n".join(report)

def main():
    """主函数"""
    print("开始智能新闻来源分析...")
    
    analyzer = IntelligentNewsSourceAnalyzer()
    stats = analyzer.analyze_news_files()
    
    # 生成报告
    report = analyzer.generate_report(stats)
    print(report)
    
    # 保存报告到文件
    report_file = os.path.join(os.path.dirname(__file__), 'news_source_analysis_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n分析报告已保存至: {report_file}")
    
    return stats

if __name__ == "__main__":
    main()