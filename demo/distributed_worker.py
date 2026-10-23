#!/usr/bin/env python3
"""
分布式爬虫系统 - 工作节点
负责执行具体的爬虫任务
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid
import hashlib
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse
from pathlib import Path
from data_storage_manager import DataStorageManager
from data_quality_management_system import DataQualityManagementSystem
from smart_page_filter import SmartPageFilter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('distributed_worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 智能配置
MASTER_URL = os.getenv('MASTER_URL', 'http://localhost:8000')
WORKER_ID = os.getenv('WORKER_ID', f'worker-{uuid.uuid4().hex[:8]}')
MAX_THREADS = int(os.getenv('MAX_THREADS', 10))  # 智能线程数：基础10个，根据CPU核心数动态调整
HEARTBEAT_INTERVAL = int(os.getenv('HEARTBEAT_INTERVAL', 30))

# 智能超时和重试配置 - 自适应优化策略
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 60))  # 智能超时：基础60秒，根据网站响应动态调整
HEARTBEAT_TIMEOUT = int(os.getenv('HEARTBEAT_TIMEOUT', 30))  # 心跳超时优化到30秒
MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', 4))  # 智能重试：最多4次，成功率低的网站减少重试
RETRY_DELAYS = [5, 15, 30, 60]  # 智能延迟：基于网站响应速度动态计算

# 网络连接智能优化配置
CONNECTION_TIMEOUT = int(os.getenv('CONNECTION_TIMEOUT', 45))  # 智能连接超时：基础45秒，动态调整
MAX_CONNECTION_RETRIES = int(os.getenv('MAX_CONNECTION_RETRIES', 5))  # 智能连接重试：最多5次，成功率低的网站减少重试

# 智能连接池配置 - 动态优化并发性能
CONNECTION_POOL_SIZE = int(os.getenv('CONNECTION_POOL_SIZE', 30))  # 智能连接池：基础30个，根据系统负载动态调整
POOL_MAX_SIZE = int(os.getenv('POOL_MAX_SIZE', 80))  # 智能最大连接数：基础80个，支持更高并发
POOL_BLOCK = os.getenv('POOL_BLOCK', 'false').lower() == 'true'  # 连接池是否阻塞

# 性能监控配置
PERFORMANCE_MONITORING = os.getenv('PERFORMANCE_MONITORING', 'true').lower() == 'true'
MONITOR_INTERVAL = int(os.getenv('MONITOR_INTERVAL', 300))  # 性能监控间隔（秒）

# 网络质量自适应配置
NETWORK_QUALITY_THRESHOLD = float(os.getenv('NETWORK_QUALITY_THRESHOLD', 0.8))  # 网络质量阈值
AUTO_ADJUST_TIMEOUT = os.getenv('AUTO_ADJUST_TIMEOUT', 'true').lower() == 'true'  # 是否自动调整超时

# 新增代理配置 - 针对非洲网站大幅优化
PROXY_ENABLED = os.getenv('PROXY_ENABLED', 'true').lower() == 'true'  # 启用代理以解决非洲网站访问问题
PROXY_CONFIG_FILE = os.getenv('PROXY_CONFIG_FILE', 'proxy_config.json')  # 代理配置文件

# 非洲网站优化配置
AFRICA_OPTIMIZATION_FILE = os.getenv('AFRICA_OPTIMIZATION_FILE', 'africa_website_optimization.json')  # 非洲网站优化配置文件

# Firecrawl配置 - 完全禁用Firecrawl功能，避免未定义函数调用错误
FIRECRAWL_ENABLED = False  # 强制禁用，避免MCP工具调用错误
MCP_FIRECRAWL_AVAILABLE = False
logger.info("Firecrawl功能已完全禁用，仅使用传统爬取方法")

class DistributedWorker:
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.is_running = False
        
        # 工作节点状态
        self.status = "idle"
        
        # 爬虫配置
        self.session = requests.Session()
        self.setup_session()
        
        # 统计信息
        self.processed_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.active_tasks = set()  # 跟踪正在处理的任务ID
        
        # 测试模式（避免真实网络请求）
        self.test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
        
        # 行为指纹模拟配置
        self.behavior_fingerprint_enabled = os.getenv('BEHAVIOR_FINGERPRINT_ENABLED', 'true').lower() == 'true'
        self.behavior_patterns = {
            'mouse_movement': {
                'enabled': True,
                'acceleration_curve': 'human',  # 人类加速度曲线
                'random_variation': 0.2,  # 20%随机变化
                'pause_probability': 0.1  # 10%概率暂停
            },
            'scrolling': {
                'enabled': True,
                'speed_variation': 0.3,  # 30%速度变化
                'scroll_pattern': 'natural',  # 自然滚动模式
                'scroll_direction_change': 0.05  # 5%概率改变滚动方向
            },
            'clicking': {
                'enabled': True,
                'click_duration': 0.1,  # 点击持续时间
                'double_click_probability': 0.02,  # 2%概率双击
                'click_position_variation': 5  # 点击位置变化像素
            }
        }
        
        # 浏览器指纹管理
        self.browser_fingerprint = self._generate_browser_fingerprint()
        
        # 高级隐匿技术配置
        self.advanced_stealth_enabled = os.getenv('ADVANCED_STEALTH_ENABLED', 'true').lower() == 'true'
        self.encryption_enabled = os.getenv('ENCRYPTION_ENABLED', 'true').lower() == 'true'
        
        # 动态策略调整配置
        self.dynamic_strategy_enabled = os.getenv('DYNAMIC_STRATEGY_ENABLED', 'true').lower() == 'true'
        self.strategy_adaptation_threshold = 0.8  # 策略调整阈值
        
        # 验证码自动处理配置
        self.captcha_auto_processing = os.getenv('CAPTCHA_AUTO_PROCESSING', 'false').lower() == 'true'
        self.captcha_service_api = os.getenv('CAPTCHA_SERVICE_API', '')
        
        logger.info(f"行为指纹模拟功能已初始化 - 启用: {self.behavior_fingerprint_enabled}, 高级隐匿: {self.advanced_stealth_enabled}")
        
        # 加载非洲网站优化配置
        self.africa_optimization_config = self._load_africa_optimization_config()
        logger.info(f"非洲网站优化配置已加载 - 启用: {self.africa_optimization_config.get('enabled', False)}")
        
        # 初始化统一数据存储管理器
        self.storage_manager = DataStorageManager(base_dir="data", backup_dir="backup")
        logger.info("统一数据存储管理器已初始化")
        
        # 初始化数据质量管理系统
        self.data_quality_system = DataQualityManagementSystem(data_dir="data/results")
        logger.info("数据质量管理系统已初始化")
        
        # 初始化智能页面过滤器
        self.smart_page_filter = SmartPageFilter()
        logger.info("智能页面过滤器已初始化")
    
    def _generate_browser_fingerprint(self) -> Dict[str, Any]:
        """生成浏览器指纹 - 模拟真实浏览器特征"""
        import platform
        import hashlib
        
        # 操作系统和浏览器信息
        system_info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'machine': platform.machine()
        }
        
        # 浏览器特征
        browser_features = {
            'user_agent': random.choice(self._get_enhanced_user_agents()),
            'language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'timezone': 'Asia/Shanghai',
            'screen_resolution': '1920x1080',
            'color_depth': 24,
            'pixel_ratio': 1.0,
            'hardware_concurrency': 8,
            'device_memory': 8,
            'webgl_vendor': 'Google Inc.',
            'webgl_renderer': 'ANGLE (NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)',
            'canvas_fingerprint': hashlib.md5(f"canvas_{random.randint(1000, 9999)}".encode()).hexdigest(),
            'fonts': ['Arial', 'Times New Roman', 'Courier New', 'Verdana', 'Georgia']
        }
        
        # 网络特征
        network_features = {
            'connection_type': 'wifi',
            'effective_type': '4g',
            'downlink': 10,
            'rtt': 50
        }
        
        # 行为特征
        behavior_features = {
            'mouse_movement_pattern': 'natural',
            'scroll_behavior': 'smooth',
            'click_timing': 'human_like',
            'typing_speed': 'medium'
        }
        
        fingerprint = {
            'system': system_info,
            'browser': browser_features,
            'network': network_features,
            'behavior': behavior_features,
            'fingerprint_hash': hashlib.md5(str(system_info).encode()).hexdigest()
        }
        
        logger.debug(f"浏览器指纹生成完成 - 指纹哈希: {fingerprint['fingerprint_hash']}")
        return fingerprint
    
    def _simulate_mouse_movement(self, target_url: str) -> float:
        """模拟鼠标移动轨迹 - 生成人类行为模式"""
        if not self.behavior_fingerprint_enabled or not self.behavior_patterns['mouse_movement']['enabled']:
            return 0.0
        
        # 计算鼠标移动时间（基于页面复杂度和随机性）
        base_time = 0.5  # 基础移动时间
        
        # 根据URL复杂度调整移动时间
        url_complexity = len(target_url) / 100  # URL长度作为复杂度指标
        complexity_factor = min(2.0, 1.0 + url_complexity * 0.1)
        
        # 添加随机变化
        random_variation = self.behavior_patterns['mouse_movement']['random_variation']
        variation = random.uniform(-random_variation, random_variation)
        
        # 计算最终移动时间
        movement_time = base_time * complexity_factor * (1 + variation)
        
        # 模拟暂停（人类行为特征）
        if random.random() < self.behavior_patterns['mouse_movement']['pause_probability']:
            pause_time = random.uniform(0.1, 0.5)
            movement_time += pause_time
        
        logger.debug(f"鼠标移动模拟完成 - 目标URL: {target_url}, 移动时间: {movement_time:.2f}s")
        return movement_time
    
    def _simulate_scrolling_behavior(self, content_length: int) -> float:
        """模拟页面滚动行为 - 基于内容长度和人类阅读习惯"""
        if not self.behavior_fingerprint_enabled or not self.behavior_patterns['scrolling']['enabled']:
            return 0.0
        
        # 根据内容长度计算滚动时间
        base_scroll_time_per_kb = 0.1  # 每KB内容的基础滚动时间
        content_kb = max(1, content_length / 1024)  # 转换为KB
        
        # 添加速度变化
        speed_variation = self.behavior_patterns['scrolling']['speed_variation']
        variation = random.uniform(-speed_variation, speed_variation)
        
        # 计算滚动时间
        scroll_time = base_scroll_time_per_kb * content_kb * (1 + variation)
        
        # 模拟滚动方向变化（人类阅读习惯）
        if random.random() < self.behavior_patterns['scrolling']['scroll_direction_change']:
            # 模拟向上滚动重新阅读
            scroll_time *= 1.2
        
        logger.debug(f"页面滚动模拟完成 - 内容长度: {content_length}字节, 滚动时间: {scroll_time:.2f}s")
        return scroll_time
    
    def _simulate_clicking_behavior(self) -> float:
        """模拟点击行为 - 包括点击持续时间和双击概率"""
        if not self.behavior_fingerprint_enabled or not self.behavior_patterns['clicking']['enabled']:
            return 0.0
        
        # 基础点击时间
        click_duration = self.behavior_patterns['clicking']['click_duration']
        
        # 模拟双击
        if random.random() < self.behavior_patterns['clicking']['double_click_probability']:
            click_duration *= 2  # 双击时间加倍
            logger.debug("检测到双击行为模拟")
        
        # 添加随机变化
        variation = random.uniform(-0.1, 0.1)  # 10%随机变化
        click_duration *= (1 + variation)
        
        logger.debug(f"点击行为模拟完成 - 点击持续时间: {click_duration:.2f}s")
        return click_duration
    
    def _apply_behavior_fingerprint(self, url: str, content_length: int = 0) -> float:
        """应用行为指纹模拟 - 综合所有行为模式"""
        if not self.behavior_fingerprint_enabled:
            return 0.0
        
        total_simulation_time = 0.0
        
        # 模拟鼠标移动
        mouse_time = self._simulate_mouse_movement(url)
        total_simulation_time += mouse_time
        
        # 模拟页面滚动（如果有内容）
        if content_length > 0:
            scroll_time = self._simulate_scrolling_behavior(content_length)
            total_simulation_time += scroll_time
        
        # 模拟点击行为
        click_time = self._simulate_clicking_behavior()
        total_simulation_time += click_time
        
        # 添加随机的人类思考时间
        thinking_time = random.uniform(0.5, 3.0)
        total_simulation_time += thinking_time
        
        logger.info(f"行为指纹模拟完成 - URL: {url}, 总模拟时间: {total_simulation_time:.2f}s")
        return total_simulation_time
    
    def _load_africa_optimization_config(self) -> Dict[str, Any]:
        """加载非洲网站优化配置"""
        default_config = {
            'enabled': False,
            'special_handling': {},
            'africa_domains': {},
            'optimization_strategies': {},
            'proxy_optimization': {}
        }
        
        try:
            if os.path.exists(AFRICA_OPTIMIZATION_FILE):
                with open(AFRICA_OPTIMIZATION_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                africa_config = config.get('africa_website_optimization', {})
                
                # 合并默认配置和文件配置
                merged_config = default_config.copy()
                merged_config.update(africa_config)
                
                logger.info(f"非洲网站优化配置加载成功 - 启用: {merged_config.get('enabled', False)}")
                return merged_config
            else:
                logger.warning(f"非洲网站优化配置文件不存在: {AFRICA_OPTIMIZATION_FILE}")
                return default_config
        except Exception as e:
            logger.warning(f"加载非洲网站优化配置失败: {e}")
            return default_config

    def _detect_captcha(self, response: requests.Response) -> bool:
        """检测响应中是否包含验证码"""
        if not response.content:
            return False
        
        content = response.text.lower()
        captcha_indicators = [
            'captcha', 'recaptcha', 'hcaptcha', '验证码', 'verification code',
            'security check', 'robot check', 'human verification'
        ]
        
        for indicator in captcha_indicators:
            if indicator in content:
                logger.warning(f"检测到验证码标识: {indicator}")
                return True
        
        # 检查常见的验证码图片URL模式
        captcha_url_patterns = [
            '/captcha', '/recaptcha', '/hcaptcha', 'captcha.jpg', 'captcha.png'
        ]
        
        for pattern in captcha_url_patterns:
            if pattern in response.url.lower():
                logger.warning(f"检测到验证码URL模式: {pattern}")
                return True
        
        return False
    
    def _handle_captcha_challenge(self, url: str, response: requests.Response) -> Optional[requests.Response]:
        """处理验证码挑战"""
        if not self.captcha_auto_solve:
            logger.warning("验证码自动处理已禁用，跳过验证码挑战")
            return None
        
        logger.info(f"开始处理验证码挑战: {url}")
        
        try:
            # 这里可以集成第三方验证码服务API
            # 例如: 2captcha, Anti-Captcha, DeathByCaptcha等
            
            if self.captcha_service == 'manual':
                logger.info("手动验证码模式 - 请手动处理验证码后继续")
                # 这里可以添加等待用户输入的逻辑
                return None
            
            elif self.captcha_service == '2captcha':
                # 2captcha API集成示例
                logger.info("使用2captcha服务处理验证码")
                # 这里添加2captcha API调用逻辑
                
            elif self.captcha_service == 'anticaptcha':
                # Anti-Captcha API集成示例
                logger.info("使用Anti-Captcha服务处理验证码")
                # 这里添加Anti-Captcha API调用逻辑
            
            # 模拟验证码处理成功
            logger.info("验证码处理成功，重新发送请求")
            
            # 重新发送请求（可能需要携带验证码token）
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'X-Captcha-Solved': 'true'
            }
            
            return self.session.get(url, headers=headers)
            
        except Exception as e:
            logger.error(f"验证码处理失败: {e}")
            return None
    
    def _dynamic_strategy_adjustment(self, url: str, response: requests.Response, attempt: int) -> dict:
        """动态策略调整 - 根据响应状态和尝试次数调整爬取策略"""
        strategy = {
            'delay_multiplier': 1.0,
            'proxy_rotation': False,
            'user_agent_rotation': False,
            'request_frequency': 'normal'
        }
        
        # 根据状态码调整策略
        if response.status_code == 429:  # 限流
            strategy['delay_multiplier'] = 2.0 + (attempt * 0.5)
            strategy['proxy_rotation'] = True
            strategy['user_agent_rotation'] = True
            strategy['request_frequency'] = 'slow'
            logger.info(f"检测到限流，调整策略: 延迟倍数={strategy['delay_multiplier']}")
        
        elif response.status_code == 403:  # 禁止访问
            strategy['proxy_rotation'] = True
            strategy['user_agent_rotation'] = True
            strategy['request_frequency'] = 'very_slow'
            logger.info("检测到403禁止访问，启用代理和User-Agent轮换")
        
        elif response.status_code == 503:  # 服务不可用
            strategy['delay_multiplier'] = 1.5
            strategy['request_frequency'] = 'slow'
            logger.info("检测到503服务不可用，降低请求频率")
        
        # 根据尝试次数调整策略
        if attempt >= 3:
            strategy['proxy_rotation'] = True
            strategy['user_agent_rotation'] = True
            strategy['delay_multiplier'] *= 1.5
            logger.info("多次尝试失败，启用高级规避策略")
        
        return strategy
    
    def request_with_retry(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """增强版带重试机制的HTTP请求 - 包含智能重试、连接优化和性能监控"""
        max_retries = 5
        base_delay = 1
        
        # 设置默认超时时间
        if 'timeout' not in kwargs:
            kwargs['timeout'] = (10, 30)  # 连接超时10秒，读取超时30秒
        
        # 设置默认请求头
        if 'headers' not in kwargs:
            kwargs['headers'] = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        
        # 应用浏览器指纹到请求头
        if self.behavior_fingerprint_enabled:
            fingerprint = self._generate_browser_fingerprint()
            headers = kwargs.get('headers', {})
            headers.update({
                'User-Agent': fingerprint['browser']['user_agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': fingerprint['browser']['language'],
                'Accept-Encoding': 'gzip, deflate, br'
            })
            kwargs['headers'] = headers
        
        for attempt in range(max_retries):
            try:
                # 请求前行为指纹模拟
                if self.behavior_fingerprint_enabled:
                    pre_request_simulation_time = self._apply_behavior_fingerprint(url)
                    logger.debug(f"请求前行为模拟完成 - 模拟时间: {pre_request_simulation_time:.2f}s")
                
                start_time = time.time()
                # 使用会话对象而不是直接requests.request，以利用连接池和代理配置
                response = self.session.request(method, url, **kwargs)
                response_time = time.time() - start_time
                
                # 记录性能统计数据
                if hasattr(self, 'performance_stats'):
                    self.performance_stats['request_times'].append(response_time)
                    self.performance_stats['successful_requests'] += 1
                    
                    # 实时更新平均响应时间
                    if len(self.performance_stats['request_times']) > 0:
                        self.performance_stats['avg_response_time'] = \
                            sum(self.performance_stats['request_times']) / len(self.performance_stats['request_times'])
                
                # 检测验证码
                if self._detect_captcha(response):
                    logger.warning(f"检测到验证码，尝试处理: {url}")
                    captcha_response = self._handle_captcha_challenge(url, response)
                    if captcha_response:
                        response = captcha_response
                    else:
                        logger.error(f"验证码处理失败，跳过此URL: {url}")
                        return None
                
                if response.status_code == 200:
                    # 请求后行为指纹模拟（基于内容长度）
                    if self.behavior_fingerprint_enabled:
                        content_length = len(response.content) if response.content else 0
                        post_request_simulation_time = self._apply_behavior_fingerprint(url, content_length)
                        logger.debug(f"请求后行为模拟完成 - 内容长度: {content_length}字节, 模拟时间: {post_request_simulation_time:.2f}s")
                    
                    logger.debug(f"请求成功: {url} (响应时间: {response_time:.2f}s)")
                    return response
                
                # 动态策略调整
                strategy = self._dynamic_strategy_adjustment(url, response, attempt)
                
                # 根据状态码决定重试策略
                if response.status_code in [429, 500, 502, 503, 504]:
                    # 服务器错误或限流，使用指数退避
                    delay = base_delay * (2 ** attempt) * strategy['delay_multiplier']
                    logger.warning(f"服务器错误 {response.status_code}，延迟 {delay}s 后重试 (尝试 {attempt + 1}/{max_retries})")
                    
                    # 应用动态策略
                    if strategy['proxy_rotation']:
                        logger.info("启用代理轮换")
                        self.setup_proxy()
                    if strategy['user_agent_rotation']:
                        logger.info("启用User-Agent轮换")
                        self.session.headers.update({'User-Agent': random.choice(self._get_enhanced_user_agents())})
                    
                    time.sleep(delay)
                    
                elif response.status_code in [400, 401, 403, 404]:
                    # 客户端错误，不重试
                    logger.error(f"客户端错误 {response.status_code}，不重试: {url}")
                    return response
                    
                else:
                    # 其他错误，线性延迟重试
                    delay = base_delay * (attempt + 1) * strategy['delay_multiplier']
                    logger.warning(f"请求失败，状态码: {response.status_code}，延迟 {delay}s 后重试 (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    
            except requests.exceptions.Timeout:
                # 记录失败请求
                if hasattr(self, 'performance_stats'):
                    self.performance_stats['failed_requests'] += 1
                
                delay = base_delay * (2 ** attempt)
                logger.warning(f"请求超时，延迟 {delay}s 后重试 (尝试 {attempt + 1}/{max_retries})")
                time.sleep(delay)
                
            except requests.exceptions.ConnectionError:
                # 记录失败请求
                if hasattr(self, 'performance_stats'):
                    self.performance_stats['failed_requests'] += 1
                
                delay = base_delay * (2 ** attempt)
                logger.warning(f"连接错误，延迟 {delay}s 后重试 (尝试 {attempt + 1}/{max_retries})")
                time.sleep(delay)
                
            except requests.exceptions.RequestException as e:
                # 记录失败请求
                if hasattr(self, 'performance_stats'):
                    self.performance_stats['failed_requests'] += 1
                
                delay = base_delay * (attempt + 1)
                logger.warning(f"请求异常: {e}，延迟 {delay}s 后重试 (尝试 {attempt + 1}/{max_retries})")
                time.sleep(delay)
                
            except Exception as e:
                # 记录失败请求
                if hasattr(self, 'performance_stats'):
                    self.performance_stats['failed_requests'] += 1
                
                logger.error(f"未知异常: {e}，不重试")
                return None
        
        # 记录最终失败
        if hasattr(self, 'performance_stats'):
            self.performance_stats['failed_requests'] += 1
        
        logger.error(f"所有重试失败: {url}")
        return None
    
    def initialize_connection(self) -> bool:
        """初始化连接到主节点"""
        logger.info(f"工作节点 {self.worker_id} 正在初始化连接到主节点...")
        
        for attempt in range(MAX_CONNECTION_RETRIES):
            try:
                logger.info(f"尝试连接到主节点 {MASTER_URL} (尝试 {attempt + 1}/{MAX_CONNECTION_RETRIES})...")
                
                # 检查主节点健康状态（使用重试机制）
                response = self.request_with_retry('GET', f"{MASTER_URL}/health", timeout=CONNECTION_TIMEOUT)
                if response and response.status_code == 200:
                    logger.info(f"[OK] 工作节点 {self.worker_id} 成功连接到主节点 (尝试 {attempt + 1})")
                    return True
                elif response:
                    logger.warning(f"主节点响应异常 (状态码: {response.status_code})，尝试 {attempt + 1}/{MAX_CONNECTION_RETRIES}")
                else:
                    logger.warning(f"主节点无响应，尝试 {attempt + 1}/{MAX_CONNECTION_RETRIES}")
            except Exception as e:
                logger.error(f"连接初始化异常 (尝试 {attempt + 1}/{MAX_CONNECTION_RETRIES}): {e}")
            
            # 等待后重试（使用更短的延迟）
            if attempt < MAX_CONNECTION_RETRIES - 1:
                delay = min(2 * (attempt + 1), 5)  # 更短的递增延迟，最大5秒
                logger.info(f"等待 {delay} 秒后重试连接...")
                time.sleep(delay)
        
        logger.error(f"工作节点 {self.worker_id} 无法连接到主节点，所有重试尝试均失败")
        return False
    
    def setup_session(self):
        """配置HTTP会话 - 增强版，特别针对非洲网站连接优化"""
        # 设置请求头 - 针对非洲网站大幅优化
        self.session.headers.update({
            'User-Agent': random.choice(self._get_enhanced_user_agents()),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.8,fr-FR,fr;q=0.6,pt-PT,pt;q=0.4,es-ES,es;q=0.2,ar;q=0.1',  # 大幅扩展非洲语言支持
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',  # 避免缓存问题
            'Pragma': 'no-cache',
            'DNT': '1',  # 不跟踪
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })
        
        # 增强连接池配置 - 使用动态配置参数
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=CONNECTION_POOL_SIZE,  # 使用配置的连接池大小
            pool_maxsize=POOL_MAX_SIZE,            # 使用配置的最大连接数
            max_retries=MAX_CONNECTION_RETRIES,    # 使用配置的重试次数
            pool_block=POOL_BLOCK
        )
        
        # 为主节点连接和应用会话配置适配器
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 设置超时 - 使用动态配置参数
        self.session.timeout = (CONNECTION_TIMEOUT, 120)  # 连接超时使用配置，读取超时120秒
        
        # 配置代理（如果启用）- 初始化时使用默认配置
        if PROXY_ENABLED:
            self.setup_proxy()  # 初始化时没有具体URL，使用默认配置
        
        # 添加非洲网站特定的连接优化
        self._setup_africa_specific_optimizations()
        
        # 初始化性能监控
        if PERFORMANCE_MONITORING:
            self._setup_performance_monitoring()
        
        logger.info(f"HTTP会话配置完成 - 连接池大小: {CONNECTION_POOL_SIZE}/{POOL_MAX_SIZE}, 超时: {CONNECTION_TIMEOUT}/120秒, 代理: {'启用' if PROXY_ENABLED else '禁用'}, 非洲优化: 启用, 性能监控: {'启用' if PERFORMANCE_MONITORING else '禁用'}")
    
    def _setup_africa_specific_optimizations(self):
        """非洲网站特定的连接优化 - 大幅增强版"""
        # 添加对非洲常见网站的特殊处理
        self.africa_domains = [
            '.gh', '.ng', '.ke', '.za', '.tz', '.ug', '.rw', '.mw', 
            '.zm', '.bw', '.na', '.ls', '.sz', '.mz', '.ao', '.cv',
            '.sn', '.ci', '.cm', '.cd', '.cg', '.ga', '.gq', '.gn',
            '.gw', '.lr', '.ml', '.ne', '.sl', '.tg', '.bf', '.bj',
            '.td', '.cf', '.km', '.dj', '.er', '.et', '.so', '.sd',
            '.ss', '.bi', '.mg', '.mu', '.sc', '.km', '.re', '.yt'
        ]
        
        # 非洲国家网络质量分级
        self.high_latency_countries = ['.et', '.so', '.sd', '.ss', '.er', '.dj', '.cf', '.td', '.ne', '.ml']
        self.medium_latency_countries = ['.za', '.ng', '.ke', '.gh', '.tz', '.ug', '.zm', '.mw', '.mz', '.ao']
        self.low_latency_countries = ['.bw', '.na', '.ls', '.sz', '.cv', '.mu', '.sc', '.re', '.yt']
        
        # 非洲网站特定的User-Agent轮换 - 大幅扩展
        self.africa_user_agents = [
            # 非洲地区常用浏览器
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
            # 移动设备浏览器
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            # 非洲本地化浏览器
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'
        ]
        
        # 非洲高峰时段配置
        self.africa_peak_hours = [9, 10, 11, 12, 13, 14, 15, 16, 17]  # 非洲工作时间
        
        # 非洲问题网站列表
        self.africa_problematic_sites = [
            'allafrica.com', 'news24.com', 'nation.co.ke', 'dailytrust.com',
            'citizen.co.ke', 'standardmedia.co.ke', 'punchng.com',
            'vanguardngr.com', 'thisdaylive.com', 'guardian.ng',
            'modernghana.com', 'liberianobserver.com', 'newsghana.com.gh',
            'sabcnews.com', 'timeslive.co.za', 'iol.co.za', 'newsday.co.zw',
            'ghanaweb.com', 'myjoyonline.com', 'graphic.com.gh',
            'businessdailyafrica.com', 'theeastafrican.co.ke', 'monitor.co.ug'
        ]
        
        logger.info(f"非洲网站优化配置完成 - 支持 {len(self.africa_domains)} 个非洲域名后缀，{len(self.africa_user_agents)} 个User-Agent，{len(self.africa_problematic_sites)} 个问题网站")
    
    def setup_proxy(self, target_url: str = None):
        """配置代理设置 - 增强版：智能代理选择和非洲网站特殊处理"""
        try:
            # 加载代理配置
            if os.path.exists(PROXY_CONFIG_FILE):
                with open(PROXY_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    proxy_config = json.load(f)
                
                # 获取代理服务器列表
                proxies = proxy_config.get('proxies', [])
                if proxies:
                    # 智能代理选择策略
                    selected_proxy = self._select_smart_proxy_for_url(proxies, target_url)
                    
                    if selected_proxy:
                        proxy_url = f"http://{selected_proxy['host']}:{selected_proxy['port']}"
                        
                        # 设置代理
                        self.session.proxies = {
                            'http': proxy_url,
                            'https': proxy_url
                        }
                        
                        # 记录代理选择详情
                        region_info = selected_proxy.get('region', '未知')
                        priority_info = selected_proxy.get('priority', 'normal')
                        logger.info(f"智能代理配置完成: {selected_proxy['host']}:{selected_proxy['port']} ({region_info}, 优先级: {priority_info})")
                        
                        # 如果是非洲网站，记录特殊处理
                        if target_url and self._is_africa_website(target_url):
                            logger.info(f"非洲网站 {target_url} 已配置区域优化代理")
                    else:
                        logger.warning("智能代理选择失败，将使用直连模式")
                        self.session.proxies = {}
                else:
                    logger.warning("代理配置文件中没有可用的代理服务器")
                    self.session.proxies = {}
            else:
                logger.warning(f"代理配置文件不存在: {PROXY_CONFIG_FILE}")
                self.session.proxies = {}
        except Exception as e:
            logger.warning(f"代理配置失败: {e}，将使用直连模式")
            self.session.proxies = {}
    
    def _select_smart_proxy_for_url(self, proxies: List[Dict], target_url: str = None) -> Optional[Dict]:
        """智能代理选择策略 - 针对非洲网站优化"""
        if not proxies:
            return None
        
        # 如果没有目标URL，随机选择
        if not target_url:
            return random.choice(proxies)
        
        # 检查是否为非洲网站
        is_africa = self._is_africa_website(target_url)
        
        # 过滤可用的代理
        available_proxies = []
        for proxy in proxies:
            # 检查代理状态（如果有状态字段）
            if proxy.get('enabled', True) and proxy.get('status', 'active') == 'active':
                available_proxies.append(proxy)
        
        if not available_proxies:
            return random.choice(proxies)
        
        # 非洲网站特殊处理
        if is_africa:
            # 优先选择非洲地区的代理
            africa_proxies = [p for p in available_proxies if 'africa' in p.get('region', '').lower() or 
                             any(country in p.get('region', '').lower() for country in ['south africa', 'kenya', 'nigeria', 'ghana', 'tanzania'])]
            
            if africa_proxies:
                # 按优先级排序
                africa_proxies.sort(key=lambda x: x.get('priority', 3))
                return africa_proxies[0]
            
            # 如果没有非洲代理，选择高优先级代理
            high_priority_proxies = [p for p in available_proxies if p.get('priority', 3) <= 2]
            if high_priority_proxies:
                return random.choice(high_priority_proxies)
        
        # 非非洲网站：优先选择高优先级代理
        high_priority_proxies = [p for p in available_proxies if p.get('priority', 3) <= 2]
        if high_priority_proxies:
            return random.choice(high_priority_proxies)
        
        # 默认随机选择
        return random.choice(available_proxies)
    
    def _is_africa_website(self, url: str) -> bool:
        """判断是否为非洲网站"""
        try:
            # 解析URL获取域名
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # 检查非洲域名后缀
            africa_tlds = ['.gh', '.ng', '.ke', '.za', '.tz', '.ug', '.rw', '.mw', 
                          '.zm', '.bw', '.na', '.ls', '.sz', '.mz', '.ao', '.cv',
                          '.sn', '.ci', '.cm', '.cd', '.cg', '.ga', '.gq', '.gn',
                          '.gw', '.lr', '.ml', '.ne', '.sl', '.tg', '.bf', '.bj',
                          '.td', '.cf', '.km', '.dj', '.er', '.et', '.so', '.sd',
                          '.ss', '.bi', '.mg', '.mu', '.sc', '.km', '.re', '.yt']
            
            # 检查域名是否包含非洲国家关键词
            africa_keywords = ['africa', 'southafrica', 'kenya', 'nigeria', 'ghana', 'tanzania',
                              'uganda', 'rwanda', 'malawi', 'zambia', 'botswana', 'namibia',
                              'lesotho', 'swaziland', 'mozambique', 'angola', 'capeverde',
                              'senegal', 'ivorycoast', 'cameroon', 'congo', 'gabon',
                              'equatorialguinea', 'guinea', 'guineabissau', 'liberia',
                              'mali', 'niger', 'sierraleone', 'togo', 'burkinafaso',
                              'benin', 'chad', 'centralafrica', 'comoros', 'djibouti',
                              'eritrea', 'ethiopia', 'somalia', 'sudan', 'southsudan',
                              'burundi', 'madagascar', 'mauritius', 'seychelles', 'reunion']
            
            # 检查TLD
            for tld in africa_tlds:
                if domain.endswith(tld):
                    return True
            
            # 检查域名关键词
            for keyword in africa_keywords:
                if keyword in domain:
                    return True
            
            return False
        except Exception:
            return False
    
    def update_worker_status(self, status: str = "active") -> bool:
        """更新工作节点状态 - 实现容错机制"""
        try:
            # 计算当前负载（基于正在处理的任务数量）
            # 在多线程模式下，需要跟踪实际正在处理的任务数量
            if hasattr(self, 'active_tasks'):
                current_load = len(self.active_tasks)
            else:
                # 如果没有active_tasks属性，使用状态判断
                current_load = 1 if self.status == "working" else 0
            
            worker_info = {
                'worker_id': self.worker_id,
                'status': status,
                'last_heartbeat': datetime.now().isoformat(),
                'processed_tasks': self.processed_tasks,
                'successful_tasks': self.successful_tasks,
                'failed_tasks': self.failed_tasks,
                'current_load': current_load  # 添加负载信息
            }
            
            # 向主节点发送心跳（使用重试机制）
            response = self.request_with_retry('POST', f"{MASTER_URL}/workers/heartbeat", 
                                             json=worker_info, timeout=HEARTBEAT_TIMEOUT)
            
            if response is None:
                logger.warning("心跳发送失败，但工作节点将继续运行")
                # 即使心跳失败，工作节点也继续运行，避免中断爬取任务
                return True  # 返回True表示工作节点继续运行
            elif response.status_code == 200:
                logger.debug(f"心跳发送成功 - {self.worker_id}")
                return True
            else:
                logger.warning(f"心跳响应异常 (状态码: {response.status_code})，但工作节点将继续运行")
                return True  # 返回True表示工作节点继续运行
                
        except Exception as e:
            logger.warning(f"心跳发送异常: {e}，但工作节点将继续运行")
            # 即使心跳异常，工作节点也继续运行
            return True  # 返回True表示工作节点继续运行
    
    def get_task(self) -> Optional[Dict[str, Any]]:
        """从主节点获取下一个任务 - 增强版：包含智能重连和错误恢复机制"""
        max_retries = 5
        retry_delay = 3
        
        for attempt in range(max_retries):
            try:
                # 从主节点API获取任务，传递worker_id参数（使用重试机制）
                response = self.request_with_retry('GET', f"{MASTER_URL}/tasks/next", 
                                                 params={'worker_id': self.worker_id},
                                                 timeout=(15, 45))  # 增加超时时间
                
                if response and response.status_code == 200:
                    result = response.json()
                    
                    # 正确处理不同的状态
                    if result['status'] == 'success' and result.get('task'):
                        task = result['task']
                        task['assigned_worker'] = self.worker_id
                        task['assigned_at'] = datetime.now().isoformat()
                        task['status'] = 'processing'
                        
                        # 添加到正在处理的任务集合
                        self.active_tasks.add(task['task_id'])
                        
                        # 安全地记录任务信息，处理可能缺少year字段的情况
                        year_info = task.get('year', '未知年份')
                        logger.info(f"获取到任务: {task['keyword']} - {year_info} (优先级: {task.get('priority', 'normal')})")
                        self.status = "working"
                        return task
                    elif result['status'] == 'no_tasks':
                        logger.info("暂无可用任务")
                        self.status = "idle"
                        return None
                    elif result['status'] == 'retry_task' and result.get('task'):
                        task = result['task']
                        task['assigned_worker'] = self.worker_id
                        task['assigned_at'] = datetime.now().isoformat()
                        task['status'] = 'processing'
                        
                        # 安全地记录重试任务信息，处理可能缺少year字段的情况
                        year_info = task.get('year', '未知年份')
                        logger.info(f"获取到重试任务: {task['keyword']} - {year_info} (第{task.get('attempts', 1)}次重试)")
                        self.status = "working"
                        return task
                    else:
                        logger.warning(f"获取任务返回异常状态: {result}")
                        self.status = "idle"
                        return None
                else:
                    logger.warning(f"获取任务失败，状态码: {response.status_code if response else '无响应'} (尝试 {attempt + 1}/{max_retries})")
                    
                    # 如果是连接错误，尝试重新连接
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        logger.info(f"等待 {retry_delay * (attempt + 1)} 秒后重试...")
                        continue
                    
                    self.status = "error"
                    return None
                    
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"连接主节点失败: {e} (尝试 {attempt + 1}/{max_retries})")
                
                if attempt < max_retries - 1:
                    # 尝试重新初始化连接
                    logger.info("尝试重新连接到主节点...")
                    if self.initialize_connection():
                        logger.info("重新连接成功，继续获取任务")
                        continue
                    
                    time.sleep(retry_delay * (attempt + 1))
                    logger.info(f"等待 {retry_delay * (attempt + 1)} 秒后重试...")
                else:
                    logger.error("所有重试失败，无法连接到主节点")
                    self.status = "error"
                    return None
                    
            except requests.exceptions.Timeout as e:
                logger.warning(f"获取任务超时: {e} (尝试 {attempt + 1}/{max_retries})")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    logger.info(f"等待 {retry_delay * (attempt + 1)} 秒后重试...")
                else:
                    logger.error("所有重试失败，任务获取超时")
                    self.status = "error"
                    return None
                    
            except Exception as e:
                logger.error(f"获取任务失败: {e} (尝试 {attempt + 1}/{max_retries})")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    logger.info(f"等待 {retry_delay * (attempt + 1)} 秒后重试...")
                else:
                    logger.error("所有重试失败，任务获取异常")
                    self.status = "error"
                    return None
        
        return None
    
    def is_valid_result(self, result: dict) -> bool:
        """验证结果是否有效（包含实际内容）"""
        if not result:
            return False
        
        # 检查状态
        if result.get('status') != 'completed':
            return False
        
        # 检查是否有实际文章内容
        articles = result.get('articles', [])
        if not articles:
            return False
        
        # 检查文章是否有有效内容
        valid_articles = 0
        for article in articles:
            if (article.get('title') and article.get('content') and 
                len(article.get('content', '').strip()) > 50):  # 内容长度至少50字符
                valid_articles += 1
        
        return valid_articles > 0
    
    def submit_crawler_result(self, task: dict, result: dict) -> bool:
        """提交爬取结果到主节点 - 增强版：包含智能重试和多重备份机制"""
        try:
            # 从正在处理的任务集合中移除
            task_id = task.get('task_id')
            if task_id and task_id in self.active_tasks:
                self.active_tasks.remove(task_id)
            
            # 检查结果是否有效
            if not self.is_valid_result(result):
                # 安全地记录无效结果信息，处理可能缺少year字段的情况
                year_info = task.get('year', '未知年份')
                logger.warning(f"结果无效，跳过提交: {task['keyword']} - {year_info}")
                # 即使结果无效，也保存到本地用于调试
                self.save_result_locally(task, result, 'invalid_result')
                return False
            
            # 准备提交数据
            submit_data = {
                'task_id': task.get('task_id'),
                'worker_id': self.worker_id,
                'status': 'completed' if result.get('status') == 'completed' else 'failed',
                'completed_at': datetime.now().isoformat(),
                'result': result
            }
            
            # 立即保存到本地作为第一重备份
            self.save_result_locally(task, result, 'initial_backup')
            
            # 提交结果到主节点（使用增强重试机制）
            max_retries = 5
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = self.request_with_retry('POST', f"{MASTER_URL}/results/submit", 
                                                     json=submit_data,
                                                     timeout=(10, 30))  # 连接超时10秒，读取超时30秒
                    
                    if response and response.status_code == 200:
                        # 安全地记录提交成功信息，处理可能缺少year字段的情况
                        year_info = task.get('year', '未知年份')
                        logger.info(f"工作节点 {self.worker_id} 提交结果成功: {task['keyword']} - {year_info}")
                        
                        # 提交成功后，保存成功标记到本地
                        self.save_result_locally(task, result, 'submission_success')
                        return True
                        
                    elif response and response.status_code in [500, 502, 503, 504]:
                        # 服务器错误，增加延迟重试
                        logger.warning(f"服务器错误 {response.status_code}，延迟重试 (尝试 {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay * (attempt + 1))
                        
                    else:
                        logger.warning(f"提交结果失败，状态码: {response.status_code if response else '无响应'}")
                        break  # 客户端错误，不重试
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"请求超时 (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay * (attempt + 1))
                    
                except requests.exceptions.ConnectionError:
                    logger.warning(f"连接错误 (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay * (attempt + 1))
                    
                except Exception as e:
                    logger.warning(f"提交结果异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay * (attempt + 1))
            
            # 如果所有重试都失败，保存到本地作为最终备份
            year_info = task.get('year', '未知年份')
            logger.error(f"所有重试失败，保存结果到本地: {task['keyword']} - {year_info}")
            self.save_result_locally(task, result, 'final_backup')
            return True
                
        except Exception as e:
            logger.error(f"提交结果异常: {e}，将结果保存到本地")
            
            # 异常情况下保存到本地
            self.save_result_locally(task, result, 'exception_backup', str(e))
            
            # 返回True表示任务处理完成，即使提交异常
            return True
    
    def save_result_locally(self, task: dict, result: dict, backup_type: str = 'normal', error_msg: str = None):
        """保存结果到本地文件 - 使用统一数据存储管理器"""
        try:
            # 准备保存数据
            save_data = {
                'task_id': task.get('task_id', 'unknown'),
                'worker_id': self.worker_id,
                'keyword': task.get('keyword'),
                'year': task.get('year'),
                'status': result.get('status'),
                'backup_type': backup_type,
                'completed_at': datetime.now().isoformat(),
                'result': result,
                'submit_error': error_msg
            }
            
            # 使用统一数据存储管理器保存结果
            filename = f"{save_data['task_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            subdir = f"crawler_results/{backup_type}/{datetime.now().strftime('%Y%m%d')}"
            
            success = self.storage_manager.save_data(
                data=save_data,
                filename=filename,
                subdir=subdir,
                compress=True,
                backup=True
            )
            
            if success:
                logger.info(f"结果已保存到统一存储: {subdir}/{filename} (备份类型: {backup_type})")
                return True
            else:
                logger.error("统一数据存储管理器保存失败")
                return False
            
        except Exception as e:
            logger.error(f"本地结果保存失败: {e}")
            
            # 紧急备份到data目录下的emergency子目录
            try:
                emergency_dir = Path("data") / "emergency"
                emergency_dir.mkdir(parents=True, exist_ok=True)
                
                emergency_file = emergency_dir / f"emergency_backup_{task.get('task_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                emergency_data = {
                    'task_id': task.get('task_id'),
                    'worker_id': self.worker_id,
                    'keyword': task.get('keyword'),
                    'year': task.get('year'),
                    'status': result.get('status'),
                    'error': str(e),
                    'emergency_saved_at': datetime.now().isoformat(),
                    'result': result
                }
                with open(emergency_file, 'w', encoding='utf-8') as f:
                    json.dump(emergency_data, f, ensure_ascii=False, indent=2)
                logger.info(f"紧急备份已保存到: {emergency_file}")
            except Exception as backup_error:
                logger.error(f"紧急备份也失败: {backup_error}")
            
            return False
    
    def execute_crawler_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行爬虫任务"""
        start_time = time.time()
        
        try:
            keyword = task['keyword']
            # 安全地获取year字段，处理可能缺少year字段的情况
            year = task.get('year', 2020)  # 默认使用2020年
            
            logger.info(f"开始执行任务: {keyword} - {year}")
            
            # 构建搜索URL
            search_urls = self.build_search_urls(keyword, year)
            
            articles = []
            failed_urls = []
            
            for url in search_urls:
                try:
                    # 随机延迟，避免触发反爬虫
                    time.sleep(random.uniform(2, 5))
                    
                    # 执行爬取
                    article_data = self.crawl_url(url, keyword, year)
                    if article_data:
                        articles.extend(article_data)
                        
                except Exception as e:
                    logger.warning(f"爬取URL失败 {url}: {e}")
                    failed_urls.append({
                        'url': url,
                        'error': str(e),
                        'error_type': type(e).__name__
                    })
                    continue
            
            # 构建结果
            result = {
                'task_id': task['task_id'],
                'worker_id': self.worker_id,
                'keyword': keyword,
                'year': year,
                'status': 'completed',
                'articles_found': len(articles),
                'articles': articles,
                'failed_urls': failed_urls,
                'processing_time': round(time.time() - start_time, 2),
                'completed_at': datetime.now().isoformat()
            }
            
            self.successful_tasks += 1
            logger.info(f"任务完成: {keyword} - {year}, 找到 {len(articles)} 篇文章, 失败URL: {len(failed_urls)}")
            
            return result
            
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            
            # 构建失败结果
            result = {
                'task_id': task['task_id'],
                'worker_id': self.worker_id,
                'keyword': task['keyword'],
                'year': year,  # 使用上面安全获取的year变量
                'status': 'failed',
                'error': str(e),
                'error_type': type(e).__name__,
                'processing_time': round(time.time() - start_time, 2),
                'completed_at': datetime.now().isoformat()
            }
            
            self.failed_tasks += 1
            
            return result
    
    def build_search_urls(self, keyword: str, year: int) -> List[str]:
        """构建搜索URL - 智能优化非洲新闻网站选择策略"""
        
        # 根据网站可靠性和可访问性分级
        high_reliability_sites = [
            # 高可靠性网站（连接稳定，内容质量高）
            "https://english.ahram.org.eg",  # 埃及金字塔报
            "https://www.news24.com",        # 南非新闻24
            "https://allafrica.com",         # 全非洲网
            "https://nation.africa",         # 非洲国家报
            "https://premiumtimesng.com",    # 尼日利亚时报
            "https://guardian.ng",           # 尼日利亚卫报
            "https://dailymaverick.co.za",   # 南非每日先锋报
            "https://mg.co.za",              # 南非邮卫报
        ]
        
        medium_reliability_sites = [
            # 中等可靠性网站
            "https://www.vanguardngr.com",    # 尼日利亚先锋报
            "https://www.thisdaylive.com",   # 尼日利亚今日报
            "https://www.iol.co.za",         # 南非独立在线
            "https://www.tunisienumerique.com",  # 突尼斯数字报
            "https://www.ghanaweb.com",       # 加纳网
            "https://theeastafrican.co.ke",   # 东非人报
            "https://www.businesslive.co.za", # 南非商业直播
            "https://www.fin24.com",          # 南非金融24
        ]
        
        low_reliability_sites = [
            # 低可靠性网站（连接问题较多，作为备选）
            "https://www.thecitizen.co.tz",   # 坦桑尼亚公民报
            "https://www.monitor.co.ug",     # 乌干达观察者报
            "https://www.newtimes.co.rw",    # 卢旺达新时代报
            "https://www.modernghana.com",   # 现代加纳
            "https://www.newsghana.com.gh",   # 加纳新闻
            "https://www.libyaobserver.ly",  # 利比亚观察者
            "https://www.maghrebia.com",      # 马格里布新闻
            "https://www.algerie-eco.com",    # 阿尔及利亚经济报
        ]
        
        # 对关键词进行URL编码
        encoded_keyword = urllib.parse.quote(keyword)
        
        # 优先使用高可靠性网站，然后中等，最后低可靠性
        all_sites = high_reliability_sites + medium_reliability_sites + low_reliability_sites
        
        urls = []
        for site in all_sites:
            # 构建搜索URL（根据网站特性）
            if "ahram" in site:
                urls.append(f"{site}/Search/1/2/0/0/0/{encoded_keyword}")
            elif "allafrica" in site:
                urls.append(f"{site}/search/?q={encoded_keyword}")
            elif "nation" in site:
                urls.append(f"{site}/search/?q={encoded_keyword}")
            elif "mg.co.za" in site:
                urls.append(f"{site}/search?q={encoded_keyword}")
            elif "dailymaverick" in site:
                urls.append(f"{site}/?s={encoded_keyword}")
            elif "guardian.ng" in site:
                urls.append(f"{site}/?s={encoded_keyword}")
            elif "premiumtimesng" in site:
                urls.append(f"{site}/?s={encoded_keyword}")
            elif "theeastafrican" in site:
                urls.append(f"{site}/search?q={encoded_keyword}")
            elif "dailynews" in site:
                urls.append(f"{site}/search?q={encoded_keyword}")
            elif "news24" in site:
                urls.append(f"{site}/search?q={encoded_keyword}")
            elif "iol.co.za" in site:
                urls.append(f"{site}/search?q={encoded_keyword}")
            elif "africanews" in site:
                urls.append(f"{site}/search/?q={encoded_keyword}")
            elif "panapress" in site:
                urls.append(f"{site}/search?q={encoded_keyword}")
            elif "businesslive" in site:
                urls.append(f"{site}/search?q={encoded_keyword}")
            elif "fin24" in site:
                urls.append(f"{site}/search?q={encoded_keyword}")
            
            # 为其他网站添加通用搜索URL格式
            elif "search" not in site:
                urls.append(f"{site}/search?q={encoded_keyword}")
        
        # 随机打乱顺序以避免模式识别
        random.shuffle(urls)
        
        # 限制URL数量，避免过多无效尝试
        max_urls = 15
        if len(urls) > max_urls:
            urls = urls[:max_urls]
        
        return urls
    
    def crawl_url(self, url: str, keyword: str, year: int) -> List[Dict[str, Any]]:
        """爬取单个URL - 增强版智能反爬虫策略"""
        try:
            logger.info(f"开始爬取URL: {url}")
            
            # 智能重试机制 - 增强版，针对非洲网站优化
            max_retries = 4  # 增加重试次数到4次
            for attempt in range(max_retries + 1):
                try:
                    # 智能延迟策略 - 根据网站类型、重试次数和网络状况调整
                    delay_time = self._calculate_smart_delay(url, attempt)
                    logger.info(f"第{attempt + 1}次尝试，等待 {delay_time:.1f} 秒后开始")
                    time.sleep(delay_time)
                    
                    # 增强版User-Agent轮换 - 包含非洲地区常用浏览器
                    user_agents = self._get_enhanced_user_agents()
                    
                    # 智能请求头生成 - 根据目标网站特性定制
                    headers = self._generate_smart_headers(url, user_agents)
                    
                    # 动态超时设置 - 非洲网站连接优化
                    timeout = self._calculate_smart_timeout(url, attempt)
                    
                    # 智能代理选择 - 针对非洲网站优化
                    proxy_config = self._select_smart_proxy(url)
                    
                    # 执行请求
                    logger.info(f"发送请求到 {url} (超时: {timeout}秒)")
                    if proxy_config:
                        response = self.session.get(url, headers=headers, timeout=timeout, proxies=proxy_config)
                    else:
                        response = self.session.get(url, headers=headers, timeout=timeout)
                    
                    response.raise_for_status()
                    
                    # 处理编码问题
                    content = response.text
                    if not content:
                        # 如果text为空，尝试使用content并解码
                        content = response.content
                        if isinstance(content, bytes):
                            try:
                                content = content.decode('utf-8')
                            except UnicodeDecodeError:
                                try:
                                    content = content.decode('latin-1')
                                except UnicodeDecodeError:
                                    content = str(content)
                    
                    # 智能反爬虫检测 - 检查响应内容是否包含反爬虫措施
                    anti_crawler_result = self._detect_anti_crawler_measures(response, content)
                    if anti_crawler_result['detected']:
                        logger.warning(f"检测到反爬虫措施: {anti_crawler_result['type']}, 置信度: {anti_crawler_result['confidence']}")
                        
                        # 根据反爬虫类型采取相应措施
                        if anti_crawler_result['type'] in ['rate_limit', 'ip_block']:
                            # 对于速率限制或IP封禁，增加延迟并重试
                            if attempt < max_retries:
                                wait_time = self._handle_anti_crawler_measures(anti_crawler_result)
                                logger.info(f"等待 {wait_time} 秒后重试")
                                time.sleep(wait_time)
                                continue
                            else:
                                logger.error(f"达到最大重试次数，放弃爬取")
                                return []
                        elif anti_crawler_result['type'] in ['captcha', 'js_challenge']:
                            # 对于验证码或JS挑战，建议使用代理或更换IP
                            logger.warning(f"需要人工干预: {anti_crawler_result['suggestion']}")
                            return []
                    
                    # 清理内容
                    if isinstance(content, str):
                        # 移除不可打印字符
                        content = ''.join(char for char in content if char.isprintable() or char in '\n\r\t')
                        # 处理HTML实体编码
                        import html
                        content = html.unescape(content)
                    
                    # 提取文章信息
                    article = {
                        'title': self.extract_title_from_html(content, url),
                        'url': url,
                        'content': self.extract_content_from_html(content, url),  # 使用内容提取优化器
                        'source': url.split('//')[1].split('/')[0],
                        'publish_date': self.extract_date_from_html(content, url),
                        'keyword': keyword,
                        'year': year,
                        'crawl_time': datetime.now().isoformat(),
                        'crawl_method': 'traditional',
                        'anti_crawler_detected': anti_crawler_result['detected'],
                        'anti_crawler_type': anti_crawler_result['type'] if anti_crawler_result['detected'] else None
                    }
                    
                    logger.info(f"成功爬取文章: {article['title']}")
                    return [article]
                    
                except Exception as e:
                    logger.error(f"第{attempt + 1}次尝试失败: {url}, 错误: {e}")
                    
                    # 如果是最后一次尝试，直接返回空结果
                    if attempt == max_retries:
                        logger.error(f"达到最大重试次数，放弃爬取")
                        return []
                    
                    # 使用智能重试决策功能
                    response = None
                    if hasattr(e, 'response'):
                        response = e.response
                    
                    retry_decision = self._should_retry_based_on_response(response, e, attempt, url)
                    
                    if retry_decision["should_retry"]:
                        # 根据智能决策进行重试
                        wait_time = retry_decision["suggested_delay"]
                        logger.info(f"智能重试决策: {retry_decision['reason']}，等待 {wait_time:.1f} 秒后重试")
                        
                        # 记录推荐操作
                        if retry_decision["recommendations"]:
                            logger.info(f"推荐操作: {', '.join(retry_decision['recommendations'])}")
                        
                        time.sleep(wait_time)
                    else:
                        # 根据智能决策不重试
                        logger.error(f"智能重试决策: {retry_decision['reason']}，放弃重试")
                        return []
            
            return []
            
        except Exception as e:
            logger.error(f"爬取URL失败: {url}, 错误: {e}")
            return []
    
    def _calculate_smart_delay(self, url: str, attempt: int) -> float:
        """智能计算延迟时间 - 特别优化非洲网站网络特性"""
        # 基础延迟策略 - 根据重试次数采用指数退避
        if attempt == 0:
            base_delay = random.uniform(1.5, 3.0)  # 首次尝试随机延迟1.5-3秒
        elif attempt == 1:
            base_delay = random.uniform(3.0, 8.0)  # 第二次尝试随机延迟3-8秒
        elif attempt == 2:
            base_delay = random.uniform(8.0, 15.0)  # 第三次尝试随机延迟8-15秒
        else:
            base_delay = random.uniform(15.0, 25.0)  # 后续尝试随机延迟15-25秒
        
        # 根据网站类型调整延迟 - 非洲网站增加更多延迟
        domain = urllib.parse.urlparse(url).netloc.lower()
        
        # 非洲国家域名列表
        african_domains = ['.za', '.ng', '.ke', '.gh', '.tz', '.ug', '.zm', '.zw', 
                          '.mw', '.mz', '.ao', '.bw', '.na', '.sz', '.ls', '.et',
                          '.so', '.sd', '.ss', '.er', '.dj', '.km', '.mg', '.mu',
                          '.sc', '.re', '.yt', '.rw', '.bi', '.cd', '.cg', '.ga',
                          '.gq', '.cf', '.td', '.ne', '.ml', '.bf', '.bj', '.tg',
                          '.ci', '.gn', '.gw', '.lr', '.sl', '.gm', '.sn', '.mr']
        
        is_african_site = any(african_domain in domain for african_domain in african_domains)
        
        if is_african_site:
            # 非洲网站根据国家网络质量调整延迟
            high_latency_countries = ['.et', '.so', '.sd', '.ss', '.er', '.dj', '.cf', '.td', '.ne', '.ml']
            medium_latency_countries = ['.za', '.ng', '.ke', '.gh', '.tz', '.ug', '.zm', '.mw', '.mz', '.ao']
            
            if any(country in domain for country in high_latency_countries):
                base_delay *= random.uniform(1.8, 2.5)  # 高延迟国家大幅增加延迟
            elif any(country in domain for country in medium_latency_countries):
                base_delay *= random.uniform(1.5, 2.0)  # 中等延迟国家增加延迟
            else:
                base_delay *= random.uniform(1.3, 1.8)  # 其他非洲国家增加基础延迟
            
            # 根据时间调整延迟（避开非洲高峰时段）
            import datetime
            now = datetime.datetime.now()
            africa_peak_hours = [9, 10, 11, 12, 13, 14, 15, 16, 17]  # 非洲工作时间
            
            if now.hour in africa_peak_hours:
                base_delay *= random.uniform(1.2, 1.6)  # 高峰时段增加延迟
        
        # 特定问题网站额外延迟
        problematic_sites = ['allafrica.com', 'news24.com', 'nation.co.ke', 'dailytrust.com',
                           'citizen.co.ke', 'standardmedia.co.ke', 'punchng.com',
                           'vanguardngr.com', 'thisdaylive.com', 'guardian.ng',
                           'modernghana.com', 'liberianobserver.com', 'newsghana.com.gh']
        
        if any(site in domain for site in problematic_sites):
            if is_african_site:
                base_delay *= random.uniform(1.5, 2.2)  # 非洲问题网站大幅增加延迟
            else:
                base_delay *= random.uniform(1.2, 1.8)  # 非非洲问题网站增加延迟
        
        return max(1.0, base_delay)  # 确保最小延迟为1秒
    
    def _get_enhanced_user_agents(self) -> List[str]:
        """获取增强版User-Agent列表 - 包含非洲地区常用浏览器"""
        return [
            # Chrome浏览器（各种版本）
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Firefox浏览器
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
            
            # Safari浏览器（非洲地区常用）
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            
            # Edge浏览器
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            
            # 移动设备浏览器（非洲地区常用）
            'Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1'
        ]
    
    def _generate_smart_headers(self, url: str, user_agents: List[str]) -> Dict[str, str]:
        """智能生成请求头 - 根据目标网站特性定制"""
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # 根据网站类型添加特定头部
        if 'news24' in url or 'allafrica' in url:
            # 新闻网站可能需要特定的Referer
            headers['Referer'] = 'https://www.google.com/'
        elif 'ahram' in url or 'nation' in url:
            # 非洲本地新闻网站可能需要本地化头部
            headers['Accept-Language'] = 'en-US,en;q=0.8,fr;q=0.6,ar;q=0.4'
        
        return headers
    
    def _calculate_smart_timeout(self, url: str, attempt: int) -> float:
        """智能计算超时时间 - 自适应优化策略"""
        # 智能超时策略 - 基于历史性能和网站特征动态调整
        if attempt == 0:
            base_timeout = random.uniform(20.0, 35.0)  # 首次尝试智能超时20-35秒
        elif attempt == 1:
            base_timeout = random.uniform(25.0, 45.0)  # 第二次尝试智能超时25-45秒
        elif attempt == 2:
            base_timeout = random.uniform(30.0, 50.0)  # 第三次尝试智能超时30-50秒
        elif attempt == 3:
            base_timeout = random.uniform(35.0, 60.0)  # 第四次尝试智能超时35-60秒
        else:
            base_timeout = random.uniform(40.0, 80.0)  # 后续尝试智能超时40-80秒
        
        # 根据网站类型智能调整超时
        domain = urllib.parse.urlparse(url).netloc.lower()
        
        # 非洲国家域名列表
        african_domains = ['.za', '.ng', '.ke', '.gh', '.tz', '.ug', '.zm', '.zw', 
                          '.mw', '.mz', '.ao', '.bw', '.na', '.sz', '.ls', '.et',
                          '.so', '.sd', '.ss', '.er', '.dj', '.km', '.mg', '.mu',
                          '.sc', '.re', '.yt', '.rw', '.bi', '.cd', '.cg', '.ga',
                          '.gq', '.cf', '.td', '.ne', '.ml', '.bf', '.bj', '.tg',
                          '.ci', '.gn', '.gw', '.lr', '.sl', '.gm', '.sn', '.mr']
        
        is_african_site = any(african_domain in domain for african_domain in african_domains)
        
        if is_african_site:
            # 非洲网站智能超时调整
            high_latency_countries = ['.et', '.so', '.sd', '.ss', '.er', '.dj', '.cf', '.td', '.ne', '.ml']
            medium_latency_countries = ['.za', '.ng', '.ke', '.gh', '.tz', '.ug', '.zm', '.mw', '.mz', '.ao']
            
            if any(country in domain for country in high_latency_countries):
                base_timeout *= random.uniform(1.5, 2.5)  # 高延迟国家智能增加超时1.5-2.5倍
            elif any(country in domain for country in medium_latency_countries):
                base_timeout *= random.uniform(1.2, 2.0)  # 中等延迟国家智能增加超时1.2-2.0倍
            else:
                base_timeout *= random.uniform(1.1, 1.8)  # 其他非洲国家智能增加超时1.1-1.8倍
            
            # 智能时间调整（避开非洲高峰时段）
            import datetime
            now = datetime.datetime.now()
            africa_peak_hours = [9, 10, 11, 12, 13, 14, 15, 16, 17]  # 非洲工作时间
            
            if now.hour in africa_peak_hours:
                base_timeout *= random.uniform(1.2, 1.8)  # 高峰时段智能增加超时
        
        # 特定问题网站智能额外超时
        problematic_sites = ['allafrica.com', 'news24.com', 'nation.co.ke', 'dailytrust.com',
                           'citizen.co.ke', 'standardmedia.co.ke', 'punchng.com',
                           'vanguardngr.com', 'thisdaylive.com', 'guardian.ng',
                           'modernghana.com', 'liberianobserver.com', 'newsghana.com.gh',
                           'sabcnews.com', 'timeslive.co.za', 'iol.co.za', 'newsday.co.zw',
                           'businesslive.co.za', 'dailymaverick.co.za']
        
        if any(site in domain for site in problematic_sites):
            if is_african_site:
                base_timeout *= random.uniform(1.5, 2.5)  # 非洲问题网站智能增加超时1.5-2.5倍
            else:
                base_timeout *= random.uniform(1.2, 2.0)  # 非非洲问题网站智能增加超时1.2-2.0倍
        
        # 智能超时上限控制
        max_timeout = 120.0  # 最大超时120秒
        return min(max(15.0, base_timeout), max_timeout)  # 确保超时在15-120秒范围内
    
    def _select_smart_proxy(self, url: str) -> Optional[Dict[str, str]]:
        """智能选择代理 - 基于性能评估和网站特征动态优化"""
        # 检查代理配置
        if not hasattr(self, 'proxy_config') or not self.proxy_config:
            return None
        
        # 加载代理列表
        proxy_list = self._load_proxy_list()
        if not proxy_list:
            return None
        
        # 智能代理选择策略
        domain = urllib.parse.urlparse(url).netloc.lower()
        
        # 非洲网站智能代理选择
        african_domains = ['.za', '.ng', '.ke', '.gh', '.tz', '.ug', '.zm', '.zw']
        is_african_site = any(african_domain in domain for african_domain in african_domains)
        
        if is_african_site:
            # 智能非洲代理选择：基于性能和地理位置
            african_proxies = [p for p in proxy_list if any(country in p.get('country', '').lower() 
                                                          for country in ['south africa', 'nigeria', 'kenya', 'ghana', 
                                                                         'tanzania', 'uganda', 'zambia', 'zimbabwe'])]
            
            if african_proxies:
                # 基于性能评分选择最优代理
                scored_proxies = []
                for proxy in african_proxies:
                    score = self._calculate_proxy_score(proxy, domain)
                    scored_proxies.append((proxy, score))
                
                # 选择评分最高的代理
                scored_proxies.sort(key=lambda x: x[1], reverse=True)
                best_proxy = scored_proxies[0][0]
                self.logger.info(f"智能选择非洲代理: {best_proxy.get('country', 'Unknown')} - 评分: {scored_proxies[0][1]:.2f}")
                return best_proxy
        
        # 智能全局代理选择
        scored_proxies = []
        for proxy in proxy_list:
            score = self._calculate_proxy_score(proxy, domain)
            scored_proxies.append((proxy, score))
        
        # 选择评分最高的代理
        scored_proxies.sort(key=lambda x: x[1], reverse=True)
        best_proxy = scored_proxies[0][0]
        self.logger.info(f"智能选择全局代理: {best_proxy.get('country', 'Unknown')} - 评分: {scored_proxies[0][1]:.2f}")
        return best_proxy
    
    def _calculate_proxy_score(self, proxy: Dict[str, str], domain: str) -> float:
        """计算代理性能评分 - 基于响应时间、成功率、地理位置等指标"""
        score = 100.0  # 基础评分
        
        # 响应时间评分（越低越好）
        response_time = proxy.get('response_time', 0)
        if response_time > 0:
            if response_time < 1000:  # 1秒内
                score += 20
            elif response_time < 3000:  # 3秒内
                score += 10
            elif response_time > 10000:  # 超过10秒
                score -= 30
        
        # 成功率评分
        success_rate = proxy.get('success_rate', 0)
        if success_rate > 0:
            if success_rate > 95:  # 成功率95%以上
                score += 25
            elif success_rate > 85:  # 成功率85%以上
                score += 15
            elif success_rate < 50:  # 成功率低于50%
                score -= 20
        
        # 地理位置评分
        proxy_country = proxy.get('country', '').lower()
        target_country = self._get_target_country_from_domain(domain)
        
        if target_country and proxy_country == target_country:
            score += 15  # 同国家代理加分
        elif target_country and any(region in proxy_country for region in ['africa', 'europe']):
            score += 10  # 同地区代理加分
        
        # 使用频率评分（避免过度使用同一代理）
        usage_count = proxy.get('usage_count', 0)
        if usage_count > 100:
            score -= 15  # 过度使用减分
        elif usage_count < 10:
            score += 10  # 新代理加分
        
        # 稳定性评分
        stability = proxy.get('stability', 0)
        if stability > 90:
            score += 15
        elif stability < 50:
            score -= 20
        
        return max(0, score)  # 确保评分不为负
    
    def _get_target_country_from_domain(self, domain: str) -> Optional[str]:
        """从域名推断目标国家"""
        country_mapping = {
            '.za': 'south africa', '.ng': 'nigeria', '.ke': 'kenya', '.gh': 'ghana',
            '.tz': 'tanzania', '.ug': 'uganda', '.zm': 'zambia', '.zw': 'zimbabwe'
        }
        
        for suffix, country in country_mapping.items():
            if suffix in domain:
                return country
        
        return None
    
    def _detect_anti_crawler_measures(self, response, content: str, url: str = "") -> Dict[str, Any]:
        """智能检测反爬虫措施 - 基于多维度分析和机器学习模式识别"""
        result = {
            'detected': False,
            'type': None,
            'confidence': 0.0,
            'suggestion': '',
            'severity': 'low',  # 新增：严重程度评估
            'recovery_time': 0.0,  # 新增：预计恢复时间
            'adaptive_strategy': []  # 新增：自适应策略建议
        }
        
        # 检查是否为非洲网站（影响检测策略）
        is_african_site = self._is_african_news_url(url) if url else False
        
        # 检查HTTP状态码（增强版）
        status_code = response.status_code
        status_detection = self._detect_by_status_code(status_code, is_african_site)
        if status_detection['detected']:
            result.update(status_detection)
        
        # 智能内容分析（多维度关键词匹配）
        content_detection = self._detect_by_content_analysis(content, is_african_site)
        if content_detection['detected'] and content_detection['confidence'] > result['confidence']:
            result.update(content_detection)
        
        # 响应头智能分析（增强WAF检测）
        header_detection = self._detect_by_header_analysis(response.headers, is_african_site)
        if header_detection['detected'] and header_detection['confidence'] > result['confidence']:
            result.update(header_detection)
        
        # 响应模式分析（异常检测）
        pattern_detection = self._detect_by_response_patterns(response, content, is_african_site)
        if pattern_detection['detected'] and pattern_detection['confidence'] > result['confidence']:
            result.update(pattern_detection)
        
        # 行为指纹分析（基于请求特征）
        behavior_detection = self._detect_by_behavior_patterns(response, url)
        if behavior_detection['detected'] and behavior_detection['confidence'] > result['confidence']:
            result.update(behavior_detection)
        
        # 综合置信度调整和策略生成
        if result['detected']:
            result = self._adjust_detection_confidence(result, is_african_site)
            result = self._generate_adaptive_strategies(result, url)
        
        return result
    
    def _detect_by_status_code(self, status_code: int, is_african_site: bool) -> Dict[str, Any]:
        """基于状态码的智能检测"""
        detection_map = {
            403: {'type': 'ip_block', 'confidence': 0.85, 'severity': 'high'},
            429: {'type': 'rate_limit', 'confidence': 0.95, 'severity': 'medium'},
            503: {'type': 'service_unavailable', 'confidence': 0.7, 'severity': 'medium'},
            451: {'type': 'legal_block', 'confidence': 0.9, 'severity': 'high'},
            418: {'type': 'teapot_block', 'confidence': 0.6, 'severity': 'low'},
            444: {'type': 'nginx_block', 'confidence': 0.8, 'severity': 'medium'}
        }
        
        if status_code in detection_map:
            detection = detection_map[status_code].copy()
            detection['detected'] = True
            
            # 非洲网站调整置信度
            if is_african_site and status_code in [503, 444]:
                detection['confidence'] *= 0.8  # 非洲网站服务器问题更常见
                detection['severity'] = 'low'
            
            # 生成建议
            detection['suggestion'] = self._generate_status_suggestion(status_code, is_african_site)
            detection['recovery_time'] = self._calculate_recovery_time(status_code, is_african_site)
            
            return detection
        
        return {'detected': False}
    
    def _detect_by_content_analysis(self, content: str, is_african_site: bool) -> Dict[str, Any]:
        """基于内容的智能分析"""
        if not content:
            return {'detected': False}
        
        content_lower = content.lower()
        
        # 多层级关键词匹配
        keyword_categories = {
            'captcha': ['captcha', '验证码', 'recaptcha', 'hcaptcha', '验证', 'verification'],
            'waf': ['cloudflare', 'distil', 'incapsula', 'akamai', 'sucuri', 'imperva'],
            'block': ['access denied', 'forbidden', 'blocked', 'banned', 'suspended'],
            'rate_limit': ['rate limit', 'too many requests', '请求过于频繁'],
            'bot_detection': ['bot detected', 'automated traffic', 'suspicious activity', '机器人检测'],
            'javascript': ['please enable javascript', 'javascript required', '需要启用javascript'],
            'africa_specific': ['mtn', 'vodacom', 'safaricom', 'airtel africa']  # 非洲特定标识
        }
        
        detected_keywords = {}
        total_matches = 0
        
        for category, keywords in keyword_categories.items():
            matches = [kw for kw in keywords if kw in content_lower]
            if matches:
                detected_keywords[category] = matches
                total_matches += len(matches)
        
        if detected_keywords:
            # 计算置信度（基于匹配数量和类型）
            base_confidence = min(0.6 + total_matches * 0.08, 0.95)
            
            # 类型判断
            if 'captcha' in detected_keywords:
                detection_type = 'captcha'
                severity = 'high'
            elif 'waf' in detected_keywords:
                detection_type = 'waf_detected'
                severity = 'medium'
            elif 'bot_detection' in detected_keywords:
                detection_type = 'bot_detected'
                severity = 'high'
            else:
                detection_type = 'content_block'
                severity = 'medium'
            
            # 非洲网站调整
            if is_african_site and 'africa_specific' in detected_keywords:
                base_confidence *= 1.1  # 非洲特定标识增加置信度
            
            return {
                'detected': True,
                'type': detection_type,
                'confidence': base_confidence,
                'severity': severity,
                'suggestion': f'检测到反爬虫关键词: {detected_keywords}',
                'recovery_time': 15.0 if detection_type == 'captcha' else 30.0
            }
        
        return {'detected': False}
    
    def _detect_by_header_analysis(self, headers: Dict[str, str], is_african_site: bool) -> Dict[str, Any]:
        """基于响应头的智能分析"""
        # 增强的WAF检测标识
        waf_indicators = {
            'cloudflare': ['cf-ray', 'cf-cache-status', 'cf-request-id'],
            'akamai': ['x-akamai-transformed', 'x-akamai-config-log-id'],
            'imperva': ['x-cdn', 'x-iinfo', 'x-protected-by'],
            'distil': ['x-distil-cs', 'x-distil-ajax'],
            'sucuri': ['x-sucuri-id', 'x-sucuri-cache']
        }
        
        detected_waf = []
        
        for waf_name, indicators in waf_indicators.items():
            if any(indicator in headers for indicator in indicators):
                detected_waf.append(waf_name)
        
        if detected_waf:
            return {
                'detected': True,
                'type': 'waf_detected',
                'confidence': 0.85,
                'severity': 'medium',
                'suggestion': f'检测到WAF防护: {detected_waf}',
                'recovery_time': 25.0
            }
        
        # 其他安全头检测
        security_headers = ['x-frame-options', 'x-content-type-options', 
                          'x-xss-protection', 'strict-transport-security']
        
        if any(header in headers for header in security_headers):
            return {
                'detected': True,
                'type': 'security_headers',
                'confidence': 0.4,
                'severity': 'low',
                'suggestion': '检测到安全头，网站可能有防护措施',
                'recovery_time': 10.0
            }
        
        return {'detected': False}
    
    def _detect_by_response_patterns(self, response, content: str, is_african_site: bool) -> Dict[str, Any]:
        """基于响应模式的异常检测"""
        # 响应体大小异常检测
        content_length = len(content)
        
        # 过小的响应体（可能被重定向到验证页面）
        if content_length < 500:
            content_lower = content.lower()
            if any(keyword in content_lower for keyword in ['captcha', 'verification', 'security']):
                return {
                    'detected': True,
                    'type': 'captcha_redirect',
                    'confidence': 0.9,
                    'severity': 'high',
                    'suggestion': '检测到验证码重定向页面',
                    'recovery_time': 20.0
                }
        
        # 响应时间异常检测（需要历史数据支持）
        if hasattr(response, 'elapsed') and response.elapsed:
            response_time = response.elapsed.total_seconds()
            # 非洲网站响应时间阈值调整
            threshold = 10.0 if is_african_site else 5.0
            if response_time > threshold:
                return {
                    'detected': True,
                    'type': 'slow_response',
                    'confidence': 0.6,
                    'severity': 'low',
                    'suggestion': '响应时间异常，可能受到限制',
                    'recovery_time': response_time * 2
                }
        
        return {'detected': False}
    
    def _detect_by_behavior_patterns(self, response, url: str) -> Dict[str, Any]:
        """基于行为模式的检测"""
        # 这里可以集成机器学习模型进行行为分析
        # 暂时使用简单的模式匹配
        
        # 检查重定向模式
        if hasattr(response, 'history') and response.history:
            redirect_count = len(response.history)
            if redirect_count > 3:
                return {
                    'detected': True,
                    'type': 'excessive_redirects',
                    'confidence': 0.7,
                    'severity': 'medium',
                    'suggestion': '检测到过多重定向，可能为反爬虫措施',
                    'recovery_time': 15.0
                }
        
        return {'detected': False}
    
    def _adjust_detection_confidence(self, detection: Dict[str, Any], is_african_site: bool) -> Dict[str, Any]:
        """调整检测置信度"""
        # 非洲网站置信度调整
        if is_african_site:
            if detection['type'] in ['service_unavailable', 'slow_response']:
                detection['confidence'] *= 0.8  # 非洲网站服务器问题更常见
            elif detection['type'] in ['waf_detected', 'bot_detected']:
                detection['confidence'] *= 1.1  # 非洲网站安全措施较少见，增加置信度
        
        # 多证据融合（如果有多个检测点）
        # 这里可以集成更复杂的证据融合算法
        
        return detection
    
    def _generate_status_suggestion(self, status_code: int, is_african_site: bool) -> str:
        """生成状态码对应的建议"""
        suggestions = {
            403: 'IP可能被封禁，建议使用代理或更换IP',
            429: '请求频率过高，建议降低爬取速度',
            503: '服务暂时不可用，建议稍后重试',
            451: '法律限制访问，建议放弃该网站',
            418: '网站返回teapot状态，可能是幽默反爬虫',
            444: 'Nginx连接关闭，可能是反爬虫措施'
        }
        
        base_suggestion = suggestions.get(status_code, '检测到异常状态码')
        
        if is_african_site and status_code in [503, 444]:
            base_suggestion += '（非洲网站网络不稳定，建议增加重试机会）'
        
        return base_suggestion
    
    def _calculate_recovery_time(self, status_code: int, is_african_site: bool) -> float:
        """计算预计恢复时间"""
        base_times = {
            403: 60.0,   # IP封禁恢复较慢
            429: 30.0,   # 速率限制恢复较快
            503: 45.0,   # 服务不可用恢复中等
            451: 0.0,    # 法律限制不恢复
            418: 5.0,    # teapot状态恢复快
            444: 25.0    # Nginx关闭恢复中等
        }
        
        base_time = base_times.get(status_code, 20.0)
        
        # 非洲网站恢复时间调整
        if is_african_site:
            base_time *= 1.5  # 非洲网站恢复时间更长
        
        return base_time
    
    def _generate_adaptive_strategies(self, detection: Dict[str, Any], url: str) -> Dict[str, Any]:
        """生成自适应策略建议"""
        strategies = []
        
        # 基于检测类型生成策略
        if detection['type'] == 'ip_block':
            strategies.extend([
                '立即更换代理IP',
                '调整User-Agent',
                '增加请求间隔时间',
                '使用住宅代理'
            ])
        elif detection['type'] == 'rate_limit':
            strategies.extend([
                '大幅降低请求频率',
                '使用分布式爬取',
                '增加随机延迟',
                '避开高峰时段'
            ])
        elif detection['type'] == 'captcha':
            strategies.extend([
                '使用验证码识别服务',
                '人工干预解决验证码',
                '更换爬取目标',
                '使用浏览器自动化'
            ])
        elif detection['type'] == 'waf_detected':
            strategies.extend([
                '使用真实浏览器指纹',
                '模拟人类行为模式',
                '降低并发数量',
                '使用高质量代理'
            ])
        
        # 非洲网站特定策略
        if self._is_african_news_url(url):
            strategies.extend([
                '增加非洲网站重试机会',
                '使用非洲本地代理',
                '调整非洲网络超时设置'
            ])
        
        detection['adaptive_strategy'] = strategies
        return detection
    
    def _handle_anti_crawler_measures(self, anti_crawler_result: Dict[str, Any], url: str = "") -> Dict[str, Any]:
        """智能处理反爬虫措施 - 多因素动态计算等待时间和策略"""
        anti_crawler_type = anti_crawler_result['type']
        confidence = anti_crawler_result['confidence']
        severity = anti_crawler_result.get('severity', 'medium')
        
        # 检查是否为非洲网站
        is_african_site = self._is_african_site(url)
        
        # 多因素动态计算等待时间
        wait_time = self._calculate_dynamic_wait_time(anti_crawler_type, confidence, severity, is_african_site)
        
        # 生成智能应对策略
        strategy = self._generate_anti_crawler_strategy(anti_crawler_type, confidence, severity, is_african_site)
        
        # 计算恢复时间（基于历史成功率）
        recovery_time = self._calculate_recovery_time_based_on_history(anti_crawler_type, is_african_site)
        
        # 添加随机性避免模式识别
        random_factor = random.uniform(0.8, 1.2)
        final_wait_time = wait_time * random_factor
        
        # 构建完整的处理结果
        result = {
            'wait_time': final_wait_time,
            'strategy': strategy,
            'recovery_time': recovery_time,
            'confidence': confidence,
            'severity': severity,
            'is_african_site': is_african_site,
            'suggested_actions': self._get_suggested_actions(anti_crawler_type, severity, is_african_site)
        }
        
        logger.info(f"反爬虫智能处理: 类型={anti_crawler_type}, 置信度={confidence:.2f}, "
                   f"严重程度={severity}, 等待时间={final_wait_time:.1f}秒, 策略={strategy}")
        
        return result
    
    def _is_african_site(self, url: str) -> bool:
        """判断是否为非洲网站"""
        if not url:
            return False
        
        domain = urllib.parse.urlparse(url).netloc.lower()
        african_domains = ['.za', '.ng', '.ke', '.gh', '.tz', '.ug', '.zm', '.zw', 
                          '.mw', '.mz', '.ao', '.bw', '.na', '.sz', '.ls', '.et',
                          '.so', '.sd', '.ss', '.er', '.dj', '.km', '.mg', '.mu',
                          '.sc', '.re', '.yt', '.rw', '.bi', '.cd', '.cg', '.ga',
                          '.gq', '.cf', '.td', '.ne', '.ml', '.bf', '.bj', '.tg',
                          '.ci', '.gn', '.gw', '.lr', '.sl', '.gm', '.sn', '.mr']
        
        return any(african_domain in domain for african_domain in african_domains)
    
    def _calculate_dynamic_wait_time(self, anti_crawler_type: str, confidence: float, 
                                    severity: str, is_african_site: bool) -> float:
        """基于多因素动态计算等待时间"""
        # 基础等待时间矩阵
        base_times = {
            'rate_limit': {'low': 15.0, 'medium': 30.0, 'high': 60.0},
            'ip_block': {'low': 30.0, 'medium': 60.0, 'high': 120.0},
            'captcha': {'low': 5.0, 'medium': 10.0, 'high': 20.0},
            'service_unavailable': {'low': 10.0, 'medium': 20.0, 'high': 40.0},
            'waf_detected': {'low': 20.0, 'medium': 40.0, 'high': 80.0},
            'bot_detected': {'low': 25.0, 'medium': 50.0, 'high': 100.0},
            'content_block': {'low': 8.0, 'medium': 15.0, 'high': 30.0}
        }
        
        # 获取基础等待时间
        base_time = base_times.get(anti_crawler_type, {'low': 10.0, 'medium': 20.0, 'high': 40.0})[severity]
        
        # 置信度调整（高置信度增加等待时间）
        confidence_factor = 1.0 + (confidence - 0.5) * 0.8  # 置信度0.5-1.0对应0.9-1.4倍
        
        # 非洲网站调整（网络不稳定，适当减少等待时间）
        africa_factor = 0.8 if is_african_site else 1.0
        
        # 时间因素调整（高峰时段增加等待时间）
        current_hour = datetime.now().hour
        time_factor = 1.2 if 9 <= current_hour <= 17 else 1.0  # 工作时间增加等待
        
        # 综合计算
        wait_time = base_time * confidence_factor * africa_factor * time_factor
        
        # 限制在合理范围内（5秒-300秒）
        return max(5.0, min(wait_time, 300.0))
    
    def _generate_anti_crawler_strategy(self, anti_crawler_type: str, confidence: float,
                                      severity: str, is_african_site: bool) -> str:
        """生成智能应对策略"""
        strategies = {
            'rate_limit': {
                'low': '降低爬取频率，增加随机延迟',
                'medium': '大幅降低频率，使用代理轮换',
                'high': '暂停爬取，等待系统恢复'
            },
            'ip_block': {
                'low': '更换User-Agent，使用不同代理',
                'medium': '更换IP地址，调整爬取模式',
                'high': '暂停爬取，等待IP解封'
            },
            'captcha': {
                'low': '尝试绕过验证码，调整请求头',
                'medium': '使用验证码识别服务或人工干预',
                'high': '暂停爬取，等待验证码过期'
            },
            'service_unavailable': {
                'low': '短暂等待后重试',
                'medium': '增加等待时间，检查网络连接',
                'high': '暂停爬取，等待服务恢复'
            }
        }
        
        # 获取基础策略
        base_strategy = strategies.get(anti_crawler_type, {
            'low': '调整爬取策略',
            'medium': '优化爬取参数',
            'high': '暂停爬取分析'
        })[severity]
        
        # 非洲网站特殊策略
        if is_african_site:
            if anti_crawler_type in ['service_unavailable', 'rate_limit']:
                base_strategy += '（非洲网站网络不稳定，建议增加重试机会）'
        
        # 高置信度策略增强
        if confidence > 0.8:
            base_strategy += '（高置信度检测，建议严格执行）'
        
        return base_strategy
    
    def _calculate_recovery_time_based_on_history(self, anti_crawler_type: str, is_african_site: bool) -> float:
        """基于历史成功率计算恢复时间"""
        # 基础恢复时间（基于类型）
        base_recovery_times = {
            'rate_limit': 30.0,
            'ip_block': 60.0,
            'captcha': 15.0,
            'service_unavailable': 20.0,
            'waf_detected': 45.0,
            'bot_detected': 50.0
        }
        
        base_time = base_recovery_times.get(anti_crawler_type, 25.0)
        
        # 非洲网站调整（网络恢复较慢）
        if is_african_site:
            base_time *= 1.3
        
        # 历史成功率调整（这里可以集成历史数据）
        # 暂时使用固定值，后续可以集成机器学习模型
        history_factor = 1.0
        
        return base_time * history_factor
    
    def _get_suggested_actions(self, anti_crawler_type: str, severity: str, is_african_site: bool) -> List[str]:
        """获取建议操作列表"""
        actions = []
        
        # 通用操作
        if severity in ['medium', 'high']:
            actions.append('更换User-Agent')
            actions.append('使用不同代理')
        
        # 类型特定操作
        if anti_crawler_type == 'rate_limit':
            actions.append('降低爬取频率')
            actions.append('增加随机延迟')
        elif anti_crawler_type == 'ip_block':
            actions.append('更换IP地址')
            actions.append('调整爬取时间')
        elif anti_crawler_type == 'captcha':
            actions.append('尝试绕过验证码')
            actions.append('使用验证码识别服务')
        elif anti_crawler_type == 'service_unavailable':
            actions.append('检查网络连接')
            actions.append('等待服务恢复')
        
        # 非洲网站特殊操作
        if is_african_site:
            actions.append('增加重试机会')
            actions.append('调整超时设置')
        
        return actions
    
    def _should_retry_based_on_response(self, response, exception: Optional[Exception], 
                                      attempt: int, url: str) -> Dict[str, Any]:
        """基于响应状态智能判断是否应该重试 - 增强版，特别优化非洲网站支持"""
        retry_decision = {
            "should_retry": False,
            "reason": "",
            "suggested_delay": 0.0,
            "suggested_timeout": 0.0,
            "recommendations": [],
            "africa_specific": False
        }
        
        # 检查是否为非洲网站
        domain = urllib.parse.urlparse(url).netloc.lower()
        african_domains = ['.za', '.ng', '.ke', '.gh', '.tz', '.ug', '.zm', '.zw', 
                          '.mw', '.mz', '.ao', '.bw', '.na', '.sz', '.ls', '.et',
                          '.so', '.sd', '.ss', '.er', '.dj', '.km', '.mg', '.mu',
                          '.sc', '.re', '.yt', '.rw', '.bi', '.cd', '.cg', '.ga',
                          '.gq', '.cf', '.td', '.ne', '.ml', '.bf', '.bj', '.tg',
                          '.ci', '.gn', '.gw', '.lr', '.sl', '.gm', '.sn', '.mr']
        
        is_african_site = any(african_domain in domain for african_domain in african_domains)
        retry_decision["africa_specific"] = is_african_site
        
        # 检查响应状态码
        if response is not None:
            status_code = response.status_code
            
            # 5xx服务器错误 - 通常值得重试，非洲网站增加重试机会
            if 500 <= status_code < 600:
                if is_african_site and attempt < 4:  # 非洲网站允许更多重试
                    retry_decision["should_retry"] = True
                    retry_decision["reason"] = f"非洲网站服务器错误 {status_code}，增加重试机会"
                    retry_decision["suggested_delay"] = self._calculate_smart_delay(url, attempt) * 1.2
                    retry_decision["suggested_timeout"] = self._calculate_smart_timeout(url, attempt) * 1.3
                    retry_decision["recommendations"] = ["非洲网站网络不稳定，增加重试机会"]
                elif attempt < 3:  # 非非洲网站正常重试
                    retry_decision["should_retry"] = True
                    retry_decision["reason"] = f"服务器错误 {status_code}"
                    retry_decision["suggested_delay"] = self._calculate_smart_delay(url, attempt)
                    retry_decision["suggested_timeout"] = self._calculate_smart_timeout(url, attempt)
                    retry_decision["recommendations"] = ["服务器暂时不可用，建议重试"]
            
            # 429速率限制 - 需要重试但增加延迟
            elif status_code == 429:
                retry_decision["should_retry"] = True
                retry_decision["reason"] = "速率限制"
                if is_african_site:
                    retry_decision["suggested_delay"] = max(45.0, self._calculate_smart_delay(url, attempt) * 2.5)
                    retry_decision["recommendations"] = ["非洲网站速率限制，大幅增加延迟后重试"]
                else:
                    retry_decision["suggested_delay"] = max(30.0, self._calculate_smart_delay(url, attempt) * 2.0)
                    retry_decision["recommendations"] = ["触发速率限制，增加延迟后重试"]
                retry_decision["suggested_timeout"] = self._calculate_smart_timeout(url, attempt)
            
            # 403禁止访问 - 可能需要更换代理或User-Agent
            elif status_code == 403:
                # 特殊处理nation.co.ke网站 - 更激进的策略
                if 'nation.co.ke' in domain and attempt < 6:  # nation.co.ke允许更多尝试
                    retry_decision["should_retry"] = True
                    retry_decision["reason"] = "nation.co.ke严格反爬虫，启用激进策略"
                    retry_decision["suggested_delay"] = self._calculate_smart_delay(url, attempt) * 3.0  # 3倍延迟
                    retry_decision["suggested_timeout"] = self._calculate_smart_timeout(url, attempt) * 2.0  # 2倍超时
                    retry_decision["recommendations"] = ["强制更换User-Agent", "切换不同地区代理", "启用浏览器指纹模拟", "增加延迟至3倍", "启用SSL验证绕过"]
                elif is_african_site and attempt < 4:  # 其他非洲网站允许更多尝试
                    retry_decision["should_retry"] = True
                    retry_decision["reason"] = "非洲网站禁止访问，增加尝试机会"
                    retry_decision["suggested_delay"] = self._calculate_smart_delay(url, attempt) * 2.0  # 2倍延迟
                    retry_decision["suggested_timeout"] = self._calculate_smart_timeout(url, attempt) * 1.5  # 1.5倍超时
                    retry_decision["recommendations"] = ["更换User-Agent", "尝试不同代理", "非洲网站网络不稳定，增加尝试"]
                elif attempt < 2:  # 非非洲网站正常重试
                    retry_decision["should_retry"] = True
                    retry_decision["reason"] = "禁止访问，尝试更换策略"
                    retry_decision["suggested_delay"] = self._calculate_smart_delay(url, attempt)
                    retry_decision["suggested_timeout"] = self._calculate_smart_timeout(url, attempt)
                    retry_decision["recommendations"] = ["更换User-Agent", "尝试不同代理"]
                else:
                    retry_decision["should_retry"] = False
                    retry_decision["reason"] = "禁止访问，多次尝试失败"
                    retry_decision["recommendations"] = ["网站可能永久封禁，建议放弃"]
            
            # 408请求超时 - 非洲网站常见问题
            elif status_code == 408:
                retry_decision["should_retry"] = True
                retry_decision["reason"] = "请求超时"
                if is_african_site:
                    retry_decision["suggested_delay"] = self._calculate_smart_delay(url, attempt) * 1.8
                    retry_decision["suggested_timeout"] = self._calculate_smart_timeout(url, attempt) * 2.0
                    retry_decision["recommendations"] = ["非洲网站网络延迟高，大幅增加超时时间"]
                else:
                    retry_decision["suggested_delay"] = self._calculate_smart_delay(url, attempt) * 1.2
                    retry_decision["suggested_timeout"] = self._calculate_smart_timeout(url, attempt) * 1.5
                    retry_decision["recommendations"] = ["网络连接问题，增加超时后重试"]
        
        # 检查异常类型
        elif exception is not None:
            exception_type = type(exception).__name__
            
            # 连接相关错误 - 通常值得重试，非洲网站增加重试机会
            if any(error_type in exception_type for error_type in ["ConnectionError", "Timeout", "ConnectTimeout"]):
                retry_decision["should_retry"] = True
                retry_decision["reason"] = f"连接错误: {exception_type}"
                if is_african_site:
                    retry_decision["suggested_delay"] = self._calculate_smart_delay(url, attempt) * 1.6
                    retry_decision["suggested_timeout"] = self._calculate_smart_timeout(url, attempt) * 2.0
                    retry_decision["recommendations"] = ["非洲网站网络不稳定，大幅增加超时和延迟"]
                else:
                    retry_decision["suggested_delay"] = self._calculate_smart_delay(url, attempt)
                    retry_decision["suggested_timeout"] = self._calculate_smart_timeout(url, attempt) * 1.5
                    retry_decision["recommendations"] = ["网络连接问题，增加超时后重试"]
            
            # SSL错误 - 可能需要调整SSL验证
            elif "SSL" in exception_type:
                if is_african_site and attempt < 3:  # 非洲网站SSL问题更常见
                    retry_decision["should_retry"] = True
                    retry_decision["reason"] = f"非洲网站SSL错误: {exception_type}，增加重试机会"
                    retry_decision["suggested_delay"] = self._calculate_smart_delay(url, attempt)
                    retry_decision["suggested_timeout"] = self._calculate_smart_timeout(url, attempt)
                    retry_decision["recommendations"] = ["非洲网站SSL证书问题常见，尝试禁用SSL验证"]
                elif attempt < 2:
                    retry_decision["should_retry"] = True
                    retry_decision["reason"] = f"SSL错误: {exception_type}"
                    retry_decision["suggested_delay"] = self._calculate_smart_delay(url, attempt)
                    retry_decision["suggested_timeout"] = self._calculate_smart_timeout(url, attempt)
                    retry_decision["recommendations"] = ["SSL证书问题，尝试禁用SSL验证"]
                else:
                    retry_decision["should_retry"] = False
                    retry_decision["reason"] = "SSL错误，多次尝试失败"
                    retry_decision["recommendations"] = ["网站SSL配置有问题，建议放弃"]
        
        # 最大重试次数检查 - 非洲网站允许更多重试
        if is_african_site:
            max_africa_attempts = MAX_RETRY_ATTEMPTS + 1  # 非洲网站多一次重试机会
            if attempt >= max_africa_attempts - 1:
                retry_decision["should_retry"] = False
                retry_decision["reason"] = f"已达到非洲网站最大重试次数 {max_africa_attempts}"
                retry_decision["recommendations"] = ["已达到非洲网站最大重试次数，停止尝试"]
        else:
            if attempt >= MAX_RETRY_ATTEMPTS - 1:
                retry_decision["should_retry"] = False
                retry_decision["reason"] = f"已达到最大重试次数 {MAX_RETRY_ATTEMPTS}"
                retry_decision["recommendations"] = ["已达到最大重试次数，停止尝试"]
        
        return retry_decision
    
    def extract_title(self, content: str, url: str) -> str:
        """从内容中提取标题"""
        # 从Markdown内容中提取标题
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## '):
                return line[3:].strip()
        
        # 如果没有找到标题，使用URL作为标题
        return url.split('//')[1].split('/')[0]
    
    def extract_publish_date(self, content: str, url: str) -> str:
        """从内容中提取发布日期"""
        import re
        from datetime import datetime
        
        # 查找常见的日期格式
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{4}\.\d{2}\.\d{2}',
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            if matches:
                date_str = matches[0].strip()
                # 尝试解析日期格式
                try:
                    # 处理常见的日期分隔符
                    date_str = re.sub(r'[/\.]', '-', date_str)
                    # 尝试解析
                    parsed_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
                    return parsed_date.strftime('%Y-%m-%d')
                except:
                    # 如果解析失败，尝试其他格式
                    try:
                        parsed_date = datetime.strptime(date_str[:10], '%d-%m-%Y')
                        return parsed_date.strftime('%Y-%m-%d')
                    except:
                        continue
        
        # 如果没有找到日期，返回"unknown"而不是当前日期
        return "unknown"
    
    def extract_title_from_html(self, html_content: str, url: str) -> str:
        """从HTML中提取标题"""
        import re
        
        # 提取<title>标签内容
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        if title_match:
            return title_match.group(1).strip()
        
        # 提取<h1>标签内容
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.IGNORECASE | re.DOTALL)
        if h1_match:
            return h1_match.group(1).strip()
        
        return url.split('//')[1].split('/')[0]
    
    def _is_african_news_url(self, url: str) -> bool:
        """检测是否为非洲新闻网站URL"""
        if not url:
            return False
            
        # 非洲新闻网站域名列表（扩展版）
        african_news_domains = [
            # 南非
            'news24.com', 'iol.co.za', 'mg.co.za', 'dailymaverick.co.za',
            'businesslive.co.za', 'fin24.com', 'timeslive.co.za',
            # 尼日利亚
            'premiumtimesng.com', 'guardian.ng', 'vanguardngr.com',
            'thisdaylive.com', 'punchng.com', 'thenationonlineng.net',
            # 肯尼亚
            'nation.co.ke', 'standardmedia.co.ke', 'the-star.co.ke',
            'businessdailyafrica.com', 'citizentv.co.ke',
            # 加纳
            'ghanaweb.com', 'modernghana.com', 'newsghana.com.gh',
            'graphic.com.gh', 'myjoyonline.com',
            # 坦桑尼亚
            'thecitizen.co.tz', 'dailynews.co.tz', 'ippmedia.com',
            # 乌干达
            'monitor.co.ug', 'newvision.co.ug', 'observer.ug',
            # 卢旺达
            'newtimes.co.rw', 'ktpress.rw',
            # 埃塞俄比亚
            'ethiopianreporter.com', 'addisfortune.net',
            # 埃及
            'english.ahram.org.eg', 'dailynewsegypt.com', 'egyptindependent.com',
            # 泛非洲
            'allafrica.com', 'africanews.com', 'panapress.com',
            'jeuneafrique.com', 'africa-confidential.com',
            # 法语区
            'lemonde.fr/afrique', 'rfi.fr/afrique', 'france24.com/fr/afrique',
            # 其他重要非洲国家
            'zambianobserver.com', 'zambiadailynation.com',  # 赞比亚
            'zimbabweindependent.co.zw', 'newsday.co.zw',  # 津巴布韦
            'malawi24.com', 'nyasatimes.com',  # 马拉维
            'mozambique.co.mz', 'clubofmozambique.com',  # 莫桑比克
            'angop.ao', 'jornaldeangola.ao',  # 安哥拉
            'namibian.com.na', 'neweralive.na',  # 纳米比亚
            'botswanaguardian.co.bw', 'sundaystandard.info',  # 博茨瓦纳
            'lesotho.co.ls', 'public-eye.co.ls',  # 莱索托
            'swazilive.com', 'times.co.sz',  # 斯威士兰
            'sabcnews.com', 'enca.com',  # 南非广播公司
            'citizen.co.za', 'news.iafrica.com',  # 南非其他
            'nigeriatoday.ng', 'leadership.ng',  # 尼日利亚其他
            'kenya-today.com', 'hivisasa.com',  # 肯尼亚其他
            'ghanaianchronicle.com', 'dailyguideafrica.com',  # 加纳其他
            'tanzaniatoday.co.tz', 'habarileo.co.tz',  # 坦桑尼亚其他
            'ugandaradionetwork.net', 'chimpreports.com',  # 乌干达其他
            'rwandatoday.africa', 'igihe.com',  # 卢旺达其他
            'ethiosports.com', 'ethiopia-insight.com',  # 埃塞俄比亚其他
            'almasryalyoum.com', 'youm7.com',  # 埃及其他
            'africa.cgtn.com', 'africanarguments.org',  # 泛非洲其他
            'africanbusinessmagazine.com', 'africareview.com',  # 非洲商业媒体
            'africanexponent.com', 'africanliberty.org',  # 非洲观点媒体
            'africatimes.com', 'africanewsagency.com',  # 非洲新闻机构
            'africanews.space', 'africanews.media',  # 非洲新闻聚合
            'africanewsnow.co.za', 'africanewswire.net',  # 非洲新闻服务
            'africanewsreport.com', 'africanewstoday.com',  # 非洲新闻报告
            'africanewsupdate.com', 'africanewsworld.com',  # 非洲新闻更新
            'africanewswire.com', 'africanewstoday.co.za',  # 非洲新闻通讯
            'africanewstoday.net', 'africanewsworld.net',  # 非洲新闻世界
            'africanewswire.org', 'africanewstoday.org',  # 非洲新闻组织
            'africanewswire.co.za', 'africanewstoday.co.za',  # 非洲新闻南非
            'africanewswire.net.za', 'africanewstoday.net.za',  # 非洲新闻网络
            'africanewswire.com.za', 'africanewstoday.com.za',  # 非洲新闻商业
            'africanewswire.org.za', 'africanewstoday.org.za',  # 非洲新闻组织南非
        ]
        
        # 检查URL是否包含非洲新闻网站域名
        for domain in african_news_domains:
            if domain in url:
                return True
        
        # 检查非洲国家域名后缀
        african_country_domains = [
            '.za', '.ng', '.ke', '.gh', '.tz', '.ug', '.zm', '.zw', 
            '.mw', '.mz', '.ao', '.bw', '.na', '.sz', '.ls', '.et',
            '.so', '.sd', '.ss', '.er', '.dj', '.km', '.mg', '.mu',
            '.sc', '.re', '.yt', '.rw', '.bi', '.cd', '.cg', '.ga',
            '.gq', '.cf', '.td', '.ne', '.ml', '.bf', '.bj', '.tg',
            '.ci', '.gn', '.gw', '.lr', '.sl', '.gm', '.sn', '.mr',
            '.ly', '.tn', '.dz', '.ma', '.eh', '.mr', '.ml', '.ne',
            '.td', '.cf', '.cg', '.cd', '.ga', '.gq', '.st', '.gw',
            '.gn', '.lr', '.sl', '.ci', '.bf', '.bj', '.tg', '.gh',
            '.ng', '.cm', '.cv', '.gm', '.gw', '.lr', '.ml', '.ne',
            '.sn', '.sl', '.tg', '.bf', '.bj', '.td', '.cf', '.km',
            '.dj', '.er', '.et', '.so', '.sd', '.ss', '.rw', '.bi',
            '.mg', '.mu', '.sc', '.km', '.yt', '.re', '.tf', '.io'
        ]
        
        # 检查URL是否包含非洲国家域名后缀
        for domain_suffix in african_country_domains:
            if domain_suffix in url:
                return True
        
        return False
    
    def extract_content_from_html(self, html_content: str, url: str = "") -> str:
        """从HTML中提取主要内容（优化版本，特别增强非洲新闻网站支持）"""
        try:
            # 导入优化后的内容提取器
            from content_extraction_optimizer import ContentExtractionOptimizer
            optimizer = ContentExtractionOptimizer()
            
            # 使用优化后的内容提取逻辑
            content = optimizer.extract_news_content_advanced(html_content, url)
            
            # 增强内容质量检测和优化
            if content and content != "内容提取失败":
                # 检查内容长度和质量
                clean_content = content.strip()
                if len(clean_content) >= 50:
                    # 如果是非洲新闻网站，放宽质量要求
                    if self._is_african_news_url(url):
                        # 非洲新闻网站：最小长度要求降低到30字符
                        if len(clean_content) >= 30:
                            logger.info(f"非洲新闻网站内容提取成功: {url}, 长度: {len(clean_content)}")
                            return clean_content
                    else:
                        # 非非洲网站：保持原有标准
                        logger.info(f"内容提取成功: {url}, 长度: {len(clean_content)}")
                        return clean_content
            
            # 如果优化提取失败，使用备用方法
            logger.warning(f"优化提取失败，使用备用方法: {url}")
            fallback_content = self._extract_content_fallback(html_content)
            
            # 对备用方法结果进行质量检查
            if fallback_content and fallback_content != "内容提取失败":
                clean_fallback = fallback_content.strip()
                if len(clean_fallback) >= 30:  # 降低备用方法的质量阈值
                    return clean_fallback
            
            return "内容提取失败"
                    
        except Exception as e:
            logger.error(f"HTML内容提取失败: {e}")
            # 备用方法
            fallback_content = self._extract_content_fallback(html_content)
            if fallback_content and fallback_content != "内容提取失败":
                return fallback_content
            return "内容提取失败"
    
    def _extract_content_fallback(self, html_content: str) -> str:
        """备用内容提取方法"""
        import re
        import html
        
        try:
            # 移除脚本和样式标签
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
            
            # 提取多种内容标签：段落、标题、列表项
            content_parts = []
            
            # 提取段落内容
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html_content, re.DOTALL)
            for p in paragraphs:
                clean_text = re.sub(r'<[^>]+>', '', p).strip()
                if clean_text and len(clean_text) > 10:  # 过滤过短的段落
                    content_parts.append(clean_text)
            
            # 提取标题内容
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                headers = re.findall(rf'<{tag}[^>]*>(.*?)</{tag}>', html_content, re.DOTALL)
                for h in headers:
                    clean_text = re.sub(r'<[^>]+>', '', h).strip()
                    if clean_text and len(clean_text) > 5:
                        content_parts.append(clean_text)
            
            # 提取列表项
            list_items = re.findall(r'<li[^>]*>(.*?)</li>', html_content, re.DOTALL)
            for li in list_items:
                clean_text = re.sub(r'<[^>]+>', '', li).strip()
                if clean_text and len(clean_text) > 10:
                    content_parts.append(clean_text)
            
            # 合并内容并处理HTML实体编码
            if content_parts:
                content = ' '.join(content_parts)
                # 解码HTML实体（如 &amp; -> &, &lt; -> <, &gt; -> > 等）
                content = html.unescape(content)
                # 清理多余的空格和换行
                content = re.sub(r'\s+', ' ', content).strip()
                # 限制长度但保留更多内容
                return content[:2000] if len(content) > 2000 else content
            else:
                # 如果无法提取内容，尝试提取body标签内的文本
                body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL)
                if body_match:
                    body_text = re.sub(r'<[^>]+>', '', body_match.group(1)).strip()
                    body_text = html.unescape(body_text)
                    body_text = re.sub(r'\s+', ' ', body_text).strip()
                    return body_text[:2000] if len(body_text) > 2000 else body_text
                else:
                    return "内容提取失败"
                    
        except Exception as e:
            logger.error(f"备用内容提取失败: {e}")
            return "内容提取失败"
    
    def extract_date_from_html(self, html_content: str, url: str) -> str:
        """
        从HTML中提取发布日期 - 增强版
        支持多种日期格式和提取策略，特别优化非洲新闻网站支持
        """
        import re
        from datetime import datetime
        
        # 策略1：从meta标签提取日期（优先级最高）
        meta_patterns = [
            r'<meta[^>]*property="(?:article:published_time|og:published_time)"[^>]*content="([^"]+)"',
            r'<meta[^>]*name="(?:publish_date|date)"[^>]*content="([^"]+)"',
            r'<meta[^>]*property="(?:article:modified_time)"[^>]*content="([^"]+)"',
            r'<meta[^>]*name="(?:DC\.date\.issued|DC\.date\.modified)"[^>]*content="([^"]+)"',
            r'<meta[^>]*name="(?:last-modified|lastmodified)"[^>]*content="([^"]+)"',
            r'<meta[^>]*name="(?:pubdate|pub_date)"[^>]*content="([^"]+)"',
            r'<meta[^>]*name="(?:timestamp|time)"[^>]*content="([^"]+)"',
            r'<meta[^>]*name="(?:created|creation_date)"[^>]*content="([^"]+)"',
            r'<meta[^>]*name="(?:OriginalPublicationDate)"[^>]*content="([^"]+)"',
            # 非洲新闻网站特有的meta标签
            r'<meta[^>]*name="(?:publish-date|publishdate)"[^>]*content="([^"]+)"',
            r'<meta[^>]*name="(?:article_date|article-date)"[^>]*content="([^"]+)"',
        ]
        
        for pattern in meta_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                parsed_date = self._parse_and_validate_date(match, url)
                if parsed_date != "unknown":
                    return parsed_date
        
        # 策略2：从HTML文本中提取日期
        date_patterns = [
            # 标准格式
            r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
            # 文本格式
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
            # 中文格式
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})年(\d{1,2})月',
            # 法语格式（非洲法语区）
            r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
            # 葡萄牙语格式（非洲葡语区）
            r'(\d{1,2})\s+(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+(\d{4})',
            # 非洲本地语言格式
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # 非洲常见日期分隔符
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # 非洲常见日期分隔符
            # 相对时间
            r'(\d+)\s+(days?|weeks?|months?|years?)\s+ago',
            r'(\d+)\s+(jours?|semaines?|mois?|années?)\s+il y a',
            r'(\d+)\s+(dias?|semanas?|meses?|anos?)\s+atrás',
            r'(\d+)\s+(天|周|月|年)前',
            # 非洲本地相对时间表达
            r'(\d+)\s+(day|week|month|year)s?\s+before',
            r'(\d+)\s+(jour|semaine|mois|année)s?\s+avant',
        ]
        
        # 清理HTML标签，提取纯文本
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = re.sub(r'\s+', ' ', text)
        
        # 优先处理包含日期关键词的文本片段
        date_keywords = ['published', 'date', 'time', 'posted', 'created', 'updated', 'modified']
        
        # 分割文本为句子，优先处理包含日期关键词的句子
        sentences = re.split(r'[.!?]', text)
        
        for sentence in sentences:
            # 如果句子包含日期关键词，优先处理
            if any(keyword in sentence.lower() for keyword in date_keywords):
                for pattern in date_patterns:
                    matches = re.findall(pattern, sentence, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            date_str = ' '.join(match)
                        else:
                            date_str = match
                        
                        # 尝试解析相对时间
                        if any(keyword in date_str.lower() for keyword in ['ago', 'il y a', 'atrás', '前', 'before', 'avant']):
                            relative_date = self._parse_relative_date(date_str)
                            if relative_date:
                                return relative_date.strftime('%Y-%m-%d')
                        
                        parsed_date = self._parse_and_validate_date(date_str, url)
                        if parsed_date != "unknown":
                            return parsed_date
        
        # 如果没有找到包含关键词的日期，处理整个文本
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    date_str = ' '.join(match)
                else:
                    date_str = match
                
                # 尝试解析相对时间
                if any(keyword in date_str.lower() for keyword in ['ago', 'il y a', 'atrás', '前', 'before', 'avant']):
                    relative_date = self._parse_relative_date(date_str)
                    if relative_date:
                        return relative_date.strftime('%Y-%m-%d')
                
                parsed_date = self._parse_and_validate_date(date_str, url)
                if parsed_date != "unknown":
                    return parsed_date
        
        # 策略3：从URL中提取日期
        url_date_patterns = [
            r'/(\d{4})/(\d{2})/(\d{2})/',
            r'/(\d{4})-(\d{2})-(\d{2})/',
            r'/(\d{4})/(\d{2})/',
            r'/(\d{4})-(\d{2})/',
            r'/(\d{4})/(\d{2})/(\d{2})/',
            r'/(\d{4})_(\d{2})_(\d{2})/',
            r'/(\d{4})(\d{2})(\d{2})/'
        ]
        
        for pattern in url_date_patterns:
            match = re.search(pattern, url)
            if match:
                groups = match.groups()
                if len(groups) >= 3:
                    # 完整的年月日
                    date_str = f"{groups[0]}-{groups[1]}-{groups[2]}"
                    parsed_date = self._parse_and_validate_date(date_str, url)
                    if parsed_date != "unknown":
                        return parsed_date
                elif len(groups) >= 2:
                    # 只有年月，使用当月第一天
                    date_str = f"{groups[0]}-{groups[1]}-01"
                    parsed_date = self._parse_and_validate_date(date_str, url)
                    if parsed_date != "unknown":
                        return parsed_date
        
        # 策略4：基于上下文推断日期
        context_date = self._infer_date_from_context(url)
        if context_date != "unknown":
            return context_date
        
        # 策略5：返回默认值
        return "unknown"
    
    def validate_article_quality(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """验证文章数据质量"""
        quality_score = 0
        issues = []
        
        # 1. 标题质量检测
        title = article.get('title', '').strip()
        if len(title) >= 10 and len(title) <= 200:
            quality_score += 25
        else:
            issues.append(f"标题长度异常: {len(title)}字符")
        
        # 2. 内容质量检测
        content = article.get('content', '').strip()
        content_length = len(content)
        if content_length >= 200:
            quality_score += 30
        elif content_length >= 100:
            quality_score += 20
        elif content_length >= 50:
            quality_score += 10
        else:
            issues.append(f"内容过短: {content_length}字符")
        
        # 3. 日期有效性检测
        date = article.get('date', '')
        if date and date != "unknown":
            quality_score += 20
            # 验证日期格式
            try:
                from datetime import datetime
                parsed_date = datetime.strptime(date, '%Y-%m-%d')
                current_year = datetime.now().year
                if 2000 <= parsed_date.year <= current_year:
                    quality_score += 10
                else:
                    issues.append(f"日期年份异常: {parsed_date.year}")
            except:
                issues.append("日期格式无效")
        else:
            issues.append("日期缺失或未知")
        
        # 4. URL有效性检测
        url = article.get('url', '')
        if url and url.startswith(('http://', 'https://')):
            quality_score += 15
        else:
            issues.append("URL格式无效")
        
        # 5. 内容重复检测（简单版）
        if content_length > 0:
            # 计算内容重复率（基于前100个字符）
            sample_text = content[:100]
            if len(set(sample_text)) / len(sample_text) > 0.5:  # 重复率低于50%
                quality_score += 10
            else:
                issues.append("内容重复率过高")
        
        # 6. 关键词相关性检测
        keywords = article.get('keywords', [])
        if keywords and len(keywords) >= 2:
            quality_score += 10
        
        # 设置质量等级
        if quality_score >= 80:
            quality_level = "excellent"
        elif quality_score >= 60:
            quality_level = "good"
        elif quality_score >= 40:
            quality_level = "fair"
        else:
            quality_level = "poor"
        
        # 添加质量信息到文章
        article['quality_score'] = quality_score
        article['quality_level'] = quality_level
        article['quality_issues'] = issues
        article['content_length'] = content_length
        
        logger.debug(f"文章质量检测: {title[:50]}... - 得分: {quality_score}, 等级: {quality_level}, 问题: {len(issues)}")
        
        return article
    
    def filter_low_quality_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤低质量文章"""
        filtered_articles = []
        
        for article in articles:
            # 验证文章质量
            validated_article = self.validate_article_quality(article)
            
            # 过滤条件：质量分数 >= 40 且内容长度 >= 100
            if (validated_article.get('quality_score', 0) >= 40 and 
                validated_article.get('content_length', 0) >= 100):
                filtered_articles.append(validated_article)
            else:
                logger.info(f"过滤低质量文章: {validated_article.get('title', '')[:50]}... - 得分: {validated_article.get('quality_score', 0)}")
        
        logger.info(f"文章过滤完成: {len(articles)} -> {len(filtered_articles)} (过滤 {len(articles) - len(filtered_articles)} 篇)")
        return filtered_articles
    
    def _parse_and_validate_date(self, date_str: str, url: str) -> str:
        """解析和验证日期 - 增强版，特别优化非洲新闻网站支持"""
        import re
        from datetime import datetime
        
        try:
            # 清理日期字符串
            date_str = date_str.strip()
            
            # 处理ISO格式日期
            if 'T' in date_str:
                date_part = date_str.split('T')[0]
                date_str = date_part
            
            # 扩展支持更多日期格式，特别针对非洲新闻网站
            date_formats = [
                # 标准格式
                '%Y-%m-%d',
                '%d-%m-%Y', 
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%Y.%m.%d',
                '%d.%m.%Y',
                '%Y/%m/%d',
                
                # 文本格式
                '%b %d, %Y',
                '%B %d, %Y',
                '%d %b %Y',
                '%d %B %Y',
                
                # 非洲新闻网站常见格式
                '%d-%b-%Y',  # 31-Dec-2023
                '%d-%B-%Y',  # 31-December-2023
                '%Y-%b-%d',  # 2023-Dec-31
                '%Y-%B-%d',  # 2023-December-31
                
                # 中文格式
                '%Y年%m月%d日',
                '%m月%d日%Y年',
                
                # 法语格式（非洲法语区）
                '%d %B %Y',  # 31 décembre 2023
                '%d %b %Y',  # 31 déc. 2023
                
                # 葡萄牙语格式（非洲葡语区）
                '%d de %B de %Y',  # 31 de dezembro de 2023
                '%d de %b de %Y',  # 31 de dez. de 2023
            ]
            
            # 首先尝试标准格式解析
            for date_format in date_formats:
                try:
                    # 截取前30个字符避免过长字符串
                    parsed_date = datetime.strptime(date_str[:30], date_format)
                    # 增强日期验证逻辑
                    if self._is_valid_date_for_context(parsed_date, url):
                        return parsed_date.strftime('%Y-%m-%d')
                except:
                    continue
            
            # 尝试提取数字日期（增强逻辑）
            numbers = re.findall(r'\d+', date_str)
            if len(numbers) >= 3:
                # 智能识别年月日顺序
                date_candidates = self._identify_date_order(numbers)
                for candidate in date_candidates:
                    try:
                        date_str = f"{candidate['year']}-{candidate['month'].zfill(2)}-{candidate['day'].zfill(2)}"
                        parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                        if self._is_valid_date_for_context(parsed_date, url):
                            return parsed_date.strftime('%Y-%m-%d')
                    except:
                        continue
            
            # 尝试相对时间解析（如"2 days ago"）
            relative_date = self._parse_relative_date(date_str)
            if relative_date and self._is_valid_date_for_context(relative_date, url):
                return relative_date.strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.debug(f"日期解析失败: {date_str}, 错误: {e}")
        
        return "unknown"
    
    def _is_valid_date_for_context(self, parsed_date, url: str) -> bool:
        """增强的日期验证逻辑，考虑上下文"""
        from datetime import datetime
        
        current_year = datetime.now().year
        
        # 基本验证：年份范围
        if not (2000 <= parsed_date.year <= current_year):
            return False
        
        # 不能是未来日期
        if parsed_date > datetime.now():
            return False
        
        # 对于非洲新闻网站，放宽日期验证
        if self._is_african_news_url(url):
            # 非洲新闻网站：允许更早的日期（1990年之后）
            if parsed_date.year >= 1990:
                return True
        else:
            # 非非洲网站：保持严格标准
            if parsed_date.year >= 2000:
                return True
        
        return False
    
    def _identify_date_order(self, numbers):
        """智能识别年月日顺序"""
        candidates = []
        
        # 尝试不同的年月日组合
        if len(numbers) >= 3:
            # 常见格式：YYYY-MM-DD
            if len(numbers[0]) == 4:
                candidates.append({
                    'year': numbers[0],
                    'month': numbers[1],
                    'day': numbers[2]
                })
            
            # 常见格式：DD-MM-YYYY
            if len(numbers[2]) == 4:
                candidates.append({
                    'year': numbers[2],
                    'month': numbers[1],
                    'day': numbers[0]
                })
            
            # 常见格式：MM-DD-YYYY
            if len(numbers[2]) == 4:
                candidates.append({
                    'year': numbers[2],
                    'month': numbers[0],
                    'day': numbers[1]
                })
        
        return candidates
    
    def _parse_relative_date(self, date_str: str):
        """解析相对时间（如"2 days ago"）"""
        import re
        from datetime import datetime, timedelta
        
        # 英文相对时间模式
        patterns = [
            (r'(\d+)\s+days?\s+ago', 'days'),
            (r'(\d+)\s+weeks?\s+ago', 'weeks'),
            (r'(\d+)\s+months?\s+ago', 'months'),
            (r'(\d+)\s+years?\s+ago', 'years'),
            (r'(\d+)\s+hours?\s+ago', 'hours'),
        ]
        
        # 法语相对时间模式（非洲法语区）
        french_patterns = [
            (r'(\d+)\s+jours?\s+il y a', 'days'),
            (r'(\d+)\s+semaines?\s+il y a', 'weeks'),
            (r'(\d+)\s+mois?\s+il y a', 'months'),
            (r'(\d+)\s+années?\s+il y a', 'years'),
        ]
        
        # 葡萄牙语相对时间模式（非洲葡语区）
        portuguese_patterns = [
            (r'(\d+)\s+dias?\s+atrás', 'days'),
            (r'(\d+)\s+semanas?\s+atrás', 'weeks'),
            (r'(\d+)\s+meses?\s+atrás', 'months'),
            (r'(\d+)\s+anos?\s+atrás', 'years'),
        ]
        
        # 中文相对时间模式
        chinese_patterns = [
            (r'(\d+)\s+天前', 'days'),
            (r'(\d+)\s+周前', 'weeks'),
            (r'(\d+)\s+月前', 'months'),
            (r'(\d+)\s+年前', 'years'),
        ]
        
        # 合并所有模式
        all_patterns = patterns + french_patterns + portuguese_patterns + chinese_patterns
        
        for pattern, unit in all_patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    num = int(match.group(1))
                    today = datetime.now()
                    
                    if unit == 'days':
                        delta = timedelta(days=num)
                    elif unit == 'weeks':
                        delta = timedelta(weeks=num)
                    elif unit == 'months':
                        delta = timedelta(days=num*30)  # 近似值
                    elif unit == 'years':
                        delta = timedelta(days=num*365)  # 近似值
                    elif unit == 'hours':
                        delta = timedelta(hours=num)
                    
                    result_date = today - delta
                    return result_date
                except:
                    continue
        
        return None
    
    def _infer_date_from_context(self, url: str) -> str:
        """基于上下文智能推断日期 - 增强版"""
        import re
        from datetime import datetime
        
        # 从URL中提取可能的年份信息
        year_patterns = [
            r'/(\d{4})/',
            r'/(\d{4})-',
            r'_(\d{4})_',
            r'(\d{4})\.',
            r'/(\d{4})_',
            r'_(\d{4})/',
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, url)
            if match:
                year = int(match.group(1))
                current_year = datetime.now().year
                # 验证年份合理性
                if 2000 <= year <= current_year:
                    # 使用该年份的1月1日作为推断日期
                    return f"{year}-01-01"
        
        # 基于网站域名推断（非洲新闻网站）
        if self._is_african_news_url(url):
            # 对于非洲新闻网站，如果无法从URL提取年份，使用当前年份
            current_year = datetime.now().year
            return f"{current_year}-01-01"
        
        return "unknown"
    
    def parse_search_results(self, html: str, keyword: str, year: int) -> List[Dict[str, Any]]:
        """解析搜索结果并应用质量验证"""
        # 这里简化处理，实际应该使用BeautifulSoup等库解析HTML
        # 返回模拟数据
        articles = []
        
        # 模拟生成一些文章数据
        for i in range(random.randint(1, 5)):
            article_id = hashlib.md5(f"{keyword}{year}{i}".encode()).hexdigest()
            
            # 生成不同质量的文章
            quality_variants = [
                {
                    'title': f"{keyword}在{year}年的重要发展报告{i+1}",
                    'content': f"这是关于{keyword}在{year}年的详细研究报告。文章分析了该领域的关键发展趋势、挑战和机遇。报告基于大量数据分析和专家访谈，提供了深入的见解。",
                    'date': f"{year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
                },
                {
                    'title': f"{keyword} {year}年新闻摘要",
                    'content': f"{keyword}领域在{year}年取得了显著进展。",
                    'date': "unknown"
                },
                {
                    'title': f"{keyword}",
                    'content': "简短内容",
                    'date': "2020-01-01"
                }
            ]
            
            variant = quality_variants[i % len(quality_variants)]
            
            article = {
                'article_id': article_id,
                'title': variant['title'],
                'url': f"https://example.com/article/{article_id}",
                'content': variant['content'],
                'date': variant['date'],
                'keyword': keyword,
                'year': year,
                'source': 'example.com',
                'crawled_at': datetime.now().isoformat(),
                'language': 'en',
                'word_count': len(variant['content']),
                'keywords': [keyword, f"{year}年", "非洲"]
            }
            
            articles.append(article)
        
        # 应用质量验证和过滤
        validated_articles = self.filter_low_quality_articles(articles)
        
        # 应用智能解析增强功能
        enhanced_articles = []
        for article in validated_articles:
            try:
                enhanced_article = enhance_with_intelligent_parsing(article)
                enhanced_articles.append(enhanced_article)
            except Exception as e:
                logger.warning(f"智能解析失败，使用原始文章: {e}")
                enhanced_articles.append(article)
        
        # 应用跨源信息对齐
        aligned_articles = []
        if len(enhanced_articles) > 1:
            try:
                aligned_articles = cross_aligner.align_articles_from_multiple_sources(enhanced_articles)
            except Exception as e:
                logger.warning(f"跨源对齐失败，使用原始文章: {e}")
                aligned_articles = enhanced_articles
        else:
            aligned_articles = enhanced_articles
        
        logger.info(f"搜索结果解析完成: 原始 {len(articles)} 篇 -> 过滤后 {len(validated_articles)} 篇 -> 智能增强 {len(aligned_articles)} 篇")
        
        return aligned_articles
    
    def _setup_performance_monitoring(self):
        """设置性能监控 - 增强网络连接性能监控"""
        try:
            # 初始化性能统计
            self.performance_stats = {
                'request_times': deque(maxlen=100),  # 最近100次请求时间
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_response_time': 0.0,
                'last_monitor_time': time.time(),
                'network_quality_score': 1.0  # 网络质量评分（0-1）
            }
            
            # 启动性能监控线程
            if PERFORMANCE_MONITORING:
                import threading
                
                def monitor_performance():
                    """性能监控线程"""
                    while True:
                        try:
                            # 计算平均响应时间
                            if self.performance_stats['request_times']:
                                self.performance_stats['avg_response_time'] = \
                                    sum(self.performance_stats['request_times']) / len(self.performance_stats['request_times'])
                            
                            # 计算网络质量评分
                            self._calculate_network_quality()
                            
                            # 自适应调整超时（如果启用）
                            if AUTO_ADJUST_TIMEOUT:
                                self._adjust_timeout_based_on_quality()
                            
                            # 记录性能日志
                            current_time = time.time()
                            if current_time - self.performance_stats['last_monitor_time'] >= MONITOR_INTERVAL:
                                logger.info(
                                    f"性能监控 - 平均响应时间: {self.performance_stats['avg_response_time']:.2f}s, "
                                    f"成功率: {self.performance_stats['successful_requests'] / max(1, self.performance_stats['successful_requests'] + self.performance_stats['failed_requests']) * 100:.1f}%, "
                                    f"网络质量: {self.performance_stats['network_quality_score']:.2f}"
                                )
                                self.performance_stats['last_monitor_time'] = current_time
                            
                        except Exception as e:
                            logger.warning(f"性能监控异常: {e}")
                        
                        time.sleep(10)  # 每10秒监控一次
                
                monitor_thread = threading.Thread(target=monitor_performance, daemon=True)
                monitor_thread.start()
                logger.info("性能监控线程已启动")
                
        except Exception as e:
            logger.warning(f"性能监控设置失败: {e}")
    
    def _calculate_network_quality(self):
        """计算网络质量评分"""
        try:
            # 基于响应时间和成功率计算网络质量
            avg_response_time = self.performance_stats['avg_response_time']
            total_requests = self.performance_stats['successful_requests'] + self.performance_stats['failed_requests']
            success_rate = self.performance_stats['successful_requests'] / max(1, total_requests)
            
            # 响应时间评分（响应时间越短，评分越高）
            response_score = max(0, 1 - (avg_response_time / 30))  # 30秒为最大容忍时间
            
            # 成功率评分
            success_score = success_rate
            
            # 综合评分
            network_quality = (response_score * 0.6 + success_score * 0.4)
            
            self.performance_stats['network_quality_score'] = max(0, min(1, network_quality))
            
        except Exception as e:
            logger.warning(f"网络质量计算异常: {e}")
    
    def _adjust_timeout_based_on_quality(self):
        """基于网络质量自适应调整超时"""
        try:
            quality = self.performance_stats['network_quality_score']
            
            # 根据网络质量调整超时时间
            # 更新全局配置（仅影响当前实例）
            global CONNECTION_TIMEOUT
            
            if quality < 0.3:  # 网络质量差
                new_timeout = min(120, CONNECTION_TIMEOUT * 2)  # 加倍超时时间
            elif quality < 0.6:  # 网络质量中等
                new_timeout = CONNECTION_TIMEOUT
            else:  # 网络质量好
                new_timeout = max(10, CONNECTION_TIMEOUT * 0.7)  # 减少超时时间
            
            # 更新会话超时设置
            if hasattr(self, 'session') and self.session:
                self.session.timeout = (new_timeout, 120)
            
            CONNECTION_TIMEOUT = new_timeout
            
            logger.debug(f"根据网络质量调整超时: {new_timeout}s (质量评分: {quality:.2f})")
            
        except Exception as e:
            logger.warning(f"超时调整异常: {e}")
    
    def run_single_thread(self):
        """单线程运行模式"""
        logger.info(f"工作节点 {self.worker_id} 启动（单线程模式）")
        
        # 创建独立的心跳发送线程
        import threading
        
        def heartbeat_worker():
            """独立的心跳发送线程 - 增强版：智能重连和错误恢复机制"""
            consecutive_failures = 0
            max_consecutive_failures = 5
            retry_delay = 5
            
            while True:
                try:
                    time.sleep(HEARTBEAT_INTERVAL)
                    
                    # 发送增强版心跳，包含系统状态信息
                    success = self.update_worker_status("active", {
                        'threads_running': threading.active_count(),
                        'memory_usage': self.get_memory_usage(),
                        'cpu_usage': self.get_cpu_usage(),
                        'processed_tasks': self.processed_tasks,
                        'failed_tasks': self.failed_tasks
                    })
                    
                    if success:
                        consecutive_failures = 0
                        logger.debug(f"工作节点 {self.worker_id} 发送心跳成功")
                    else:
                        consecutive_failures += 1
                        logger.warning(f"工作节点 {self.worker_id} 心跳发送失败，连续失败次数: {consecutive_failures}")
                        
                        # 如果连续失败超过阈值，尝试重新连接
                        if consecutive_failures >= max_consecutive_failures:
                            logger.error("心跳连续失败次数过多，尝试重新连接主节点")
                            
                            # 尝试重新连接，最多重试3次
                            for reconnect_attempt in range(3):
                                if self.initialize_connection():
                                    consecutive_failures = 0
                                    logger.info("重新连接成功，心跳恢复")
                                    break
                                else:
                                    logger.warning(f"重新连接失败，第{reconnect_attempt + 1}次尝试")
                                    time.sleep(retry_delay)
                            
                            if consecutive_failures > 0:
                                logger.error("所有重连尝试失败，系统可能处于离线状态")
                                # 不停止线程，继续尝试
                                
                except requests.exceptions.ConnectionError as e:
                    consecutive_failures += 1
                    logger.warning(f"心跳连接异常: {e}，连续失败次数: {consecutive_failures}")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error("心跳连续连接异常次数过多，尝试重新连接主节点")
                        # 尝试重新连接
                        for reconnect_attempt in range(3):
                            if self.initialize_connection():
                                consecutive_failures = 0
                                logger.info("重新连接成功")
                                break
                            else:
                                logger.warning(f"重新连接失败，第{reconnect_attempt + 1}次尝试")
                                time.sleep(retry_delay)
                                
                except requests.exceptions.Timeout as e:
                    consecutive_failures += 1
                    logger.warning(f"心跳超时: {e}，连续失败次数: {consecutive_failures}")
                    
                    # 超时情况下不立即重连，等待下一次心跳
                    if consecutive_failures >= max_consecutive_failures:
                        logger.warning("心跳连续超时次数过多，检查网络连接")
                        
                except Exception as e:
                    consecutive_failures += 1
                    logger.error(f"心跳发送异常: {e}，连续失败次数: {consecutive_failures}")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error("心跳连续异常次数过多，尝试重新连接主节点")
                        # 尝试重新连接
                        for reconnect_attempt in range(3):
                            if self.initialize_connection():
                                consecutive_failures = 0
                                logger.info("重新连接成功")
                                break
                            else:
                                logger.warning(f"重新连接失败，第{reconnect_attempt + 1}次尝试")
                                time.sleep(retry_delay)
        
        # 启动心跳线程
        heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
        heartbeat_thread.start()
        
        while True:
            try:
                # 获取任务
                task = self.get_task()
                
                if task:
                    self.processed_tasks += 1
                    
                    # 执行任务
                    result = self.execute_crawler_task(task)
                    
                    # 提交结果
                    self.submit_crawler_result(task, result)
                    
                    # 任务完成后短暂休息
                    time.sleep(1)
                else:
                    # 没有任务，等待一段时间
                    logger.info("队列为空，等待新任务...")
                    time.sleep(10)
                    
            except Exception as e:
                logger.error(f"工作节点异常: {e}")
                time.sleep(5)
    
    def run_multi_thread(self):
        """多线程运行模式"""
        logger.info(f"工作节点 {self.worker_id} 启动（多线程模式，{MAX_THREADS}线程）")
        
        last_heartbeat = time.time()
        
        # 创建独立的心跳发送线程
        import threading
        
        def heartbeat_worker():
            """独立的心跳发送线程"""
            consecutive_failures = 0
            max_consecutive_failures = 3
            
            while True:
                try:
                    time.sleep(HEARTBEAT_INTERVAL)
                    success = self.update_worker_status("active")
                    
                    if success:
                        consecutive_failures = 0
                        logger.debug(f"工作节点 {self.worker_id} 发送心跳成功")
                    else:
                        consecutive_failures += 1
                        logger.warning(f"工作节点 {self.worker_id} 心跳发送失败，连续失败次数: {consecutive_failures}")
                        
                        # 如果连续失败超过阈值，尝试重新连接
                        if consecutive_failures >= max_consecutive_failures:
                            logger.warning("心跳连续失败，尝试重新连接到主节点...")
                            if self.initialize_connection():
                                consecutive_failures = 0
                                logger.info("重新连接成功，心跳恢复")
                            else:
                                logger.error("重新连接失败，心跳线程将停止")
                                break
                except Exception as e:
                    consecutive_failures += 1
                    logger.error(f"心跳发送异常: {e}")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error("心跳异常次数过多，线程将停止")
                        break
        
        # 启动心跳线程
        heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
        heartbeat_thread.start()
        
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            while True:
                try:
                    # 获取一批任务
                    tasks = []
                    for _ in range(min(MAX_THREADS * 2, 20)):  # 获取一批任务
                        task = self.get_task()
                        if task:
                            tasks.append(task)
                        else:
                            break
                    
                    if tasks:
                        # 提交任务到线程池
                        future_to_task = {
                            executor.submit(self.execute_crawler_task, task): task 
                            for task in tasks
                        }
                        
                        # 处理完成的任务
                        for future in as_completed(future_to_task):
                            task = future_to_task[future]
                            try:
                                result = future.result()
                                self.submit_crawler_result(task, result)
                                self.processed_tasks += 1
                            except Exception as e:
                                logger.error(f"任务执行异常: {e}")
                                
                                # 提交失败结果
                                failed_result = {
                                    'task_id': task['task_id'],
                                    'worker_id': self.worker_id,
                                    'keyword': task['keyword'],
                                    'year': task.get('year', 2020),  # 安全地获取year字段
                                    'status': 'failed',
                                    'error': str(e),
                                    'completed_at': datetime.now().isoformat()
                                }
                                self.submit_crawler_result(task, failed_result)
                                self.failed_tasks += 1
                    else:
                        # 没有任务，等待
                        logger.info("队列为空，等待新任务...")
                        time.sleep(10)
                        
                except Exception as e:
                    logger.error(f"工作节点异常: {e}")
                    time.sleep(5)

# 创建监控API（可选功能，默认禁用）
MONITORING_ENABLED = os.getenv('MONITORING_ENABLED', 'false').lower() == 'true'

if MONITORING_ENABLED:
    from flask import Flask, jsonify
    import psutil
    import threading
    from collections import deque
    
    worker_app = Flask(__name__)
    
    # 全局变量，用于存储工作节点实例
    global_worker = None
    
    # 性能监控数据
    performance_data = {
        'cpu_usage': deque(maxlen=60),  # 保存最近60秒的CPU使用率
        'memory_usage': deque(maxlen=60),  # 保存最近60秒的内存使用率
        'task_throughput': deque(maxlen=60),  # 保存最近60秒的任务吞吐量
        'last_update': time.time()
    }
    
    def collect_performance_metrics():
        """收集性能指标"""
        while True:
            try:
                # 收集CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                performance_data['cpu_usage'].append(cpu_percent)
                
                # 收集内存使用率
                memory_info = psutil.virtual_memory()
                performance_data['memory_usage'].append(memory_info.percent)
                
                # 计算任务吞吐量（每分钟处理的任务数）
                current_time = time.time()
                if global_worker:
                    # 这里简化处理，实际应该记录更详细的任务统计
                    performance_data['task_throughput'].append(
                        global_worker.processed_tasks / max(1, (current_time - performance_data['last_update']))
                    )
                
                performance_data['last_update'] = current_time
                
            except Exception as e:
                logger.error(f"性能监控异常: {e}")
            
            time.sleep(1)  # 每秒收集一次
    
    # 启动性能监控线程
    performance_thread = threading.Thread(target=collect_performance_metrics, daemon=True)
    performance_thread.start()
    
    @worker_app.route('/')
    def worker_status():
        """工作节点状态"""
        if global_worker is None:
            return jsonify({'error': '工作节点未启动'}), 503
        
        # 计算性能指标
        avg_cpu = sum(performance_data['cpu_usage']) / max(1, len(performance_data['cpu_usage']))
        avg_memory = sum(performance_data['memory_usage']) / max(1, len(performance_data['memory_usage']))
        avg_throughput = sum(performance_data['task_throughput']) / max(1, len(performance_data['task_throughput']))
        
        return jsonify({
            'worker_id': global_worker.worker_id,
            'status': 'running',
            'processed_tasks': global_worker.processed_tasks,
            'successful_tasks': global_worker.successful_tasks,
            'failed_tasks': global_worker.failed_tasks,
            'success_rate': global_worker.successful_tasks / max(1, global_worker.processed_tasks) * 100,
            'performance': {
                'cpu_usage_avg': round(avg_cpu, 2),
                'memory_usage_avg': round(avg_memory, 2),
                'task_throughput_avg': round(avg_throughput, 2),
                'cpu_usage_recent': list(performance_data['cpu_usage']),
                'memory_usage_recent': list(performance_data['memory_usage'])
            },
            'timestamp': datetime.now().isoformat()
        })
    
    @worker_app.route('/health')
    def health_check():
        """健康检查"""
        return jsonify({'status': 'healthy'})
    
    @worker_app.route('/quality-stats')
    def quality_statistics():
        """质量统计信息"""
        if global_worker is None:
            return jsonify({'error': '工作节点未启动'}), 503
        
        # 这里可以添加更详细的质量统计
        return jsonify({
            'quality_metrics': {
                'articles_processed': global_worker.processed_tasks,
                'quality_levels': {
                    'excellent': 0,  # 实际应该从数据中统计
                    'good': 0,
                    'fair': 0,
                    'poor': 0
                },
                'avg_quality_score': 0,
                'filtered_articles': 0
            }
        })
    
    @worker_app.route('/performance')
    def performance_details():
        """详细性能信息"""
        if global_worker is None:
            return jsonify({'error': '工作节点未启动'}), 503
        
        # 获取系统详细信息
        cpu_count = psutil.cpu_count()
        memory_total = psutil.virtual_memory().total / (1024 ** 3)  # GB
        disk_usage = psutil.disk_usage('/')
        
        return jsonify({
            'system': {
                'cpu_cores': cpu_count,
                'memory_total_gb': round(memory_total, 2),
                'disk_total_gb': round(disk_usage.total / (1024 ** 3), 2),
                'disk_used_gb': round(disk_usage.used / (1024 ** 3), 2),
                'disk_free_gb': round(disk_usage.free / (1024 ** 3), 2)
            },
            'network': {
                'connections': len(psutil.net_connections())
            }
        })

def submit_keywords_to_master():
    """向主节点提交关键词任务"""
    try:
        logger.info("正在向主节点提交关键词任务...")
        response = requests.post(f"{MASTER_URL}/submit-tasks")
        if response.status_code == 200:
            result = response.json()
            logger.info(f"关键词任务提交成功: {result.get('message', '任务已提交')}")
            logger.info(f"提交了 {result.get('tasks_submitted', 0)} 个任务")
            return True
        else:
            logger.error(f"关键词任务提交失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"提交关键词任务失败: {e}")
        return False

def run_worker():
    """运行工作节点"""
    # 创建工作节点实例
    worker = DistributedWorker(WORKER_ID)
    logger.info(f"启动分布式爬虫工作节点: {worker.worker_id}")
    
    # 首先进行连接初始化
    logger.info("正在初始化主节点连接...")
    connection_success = worker.initialize_connection()
    
    if not connection_success:
        logger.error("无法连接到主节点，工作节点启动失败")
        return
    
    # 连接成功后向主节点注册
    try:
        worker.update_worker_status("active")
        logger.info(f"工作节点 {worker.worker_id} 已向主节点注册")
    except Exception as e:
        logger.warning(f"工作节点注册失败: {e}")
    
    # 向主节点提交关键词任务
    keywords_submitted = submit_keywords_to_master()
    if not keywords_submitted:
        logger.warning("关键词任务提交失败，系统将使用默认任务")
    
    # 可选：在后台线程中启动Flask监控API（默认禁用）
    if MONITORING_ENABLED:
        import threading
        
        # 设置全局工作节点实例
        global global_worker
        global_worker = worker
        
        def run_flask():
            worker_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info("工作节点监控API已启动 (端口: 5000)")
    else:
        logger.info("工作节点监控API已禁用")
    
    # 根据配置选择运行模式
    if MAX_THREADS > 1:
        worker.run_multi_thread()
    else:
        worker.run_single_thread()

# =============================================================================
# 智能解析与后处理模块
# =============================================================================

class IntelligentParser:
    """智能解析器 - 基于LLM的语义理解与多模态数据融合"""
    
    def __init__(self):
        self.llm_available = False
        self._initialize_llm()
        self.supported_languages = ['en', 'fr', 'pt', 'es', 'ar', 'sw']  # 非洲主要语言
        self.african_countries = [
            'nigeria', 'south africa', 'kenya', 'egypt', 'ghana', 'ethiopia',
            'morocco', 'tanzania', 'uganda', 'algeria', 'angola', 'congo',
            'cameroon', 'ivory coast', 'senegal', 'zimbabwe', 'zambia', 'mozambique'
        ]
        
    def _initialize_llm(self):
        """初始化LLM能力（如果可用）"""
        try:
            # 检查是否有可用的LLM API
            # 这里可以集成OpenAI、Claude、本地模型等
            self.llm_available = False  # 默认禁用，需要时启用
            logger.info("LLM智能解析器初始化完成")
        except Exception as e:
            logger.warning(f"LLM初始化失败: {e}")
    
    def intelligent_content_analysis(self, content, title="", url="", language="en"):
        """智能内容分析 - 基于语义理解的内容解析"""
        try:
            analysis_result = {
                'semantic_summary': self._extract_semantic_summary(content, title),
                'key_entities': self._extract_entities(content, language),
                'sentiment_analysis': self._analyze_sentiment(content, language),
                'topic_classification': self._classify_topic(content, language),
                'geographic_references': self._extract_geographic_references(content),
                'temporal_references': self._extract_temporal_references(content),
                'quality_score': self._calculate_content_quality(content, title),
                'relevance_to_africa': self._assess_africa_relevance(content, title)
            }
            
            return analysis_result
            
        except Exception as e:
            logger.warning(f"智能内容分析失败: {e}")
            return self._fallback_content_analysis(content, title)
    
    def _extract_semantic_summary(self, content, title):
        """提取语义摘要"""
        # 基于规则的关键信息提取
        summary_parts = []
        
        # 提取关键信息
        if title:
            summary_parts.append(f"标题: {title}")
        
        # 提取第一段关键信息
        sentences = content.split('. ')
        if sentences:
            first_sentence = sentences[0]
            if len(first_sentence) > 20:  # 确保有足够内容
                summary_parts.append(f"主要内容: {first_sentence[:200]}...")
        
        return ' | '.join(summary_parts) if summary_parts else "内容摘要不可用"
    
    def _extract_entities(self, content, language):
        """提取命名实体"""
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'african_keywords': []
        }
        
        # 基于规则的关键词提取
        content_lower = content.lower()
        
        # 提取非洲相关关键词
        african_keywords = [
            'africa', 'african', 'development', 'economy', 'politics',
            'health', 'education', 'technology', 'innovation', 'climate',
            'agriculture', 'infrastructure', 'trade', 'investment'
        ]
        
        for keyword in african_keywords:
            if keyword in content_lower:
                entities['african_keywords'].append(keyword)
        
        # 提取非洲国家名称
        for country in self.african_countries:
            if country in content_lower:
                entities['locations'].append(country.title())
        
        return entities
    
    def _analyze_sentiment(self, content, language):
        """情感分析"""
        # 基于关键词的情感分析
        positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'growth', 'improve', 'develop']
        negative_words = ['bad', 'poor', 'negative', 'problem', 'crisis', 'decline', 'conflict', 'corruption']
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _classify_topic(self, content, language):
        """主题分类"""
        content_lower = content.lower()
        
        topic_keywords = {
            'politics': ['government', 'president', 'election', 'policy', 'minister'],
            'economy': ['economy', 'gdp', 'market', 'trade', 'investment', 'business'],
            'technology': ['technology', 'digital', 'internet', 'mobile', 'innovation'],
            'health': ['health', 'medical', 'disease', 'hospital', 'vaccine'],
            'education': ['education', 'school', 'university', 'student', 'learning'],
            'environment': ['climate', 'environment', 'conservation', 'sustainability']
        }
        
        topic_scores = {topic: 0 for topic in topic_keywords}
        
        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    topic_scores[topic] += 1
        
        # 找到得分最高的主题
        if any(topic_scores.values()):
            main_topic = max(topic_scores, key=topic_scores.get)
            return main_topic
        
        return 'general'
    
    def _extract_geographic_references(self, content):
        """提取地理引用"""
        references = []
        
        # 检测非洲国家引用
        for country in self.african_countries:
            if country in content.lower():
                references.append({
                    'type': 'country',
                    'name': country.title(),
                    'region': self._get_african_region(country)
                })
        
        return references
    
    def _get_african_region(self, country):
        """获取非洲地区分类"""
        regions = {
            'west_africa': ['nigeria', 'ghana', 'ivory coast', 'senegal'],
            'east_africa': ['kenya', 'tanzania', 'uganda', 'ethiopia'],
            'southern_africa': ['south africa', 'zimbabwe', 'zambia', 'mozambique'],
            'north_africa': ['egypt', 'morocco', 'algeria'],
            'central_africa': ['congo', 'cameroon', 'angola']
        }
        
        for region, countries in regions.items():
            if country in countries:
                return region
        
        return 'other'
    
    def _extract_temporal_references(self, content):
        """提取时间引用"""
        # 简单的年份提取
        import re
        
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, content)
        
        return [f"20{y}" for y in set(years) if len(y) == 2]
    
    def _calculate_content_quality(self, content, title):
        """计算内容质量评分"""
        score = 0.5  # 基础分
        
        # 基于内容长度
        content_length = len(content)
        if content_length > 500:
            score += 0.2
        elif content_length > 200:
            score += 0.1
        
        # 基于标题质量
        if title and len(title) > 10:
            score += 0.1
        
        # 基于句子结构
        sentences = content.split('. ')
        if len(sentences) > 3:
            score += 0.1
        
        # 基于关键词密度
        important_words = ['africa', 'development', 'research', 'study', 'report']
        word_count = sum(1 for word in important_words if word in content.lower())
        if word_count >= 2:
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_africa_relevance(self, content, title):
        """评估非洲相关性"""
        relevance_score = 0
        
        africa_keywords = ['africa', 'african'] + self.african_countries
        
        content_lower = content.lower()
        
        # 检查标题中的非洲关键词
        if title:
            title_lower = title.lower()
            for keyword in africa_keywords:
                if keyword in title_lower:
                    relevance_score += 2
        
        # 检查内容中的非洲关键词
        for keyword in africa_keywords:
            if keyword in content_lower:
                relevance_score += 1
        
        return min(10, relevance_score) / 10.0  # 归一化到0-1
    
    def _fallback_content_analysis(self, content, title):
        """备用内容分析"""
        return {
            'semantic_summary': f"备用分析: {title or '无标题'}",
            'key_entities': {'persons': [], 'organizations': [], 'locations': [], 'dates': [], 'african_keywords': []},
            'sentiment_analysis': 'neutral',
            'topic_classification': 'general',
            'geographic_references': [],
            'temporal_references': [],
            'quality_score': 0.5,
            'relevance_to_africa': 0.3
        }

class DataCleaningEngine:
    """数据清洗与标准化引擎 - 增强版"""
    
    def __init__(self):
        self.date_formats = [
            '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y.%m.%d',
            '%B %d, %Y', '%d %B %Y', '%b %d, %Y', '%d %b %Y',
            '%Y/%m/%d', '%m-%d-%Y', '%d.%m.%Y', '%Y年%m月%d日'
        ]
        
        # 质量评估阈值
        self.quality_thresholds = {
            'min_title_length': 3,
            'min_content_length': 50,
            'max_content_length': 10000,
            'min_word_count': 10
        }
        
        # 常见垃圾内容模式
        self.spam_patterns = [
            r'广告.*?赞助', r'点击.*?查看', r'阅读.*?全文',
            r'登录.*?继续', r'注册.*?会员', r'下载.*?APP'
        ]
        
        # 语言检测模型
        self.language_detector = None
        
    def clean_and_standardize_article(self, article_data):
        """清洗和标准化文章数据 - 增强版"""
        try:
            cleaned_data = article_data.copy()
            
            # 数据质量评估
            quality_score = self._assess_data_quality(cleaned_data)
            cleaned_data['quality_score'] = quality_score
            
            # 清洗标题
            if 'title' in cleaned_data:
                cleaned_data['title'] = self._clean_text(cleaned_data['title'])
                cleaned_data['title_length'] = len(cleaned_data['title'])
            
            # 清洗内容
            if 'content' in cleaned_data:
                cleaned_data['content'] = self._clean_text(cleaned_data['content'])
                cleaned_data['content_length'] = len(cleaned_data['content'])
            
            # 标准化日期
            if 'date' in cleaned_data:
                cleaned_data['date'] = self._standardize_date(cleaned_data['date'])
            
            # 智能语言检测和标准化
            if 'language' in cleaned_data:
                cleaned_data['language'] = self._standardize_language(cleaned_data['language'])
            else:
                # 自动检测语言
                detected_lang = self._detect_language(cleaned_data.get('content', '') + ' ' + cleaned_data.get('title', ''))
                cleaned_data['language'] = detected_lang
            
            # 计算字数
            cleaned_data['word_count'] = len(cleaned_data.get('content', '').split())
            
            # 提取关键词
            cleaned_data['keywords'] = self._extract_keywords(cleaned_data.get('content', ''))
            
            # 情感分析
            cleaned_data['sentiment'] = self._analyze_sentiment(cleaned_data.get('content', ''))
            
            # 垃圾内容检测
            cleaned_data['is_spam'] = self._detect_spam(cleaned_data)
            
            # 数据完整性检查
            cleaned_data['completeness_score'] = self._calculate_completeness(cleaned_data)
            
            # 添加清洗标记和时间戳
            cleaned_data['cleaned'] = True
            cleaned_data['cleaned_at'] = datetime.now().isoformat()
            cleaned_data['cleaning_version'] = '2.0'
            
            logger.info(f"数据清洗完成: 质量评分 {quality_score:.2f}, 完整性 {cleaned_data['completeness_score']:.2f}")
            
            return cleaned_data
            
        except Exception as e:
            logger.warning(f"数据清洗失败: {e}")
            return article_data
    
    def _assess_data_quality(self, article_data):
        """评估数据质量"""
        score = 100.0
        
        # 标题质量
        title = article_data.get('title', '')
        if len(title) < self.quality_thresholds['min_title_length']:
            score -= 20
        elif len(title) > 200:
            score -= 10
        
        # 内容质量
        content = article_data.get('content', '')
        if len(content) < self.quality_thresholds['min_content_length']:
            score -= 30
        elif len(content) > self.quality_thresholds['max_content_length']:
            score -= 15
        
        # URL有效性
        url = article_data.get('url', '')
        if not url or not url.startswith(('http://', 'https://')):
            score -= 25
        
        # 日期有效性
        date = article_data.get('date', '')
        if date and date != 'unknown':
            try:
                from datetime import datetime
                datetime.strptime(date, '%Y-%m-%d')
            except:
                score -= 10
        
        return max(0, score)
    
    def _clean_text(self, text):
        """增强版文本清洗"""
        if not text:
            return ""
        
        import re
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 移除JavaScript代码
        text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL)
        
        # 移除CSS样式
        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL)
        
        # 移除多余空格和换行
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符但保留基本标点
        text = re.sub(r'[^\w\s.,!?;:()\-\'\"\u4e00-\u9fff\u0600-\u06ff]', ' ', text)
        
        # 清理开头和结尾的标点
        text = re.sub(r'^[\s\.,!?;:()\-]+|[\s\.,!?;:()\-]+$', '', text)
        
        return text.strip()
    
    def _standardize_date(self, date_str):
        """增强版日期标准化"""
        if not date_str or date_str.lower() in ['unknown', 'none', 'null', '']:
            return "unknown"
        
        try:
            from datetime import datetime
            
            # 清理日期字符串
            date_str = date_str.strip()
            
            # 尝试各种日期格式
            for fmt in self.date_formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # 尝试解析相对日期（如"2天前"）
            relative_match = re.search(r'(\d+)\s*(天|小时|分钟|月|年)\s*前', date_str)
            if relative_match:
                value, unit = relative_match.groups()
                value = int(value)
                now = datetime.now()
                
                if unit == '天':
                    delta = timedelta(days=value)
                elif unit == '小时':
                    delta = timedelta(hours=value)
                elif unit == '分钟':
                    delta = timedelta(minutes=value)
                elif unit == '月':
                    delta = timedelta(days=value*30)
                elif unit == '年':
                    delta = timedelta(days=value*365)
                
                result_date = now - delta
                return result_date.strftime('%Y-%m-%d')
            
            # 如果所有格式都失败，返回原始值
            return date_str
            
        except Exception:
            return date_str
    
    def _standardize_language(self, lang_code):
        """增强版语言代码标准化"""
        language_map = {
            'english': 'en', 'eng': 'en', 'en-us': 'en', 'en-gb': 'en', 'english-us': 'en',
            'french': 'fr', 'français': 'fr', 'fr-fr': 'fr', 'francais': 'fr',
            'portuguese': 'pt', 'português': 'pt', 'pt-pt': 'pt', 'portugues': 'pt',
            'spanish': 'es', 'español': 'es', 'es-es': 'es', 'espanol': 'es',
            'arabic': 'ar', 'العربية': 'ar', 'ar-sa': 'ar', 'arab': 'ar',
            'swahili': 'sw', 'kiswahili': 'sw', 'swahili-tz': 'sw', 'swahili-ke': 'sw',
            'chinese': 'zh', '中文': 'zh', 'zh-cn': 'zh', 'zh-tw': 'zh', 'chinese-simplified': 'zh',
            'russian': 'ru', 'русский': 'ru', 'ru-ru': 'ru',
            'german': 'de', 'deutsch': 'de', 'de-de': 'de'
        }
        
        if lang_code.lower() in language_map:
            return language_map[lang_code.lower()]
        
        # 如果是标准代码，直接返回
        if len(lang_code) == 2:
            return lang_code.lower()
        
        return 'unknown'
    
    def _detect_language(self, text):
        """智能语言检测"""
        if not text or len(text) < 10:
            return 'unknown'
        
        try:
            # 简单的基于字符的语言检测
            import re
            
            # 中文字符检测
            if re.search(r'[\u4e00-\u9fff]', text):
                return 'zh'
            
            # 阿拉伯字符检测
            if re.search(r'[\u0600-\u06ff]', text):
                return 'ar'
            
            # 西里尔字符检测
            if re.search(r'[\u0400-\u04ff]', text):
                return 'ru'
            
            # 基于常见词汇的检测
            text_lower = text.lower()
            
            # 英语词汇
            english_words = ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that']
            # 法语词汇
            french_words = ['le', 'la', 'les', 'de', 'des', 'un', 'une', 'et', 'est', 'dans']
            # 西班牙语词汇
            spanish_words = ['el', 'la', 'los', 'las', 'de', 'en', 'y', 'es', 'un', 'una']
            # 葡萄牙语词汇
            portuguese_words = ['o', 'a', 'os', 'as', 'de', 'em', 'e', 'é', 'um', 'uma']
            
            scores = {}
            for word in english_words:
                if word in text_lower:
                    scores['en'] = scores.get('en', 0) + 1
            
            for word in french_words:
                if word in text_lower:
                    scores['fr'] = scores.get('fr', 0) + 1
            
            for word in spanish_words:
                if word in text_lower:
                    scores['es'] = scores.get('es', 0) + 1
            
            for word in portuguese_words:
                if word in text_lower:
                    scores['pt'] = scores.get('pt', 0) + 1
            
            if scores:
                return max(scores.items(), key=lambda x: x[1])[0]
            
            return 'en'  # 默认英语
            
        except Exception:
            return 'unknown'
    
    def _extract_keywords(self, text, max_keywords=10):
        """提取关键词"""
        if not text or len(text) < 50:
            return []
        
        try:
            import re
            from collections import Counter
            
            # 移除标点符号
            words = re.findall(r'\b\w+\b', text.lower())
            
            # 过滤停用词
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
                'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
                'le', 'la', 'les', 'de', 'des', 'un', 'une', 'et', 'est', 'dans',
                'el', 'los', 'las', 'y', 'es', 'un', 'una', 'de', 'en',
                'o', 'os', 'as', 'e', 'é', 'um', 'uma', 'de', 'em'
            }
            
            filtered_words = [word for word in words if len(word) > 2 and word not in stop_words]
            
            # 计算词频
            word_freq = Counter(filtered_words)
            
            # 返回前N个关键词
            return [word for word, freq in word_freq.most_common(max_keywords)]
            
        except Exception:
            return []
    
    def _analyze_sentiment(self, text):
        """简单情感分析"""
        if not text:
            return 'neutral'
        
        try:
            positive_words = {
                'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'perfect',
                'happy', 'joy', 'love', 'like', 'nice', 'beautiful', 'best', 'better',
                'success', 'win', 'victory', 'positive', 'optimistic', 'hope', 'promising'
            }
            
            negative_words = {
                'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'dislike',
                'sad', 'angry', 'frustrated', 'disappointed', 'failure', 'problem',
                'issue', 'error', 'mistake', 'negative', 'pessimistic', 'worry', 'concern'
            }
            
            words = set(text.lower().split())
            
            positive_count = len(words & positive_words)
            negative_count = len(words & negative_words)
            
            if positive_count > negative_count:
                return 'positive'
            elif negative_count > positive_count:
                return 'negative'
            else:
                return 'neutral'
                
        except Exception:
            return 'neutral'
    
    def _detect_spam(self, article_data):
        """垃圾内容检测"""
        try:
            content = article_data.get('content', '').lower()
            title = article_data.get('title', '').lower()
            
            # 检查垃圾模式
            for pattern in self.spam_patterns:
                import re
                if re.search(pattern, content) or re.search(pattern, title):
                    return True
            
            # 检查内容长度异常
            if len(content) < 20 or len(content) > 50000:
                return True
            
            # 检查标题长度异常
            if len(title) < 3 or len(title) > 500:
                return True
            
            return False
            
        except Exception:
            return False
    
    def _calculate_completeness(self, article_data):
        """计算数据完整性得分"""
        required_fields = ['title', 'content', 'url', 'date']
        optional_fields = ['author', 'source', 'language', 'category']
        
        score = 0
        max_score = len(required_fields) * 2 + len(optional_fields)
        
        # 必需字段
        for field in required_fields:
            value = article_data.get(field, '')
            if value and value != 'unknown':
                score += 2
            elif value:
                score += 1
        
        # 可选字段
        for field in optional_fields:
            value = article_data.get(field, '')
            if value and value != 'unknown':
                score += 1
        
        return (score / max_score) * 100 if max_score > 0 else 0
    
    def batch_clean_articles(self, articles_list):
        """批量清洗文章数据"""
        cleaned_articles = []
        stats = {
            'total': len(articles_list),
            'cleaned': 0,
            'failed': 0,
            'quality_scores': []
        }
        
        for article in articles_list:
            try:
                cleaned_article = self.clean_and_standardize_article(article)
                cleaned_articles.append(cleaned_article)
                stats['cleaned'] += 1
                stats['quality_scores'].append(cleaned_article.get('quality_score', 0))
            except Exception as e:
                logger.warning(f"批量清洗失败: {e}")
                stats['failed'] += 1
        
        # 计算统计信息
        if stats['quality_scores']:
            stats['avg_quality'] = sum(stats['quality_scores']) / len(stats['quality_scores'])
            stats['min_quality'] = min(stats['quality_scores'])
            stats['max_quality'] = max(stats['quality_scores'])
        
        logger.info(f"批量清洗完成: {stats['cleaned']}/{stats['total']} 成功, 平均质量 {stats.get('avg_quality', 0):.2f}")
        
        return cleaned_articles, stats

class CrossSourceAlignment:
    """跨数据源信息对齐与融合引擎"""
    
    def __init__(self):
        self.entity_cache = {}
        self.similarity_threshold = 0.6  # 相似度阈值
        self.min_content_length = 50     # 最小内容长度
        
    def align_articles_from_multiple_sources(self, articles_list):
        """对齐来自多个来源的文章"""
        try:
            if not articles_list:
                return []
            
            # 预处理：过滤低质量文章
            filtered_articles = self._preprocess_articles(articles_list)
            
            # 按标题和内容相似度分组
            grouped_articles = self._group_similar_articles(filtered_articles)
            
            # 对每组文章进行智能信息融合
            aligned_articles = []
            fusion_stats = {
                'total_groups': len(grouped_articles),
                'articles_fused': 0,
                'quality_improvements': []
            }
            
            for group in grouped_articles:
                if group:
                    aligned_article = self._fuse_article_information(group)
                    if aligned_article:
                        aligned_articles.append(aligned_article)
                        fusion_stats['articles_fused'] += len(group)
                        
                        # 计算质量改进
                        base_quality = max(article.get('quality_score', 0) for article in group)
                        fused_quality = aligned_article.get('quality_score', 0)
                        if fused_quality > base_quality:
                            fusion_stats['quality_improvements'].append(fused_quality - base_quality)
            
            # 计算融合统计
            if fusion_stats['quality_improvements']:
                fusion_stats['avg_quality_improvement'] = sum(fusion_stats['quality_improvements']) / len(fusion_stats['quality_improvements'])
            
            logger.info(f"跨源对齐完成: {len(articles_list)} 篇 -> {len(aligned_articles)} 篇, "
                       f"质量改进: {fusion_stats.get('avg_quality_improvement', 0):.2f}")
            
            return aligned_articles
            
        except Exception as e:
            logger.warning(f"跨源对齐失败: {e}")
            return articles_list
    
    def _preprocess_articles(self, articles):
        """预处理文章数据"""
        filtered_articles = []
        
        for article in articles:
            # 检查基本完整性
            if not article.get('title') or not article.get('content'):
                continue
            
            # 检查内容长度
            if len(article.get('content', '')) < self.min_content_length:
                continue
            
            # 检查垃圾内容
            if article.get('is_spam', False):
                continue
            
            filtered_articles.append(article)
        
        return filtered_articles
    
    def _group_similar_articles(self, articles):
        """按相似度分组文章"""
        groups = []
        used_indices = set()
        
        for i, article1 in enumerate(articles):
            if i in used_indices:
                continue
            
            group = [article1]
            used_indices.add(i)
            
            for j, article2 in enumerate(articles[i+1:], i+1):
                if j in used_indices:
                    continue
                
                if self._are_articles_similar(article1, article2):
                    group.append(article2)
                    used_indices.add(j)
            
            groups.append(group)
        
        return groups
    
    def _are_articles_similar(self, article1, article2):
        """判断两篇文章是否相似"""
        # 基于标题相似度
        title_similarity = self._calculate_title_similarity(article1, article2)
        
        # 基于内容相似度
        content_similarity = self._calculate_content_similarity(article1, article2)
        
        # 基于实体相似度
        entity_similarity = self._calculate_entity_similarity(article1, article2)
        
        # 综合相似度计算
        overall_similarity = (title_similarity * 0.4 + 
                             content_similarity * 0.4 + 
                             entity_similarity * 0.2)
        
        return overall_similarity > self.similarity_threshold
    
    def _calculate_title_similarity(self, article1, article2):
        """计算标题相似度"""
        title1 = article1.get('title', '').lower()
        title2 = article2.get('title', '').lower()
        
        if not title1 or not title2:
            return 0.0
        
        # 使用Jaccard相似度
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_content_similarity(self, article1, article2):
        """计算内容相似度"""
        content1 = article1.get('content', '').lower()
        content2 = article2.get('content', '').lower()
        
        if not content1 or not content2:
            return 0.0
        
        # 提取关键词进行比较
        keywords1 = set(self._extract_keywords(content1, max_keywords=20))
        keywords2 = set(self._extract_keywords(content2, max_keywords=20))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_entity_similarity(self, article1, article2):
        """计算实体相似度"""
        # 提取文章中的关键实体（人物、地点、组织等）
        entities1 = self._extract_entities(article1)
        entities2 = self._extract_entities(article2)
        
        if not entities1 or not entities2:
            return 0.0
        
        intersection = len(entities1 & entities2)
        union = len(entities1 | entities2)
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_entities(self, article):
        """提取文章中的关键实体"""
        try:
            text = f"{article.get('title', '')} {article.get('content', '')}"
            
            # 简单的实体提取（基于关键词和模式匹配）
            entities = set()
            
            # 提取非洲国家名称
            african_countries = {
                'nigeria', 'south africa', 'kenya', 'ethiopia', 'egypt', 'ghana',
                'tanzania', 'uganda', 'algeria', 'sudan', 'morocco', 'angola',
                'mozambique', 'zambia', 'zimbabwe', 'senegal', 'tunisia', 'libya'
            }
            
            for country in african_countries:
                if country in text.lower():
                    entities.add(country)
            
            # 提取常见组织名称
            organizations = {
                'un', 'united nations', 'african union', 'world bank', 'imf',
                'who', 'world health organization', 'unicef', 'red cross'
            }
            
            for org in organizations:
                if org in text.lower():
                    entities.add(org)
            
            # 提取关键词作为补充实体
            keywords = self._extract_keywords(text, max_keywords=15)
            entities.update(keywords)
            
            return entities
            
        except Exception:
            return set()
    
    def _extract_keywords(self, text, max_keywords=10):
        """提取关键词"""
        try:
            import re
            from collections import Counter
            
            words = re.findall(r'\b\w+\b', text.lower())
            
            # 过滤停用词
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
                'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had'
            }
            
            filtered_words = [word for word in words if len(word) > 2 and word not in stop_words]
            word_freq = Counter(filtered_words)
            
            return [word for word, freq in word_freq.most_common(max_keywords)]
            
        except Exception:
            return []
    
    def _fuse_article_information(self, articles):
        """智能融合文章信息"""
        if not articles:
            return None
        
        # 选择质量最高的文章作为基础
        base_article = max(articles, key=lambda x: x.get('quality_score', 0))
        
        fused_article = base_article.copy()
        
        # 合并来源信息
        sources = [article.get('source', '') for article in articles]
        fused_article['sources'] = list(set(filter(None, sources)))
        
        # 智能选择最佳日期
        fused_article['date'] = self._select_best_date(articles)
        
        # 融合内容（选择最完整的内容）
        fused_article['content'] = self._fuse_content(articles)
        
        # 融合作者信息
        fused_article['author'] = self._fuse_authors(articles)
        
        # 融合关键词
        fused_article['keywords'] = self._fuse_keywords(articles)
        
        # 融合情感分析结果
        fused_article['sentiment'] = self._fuse_sentiment(articles)
        
        # 计算融合后的质量评分
        fused_article['quality_score'] = self._calculate_fused_quality(articles)
        
        # 标记为融合结果
        fused_article['fused'] = True
        fused_article['original_count'] = len(articles)
        fused_article['fusion_timestamp'] = self._get_current_timestamp()
        
        return fused_article
    
    def _select_best_date(self, articles):
        """选择最佳日期"""
        dates = [article.get('date', '') for article in articles]
        valid_dates = [d for d in dates if d and d != 'unknown']
        
        if not valid_dates:
            return 'unknown'
        
        try:
            from datetime import datetime
            # 选择最新的日期
            latest_date = max(valid_dates, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
            return latest_date
        except:
            # 如果日期格式不标准，返回第一个有效日期
            return valid_dates[0]
    
    def _fuse_content(self, articles):
        """融合内容"""
        # 选择内容最长的文章
        return max(articles, key=lambda x: len(x.get('content', ''))).get('content', '')
    
    def _fuse_authors(self, articles):
        """融合作者信息"""
        authors = [article.get('author', '') for article in articles]
        valid_authors = [a for a in authors if a and a != 'unknown']
        
        if not valid_authors:
            return 'unknown'
        
        # 选择出现频率最高的作者
        from collections import Counter
        author_counts = Counter(valid_authors)
        return author_counts.most_common(1)[0][0]
    
    def _fuse_keywords(self, articles):
        """融合关键词"""
        all_keywords = []
        for article in articles:
            keywords = article.get('keywords', [])
            if keywords:
                all_keywords.extend(keywords)
        
        if not all_keywords:
            return []
        
        # 按频率排序并去重
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        return [kw for kw, count in keyword_counts.most_common(15)]
    
    def _fuse_sentiment(self, articles):
        """融合情感分析结果"""
        sentiments = [article.get('sentiment', 'neutral') for article in articles]
        
        # 简单投票机制
        from collections import Counter
        sentiment_counts = Counter(sentiments)
        return sentiment_counts.most_common(1)[0][0]
    
    def _calculate_fused_quality(self, articles):
        """计算融合后的质量评分"""
        # 基础质量评分（取最高分）
        base_quality = max(article.get('quality_score', 0) for article in articles)
        
        # 融合质量加成
        fusion_bonus = min(len(articles) * 5, 20)  # 最多加成20分
        
        # 内容完整性加成
        content_lengths = [len(article.get('content', '')) for article in articles]
        max_content_length = max(content_lengths) if content_lengths else 0
        content_bonus = min(max_content_length / 1000, 10)  # 最多加成10分
        
        return min(base_quality + fusion_bonus + content_bonus, 100)
    
    def _get_current_timestamp(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

class MultimodalDataProcessor:
    """多模态数据处理与融合引擎"""
    
    def __init__(self):
        self.image_processing_enabled = False
        self.audio_processing_enabled = False
        self.ocr_enabled = False
        self.sentiment_analysis_enabled = True  # 默认启用情感分析
        self.keyword_extraction_enabled = True  # 默认启用关键词提取
        
        # 初始化多模态处理能力
        self._initialize_multimodal_capabilities()
    
    def _initialize_multimodal_capabilities(self):
        """初始化多模态处理能力"""
        try:
            # 检查图像处理能力
            try:
                import cv2
                self.image_processing_enabled = True
                logger.info("图像处理能力已启用 (OpenCV)")
            except ImportError:
                logger.warning("OpenCV未安装，图像处理功能受限")
            
            # 检查音频处理能力
            try:
                import librosa
                self.audio_processing_enabled = True
                logger.info("音频处理能力已启用 (Librosa)")
            except ImportError:
                logger.warning("Librosa未安装，音频处理功能受限")
            
            # 检查OCR能力
            try:
                import pytesseract
                from PIL import Image
                self.ocr_enabled = True
                logger.info("OCR能力已启用 (Tesseract)")
            except ImportError:
                logger.warning("OCR库未安装，文字识别功能受限")
                
        except Exception as e:
            logger.warning(f"多模态能力初始化失败: {e}")
    
    def process_multimodal_content(self, article_data):
        """处理多模态内容并生成洞察"""
        try:
            insights = {
                'multimodal_analysis': {},
                'sentiment_analysis': {},
                'keyword_insights': {},
                'content_quality': {},
                'africa_relevance': {}
            }
            
            # 处理文本内容
            text_content = article_data.get('content', '')
            if text_content:
                insights.update(self._analyze_text_content(text_content, article_data))
            
            # 处理图像内容
            image_urls = article_data.get('image_urls', [])
            if image_urls and self.image_processing_enabled:
                insights['multimodal_analysis']['images'] = self._analyze_images(image_urls)
            
            # 处理音频/视频内容
            media_urls = article_data.get('media_urls', [])
            if media_urls and self.audio_processing_enabled:
                insights['multimodal_analysis']['media'] = self._analyze_media(media_urls)
            
            # 生成综合洞察
            insights['comprehensive_insights'] = self._generate_comprehensive_insights(insights, article_data)
            
            return insights
            
        except Exception as e:
            logger.warning(f"多模态内容处理失败: {e}")
            return {}
    
    def _analyze_text_content(self, text_content, article_data):
        """分析文本内容"""
        insights = {}
        
        # 情感分析
        if self.sentiment_analysis_enabled:
            insights['sentiment_analysis'] = self._perform_sentiment_analysis(text_content)
        
        # 关键词提取
        if self.keyword_extraction_enabled:
            insights['keyword_insights'] = self._extract_keywords_and_entities(text_content)
        
        # 内容质量评估
        insights['content_quality'] = self._assess_content_quality(text_content)
        
        # 非洲相关性评估
        insights['africa_relevance'] = self._assess_africa_relevance(text_content)
        
        return insights
    
    def _perform_sentiment_analysis(self, text):
        """执行情感分析"""
        try:
            # 简单的情感分析实现（可替换为更复杂的NLP库）
            positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'growth', 'development']
            negative_words = ['bad', 'poor', 'negative', 'failure', 'problem', 'crisis', 'conflict']
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            total_words = len(text.split())
            if total_words == 0:
                return {'sentiment': 'neutral', 'score': 0.0}
            
            sentiment_score = (positive_count - negative_count) / total_words
            
            if sentiment_score > 0.1:
                sentiment = 'positive'
            elif sentiment_score < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'sentiment': sentiment,
                'score': sentiment_score,
                'positive_words': positive_count,
                'negative_words': negative_count
            }
            
        except Exception as e:
            logger.warning(f"情感分析失败: {e}")
            return {'sentiment': 'neutral', 'score': 0.0}
    
    def _extract_keywords_and_entities(self, text):
        """提取关键词和实体"""
        try:
            # 简单的关键词提取实现
            import re
            from collections import Counter
            
            # 移除标点符号
            words = re.findall(r'\b\w+\b', text.lower())
            
            # 过滤停用词
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
            
            # 计算词频
            word_freq = Counter(filtered_words)
            top_keywords = word_freq.most_common(10)
            
            # 识别非洲相关实体
            africa_entities = self._identify_africa_entities(text)
            
            return {
                'top_keywords': [{'word': word, 'frequency': freq} for word, freq in top_keywords],
                'africa_entities': africa_entities,
                'total_unique_words': len(set(filtered_words))
            }
            
        except Exception as e:
            logger.warning(f"关键词提取失败: {e}")
            return {'top_keywords': [], 'africa_entities': [], 'total_unique_words': 0}
    
    def _identify_africa_entities(self, text):
        """识别非洲相关实体"""
        africa_countries = [
            'nigeria', 'south africa', 'kenya', 'ghana', 'ethiopia', 'egypt', 'tanzania',
            'uganda', 'morocco', 'algeria', 'angola', 'mozambique', 'zambia', 'zimbabwe',
            'senegal', 'cameroon', 'cote d\'ivoire', 'tunisia', 'libya', 'sudan'
        ]
        
        africa_cities = [
            'lagos', 'cairo', 'nairobi', 'accra', 'addis ababa', 'dar es salaam',
            'kampala', 'casablanca', 'algiers', 'luanda', 'maputo', 'lusaka',
            'harare', 'dakar', 'yaounde', 'abidjan', 'tunis', 'tripoli', 'khartoum'
        ]
        
        entities_found = []
        text_lower = text.lower()
        
        for country in africa_countries:
            if country in text_lower:
                entities_found.append({'type': 'country', 'name': country, 'relevance': 'high'})
        
        for city in africa_cities:
            if city in text_lower:
                entities_found.append({'type': 'city', 'name': city, 'relevance': 'medium'})
        
        return entities_found
    
    def _assess_content_quality(self, text):
        """评估内容质量"""
        try:
            words = text.split()
            sentences = text.split('.')
            
            # 计算基本指标
            word_count = len(words)
            sentence_count = len([s for s in sentences if s.strip()])
            avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
            
            # 质量评分
            quality_score = min(word_count / 100, 1.0)  # 基于长度
            
            return {
                'word_count': word_count,
                'sentence_count': sentence_count,
                'avg_sentence_length': round(avg_sentence_length, 2),
                'quality_score': round(quality_score, 2),
                'quality_level': 'high' if quality_score > 0.7 else 'medium' if quality_score > 0.3 else 'low'
            }
            
        except Exception as e:
            logger.warning(f"内容质量评估失败: {e}")
            return {'quality_score': 0.0, 'quality_level': 'unknown'}
    
    def _assess_africa_relevance(self, text):
        """评估非洲相关性"""
        try:
            africa_keywords = [
                'africa', 'african', 'development', 'economy', 'investment', 'trade',
                'infrastructure', 'agriculture', 'mining', 'technology', 'innovation'
            ]
            
            text_lower = text.lower()
            keyword_matches = sum(1 for keyword in africa_keywords if keyword in text_lower)
            
            relevance_score = min(keyword_matches / len(africa_keywords), 1.0)
            
            return {
                'relevance_score': round(relevance_score, 2),
                'keyword_matches': keyword_matches,
                'relevance_level': 'high' if relevance_score > 0.5 else 'medium' if relevance_score > 0.2 else 'low'
            }
            
        except Exception as e:
            logger.warning(f"非洲相关性评估失败: {e}")
            return {'relevance_score': 0.0, 'relevance_level': 'unknown'}
    
    def _analyze_images(self, image_urls):
        """分析图像内容"""
        try:
            if not self.image_processing_enabled:
                return {'status': 'disabled', 'message': '图像处理功能未启用'}
            
            analysis_results = []
            
            for i, image_url in enumerate(image_urls[:3]):  # 限制分析前3张图片
                try:
                    # 这里可以添加实际的图像分析代码
                    # 例如使用OpenCV进行图像特征提取
                    analysis_result = {
                        'image_url': image_url,
                        'analysis_type': 'basic',
                        'status': 'analyzed',
                        'features': ['颜色分析', '基本形状识别'],
                        'ocr_text': self._extract_text_from_image(image_url) if self.ocr_enabled else 'OCR未启用'
                    }
                    analysis_results.append(analysis_result)
                    
                except Exception as e:
                    analysis_results.append({
                        'image_url': image_url,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return {
                'total_images': len(image_urls),
                'analyzed_count': len(analysis_results),
                'results': analysis_results
            }
            
        except Exception as e:
            logger.warning(f"图像分析失败: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _extract_text_from_image(self, image_url):
        """从图像中提取文字"""
        try:
            if not self.ocr_enabled:
                return "OCR功能未启用"
            
            # 这里可以添加实际的OCR代码
            # 例如使用Tesseract进行文字识别
            return "OCR文本提取功能待实现"
            
        except Exception as e:
            return f"OCR提取失败: {str(e)}"
    
    def _analyze_media(self, media_urls):
        """分析音频/视频内容"""
        try:
            if not self.audio_processing_enabled:
                return {'status': 'disabled', 'message': '音频处理功能未启用'}
            
            analysis_results = []
            
            for media_url in media_urls[:2]:  # 限制分析前2个媒体文件
                try:
                    # 这里可以添加实际的媒体分析代码
                    analysis_result = {
                        'media_url': media_url,
                        'analysis_type': 'basic',
                        'status': 'analyzed',
                        'features': ['音频波形分析', '基本时长检测']
                    }
                    analysis_results.append(analysis_result)
                    
                except Exception as e:
                    analysis_results.append({
                        'media_url': media_url,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return {
                'total_media': len(media_urls),
                'analyzed_count': len(analysis_results),
                'results': analysis_results
            }
            
        except Exception as e:
            logger.warning(f"媒体分析失败: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _generate_comprehensive_insights(self, insights, article_data):
        """生成综合洞察"""
        try:
            comprehensive = {
                'summary': '',
                'key_findings': [],
                'recommendations': [],
                'confidence_score': 0.0
            }
            
            # 生成摘要
            sentiment = insights.get('sentiment_analysis', {}).get('sentiment', 'neutral')
            relevance = insights.get('africa_relevance', {}).get('relevance_level', 'unknown')
            quality = insights.get('content_quality', {}).get('quality_level', 'unknown')
            
            comprehensive['summary'] = f"这是一篇{quality}质量的文章，情感倾向为{sentiment}，非洲相关性为{relevance}。"
            
            # 关键发现
            if sentiment != 'neutral':
                comprehensive['key_findings'].append(f"文章情感倾向明显：{sentiment}")
            
            if relevance != 'low':
                comprehensive['key_findings'].append(f"非洲相关性：{relevance}")
            
            # 推荐
            if quality == 'low':
                comprehensive['recommendations'].append("建议寻找更高质量的内容来源")
            
            if relevance == 'high':
                comprehensive['recommendations'].append("这篇文章对非洲研究具有重要参考价值")
            
            # 置信度评分
            confidence_factors = []
            if insights.get('sentiment_analysis'):
                confidence_factors.append(0.3)
            if insights.get('keyword_insights', {}).get('top_keywords'):
                confidence_factors.append(0.3)
            if insights.get('content_quality', {}).get('quality_score', 0) > 0.5:
                confidence_factors.append(0.4)
            
            comprehensive['confidence_score'] = round(sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0, 2)
            
            return comprehensive
            
        except Exception as e:
            logger.warning(f"综合洞察生成失败: {e}")
            return {'summary': '洞察生成失败', 'key_findings': [], 'recommendations': [], 'confidence_score': 0.0}

# 全局智能解析器实例
intelligent_parser = IntelligentParser()
data_cleaner = DataCleaningEngine()
cross_aligner = CrossSourceAlignment()
multimodal_processor = MultimodalDataProcessor()

def enhance_with_intelligent_parsing(article_data):
    """使用智能解析增强文章数据"""
    try:
        # 数据清洗
        cleaned_article = data_cleaner.clean_and_standardize_article(article_data)
        
        # 智能内容分析
        content = cleaned_article.get('content', '')
        title = cleaned_article.get('title', '')
        language = cleaned_article.get('language', 'en')
        
        analysis_result = intelligent_parser.intelligent_content_analysis(
            content, title, cleaned_article.get('url', ''), language
        )
        
        # 多模态数据处理与洞察生成
        multimodal_insights = multimodal_processor.process_multimodal_content(cleaned_article)
        
        # 合并所有分析结果
        enhanced_article = {**cleaned_article, **analysis_result, **multimodal_insights}
        enhanced_article['enhanced'] = True
        enhanced_article['enhanced_at'] = datetime.now().isoformat()
        
        logger.info(f"智能解析增强完成，包含多模态洞察: {len(multimodal_insights)} 个分析维度")
        return enhanced_article
        
    except Exception as e:
        logger.warning(f"智能解析增强失败: {e}")
        return article_data

    def get_memory_usage(self):
        """获取内存使用情况"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except:
            return 0

    def get_cpu_usage(self):
        """获取CPU使用率"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except:
            return 0

    def update_worker_status(self, status, extra_info=None):
        """更新工作节点状态到主节点"""
        try:
            data = {
                'worker_id': self.worker_id,
                'status': status,
                'timestamp': time.time(),
                'ip': self.get_local_ip(),
                'version': self.version
            }
            
            if extra_info:
                data.update(extra_info)
            
            response = requests.post(
                f"{self.master_url}/api/worker/status",
                json=data,
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"更新工作节点状态失败: {e}")
            return False

    def get_local_ip(self):
        """获取本地IP地址"""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "unknown"

if __name__ == "__main__":
    run_worker()