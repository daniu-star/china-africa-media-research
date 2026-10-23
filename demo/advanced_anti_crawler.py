"""
高级反爬虫检测与规避模块
实现智能反爬虫策略，包括请求随机化、浏览器指纹模拟等
"""

import time
import random
import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AdvancedAntiCrawler:
    """高级反爬虫检测与规避系统"""
    
    def __init__(self):
        # 反爬虫检测配置
        self.detection_config = {
            'max_403_retries': 5,           # 403错误最大重试次数
            'max_429_retries': 3,           # 429错误最大重试次数
            'ban_detection_threshold': 3,    # 封禁检测阈值
            'ban_cooldown_minutes': 30,      # 封禁冷却时间（分钟）
            'request_jitter_range': (0.5, 2.0),  # 请求抖动范围
            'session_duration_minutes': 60,  # 会话持续时间
        }
        
        # 浏览器指纹配置
        self.fingerprint_config = {
            'user_agent_pool_size': 50,      # User-Agent池大小
            'accept_language_pool': [       # 接受语言池
                'en-US,en;q=0.9',
                'en-GB,en;q=0.8',
                'en-CA,en;q=0.7',
                'en-AU,en;q=0.6',
                'en-ZA,en;q=0.5'
            ],
            'screen_resolutions': [         # 屏幕分辨率池
                '1920x1080', '1366x768', '1536x864',
                '1440x900', '1280x720', '1600x900'
            ],
            'timezone_offsets': [           # 时区偏移池
                '-300', '-240', '-180', '-120', '-60', '0',
                '60', '120', '180', '240', '300', '360', '420'
            ]
        }
        
        # 状态跟踪
        self.website_status = {}  # 网站状态跟踪
        self.session_tracker = {}  # 会话跟踪
        self.error_patterns = {}   # 错误模式分析
        
        # 初始化浏览器指纹池
        self._init_fingerprint_pools()
    
    def _init_fingerprint_pools(self):
        """初始化浏览器指纹池"""
        # User-Agent池
        self.user_agents = self._generate_user_agent_pool()
        
        # 浏览器指纹特征池
        self.browser_fingerprints = self._generate_browser_fingerprints()
        
        logger.info(f"浏览器指纹池初始化完成: {len(self.user_agents)}个User-Agent")
    
    def _generate_user_agent_pool(self) -> List[str]:
        """生成User-Agent池"""
        user_agents = []
        
        # Chrome浏览器（不同版本和平台）
        chrome_versions = ['120.0.0.0', '119.0.0.0', '118.0.0.0', '117.0.0.0', '116.0.0.0']
        for version in chrome_versions:
            user_agents.extend([
                f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36',
                f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36',
                f'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36',
                f'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36',
            ])
        
        # Firefox浏览器
        firefox_versions = ['121.0', '120.0', '119.0', '118.0', '117.0']
        for version in firefox_versions:
            user_agents.extend([
                f'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}) Gecko/20100101 Firefox/{version}',
                f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:{version}) Gecko/20100101 Firefox/{version}',
                f'Mozilla/5.0 (X11; Linux x86_64; rv:{version}) Gecko/20100101 Firefox/{version}',
            ])
        
        # Safari浏览器
        safari_versions = ['17.1', '17.0', '16.6', '16.5', '16.4']
        for version in safari_versions:
            user_agents.extend([
                f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15',
            ])
        
        # Edge浏览器
        edge_versions = ['120.0.0.0', '119.0.0.0', '118.0.0.0']
        for version in edge_versions:
            user_agents.extend([
                f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 Edg/{version}',
            ])
        
        return user_agents
    
    def _generate_browser_fingerprints(self) -> List[Dict[str, Any]]:
        """生成浏览器指纹特征"""
        fingerprints = []
        
        for i in range(self.fingerprint_config['user_agent_pool_size']):
            fingerprint = {
                'user_agent': random.choice(self.user_agents),
                'accept_language': random.choice(self.fingerprint_config['accept_language_pool']),
                'screen_resolution': random.choice(self.fingerprint_config['screen_resolutions']),
                'timezone_offset': random.choice(self.fingerprint_config['timezone_offsets']),
                'platform': random.choice(['Win32', 'MacIntel', 'Linux x86_64']),
                'hardware_concurrency': random.choice([4, 8, 12, 16]),
                'device_memory': random.choice([4, 8, 16]),
                'color_depth': random.choice([24, 30, 32]),
                'pixel_ratio': random.choice([1.0, 1.25, 1.5, 2.0]),
                'sec_ch_ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua_platform': random.choice(['"Windows"', '"macOS"', '"Linux"']),
                'dnt': random.choice(['0', '1']),
                'sec_gpc': random.choice(['0', '1']),
            }
            fingerprints.append(fingerprint)
        
        return fingerprints

    def get_deep_fingerprint(self, domain: str) -> Dict[str, Any]:
        """获取深度指纹 - 包含更多浏览器特征"""
        # 获取基础指纹
        session_id = self._get_session_fingerprint(domain)
        base_fingerprint = self.browser_fingerprints[session_id % len(self.browser_fingerprints)]
        
        # 创建深度指纹
        deep_fingerprint = base_fingerprint.copy()
        
        # 添加深度特征
        deep_fingerprint.update({
            'sec_fetch_dest': 'document',
            'sec_fetch_mode': 'navigate',
            'sec_fetch_site': 'none',
            'sec_fetch_user': '?1',
            'viewport_width': deep_fingerprint['screen_resolution'].split('x')[0],
            'viewport_height': deep_fingerprint['screen_resolution'].split('x')[1],
            'accept_encoding': 'gzip, deflate, br',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'cache_control': 'max-age=0',
            'upgrade_insecure_requests': '1',
        })
        
        # 针对非洲网站的特殊深度特征
        african_domains = ['.co.za', '.co.ke', '.com.gh', '.com.ng', '.co.tz', '.co.ug', '.rw']
        is_african_site = any(domain.endswith(ext) for ext in african_domains)
        
        if is_african_site:
            deep_fingerprint.update({
                'x_requested_with': 'XMLHttpRequest',
                'x_forwarded_for': self._generate_random_ip(),
                'referer': self._generate_african_referer(domain),
            })
        
        return deep_fingerprint
    
    def get_optimized_headers(self, url: str, domain: str = None, deep_change: bool = False) -> Dict[str, str]:
        """获取优化的请求头（包含浏览器指纹） - 针对非洲网站优化"""
        if domain is None:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
        
        # 检测是否为非洲网站
        african_domains = ['.co.za', '.co.ke', '.com.gh', '.com.ng', '.co.tz', '.co.ug', '.rw']
        is_african_site = any(domain.endswith(ext) for ext in african_domains)
        
        # 获取或创建域名的会话指纹
        session_id = self._get_session_fingerprint(domain)
        fingerprint = self.browser_fingerprints[session_id % len(self.browser_fingerprints)]
        
        # 基础请求头
        headers = {
            'User-Agent': fingerprint['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
        }
        
        # 深度指纹变更：添加更多浏览器特征
        if deep_change:
            headers.update({
                'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"' + fingerprint['platform'] + '"',
                'Sec-GPC': '1',
            })
        
        # 针对非洲网站的特殊配置
        if is_african_site:
            # 非洲地区语言偏好
            african_languages = [
                'en-US,en;q=0.9',  # 英语（南非、肯尼亚、加纳等）
                'fr-FR,fr;q=0.9',  # 法语（科特迪瓦、塞内加尔等）
                'pt-PT,pt;q=0.9',  # 葡萄牙语（安哥拉、莫桑比克等）
                'ar-SA,ar;q=0.8',  # 阿拉伯语（北非地区）
                'sw-KE,sw;q=0.7',  # 斯瓦希里语（东非）
            ]
            headers['Accept-Language'] = random.choice(african_languages)
            
            # 非洲地区常见的额外请求头
            headers.update({
                'Referer': self._generate_african_referer(domain),
                'X-Requested-With': 'XMLHttpRequest',
                'X-Forwarded-For': self._generate_random_ip(),
            })
        else:
            # 非非洲网站的默认配置
            headers['Accept-Language'] = fingerprint['accept_language']
            
            # 添加现代浏览器安全头
            headers.update({
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            })
        
        # 添加浏览器特征头
        headers.update({
            'Viewport-Width': fingerprint['screen_resolution'].split('x')[0],
            'Sec-CH-UA-Platform': '"' + fingerprint['platform'] + '"',
        })
        
        logger.debug(f"为网站 {domain} 生成优化请求头 (非洲网站: {is_african_site}, 深度变更: {deep_change})")
        return headers
    
    def _get_session_fingerprint(self, domain: str) -> int:
        """获取或创建域名的会话指纹"""
        current_time = time.time()
        
        if domain in self.session_tracker:
            session_info = self.session_tracker[domain]
            # 检查会话是否过期
            if current_time - session_info['created_at'] < self.detection_config['session_duration_minutes'] * 60:
                return session_info['fingerprint_id']
        
        # 创建新的会话指纹
        fingerprint_id = random.randint(0, len(self.browser_fingerprints) - 1)
        self.session_tracker[domain] = {
            'fingerprint_id': fingerprint_id,
            'created_at': current_time,
            'request_count': 0
        }
        
        return fingerprint_id
    
    def _generate_african_referer(self, domain: str) -> str:
        """为非洲网站生成合适的Referer"""
        # 非洲地区常见的搜索引擎和社交媒体作为Referer
        referer_sources = [
            f"https://www.google.com/search?q={domain.replace('.', '+')}",
            f"https://www.bing.com/search?q={domain}",
            f"https://www.facebook.com/",
            f"https://twitter.com/",
            f"https://www.linkedin.com/",
            f"https://www.instagram.com/",
            f"https://news.google.com/",
            f"https://www.youtube.com/",
        ]
        return random.choice(referer_sources)
    
    def _generate_random_ip(self) -> str:
        """生成随机IP地址"""
        # 生成非洲地区的IP地址范围
        african_ip_ranges = [
            ("41.", "41.0.0.0/8"),  # 南非
            ("102.", "102.0.0.0/8"),  # 尼日利亚
            ("105.", "105.0.0.0/8"),  # 肯尼亚
            ("154.", "154.0.0.0/8"),  # 加纳
            ("197.", "197.0.0.0/8"),  # 坦桑尼亚
            ("196.", "196.0.0.0/8"),  # 乌干达
        ]
        
        prefix, _ = random.choice(african_ip_ranges)
        return f"{prefix}{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    
    def calculate_smart_delay(self, url: str, attempt: int = 0, last_status_code: int = None) -> float:
        """计算智能延迟时间"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        base_delay = 2.0  # 基础延迟
        
        # 根据状态码调整延迟
        if last_status_code == 429:  # 频率限制
            base_delay *= 3.0
        elif last_status_code == 403:  # 禁止访问
            base_delay *= 2.0
        
        # 根据尝试次数指数退避
        delay = base_delay * (2.0 ** attempt)
        
        # 添加随机抖动
        jitter_min, jitter_max = self.detection_config['request_jitter_range']
        delay_with_jitter = delay * random.uniform(jitter_min, jitter_max)
        
        # 检查网站状态
        if domain in self.website_status:
            site_status = self.website_status[domain]
            
            # 如果网站有封禁历史，增加延迟
            if site_status.get('banned', False):
                delay_with_jitter *= 2.0
            
            # 根据错误率调整延迟
            error_rate = site_status.get('error_rate', 0)
            if error_rate > 0.5:  # 错误率超过50%
                delay_with_jitter *= (1.0 + error_rate)
        
        # 限制最大延迟为120秒
        max_delay = min(delay_with_jitter, 120.0)
        
        logger.info(f"智能延迟计算: 基础{base_delay:.1f}s, 尝试{attempt}, 状态码{last_status_code}, 最终{max_delay:.1f}s")
        return max_delay
    
    def handle_anti_crawler_response(self, url: str, status_code: int, response_headers: Dict[str, str]) -> Dict[str, Any]:
        """处理反爬虫响应"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        # 更新网站状态
        self._update_website_status(domain, status_code)
        
        action = {
            'should_retry': False,
            'delay_before_retry': 0.0,
            'change_fingerprint': False,
            'ban_detected': False,
            'recommendation': 'continue'
        }
        
        # 分析状态码
        if status_code == 200:
            action['recommendation'] = 'success'
            
        elif status_code == 403:  # 禁止访问
            action = self._handle_403_response(domain, action)
            
        elif status_code == 429:  # 频率限制
            action = self._handle_429_response(domain, response_headers, action)
            
        elif status_code >= 500:  # 服务器错误
            action = self._handle_server_error(domain, action)
        
        return action
    
    def _update_website_status(self, domain: str, status_code: int):
        """更新网站状态"""
        if domain not in self.website_status:
            self.website_status[domain] = {
                'total_requests': 0,
                'successful_requests': 0,
                'error_requests': 0,
                'last_403_time': None,
                'last_429_time': None,
                'consecutive_errors': 0,
                'banned': False,
                'ban_start_time': None
            }
        
        status = self.website_status[domain]
        status['total_requests'] += 1
        
        if status_code == 200:
            status['successful_requests'] += 1
            status['consecutive_errors'] = 0
        else:
            status['error_requests'] += 1
            status['consecutive_errors'] += 1
            
            if status_code == 403:
                status['last_403_time'] = time.time()
            elif status_code == 429:
                status['last_429_time'] = time.time()
        
        # 计算错误率
        if status['total_requests'] > 0:
            status['error_rate'] = status['error_requests'] / status['total_requests']
        
        # 检测封禁
        self._detect_ban_status(domain, status)
    
    def _detect_ban_status(self, domain: str, status: Dict[str, Any]):
        """检测封禁状态"""
        current_time = time.time()
        
        # 如果连续错误超过阈值，标记为封禁
        if status['consecutive_errors'] >= self.detection_config['ban_detection_threshold']:
            if not status['banned']:
                status['banned'] = True
                status['ban_start_time'] = current_time
                logger.warning(f"检测到网站 {domain} 可能被封禁")
        
        # 检查封禁冷却时间
        if status['banned'] and status['ban_start_time']:
            ban_duration = current_time - status['ban_start_time']
            if ban_duration > self.detection_config['ban_cooldown_minutes'] * 60:
                status['banned'] = False
                status['ban_start_time'] = None
                status['consecutive_errors'] = 0
                logger.info(f"网站 {domain} 封禁冷却期结束")
    
    def _handle_403_response(self, domain: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """处理403响应 - 针对非洲网站优化的智能策略"""
        status = self.website_status.get(domain, {})
        
        # 检查403错误次数
        error_count = status.get('consecutive_errors', 0)
        
        # 针对非洲网站的智能403处理策略
        african_domains = ['.co.za', '.co.ke', '.com.gh', '.com.ng', '.co.tz', '.co.ug', '.rw']
        is_african_site = any(domain.endswith(ext) for ext in african_domains)
        
        if is_african_site:
            # 非洲网站专用403处理策略 - 更智能的持续重试
            if error_count <= 15:  # 前15次403错误，持续重试
                action['should_retry'] = True
                # 动态延迟：基于错误计数和网站类型
                if error_count <= 5:
                    # 前5次：5-15秒延迟
                    action['delay_before_retry'] = random.uniform(5.0, 15.0)
                elif error_count <= 10:
                    # 6-10次：15-30秒延迟
                    action['delay_before_retry'] = random.uniform(15.0, 30.0)
                else:
                    # 11-15次：30-60秒延迟
                    action['delay_before_retry'] = random.uniform(30.0, 60.0)
                
                action['change_fingerprint'] = True
                action['recommendation'] = 'retry_with_new_fingerprint'
                logger.info(f"非洲网站 {domain} 403错误处理: 持续重试 (错误计数: {error_count}, 延迟: {action['delay_before_retry']:.1f}秒)")
            
            elif error_count <= 25:  # 16-25次403错误，延长重试
                action['should_retry'] = True
                # 延长延迟：60-120秒
                action['delay_before_retry'] = random.uniform(60.0, 120.0)
                action['change_fingerprint'] = True
                action['recommendation'] = 'retry_with_extended_delay'
                logger.info(f"非洲网站 {domain} 403错误处理: 延长重试 (错误计数: {error_count}, 延迟: {action['delay_before_retry']:.1f}秒)")
            
            elif error_count <= 40:  # 26-40次403错误，智能冷却后继续
                action['should_retry'] = True
                # 智能冷却：基于错误率计算冷却时间
                error_rate = status.get('error_rate', 0)
                cooldown_time = max(120.0, error_rate * 300.0)  # 最少2分钟，最多5分钟
                action['delay_before_retry'] = cooldown_time
                action['change_fingerprint'] = True
                action['recommendation'] = 'retry_after_cooldown'
                logger.warning(f"非洲网站 {domain} 403错误处理: 智能冷却后继续 (错误计数: {error_count}, 冷却: {cooldown_time:.1f}秒)")
            
            else:  # 超过40次403错误，启用高级规避策略
                action['should_retry'] = True
                # 高级规避：长时间冷却 + 深度指纹变更
                cooldown_time = random.uniform(300.0, 600.0)  # 5-10分钟冷却
                action['delay_before_retry'] = cooldown_time
                action['change_fingerprint'] = True
                action['deep_fingerprint_change'] = True  # 深度指纹变更
                action['recommendation'] = 'retry_with_deep_fingerprint_change'
                logger.warning(f"非洲网站 {domain} 403错误处理: 高级规避策略 (错误计数: {error_count}, 深度冷却: {cooldown_time:.1f}秒)")
        
        else:
            # 非非洲网站的默认403处理策略
            if error_count <= self.detection_config['max_403_retries']:
                action['should_retry'] = True
                action['delay_before_retry'] = self.calculate_smart_delay('', error_count, 403)
                action['change_fingerprint'] = True
                action['recommendation'] = 'retry_with_new_fingerprint'
            else:
                action['ban_detected'] = True
                action['recommendation'] = 'wait_for_cooldown'
        
        return action
    
    def _handle_429_response(self, domain: str, headers: Dict[str, str], action: Dict[str, Any]) -> Dict[str, Any]:
        """处理429响应"""
        status = self.website_status.get(domain, {})
        error_count = status.get('consecutive_errors', 0)
        
        if error_count <= self.detection_config['max_429_retries']:
            action['should_retry'] = True
            
            # 从响应头获取重试时间
            retry_after = headers.get('Retry-After')
            if retry_after:
                try:
                    delay = float(retry_after)
                except ValueError:
                    delay = self.calculate_smart_delay('', error_count, 429)
            else:
                delay = self.calculate_smart_delay('', error_count, 429)
            
            action['delay_before_retry'] = delay
            action['recommendation'] = 'retry_after_delay'
        else:
            action['ban_detected'] = True
            action['recommendation'] = 'wait_for_cooldown'
        
        return action
    
    def _handle_server_error(self, domain: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """处理服务器错误"""
        action['should_retry'] = True
        action['delay_before_retry'] = self.calculate_smart_delay('', 0, 500)
        action['recommendation'] = 'retry_after_delay'
        
        return action
    
    def get_website_status_report(self, domain: str = None) -> Dict[str, Any]:
        """获取网站状态报告"""
        if domain:
            return self.website_status.get(domain, {})
        else:
            return {
                'total_websites': len(self.website_status),
                'banned_websites': sum(1 for s in self.website_status.values() if s.get('banned', False)),
                'websites': self.website_status
            }

# 全局实例
advanced_anti_crawler = AdvancedAntiCrawler()