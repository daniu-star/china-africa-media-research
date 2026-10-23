#!/usr/bin/env python3
"""
非洲网站连接优化器
针对非洲网站的特殊网络环境进行优化
"""

import json
import time
import requests
from urllib.parse import urlparse

class AfricaConnectionOptimizer:
    """非洲网站连接优化器"""
    
    def __init__(self, config_file='africa_website_optimization.json'):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                return config_data.get('africa_website_optimization', {})
        except FileNotFoundError:
            print("❌ 配置文件不存在，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            "enabled": True,
            "special_handling": {
                "timeout_multiplier": 2.0,
                "retry_multiplier": 3,
                "delay_between_requests": 10,
                "user_agent_rotation": True,
                "proxy_priority": "africa_first"
            },
            "optimization_strategies": {
                "connection_timeout": 60,
                "read_timeout": 120,
                "max_retries": 5,
                "backoff_factor": 2,
                "user_agents": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                ]
            }
        }
    
    def get_optimized_settings(self, url):
        """获取针对特定URL的优化设置"""
        domain = urlparse(url).netloc
        
        # 获取基础设置
        base_settings = self.config.get('optimization_strategies', {}).copy()
        
        # 获取特殊处理设置
        special_handling = self.config.get('special_handling', {})
        
        # 应用超时倍增器
        timeout_multiplier = special_handling.get('timeout_multiplier', 2.0)
        base_settings['connection_timeout'] = int(base_settings.get('connection_timeout', 60) * timeout_multiplier)
        base_settings['read_timeout'] = int(base_settings.get('read_timeout', 120) * timeout_multiplier)
        
        # 应用重试倍增器
        retry_multiplier = special_handling.get('retry_multiplier', 3)
        base_settings['max_retries'] = base_settings.get('max_retries', 5) * retry_multiplier
        
        # 添加延迟设置
        base_settings['delay_between_requests'] = special_handling.get('delay_between_requests', 10)
        
        return base_settings
    
    def optimize_request(self, url, method='GET', **kwargs):
        """优化请求设置"""
        settings = self.get_optimized_settings(url)
        
        # 设置超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = (
                settings.get('connection_timeout', 120),
                settings.get('read_timeout', 180)
            )
        
        # 设置User-Agent
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        
        if 'User-Agent' not in kwargs['headers']:
            import random
            kwargs['headers']['User-Agent'] = random.choice(settings['user_agents'])
        
        return method, url, kwargs
    
    def execute_request_with_retry(self, url, method='GET', **kwargs):
        """执行带重试机制的请求"""
        settings = self.get_optimized_settings(url)
        max_retries = settings.get('max_retries', 15)  # 默认15次重试
        backoff_factor = settings.get('backoff_factor', 2)
        
        method, url, kwargs = self.optimize_request(url, method, **kwargs)
        
        for attempt in range(max_retries):
            try:
                response = requests.request(method, url, **kwargs)
                
                if response.status_code == 200:
                    return response
                else:
                    print(f"⚠️  尝试 {attempt + 1}/{max_retries}: 状态码 {response.status_code}")
                    
            except requests.exceptions.Timeout as e:
                print(f"⏰ 尝试 {attempt + 1}/{max_retries}: 超时错误 - {e}")
            except requests.exceptions.ConnectionError as e:
                print(f"🔌 尝试 {attempt + 1}/{max_retries}: 连接错误 - {e}")
            except Exception as e:
                print(f"❌ 尝试 {attempt + 1}/{max_retries}: 其他错误 - {e}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                delay = backoff_factor ** attempt  # 指数退避
                print(f"⏳ 等待 {delay} 秒后重试...")
                time.sleep(delay)
        
        raise Exception(f"❌ 所有 {max_retries} 次尝试均失败")

def test_optimized_connection():
    """测试优化后的连接"""
    optimizer = AfricaConnectionOptimizer()
    
    test_urls = [
        "http://www.dailymaverick.co.za",
        "https://www.thecitizen.co.tz",
        "http://allafrica.com",
        "http://httpbin.org/ip"  # 作为对比测试
    ]
    
    print("🚀 开始测试优化后的非洲网站连接")
    print("=" * 60)
    
    for url in test_urls:
        print(f"\n🔍 测试 URL: {url}")
        
        try:
            # 获取优化设置
            settings = optimizer.get_optimized_settings(url)
            print(f"   ⚙️  优化设置: 超时={settings.get('connection_timeout')}s, "
                  f"重试次数={settings.get('retry_attempts')}")
            
            # 执行请求
            start_time = time.time()
            response = optimizer.execute_request_with_retry(url)
            end_time = time.time()
            
            print(f"   ✅ 连接成功 - 状态码: {response.status_code}")
            print(f"   ⏱️  耗时: {end_time - start_time:.2f} 秒")
            
            if 'httpbin' in url:
                try:
                    ip_info = response.json()
                    print(f"   🌐 当前IP: {ip_info.get('origin', 'unknown')}")
                except:
                    pass
                    
        except Exception as e:
            print(f"   ❌ 连接失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")

if __name__ == "__main__":
    test_optimized_connection()