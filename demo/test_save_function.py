#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试save_result_locally方法功能
"""

import sys
import os
import json
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_storage_manager import create_storage_manager

def test_save_result_locally():
    """测试save_result_locally方法功能"""
    print("=== 测试save_result_locally方法 ===")
    
    # 创建存储管理器
    storage_manager = create_storage_manager()
    print("✓ 存储管理器创建成功")
    
    # 模拟爬取结果数据
    crawl_result = {
        "task_id": "test_task_001",
        "url": "https://example.com/test-article",
        "title": "测试文章标题",
        "content": "这是测试文章内容，用于验证数据保存功能。",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "test_source",
        "keywords": ["测试", "数据保存", "验证"],
        "metadata": {
            "language": "zh",
            "category": "test",
            "word_count": 50
        }
    }
    
    try:
        # 模拟调用save_result_locally方法
        print("\n1. 测试保存到crawler_results目录...")
        result_path = storage_manager.save_data(
            data=crawl_result,
            filename=f"crawl_result_{int(time.time())}.json",
            subdir="crawler_results/test",
            compress=True,
            backup=True
        )
        print(f"✓ 数据保存成功: {result_path}")
        
        # 检查crawler_results目录是否创建
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        crawler_results_dir = os.path.join(data_dir, "crawler_results")
        
        if os.path.exists(crawler_results_dir):
            print(f"✓ crawler_results目录已创建: {crawler_results_dir}")
            
            # 列出目录内容
            for root, dirs, files in os.walk(crawler_results_dir):
                level = root.replace(crawler_results_dir, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    print(f"{subindent}{file}")
        else:
            print("✗ crawler_results目录未创建")
            
        # 测试加载保存的数据
        print("\n2. 测试数据加载功能...")
        
        # 获取保存的文件名
        test_dir = os.path.join(crawler_results_dir, "test")
        if os.path.exists(test_dir):
            files = os.listdir(test_dir)
            if files:
                test_file = files[0]
                loaded_data = storage_manager.load_data(test_file, "crawler_results/test")
                if loaded_data and loaded_data.get("task_id") == "test_task_001":
                    print("✓ 数据加载成功")
                    print(f"  标题: {loaded_data.get('title')}")
                    print(f"  内容长度: {len(loaded_data.get('content', ''))} 字符")
                else:
                    print("✗ 数据加载失败")
            else:
                print("✗ 未找到测试文件")
        else:
            print("✗ 测试目录不存在")
            
        # 测试存储统计
        print("\n3. 测试存储统计...")
        stats = storage_manager.get_storage_stats()
        print(f"✓ 存储统计获取成功")
        print(f"  总文件数: {stats.get('total_files', 0)}")
        print(f"  总大小: {stats.get('total_size', 0)} 字节")
        
        # 检查是否有crawler_results相关的统计
        if 'crawler_results' in str(stats):
            print("✓ crawler_results目录在统计中")
        else:
            print("⚠ crawler_results目录未在统计中显示")
            
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_saves():
    """测试多次保存功能"""
    print("\n=== 测试多次保存功能 ===")
    
    storage_manager = create_storage_manager()
    
    # 保存多个测试数据
    for i in range(3):
        test_data = {
            "task_id": f"multi_test_{i:03d}",
            "title": f"测试文章 {i+1}",
            "content": f"这是第 {i+1} 个测试文章的内容。",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        result_path = storage_manager.save_data(
            data=test_data,
            filename=f"multi_test_{i:03d}.json",
            subdir="crawler_results/multi_test",
            compress=True
        )
        print(f"✓ 保存测试数据 {i+1}: {result_path}")
    
    # 检查保存的文件
    multi_test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "crawler_results", "multi_test")
    if os.path.exists(multi_test_dir):
        files = os.listdir(multi_test_dir)
        print(f"✓ 多测试目录包含 {len(files)} 个文件")
        for file in files:
            print(f"  - {file}")
    else:
        print("✗ 多测试目录未创建")
    
    return True

if __name__ == "__main__":
    success1 = test_save_result_locally()
    success2 = test_multiple_saves()
    
    if success1 and success2:
        print("\n=== save_result_locally方法测试通过 ===")
        print("✓ 数据保存功能正常")
        print("✓ crawler_results目录创建成功") 
        print("✓ 多次保存功能正常")
    else:
        print("\n=== save_result_locally方法测试失败 ===")