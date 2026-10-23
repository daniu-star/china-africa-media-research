#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合所有results文件中的数据到results_5.json
"""

import json
import os
from pathlib import Path

def merge_results_files():
    """整合所有results文件到results_5.json"""
    
    # 定义结果文件路径
    results_dir = Path("data/results")
    target_file = results_dir / "results_5.json"
    
    # 获取所有results文件
    results_files = sorted([f for f in results_dir.glob("results_*.json") if f.name != "results_5.json"])
    
    print(f"找到 {len(results_files)} 个results文件需要整合")
    
    # 读取所有数据
    all_data = []
    
    for file_path in results_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data.extend(data)
                print(f"从 {file_path.name} 读取了 {len(data)} 条记录")
        except Exception as e:
            print(f"读取 {file_path} 时出错: {e}")
    
    # 读取外.json文件
    external_file = results_dir / "外.json"
    if external_file.exists():
        try:
            with open(external_file, 'r', encoding='utf-8') as f:
                external_data = json.load(f)
                all_data.extend(external_data)
                print(f"从 外.json 读取了 {len(external_data)} 条记录")
        except Exception as e:
            print(f"读取 外.json 时出错: {e}")
    
    # 去重处理（基于task_id）
    unique_data = {}
    for item in all_data:
        task_id = item.get('task_id')
        if task_id not in unique_data:
            unique_data[task_id] = item
        else:
            # 如果已存在，比较时间戳，保留最新的
            existing_time = unique_data[task_id].get('processed_at', '')
            new_time = item.get('processed_at', '')
            if new_time > existing_time:
                unique_data[task_id] = item
    
    # 转换为列表
    final_data = list(unique_data.values())
    
    print(f"整合后共有 {len(final_data)} 条唯一记录")
    
    # 统计成功爬取的数据
    successful_data = [item for item in final_data if item.get('results') and len(item['results']) > 0]
    print(f"其中成功爬取的数据有 {len(successful_data)} 条")
    
    # 按处理时间排序（处理可能的类型不一致问题）
    def get_sort_key(item):
        processed_at = item.get('processed_at', '')
        if isinstance(processed_at, str):
            return processed_at
        return str(processed_at)
    
    final_data.sort(key=get_sort_key)
    
    # 写入results_5.json
    try:
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        print(f"数据已成功整合到 {target_file}")
        
        # 生成统计信息
        generate_statistics(final_data)
        
    except Exception as e:
        print(f"写入 {target_file} 时出错: {e}")

def generate_statistics(data):
    """生成数据统计信息"""
    
    print("\n=== 数据统计信息 ===")
    print(f"总任务数: {len(data)}")
    
    # 成功爬取的任务统计
    successful_tasks = [item for item in data if item.get('results') and len(item['results']) > 0]
    print(f"成功爬取的任务数: {len(successful_tasks)}")
    
    # 按关键词语言分类统计
    language_stats = {}
    for item in data:
        keyword = item.get('keyword', '')
        if 'china' in keyword.lower() or 'chinese' in keyword.lower():
            lang = '英文'
        elif any(word in keyword.lower() for word in ['zulu', 'swahili', 'amharic']):
            lang = '非洲语言'
        else:
            lang = '中文'
        
        if lang not in language_stats:
            language_stats[lang] = 0
        language_stats[lang] += 1
    
    print("\n按语言分类统计:")
    for lang, count in language_stats.items():
        print(f"  {lang}: {count} 个任务")
    
    # 按年份统计
    year_stats = {}
    for item in data:
        year = item.get('year', '未知')
        if year not in year_stats:
            year_stats[year] = 0
        year_stats[year] += 1
    
    print("\n按年份统计:")
    # 处理年份类型不一致问题
    try:
        for year, count in sorted(year_stats.items(), key=lambda x: str(x[0])):
            print(f"  {year}: {count} 个任务")
    except:
        for year, count in year_stats.items():
            print(f"  {year}: {count} 个任务")
    
    # 数据质量统计
    total_articles = sum(item.get('quality_stats', {}).get('total_articles', 0) for item in data)
    valid_articles = sum(item.get('quality_stats', {}).get('valid_articles', 0) for item in data)
    
    print(f"\n数据质量统计:")
    print(f"  总爬取文章数: {total_articles}")
    print(f"  有效文章数: {valid_articles}")
    print(f"  有效率: {valid_articles/total_articles*100:.1f}%" if total_articles > 0 else "  有效率: 0%")

if __name__ == "__main__":
    merge_results_files()