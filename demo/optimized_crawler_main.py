#!/usr/bin/env python3
"""
优化后的爬虫主程序
集成所有优化模块，提供完整的爬虫解决方案
"""

import time
import logging
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
import json

# 导入优化模块
from network_optimizer import NetworkOptimizer
from anti_anti_crawler import AntiAntiCrawler
from smart_retry_handler import SmartRetryHandler
from proxy_geo_optimizer import ProxyGeoOptimizer
from intelligent_crawling_strategy import IntelligentCrawlingStrategy
from crawler_test_monitor import CrawlerTestMonitor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OptimizedCrawler:
    """优化后的爬虫类"""
    
    def __init__(self, config_file: str = "config.yaml"):
        # 初始化优化模块
        self.network_optimizer = NetworkOptimizer()
        self.anti_crawler = AntiAntiCrawler()
        self.retry_handler = SmartRetryHandler()
        self.proxy_optimizer = ProxyGeoOptimizer()
        self.crawling_strategy = IntelligentCrawlingStrategy()
        self.monitor = CrawlerTestMonitor()
        
        # 爬虫状态
        self.crawler_status = {
            'start_time': datetime.now(),
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'current_strategy': 'balanced',
            'last_optimization': datetime.now(),
            'performance_stats': {}
        }
        
        # 配置
        self.config = self._load_config(config_file)
        
        logger.info("优化爬虫系统初始化完成")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """加载配置文件"""
        # 简化配置加载，实际应该从文件读取
        return {
            'max_concurrent_requests': 5,
            'default_timeout': 60,
            'max_retries': 5,
            'request_delay': 2,
            'monitoring_enabled': True,
            'performance_thresholds': {
                'min_success_rate': 0.6,
                'max_response_time': 10
            }
        }
    
    def crawl_url(self, url: str, strategy: str = None) -> Dict[str, Any]:
        """爬取单个URL"""
        start_time = time.time()
        
        # 选择爬取策略
        if strategy is None:
            strategy = self.crawling_strategy.select_crawling_strategy(url)
        
        # 获取优化参数
        optimized_params = self._get_optimized_parameters(url, strategy)
        
        # 执行爬取
        result = self._execute_crawl(url, optimized_params)
        
        # 更新统计
        self._update_statistics(result, time.time() - start_time)
        
        # 优化策略调整
        self._optimize_strategy_based_on_result(result)
        
        return result
    
    def _get_optimized_parameters(self, url: str, strategy: str) -> Dict[str, Any]:
        """获取优化后的爬取参数"""
        # 获取优化参数
        timeout = self.network_optimizer.calculate_smart_timeout(url)
        
        # 反爬虫优化
        headers = self.anti_crawler.get_optimized_headers(url)
        delay = self.anti_crawler.calculate_smart_delay(url)
        
        # 代理优化
        proxies = self.proxy_optimizer.select_optimal_proxy(url)
        
        # 重试策略
        retry_config = self.retry_handler.get_error_profile(url)
        
        return {
            'timeout': timeout,
            'headers': headers,
            'delay': delay,
            'proxies': proxies,
            'retry_config': retry_config,
            'strategy': strategy
        }
    
    def _execute_crawl(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行爬取操作"""
        # 应用延迟
        if params['delay'] > 0:
            time.sleep(params['delay'])
        
        # 准备请求参数
        request_kwargs = {
            'url': url,
            'timeout': params['timeout'],
            'headers': params['headers']
        }
        
        if params['proxies']:
            request_kwargs['proxies'] = params['proxies']
        
        # 执行请求（带重试）
        max_retries = 5  # 默认最大重试次数
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(**request_kwargs)
                
                if response.status_code == 200:
                    return {
                        'success': True,
                        'url': url,
                        'status_code': 200,
                        'content': response.text,
                        'response_time': response.elapsed.total_seconds(),
                        'attempts': attempt + 1,
                        'strategy': params['strategy']
                    }
                else:
                    # 记录错误但继续重试
                    error_type = f"HTTP_{response.status_code}"
                    
            except requests.exceptions.Timeout:
                error_type = "timeout"
            except requests.exceptions.ConnectionError:
                error_type = "connection_error"
            except Exception as e:
                error_type = f"other_error: {str(e)}"
            
            # 如果不是最后一次尝试，等待重试延迟
            if attempt < max_retries:
                # 使用指数退避策略计算延迟
                retry_delay = min(2 ** attempt, 60)  # 最大延迟60秒
                time.sleep(retry_delay)
        
        # 所有重试都失败
        return {
            'success': False,
            'url': url,
            'error_type': error_type,
            'attempts': max_retries + 1,
            'strategy': params['strategy']
        }
    
    def _update_statistics(self, result: Dict[str, Any], total_time: float):
        """更新统计信息"""
        self.crawler_status['total_requests'] += 1
        
        if result['success']:
            self.crawler_status['successful_requests'] += 1
        else:
            self.crawler_status['failed_requests'] += 1
        
        # 更新性能统计
        strategy = result['strategy']
        
        # 如果strategy是字典类型，转换为字符串
        if isinstance(strategy, dict):
            strategy = strategy.get('name', 'unknown')
        
        if strategy not in self.crawler_status['performance_stats']:
            self.crawler_status['performance_stats'][strategy] = {
                'total': 0,
                'success': 0,
                'total_time': 0
            }
        
        stats = self.crawler_status['performance_stats'][strategy]
        stats['total'] += 1
        stats['total_time'] += total_time
        
        if result['success']:
            stats['success'] += 1
    
    def _optimize_strategy_based_on_result(self, result: Dict[str, Any]):
        """基于结果优化策略"""
        # 根据最近的成功率调整策略
        recent_success_rate = self._calculate_recent_success_rate()
        
        if recent_success_rate < 0.4:
            # 成功率过低，切换到保守策略
            logger.warning(f"成功率过低({recent_success_rate:.1%})，建议使用保守策略")
        elif recent_success_rate > 0.8:
            # 成功率很高，可以尝试激进策略
            logger.info(f"成功率较高({recent_success_rate:.1%})，可以尝试激进策略")
        
        # 更新最后优化时间
        self.crawler_status['last_optimization'] = datetime.now()
    
    def _calculate_recent_success_rate(self, window_size: int = 50) -> float:
        """计算最近的成功率"""
        if self.crawler_status['total_requests'] == 0:
            return 0.0
        
        # 简化实现：使用整体成功率
        # 实际应该使用滑动窗口计算最近的成功率
        return self.crawler_status['successful_requests'] / self.crawler_status['total_requests']
    
    def batch_crawl(self, urls: List[str], strategy: str = None) -> List[Dict[str, Any]]:
        """批量爬取URL"""
        results = []
        
        # 控制并发数量
        max_concurrent = self.config['max_concurrent_requests']
        
        # 分批处理
        for i in range(0, len(urls), max_concurrent):
            batch_urls = urls[i:i + max_concurrent]
            
            # 并发爬取
            threads = []
            batch_results = []
            
            for url in batch_urls:
                thread = threading.Thread(
                    target=lambda u, r: r.append(self.crawl_url(u, strategy)),
                    args=(url, batch_results)
                )
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            results.extend(batch_results)
            
            # 批次间延迟
            time.sleep(1)
        
        return results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        total_requests = self.crawler_status['total_requests']
        
        if total_requests == 0:
            return {
                'status': '未开始爬取',
                'success_rate': 0,
                'average_response_time': 0
            }
        
        success_rate = self.crawler_status['successful_requests'] / total_requests
        
        # 计算平均响应时间
        total_time = sum(
            stats['total_time'] for stats in self.crawler_status['performance_stats'].values()
        )
        average_response_time = total_time / total_requests
        
        # 策略性能分析
        strategy_performance = {}
        for strategy, stats in self.crawler_status['performance_stats'].items():
            if stats['total'] > 0:
                strategy_success_rate = stats['success'] / stats['total']
                strategy_avg_time = stats['total_time'] / stats['total']
                
                strategy_performance[strategy] = {
                    'success_rate': round(strategy_success_rate * 100, 2),
                    'average_time': round(strategy_avg_time, 2),
                    'total_requests': stats['total']
                }
        
        # 性能状态
        if success_rate >= 0.8:
            performance_status = "优秀"
        elif success_rate >= 0.6:
            performance_status = "良好"
        elif success_rate >= 0.4:
            performance_status = "一般"
        else:
            performance_status = "较差"
        
        return {
            'status': performance_status,
            'total_requests': total_requests,
            'successful_requests': self.crawler_status['successful_requests'],
            'failed_requests': self.crawler_status['failed_requests'],
            'success_rate': round(success_rate * 100, 2),
            'average_response_time': round(average_response_time, 2),
            'running_time': str(datetime.now() - self.crawler_status['start_time']),
            'strategy_performance': strategy_performance,
            'current_strategy': 'balanced',
            'recommendations': self._generate_recommendations(success_rate)
        }
    
    def _generate_recommendations(self, success_rate: float) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if success_rate < 0.6:
            recommendations.append("成功率较低，建议检查网络连接和代理配置")
        
        if self.crawler_status['failed_requests'] > self.crawler_status['successful_requests']:
            recommendations.append("失败请求多于成功请求，建议优化爬取策略")
        
        # 分析策略性能
        for strategy, stats in self.crawler_status['performance_stats'].items():
            if stats['total'] >= 10:  # 有足够样本
                strategy_success_rate = stats['success'] / stats['total']
                
                if strategy_success_rate < 0.3:
                    recommendations.append(f"策略 '{strategy}' 性能较差，建议减少使用")
                elif strategy_success_rate > 0.8:
                    recommendations.append(f"策略 '{strategy}' 性能优秀，可以优先使用")
        
        return recommendations
    
    def start_monitoring(self):
        """启动监控"""
        if self.config['monitoring_enabled']:
            self.monitor.start_monitoring()
            logger.info("爬虫监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        if self.config['monitoring_enabled']:
            self.monitor.stop_monitoring()
            logger.info("爬虫监控已停止")
    
    def export_performance_report(self, filename: str = None):
        """导出性能报告"""
        if filename is None:
            filename = f"crawler_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.get_performance_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"性能报告已导出到: {filename}")
        return filename

# 使用示例
def test_optimized_crawler():
    """测试优化后的爬虫"""
    # 创建优化爬虫实例
    crawler = OptimizedCrawler()
    
    # 启动监控
    crawler.start_monitoring()
    
    # 测试URL列表
    test_urls = [
        "https://www.news24.com",
        "https://www.nation.co.ke",
        "https://www.punchng.com", 
        "https://www.ahram.org.eg",
        "https://www.thecitizen.co.tz",
        "https://www.dailytrust.com",
        "https://www.standardmedia.co.ke",
        "https://www.monitor.co.ug"
    ]
    
    print("开始测试优化后的爬虫...")
    
    # 分批测试
    for batch_num in range(3):
        print(f"\n第 {batch_num + 1} 批测试...")
        
        # 随机选择部分URL进行测试
        import random
        batch_urls = random.sample(test_urls, min(4, len(test_urls)))
        
        # 执行批量爬取
        results = crawler.batch_crawl(batch_urls)
        
        # 分析结果
        successful_crawls = [r for r in results if r['success']]
        failed_crawls = [r for r in results if not r['success']]
        
        print(f"成功: {len(successful_crawls)} 个URL")
        print(f"失败: {len(failed_crawls)} 个URL")
        
        if successful_crawls:
            avg_response_time = sum(r.get('response_time', 0) for r in successful_crawls) / len(successful_crawls)
            print(f"平均响应时间: {avg_response_time:.2f}秒")
        
        # 显示性能报告
        report = crawler.get_performance_report()
        print(f"当前成功率: {report['success_rate']}%")
        print(f"性能状态: {report['status']}")
        
        # 等待一段时间再进行下一批测试
        time.sleep(30)
    
    # 停止监控
    crawler.stop_monitoring()
    
    # 生成最终报告
    final_report = crawler.get_performance_report()
    print("\n" + "="*50)
    print("最终性能报告:")
    print(json.dumps(final_report, indent=2, ensure_ascii=False))
    
    # 导出报告
    crawler.export_performance_report()
    
    return final_report

if __name__ == "__main__":
    # 运行测试
    test_optimized_crawler()