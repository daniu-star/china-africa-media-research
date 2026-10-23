#!/usr/bin/env python3
"""
清理和合并数据脚本
删除results_7.json中的模拟数据，合并real_results_7.json中的真实数据
"""

import json
import os
from datetime import datetime

def clean_and_merge_data():
    # 文件路径
    results_file = "data/results/results_7.json"
    real_results_file = "data/results/real_results_7.json"
    
    # 备份原文件
    backup_file = f"data/results/results_7_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    print("=== 数据清理和合并开始 ===")
    
    # 检查文件是否存在
    if not os.path.exists(results_file):
        print(f"错误: {results_file} 不存在")
        return
    
    if not os.path.exists(real_results_file):
        print(f"错误: {real_results_file} 不存在")
        return
    
    # 备份原文件
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            original_data = f.read()
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(original_data)
        print(f"✓ 已备份原文件到: {backup_file}")
    except Exception as e:
        print(f"✗ 备份失败: {e}")
        return
    
    # 读取原数据
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            original_results = json.load(f)
        print(f"✓ 读取原数据: {len(original_results)} 条记录")
    except Exception as e:
        print(f"✗ 读取原数据失败: {e}")
        return
    
    # 读取真实数据
    try:
        with open(real_results_file, 'r', encoding='utf-8') as f:
            real_results = json.load(f)
        print(f"✓ 读取真实数据: {len(real_results)} 条记录")
    except Exception as e:
        print(f"✗ 读取真实数据失败: {e}")
        return
    
    # 识别和删除模拟数据
    # 模拟数据特征: crawl_method为"simulated-real-data"，URL包含"africanews.com"
    cleaned_results = []
    simulated_count = 0
    
    for result in original_results:
        if result.get('crawl_method') == 'simulated-real-data':
            simulated_count += 1
            continue
        
        # 检查URL是否包含模拟特征
        has_simulated_url = False
        for article in result.get('results', []):
            if 'africanews.com' in article.get('url', ''):
                has_simulated_url = True
                break
        
        if has_simulated_url:
            simulated_count += 1
            continue
        
        cleaned_results.append(result)
    
    print(f"✓ 删除模拟数据: {simulated_count} 条")
    print(f"✓ 保留真实数据: {len(cleaned_results)} 条")
    
    # 合并真实数据
    # 创建任务ID集合以避免重复
    existing_task_ids = {result['task_id'] for result in cleaned_results}
    
    merged_count = 0
    for real_result in real_results:
        if real_result['task_id'] not in existing_task_ids:
            cleaned_results.append(real_result)
            merged_count += 1
    
    print(f"✓ 合并新数据: {merged_count} 条")
    print(f"✓ 最终数据量: {len(cleaned_results)} 条")
    
    # 保存清理后的数据
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_results, f, ensure_ascii=False, indent=2)
        print(f"✓ 数据已保存到: {results_file}")
    except Exception as e:
        print(f"✗ 保存失败: {e}")
        return
    
    # 验证保存结果
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        print(f"✓ 验证保存: {len(saved_data)} 条记录")
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        return
    
    print("=== 数据清理和合并完成 ===")
    print(f"最终数据文件: {results_file}")
    print(f"备份文件: {backup_file}")
    print(f"真实数据源: {real_results_file}")

if __name__ == "__main__":
    clean_and_merge_data()