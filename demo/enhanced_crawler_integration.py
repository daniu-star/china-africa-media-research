"""
增强爬虫集成模块
将高级错误处理、监控和优化功能集成到非洲报纸爬虫中
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

from advanced_error_handler import AdvancedErrorHandler, ErrorSeverity, create_error_context
from crawler_monitor import CrawlerMonitor, CrawlerStatus
from smart_retry_optimizer import SmartRetryOptimizer


class EnhancedCrawlerIntegration:
    """增强爬虫集成类"""
    
    def __init__(self, crawler_instance):
        self.crawler = crawler_instance
        self.error_handler = AdvancedErrorHandler()
        self.monitor = CrawlerMonitor()
        self.optimizer = SmartRetryOptimizer()
        
        self.logger = logging.getLogger(__name__)
        
        # 集成智能重试处理器
        if hasattr(crawler_instance, 'smart_retry_handler'):
            self.smart_retry_handler = crawler_instance.smart_retry_handler
        else:
            self.logger.warning("未找到智能重试处理器，部分功能可能受限")
            self.smart_retry_handler = None
    
    def enhanced_crawl_article(self, url: str, newspaper: str) -> Dict[str, Any]:
        """增强的文章爬取方法"""
        self.monitor.update_status(CrawlerStatus.RUNNING, {
            'task': 'crawl_article',
            'url': url,
            'newspaper': newspaper
        })
        
        start_time = time.time()
        result = None
        error_context = None
        
        try:
            # 获取最优重试配置
            domain = self._extract_domain(url)
            retry_config = self.optimizer.get_optimal_retry_config(domain)
            
            # 使用智能重试处理器执行爬取
            if self.smart_retry_handler:
                result = self.smart_retry_handler.execute_with_retry(
                    lambda: self.crawler.crawl_article(url, newspaper),
                    url=url,
                    max_retries=retry_config.max_retries,
                    base_delay=retry_config.base_delay
                )
            else:
                # 备用方案：直接调用爬虫方法
                result = self.crawler.crawl_article(url, newspaper)
            
            # 记录成功请求
            response_time = time.time() - start_time
            self.optimizer.record_request(domain, True, response_time)
            
            # 更新监控状态
            self.monitor.update_status(CrawlerStatus.RUNNING, {
                'task': 'crawl_article',
                'url': url,
                'newspaper': newspaper,
                'status': 'success'
            })
            
            return result
            
        except Exception as e:
            # 记录错误
            response_time = time.time() - start_time
            error_type = self._classify_error(e)
            
            error_context = create_error_context(
                url=url,
                error_type=error_type,
                error_message=str(e),
                severity=self._determine_severity(error_type)
            )
            
            self.error_handler.record_error(error_context)
            self.optimizer.record_request(domain, False, response_time, error_type)
            
            # 获取恢复策略
            recovery_strategy = self.error_handler.get_recovery_strategy(error_type, url)
            
            # 更新监控状态
            self.monitor.update_status(CrawlerStatus.ERROR if recovery_strategy else CrawlerStatus.RUNNING, {
                'task': 'crawl_article',
                'url': url,
                'newspaper': newspaper,
                'error': str(e),
                'recovery_strategy': recovery_strategy
            })
            
            # 根据恢复策略处理错误
            if recovery_strategy:
                self._handle_recovery_strategy(recovery_strategy, url, newspaper)
            
            raise
    
    def enhanced_search_articles(self, newspaper: str, keywords: list, 
                                start_date: str, end_date: str) -> Dict[str, Any]:
        """增强的文章搜索方法"""
        self.monitor.update_status(CrawlerStatus.RUNNING, {
            'task': 'search_articles',
            'newspaper': newspaper,
            'keywords': keywords,
            'date_range': f"{start_date} to {end_date}"
        })
        
        try:
            # 使用智能重试处理器执行搜索
            if self.smart_retry_handler:
                result = self.smart_retry_handler.execute_with_retry(
                    lambda: self.crawler.search_articles(newspaper, keywords, start_date, end_date),
                    url=f"search_{newspaper}",
                    max_retries=3,
                    base_delay=2.0
                )
            else:
                result = self.crawler.search_articles(newspaper, keywords, start_date, end_date)
            
            # 记录搜索性能
            domain = f"search_{newspaper}"
            self.optimizer.record_request(domain, True, 0)  # 搜索时间较短，使用0作为响应时间
            
            self.monitor.update_status(CrawlerStatus.RUNNING, {
                'task': 'search_articles',
                'newspaper': newspaper,
                'status': 'success',
                'results_count': len(result.get('articles', []))
            })
            
            return result
            
        except Exception as e:
            error_type = self._classify_error(e)
            
            error_context = create_error_context(
                url=f"search_{newspaper}",
                error_type=error_type,
                error_message=str(e),
                severity=self._determine_severity(error_type)
            )
            
            self.error_handler.record_error(error_context)
            
            self.monitor.update_status(CrawlerStatus.ERROR, {
                'task': 'search_articles',
                'newspaper': newspaper,
                'error': str(e)
            })
            
            raise
    
    def _extract_domain(self, url: str) -> str:
        """从URL中提取域名"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    
    def _classify_error(self, error: Exception) -> str:
        """分类错误类型"""
        error_str = str(error).lower()
        
        if 'timeout' in error_str or 'timed out' in error_str:
            return 'timeout'
        elif 'connection' in error_str or 'connect' in error_str:
            return 'connection'
        elif 'rate limit' in error_str or '429' in error_str:
            return 'rate_limit'
        elif '403' in error_str or 'forbidden' in error_str:
            return 'anti_crawler'
        elif '50' in error_str:  # 500, 502, 503等服务器错误
            return 'server_error'
        elif '40' in error_str:  # 400, 404等客户端错误
            return 'client_error'
        else:
            return 'unknown'
    
    def _determine_severity(self, error_type: str) -> ErrorSeverity:
        """确定错误严重程度"""
        severity_map = {
            'timeout': ErrorSeverity.MEDIUM,
            'connection': ErrorSeverity.HIGH,
            'rate_limit': ErrorSeverity.MEDIUM,
            'anti_crawler': ErrorSeverity.HIGH,
            'server_error': ErrorSeverity.MEDIUM,
            'client_error': ErrorSeverity.LOW,
            'unknown': ErrorSeverity.MEDIUM
        }
        return severity_map.get(error_type, ErrorSeverity.MEDIUM)
    
    def _handle_recovery_strategy(self, strategy: Dict[str, Any], url: str, newspaper: str):
        """处理恢复策略"""
        action = strategy.get('action')
        
        if action == 'retry':
            delay = strategy.get('delay', 5)
            self.logger.info(f"执行恢复策略: 等待{delay}秒后重试")
            time.sleep(delay)
            
            # 可以在这里实现更复杂的重试逻辑
            if strategy.get('change_proxy'):
                self._rotate_proxy()
            
            if strategy.get('rotate_user_agent'):
                self._rotate_user_agent()
                
        elif action == 'wait_and_retry':
            delay = strategy.get('delay', 60)
            self.logger.info(f"执行恢复策略: 等待{delay}秒后重试")
            time.sleep(delay)
            
        elif action == 'skip':
            self.logger.info("执行恢复策略: 跳过当前任务")
            # 跳过逻辑可以在调用层实现
    
    def _rotate_proxy(self):
        """轮换代理"""
        if hasattr(self.crawler, 'proxy_manager'):
            try:
                self.crawler.proxy_manager.rotate_proxy()
                self.logger.info("代理已轮换")
            except Exception as e:
                self.logger.warning(f"轮换代理失败: {e}")
    
    def _rotate_user_agent(self):
        """轮换User-Agent"""
        if hasattr(self.crawler, 'session') and self.crawler.session:
            try:
                # 这里可以实现User-Agent轮换逻辑
                self.logger.info("User-Agent轮换功能待实现")
            except Exception as e:
                self.logger.warning(f"轮换User-Agent失败: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'monitor': self.monitor.get_dashboard_data(),
            'error_stats': self.error_handler.get_error_statistics(),
            'optimization_recommendations': self.error_handler.get_optimization_recommendations(),
            'domain_performance': {
                domain: self.optimizer.get_domain_analysis(domain)
                for domain in self.optimizer.domain_performance.keys()
            }
        }
    
    def export_comprehensive_report(self, filename: str) -> bool:
        """导出综合报告"""
        try:
            report = {
                'export_timestamp': datetime.now().isoformat(),
                'system_status': self.get_system_status(),
                'error_report': self._generate_error_report(),
                'performance_report': self._generate_performance_report(),
                'optimization_report': self._generate_optimization_report()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"综合报告已导出到: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出综合报告失败: {e}")
            return False
    
    def _generate_error_report(self) -> Dict[str, Any]:
        """生成错误报告"""
        return {
            'recent_errors': self.error_handler.get_error_statistics(),
            'error_patterns': self.error_handler.error_patterns,
            'recovery_success_rate': self._calculate_recovery_success_rate()
        }
    
    def _generate_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        return {
            'domain_performance': {
                domain: self.optimizer.get_domain_analysis(domain)
                for domain in self.optimizer.domain_performance.keys()
            },
            'overall_performance': self.optimizer._get_summary_statistics()
        }
    
    def _generate_optimization_report(self) -> Dict[str, Any]:
        """生成优化报告"""
        return {
            'error_optimization': self.error_handler.get_optimization_recommendations(),
            'retry_optimization': self.optimizer._get_global_recommendations(),
            'system_optimization': self._generate_system_optimization_suggestions()
        }
    
    def _calculate_recovery_success_rate(self) -> float:
        """计算恢复成功率"""
        # 简化实现，实际可以根据历史数据计算
        return 0.85  # 假设85%的恢复成功率
    
    def _generate_system_optimization_suggestions(self) -> List[str]:
        """生成系统优化建议"""
        suggestions = []
        
        # 基于监控数据生成建议
        monitor_data = self.monitor.get_dashboard_data()
        
        if monitor_data['metrics'].get('success_rate', 1.0) < 0.9:
            suggestions.append("系统成功率较低，建议优化网络连接和代理设置")
        
        if monitor_data['alerts']:
            suggestions.append(f"存在{len(monitor_data['alerts'])}个未处理警报，建议及时处理")
        
        return suggestions
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitor.stop_monitoring()


# 使用示例
def create_enhanced_crawler(crawler_instance):
    """创建增强爬虫实例"""
    return EnhancedCrawlerIntegration(crawler_instance)


if __name__ == "__main__":
    # 示例用法
    try:
        from african_newspaper_crawler import AfricanNewspaperCrawler
        
        # 创建原始爬虫实例
        crawler = AfricanNewspaperCrawler()
        
        # 创建增强爬虫实例
        enhanced_crawler = EnhancedCrawlerIntegration(crawler)
        
        # 使用增强功能爬取文章
        result = enhanced_crawler.enhanced_crawl_article(
            "https://example.com/article",
            "ahram"
        )
        
        print("爬取结果:", result)
        
        # 获取系统状态
        status = enhanced_crawler.get_system_status()
        print("系统状态:", json.dumps(status, indent=2, ensure_ascii=False))
        
        # 导出报告
        enhanced_crawler.export_comprehensive_report("crawler_report.json")
        
    except Exception as e:
        print(f"示例执行失败: {e}")