#!/usr/bin/env python3
"""
网络连接优化模块
专门针对非洲网站网络环境进行优化
"""

import time
import random
import logging
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
import socket

logger = logging.getLogger(__name__)

class NetworkOptimizer:
    """网络连接优化器"""
    
    def __init__(self):
        # 非洲网站网络特性数据库
        self.africa_network_profiles = {
            # 南非网站
            '.co.za': {'avg_latency': 15, 'timeout_multiplier': 2.0, 'retry_count': 8},
            '.za': {'avg_latency': 20, 'timeout_multiplier': 2.5, 'retry_count': 10},
            
            # 东非网站
            '.ke': {'avg_latency': 25, 'timeout_multiplier': 3.0, 'retry_count': 12},  # 肯尼亚
            '.ug': {'avg_latency': 30, 'timeout_multiplier': 3.5, 'retry_count': 15},  # 乌干达
            '.tz': {'avg_latency': 35, 'timeout_multiplier': 4.0, 'retry_count': 15},  # 坦桑尼亚
            
            # 西非网站
            '.ng': {'avg_latency': 40, 'timeout_multiplier': 4.5, 'retry_count': 25},  # 尼日利亚
            '.gh': {'avg_latency': 60, 'timeout_multiplier': 6.0, 'retry_count': 30},  # 加纳（Modern Ghana网站优化）
            '.ci': {'avg_latency': 50, 'timeout_multiplier': 5.5, 'retry_count': 25},  # 科特迪瓦
            
            # 北非网站
            '.eg': {'avg_latency': 20, 'timeout_multiplier': 2.0, 'retry_count': 8},  # 埃及
            '.ma': {'avg_latency': 25, 'timeout_multiplier': 2.5, 'retry_count': 10},  # 摩洛哥
            '.tn': {'avg_latency': 30, 'timeout_multiplier': 3.0, 'retry_count': 12},  # 突尼斯
            
            # 其他非洲地区
            '.et': {'avg_latency': 60, 'timeout_multiplier': 6.0, 'retry_count': 25},  # 埃塞俄比亚
            '.zm': {'avg_latency': 55, 'timeout_multiplier': 5.5, 'retry_count': 22},  # 赞比亚
            '.mw': {'avg_latency': 65, 'timeout_multiplier': 6.5, 'retry_count': 25},  # 马拉维
        }
        
        # 动态超时调整参数
        self.dynamic_timeout_base = 600  # 基础超时时间600秒（针对非洲网站优化）
        self.max_timeout = 1200  # 最大超时时间1200秒（针对Modern Ghana等高延迟网站）
        
        # 连接池配置
        self.connection_pool_size = 20
        self.keep_alive_timeout = 300
        
        # 性能统计
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_latency': 0,
            'timeout_events': 0
        }
    
    def get_network_profile(self, url: str) -> Dict[str, Any]:
        """根据URL获取网络特性配置"""
        try:
            domain = urlparse(url).netloc.lower()
            
            # 匹配非洲国家域名
            for suffix, profile in self.africa_network_profiles.items():
                if domain.endswith(suffix):
                    logger.info(f"检测到非洲网站 {domain}，应用网络配置: {profile}")
                    return profile
            
            # 默认配置（针对非非洲网站）
            default_profile = {
                'avg_latency': 10,
                'timeout_multiplier': 1.0,
                'retry_count': 5
            }
            logger.info(f"非非洲网站 {domain}，使用默认配置")
            return default_profile
            
        except Exception as e:
            logger.warning(f"获取网络配置失败: {e}，使用默认配置")
            return {
                'avg_latency': 10,
                'timeout_multiplier': 1.0,
                'retry_count': 5
            }
    
    def calculate_smart_timeout(self, url: str, attempt: int = 0) -> int:
        """计算智能超时时间"""
        profile = self.get_network_profile(url)
        
        # 基础超时时间
        base_timeout = self.dynamic_timeout_base * profile['timeout_multiplier']
        
        # 根据重试次数增加超时时间
        timeout_increase = min(attempt * 30, 300)  # 每次重试增加30秒，最多增加300秒
        
        # 最终超时时间
        final_timeout = min(base_timeout + timeout_increase, self.max_timeout)
        
        logger.info(f"URL: {url}, 重试次数: {attempt}, 智能超时: {final_timeout}秒")
        return int(final_timeout)
    
    def calculate_smart_delay(self, url: str, attempt: int = 0) -> float:
        """计算智能延迟时间"""
        profile = self.get_network_profile(url)
        
        # 基础延迟
        base_delay = profile['avg_latency'] * 0.1  # 平均延迟的10%
        
        # 随机抖动
        random_jitter = random.uniform(0.5, 2.0)
        
        # 重试延迟增加
        retry_penalty = min(attempt * 5, 30)  # 每次重试增加5秒，最多30秒
        
        # 最终延迟时间
        final_delay = max(base_delay * random_jitter + retry_penalty, 1.0)  # 最少1秒
        
        logger.info(f"URL: {url}, 重试次数: {attempt}, 智能延迟: {final_delay:.2f}秒")
        return final_delay
    
    def get_optimized_retry_config(self, url: str) -> Dict[str, Any]:
        """获取优化的重试配置"""
        profile = self.get_network_profile(url)
        domain = urlparse(url).netloc.lower()
        
        # 基础重试配置
        base_config = {
            'max_retries': profile['retry_count'],
            'backoff_factor': 2.0,
            'max_delay': 300,
            'retryable_status_codes': [500, 502, 503, 504, 408, 429],
            'retryable_exceptions': [
                socket.timeout,
                ConnectionError,
                ConnectionResetError,
                TimeoutError
            ]
        }
        
        # 智能重试策略：基于历史成功率调整
        success_rate = self.performance_stats.get(f'{domain}_success_rate', 0.8)
        if success_rate < 0.5:
            # 成功率低于50%，增加重试次数和延迟
            base_config['max_retries'] = min(8, base_config['max_retries'] + 2)
            base_config['backoff_factor'] = max(2.5, base_config['backoff_factor'])
        elif success_rate > 0.9:
            # 成功率高于90%，减少重试次数
            base_config['max_retries'] = max(2, base_config['max_retries'] - 1)
        
        # 针对403错误的特殊处理
        recent_403_count = self.performance_stats.get(f'{domain}_recent_403', 0)
        if recent_403_count > 3:
            # 频繁403错误，启用智能冷却策略
            base_config['max_retries'] = min(10, base_config['max_retries'] + 3)
            base_config['backoff_factor'] = max(3.0, base_config['backoff_factor'])
            base_config['enable_smart_cooldown'] = True
        
        return base_config
    
    def update_performance_stats(self, success: bool, latency: float, timeout: bool = False):
        """更新性能统计"""
        self.performance_stats['total_requests'] += 1
        
        if success:
            self.performance_stats['successful_requests'] += 1
        else:
            self.performance_stats['failed_requests'] += 1
            if timeout:
                self.performance_stats['timeout_events'] += 1
        
        # 更新平均延迟（移动平均）
        if self.performance_stats['total_requests'] > 0:
            current_avg = self.performance_stats['average_latency']
            new_avg = (current_avg * (self.performance_stats['total_requests'] - 1) + latency) / self.performance_stats['total_requests']
            self.performance_stats['average_latency'] = new_avg
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        total = self.performance_stats['total_requests']
        success = self.performance_stats['successful_requests']
        
        if total > 0:
            success_rate = success / total
        else:
            success_rate = 0
        
        return {
            'success_rate': round(success_rate * 100, 2),
            'total_requests': total,
            'successful_requests': success,
            'failed_requests': self.performance_stats['failed_requests'],
            'timeout_rate': round(self.performance_stats['timeout_events'] / total * 100, 2) if total > 0 else 0,
            'average_latency': round(self.performance_stats['average_latency'], 2),
            'recommendations': self.generate_recommendations()
        }
    
    def generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if self.performance_stats['timeout_events'] / self.performance_stats['total_requests'] > 0.3:
            recommendations.append("建议进一步增加超时时间到400秒以上")
        
        if self.performance_stats['failed_requests'] / self.performance_stats['total_requests'] > 0.5:
            recommendations.append("建议启用代理服务器和更智能的重试策略")
        
        if self.performance_stats['average_latency'] > 30:
            recommendations.append("检测到高延迟网络，建议优化连接池配置")
        
        return recommendations

# 使用示例
def test_network_optimizer():
    """测试网络优化器"""
    optimizer = NetworkOptimizer()
    
    # 测试不同非洲网站
    test_urls = [
        "https://www.news24.com",  # 南非
        "https://www.nation.co.ke",  # 肯尼亚
        "https://www.punchng.com",  # 尼日利亚
        "https://www.google.com"  # 非非洲网站
    ]
    
    for url in test_urls:
        print(f"\n测试URL: {url}")
        profile = optimizer.get_network_profile(url)
        timeout = optimizer.calculate_smart_timeout(url)
        delay = optimizer.calculate_smart_delay(url)
        retry_config = optimizer.get_optimized_retry_config(url)
        
        print(f"网络配置: {profile}")
        print(f"智能超时: {timeout}秒")
        print(f"智能延迟: {delay:.2f}秒")
        print(f"重试配置: {retry_config}")

if __name__ == "__main__":
    test_network_optimizer()