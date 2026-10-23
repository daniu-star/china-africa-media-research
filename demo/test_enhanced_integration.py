"""
增强爬虫集成测试脚本
测试高级错误处理、监控和优化功能的集成效果
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_crawler_integration import EnhancedCrawlerIntegration
from advanced_error_handler import AdvancedErrorHandler, ErrorSeverity, create_error_context
from crawler_monitor import CrawlerMonitor, CrawlerStatus
from smart_retry_optimizer import SmartRetryOptimizer


def test_enhanced_crawler_initialization():
    """测试增强爬虫初始化"""
    print("🧪 测试增强爬虫初始化...")
    
    try:
        # 创建一个模拟爬虫类
        class MockCrawler:
            def __init__(self):
                self.smart_retry_handler = None
                self.session = None
            
            def crawl_article(self, url, newspaper):
                return {"title": "测试文章", "content": "测试内容", "url": url}
            
            def search_articles(self, newspaper, keywords, start_date, end_date):
                return {"articles": [{"title": "测试文章1", "url": "http://example.com/1"}]}
        
        # 创建增强爬虫实例
        mock_crawler = MockCrawler()
        enhanced_crawler = EnhancedCrawlerIntegration(mock_crawler)
        
        # 验证组件初始化
        assert enhanced_crawler.error_handler is not None, "错误处理器未正确初始化"
        assert enhanced_crawler.monitor is not None, "监控器未正确初始化"
        assert enhanced_crawler.optimizer is not None, "优化器未正确初始化"
        
        print("✅ 增强爬虫初始化测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 增强爬虫初始化测试失败: {e}")
        return False


def test_enhanced_crawl_article():
    """测试增强的文章爬取功能"""
    print("🧪 测试增强的文章爬取功能...")
    
    try:
        class MockCrawler:
            def __init__(self):
                self.smart_retry_handler = None
            
            def crawl_article(self, url, newspaper):
                return {
                    "title": "测试文章标题",
                    "content": "测试文章内容",
                    "url": url,
                    "newspaper": newspaper,
                    "timestamp": datetime.now().isoformat()
                }
        
        mock_crawler = MockCrawler()
        enhanced_crawler = EnhancedCrawlerIntegration(mock_crawler)
        
        # 测试正常爬取
        result = enhanced_crawler.enhanced_crawl_article(
            "https://example.com/article",
            "ahram"
        )
        
        assert result is not None, "爬取结果不应为空"
        assert "title" in result, "结果应包含标题"
        assert "content" in result, "结果应包含内容"
        
        print("✅ 增强文章爬取测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 增强文章爬取测试失败: {e}")
        return False


def test_enhanced_search_articles():
    """测试增强的文章搜索功能"""
    print("🧪 测试增强的文章搜索功能...")
    
    try:
        class MockCrawler:
            def __init__(self):
                self.smart_retry_handler = None
            
            def search_articles(self, newspaper, keywords, start_date, end_date):
                return {
                    "articles": [
                        {
                            "title": f"包含{keywords[0]}的文章",
                            "url": "http://example.com/1",
                            "date": "2024-01-01"
                        }
                    ],
                    "total_count": 1
                }
        
        mock_crawler = MockCrawler()
        enhanced_crawler = EnhancedCrawlerIntegration(mock_crawler)
        
        # 测试搜索功能
        result = enhanced_crawler.enhanced_search_articles(
            "ahram",
            ["政治", "经济"],
            "2024-01-01",
            "2024-01-31"
        )
        
        assert result is not None, "搜索结果不应为空"
        assert "articles" in result, "结果应包含文章列表"
        assert len(result["articles"]) > 0, "文章列表不应为空"
        
        print("✅ 增强文章搜索测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 增强文章搜索测试失败: {e}")
        return False


def test_error_handling_integration():
    """测试错误处理集成"""
    print("🧪 测试错误处理集成...")
    
    try:
        class MockCrawler:
            def __init__(self):
                self.smart_retry_handler = None
            
            def crawl_article(self, url, newspaper):
                raise ConnectionError("模拟连接错误")
        
        mock_crawler = MockCrawler()
        enhanced_crawler = EnhancedCrawlerIntegration(mock_crawler)
        
        # 测试错误处理
        try:
            enhanced_crawler.enhanced_crawl_article("https://example.com", "ahram")
            print("❌ 错误处理测试失败: 预期抛出异常但未抛出")
            return False
        except ConnectionError:
            # 预期行为：错误被正确捕获和处理
            pass
        
        # 验证错误被记录
        error_stats = enhanced_crawler.error_handler.get_error_statistics()
        assert error_stats["total_errors"] > 0, "错误应被记录"
        
        print("✅ 错误处理集成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 错误处理集成测试失败: {e}")
        return False


def test_monitoring_integration():
    """测试监控集成"""
    print("🧪 测试监控集成...")
    
    try:
        class MockCrawler:
            def __init__(self):
                self.smart_retry_handler = None
            
            def crawl_article(self, url, newspaper):
                return {"title": "测试", "content": "测试"}
        
        mock_crawler = MockCrawler()
        enhanced_crawler = EnhancedCrawlerIntegration(mock_crawler)
        
        # 执行一些操作
        enhanced_crawler.enhanced_crawl_article("https://example.com", "ahram")
        
        # 检查监控数据
        status = enhanced_crawler.get_system_status()
        
        assert "monitor" in status, "系统状态应包含监控数据"
        assert "error_stats" in status, "系统状态应包含错误统计"
        assert "optimization_recommendations" in status, "系统状态应包含优化建议"
        
        monitor_data = status["monitor"]
        assert "status" in monitor_data, "监控数据应包含状态信息"
        assert "metrics" in monitor_data, "监控数据应包含指标"
        
        print("✅ 监控集成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 监控集成测试失败: {e}")
        return False


def test_optimization_integration():
    """测试优化集成"""
    print("🧪 测试优化集成...")
    
    try:
        class MockCrawler:
            def __init__(self):
                self.smart_retry_handler = None
            
            def crawl_article(self, url, newspaper):
                return {"title": "测试", "content": "测试"}
        
        mock_crawler = MockCrawler()
        enhanced_crawler = EnhancedCrawlerIntegration(mock_crawler)
        
        # 模拟一些请求记录
        domain = "example.com"
        for i in range(5):
            enhanced_crawler.optimizer.record_request(domain, True, 1.0)
        
        for i in range(2):
            enhanced_crawler.optimizer.record_request(domain, False, 2.0, "timeout")
        
        # 检查优化建议
        domain_analysis = enhanced_crawler.optimizer.get_domain_analysis(domain)
        
        assert domain_analysis is not None, "域名分析不应为空"
        assert "success_rate" in domain_analysis, "分析应包含成功率"
        assert "optimization_suggestions" in domain_analysis, "分析应包含优化建议"
        
        print("✅ 优化集成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 优化集成测试失败: {e}")
        return False


def test_report_generation():
    """测试报告生成功能"""
    print("🧪 测试报告生成功能...")
    
    try:
        class MockCrawler:
            def __init__(self):
                self.smart_retry_handler = None
            
            def crawl_article(self, url, newspaper):
                return {"title": "测试", "content": "测试"}
        
        mock_crawler = MockCrawler()
        enhanced_crawler = EnhancedCrawlerIntegration(mock_crawler)
        
        # 生成报告
        report_filename = "test_report.json"
        success = enhanced_crawler.export_comprehensive_report(report_filename)
        
        assert success, "报告生成应成功"
        
        # 验证报告文件存在且内容有效
        assert os.path.exists(report_filename), "报告文件应存在"
        
        with open(report_filename, 'r', encoding='utf-8') as f:
            report_content = json.load(f)
        
        assert "export_timestamp" in report_content, "报告应包含导出时间戳"
        assert "system_status" in report_content, "报告应包含系统状态"
        assert "error_report" in report_content, "报告应包含错误报告"
        
        # 清理测试文件
        if os.path.exists(report_filename):
            os.remove(report_filename)
        
        print("✅ 报告生成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 报告生成测试失败: {e}")
        
        # 清理测试文件（如果存在）
        report_filename = "test_report.json"
        if os.path.exists(report_filename):
            os.remove(report_filename)
        
        return False


def test_comprehensive_integration():
    """测试综合集成功能"""
    print("🧪 测试综合集成功能...")
    
    try:
        class MockCrawler:
            def __init__(self):
                self.smart_retry_handler = None
                self.proxy_manager = None
            
            def crawl_article(self, url, newspaper):
                # 模拟成功和失败交替
                import random
                if random.random() > 0.3:
                    return {
                        "title": f"{newspaper}文章",
                        "content": "测试内容",
                        "url": url
                    }
                else:
                    raise ConnectionError("模拟连接错误")
            
            def search_articles(self, newspaper, keywords, start_date, end_date):
                return {
                    "articles": [
                        {"title": f"{keyword}相关文章", "url": f"http://example.com/{i}"}
                        for i, keyword in enumerate(keywords)
                    ]
                }
        
        mock_crawler = MockCrawler()
        enhanced_crawler = EnhancedCrawlerIntegration(mock_crawler)
        
        # 执行一系列操作
        operations = []
        
        # 爬取操作
        try:
            result = enhanced_crawler.enhanced_crawl_article("https://example.com/1", "ahram")
            operations.append(("crawl", "success"))
        except Exception as e:
            operations.append(("crawl", "error"))
        
        # 搜索操作
        try:
            result = enhanced_crawler.enhanced_search_articles(
                "ahram", ["政治"], "2024-01-01", "2024-01-31"
            )
            operations.append(("search", "success"))
        except Exception as e:
            operations.append(("search", "error"))
        
        # 获取系统状态
        status = enhanced_crawler.get_system_status()
        
        # 验证系统状态完整性
        required_keys = ['monitor', 'error_stats', 'optimization_recommendations', 'domain_performance']
        for key in required_keys:
            assert key in status, f"系统状态应包含{key}"
        
        print("✅ 综合集成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 综合集成测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始增强爬虫集成测试...\n")
    
    tests = [
        ("增强爬虫初始化", test_enhanced_crawler_initialization),
        ("增强文章爬取", test_enhanced_crawl_article),
        ("增强文章搜索", test_enhanced_search_articles),
        ("错误处理集成", test_error_handling_integration),
        ("监控集成", test_monitoring_integration),
        ("优化集成", test_optimization_integration),
        ("报告生成", test_report_generation),
        ("综合集成", test_comprehensive_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        start_time = time.time()
        success = test_func()
        end_time = time.time()
        
        results.append({
            "test": test_name,
            "success": success,
            "duration": round(end_time - start_time, 2)
        })
        
        print()  # 空行分隔
    
    # 输出测试结果汇总
    print("📊 测试结果汇总:")
    print("=" * 50)
    
    passed_tests = [r for r in results if r["success"]]
    failed_tests = [r for r in results if not r["success"]]
    
    print(f"✅ 通过的测试: {len(passed_tests)}/{len(tests)}")
    print(f"❌ 失败的测试: {len(failed_tests)}/{len(tests)}")
    
    if passed_tests:
        print("\n通过的测试:")
        for result in passed_tests:
            print(f"  ✓ {result['test']} ({result['duration']}秒)")
    
    if failed_tests:
        print("\n失败的测试:")
        for result in failed_tests:
            print(f"  ✗ {result['test']} ({result['duration']}秒)")
    
    print("=" * 50)
    
    if len(failed_tests) == 0:
        print("🎉 所有测试通过！增强爬虫集成功能正常！")
        return True
    else:
        print(f"⚠️  {len(failed_tests)}个测试失败，需要进一步调试")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)