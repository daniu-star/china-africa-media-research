#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确统计修复后的JSON文件数据条数
"""

import json
import os

def count_data_in_file(file_path):
    """统计单个JSON文件中的数据条数"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return len(data)
        else:
            return 1  # 如果是单个对象
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return 0

def analyze_data_structure(file_path):
    """分析数据结构"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            print(f"\n文件 {os.path.basename(file_path)} 数据结构分析:")
            print(f"- 数据类型: 列表，包含 {len(data)} 个对象")
            print(f"- 第一个对象的字段: {list(first_item.keys())}")
            
            # 统计有内容的字段
            content_fields = []
            for key, value in first_item.items():
                if value and str(value).strip():
                    content_fields.append(key)
            
            print(f"- 有内容的字段: {content_fields}")
            
            # 检查是否有文章数据
            if 'articles' in first_item:
                articles = first_item.get('articles', [])
                print(f"- articles字段包含 {len(articles)} 篇文章")
            else:
                print("- 没有articles字段，数据为直接爬取的内容")
                
            # 统计关键词分布
            keywords = {}
            years = {}
            sources = {}
            
            for item in data[:100]:  # 只检查前100条避免性能问题
                keyword = item.get('keyword', 'unknown')
                year = item.get('year', 'unknown')
                source = item.get('source', 'unknown')
                
                keywords[keyword] = keywords.get(keyword, 0) + 1
                years[year] = years.get(year, 0) + 1
                sources[source] = sources.get(source, 0) + 1
            
            print(f"- 关键词分布 (前5): {dict(list(keywords.items())[:5])}")
            print(f"- 年份分布 (前5): {dict(list(years.items())[:5])}")
            print(f"- 来源分布 (前5): {dict(list(sources.items())[:5])}")
            
    except Exception as e:
        print(f"分析文件 {file_path} 结构时出错: {e}")

def main():
    files_to_check = [
        "c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\data\\results_0.json.backup",
        "c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\data\\results_1.json"
    ]
    
    total_records = 0
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            count = count_data_in_file(file_path)
            total_records += count
            print(f"文件 {os.path.basename(file_path)}: {count:,} 条记录")
            
            # 分析数据结构
            analyze_data_structure(file_path)
        else:
            print(f"文件 {file_path} 不存在")
    
    print(f"\n{'='*60}")
    print(f"总计: {total_records:,} 条记录")
    print(f"{'='*60}")
    
    # 显示文件大小信息
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"{os.path.basename(file_path)} 文件大小: {size_mb:.2f} MB")

if __name__ == "__main__":
    main()