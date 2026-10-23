#!/usr/bin/env python3
"""
反爬虫规避模块
专门针对非洲网站的反爬虫机制进行优化
"""

import random
import time
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import hashlib

logger = logging.getLogger(__name__)

class AntiAntiCrawler:
    """反爬虫规避器"""
    
    def __init__(self):
        # 非洲网站反爬虫特性数据库
        self.africa_anti_crawler_profiles = {
            # 南非网站
            '.co.za': {
                'user_agent_rotation': 'high',
                'request_delay': 15,
                'javascript_rendering': 'medium',
                'captcha_detection': 'low',
                'behavior_simulation': 'high'
            },
            
            # 东非网站
            '.ke': {
                'user_agent_rotation': 'medium',
                'request_delay': 20,
                'javascript_rendering': 'low',
                'captcha_detection': 'low',
                'behavior_simulation': 'medium'
            },
            
            # 西非网站
            '.ng': {
                'user_agent_rotation': 'high',
                'request_delay': 25,
                'javascript_rendering': 'high',
                'captcha_detection': 'medium',
                'behavior_simulation': 'high'
            },
            
            # 北非网站
            '.eg': {
                'user_agent_rotation': 'medium',
                'request_delay': 10,
                'javascript_rendering': 'medium',
                'captcha_detection': 'high',
                'behavior_simulation': 'medium'
            }
        }
        
        # 用户代理池
        self.user_agents = self._load_user_agents()
        
        # 行为模拟参数
        self.behavior_patterns = {
            'mouse_movement': True,
            'scroll_behavior': True,
            'click_patterns': True,
            'time_spent': True
        }
        
        # 会话管理
        self.session_tracker = {}
        
        # 检测统计
        self.detection_stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'captcha_encounters': 0,
            'rate_limit_hits': 0
        }
    
    def _load_user_agents(self) -> List[str]:
        """加载用户代理池"""
        return [
            # Chrome 浏览器
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            
            # Firefox 浏览器
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux i686; rv:121.0) Gecko/20100101 Firefox/121.0",
            
            # Safari 浏览器
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            
            # Edge 浏览器
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            
            # 非洲本地浏览器
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",  # 非洲常见版本
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",  # 较旧版本
        ]
    
    def get_anti_crawler_profile(self, url: str) -> Dict[str, Any]:
        """根据URL获取反爬虫配置"""
        try:
            domain = urlparse(url).netloc.lower()
            
            # 匹配非洲国家域名
            for suffix, profile in self.africa_anti_crawler_profiles.items():
                if domain.endswith(suffix):
                    logger.info(f"检测到非洲网站 {domain}，应用反爬虫配置: {profile}")
                    return profile
            
            # 默认配置
            default_profile = {
                'user_agent_rotation': 'medium',
                'request_delay': 10,
                'javascript_rendering': 'low',
                'captcha_detection': 'low',
                'behavior_simulation': 'medium'
            }
            logger.info(f"非非洲网站 {domain}，使用默认反爬虫配置")
            return default_profile
            
        except Exception as e:
            logger.warning(f"获取反爬虫配置失败: {e}，使用默认配置")
            return {
                'user_agent_rotation': 'medium',
                'request_delay': 10,
                'javascript_rendering': 'low',
                'captcha_detection': 'low',
                'behavior_simulation': 'medium'
            }
    
    def get_rotated_user_agent(self, url: str) -> str:
        """获取轮换的用户代理"""
        domain = urlparse(url).netloc
        
        # 特殊处理nation.co.ke网站 - 更激进的User-Agent轮换策略
        if 'nation.co.ke' in domain:
            # nation.co.ke专用User-Agent池
            nation_ke_agents = [
                # 最新Chrome版本
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                
                # 较旧但稳定的Chrome版本
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                
                # Firefox版本
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
                
                # Safari版本
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
                
                # Edge版本
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
                
                # 移动设备User-Agent
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36"
            ]
            
            # 每次请求都强制更换User-Agent
            user_agent = random.choice(nation_ke_agents)
            logger.info(f"nation.co.ke网站启用激进User-Agent轮换: {user_agent[:50]}...")
            return user_agent
        
        profile = self.get_anti_crawler_profile(url)
        
        # 根据配置选择轮换策略
        if profile['user_agent_rotation'] == 'high':
            # 高频轮换：每次请求都更换
            user_agent = random.choice(self.user_agents)
        elif profile['user_agent_rotation'] == 'medium':
            # 中频轮换：每5次请求更换一次
            if domain not in self.session_tracker:
                self.session_tracker[domain] = {'request_count': 0, 'current_ua': random.choice(self.user_agents)}
            
            tracker = self.session_tracker[domain]
            tracker['request_count'] += 1
            
            if tracker['request_count'] % 5 == 0:
                tracker['current_ua'] = random.choice(self.user_agents)
            
            user_agent = tracker['current_ua']
        else:
            # 低频轮换：每个会话使用固定UA
            if domain not in self.session_tracker:
                self.session_tracker[domain] = {'current_ua': random.choice(self.user_agents)}
            
            user_agent = self.session_tracker[domain]['current_ua']
        
        logger.debug(f"为 {url} 选择用户代理: {user_agent[:50]}...")
        return user_agent
    
    def calculate_smart_delay(self, url: str, request_count: int = 0) -> float:
        """计算智能延迟时间"""
        domain = urlparse(url).netloc
        
        # 特殊处理nation.co.ke网站 - 更长的延迟策略
        if 'nation.co.ke' in domain:
            # nation.co.ke专用延迟策略
            base_delay = 8.0  # 基础延迟8秒
            
            # 根据请求次数增加延迟，但更激进
            if request_count == 0:
                delay = base_delay
            elif request_count == 1:
                delay = base_delay * 2.5  # 第二次请求20秒
            elif request_count == 2:
                delay = base_delay * 4.0  # 第三次请求32秒
            elif request_count == 3:
                delay = base_delay * 6.0  # 第四次请求48秒
            elif request_count == 4:
                delay = base_delay * 8.0  # 第五次请求64秒
            else:
                delay = base_delay * 10.0  # 第六次请求80秒
            
            # 添加随机抖动
            jitter = random.uniform(0.7, 1.3)
            delay = delay * jitter
            
            # 限制最大延迟为120秒
            delay = min(delay, 120.0)
            
            logger.info(f"nation.co.ke智能延迟: {delay:.2f}秒 (请求计数: {request_count})")
            return delay
        
        profile = self.get_anti_crawler_profile(url)
        
        # 基础延迟
        base_delay = profile['request_delay']
        
        # 随机抖动
        random_jitter = random.uniform(0.8, 1.5)
        
        # 请求频率惩罚（防止短时间内大量请求）
        frequency_penalty = min(request_count * 0.5, 10)
        
        # 最终延迟时间
        final_delay = max(base_delay * random_jitter + frequency_penalty, 3.0)
        
        logger.debug(f"URL: {url}, 请求计数: {request_count}, 智能延迟: {final_delay:.2f}秒")
        return final_delay
    
    def get_optimized_headers(self, url: str) -> Dict[str, str]:
        """获取优化的请求头 - 根据目标网站特性定制"""
        # 获取轮换的用户代理
        user_agent = self.get_rotated_user_agent(url)
        
        # 基础请求头
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # 根据网站类型添加特定头部
        domain = urlparse(url).netloc.lower()
        
        if 'news24' in domain or 'allafrica' in domain:
            # 新闻网站可能需要特定的Referer
            headers['Referer'] = 'https://www.google.com/'
        elif 'ahram' in domain or 'nation' in domain:
            # 非洲本地新闻网站可能需要本地化头部
            headers['Accept-Language'] = 'en-US,en;q=0.8,fr;q=0.6,ar;q=0.4'
        
        # 添加浏览器指纹相关的请求头
        headers.update(self._generate_fingerprint_headers(url))
        
        logger.debug(f"为 {url} 生成优化请求头，User-Agent: {user_agent[:50]}...")
        return headers

    def get_optimized_proxy(self, url: str) -> Optional[Dict[str, str]]:
        """获取优化的代理配置 - 针对nation.co.ke网站优化"""
        domain = urlparse(url).netloc
        
        # 特殊处理nation.co.ke网站 - 智能代理策略
        if 'nation.co.ke' in domain:
            logger.info("nation.co.ke网站启用智能代理策略")
            
            # nation.co.ke专用代理策略 - 更真实的代理池
            nation_ke_proxies = [
                # 肯尼亚本地代理优先
                {'http': 'http://proxy-ke-1.nation.com:8080', 'https': 'https://proxy-ke-1.nation.com:8080'},
                {'http': 'http://proxy-ke-2.nation.com:8080', 'https': 'https://proxy-ke-2.nation.com:8080'},
                {'http': 'http://proxy-ke-3.nation.com:8080', 'https': 'https://proxy-ke-3.nation.com:8080'},
                
                # 东非地区代理
                {'http': 'http://proxy-tz-1.eastafrica.com:8080', 'https': 'https://proxy-tz-1.eastafrica.com:8080'},
                {'http': 'http://proxy-ug-1.eastafrica.com:8080', 'https': 'https://proxy-ug-1.eastafrica.com:8080'},
                
                # 南非地区代理
                {'http': 'http://proxy-za-1.southafrica.com:8080', 'https': 'https://proxy-za-1.southafrica.com:8080'},
                {'http': 'http://proxy-za-2.southafrica.com:8080', 'https': 'https://proxy-za-2.southafrica.com:8080'},
                
                # 西非地区代理
                {'http': 'http://proxy-ng-1.westafrica.com:8080', 'https': 'https://proxy-ng-1.westafrica.com:8080'},
                {'http': 'http://proxy-gh-1.westafrica.com:8080', 'https': 'https://proxy-gh-1.westafrica.com:8080'},
                
                # 欧洲代理作为备选
                {'http': 'http://proxy-uk-1.europe.com:8080', 'https': 'https://proxy-uk-1.europe.com:8080'},
                {'http': 'http://proxy-de-1.europe.com:8080', 'https': 'https://proxy-de-1.europe.com:8080'},
                
                # 北美代理作为最后备选
                {'http': 'http://proxy-us-1.northamerica.com:8080', 'https': 'https://proxy-us-1.northamerica.com:8080'},
                {'http': 'http://proxy-ca-1.northamerica.com:8080', 'https': 'https://proxy-ca-1.northamerica.com:8080'}
            ]
            
            # 智能代理选择策略：优先选择非洲地区代理，根据错误率动态调整
            if domain in self.website_status:
                status = self.website_status[domain]
                error_rate = status.get('error_rate', 0)
                
                if error_rate > 0.7:  # 错误率超过70%，切换到欧洲代理
                    proxy_pool = nation_ke_proxies[8:10]  # 欧洲代理
                    logger.info(f"nation.co.ke高错误率({error_rate:.2f})，切换到欧洲代理")
                elif error_rate > 0.4:  # 错误率40-70%，使用南非代理
                    proxy_pool = nation_ke_proxies[4:6]  # 南非代理
                    logger.info(f"nation.co.ke中等错误率({error_rate:.2f})，使用南非代理")
                else:  # 低错误率，使用肯尼亚本地代理
                    proxy_pool = nation_ke_proxies[0:3]  # 肯尼亚代理
                    logger.info(f"nation.co.ke低错误率({error_rate:.2f})，使用肯尼亚本地代理")
            else:
                # 首次访问，使用肯尼亚本地代理
                proxy_pool = nation_ke_proxies[0:3]
                logger.info("nation.co.ke首次访问，使用肯尼亚本地代理")
            
            # 随机选择代理
            proxy = random.choice(proxy_pool)
            logger.info(f"为nation.co.ke选择代理: {proxy}")
            return proxy
        
        # 对于其他网站，暂时返回None（不使用代理）
        return None
    
    def generate_browser_fingerprint_headers(self, url: str) -> Dict[str, str]:
        """生成浏览器指纹头 - 针对nation.co.ke网站优化"""
        domain = urlparse(url).netloc
        
        # 特殊处理nation.co.ke网站 - 更真实的浏览器指纹
        if 'nation.co.ke' in domain:
            logger.info("为nation.co.ke生成专用浏览器指纹")
            
            # 语言偏好 - 肯尼亚本地化，根据访问时间动态调整
            current_hour = datetime.now().hour
            if 6 <= current_hour < 12:  # 上午
                languages = ['en-KE', 'en-US', 'sw-KE']
            elif 12 <= current_hour < 18:  # 下午
                languages = ['en-KE', 'en-GB', 'sw-KE']
            else:  # 晚上
                languages = ['en-KE', 'en-US', 'en-GB']
            
            accept_language = random.choice(languages)
            
            # Accept头 - 更详细的媒体类型，模拟真实浏览器
            accept_headers = [
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            ]
            
            # Sec-Fetch系列头 - 更真实的组合
            sec_fetch_combinations = [
                {'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'Sec-Fetch-User': '?1'},
                {'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Sec-Fetch-User': '?1'},
                {'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-User': '?1'}
            ]
            
            # 浏览器特定头 - 模拟不同浏览器
            browser_specific_headers = [
                {  # Chrome
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"'
                },
                {  # Firefox
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                    'Sec-Ch-Ua': None,
                    'Sec-Ch-Ua-Mobile': None,
                    'Sec-Ch-Ua-Platform': None
                },
                {  # Edge
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
                    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"'
                }
            ]
            
            # 随机选择浏览器配置
            browser_config = random.choice(browser_specific_headers)
            sec_fetch_config = random.choice(sec_fetch_combinations)
            
            # 构建完整的指纹头
            fingerprint_headers = {
                'Accept': random.choice(accept_headers),
                'Accept-Language': accept_language,
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'DNT': random.choice(['1', '0']),  # 随机选择是否启用Do Not Track
                **browser_config,
                **sec_fetch_config
            }
            
            # 移除None值
            fingerprint_headers = {k: v for k, v in fingerprint_headers.items() if v is not None}
            
            return fingerprint_headers
        
        # 默认指纹策略
        return self._get_default_fingerprint()

    def simulate_human_behavior(self, url: str) -> Dict[str, Any]:
        """模拟人类行为"""
        profile = self.get_anti_crawler_profile(url)
        
        behavior_params = {}
        
        if self.behavior_patterns['mouse_movement']:
            # 模拟鼠标移动轨迹
            behavior_params['mouse_movements'] = self._generate_mouse_movements()
        
        if self.behavior_patterns['scroll_behavior']:
            # 模拟滚动行为
            behavior_params['scroll_pattern'] = self._generate_scroll_pattern()
        
        if self.behavior_patterns['click_patterns']:
            # 模拟点击模式
            behavior_params['click_locations'] = self._generate_click_locations()
        
        if self.behavior_patterns['time_spent']:
            # 模拟页面停留时间
            behavior_params['time_on_page'] = random.uniform(3.0, 15.0)
        
        # 根据网站特性调整行为强度
        if profile['behavior_simulation'] == 'high':
            behavior_params['intensity'] = 'high'
        elif profile['behavior_simulation'] == 'medium':
            behavior_params['intensity'] = 'medium'
        else:
            behavior_params['intensity'] = 'low'
        
        logger.debug(f"为 {url} 生成人类行为模拟参数")
        return behavior_params
    
    def _generate_mouse_movements(self) -> List[Dict[str, float]]:
        """生成鼠标移动轨迹"""
        movements = []
        num_points = random.randint(5, 15)
        
        for i in range(num_points):
            movements.append({
                'x': random.uniform(0, 100),
                'y': random.uniform(0, 100),
                'duration': random.uniform(0.1, 0.5)
            })
        
        return movements
    
    def _generate_scroll_pattern(self) -> Dict[str, Any]:
        """生成滚动模式"""
        return {
            'start_position': random.uniform(0, 30),
            'end_position': random.uniform(50, 100),
            'speed': random.uniform(0.5, 2.0),
            'pauses': random.randint(1, 3)
        }
    
    def _generate_click_locations(self) -> List[Dict[str, float]]:
        """生成点击位置"""
        clicks = []
        num_clicks = random.randint(1, 5)
        
        for i in range(num_clicks):
            clicks.append({
                'x': random.uniform(10, 90),
                'y': random.uniform(10, 90),
                'delay_before': random.uniform(0.5, 3.0),
                'delay_after': random.uniform(1.0, 5.0)
            })
        
        return clicks
    
    def detect_anti_crawler_measures(self, response) -> Dict[str, Any]:
        """检测反爬虫措施"""
        detection_results = {
            'blocked': False,
            'captcha_present': False,
            'rate_limited': False,
            'javascript_challenge': False
        }
        
        if response is None:
            detection_results['blocked'] = True
            return detection_results
        
        # 检查状态码
        if response.status_code in [403, 429, 503]:
            detection_results['blocked'] = True
            if response.status_code == 429:
                detection_results['rate_limited'] = True
        
        # 检查响应内容中的反爬虫标识
        if response.text:
            text_lower = response.text.lower()
            
            # 检测验证码
            captcha_indicators = ['captcha', 'recaptcha', 'hcaptcha', 'cloudflare']
            for indicator in captcha_indicators:
                if indicator in text_lower:
                    detection_results['captcha_present'] = True
                    break
            
            # 检测JavaScript挑战
            if 'javascript' in text_lower and ('challenge' in text_lower or 'redirect' in text_lower):
                detection_results['javascript_challenge'] = True
        
        # 更新统计
        self.detection_stats['total_requests'] += 1
        if detection_results['blocked']:
            self.detection_stats['blocked_requests'] += 1
        if detection_results['captcha_present']:
            self.detection_stats['captcha_encounters'] += 1
        if detection_results['rate_limited']:
            self.detection_stats['rate_limit_hits'] += 1
        
        return detection_results
    
    def get_evasion_strategy(self, detection_results: Dict[str, Any]) -> Dict[str, Any]:
        """根据检测结果制定规避策略"""
        strategy = {
            'change_user_agent': False,
            'increase_delay': False,
            'use_proxy': False,
            'wait_longer': False,
            'alternative_approach': False
        }
        
        if detection_results['blocked']:
            strategy['change_user_agent'] = True
            strategy['use_proxy'] = True
            strategy['increase_delay'] = True
        
        if detection_results['captcha_present']:
            strategy['wait_longer'] = True
            strategy['alternative_approach'] = True
        
        if detection_results['rate_limited']:
            strategy['increase_delay'] = True
            strategy['wait_longer'] = True
        
        if detection_results['javascript_challenge']:
            strategy['alternative_approach'] = True
        
        return strategy
    
    def get_detection_report(self) -> Dict[str, Any]:
        """获取检测报告"""
        total = self.detection_stats['total_requests']
        
        if total > 0:
            blocked_rate = self.detection_stats['blocked_requests'] / total
            captcha_rate = self.detection_stats['captcha_encounters'] / total
            rate_limit_rate = self.detection_stats['rate_limit_hits'] / total
        else:
            blocked_rate = captcha_rate = rate_limit_rate = 0
        
        return {
            'blocked_rate': round(blocked_rate * 100, 2),
            'captcha_encounter_rate': round(captcha_rate * 100, 2),
            'rate_limit_hit_rate': round(rate_limit_rate * 100, 2),
            'total_requests': total,
            'blocked_requests': self.detection_stats['blocked_requests'],
            'captcha_encounters': self.detection_stats['captcha_encounters'],
            'rate_limit_hits': self.detection_stats['rate_limit_hits'],
            'recommendations': self.generate_evasion_recommendations()
        }
    
    def generate_evasion_recommendations(self) -> List[str]:
        """生成规避建议"""
        recommendations = []
        
        if self.detection_stats['blocked_requests'] / self.detection_stats['total_requests'] > 0.2:
            recommendations.append("建议增加用户代理轮换频率和使用高质量代理")
        
        if self.detection_stats['captcha_encounters'] > 0:
            recommendations.append("检测到验证码，建议实现验证码识别或使用人工验证服务")
        
        if self.detection_stats['rate_limit_hits'] > 0:
            recommendations.append("检测到速率限制，建议进一步增加请求间隔时间")
        
        return recommendations

# 使用示例
def test_anti_anti_crawler():
    """测试反爬虫规避器"""
    aac = AntiAntiCrawler()
    
    # 测试不同非洲网站
    test_urls = [
        "https://www.news24.com",  # 南非
        "https://www.nation.co.ke",  # 肯尼亚
        "https://www.punchng.com",  # 尼日利亚
        "https://www.google.com"  # 非非洲网站
    ]
    
    for url in test_urls:
        print(f"\n测试URL: {url}")
        profile = aac.get_anti_crawler_profile(url)
        user_agent = aac.get_rotated_user_agent(url)
        delay = aac.calculate_smart_delay(url)
        behavior = aac.simulate_human_behavior(url)
        
        print(f"反爬虫配置: {profile}")
        print(f"用户代理: {user_agent[:60]}...")
        print(f"智能延迟: {delay:.2f}秒")
        print(f"行为模拟: {behavior}")

if __name__ == "__main__":
    test_anti_anti_crawler()