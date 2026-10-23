#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多语言文本清洗与NLTK分词向量化脚本
支持英文、中文等多语言文本处理
"""

import json
import re
import string
import numpy as np
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

# NLTK相关导入
try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk import pos_tag
    from nltk.probability import FreqDist
    
    # 检查NLTK数据包是否已下载
    def check_nltk_data():
        required_packages = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
        missing_packages = []
        
        for package in required_packages:
            try:
                if package == 'punkt':
                    nltk.data.find('tokenizers/punkt')
                elif package == 'stopwords':
                    nltk.data.find('corpora/stopwords')
                elif package == 'wordnet':
                    nltk.data.find('corpora/wordnet')
                elif package == 'averaged_perceptron_tagger':
                    nltk.data.find('taggers/averaged_perceptron_tagger')
                print(f"✓ {package} 数据包已存在")
            except LookupError:
                missing_packages.append(package)
                print(f"✗ {package} 数据包缺失")
        
        return missing_packages

    # 尝试下载缺失的数据包
    def download_missing_packages(missing_packages):
        if not missing_packages:
            print("所有必要数据包都已存在")
            return True
        
        print(f"尝试下载缺失的数据包: {missing_packages}")
        
        for package in missing_packages:
            try:
                print(f"正在下载 {package}...")
                nltk.download(package, quiet=True)
                print(f"✓ {package} 下载成功")
            except Exception as e:
                print(f"✗ {package} 下载失败: {e}")
                return False
        
        return True

    # 检查并下载数据包
    print("检查NLTK数据包状态...")
    missing_packages = check_nltk_data()

    if missing_packages:
        print("\n尝试下载缺失的数据包...")
        success = download_missing_packages(missing_packages)
        if not success:
            print("\n警告: 部分数据包下载失败，将使用备用分词方法")
            # 设置备用标志
            use_backup_tokenizer = True
        else:
            use_backup_tokenizer = False
    else:
        use_backup_tokenizer = False

    print("\n数据包检查完成")
    
except ImportError:
    print("警告: NLTK未安装，请运行 'pip install nltk'")

# 备用分词函数（当NLTK数据包不可用时使用）
def backup_tokenize(text):
    """简单的基于空格和标点的分词方法"""
    # 使用正则表达式分割单词
    tokens = re.findall(r'\b\w+\b', text.lower())
    return tokens

# 文本向量化相关
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF

class MultiLanguageTextProcessor:
    """多语言文本处理器"""
    
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.english_stopwords = set(stopwords.words('english'))
        
        # 扩展停用词列表
        self.custom_stopwords = {
            'said', 'says', 'say', 'according', 'also', 'would', 'could', 
            'may', 'might', 'must', 'shall', 'should', 'will', 'can',
            'one', 'two', 'three', 'first', 'second', 'third', 'new',
            'year', 'years', 'month', 'months', 'day', 'days', 'time',
            'percent', 'percentage', 'million', 'billion', 'trillion'
        }
        
        self.all_stopwords = self.english_stopwords.union(self.custom_stopwords)
        
        # 语言检测模式
        self.chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        self.english_pattern = re.compile(r'[a-zA-Z]+')
    
    def detect_language(self, text):
        """检测文本的主要语言"""
        if not text:
            return "unknown"
        
        chinese_chars = len(self.chinese_pattern.findall(text))
        english_words = len(self.english_pattern.findall(text))
        
        if chinese_chars > english_words / 2:
            return "chinese"
        elif english_words > 0:
            return "english"
        else:
            return "unknown"
    
    def clean_text(self, text):
        """基础文本清洗"""
        if not text:
            return ""
        
        # 转换为小写
        text = text.lower()
        
        # 移除URL
        text = re.sub(r'http\S+|www\.\S+', '', text)
        
        # 移除HTML标签
        text = re.sub(r'<.*?>', '', text)
        
        # 移除特殊字符和数字，但保留基本标点
        text = re.sub(r'[^\w\s.,!?;:]', '', text)
        
        # 标准化空白字符
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize_english(self, text):
        """英文分词"""
        # 根据NLTK数据包状态选择分词方法
        if 'use_backup_tokenizer' in globals() and use_backup_tokenizer:
            tokens = backup_tokenize(text)
        else:
            try:
                tokens = word_tokenize(text)
            except Exception as e:
                print(f"NLTK分词失败，使用备用方法: {e}")
                tokens = backup_tokenize(text)
        
        # 过滤停用词和短词
        tokens = [token for token in tokens 
                 if token not in self.all_stopwords and len(token) > 2]
        
        # 词形还原
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        
        return tokens
    
    def tokenize_chinese(self, text):
        """中文分词（简化版，实际应用中建议使用jieba）"""
        # 这里使用基于字符的分词，实际应用中建议安装jieba
        tokens = list(text)
        
        # 过滤单个字符（除了常见的中文单字）
        common_chinese_chars = {'的', '是', '在', '有', '和', '与', '及', '或'}
        tokens = [token for token in tokens 
                 if len(token) > 1 or token in common_chinese_chars]
        
        return tokens
    
    def tokenize_text(self, text):
        """多语言分词"""
        if not text:
            return []
        
        language = self.detect_language(text)
        
        if language == "english":
            return self.tokenize_english(text)
        elif language == "chinese":
            return self.tokenize_chinese(text)
        else:
            # 默认使用英文分词
            return self.tokenize_english(text)
    
    def get_pos_tags(self, tokens):
        """获取词性标注"""
        if not tokens:
            return []
        
        try:
            return pos_tag(tokens)
        except:
            return [(token, 'UNK') for token in tokens]

class TextVectorizer:
    """文本向量化器"""
    
    def __init__(self, max_features=5000):
        self.max_features = max_features
        self.tfidf_vectorizer = None
        self.count_vectorizer = None
    
    def fit_tfidf(self, texts):
        """训练TF-IDF向量化器"""
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2)  # 包含单字和双字词组
        )
        
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
        return tfidf_matrix
    
    def fit_count(self, texts):
        """训练词袋模型向量化器"""
        self.count_vectorizer = CountVectorizer(
            max_features=self.max_features,
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2)
        )
        
        count_matrix = self.count_vectorizer.fit_transform(texts)
        return count_matrix
    
    def get_feature_names(self):
        """获取特征名称"""
        if self.tfidf_vectorizer:
            return self.tfidf_vectorizer.get_feature_names_out()
        elif self.count_vectorizer:
            return self.count_vectorizer.get_feature_names_out()
        else:
            return []

class NewsDataAnalyzer:
    """新闻数据分析器"""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = []
        self.processor = MultiLanguageTextProcessor()
        self.vectorizer = TextVectorizer()
    
    def load_data(self, sample_size=None):
        """加载数据"""
        print("正在加载数据...")
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            # 检查数据类型
            print(f"数据类型: {type(self.data)}")
            if isinstance(self.data, list):
                print(f"列表长度: {len(self.data)}")
                if len(self.data) > 0:
                    print(f"第一个元素类型: {type(self.data[0])}")
            
            if sample_size and sample_size < len(self.data):
                self.data = self.data[:sample_size]
            
            print(f"成功加载 {len(self.data)} 条新闻数据")
            return True
            
        except Exception as e:
            print(f"数据加载失败: {e}")
            return False
    
    def analyze_data_structure(self):
        """分析数据结构"""
        print("\n=== 数据结构分析 ===")
        
        if not self.data:
            print("无数据可分析")
            return
        
        # 基本统计
        print(f"总新闻数量: {len(self.data)}")
        
        # 字段存在性检查
        if isinstance(self.data, list) and len(self.data) > 0:
            sample_record = self.data[0]
            if isinstance(sample_record, dict):
                print(f"可用字段: {list(sample_record.keys())}")
                
                # 语言分布分析
                languages = []
                sample_size = min(1000, len(self.data))
                for i in range(sample_size):
                    record = self.data[i]
                    if isinstance(record, dict):
                        title_lang = self.processor.detect_language(record.get('title', ''))
                        summary_lang = self.processor.detect_language(record.get('summary', ''))
                        languages.extend([title_lang, summary_lang])
                
                lang_counts = Counter(languages)
                print(f"语言分布: {dict(lang_counts)}")
                
                # 文本长度分析
                title_lengths = []
                summary_lengths = []
                for i in range(sample_size):
                    record = self.data[i]
                    if isinstance(record, dict):
                        title_lengths.append(len(record.get('title', '')))
                        summary_lengths.append(len(record.get('summary', '')))
                
                if title_lengths:
                    print(f"标题平均长度: {np.mean(title_lengths):.1f} 字符")
                if summary_lengths:
                    print(f"摘要平均长度: {np.mean(summary_lengths):.1f} 字符")
            else:
                print("数据格式异常: 记录不是字典类型")
        else:
            print("数据格式异常: 数据不是列表或为空")
    
    def clean_and_tokenize_data(self):
        """清洗和分词数据"""
        print("\n=== 文本清洗与分词 ===")
        
        cleaned_data = []
        
        for i, record in enumerate(self.data):
            if i % 1000 == 0:
                print(f"处理进度: {i}/{len(self.data)}")
            
            # 检查记录类型
            if not isinstance(record, dict):
                print(f"警告: 第{i}条记录不是字典类型，跳过处理")
                continue
            
            # 创建清理后的记录
            cleaned_record = {}
            
            # 复制原始字段
            for key, value in record.items():
                cleaned_record[key] = value
            
            # 清洗标题
            title = record.get('title', '')
            cleaned_title = self.processor.clean_text(title)
            title_tokens = self.processor.tokenize_text(cleaned_title)
            
            # 清洗摘要
            summary = record.get('summary', '')
            cleaned_summary = self.processor.clean_text(summary)
            summary_tokens = self.processor.tokenize_text(cleaned_summary)
            
            # 添加到记录
            cleaned_record.update({
                'cleaned_title': cleaned_title,
                'title_tokens': title_tokens,
                'cleaned_summary': cleaned_summary,
                'summary_tokens': summary_tokens,
                'title_language': self.processor.detect_language(title),
                'summary_language': self.processor.detect_language(summary)
            })
            
            cleaned_data.append(cleaned_record)
        
        return cleaned_data
    
    def vectorize_texts(self, cleaned_data):
        """文本向量化"""
        print("\n=== 文本向量化 ===")
        
        # 准备文本数据
        titles = [record['cleaned_title'] for record in cleaned_data]
        summaries = [record['cleaned_summary'] for record in cleaned_data]
        
        # TF-IDF向量化
        print("正在进行TF-IDF向量化...")
        title_tfidf = self.vectorizer.fit_tfidf(titles)
        summary_tfidf = self.vectorizer.fit_tfidf(summaries)
        
        print(f"标题TF-IDF矩阵形状: {title_tfidf.shape}")
        print(f"摘要TF-IDF矩阵形状: {summary_tfidf.shape}")
        
        return title_tfidf, summary_tfidf
    
    def generate_report(self, cleaned_data, title_tfidf, summary_tfidf):
        """生成分析报告"""
        print("\n=== 生成分析报告 ===")
        
        report = {
            'basic_stats': {
                'total_records': len(self.data),
                'cleaned_records': len(cleaned_data)
            },
            'language_distribution': {},
            'token_statistics': {},
            'vectorization_info': {}
        }
        
        # 语言分布
        title_langs = [record['title_language'] for record in cleaned_data]
        summary_langs = [record['summary_language'] for record in cleaned_data]
        
        report['language_distribution']['title'] = dict(Counter(title_langs))
        report['language_distribution']['summary'] = dict(Counter(summary_langs))
        
        # 分词统计
        title_token_counts = [len(record['title_tokens']) for record in cleaned_data]
        summary_token_counts = [len(record['summary_tokens']) for record in cleaned_data]
        
        report['token_statistics']['title'] = {
            'mean_tokens': np.mean(title_token_counts),
            'max_tokens': np.max(title_token_counts),
            'min_tokens': np.min(title_token_counts)
        }
        
        report['token_statistics']['summary'] = {
            'mean_tokens': np.mean(summary_token_counts),
            'max_tokens': np.max(summary_token_counts),
            'min_tokens': np.min(summary_token_counts)
        }
        
        # 向量化信息
        report['vectorization_info']['title_tfidf_shape'] = title_tfidf.shape
        report['vectorization_info']['summary_tfidf_shape'] = summary_tfidf.shape
        
        # 保存报告（处理NumPy数据类型的序列化）
        def convert_to_serializable(obj):
            """将NumPy数据类型转换为Python原生类型"""
            if isinstance(obj, (np.integer, np.floating)):
                return obj.item()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            else:
                return obj
        
        # 转换报告数据
        serializable_report = convert_to_serializable(report)
        
        with open('text_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(serializable_report, f, indent=2, ensure_ascii=False)
        
        print("分析报告已保存至: text_analysis_report.json")
        
        return report

def main():
    """主函数"""
    file_path = "清洗数据.json"
    
    # 创建分析器
    analyzer = NewsDataAnalyzer(file_path)
    
    # 加载数据（抽样处理，避免内存问题）
    if not analyzer.load_data(sample_size=5000):
        return
    
    # 分析数据结构
    analyzer.analyze_data_structure()
    
    # 清洗和分词
    cleaned_data = analyzer.clean_and_tokenize_data()
    
    # 向量化
    title_tfidf, summary_tfidf = analyzer.vectorize_texts(cleaned_data)
    
    # 生成报告
    report = analyzer.generate_report(cleaned_data, title_tfidf, summary_tfidf)
    
    print("\n=== 分析完成 ===")
    print("详细报告已生成，包含：")
    print("- 数据结构分析")
    print("- 语言分布统计")
    print("- 分词质量评估")
    print("- 向量化结果")

if __name__ == "__main__":
    main()