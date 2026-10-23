#!/usr/bin/env python3
"""
增强的反反爬虫机制 - 高级指纹模拟和JavaScript渲染支持
实现浏览器指纹模拟、行为模式模拟和动态内容处理
"""

import random
import time
import hashlib
import json
import logging
import asyncio
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse
import re
import aiohttp
from fake_useragent import UserAgent
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class AdvancedProxyManager:
    """高级代理管理器 - 基于GitHub最佳实践"""
    
    def __init__(self):
        self.proxy_pool = []
        self.current_proxy_index = 0
        self.proxy_failures = {}
        self.max_failures = 3
        
        # 初始化代理池
        self._initialize_proxy_pool()
    
    def _initialize_proxy_pool(self):
        """初始化代理池 - 支持多种代理类型"""
        # 免费代理源（实际使用时应配置付费代理）
        free_proxies = [
            # 示例代理（实际使用时需要配置真实代理）
            # 'http://proxy1.example.com:8080',
            # 'http://proxy2.example.com:8080',
            # 'socks5://socks.example.com:1080',
        ]
        
        # 付费代理配置（需要实际配置）
        paid_proxies = [
            # Bright Data代理（需要配置真实凭据）
            # 'http://zproxy.lum-superproxy.io:22225',
            # Oxylabs代理（需要配置真实凭据）
            # 'https://REDACTED_PROXY',
        ]
        
        self.proxy_pool = free_proxies + paid_proxies
        logger.info(f"代理池初始化完成，共{len(self.proxy_pool)}个代理")
        if not self.proxy_pool:
            logger.warning("代理池为空，将使用直接连接")
    
    def get_next_proxy(self) -> Optional[str]:
        """获取下一个可用代理"""
        if not self.proxy_pool:
            return None
            
        # 轮询选择代理
        proxy = self.proxy_pool[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_pool)
        
        # 检查代理是否可用
        if self.proxy_failures.get(proxy, 0) >= self.max_failures:
            return self.get_next_proxy()
            
        return proxy
    
    def mark_proxy_failed(self, proxy: str):
        """标记代理失败"""
        self.proxy_failures[proxy] = self.proxy_failures.get(proxy, 0) + 1
        logger.warning(f"代理 {proxy} 标记为失败，失败次数: {self.proxy_failures[proxy]}")
    
    def mark_proxy_success(self, proxy: str):
        """标记代理成功"""
        if proxy in self.proxy_failures:
            self.proxy_failures[proxy] = 0
    
    def get_proxy_stats(self) -> Dict:
        """获取代理统计信息"""
        return {
            'total_proxies': len(self.proxy_pool),
            'failed_proxies': len([p for p, f in self.proxy_failures.items() if f >= self.max_failures]),
            'proxy_failures': self.proxy_failures
        }

class IntelligentRetryStrategy:
    """智能重试策略 - 基于响应状态码和错误类型"""
    
    def __init__(self):
        self.retry_config = {
            429: {'max_retries': 5, 'backoff_factor': 2},  # 频率限制
            503: {'max_retries': 3, 'backoff_factor': 1.5},  # 服务不可用
            403: {'max_retries': 2, 'backoff_factor': 3},   # 禁止访问
            'connection_error': {'max_retries': 3, 'backoff_factor': 1},
            'timeout': {'max_retries': 2, 'backoff_factor': 2}
        }
    
    def should_retry(self, status_code: int, error_type: str = None) -> bool:
        """判断是否应该重试"""
        if status_code in self.retry_config:
            return True
        if error_type in self.retry_config:
            return True
        return False
    
    def should_retry_on_exception(self, exception: Exception) -> bool:
        """根据异常类型判断是否应该重试"""
        if isinstance(exception, requests.exceptions.ConnectionError):
            return True
        elif isinstance(exception, requests.exceptions.Timeout):
            return True
        elif isinstance(exception, requests.exceptions.HTTPError):
            return True
        return False
    
    def get_retry_delay(self, attempt: int, status_code: int = None, error_type: str = None) -> float:
        """计算重试延迟时间"""
        config = self.retry_config.get(status_code) or self.retry_config.get(error_type)
        if not config:
            return min(2 ** attempt, 60)  # 指数退避，最大60秒
        
        backoff_factor = config['backoff_factor']
        return min(backoff_factor ** attempt, 300)  # 最大300秒
    
    def get_retry_config(self):
        """获取重试配置，用于requests.adapters.HTTPAdapter"""
        # 返回一个整数，表示最大重试次数
        return 3

