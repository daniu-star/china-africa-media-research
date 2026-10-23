#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能重试处理器集成测试脚本
测试SmartRetryHandler与非洲报纸爬虫的集成效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from african_newspaper_crawler import AfricanNewspaperCrawler
from smart_retry_handler import SmartRetryHandler
import logging

# 配置测试日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_smart_retry_handler_initialization():
    """测试SmartRetryHandler初始化"""
    print("=== 测试SmartRetryHandler初始化 ===")
    
    try:
        handler = SmartRetryHandler()
        print("✓ SmartRetryHandler初始化成功")
        
        # 测试错误分类
        from smart_retry_handler import ErrorCategory
        test_error = Exception("Connection refused")
        category = handler.classify_error(test_error, None, "http://test.com")
        print(f"✓ 错误分类测试成功: {category}")
        
        # 检查错误分类是否正确
        if category != ErrorCategory.CONNECTION:
            raise AssertionError(f"错误分类不正确，期望: CONNECTION，实际: {category}")
        
        # 测试错误统计更新
        handler.update_error_stats(category, True)
        print("✓ 错误统计更新测试成功")
        
        # 测试错误报告生成
        report = handler.get_error_report()
        print("✓ 错误报告生成测试成功")
        print(f"错误报告摘要: {report.get('summary', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"✗ SmartRetryHandler初始化测试失败: {e}")
        return False

def test_crawler_integration():
    """测试爬虫与SmartRetryHandler的集成"""
    print("\n=== 测试爬虫集成 ===")
    
    try:
        crawler = AfricanNewspaperCrawler(max_workers=1)
        print("✓ 非洲报纸爬虫初始化成功")
        
        # 检查SmartRetryHandler是否已集成
        if hasattr(crawler, 'smart_retry_handler') and crawler.smart_retry_handler is not None:
            print("✓ SmartRetryHandler已成功集成到爬虫")
        else:
            print("✗ SmartRetryHandler未正确集成到爬虫")
            return False
        
        # 测试会话创建和错误统计集成
        session = crawler.get_session('ahram')
        if hasattr(session, 'error_stats'):
            print("✓ 会话错误统计功能集成成功")
            print(f"会话错误统计结构: {session.error_stats}")
        else:
            print("✗ 会话错误统计功能未正确集成")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 爬虫集成测试失败: {e}")
        return False

def test_execute_with_retry_methods():
    """测试execute_with_retry方法在爬虫中的使用"""
    print("\n=== 测试execute_with_retry方法 ===")
    
    try:
        crawler = AfricanNewspaperCrawler(max_workers=1)
        
        # 测试一个简单的搜索函数
        def test_search_function(url=None):
            """模拟搜索函数"""
            return ["test_article_1", "test_article_2"]
        
        # 使用execute_with_retry执行测试函数
        result = crawler.smart_retry_handler.execute_with_retry(
            test_search_function,
            "测试搜索功能",
            "http://test.com/search"
        )
        
        print(f"✓ execute_with_retry测试成功，结果: {result}")
        
        # 测试错误处理
        def failing_function(url=None):
            """模拟失败函数"""
            raise Exception("模拟失败")
        
        try:
            crawler.smart_retry_handler.execute_with_retry(
                failing_function,
                "测试失败处理",
                "http://test.com/fail"
            )
        except Exception as e:
            print(f"✓ 错误处理测试成功，正确捕获异常: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ execute_with_retry方法测试失败: {e}")
        return False

def test_error_statistics():
    """测试错误统计功能"""
    print("\n=== 测试错误统计功能 ===")
    
    try:
        crawler = AfricanNewspaperCrawler(max_workers=1)
        handler = crawler.smart_retry_handler
        
        # 生成一些测试错误
        from smart_retry_handler import ErrorCategory
        
        # 模拟不同类型的错误
        test_errors = [
            ErrorCategory.CONNECTION,
            ErrorCategory.SERVER_ERROR,
            ErrorCategory.CLIENT_ERROR,
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.TIMEOUT
        ]
        
        for error_category in test_errors:
            handler.update_error_stats(error_category, False)  # 失败
            handler.update_error_stats(error_category, True)   # 成功恢复
        
        # 获取错误报告
        report = handler.get_error_report()
        
        print("✓ 错误统计功能测试成功")
        print(f"总错误数: {report.get('total_errors', 0)}")
        print(f"恢复率: {report.get('recovery_rate', 0):.2%}")
        print(f"错误分布: {report.get('error_distribution', {})}")
        
        # 测试优化建议生成
        recommendations = handler.generate_retry_recommendations()
        if recommendations:
            print("✓ 优化建议生成成功")
            for rec in recommendations:
                print(f"  - {rec}")
        
        return True
        
    except Exception as e:
        print(f"✗ 错误统计功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始智能重试处理器集成测试...\n")
    
    tests = [
        ("SmartRetryHandler初始化", test_smart_retry_handler_initialization),
        ("爬虫集成", test_crawler_integration),
        ("execute_with_retry方法", test_execute_with_retry_methods),
        ("错误统计功能", test_error_statistics)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
                print(f"✓ {test_name}测试通过\n")
            else:
                print(f"✗ {test_name}测试失败\n")
        except Exception as e:
            print(f"✗ {test_name}测试异常: {e}\n")
    
    print("=" * 50)
    print(f"测试结果: {passed_tests}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！智能重试处理器集成成功！")
        return True
    else:
        print("⚠️ 部分测试失败，请检查集成问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)