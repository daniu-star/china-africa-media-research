#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容质量分析脚本
分析现有数据中的登录页面和内容截断问题
"""

import json
import re
import os

def analyze_content_quality():
    """分析数据文件中的内容质量问题"""
    
    # 加载数据文件
    data_file = 'data/results_enhanced_with_dates.json'
    if not os.path.exists(data_file):
        print(f'错误: 数据文件 {data_file} 不存在')
        return
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data_dict = json.load(f)
    except Exception as e:
        print(f'加载数据文件失败: {e}')
        return
    
    # 获取文章列表
    if 'articles' not in data_dict:
        print('错误: 数据文件中没有articles键')
        return
    
    data = data_dict['articles']
    
    print('=== 内容质量分析报告 ===')
    print(f'总文章数: {len(data)}')
    
    # 检测登录页面内容
    login_patterns = [
        r'sign\s*in', r'log\s*in', r'login', r'username', r'password', 
        r'forgot\s*password', r'get\s*help', r'welcome', r'account'
    ]
    
    login_articles = []
    for article in data:
        content = article.get('content', '').lower()
        for pattern in login_patterns:
            if re.search(pattern, content):
                login_articles.append({
                    'title': article.get('title', ''),
                    'source': article.get('source', ''),
                    'content_preview': content[:200]
                })
                break
    
    print(f'检测到登录页面内容: {len(login_articles)} 篇')
    if login_articles:
        print('前5篇登录页面文章:')
        for i, article in enumerate(login_articles[:5]):
            print(f'{i+1}. 标题: {article["title"]}')
            print(f'   来源: {article["source"]}')
            print(f'   内容预览: {article["content_preview"]}')
            print()
    
    # 检测内容截断问题
    truncated_articles = []
    for article in data:
        content = article.get('content', '')
        if len(content) < 100:  # 内容过短
            truncated_articles.append({
                'title': article.get('title', ''),
                'source': article.get('source', ''),
                'content_length': len(content)
            })
    
    print(f'检测到内容截断问题: {len(truncated_articles)} 篇（内容长度<100字符）')
    if truncated_articles:
        print('前5篇截断文章:')
        for i, article in enumerate(truncated_articles[:5]):
            print(f'{i+1}. 标题: {article["title"]}')
            print(f'   来源: {article["source"]}')
            print(f'   内容长度: {article["content_length"]}')
            print()
    
    # 检测省略号问题
    ellipsis_articles = []
    for article in data:
        content = article.get('content', '')
        if '...' in content or '…' in content:
            ellipsis_articles.append({
                'title': article.get('title', ''),
                'source': article.get('source', ''),
                'content_preview': content[:200]
            })
    
    print(f'检测到省略号问题: {len(ellipsis_articles)} 篇')
    if ellipsis_articles:
        print('前5篇省略号文章:')
        for i, article in enumerate(ellipsis_articles[:5]):
            print(f'{i+1}. 标题: {article["title"]}')
            print(f'   来源: {article["source"]}')
            print(f'   内容预览: {article["content_preview"]}')
            print()
    
    # 内容长度分布分析
    content_lengths = [len(article.get('content', '')) for article in data]
    avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
    max_length = max(content_lengths) if content_lengths else 0
    min_length = min(content_lengths) if content_lengths else 0
    
    print(f'内容长度统计:')
    print(f'  平均长度: {avg_length:.1f} 字符')
    print(f'  最大长度: {max_length} 字符')
    print(f'  最小长度: {min_length} 字符')
    
    # 长度分布
    length_ranges = [
        (0, 100, "极短"),
        (100, 500, "短"),
        (500, 1000, "中等"),
        (1000, 2000, "长"),
        (2000, float('inf'), "极长")
    ]
    
    print('内容长度分布:')
    for min_len, max_len, label in length_ranges:
        count = sum(1 for length in content_lengths if min_len <= length < max_len)
        percentage = (count / len(data)) * 100 if data else 0
        max_str = "∞" if max_len == float('inf') else str(max_len)
        print(f'  {label} ({min_len}-{max_str}字符): {count} 篇 ({percentage:.1f}%)')

if __name__ == '__main__':
    analyze_content_quality()