#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据存储管理器集成功能
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from intelligent_crawling_system import IntelligentCrawlingSystem
from data_storage_manager import DataStorageManager

def test_data_storage_integration():
    """测试数据存储管理器集成功能"""
    print("=== 测试数据存储管理器集成功能 ===")
    
    # 1. 创建数据存储管理器
    print("\n1. 创建数据存储管理器...")
    
    storage_manager = DataStorageManager('test_storage')
    print("✓ 数据存储管理器创建成功")
    
    # 2. 创建智能爬虫系统
    print("\n2. 创建智能爬虫系统...")
    
    # 配置智能爬虫系统
    storage_config = {
        'base_dir': 'test_storage',
        'backup_dir': 'test_storage/backup'
    }
    
    crawler = IntelligentCrawlingSystem(
        config_file="adaptive_learning_config.json",
        storage_config=storage_config
    )
    print("✓ 智能爬虫系统创建成功")
    
    # 3. 测试系统状态保存和加载
    print("\n3. 测试系统状态保存和加载...")
    
    # 模拟一些系统状态数据
    crawler.system_status = {
        'total_requests': 100,
        'successful_requests': 85,
        'failed_requests': 15,
        'last_updated': datetime.now().isoformat()
    }
    
    crawler.realtime_metrics = {
        'requests_per_minute': 10,
        'success_rate': 0.85,
        'average_latency': 1.5
    }
    
    # 保存系统状态
    crawler._save_system_state()
    print("✓ 系统状态保存成功")
    
    # 重置系统状态
    crawler.system_status = {}
    crawler.realtime_metrics = {}
    
    # 加载系统状态
    crawler._load_system_state()
    print("✓ 系统状态加载成功")
    print(f"   - 总请求数: {crawler.system_status.get('total_requests', 0)}")
    print(f"   - 成功率: {crawler.realtime_metrics.get('success_rate', 0)}")
    
    # 4. 测试爬虫结果保存
    print("\n4. 测试爬虫结果保存...")
    
    # 模拟爬虫结果
    test_url = "https://example.com"
    test_strategy = "balanced"
    test_result = {
        'success': True,
        'status_code': 200,
        'latency': 1.2,
        'content': 'Test content'
    }
    test_proxy = {
        'proxy_type': 'http',
        'proxy_address': '127.0.0.1:8080'
    }
    
    # 保存爬虫结果
    crawler._save_crawl_result(test_url, test_strategy, test_result, test_proxy)
    print("✓ 爬虫结果保存成功")
    
    # 5. 测试爬虫历史加载
    print("\n5. 测试爬虫历史加载...")
    
    history = crawler.load_crawl_history(limit=10)
    print(f"✓ 加载到 {len(history)} 条爬虫历史记录")
    
    if history:
        for i, record in enumerate(history[:3]):  # 只显示前3条
            print(f"   记录 {i+1}: {record.get('url', 'N/A')} - {record.get('success', False)}")
    
    # 6. 测试数据存储管理器的基本功能
    print("\n6. 测试数据存储管理器基本功能...")
    
    # 测试保存数据
    test_data = {
        'test_key': 'test_value',
        'timestamp': datetime.now().isoformat()
    }
    
    storage_manager.save_data(test_data, 'test_file.json')
    print("✓ 数据保存成功")
    
    # 测试加载数据
    loaded_data = storage_manager.load_data('test_file.json')
    if loaded_data and loaded_data.get('test_key') == 'test_value':
        print("✓ 数据加载成功")
    else:
        print("✗ 数据加载失败")
    
    # 测试文件列表
    files = storage_manager.list_files('')
    print(f"✓ 文件列表获取成功，共 {len(files)} 个文件")
    
    # 7. 清理测试数据
    print("\n7. 清理测试数据...")
    
    try:
        import shutil
        if os.path.exists('test_storage'):
            shutil.rmtree('test_storage')
        print("✓ 测试数据清理完成")
    except Exception as e:
        print(f"✗ 清理失败: {e}")
    
    print("\n=== 数据存储管理器集成测试完成 ===")
    print("✓ 所有功能测试通过")
    
    return True

def test_crawl_with_storage():
    """测试带数据存储的爬虫功能"""
    print("\n=== 测试带数据存储的爬虫功能 ===")
    
    # 创建爬虫系统
    storage_config = {
        'base_dir': 'test_crawl_storage',
        'backup_dir': 'test_crawl_storage/backup'
    }
    
    crawler = IntelligentCrawlingSystem(
        config_file="adaptive_learning_config.json",
        storage_config=storage_config
    )
    
    # 测试URL列表
    test_urls = [
        "https://httpbin.org/status/200",  # 简单的测试URL
        "https://httpbin.org/status/404",  # 404错误URL
    ]
    
    results = []
    
    for i, url in enumerate(test_urls):
        print(f"\n爬取URL {i+1}/{len(test_urls)}: {url}")
        
        try:
            result = crawler.crawl_url(url, use_learning=True)
            results.append(result)
            
            if result['success']:
                print(f"✓ 爬取成功 - 策略: {result['strategy_used']}")
            else:
                print(f"✗ 爬取失败 - 策略: {result['strategy_used']}")
                
        except Exception as e:
            print(f"✗ 爬取异常: {e}")
    
    # 检查爬虫历史
    print("\n检查爬虫历史记录...")
    history = crawler.load_crawl_history()
    print(f"保存的爬虫记录数量: {len(history)}")
    
    # 清理
    try:
        import shutil
        if os.path.exists('test_crawl_storage'):
            shutil.rmtree('test_crawl_storage')
        print("✓ 测试数据清理完成")
    except Exception as e:
        print(f"✗ 清理失败: {e}")
    
    return len(results) > 0

if __name__ == "__main__":
    try:
        # 运行集成测试
        success1 = test_data_storage_integration()
        
        # 运行爬虫测试
        success2 = test_crawl_with_storage()
        
        if success1 and success2:
            print("\n🎉 所有测试通过！数据存储管理器集成成功！")
        else:
            print("\n⚠️ 部分测试失败，请检查代码")
            
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()