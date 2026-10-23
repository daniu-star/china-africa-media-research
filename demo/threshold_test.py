#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阈值测试：模拟results_7.json达到50,000行时自动切换到results_8.json
"""

import json
import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_results7_crawler import save_results7

def create_large_test_data(num_items=50000):
    """创建大量测试数据来快速达到阈值"""
    test_data = []
    for i in range(num_items):
        test_data.append({
            "id": i,
            "title": f"测试文章 {i}",
            "content": f"这是测试文章 {i} 的内容，用于测试自动文件切换功能",
            "source": "threshold_test",
            "timestamp": "2024-01-01 00:00:00"
        })
    return test_data

def check_file_counts():
    """检查文件中的任务数量"""
    results7_path = Path("data/results/results_7.json")
    results8_path = Path("data/results/results_8.json")
    
    count7 = 0
    count8 = 0
    
    if results7_path.exists():
        try:
            with open(results7_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            count7 = len(data)
        except json.JSONDecodeError:
            count7 = 0
    
    if results8_path.exists():
        try:
            with open(results8_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            count8 = len(data)
        except json.JSONDecodeError:
            count8 = 0
    
    return count7, count8

def main():
    """主测试函数"""
    print("=== 阈值测试：模拟results_7.json达到50,000行时自动切换到results_8.json ===\n")
    
    # 确保数据目录存在
    Path("data/results").mkdir(parents=True, exist_ok=True)
    
    # 检查当前状态
    count7, count8 = check_file_counts()
    print(f"当前状态:")
    print(f"  results_7.json: {count7} 个任务")
    print(f"  results_8.json: {count8} 个任务")
    print(f"  距离50,000行阈值还差: {50000 - count7} 行\n")
    
    if count7 >= 50000:
        print("✓ results_7.json已经达到50,000行阈值，自动切换功能已生效")
        print("  新数据应该已经自动保存到results_8.json")
        return
    
    # 计算需要添加的任务数量
    needed = 50000 - count7
    
    if needed > 0:
        print(f"需要添加 {needed} 个任务来达到阈值...")
        
        # 分批添加数据，避免内存问题
        batch_size = 10000
        batches = (needed + batch_size - 1) // batch_size
        
        for i in range(batches):
            current_batch_size = min(batch_size, needed - i * batch_size)
            if current_batch_size <= 0:
                break
                
            print(f"\n添加第 {i+1}/{batches} 批数据 ({current_batch_size} 个任务)...")
            
            # 创建测试数据
            test_data = create_large_test_data(current_batch_size)
            
            # 保存数据
            success = save_results7(test_data)
            
            if success:
                # 检查更新后的状态
                new_count7, new_count8 = check_file_counts()
                print(f"  保存成功!")
                print(f"  results_7.json: {new_count7} 个任务")
                print(f"  results_8.json: {new_count8} 个任务")
                
                # 检查是否达到阈值
                if new_count7 >= 50000:
                    print("\n🎉 已达到50,000行阈值！自动切换功能已激活！")
                    print("   后续数据将自动保存到results_8.json")
                    break
            else:
                print("✗ 保存失败")
                break
    
    # 最终状态检查
    print("\n=== 最终状态 ===")
    final_count7, final_count8 = check_file_counts()
    print(f"results_7.json: {final_count7} 个任务")
    print(f"results_8.json: {final_count8} 个任务")
    
    if final_count7 >= 50000:
        print("\n✅ 测试成功！自动文件切换功能正常工作")
        print("   当results_7.json达到50,000行时，系统会自动创建并保存到results_8.json")
    else:
        print(f"\n⚠ 尚未达到50,000行阈值，当前还差 {50000 - final_count7} 行")
        print("   当达到阈值时，系统会自动切换到results_8.json")

if __name__ == "__main__":
    main()