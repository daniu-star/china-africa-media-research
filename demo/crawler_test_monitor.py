#!/usr/bin/env python3
"""
爬虫测试和监控模块
用于测试优化效果并实时监控性能
"""

import time
import json
import logging
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests

logger = logging.getLogger(__name__)

class CrawlerTestMonitor:
    """爬虫测试和监控器"""
    
    def __init__(self):
        # 测试配置
        self.test_config = {
            'test_urls': [
                "https://www.news24.com",
                "https://www.nation.co.ke", 
                "https://www.punchng.com",
                "https://www.ahram.org.eg",
                "https://www.thecitizen.co.tz"
            ],
            'test_interval': 300,  # 5分钟
            'test_timeout': 60,
            'max_concurrent_tests': 3
        }
        
        # 监控数据
        self.monitoring_data = {
            'start_time': datetime.now(),
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'average_response_time': 0,
            'website_performance': {},
            'hourly_stats': {},
            'alerts': []
        }
        
        # 性能阈值
        self.performance_thresholds = {
            'min_success_rate': 0.6,  # 最低成功率
            'max_response_time': 10,   # 最大响应时间(秒)
            'max_error_rate': 0.3     # 最大错误率
        }
        
        # 监控线程
        self.monitoring_thread = None
        self.monitoring_active = False
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring_active:
            logger.warning("监控已经在运行中")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        logger.info("爬虫监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        logger.info("爬虫监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring_active:
            try:
                # 执行测试
                self.run_performance_test()
                
                # 检查性能阈值
                self.check_performance_thresholds()
                
                # 生成报告
                self.generate_hourly_report()
                
                # 等待下一个测试周期
                time.sleep(self.test_config['test_interval'])
                
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                time.sleep(60)  # 出错后等待1分钟
    
    def run_performance_test(self):
        """执行性能测试"""
        logger.info("开始性能测试")
        
        test_results = []
        
        # 并发测试
        threads = []
        for url in self.test_config['test_urls']:
            thread = threading.Thread(target=self._test_single_url, args=(url, test_results))
            threads.append(thread)
            thread.start()
            
            # 控制并发数量
            if len(threads) >= self.test_config['max_concurrent_tests']:
                for t in threads:
                    t.join()
                threads = []
        
        # 等待剩余线程完成
        for t in threads:
            t.join()
        
        # 更新监控数据
        self._update_monitoring_data(test_results)
        
        logger.info(f"性能测试完成: {len(test_results)} 个测试")
    
    def _test_single_url(self, url: str, results: List[Dict[str, Any]]):
        """测试单个URL"""
        start_time = time.time()
        success = False
        response_time = 0
        error_type = None
        
        try:
            response = requests.get(
                url, 
                timeout=self.test_config['test_timeout'],
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                success = True
                logger.debug(f"测试 {url} 成功, 响应时间: {response_time:.2f}秒")
            else:
                error_type = f"HTTP_{response.status_code}"
                logger.warning(f"测试 {url} 失败, 状态码: {response.status_code}")
                
        except requests.exceptions.Timeout:
            response_time = self.test_config['test_timeout']
            error_type = "timeout"
            logger.warning(f"测试 {url} 超时")
            
        except requests.exceptions.ConnectionError:
            response_time = time.time() - start_time
            error_type = "connection_error"
            logger.warning(f"测试 {url} 连接错误")
            
        except Exception as e:
            response_time = time.time() - start_time
            error_type = "other_error"
            logger.warning(f"测试 {url} 其他错误: {e}")
        
        results.append({
            'url': url,
            'success': success,
            'response_time': response_time,
            'error_type': error_type,
            'timestamp': datetime.now()
        })
    
    def _update_monitoring_data(self, test_results: List[Dict[str, Any]]):
        """更新监控数据"""
        for result in test_results:
            self.monitoring_data['total_tests'] += 1
            
            if result['success']:
                self.monitoring_data['successful_tests'] += 1
            else:
                self.monitoring_data['failed_tests'] += 1
            
            # 更新平均响应时间
            if self.monitoring_data['total_tests'] > 0:
                self.monitoring_data['average_response_time'] = (
                    self.monitoring_data['average_response_time'] * (self.monitoring_data['total_tests'] - 1) + 
                    result['response_time']
                ) / self.monitoring_data['total_tests']
            
            # 更新网站性能数据
            domain = self._extract_domain(result['url'])
            if domain not in self.monitoring_data['website_performance']:
                self.monitoring_data['website_performance'][domain] = {
                    'total_tests': 0,
                    'successful_tests': 0,
                    'failed_tests': 0,
                    'average_response_time': 0,
                    'last_test_time': None
                }
            
            website_stats = self.monitoring_data['website_performance'][domain]
            website_stats['total_tests'] += 1
            
            if result['success']:
                website_stats['successful_tests'] += 1
            else:
                website_stats['failed_tests'] += 1
            
            website_stats['average_response_time'] = (
                website_stats['average_response_time'] * (website_stats['total_tests'] - 1) + 
                result['response_time']
            ) / website_stats['total_tests']
            
            website_stats['last_test_time'] = result['timestamp']
    
    def _extract_domain(self, url: str) -> str:
        """提取域名"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return 'unknown'
    
    def check_performance_thresholds(self):
        """检查性能阈值"""
        current_hour = datetime.now().strftime('%Y-%m-%d %H:00')
        
        # 计算当前成功率
        if self.monitoring_data['total_tests'] > 0:
            success_rate = self.monitoring_data['successful_tests'] / self.monitoring_data['total_tests']
        else:
            success_rate = 0
        
        # 检查成功率阈值
        if success_rate < self.performance_thresholds['min_success_rate']:
            alert = {
                'type': 'low_success_rate',
                'message': f"成功率过低: {success_rate:.1%} (阈值: {self.performance_thresholds['min_success_rate']:.1%})",
                'severity': 'high',
                'timestamp': datetime.now()
            }
            self.monitoring_data['alerts'].append(alert)
            logger.warning(alert['message'])
        
        # 检查响应时间阈值
        if self.monitoring_data['average_response_time'] > self.performance_thresholds['max_response_time']:
            alert = {
                'type': 'high_response_time',
                'message': f"平均响应时间过高: {self.monitoring_data['average_response_time']:.2f}秒 (阈值: {self.performance_thresholds['max_response_time']}秒)",
                'severity': 'medium',
                'timestamp': datetime.now()
            }
            self.monitoring_data['alerts'].append(alert)
            logger.warning(alert['message'])
        
        # 检查网站性能
        for domain, stats in self.monitoring_data['website_performance'].items():
            if stats['total_tests'] >= 5:  # 至少有5次测试
                website_success_rate = stats['successful_tests'] / stats['total_tests']
                
                if website_success_rate < 0.3:  # 网站成功率低于30%
                    alert = {
                        'type': 'website_performance_issue',
                        'message': f"网站 {domain} 性能问题: 成功率 {website_success_rate:.1%}",
                        'severity': 'medium',
                        'timestamp': datetime.now()
                    }
                    self.monitoring_data['alerts'].append(alert)
                    logger.warning(alert['message'])
    
    def generate_hourly_report(self):
        """生成小时报告"""
        current_hour = datetime.now().strftime('%Y-%m-%d %H:00')
        
        if current_hour not in self.monitoring_data['hourly_stats']:
            self.monitoring_data['hourly_stats'][current_hour] = {
                'total_tests': 0,
                'successful_tests': 0,
                'failed_tests': 0,
                'average_response_time': 0
            }
        
        # 更新小时统计（简化实现）
        # 实际应该保存每个小时的独立统计数据
    
    def get_monitoring_report(self) -> Dict[str, Any]:
        """获取监控报告"""
        # 计算成功率
        if self.monitoring_data['total_tests'] > 0:
            success_rate = self.monitoring_data['successful_tests'] / self.monitoring_data['total_tests']
        else:
            success_rate = 0
        
        # 计算错误率
        error_rate = 1 - success_rate if self.monitoring_data['total_tests'] > 0 else 0
        
        # 生成网站性能排名
        website_ranking = []
        for domain, stats in self.monitoring_data['website_performance'].items():
            if stats['total_tests'] > 0:
                website_success_rate = stats['successful_tests'] / stats['total_tests']
                website_ranking.append({
                    'domain': domain,
                    'success_rate': round(website_success_rate * 100, 2),
                    'average_response_time': round(stats['average_response_time'], 2),
                    'total_tests': stats['total_tests']
                })
        
        # 按成功率排序
        website_ranking.sort(key=lambda x: x['success_rate'], reverse=True)
        
        return {
            'monitoring_duration': str(datetime.now() - self.monitoring_data['start_time']),
            'total_tests': self.monitoring_data['total_tests'],
            'successful_tests': self.monitoring_data['successful_tests'],
            'failed_tests': self.monitoring_data['failed_tests'],
            'success_rate': round(success_rate * 100, 2),
            'error_rate': round(error_rate * 100, 2),
            'average_response_time': round(self.monitoring_data['average_response_time'], 2),
            'website_ranking': website_ranking[:10],  # 前10个网站
            'recent_alerts': self.monitoring_data['alerts'][-10:],  # 最近10个警报
            'performance_status': self._get_performance_status(success_rate),
            'recommendations': self._generate_recommendations(success_rate, error_rate)
        }
    
    def _get_performance_status(self, success_rate: float) -> str:
        """获取性能状态"""
        if success_rate >= 0.8:
            return "优秀"
        elif success_rate >= 0.6:
            return "良好" 
        elif success_rate >= 0.4:
            return "一般"
        else:
            return "较差"
    
    def _generate_recommendations(self, success_rate: float, error_rate: float) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if success_rate < 0.6:
            recommendations.append("成功率较低，建议检查网络连接和代理配置")
        
        if error_rate > 0.3:
            recommendations.append("错误率较高，建议优化爬取策略和增加重试次数")
        
        if self.monitoring_data['average_response_time'] > 5:
            recommendations.append("响应时间较长，建议优化网络连接或选择更近的代理")
        
        # 分析具体错误类型
        timeout_count = len([a for a in self.monitoring_data['alerts'] if a['type'] == 'timeout'])
        connection_count = len([a for a in self.monitoring_data['alerts'] if a['type'] == 'connection_error'])
        
        if timeout_count > connection_count:
            recommendations.append("超时错误较多，建议增加超时时间或优化网络连接")
        elif connection_count > timeout_count:
            recommendations.append("连接错误较多，建议检查代理配置或更换代理服务器")
        
        return recommendations
    
    def export_report(self, filename: str = None):
        """导出报告"""
        if filename is None:
            filename = f"crawler_monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.get_monitoring_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"监控报告已导出到: {filename}")
        return filename

# 使用示例
def test_crawler_monitor():
    """测试爬虫监控器"""
    monitor = CrawlerTestMonitor()
    
    # 启动监控
    monitor.start_monitoring()
    
    # 运行几次测试
    for i in range(3):
        print(f"\n第 {i+1} 轮测试...")
        monitor.run_performance_test()
        
        # 获取报告
        report = monitor.get_monitoring_report()
        print(f"当前状态: {report['performance_status']}")
        print(f"成功率: {report['success_rate']}%")
        print(f"平均响应时间: {report['average_response_time']}秒")
        
        time.sleep(60)  # 等待1分钟
    
    # 停止监控
    monitor.stop_monitoring()
    
    # 导出最终报告
    final_report = monitor.get_monitoring_report()
    print(f"\n最终报告:")
    print(json.dumps(final_report, indent=2, ensure_ascii=False))
    
    # 导出到文件
    monitor.export_report()

if __name__ == "__main__":
    test_crawler_monitor()