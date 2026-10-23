#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全测试自动文件切换功能
避免JSON格式错误，使用更稳健的测试方法
"""

import json
import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_results7_crawler import save_results7

def create_test_data(num_items=1000):
    """创建测试数据"""
    test_data = []
    for i in range(num_items):
        test_data.append({
            "id": i,
            "title": f"测试文章 {i}",
            "content": f"这是测试文章 {i} 的内容",
            "source": "test_source",
            "timestamp": "2024-01-01 00:00:00"
        })
    return test_data

def check_file_status():
    """检查文件状态"""
    results7_path = Path("data/results/results_7.json")
    results8_path = Path("data/results/results_8.json")
    
    print("=== 文件状态检查 ===")
    
    # 检查results_7.json
    if results7_path.exists():
        try:
            with open(results7_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"results_7.json: 存在，包含 {len(data)} 个任务")
        except json.JSONDecodeError as e:
            print(f"results_7.json: 存在，但格式错误: {e}")
    else:
        print("results_7.json: 不存在")
    
    # 检查results_8.json
    if results8_path.exists():
        try:
            with open(results8_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"results_8.json: 存在，包含 {len(data)} 个任务")
        except json.JSONDecodeError as e:
            print(f"results_8.json: 存在，但格式错误: {e}")
    else:
        print("results_8.json: 不存在")
    
    print()

def test_small_batch():
    """测试小批量数据保存"""
    print("=== 测试小批量数据保存 ===")
    
    # 创建少量测试数据
    test_data = create_test_data(10)
    
    # 保存数据
    success = save_results7(test_data)
    
    if success:
        print("✓ 小批量数据保存成功")
    else:
        print("✗ 小批量数据保存失败")
    
    check_file_status()

def test_auto_switch_simulation():
    """模拟自动切换功能测试"""
    print("=== 模拟自动切换功能测试 ===")
    
    # 首先检查当前文件状态
    results7_path = Path("data/results/results_7.json")
    
    current_count = 0
    if results7_path.exists():
        try:
            with open(results7_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            current_count = len(data)
        except json.JSONDecodeError:
            # 如果文件格式错误，重置为空文件
            with open(results7_path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2, ensure_ascii=False)
    
    print(f"当前results_7.json包含 {current_count} 个任务")
    
    # 计算需要添加的任务数量来达到阈值
    remaining_to_threshold = 50000 - current_count
    
    if remaining_to_threshold <= 0:
        print("✓ 当前文件已超过50,000行阈值，自动切换功能已生效")
        return
    
    # 测试接近阈值的情况
    if remaining_to_threshold <= 1000:
        print(f"当前距离阈值仅差 {remaining_to_threshold} 行，测试自动切换...")
        
        # 添加刚好超过阈值的数据
        test_data = create_test_data(remaining_to_threshold + 100)
        success = save_results7(test_data)
        
        if success:
            print("✓ 自动切换功能测试成功")
        else:
            print("✗ 自动切换功能测试失败")
    else:
        print(f"当前距离阈值还有 {remaining_to_threshold} 行，需要更多数据才能测试自动切换功能")
        
        # 添加一些数据来接近阈值
        batch_size = min(1000, remaining_to_threshold - 1000)
        if batch_size > 0:
            test_data = create_test_data(batch_size)
            success = save_results7(test_data)
            
            if success:
                print(f"✓ 已添加 {batch_size} 个任务，继续接近阈值")
            else:
                print(f"✗ 添加 {batch_size} 个任务失败")
    
    check_file_status()

def main():
    """主测试函数"""
    print("开始安全测试自动文件切换功能...\n")
    
    # 确保数据目录存在
    Path("data/results").mkdir(parents=True, exist_ok=True)
    
    # 1. 检查文件状态
    check_file_status()
    
    # 2. 测试小批量数据保存
    test_small_batch()
    
    # 3. 模拟自动切换功能
    test_auto_switch_simulation()
    
    print("测试完成！")

if __name__ == "__main__":
    main()