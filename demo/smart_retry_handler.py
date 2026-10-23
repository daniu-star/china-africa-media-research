#!/usr/bin/env python3
"""
智能重试和错误处理模块 - 增强版
专门针对非洲网站网络环境进行优化，集成高级错误分类和自适应重试策略
"""

import time
import random
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from urllib.parse import urlparse
import socket
from enum import Enum
import requests
import urllib3
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RetryStrategy(Enum):
    """重试策略枚举"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    ADAPTIVE = "adaptive"

class ErrorCategory(Enum):
    """错误分类枚举 - 增强版"""
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    ANTI_CRAWLER = "anti_crawler"
    SSL_ERROR = "ssl_error"
    DNS_ERROR = "dns_error"
    UNKNOWN = "unknown"

class SmartRetryHandler:
    """智能重试处理器 - 增强版"""
    
    def __init__(self):
        # 非洲网站错误特性数据库 - 增强版
        self.africa_error_profiles = {
            # 南非网站 - 网络相对稳定
            '.co.za': {
                'timeout_retries': 8,
                'connection_retries': 10,
                'rate_limit_retries': 5,
                'server_error_retries': 3,
                'ssl_error_retries': 4,
                'anti_crawler_retries': 3,
                'strategy': RetryStrategy.ADAPTIVE,
                'base_timeout': 30,
                'max_timeout': 120
            },
            
            # 东非网站 - 网络不稳定，增加重试
            '.ke': {
                'timeout_retries': 12,
                'connection_retries': 15,
                'rate_limit_retries': 8,
                'server_error_retries': 5,
                'ssl_error_retries': 6,
                'anti_crawler_retries': 4,
                'strategy': RetryStrategy.EXPONENTIAL_BACKOFF,
                'base_timeout': 45,
                'max_timeout': 180
            },
            
            # 西非网站 - 网络最不稳定，最大重试
            '.ng': {
                'timeout_retries': 15,
                'connection_retries': 20,
                'rate_limit_retries': 10,
                'server_error_retries': 8,
                'ssl_error_retries': 8,
                'anti_crawler_retries': 5,
                'strategy': RetryStrategy.ADAPTIVE,
                'base_timeout': 60,
                'max_timeout': 240
            },
            
            # 北非网站 - 网络相对稳定
            '.eg': {
                'timeout_retries': 6,
                'connection_retries': 8,
                'rate_limit_retries': 4,
                'server_error_retries': 3,
                'ssl_error_retries': 3,
                'anti_crawler_retries': 2,
                'strategy': RetryStrategy.LINEAR_BACKOFF,
                'base_timeout': 25,
                'max_timeout': 90
            },
            
            # 其他非洲国家域名
            '.gh': {  # 加纳
                'timeout_retries': 10,
                'connection_retries': 12,
                'rate_limit_retries': 6,
                'server_error_retries': 4,
                'ssl_error_retries': 5,
                'anti_crawler_retries': 3,
                'strategy': RetryStrategy.ADAPTIVE,
                'base_timeout': 40,
                'max_timeout': 150
            },
            
            '.tz': {  # 坦桑尼亚
                'timeout_retries': 11,
                'connection_retries': 14,
                'rate_limit_retries': 7,
                'server_error_retries': 5,
                'ssl_error_retries': 6,
                'anti_crawler_retries': 4,
                'strategy': RetryStrategy.EXPONENTIAL_BACKOFF,
                'base_timeout': 50,
                'max_timeout': 180
            }
        }
        
        # 错误统计
        self.error_stats = {
            'total_errors': 0,
            'timeout_errors': 0,
            'connection_errors': 0,
            'rate_limit_errors': 0,
            'server_errors': 0,
            'client_errors': 0,
            'anti_crawler_errors': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0
        }
        
        # 自适应参数
        self.adaptive_params = {
            'base_delay': 5,
            'max_delay': 300,
            'success_threshold': 0.8,
            'failure_threshold': 0.3
        }
    
    def classify_error(self, error: Exception, response: Optional[Any] = None, url: str = '') -> ErrorCategory:
        """分类错误类型 - 增强版"""
        error_str = str(error).lower()
        
        # SSL证书错误
        if any(keyword in error_str for keyword in ['ssl', 'certificate', 'tls', 'handshake']):
            return ErrorCategory.SSL_ERROR
            
        # 反爬虫检测
        if any(keyword in error_str for keyword in ['bot', 'crawler', 'scraper', 'blocked', 'forbidden', '403']):
            return ErrorCategory.ANTI_CRAWLER
            
        # 超时错误
        if any(keyword in error_str for keyword in ['timeout', 'timed out', 'time out', 'read timeout', 'connect timeout']):
            return ErrorCategory.TIMEOUT
            
        # 连接错误
        if any(keyword in error_str for keyword in ['connection', 'connect', 'network', 'refused', 'reset', 'socket']):
            return ErrorCategory.CONNECTION
            
        # 速率限制
        if any(keyword in error_str for keyword in ['rate limit', 'too many requests', '429', 'throttling', 'quota']):
            return ErrorCategory.RATE_LIMIT
            
        # DNS解析错误
        if any(keyword in error_str for keyword in ['dns', 'name resolution', 'host not found']):
            return ErrorCategory.DNS_ERROR
            
        # 服务器错误
        if response and hasattr(response, 'status_code'):
            if 500 <= response.status_code < 600:
                return ErrorCategory.SERVER_ERROR
                
        # 客户端错误
        if response and hasattr(response, 'status_code'):
            if 400 <= response.status_code < 500:
                return ErrorCategory.CLIENT_ERROR
                
        # 基于URL的特定错误检测
        if url:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # 特定网站的错误模式检测
            if 'allafrica.com' in domain and 'redirect' in error_str:
                return ErrorCategory.ANTI_CRAWLER
            elif 'nation.co.ke' in domain and 'cloudflare' in error_str:
                return ErrorCategory.ANTI_CRAWLER
                
        return ErrorCategory.UNKNOWN
    
    def get_error_profile(self, url: str) -> Dict[str, Any]:
        """根据URL获取错误处理配置"""
        try:
            domain = urlparse(url).netloc.lower()
            
            # 匹配非洲国家域名
            for suffix, profile in self.africa_error_profiles.items():
                if domain.endswith(suffix):
                    logger.info(f"检测到非洲网站 {domain}，应用错误处理配置: {profile}")
                    return profile
            
            # 默认配置
            default_profile = {
                'timeout_retries': 5,
                'connection_retries': 8,
                'rate_limit_retries': 3,
                'server_error_retries': 2,
                'strategy': RetryStrategy.EXPONENTIAL_BACKOFF
            }
            logger.info(f"非非洲网站 {domain}，使用默认错误处理配置")
            return default_profile
            
        except Exception as e:
            logger.warning(f"获取错误处理配置失败: {e}，使用默认配置")
            return {
                'timeout_retries': 5,
                'connection_retries': 8,
                'rate_limit_retries': 3,
                'server_error_retries': 2,
                'strategy': RetryStrategy.EXPONENTIAL_BACKOFF
            }
    
    def get_max_retries(self, url: str, error_category: ErrorCategory) -> int:
        """获取最大重试次数"""
        profile = self.get_error_profile(url)
        
        if error_category == ErrorCategory.TIMEOUT:
            return profile['timeout_retries']
        elif error_category == ErrorCategory.CONNECTION:
            return profile['connection_retries']
        elif error_category == ErrorCategory.RATE_LIMIT:
            return profile['rate_limit_retries']
        elif error_category == ErrorCategory.SERVER_ERROR:
            return profile['server_error_retries']
        elif error_category == ErrorCategory.SSL_ERROR:
            return profile.get('ssl_error_retries', 2)  # SSL错误重试次数
        elif error_category == ErrorCategory.DNS_ERROR:
            return profile.get('dns_error_retries', 2)  # DNS错误重试次数
        elif error_category == ErrorCategory.ANTI_CRAWLER:
            return profile.get('anti_crawler_retries', 3)  # 反爬虫错误重试次数
        else:
            return 3  # 未知错误默认重试3次
    
    def calculate_retry_delay(self, url: str, error_category: ErrorCategory, 
                             attempt: int, strategy: RetryStrategy) -> float:
        """计算重试延迟时间"""
        profile = self.get_error_profile(url)
        
        if strategy == RetryStrategy.ADAPTIVE:
            return self._adaptive_delay(url, error_category, attempt)
        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return self._exponential_backoff(attempt)
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            return self._linear_backoff(attempt)
        elif strategy == RetryStrategy.FIXED_DELAY:
            return self._fixed_delay()
        else:
            return self._exponential_backoff(attempt)
    
    def _adaptive_delay(self, url: str, error_category: ErrorCategory, attempt: int) -> float:
        """自适应延迟计算"""
        base_delay = self.adaptive_params['base_delay']
        max_delay = self.adaptive_params['max_delay']
        
        # 根据错误类型调整基础延迟
        error_multipliers = {
            ErrorCategory.TIMEOUT: 2.0,
            ErrorCategory.CONNECTION: 3.0,
            ErrorCategory.RATE_LIMIT: 4.0,
            ErrorCategory.SERVER_ERROR: 1.5,
            ErrorCategory.SSL_ERROR: 2.5,
            ErrorCategory.DNS_ERROR: 3.5,
            ErrorCategory.ANTI_CRAWLER: 5.0,
            ErrorCategory.UNKNOWN: 1.0
        }
        
        multiplier = error_multipliers.get(error_category, 1.0)
        
        # 根据重试次数增加延迟
        attempt_penalty = min(attempt * 10, 100)  # 每次重试增加10秒，最多100秒
        
        # 随机抖动
        random_jitter = random.uniform(0.8, 1.5)
        
        # 最终延迟时间
        final_delay = min(base_delay * multiplier * random_jitter + attempt_penalty, max_delay)
        
        logger.info(f"自适应延迟计算 - URL: {url}, 错误类型: {error_category.value}, "
                   f"重试次数: {attempt}, 延迟: {final_delay:.2f}秒")
        
        return final_delay
    
    def _exponential_backoff(self, attempt: int) -> float:
        """指数退避策略"""
        delay = min(self.adaptive_params['base_delay'] * (2 ** attempt), 
                   self.adaptive_params['max_delay'])
        return delay * random.uniform(0.8, 1.2)
    
    def _linear_backoff(self, attempt: int) -> float:
        """线性退避策略"""
        delay = min(self.adaptive_params['base_delay'] * attempt, 
                   self.adaptive_params['max_delay'])
        return delay * random.uniform(0.8, 1.2)
    
    def _fixed_delay(self) -> float:
        """固定延迟策略"""
        return self.adaptive_params['base_delay'] * random.uniform(0.8, 1.2)
    
    def should_retry(self, url: str, error_category: ErrorCategory, attempt: int) -> bool:
        """判断是否应该重试"""
        max_retries = self.get_max_retries(url, error_category)
        
        if attempt >= max_retries:
            logger.warning(f"达到最大重试次数 {max_retries}，停止重试 URL: {url}")
            return False
        
        # 某些错误类型不应该重试
        if error_category == ErrorCategory.CLIENT_ERROR and attempt > 1:
            logger.warning(f"客户端错误，减少重试次数 URL: {url}")
            return False
        
        return True
    
    def update_error_stats(self, error_category: ErrorCategory, recovery_success: bool):
        """更新错误统计"""
        self.error_stats['total_errors'] += 1
        
        if error_category == ErrorCategory.TIMEOUT:
            self.error_stats['timeout_errors'] += 1
        elif error_category == ErrorCategory.CONNECTION:
            self.error_stats['connection_errors'] += 1
        elif error_category == ErrorCategory.RATE_LIMIT:
            self.error_stats['rate_limit_errors'] += 1
        elif error_category == ErrorCategory.SERVER_ERROR:
            self.error_stats['server_errors'] += 1
        elif error_category == ErrorCategory.CLIENT_ERROR:
            self.error_stats['client_errors'] += 1
        elif error_category == ErrorCategory.SSL_ERROR:
            self.error_stats['ssl_errors'] += 1
        elif error_category == ErrorCategory.DNS_ERROR:
            self.error_stats['dns_errors'] += 1
        elif error_category == ErrorCategory.ANTI_CRAWLER:
            self.error_stats['anti_crawler_errors'] += 1
        
        if recovery_success:
            self.error_stats['successful_recoveries'] += 1
        else:
            self.error_stats['failed_recoveries'] += 1
    
    def get_error_report(self) -> Dict[str, Any]:
        """获取错误报告"""
        total_errors = self.error_stats['total_errors']
        
        if total_errors > 0:
            recovery_rate = self.error_stats['successful_recoveries'] / total_errors
        else:
            recovery_rate = 0
        
        return {
            'total_errors': total_errors,
            'timeout_errors': self.error_stats['timeout_errors'],
            'connection_errors': self.error_stats['connection_errors'],
            'rate_limit_errors': self.error_stats['rate_limit_errors'],
            'server_errors': self.error_stats['server_errors'],
            'client_errors': self.error_stats['client_errors'],
            'ssl_errors': self.error_stats.get('ssl_errors', 0),
            'dns_errors': self.error_stats.get('dns_errors', 0),
            'anti_crawler_errors': self.error_stats['anti_crawler_errors'],
            'recovery_rate': round(recovery_rate * 100, 2),
            'successful_recoveries': self.error_stats['successful_recoveries'],
            'failed_recoveries': self.error_stats['failed_recoveries'],
            'recommendations': self.generate_retry_recommendations()
        }
    
    def generate_retry_recommendations(self) -> List[str]:
        """生成重试建议"""
        recommendations = []
        total_errors = self.error_stats['total_errors']
        
        if total_errors == 0:
            return ["当前无错误记录，系统运行正常"]
        
        # 超时错误建议
        if self.error_stats['timeout_errors'] / total_errors > 0.3:
            recommendations.append("检测到大量超时错误，建议增加超时时间和重试次数")
        
        # 连接错误建议
        if self.error_stats['connection_errors'] / total_errors > 0.2:
            recommendations.append("检测到连接错误，建议检查网络连接和代理配置")
        
        # 速率限制建议
        if self.error_stats['rate_limit_errors'] > 0:
            recommendations.append("检测到速率限制，建议增加请求间隔时间")
        
        # 反爬虫错误建议
        if self.error_stats['anti_crawler_errors'] > 0:
            recommendations.append("检测到反爬虫措施，建议优化用户代理轮换和行为模拟")
        
        # 恢复率建议
        recovery_rate = self.error_stats['successful_recoveries'] / total_errors
        if recovery_rate < 0.5:
            recommendations.append("错误恢复率较低，建议优化重试策略和延迟计算")
        
        return recommendations
    
    def execute_with_retry(self, func: Callable, url: str, *args, **kwargs) -> Any:
        """执行带重试的函数"""
        attempt = 0
        max_attempts = 10  # 默认最大尝试次数
        
        while attempt < max_attempts:
            try:
                result = func(*args, **kwargs)
                
                # 如果函数成功执行，检查响应状态
                if hasattr(result, 'status_code') and result.status_code >= 400:
                    error_category = self.classify_error(Exception(f"HTTP {result.status_code}"), result)
                    
                    if self.should_retry(url, error_category, attempt):
                        delay = self.calculate_retry_delay(url, error_category, attempt, 
                                                         RetryStrategy.ADAPTIVE)
                        logger.warning(f"HTTP错误 {result.status_code}，第{attempt + 1}次重试，等待{delay:.2f}秒")
                        time.sleep(delay)
                        attempt += 1
                        continue
                    else:
                        self.update_error_stats(error_category, False)
                        raise Exception(f"HTTP错误 {result.status_code}，重试失败")
                
                # 成功执行
                if attempt > 0:
                    self.update_error_stats(ErrorCategory.UNKNOWN, True)
                
                return result
                
            except Exception as e:
                error_category = self.classify_error(e)
                
                if self.should_retry(url, error_category, attempt):
                    delay = self.calculate_retry_delay(url, error_category, attempt, 
                                                     RetryStrategy.ADAPTIVE)
                    logger.warning(f"错误类型: {error_category.value}，第{attempt + 1}次重试，等待{delay:.2f}秒")
                    time.sleep(delay)
                    attempt += 1
                else:
                    self.update_error_stats(error_category, False)
                    raise
        
        # 达到最大尝试次数
        raise Exception(f"达到最大重试次数 {max_attempts}，操作失败")

# 使用示例
def test_smart_retry_handler():
    """测试智能重试处理器"""
    handler = SmartRetryHandler()
    
    # 测试不同非洲网站
    test_urls = [
        "https://www.news24.com",  # 南非
        "https://www.nation.co.ke",  # 肯尼亚
        "https://www.punchng.com",  # 尼日利亚
        "https://www.google.com"  # 非非洲网站
    ]
    
    for url in test_urls:
        print(f"\n测试URL: {url}")
        profile = handler.get_error_profile(url)
        
        # 测试不同错误类型的重试配置
        error_types = [
            ErrorCategory.NETWORK_TIMEOUT,
            ErrorCategory.CONNECTION_ERROR,
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.SERVER_ERROR
        ]
        
        for error_type in error_types:
            max_retries = handler.get_max_retries(url, error_type)
            delay = handler.calculate_retry_delay(url, error_type, 1, profile['strategy'])
            
            print(f"错误类型: {error_type.value}")
            print(f"最大重试次数: {max_retries}")
            print(f"第一次重试延迟: {delay:.2f}秒")

if __name__ == "__main__":
    test_smart_retry_handler()