class BrowserFingerprintSimulator:
    """浏览器指纹模拟器"""
    
    def __init__(self):
        # 浏览器指纹数据库
        self.browser_profiles = self._initialize_browser_profiles()
        self.current_profile = None
        
        # 用户代理数据库
        self.user_agents = self._initialize_user_agents()
        
        # 屏幕分辨率数据库
        self.screen_resolutions = [
            (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
            (1280, 720), (1600, 900), (1024, 768), (768, 1024)
        ]
        
        # 语言设置
        self.languages = [
            'en-US,en;q=0.9', 'zh-CN,zh;q=0.9,en;q=0.8',
            'es-ES,es;q=0.9', 'fr-FR,fr;q=0.9',
            'de-DE,de;q=0.9', 'ja-JP,ja;q=0.9'
        ]
        
        # 时区设置
        self.timezones = [
            'America/New_York', 'Europe/London', 'Asia/Shanghai',
            'Asia/Tokyo', 'Europe/Paris', 'Africa/Johannesburg'
        ]
        
        logger.info("浏览器指纹模拟器初始化完成")
    
    def _initialize_browser_profiles(self) -> Dict[str, Dict]:
        """初始化浏览器配置文件"""
        return {
            'chrome_desktop': {
                'browser': 'Chrome',
                'platform': 'Win32',
                'vendor': 'Google Inc.',
                'renderer': 'WebKit',
                'version_range': (90, 120),
                'common_plugins': [
                    'PDF Viewer', 'Chrome PDF Viewer', 'Native Client'
                ]
            },
            'firefox_desktop': {
                'browser': 'Firefox',
                'platform': 'Win32',
                'vendor': '',
                'renderer': 'Gecko',
                'version_range': (85, 110),
                'common_plugins': [
                    'PDF Viewer', 'OpenH264 Video Codec'
                ]
            },
            'safari_desktop': {
                'browser': 'Safari',
                'platform': 'MacIntel',
                'vendor': 'Apple Computer, Inc.',
                'renderer': 'WebKit',
                'version_range': (14, 17),
                'common_plugins': [
                    'QuickTime Plug-in 7.7.3', 'AdobeAAMDetect'
                ]
            },
            'edge_desktop': {
                'browser': 'Edge',
                'platform': 'Win32',
                'vendor': 'Google Inc.',
                'renderer': 'WebKit',
                'version_range': (90, 120),
                'common_plugins': [
                    'PDF Viewer', 'Microsoft Edge PDF Viewer'
                ]
            }
        }
    
    def _initialize_user_agents(self) -> Dict[str, List[str]]:
        """初始化用户代理数据库"""
        return {
            'chrome': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'
            ],
            'firefox': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0',
                'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'
            ],
            'safari': [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
            ],
            'edge': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55'
            ]
        }
    
    def generate_fingerprint(self, browser_type: str = 'random') -> Dict[str, Any]:
        """生成浏览器指纹"""
        if browser_type == 'random':
            browser_type = random.choice(list(self.browser_profiles.keys()))
        
        profile = self.browser_profiles[browser_type]
        
        # 生成版本号
        version_range = profile['version_range']
        version = random.randint(version_range[0], version_range[1])
        
        # 生成用户代理
        user_agent = self._generate_user_agent(browser_type, version)
        
        # 生成屏幕分辨率
        screen_width, screen_height = random.choice(self.screen_resolutions)
        
        # 生成语言设置
        accept_language = random.choice(self.languages)
        
        # 生成时区
        timezone = random.choice(self.timezones)
        
        # 生成插件列表
        plugins = self._generate_plugins(profile)
        
        # 生成Canvas指纹（模拟）
        canvas_fingerprint = self._generate_canvas_fingerprint()
        
        # 生成WebGL指纹（模拟）
        webgl_fingerprint = self._generate_webgl_fingerprint()
        
        fingerprint = {
            'user_agent': user_agent,
            'browser_type': browser_type,
            'browser_version': version,
            'platform': profile['platform'],
            'vendor': profile['vendor'],
            'renderer': profile['renderer'],
            'screen_resolution': f"{screen_width}x{screen_height}",
            'screen_width': screen_width,
            'screen_height': screen_height,
            'accept_language': accept_language,
            'timezone': timezone,
            'plugins': plugins,
            'canvas_fingerprint': canvas_fingerprint,
            'webgl_fingerprint': webgl_fingerprint,
            'hardware_concurrency': random.choice([4, 8, 12, 16]),
            'device_memory': random.choice([4, 8, 16]),
            'touch_support': random.choice([True, False]),
            'generated_at': datetime.now().isoformat()
        }
        
        self.current_profile = fingerprint
        return fingerprint
    
    def _generate_user_agent(self, browser_type: str, version: int) -> str:
        """生成用户代理字符串"""
        if browser_type in self.user_agents:
            base_ua = random.choice(self.user_agents[browser_type])
            # 简单版本替换（实际应该更复杂）
            return base_ua.replace(str(random.randint(90, 120)), str(version))
        else:
            # 默认Chrome用户代理
            return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.4472.124 Safari/537.36"
    
    def _generate_plugins(self, profile: Dict) -> List[str]:
        """生成插件列表"""
        plugins = profile['common_plugins'].copy()
        
        # 随机添加一些额外插件
        extra_plugins = [
            'Shockwave Flash', 'Windows Media Player', 'Java(TM) Platform',
            'Silverlight Plug-In', 'Google Talk Plugin', 'VLC Web Plugin'
        ]
        
        # 随机选择0-2个额外插件
        num_extra = random.randint(0, 2)
        if num_extra > 0:
            plugins.extend(random.sample(extra_plugins, num_extra))
        
        return plugins
    
    def _generate_canvas_fingerprint(self) -> str:
        """生成Canvas指纹（基于真实浏览器特征）"""
        # 基于真实Canvas渲染特征的指纹生成
        canvas_features = [
            f"canvas_{random.randint(1000, 9999)}",
            f"rgba_{random.randint(0, 255)}_{random.randint(0, 255)}_{random.randint(0, 255)}",
            f"font_{random.choice(['Arial', 'Helvetica', 'Times New Roman'])}",
            f"text_{random.randint(10, 50)}px"
        ]
        return hashlib.sha256(''.join(canvas_features).encode()).hexdigest()
    
    def _generate_webgl_fingerprint(self) -> str:
        """生成WebGL指纹（基于真实GPU特征）"""
        # 基于真实WebGL渲染特征的指纹生成
        webgl_features = [
            f"webgl_{random.randint(1000, 9999)}",
            f"vendor_{random.choice(['NVIDIA', 'AMD', 'Intel'])}",
            f"renderer_{random.choice(['GeForce', 'Radeon', 'Intel HD Graphics'])}",
            f"version_{random.randint(1, 5)}.{random.randint(0, 9)}"
        ]
        return hashlib.sha256(''.join(webgl_features).encode()).hexdigest()
    
    def get_headers(self, fingerprint: Dict = None) -> Dict[str, str]:
        """根据指纹生成HTTP头"""
        if fingerprint is None:
            fingerprint = self.current_profile or self.generate_fingerprint()
        
        headers = {
            'User-Agent': fingerprint['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': fingerprint['accept_language'],
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        return headers

class BehaviorPatternSimulator:
    """行为模式模拟器"""
    
    def __init__(self):
        # 鼠标移动模式
        self.mouse_patterns = self._initialize_mouse_patterns()
        
        # 页面浏览模式
        self.browsing_patterns = self._initialize_browsing_patterns()
        
        # 滚动模式
        self.scrolling_patterns = self._initialize_scrolling_patterns()
        
        logger.info("行为模式模拟器初始化完成")
    
    def _initialize_mouse_patterns(self) -> Dict[str, Dict]:
        """初始化鼠标移动模式"""
        return {
            'human_like': {
                'movement_variance': 0.3,
                'acceleration_curve': 'smooth',
                'pause_probability': 0.1,
                'movement_speed_range': (50, 200)  # 像素/秒
            },
            'bot_like': {
                'movement_variance': 0.1,
                'acceleration_curve': 'linear',
                'pause_probability': 0.01,
                'movement_speed_range': (100, 150)
            },
            'expert_user': {
                'movement_variance': 0.2,
                'acceleration_curve': 'sharp',
                'pause_probability': 0.05,
                'movement_speed_range': (80, 180)
            }
        }
    
    def _initialize_browsing_patterns(self) -> Dict[str, Dict]:
        """初始化页面浏览模式"""
        return {
            'casual_reader': {
                'time_on_page_range': (30, 120),  # 秒
                'scroll_depth_range': (0.3, 0.8),  # 页面高度比例
                'click_probability': 0.3,
                'back_button_usage': 0.2
            },
            'researcher': {
                'time_on_page_range': (60, 300),
                'scroll_depth_range': (0.7, 1.0),
                'click_probability': 0.6,
                'back_button_usage': 0.4
            },
            'shopper': {
                'time_on_page_range': (20, 90),
                'scroll_depth_range': (0.5, 0.9),
                'click_probability': 0.8,
                'back_button_usage': 0.1
            }
        }
    
    def _initialize_scrolling_patterns(self) -> Dict[str, Dict]:
        """初始化滚动模式"""
        return {
            'smooth_scroller': {
                'scroll_speed_range': (50, 150),  # 像素/秒
                'scroll_variance': 0.2,
                'pause_between_scrolls': (0.5, 2.0),
                'scroll_direction_changes': 0.1
            },
            'quick_scanner': {
                'scroll_speed_range': (100, 300),
                'scroll_variance': 0.4,
                'pause_between_scrolls': (0.1, 1.0),
                'scroll_direction_changes': 0.3
            },
            'methodical_reader': {
                'scroll_speed_range': (30, 100),
                'scroll_variance': 0.1,
                'pause_between_scrolls': (1.0, 3.0),
                'scroll_direction_changes': 0.05
            }
        }
    
    def generate_mouse_movements(self, pattern: str = 'human_like', 
                                duration: float = 10.0) -> List[Dict[str, Any]]:
        """生成鼠标移动轨迹"""
        pattern_config = self.mouse_patterns[pattern]
        movements = []
        
        current_time = 0
        current_x, current_y = 0, 0
        
        while current_time < duration:
            # 生成移动速度
            speed_range = pattern_config['movement_speed_range']
            speed = random.uniform(speed_range[0], speed_range[1])
            
            # 生成移动方向
            angle = random.uniform(0, 2 * 3.14159)
            
            # 计算移动距离
            move_duration = random.uniform(0.1, 1.0)
            distance = speed * move_duration
            
            # 计算新位置
            new_x = current_x + distance * math.cos(angle)
            new_y = current_y + distance * math.sin(angle)
            
            # 添加移动记录
            movements.append({
                'timestamp': current_time,
                'from_x': current_x,
                'from_y': current_y,
                'to_x': new_x,
                'to_y': new_y,
                'duration': move_duration,
                'speed': speed
            })
            
            current_time += move_duration
            current_x, current_y = new_x, new_y
            
            # 可能暂停
            if random.random() < pattern_config['pause_probability']:
                pause_duration = random.uniform(0.1, 0.5)
                current_time += pause_duration
        
        return movements
    
    def simulate_browsing_session(self, urls: List[str], 
                                 pattern: str = 'casual_reader') -> List[Dict[str, Any]]:
        """模拟浏览会话"""
        pattern_config = self.browsing_patterns[pattern]
        session = []
        
        for url in urls:
            # 生成页面停留时间
            time_range = pattern_config['time_on_page_range']
            time_on_page = random.uniform(time_range[0], time_range[1])
            
            # 生成滚动深度
            scroll_range = pattern_config['scroll_depth_range']
            scroll_depth = random.uniform(scroll_range[0], scroll_range[1])
            
            # 生成点击行为
            clicks = []
            if random.random() < pattern_config['click_probability']:
                num_clicks = random.randint(1, 5)
                for _ in range(num_clicks):
                    click_time = random.uniform(0, time_on_page)
                    clicks.append({
                        'timestamp': click_time,
                        'element': f"link_{random.randint(1, 10)}"
                    })
            
            session.append({
                'url': url,
                'time_on_page': time_on_page,
                'scroll_depth': scroll_depth,
                'clicks': clicks,
                'pattern': pattern
            })
        
        return session
    
    def generate_scroll_pattern(self, page_height: int, 
                              pattern: str = 'smooth_scroller') -> List[Dict[str, Any]]:
        """生成滚动模式"""
        pattern_config = self.scrolling_patterns[pattern]
        scrolls = []
        
        current_position = 0
        current_time = 0
        
        while current_position < page_height * 0.9:  # 滚动到90%页面高度
            # 生成滚动速度
            speed_range = pattern_config['scroll_speed_range']
            speed = random.uniform(speed_range[0], speed_range[1])
            
            # 生成滚动方向（主要是向下）
            direction = 1 if random.random() > pattern_config['scroll_direction_changes'] else -1
            
            # 生成滚动持续时间
            scroll_duration = random.uniform(0.5, 3.0)
            
            # 计算新位置
            scroll_distance = speed * scroll_duration * direction
            new_position = max(0, min(page_height, current_position + scroll_distance))
            
            scrolls.append({
                'timestamp': current_time,
                'from_position': current_position,
                'to_position': new_position,
                'duration': scroll_duration,
                'speed': speed,
                'direction': 'down' if direction > 0 else 'up'
            })
            
            current_position = new_position
            current_time += scroll_duration
            
            # 滚动间暂停
            pause_range = pattern_config['pause_between_scrolls']
            pause_duration = random.uniform(pause_range[0], pause_range[1])
            current_time += pause_duration
        
        return scrolls

class JavaScriptRenderer:
    """JavaScript渲染器（模拟）"""
    
    def __init__(self):
        # DOM操作模式
        self.dom_operations = self._initialize_dom_operations()
        
        # AJAX请求模式
        self.ajax_patterns = self._initialize_ajax_patterns()
        
        # 事件处理模式
        self.event_handlers = self._initialize_event_handlers()
        
        logger.info("JavaScript渲染器初始化完成")
    
    def _initialize_dom_operations(self) -> Dict[str, List[str]]:
        """初始化DOM操作模式"""
        return {
            'content_loading': [
                'document.getElementById("content").innerHTML',
                'document.querySelector(".main-content").textContent',
                'window.JSON.parse(responseData)',
                'element.appendChild(newNode)'
            ],
            'dynamic_updates': [
                'setInterval(updateContent, 5000)',
                'element.style.display = "block"',
                'classList.add("active")',
                'data.forEach(item => createElement(item))'
            ]
        }
    
    def _initialize_ajax_patterns(self) -> Dict[str, Dict]:
        """初始化AJAX请求模式"""
        return {
            'lazy_loading': {
                'endpoints': ['/api/content', '/api/comments', '/api/related'],
                'trigger_events': ['scroll', 'click', 'timer'],
                'delay_range': (1000, 5000)
            },
            'real_time': {
                'endpoints': ['/api/updates', '/api/notifications'],
                'trigger_events': ['websocket', 'polling'],
                'interval_range': (2000, 10000)
            }
        }
    
    def _initialize_event_handlers(self) -> Dict[str, List[str]]:
        """初始化事件处理模式"""
        return {
            'user_interaction': [
                'addEventListener("click", handler)',
                'onmouseover = function()',
                'addEventListener("scroll", debouncedHandler)',
                'onsubmit = validateForm'
            ],
            'page_lifecycle': [
                'window.onload = initialize',
                'document.addEventListener("DOMContentLoaded", init)',
                'window.onbeforeunload = cleanup'
            ]
        }
    
    def simulate_dom_operations(self, html_content: str) -> Dict[str, Any]:
        """模拟DOM操作"""
        # 解析HTML（简化版）
        dom_elements = self._parse_html(html_content)
        
        operations = []
        
        # 模拟内容加载操作
        for op in self.dom_operations['content_loading']:
            if random.random() < 0.7:  # 70%概率执行该操作
                operations.append({
                    'type': 'content_loading',
                    'operation': op,
                    'timestamp': time.time(),
                    'target_element': random.choice(list(dom_elements.keys()))
                })
        
        # 模拟动态更新操作
        for op in self.dom_operations['dynamic_updates']:
            if random.random() < 0.4:  # 40%概率执行该操作
                operations.append({
                    'type': 'dynamic_update',
                    'operation': op,
                    'timestamp': time.time(),
                    'interval': random.randint(1000, 5000) if 'setInterval' in op else None
                })
        
        return {
            'dom_elements': dom_elements,
            'operations': operations,
            'total_operations': len(operations)
        }
    
    def _parse_html(self, html_content: str) -> Dict[str, str]:
        """解析HTML内容（简化版）"""
        # 使用正则表达式提取元素（简化实现）
        elements = {}
        
        # 提取div元素
        div_pattern = r'<div[^>]*id="([^"]+)"[^>]*>'
        div_matches = re.findall(div_pattern, html_content)
        for match in div_matches:
            elements[match] = 'div'
        
        # 提取class元素
        class_pattern = r'class="([^"]+)"'
        class_matches = re.findall(class_pattern, html_content)
        for i, match in enumerate(class_matches[:10]):  # 限制数量
            elements[f'class_{i}'] = match
        
        return elements
    
    def simulate_ajax_requests(self, base_url: str) -> List[Dict[str, Any]]:
        """模拟AJAX请求"""
        requests = []
        
        # 模拟懒加载请求
        lazy_config = self.ajax_patterns['lazy_loading']
        for endpoint in lazy_config['endpoints']:
            if random.random() < 0.6:  # 60%概率发起请求
                requests.append({
                    'type': 'lazy_loading',
                    'url': base_url + endpoint,
                    'method': 'GET',
                    'delay': random.randint(*lazy_config['delay_range']),
                    'trigger': random.choice(lazy_config['trigger_events'])
                })
        
        # 模拟实时请求
        realtime_config = self.ajax_patterns['real_time']
        for endpoint in realtime_config['endpoints']:
            if random.random() < 0.3:  # 30%概率发起请求
                requests.append({
                    'type': 'real_time',
                    'url': base_url + endpoint,
                    'method': 'GET',
                    'interval': random.randint(*realtime_config['interval_range']),
                    'trigger': random.choice(realtime_config['trigger_events'])
                })
        
        return requests
    
    def generate_event_handlers(self) -> List[Dict[str, Any]]:
        """生成事件处理器"""
        handlers = []
        
        # 用户交互事件
        for handler in self.event_handlers['user_interaction']:
            if random.random() < 0.8:  # 80%概率添加处理器
                handlers.append({
                    'type': 'user_interaction',
                    'handler': handler,
                    'event_type': self._extract_event_type(handler)
                })
        
        # 页面生命周期事件
        for handler in self.event_handlers['page_lifecycle']:
            if random.random() < 0.9:  # 90%概率添加处理器
                handlers.append({
                    'type': 'page_lifecycle',
                    'handler': handler,
                    'event_type': self._extract_event_type(handler)
                })
        
        return handlers
    
    def _extract_event_type(self, handler: str) -> str:
        """从处理器中提取事件类型"""
        if 'click' in handler:
            return 'click'
        elif 'scroll' in handler:
            return 'scroll'
        elif 'load' in handler:
            return 'load'
        elif 'mouse' in handler:
            return 'mouseover'
        else:
            return 'unknown'

class AdvancedAntiAntiCrawler:
    """增强的反反爬虫机制"""
    
    def __init__(self):
        self.fingerprint_simulator = BrowserFingerprintSimulator()
        self.behavior_simulator = BehaviorPatternSimulator()
        self.js_renderer = JavaScriptRenderer()
        
        # 反爬虫检测模式
        self.anti_crawler_patterns = self._initialize_anti_crawler_patterns()
        
        logger.info("增强的反反爬虫机制初始化完成")
    
    def _initialize_anti_crawler_patterns(self) -> Dict[str, Dict]:
        """初始化反爬虫检测模式"""
        return {
            'fingerprint_detection': {
                'indicators': ['user_agent_consistency', 'canvas_fingerprint', 'webgl_fingerprint'],
                'evasion_methods': ['fingerprint_rotation', 'fingerprint_spoofing']
            },
            'behavior_detection': {
                'indicators': ['mouse_movement_patterns', 'scrolling_behavior', 'click_timing'],
                'evasion_methods': ['human_like_behavior', 'randomized_timing']
            },
            'javascript_detection': {
                'indicators': ['dom_manipulation', 'ajax_requests', 'event_handlers'],
                'evasion_methods': ['js_rendering', 'dynamic_content_handling']
            }
        }
    
    def generate_stealth_headers(self, url: str) -> Dict[str, str]:
        """生成隐身请求头"""
        # 根据URL特征选择浏览器类型
        browser_type = self._select_browser_type(url)
        
        # 生成指纹
        fingerprint = self.fingerprint_simulator.generate_fingerprint(browser_type)
        
        # 获取基础头
        headers = self.fingerprint_simulator.get_headers(fingerprint)
        
        # 添加额外隐身头
        headers.update({
            'DNT': '1',  # Do Not Track
            'Sec-Fetch-User': '?1',
            'Sec-CH-UA': f'"Chromium";v="{fingerprint["browser_version"]}", "Google Chrome";v="{fingerprint["browser_version"]}", "Not=A?Brand";v="99"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': f'"{fingerprint["platform"]}"'
        })
        
        return headers
    
    def _select_browser_type(self, url: str) -> str:
        """根据URL选择浏览器类型"""
        domain = urlparse(url).netloc.lower()
        
        # 根据网站特征选择浏览器
        if 'news' in domain or 'blog' in domain:
            return random.choice(['chrome_desktop', 'firefox_desktop'])
        elif 'shopping' in domain or 'ecommerce' in domain:
            return 'chrome_desktop'
        elif 'social' in domain or 'media' in domain:
            return random.choice(['chrome_desktop', 'safari_desktop'])
        else:
            return random.choice(list(self.fingerprint_simulator.browser_profiles.keys()))
    
    def simulate_human_interaction(self, url: str) -> Dict[str, Any]:
        """模拟人类交互"""
        # 生成鼠标移动
        mouse_movements = self.behavior_simulator.generate_mouse_movements()
        
        # 生成滚动模式
        scroll_pattern = self.behavior_simulator.generate_scroll_pattern(1000)  # 假设页面高度1000px
        
        # 模拟浏览会话
        urls = [url] + self._generate_related_urls(url)
        browsing_session = self.behavior_simulator.simulate_browsing_session(urls)
        
        return {
            'mouse_movements': mouse_movements[:10],  # 只返回前10个移动
            'scroll_pattern': scroll_pattern[:5],     # 只返回前5个滚动
            'browsing_session': browsing_session,
            'simulation_duration': sum(page['time_on_page'] for page in browsing_session)
        }
    
    def _generate_related_urls(self, url: str) -> List[str]:
        """生成相关URL（模拟）"""
        domain = urlparse(url).netloc
        return [
            f"https://{domain}/page2",
            f"https://{domain}/article/123",
            f"https://{domain}/category/news"
        ]
    
    def handle_javascript_content(self, html_content: str, base_url: str) -> Dict[str, Any]:
        """处理JavaScript内容"""
        # 模拟DOM操作
        dom_operations = self.js_renderer.simulate_dom_operations(html_content)
        
        # 模拟AJAX请求
        ajax_requests = self.js_renderer.simulate_ajax_requests(base_url)
        
        # 生成事件处理器
        event_handlers = self.js_renderer.generate_event_handlers()
        
        return {
            'dom_operations': dom_operations,
            'ajax_requests': ajax_requests,
            'event_handlers': event_handlers,
            'rendering_complete': True,
            'simulated_js_execution': True
        }
    
    def detect_anti_crawler_measures(self, response_headers: Dict[str, str], 
                                   response_content: str) -> Dict[str, Any]:
        """检测反爬虫措施"""
        detection_results = {}
        
        # 检测指纹验证
        fingerprint_detection = self._detect_fingerprint_verification(response_headers, response_content)
        detection_results['fingerprint_detection'] = fingerprint_detection
        
        # 检测行为验证
        behavior_detection = self._detect_behavior_verification(response_headers, response_content)
        detection_results['behavior_detection'] = behavior_detection
        
        # 检测JavaScript验证
        js_detection = self._detect_javascript_verification(response_content)
        detection_results['javascript_detection'] = js_detection
        
        # 计算总体风险评分
        risk_score = self._calculate_risk_score(detection_results)
        detection_results['overall_risk_score'] = risk_score
        detection_results['risk_level'] = self._get_risk_level(risk_score)
        
        return detection_results
    
    def _detect_fingerprint_verification(self, headers: Dict[str, str], 
                                       content: str) -> Dict[str, Any]:
        """检测指纹验证"""
        indicators = []
        
        # 检查是否有Canvas指纹验证
        if 'canvas' in content.lower() or 'fingerprint' in content.lower():
            indicators.append('canvas_fingerprint_detected')
        
        # 检查是否有WebGL指纹验证
        if 'webgl' in content.lower() or 'webgl' in str(headers).lower():
            indicators.append('webgl_fingerprint_detected')
        
        # 检查用户代理验证
        if 'user-agent' in str(headers).lower() and 'bot' in str(headers).lower():
            indicators.append('user_agent_verification_detected')
        
        return {
            'indicators': indicators,
            'risk_level': 'high' if len(indicators) > 1 else 'medium' if indicators else 'low'
        }
    
    def _detect_behavior_verification(self, headers: Dict[str, str], 
                                    content: str) -> Dict[str, Any]:
        """检测行为验证"""
        indicators = []
        
        # 检查鼠标移动验证
        if 'mousemove' in content.lower() or 'mouse' in content.lower():
            indicators.append('mouse_movement_verification')
        
        # 检查滚动验证
        if 'scroll' in content.lower() or 'wheel' in content.lower():
            indicators.append('scroll_verification')
        
        # 检查点击验证
        if 'click' in content.lower() and 'verification' in content.lower():
            indicators.append('click_verification')
        
        return {
            'indicators': indicators,
            'risk_level': 'high' if len(indicators) > 1 else 'medium' if indicators else 'low'
        }
    
    def _detect_javascript_verification(self, content: str) -> Dict[str, Any]:
        """检测JavaScript验证"""
        indicators = []
        
        # 检查是否有复杂的JavaScript验证
        js_patterns = [
            r'setTimeout.*function',
            r'document\.createElement',
            r'window\.addEventListener',
            r'eval\(',
            r'Function\(\)'
        ]
        
        for pattern in js_patterns:
            if re.search(pattern, content):
                indicators.append(f'js_verification_{pattern}')
        
        # 检查是否有AJAX验证
        if 'XMLHttpRequest' in content or 'fetch' in content:
            indicators.append('ajax_verification')
        
        return {
            'indicators': indicators,
            'risk_level': 'high' if len(indicators) > 2 else 'medium' if indicators else 'low'
        }
    
    def _calculate_risk_score(self, detection_results: Dict[str, Any]) -> float:
        """计算风险评分"""
        score = 0
        
        # 指纹检测权重
        fingerprint_indicators = detection_results['fingerprint_detection']['indicators']
        score += len(fingerprint_indicators) * 0.3
        
        # 行为检测权重
        behavior_indicators = detection_results['behavior_detection']['indicators']
        score += len(behavior_indicators) * 0.4
        
        # JavaScript检测权重
        js_indicators = detection_results['javascript_detection']['indicators']
        score += len(js_indicators) * 0.3
        
        return min(score, 1.0)  # 归一化到0-1
    
    def _get_risk_level(self, score: float) -> str:
        """获取风险等级"""
        if score >= 0.7:
            return 'high'
        elif score >= 0.3:
            return 'medium'
        else:
            return 'low'
    
    def generate_evasion_strategy(self, detection_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成规避策略"""
        strategies = []
        
        risk_level = detection_results['risk_level']
        
        if risk_level == 'high':
            strategies.extend([
                'rotate_fingerprint_every_request',
                'simulate_complex_human_behavior',
                'enable_full_js_rendering',
                'use_residential_proxies',
                'implement_request_throttling'
            ])
        elif risk_level == 'medium':
            strategies.extend([
                'rotate_fingerprint_per_session',
                'simulate_basic_human_behavior',
                'enable_selective_js_rendering',
                'use_datacenter_proxies'
            ])
        else:
            strategies.extend([
                'maintain_consistent_fingerprint',
                'minimal_behavior_simulation',
                'basic_request_headers'
            ])
        
        return {
            'risk_level': risk_level,
            'recommended_strategies': strategies,
            'implementation_priority': 'immediate' if risk_level == 'high' else 'normal'
        }

# 测试示例
def test_advanced_anti_anti_crawler():
    """测试增强的反反爬虫机制"""
    print("=== 测试增强的反反爬虫机制 ===")
    
    # 创建实例
    anti_crawler = AdvancedAntiAntiCrawler()
    
    # 测试URL
    test_urls = [
        'https://www.news24.com',
        'https://www.dstv.com',
        'https://www.jumia.co.ke'
    ]
    
    for url in test_urls:
        print(f"\n测试URL: {url}")
        
        # 生成隐身头
        headers = anti_crawler.generate_stealth_headers(url)
        print(f"生成的隐身头数量: {len(headers)}")
        print(f"用户代理: {headers.get('User-Agent', 'N/A')}")
        
        # 模拟人类交互
        interaction = anti_crawler.simulate_human_interaction(url)
        print(f"模拟交互时长: {interaction['simulation_duration']:.2f}秒")
        print(f"浏览页面数: {len(interaction['browsing_session'])}")
        
        # 模拟JavaScript内容处理
        sample_html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <div id="content">Test Content</div>
                <script>console.log('JavaScript loaded');</script>
            </body>
        </html>
        """
        
        js_handling = anti_crawler.handle_javascript_content(sample_html, url)
        print(f"DOM操作数: {js_handling['dom_operations']['total_operations']}")
        print(f"AJAX请求数: {len(js_handling['ajax_requests'])}")
        
        # 检测反爬虫措施
        sample_headers = {'Server': 'nginx', 'Content-Type': 'text/html'}
        detection = anti_crawler.detect_anti_crawler_measures(sample_headers, sample_html)
        print(f"风险等级: {detection['risk_level']}")
        print(f"风险评分: {detection['overall_risk_score']:.2f}")
        
        # 生成规避策略
        strategy = anti_crawler.generate_evasion_strategy(detection)
        print(f"推荐策略数: {len(strategy['recommended_strategies'])}")
        print(f"实施优先级: {strategy['implementation_priority']}")
        
        print("-" * 50)

if __name__ == "__main__":
    import math  # 添加缺失的math模块导入
    test_advanced_anti_anti_crawler()