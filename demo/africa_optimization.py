"""
非洲网站爬虫优化配置
专门针对非洲网站的网络特性、反爬虫机制和内容结构进行优化
"""

import random
from typing import Dict, List, Any

class AfricaCrawlerOptimizer:
    """非洲网站爬虫优化器"""
    
    # 非洲国家域名后缀列表
    AFRICAN_DOMAINS = [
        '.za', '.ng', '.ke', '.gh', '.tz', '.ug', '.zm', '.zw', 
        '.mw', '.mz', '.ao', '.bw', '.na', '.sz', '.ls', '.et',
        '.so', '.sd', '.ss', '.er', '.dj', '.km', '.mg', '.mu',
        '.sc', '.re', '.yt', '.rw', '.bi', '.cd', '.cg', '.ga',
        '.gq', '.cf', '.td', '.ne', '.ml', '.bf', '.bj', '.tg',
        '.ci', '.gn', '.gw', '.lr', '.sl', '.gm', '.sn', '.mr'
    ]
    
    # 非洲网站常见问题类型
    PROBLEM_SITES = {
        'high_latency': ['co.za', 'ng', 'ke', 'gh', 'tz'],  # 高延迟网站
        'strict_anti_bot': ['businesslive.co.za', 'guardian.ng', 'modernghana.com'],  # 严格反爬虫
        'ssl_issues': ['dailymaverick.co.za', 'thecitizen.co.tz'],  # SSL证书问题
        'slow_response': ['vanguardngr.com', 'punchng.com']  # 慢响应网站
    }
    
    @classmethod
    def is_african_site(cls, url: str) -> bool:
        """判断是否为非洲网站"""
        import urllib.parse
        domain = urllib.parse.urlparse(url).netloc.lower()
        return any(african_domain in domain for african_domain in cls.AFRICAN_DOMAINS)
    
    @classmethod
    def get_site_category(cls, url: str) -> str:
        """获取网站分类"""
        import urllib.parse
        domain = urllib.parse.urlparse(url).netloc.lower()
        
        for category, sites in cls.PROBLEM_SITES.items():
            if any(site in domain for site in sites):
                return category
        
        return 'normal'
    
    @classmethod
    def get_optimized_timeout(cls, url: str, attempt: int) -> float:
        """获取优化后的超时时间"""
        if not cls.is_african_site(url):
            # 非非洲网站使用标准超时
            return min(30.0 + attempt * 10, 60.0)
        
        category = cls.get_site_category(url)
        
        # 根据网站类别和重试次数设置超时
        if category == 'high_latency':
            return min(60.0 + attempt * 20, 120.0)
        elif category == 'slow_response':
            return min(45.0 + attempt * 15, 90.0)
        elif category == 'strict_anti_bot':
            return min(40.0 + attempt * 15, 80.0)
        else:
            return min(35.0 + attempt * 12, 70.0)
    
    @classmethod
    def get_optimized_delay(cls, url: str, attempt: int) -> float:
        """获取优化后的延迟时间"""
        if not cls.is_african_site(url):
            # 非非洲网站使用标准延迟
            return random.uniform(2.0, 5.0) + attempt * 2
        
        category = cls.get_site_category(url)
        
        # 根据网站类别和重试次数设置延迟
        if category == 'strict_anti_bot':
            return random.uniform(8.0, 15.0) + attempt * 5
        elif category == 'high_latency':
            return random.uniform(5.0, 10.0) + attempt * 3
        else:
            return random.uniform(3.0, 8.0) + attempt * 2
    
    @classmethod
    def get_max_retries(cls, url: str) -> int:
        """获取最大重试次数"""
        if not cls.is_african_site(url):
            return 3
        
        category = cls.get_site_category(url)
        
        # 非洲网站增加重试次数
        if category in ['high_latency', 'slow_response']:
            return 6  # 网络不稳定的网站增加重试
        elif category == 'strict_anti_bot':
            return 4  # 反爬虫严格的网站减少重试
        else:
            return 5
    
    @classmethod
    def get_smart_user_agents(cls, url: str) -> List[str]:
        """获取智能User-Agent列表"""
        # 基础User-Agent列表
        base_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/120.0"
        ]
        
        if not cls.is_african_site(url):
            return base_agents
        
        # 非洲网站添加更多User-Agent选择
        africa_agents = base_agents + [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
        ]
        
        return africa_agents
    
    @classmethod
    def should_use_proxy(cls, url: str, attempt: int) -> bool:
        """判断是否应该使用代理"""
        if not cls.is_african_site(url):
            return attempt >= 1  # 非非洲网站第一次尝试不使用代理
        
        category = cls.get_site_category(url)
        
        # 非洲网站根据类别决定代理使用策略
        if category == 'strict_anti_bot':
            return attempt >= 0  # 严格反爬虫网站始终使用代理
        elif category in ['high_latency', 'slow_response']:
            return attempt >= 2  # 网络问题网站延迟使用代理
        else:
            return attempt >= 1
    
    @classmethod
    def get_optimization_recommendations(cls, url: str) -> List[str]:
        """获取优化建议"""
        recommendations = []
        
        if not cls.is_african_site(url):
            return ["标准爬取策略"]
        
        category = cls.get_site_category(url)
        
        if category == 'high_latency':
            recommendations.extend([
                "增加超时时间至60-120秒",
                "使用连接保持策略",
                "启用自动重试机制",
                "降低并行请求数量"
            ])
        
        if category == 'strict_anti_bot':
            recommendations.extend([
                "使用高质量代理",
                "频繁轮换User-Agent",
                "增加请求延迟",
                "模拟人类行为模式"
            ])
        
        if category == 'ssl_issues':
            recommendations.extend([
                "禁用SSL验证",
                "使用HTTP备用方案",
                "增加连接超时"
            ])
        
        if category == 'slow_response':
            recommendations.extend([
                "大幅增加读取超时",
                "使用渐进式超时策略",
                "启用连接池优化"
            ])
        
        return recommendations

# 导出优化配置
def get_africa_optimized_config() -> Dict[str, Any]:
    """获取非洲网站优化配置"""
    return {
        "timeout_strategy": "adaptive",  # 自适应超时策略
        "max_retries": 5,  # 最大重试次数
        "base_timeout": 60.0,  # 基础超时时间
        "max_timeout": 120.0,  # 最大超时时间
        "delay_range": [3.0, 15.0],  # 延迟范围
        "user_agent_rotation": True,  # User-Agent轮换
        "proxy_enabled": True,  # 代理启用
        "connection_pool_size": 10,  # 连接池大小
        "keep_alive": True,  # 连接保持
        "retry_on_failure": True  # 失败重试
    }