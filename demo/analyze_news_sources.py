#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析新闻数据中的网站来源及其占比
"""

import json
import os
from collections import Counter
from urllib.parse import urlparse

def analyze_cleaned_data():
    """分析清洗数据.json中的新闻来源"""
    print("正在分析清洗数据.json...")
    
    try:
        with open('清洗数据.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 统计来源分布
        sources = []
        for item in data:
            if isinstance(item, dict) and 'source' in item:
                sources.append(item['source'])
        
        source_counter = Counter(sources)
        total_count = len(sources)
        
        print(f"清洗数据.json分析结果:")
        print(f"总新闻数量: {total_count}")
        print("\n新闻来源分布:")
        print("-" * 60)
        
        for source, count in source_counter.most_common():
            percentage = (count / total_count) * 100
            print(f"{source}: {count} 条 ({percentage:.2f}%)")
        
        return source_counter, total_count
        
    except Exception as e:
        print(f"分析清洗数据.json时出错: {e}")
        return None, 0

def analyze_china_articles():
    """分析china_articles.json中的新闻来源"""
    print("\n正在分析china_articles.json...")
    
    try:
        with open('china_articles.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 统计来源分布
        sources = []
        for item in data:
            if isinstance(item, dict) and 'source' in item:
                sources.append(item['source'])
        
        source_counter = Counter(sources)
        total_count = len(sources)
        
        print(f"china_articles.json分析结果:")
        print(f"总新闻数量: {total_count}")
        print("\n新闻来源分布:")
        print("-" * 60)
        
        for source, count in source_counter.most_common():
            percentage = (count / total_count) * 100
            print(f"{source}: {count} 条 ({percentage:.2f}%)")
        
        return source_counter, total_count
        
    except Exception as e:
        print(f"分析china_articles.json时出错: {e}")
        return None, 0

def analyze_all_unique_news():
    """分析all_unique_news_data.json中的新闻来源"""
    print("\n正在分析all_unique_news_data.json...")
    
    try:
        with open('all_unique_news_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 统计来源分布
        sources = []
        urls = []
        
        for item in data:
            if isinstance(item, dict):
                if 'source' in item:
                    sources.append(item['source'])
                if 'url' in item and item['url']:
                    urls.append(item['url'])
        
        source_counter = Counter(sources)
        total_count = len(sources)
        
        print(f"all_unique_news_data.json分析结果:")
        print(f"总新闻数量: {total_count}")
        print(f"包含URL的新闻数量: {len(urls)}")
        
        # 分析URL域名分布
        if urls:
            domains = []
            for url in urls:
                try:
                    parsed = urlparse(url)
                    domain = parsed.netloc
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    domains.append(domain)
                except:
                    domains.append('无效URL')
            
            domain_counter = Counter(domains)
            
            print("\nURL域名分布:")
            print("-" * 60)
            for domain, count in domain_counter.most_common():
                percentage = (count / len(urls)) * 100
                print(f"{domain}: {count} 条 ({percentage:.2f}%)")
        
        print("\n新闻来源分布:")
        print("-" * 60)
        for source, count in source_counter.most_common():
            percentage = (count / total_count) * 100
            print(f"{source}: {count} 条 ({percentage:.2f}%)")
        
        return source_counter, total_count, urls
        
    except Exception as e:
        print(f"分析all_unique_news_data.json时出错: {e}")
        return None, 0, []

def main():
    """主函数"""
    print("=" * 80)
    print("新闻数据来源分析报告")
    print("=" * 80)
    
    # 分析各个文件
    cleaned_sources, cleaned_total = analyze_cleaned_data()
    china_sources, china_total = analyze_china_articles()
    unique_sources, unique_total, unique_urls = analyze_all_unique_news()
    
    # 汇总分析
    print("\n" + "=" * 80)
    print("数据汇总分析")
    print("=" * 80)
    
    total_articles = cleaned_total + china_total + unique_total
    print(f"总新闻数量: {total_articles} 条")
    print(f"清洗数据.json: {cleaned_total} 条")
    print(f"china_articles.json: {china_total} 条")
    print(f"all_unique_news_data.json: {unique_total} 条")
    
    print(f"\n包含URL的新闻数量: {len(unique_urls)} 条")
    print(f"缺少URL的新闻数量: {total_articles - len(unique_urls)} 条")
    
    print("\n" + "=" * 80)
    print("数据质量评估")
    print("=" * 80)
    
    url_coverage = (len(unique_urls) / total_articles) * 100
    print(f"URL覆盖率: {url_coverage:.2f}%")
    
    if url_coverage < 50:
        print("⚠️  警告: URL覆盖率较低，建议补充URL信息以提高数据质量")
    else:
        print("✓ URL覆盖率良好")

if __name__ == "__main__":
    main()