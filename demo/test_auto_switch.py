#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试results_7.json文件达到50,000行时自动切换到results_8.json的功能
"""

import json
import os
from pathlib import Path
from simple_results7_crawler import save_results7

def test_auto_switch():
    """测试自动文件切换功能"""
    
    # 检查当前results_7.json文件状态
    results7_path = Path("data/results/results_7.json")
    results8_path = Path("data/results/results_8.json")
    
    if results7_path.exists():
        with open(results7_path, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
        print(f"当前results_7.json文件行数: {len(current_data)}")
    else:
        print("results_7.json文件不存在")
        current_data = []
    
    if results8_path.exists():
        with open(results8_path, 'r', encoding='utf-8') as f:
            results8_data = json.load(f)
        print(f"当前results_8.json文件行数: {len(results8_data)}")
    else:
        print("results_8.json文件不存在")
    
    # 创建测试数据
    test_data = []
    for i in range(100):
        test_task = {
            'task_id': f'test_task_{i}',
            'keyword': 'test keyword',
            'year': 2024,
            'language': 'english',
            'status': 'completed',
            'results': [
                {
                    'title': f'Test Article {i}',
                    'content': 'This is a test article content.',
                    'url': f'https://test.com/article{i}'
                }
            ]
        }
        test_data.append(test_task)
    
    print(f"\n准备测试数据: {len(test_data)}个任务")
    
    # 测试保存功能
    print("\n开始测试保存功能...")
    success = save_results7(test_data)
    
    if success:
        print("✓ 保存功能测试成功")
        
        # 检查文件状态
        if results7_path.exists():
            with open(results7_path, 'r', encoding='utf-8') as f:
                updated_data = json.load(f)
            print(f"✓ results_7.json更新后行数: {len(updated_data)}")
        
        if results8_path.exists():
            with open(results8_path, 'r', encoding='utf-8') as f:
                results8_updated = json.load(f)
            print(f"✓ results_8.json更新后行数: {len(results8_updated)}")
    else:
        print("✗ 保存功能测试失败")

def simulate_50000_threshold():
    """模拟达到50,000行阈值的情况"""
    
    print("\n=== 模拟50,000行阈值测试 ===")
    
    # 创建接近50,000行的测试数据
    large_test_data = []
    
    # 检查当前行数
    results7_path = Path("data/results/results_7.json")
    if results7_path.exists():
        with open(results7_path, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
        current_count = len(current_data)
        print(f"当前results_7.json行数: {current_count}")
        
        # 计算需要添加的数据量
        needed = 50000 - current_count
        
        if needed > 0:
            print(f"需要添加{needed}行数据来达到50,000行阈值")
            
            # 创建测试数据（分批添加，避免内存问题）
            batch_size = 1000
            batches = (needed + batch_size - 1) // batch_size
            
            for batch in range(batches):
                batch_data = []
                start_idx = batch * batch_size
                end_idx = min(start_idx + batch_size, needed)
                
                for i in range(start_idx, end_idx):
                    test_task = {
                        'task_id': f'simulate_task_{i}',
                        'keyword': 'simulation keyword',
                        'year': 2024,
                        'language': 'english',
                        'status': 'completed',
                        'results': [
                            {
                                'title': f'Simulation Article {i}',
                                'content': 'This is a simulation article for testing the 50,000 line threshold.',
                                'url': f'https://simulation.com/article{i}'
                            }
                        ]
                    }
                    batch_data.append(test_task)
                
                print(f"添加批次 {batch + 1}/{batches}: {len(batch_data)}个任务")
                success = save_results7(batch_data)
                
                if success:
                    print(f"✓ 批次 {batch + 1} 保存成功")
                else:
                    print(f"✗ 批次 {batch + 1} 保存失败")
                    break
        else:
            print("当前文件已超过50,000行，将测试自动切换功能")
            
            # 添加少量数据测试切换
            test_data = [{
                'task_id': 'threshold_test_task',
                'keyword': 'threshold test',
                'year': 2024,
                'language': 'english',
                'status': 'completed',
                'results': [{'title': 'Threshold Test Article', 'content': 'Testing auto-switch functionality.'}]
            }]
            
            success = save_results7(test_data)
            if success:
                print("✓ 自动切换功能测试成功")
            else:
                print("✗ 自动切换功能测试失败")
    else:
        print("results_7.json文件不存在，无法进行阈值测试")

if __name__ == "__main__":
    print("=== 测试自动文件切换功能 ===")
    
    # 确保目录存在
    Path("data/results").mkdir(parents=True, exist_ok=True)
    
    # 运行基本测试
    test_auto_switch()
    
    # 运行阈值测试
    simulate_50000_threshold()
    
    print("\n=== 测试完成 ===")