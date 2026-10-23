"""
Modern Ghana优化器集成测试脚本
测试Modern Ghana网站专用优化策略的集成效果
"""

import sys
import os
import time
import json

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modernghana_optimizer import ModernGhanaOptimizer

def test_modernghana_optimizer():
    """测试Modern Ghana优化器基本功能"""
    print("=== Modern Ghana优化器基本功能测试 ===")
    
    optimizer = ModernGhanaOptimizer()
    
    # 测试URL识别
    test_urls = [
        "https://www.modernghana.com/news/1234567/example-article",
        "https://modernghana.com/politics/9876543/news",
        "https://example.com/news/1234567/article",
        "https://www.ghanaweb.com/news/1234567/article"
    ]
    
    for url in test_urls:
        is_modernghana = optimizer.is_modernghana_url(url)
        print(f"URL: {url}")
        print(f"  是否为Modern Ghana网站: {is_modernghana}")
    
    print("\n=== 超时策略测试 ===")
    modernghana_url = "https://www.modernghana.com/news/1234567/example-article"
    
    for attempt in range(3):
        timeout = optimizer.calculate_smart_timeout(modernghana_url, attempt)
        print(f"重试{attempt}次 - 超时设置: {timeout}")
    
    print("\n=== 延迟策略测试 ===")
    for attempt in range(3):
        delay = optimizer.calculate_smart_delay(modernghana_url, attempt)
        print(f"重试{attempt}次 - 延迟设置: {delay:.2f}秒")
    
    print("\n=== 请求头测试 ===")
    headers = optimizer.get_optimized_headers(modernghana_url)
    print(f"Modern Ghana专用请求头: {json.dumps(headers, indent=2)}")
    
    print("\n=== 代理策略测试 ===")
    proxy_strategy = optimizer.get_proxy_strategy(modernghana_url)
    print(f"代理策略: {json.dumps(proxy_strategy, indent=2)}")

def test_performance_tracking():
    """测试性能跟踪功能"""
    print("\n=== 性能跟踪测试 ===")
    
    optimizer = ModernGhanaOptimizer()
    
    # 模拟一些请求结果
    test_results = [
        (True, 45.2, None),   # 成功请求，耗时45.2秒
        (False, 60.0, 'timeout'),  # 超时错误
        (True, 38.7, None),   # 成功请求
        (False, 15.3, 'connection'),  # 连接错误
        (True, 52.1, None),   # 成功请求
        (False, 75.8, 'timeout'),  # 超时错误
    ]
    
    for success, response_time, error_type in test_results:
        optimizer.update_performance_stats(success, response_time, error_type)
        print(f"更新统计: 成功={success}, 耗时={response_time}秒, 错误类型={error_type}")
    
    # 获取性能报告
    report = optimizer.get_performance_report()
    print(f"\n性能报告: {json.dumps(report, indent=2)}")

def test_integration_with_worker():
    """测试与工作节点的集成"""
    print("\n=== 工作节点集成测试 ===")
    
    try:
        from distributed_worker_fixed import DistributedWorker
        
        # 创建测试工作节点
        worker = DistributedWorker()
        
        # 测试Modern Ghana URL识别
        test_urls = [
            "https://www.modernghana.com/news/1234567/example-article",
            "https://example.com/news/1234567/article"
        ]
        
        for url in test_urls:
            is_modernghana = worker.modernghana_optimizer.is_modernghana_url(url)
            print(f"URL: {url}")
            print(f"  工作节点识别为Modern Ghana: {is_modernghana}")
            
            if is_modernghana:
                # 测试专用策略
                timeout = worker.modernghana_optimizer.calculate_smart_timeout(url)
                delay = worker.modernghana_optimizer.calculate_smart_delay(url)
                print(f"  专用超时策略: {timeout}")
                print(f"  专用延迟策略: {delay:.2f}秒")
        
        # 测试状态报告
        status = worker.get_status()
        print(f"\n工作节点状态包含Modern Ghana性能报告: {'modernghana_performance' in status}")
        
        if 'modernghana_performance' in status:
            print(f"Modern Ghana性能报告: {json.dumps(status['modernghana_performance'], indent=2)}")
        
    except Exception as e:
        print(f"集成测试失败: {e}")
        print("注意: 这可能是由于工作节点依赖的其他模块未正确配置")

def main():
    """主测试函数"""
    print("Modern Ghana优化器集成测试")
    print("=" * 50)
    
    # 测试基本功能
    test_modernghana_optimizer()
    
    # 测试性能跟踪
    test_performance_tracking()
    
    # 测试工作节点集成
    test_integration_with_worker()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    
    print("\n=== 优化策略总结 ===")
    print("1. Modern Ghana网站专用超时策略: 连接60秒, 读取120秒, 最大300秒")
    print("2. 智能重试机制: 最大重试8次, 指数退避延迟")
    print("3. 专用请求头: 加纳地区优化的浏览器指纹")
    print("4. 性能监控: 实时跟踪成功率、错误率、响应时间")
    print("5. 智能代理策略: 优先使用加纳及周边地区代理")

if __name__ == "__main__":
    main()