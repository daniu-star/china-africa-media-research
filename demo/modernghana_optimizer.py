"""
Modern Ghana网站专用优化模块
针对Modern Ghana网站连接超时问题的专项优化方案
"""

import time
import random
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ModernGhanaOptimizer:
    """Modern Ghana网站专用优化器"""
    
    def __init__(self):
        self.optimization_config = {
            # 超时配置
            'connect_timeout': 60,  # 连接超时60秒
            'read_timeout': 120,     # 读取超时120秒
            'max_timeout': 300,      # 最大超时300秒
            
            # 重试配置
            'max_retries': 8,        # 最大重试次数8次
            'base_delay': 10,        # 基础延迟10秒
            'max_delay': 120,        # 最大延迟120秒
            'backoff_factor': 2.0,   # 退避因子2.0
            
            # 连接优化
            'keep_alive': True,      # 启用连接保持
            'pool_connections': 10,  # 连接池大小10
            'pool_maxsize': 20,      # 最大连接数20
            
            # 代理策略
            'preferred_proxy_regions': ['ghana', 'nigeria', 'south africa', 'kenya'],
            'proxy_timeout': 180,    # 代理超时180秒
            
            # 智能延迟策略
            'peak_hours_delay_multiplier': 2.0,  # 高峰时段延迟倍数
            'weekend_delay_multiplier': 1.5,     # 周末延迟倍数
        }
        
        # 性能统计
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'timeout_errors': 0,
            'connection_errors': 0,
            'average_response_time': 0
        }
    
    def is_modernghana_url(self, url: str) -> bool:
        """检查是否为Modern Ghana网站URL"""
        try:
            domain = urlparse(url).netloc.lower()
            return 'modernghana.com' in domain
        except Exception:
            return False
    
    def calculate_smart_timeout(self, url: str, attempt: int = 0) -> tuple:
        """计算智能超时时间"""
        if not self.is_modernghana_url(url):
            return (self.optimization_config['connect_timeout'], 
                   self.optimization_config['read_timeout'])
        
        # Modern Ghana网站专用超时策略
        base_connect_timeout = self.optimization_config['connect_timeout']
        base_read_timeout = self.optimization_config['read_timeout']
        
        # 根据重试次数增加超时
        connect_timeout = min(base_connect_timeout + (attempt * 15), 
                            self.optimization_config['max_timeout'])
        read_timeout = min(base_read_timeout + (attempt * 30), 
                          self.optimization_config['max_timeout'])
        
        logger.info(f"Modern Ghana智能超时: 连接{connect_timeout}秒, 读取{read_timeout}秒, 重试{attempt}次")
        return (connect_timeout, read_timeout)
    
    def calculate_smart_delay(self, url: str, attempt: int = 0) -> float:
        """计算智能延迟时间"""
        if not self.is_modernghana_url(url):
            return max(1.0, random.uniform(2.0, 5.0))
        
        # Modern Ghana网站专用延迟策略
        base_delay = self.optimization_config['base_delay']
        max_delay = self.optimization_config['max_delay']
        
        # 指数退避延迟
        delay = min(base_delay * (self.optimization_config['backoff_factor'] ** attempt), 
                   max_delay)
        
        # 随机抖动
        delay_with_jitter = delay * random.uniform(0.8, 1.2)
        
        # 时间因素调整
        current_hour = time.localtime().tm_hour
        current_weekday = time.localtime().tm_wday
        
        # 高峰时段延迟增加
        if 9 <= current_hour <= 17:  # 工作时间
            delay_with_jitter *= self.optimization_config['peak_hours_delay_multiplier']
        
        # 周末延迟调整
        if current_weekday >= 5:  # 周末
            delay_with_jitter *= self.optimization_config['weekend_delay_multiplier']
        
        logger.info(f"Modern Ghana智能延迟: {delay_with_jitter:.2f}秒, 重试{attempt}次")
        return max(5.0, delay_with_jitter)  # 最少5秒
    
    def get_optimized_headers(self, url: str) -> Dict[str, str]:
        """获取优化的请求头"""
        if not self.is_modernghana_url(url):
            return {}
        
        # Modern Ghana网站专用请求头
        headers = {
            'User-Agent': self._get_modernghana_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GH,en;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        return headers
    
    def _get_modernghana_user_agent(self) -> str:
        """获取Modern Ghana网站专用User-Agent"""
        # Modern Ghana网站常用浏览器User-Agent
        user_agents = [
            # Chrome浏览器（加纳地区）
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Firefox浏览器
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            
            # Safari浏览器
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            
            # Edge浏览器
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        ]
        
        return random.choice(user_agents)
    
    def get_proxy_strategy(self, url: str) -> Dict[str, Any]:
        """获取代理策略"""
        if not self.is_modernghana_url(url):
            return {}
        
        # Modern Ghana网站专用代理策略
        return {
            'enabled': True,
            'preferred_regions': self.optimization_config['preferred_proxy_regions'],
            'timeout': self.optimization_config['proxy_timeout'],
            'max_retries': 3,
            'fallback_to_direct': True,  # 代理失败时回退到直接连接
        }
    
    def update_performance_stats(self, success: bool, response_time: float, 
                                error_type: Optional[str] = None):
        """更新性能统计"""
        self.performance_stats['total_requests'] += 1
        
        if success:
            self.performance_stats['successful_requests'] += 1
            # 更新平均响应时间
            if self.performance_stats['average_response_time'] == 0:
                self.performance_stats['average_response_time'] = response_time
            else:
                self.performance_stats['average_response_time'] = (
                    self.performance_stats['average_response_time'] * 0.9 + response_time * 0.1
                )
        else:
            if error_type == 'timeout':
                self.performance_stats['timeout_errors'] += 1
            elif error_type == 'connection':
                self.performance_stats['connection_errors'] += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        total = self.performance_stats['total_requests']
        success = self.performance_stats['successful_requests']
        
        if total > 0:
            success_rate = (success / total) * 100
            timeout_rate = (self.performance_stats['timeout_errors'] / total) * 100
            connection_error_rate = (self.performance_stats['connection_errors'] / total) * 100
        else:
            success_rate = timeout_rate = connection_error_rate = 0
        
        return {
            'total_requests': total,
            'success_rate': round(success_rate, 2),
            'timeout_error_rate': round(timeout_rate, 2),
            'connection_error_rate': round(connection_error_rate, 2),
            'average_response_time': round(self.performance_stats['average_response_time'], 2),
            'optimization_recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        total = self.performance_stats['total_requests']
        if total == 0:
            return ["暂无足够数据生成建议"]
        
        timeout_rate = self.performance_stats['timeout_errors'] / total
        connection_error_rate = self.performance_stats['connection_errors'] / total
        
        if timeout_rate > 0.3:
            recommendations.append("建议进一步增加超时时间到400秒以上")
        
        if connection_error_rate > 0.4:
            recommendations.append("建议优化代理服务器选择和连接池配置")
        
        if self.performance_stats['average_response_time'] > 60:
            recommendations.append("检测到高延迟，建议使用加纳本地代理服务器")
        
        if not recommendations:
            recommendations.append("当前配置表现良好，建议继续监控")
        
        return recommendations

# 使用示例
def test_modernghana_optimizer():
    """测试Modern Ghana优化器"""
    optimizer = ModernGhanaOptimizer()
    
    # 测试Modern Ghana URL
    test_url = "https://www.modernghana.com/news/1234567/example-article"
    
    print("=== Modern Ghana优化器测试 ===")
    print(f"URL: {test_url}")
    print(f"是否为Modern Ghana网站: {optimizer.is_modernghana_url(test_url)}")
    
    # 测试超时计算
    for attempt in range(3):
        timeout = optimizer.calculate_smart_timeout(test_url, attempt)
        print(f"重试{attempt}次 - 超时设置: {timeout}")
    
    # 测试延迟计算
    for attempt in range(3):
        delay = optimizer.calculate_smart_delay(test_url, attempt)
        print(f"重试{attempt}次 - 延迟设置: {delay:.2f}秒")
    
    # 测试请求头
    headers = optimizer.get_optimized_headers(test_url)
    print(f"优化请求头: {headers}")
    
    # 测试代理策略
    proxy_strategy = optimizer.get_proxy_strategy(test_url)
    print(f"代理策略: {proxy_strategy}")

if __name__ == "__main__":
    test_modernghana_optimizer()