#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证：测试超过50,000行时数据是否自动保存到results_8.json
"""

import json
import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_results7_crawler import save_results7

def create_verification_data(num_items=1000):
    """创建验证数据"""
    test_data = []
    for i in range(num_items):
        test_data.append({
            "id": f"verify_{i}",
            "title": f"验证文章 {i}",
            "content": f"这是验证文章 {i} 的内容，用于验证自动切换到results_8.json",
            "source": "final_verification",
            "timestamp": "2024-01-01 00:00:00"
        })
    return test_data

def check_file_status():
    """检查文件状态"""
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
    """主验证函数"""
    print("=== 最终验证：测试自动文件切换功能 ===\n")
    
    # 确保数据目录存在
    Path("data/results").mkdir(parents=True, exist_ok=True)
    
    # 检查当前状态
    count7, count8 = check_file_status()
    print(f"当前状态:")
    print(f"  results_7.json: {count7} 个任务")
    print(f"  results_8.json: {count8} 个任务")
    
    if count7 >= 50000:
        print("\n✅ results_7.json已经达到50,000行阈值")
        print("   现在测试添加新数据是否会自动保存到results_8.json...\n")
        
        # 创建验证数据
        test_data = create_verification_data(100)
        
        # 保存数据（应该自动切换到results_8.json）
        success = save_results7(test_data)
        
        if success:
            # 检查更新后的状态
            new_count7, new_count8 = check_file_status()
            
            print("✅ 数据保存成功！")
            print(f"  更新后状态:")
            print(f"    results_7.json: {new_count7} 个任务")
            print(f"    results_8.json: {new_count8} 个任务")
            
            # 验证自动切换是否生效
            if new_count7 == count7 and new_count8 > count8:
                print("\n🎉 验证成功！自动文件切换功能正常工作！")
                print("   当results_7.json达到50,000行后，新数据确实自动保存到了results_8.json")
                print(f"   新增了 {new_count8 - count8} 个任务到results_8.json")
            else:
                print("\n⚠ 验证结果异常，请检查自动切换逻辑")
        else:
            print("✗ 数据保存失败")
    else:
        print(f"\n⚠ results_7.json尚未达到50,000行阈值（当前: {count7} 行）")
        print("   请先运行阈值测试脚本使results_7.json达到50,000行")

if __name__ == "__main__":
    main()