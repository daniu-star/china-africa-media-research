#!/usr/bin/env python3
"""
分布式爬虫系统 - 修复版工作节点
专门解决Windows网络连接问题
"""

import os
import json
import time
import requests
import logging
import signal
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid
import threading
import random
import asyncio
from concurrent.futures import ThreadPoolExecutor
import html
import re  # 添加正则表达式模块导入
from urllib.parse import urlparse  # 添加URL解析模块导入
import socket  # 添加socket模块用于获取本地IP
import psutil  # 添加psutil模块用于获取系统资源使用率
from modernghana_optimizer import ModernGhanaOptimizer  # 导入Modern Ghana优化器
from advanced_anti_crawler import advanced_anti_crawler  # 导入高级反爬虫模块
from data_quality_optimizer import data_quality_optimizer  # 导入数据质量优化模块
from data_quality_management_system import DataQualityManagementSystem  # 导入数据质量管理系统
from smart_page_filter import SmartPageFilter  # 导入智能页面过滤器

# 配置日志 - 修复Unicode编码问题
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('distributed_worker_fixed.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置 - 优化网络连接设置
MASTER_URL = os.getenv('MASTER_URL', 'http://127.0.0.1:8000')
WORKER_ID = os.getenv('WORKER_ID', f'worker-fixed-{random.randint(1000, 9999)}')
CONNECTION_POOL_SIZE = int(os.getenv('CONNECTION_POOL_SIZE', 10))
POOL_BLOCK = os.getenv('POOL_BLOCK', 'False').lower() == 'true'

# 网络连接优化配置 - 与主节点保持一致
CONNECTION_TIMEOUT = 30  # 连接超时时间（秒）
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 60))  # 请求超时时间（秒）
HEARTBEAT_INTERVAL = int(os.getenv('HEARTBEAT_INTERVAL', 30))
TASK_PROCESSING_TIME = int(os.getenv('TASK_PROCESSING_TIME', 5))

# 重试配置
MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', 5))  # 增加到5次重试
RETRY_DELAY_BASE = int(os.getenv('RETRY_DELAY_BASE', 5))
RETRY_DELAY_MAX = int(os.getenv('RETRY_DELAY_MAX', 60))

# 主机绑定配置 - 解决Windows网络连接问题
HOST = "0.0.0.0"         # 绑定所有网络接口
WORKER_PORT = 5000       # 工作节点端口

class SimpleAntiCrawlerManager:
    """简单的反爬虫管理器 - 用于标记顽固网站"""
    
    def __init__(self):
        self.banned_sites = set()  # 被标记为顽固网站的域名集合
        self.banned_file = 'banned_sites.json'  # 保存被标记网站的JSON文件
        self.load_banned_sites()
    
    def load_banned_sites(self):
        """从文件加载被标记的网站"""
        try:
            if os.path.exists(self.banned_file):
                with open(self.banned_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.banned_sites = set(data.get('banned_sites', []))
                logger.info(f"加载了 {len(self.banned_sites)} 个被标记的顽固网站")
        except Exception as e:
            logger.warning(f"加载被标记网站文件失败: {e}")
    
    def save_banned_sites(self):
        """保存被标记的网站到文件"""
        try:
            data = {'banned_sites': list(self.banned_sites)}
            with open(self.banned_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存被标记网站文件失败: {e}")
    
    def is_site_banned(self, domain: str) -> bool:
        """检查网站是否被标记为顽固网站"""
        return domain in self.banned_sites
    
    def mark_site_as_banned(self, domain: str):
        """标记网站为顽固网站"""
        if domain not in self.banned_sites:
            self.banned_sites.add(domain)
            self.save_banned_sites()
            logger.warning(f"网站 {domain} 已被标记为顽固网站")
    
    def unmark_site_as_banned(self, domain: str):
        """取消标记网站为顽固网站"""
        if domain in self.banned_sites:
            self.banned_sites.remove(domain)
            self.save_banned_sites()
            logger.info(f"网站 {domain} 已从顽固网站列表中移除")

class ConnectionManager:
    """连接管理器 - 专门处理Windows网络连接问题"""
    
    def __init__(self):
        # 创建会话并配置连接池
        self.session = requests.Session()
        
        # 配置连接适配器
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=CONNECTION_POOL_SIZE,
            pool_maxsize=CONNECTION_POOL_SIZE,
            max_retries=3,
            pool_block=POOL_BLOCK
        )
        
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 连接统计
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'connection_errors': 0,
            'timeout_errors': 0,
            'last_error': None,
            'last_success': None
        }
        
        # 连接状态监控
        self.connection_healthy = True
        self.last_health_check = time.time()
        
        logger.info(f"连接管理器初始化完成 - 连接池大小: {CONNECTION_POOL_SIZE}")
    
    def make_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """发送HTTP请求，包含智能反爬虫策略和重试机制"""
        self.stats['total_requests'] += 1
        
        # 设置默认超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = REQUEST_TIMEOUT
        
        # 使用高级反爬虫模块获取优化的请求头
        anti_crawler_headers = advanced_anti_crawler.get_optimized_headers(url)
        
        # 合并请求头（用户自定义头优先）
        if 'headers' in kwargs:
            kwargs['headers'] = {**anti_crawler_headers, **kwargs['headers']}
        else:
            kwargs['headers'] = anti_crawler_headers
        
        # 重试机制
        for attempt in range(MAX_RETRY_ATTEMPTS + 1):
            try:
                # 计算智能延迟时间
                delay = advanced_anti_crawler.calculate_smart_delay(url, attempt)
                if delay > 0:
                    logger.info(f"智能延迟 {delay:.1f} 秒 (重试次数: {attempt})")
                    time.sleep(delay)
                
                response = self.session.request(method, url, **kwargs)
                
                # 处理反爬虫响应
                anti_crawler_action = advanced_anti_crawler.handle_anti_crawler_response(
                    url, response.status_code, dict(response.headers)
                )
                
                # 根据反爬虫策略决定下一步行动
                if anti_crawler_action['should_retry'] and attempt < MAX_RETRY_ATTEMPTS:
                    logger.warning(f"反爬虫检测: {url} - 状态码: {response.status_code} - 建议: {anti_crawler_action['recommendation']}")
                    
                    # 应用延迟
                    if anti_crawler_action['delay_before_retry'] > 0:
                        time.sleep(anti_crawler_action['delay_before_retry'])
                    
                    # 如果需要更换指纹，重新获取请求头
                    if anti_crawler_action['change_fingerprint']:
                        anti_crawler_headers = advanced_anti_crawler.get_optimized_headers(url)
                        if 'headers' in kwargs:
                            kwargs['headers'] = {**anti_crawler_headers, **kwargs['headers']}
                        else:
                            kwargs['headers'] = anti_crawler_headers
                    
                    continue
                
                # 检查响应状态
                if response.status_code < 500:  # 非服务器错误
                    self.stats['successful_requests'] += 1
                    self.stats['last_success'] = time.time()
                    self.connection_healthy = True
                    return response
                else:
                    # 服务器错误，需要重试
                    logger.warning(f"服务器错误 {response.status_code}，尝试 {attempt + 1}/{MAX_RETRY_ATTEMPTS}")
                    
            except requests.exceptions.ConnectionError as e:
                self.stats['connection_errors'] += 1
                self.stats['last_error'] = str(e)
                logger.warning(f"连接错误，尝试 {attempt + 1}/{MAX_RETRY_ATTEMPTS}: {e}")
                
            except requests.exceptions.Timeout as e:
                self.stats['timeout_errors'] += 1
                self.stats['last_error'] = str(e)
                logger.warning(f"请求超时，尝试 {attempt + 1}/{MAX_RETRY_ATTEMPTS}: {e}")
                
            except requests.exceptions.RequestException as e:
                self.stats['failed_requests'] += 1
                self.stats['last_error'] = str(e)
                logger.warning(f"请求异常，尝试 {attempt + 1}/{MAX_RETRY_ATTEMPTS}: {e}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < MAX_RETRY_ATTEMPTS:
                # 智能重试延迟计算
                error_type = None
                if 'response' in locals():
                    if response.status_code == 403:
                        error_type = '403'
                    elif response.status_code == 429:
                        error_type = '429'
                elif 'e' in locals():
                    if isinstance(e, requests.exceptions.ConnectionError):
                        error_type = 'connection_error'
                    elif isinstance(e, requests.exceptions.Timeout):
                        error_type = 'timeout'
                
                delay = self.calculate_retry_delay(attempt, error_type, url)
                logger.info(f"智能重试: 等待 {delay} 秒后重试 (错误类型: {error_type or 'unknown'})...")
                time.sleep(delay)
        
        # 所有重试都失败
        self.stats['failed_requests'] += 1
        self.connection_healthy = False
        logger.error(f"请求失败: {url}")
        return None
    
    def calculate_retry_delay(self, attempt: int, error_type: str = None, url: str = None) -> int:
        """计算智能重试延迟时间"""
        # 基础延迟
        base_delay = RETRY_DELAY_BASE
        
        # 基于错误类型的调整
        if error_type == 'connection_error':
            # 连接错误：较短延迟
            base_delay = max(1, base_delay * 0.8)
        elif error_type == 'timeout':
            # 超时错误：中等延迟
            base_delay = base_delay * 1.2
        elif error_type == '403':
            # 403错误：较长延迟，需要更多冷却时间
            base_delay = base_delay * 2.0
        elif error_type == '429':
            # 429错误：最长延迟，避免被进一步限制
            base_delay = base_delay * 3.0
        
        # 基于URL域名的智能调整
        if url:
            domain = url.replace('https://', '').replace('http://', '').split('/')[0]
            
            # 针对非洲高延迟网站的优化
            if any(african_domain in domain for african_domain in ['.co.za', '.co.ke', '.com.gh', '.ng']):
                # 非洲网站增加延迟容忍度
                base_delay = base_delay * 1.5
            
            # 针对Modern Ghana的特殊处理
            if 'modernghana.com' in domain:
                base_delay = base_delay * 2.0  # 更长的延迟
        
        # 指数退避算法，带随机抖动
        delay = min(base_delay * (2 ** attempt), RETRY_DELAY_MAX)
        jitter = random.uniform(0.8, 1.2)  # 减少抖动范围，更稳定
        
        return int(delay * jitter)
    
    def _get_adjusted_timeout(self, base_timeout: float, attempt: int, url: str) -> float:
        """获取调整后的超时时间"""
        # 基于尝试次数的调整
        timeout_multiplier = 1.0 + (attempt * 0.3)  # 每次尝试增加30%超时时间
        adjusted_timeout = base_timeout * timeout_multiplier
        
        # 基于URL域名的调整
        if url:
            domain = url.replace('https://', '').replace('http://', '').split('/')[0]
            
            # 针对非洲高延迟网站的优化
            if any(african_domain in domain for african_domain in ['.co.za', '.co.ke', '.com.gh', '.ng']):
                adjusted_timeout = adjusted_timeout * 1.5
            
            # 针对Modern Ghana的特殊处理
            if 'modernghana.com' in domain:
                adjusted_timeout = adjusted_timeout * 2.0
        
        # 最大超时限制
        max_timeout = 300.0  # 5分钟
        return min(adjusted_timeout, max_timeout)
    
    def check_connection_health(self) -> bool:
        """检查连接健康状态"""
        current_time = time.time()
        
        # 如果最近有成功请求，认为连接健康
        if (self.stats['last_success'] and 
            current_time - self.stats['last_success'] < 300):  # 5分钟内
            return True
        
        # 如果最近有错误，检查是否需要重新连接
        if (self.stats['last_error'] and 
            current_time - self.last_health_check > 60):  # 每分钟检查一次
            
            self.last_health_check = current_time
            
            # 尝试发送健康检查请求
            try:
                response = self.session.get(f"{MASTER_URL}/health", timeout=10)
                if response.status_code == 200:
                    self.connection_healthy = True
                    return True
            except:
                pass
            
            self.connection_healthy = False
        
        return self.connection_healthy
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        return self.stats.copy()
    
    def close(self):
        """关闭连接"""
        self.session.close()
        logger.info("连接已关闭")

class DistributedWorker:
    """分布式工作节点"""
    
    def __init__(self):
        self.worker_id = WORKER_ID
        self.connection_manager = ConnectionManager()
        self.modernghana_optimizer = ModernGhanaOptimizer()
        self.running = False
        self.current_task = None
        self.task_queue = []
        
        # 简单的反爬虫管理器 - 用于标记顽固网站
        self.anti_crawler_manager = SimpleAntiCrawlerManager()
        
        # 工作统计
        self.worker_stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_processing_time': 0,
            'last_task_completed': None,
            'start_time': time.time(),
            'response_times': [],  # 记录每个任务的响应时间
            'last_active': time.time(),  # 最后活动时间
            'success_rate': 1.0,  # 初始成功率设为100%
            'avg_response_time': 0.0  # 平均响应时间
        }
        
        # 线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=3)
        
        # 初始化数据质量管理系统
        self.data_quality_system = DataQualityManagementSystem("data/results")
        logger.info("数据质量管理系统初始化完成")
        
        # 初始化智能页面过滤器
        self.smart_page_filter = SmartPageFilter()
        logger.info("智能页面过滤器初始化完成")
        
        logger.info(f"工作节点 {self.worker_id} 初始化完成")
    
    def _select_smart_proxy_for_url(self, proxies: List[Dict], target_url: str = None) -> Optional[Dict]:
        """基于目标URL的智能代理选择策略 - 优化版"""
        if not proxies:
            return None
            
        # 过滤可用代理 - 更严格的筛选条件
        available_proxies = []
        current_time = time.time()
        
        for proxy in proxies:
            # 检查代理状态
            last_check = proxy.get('last_checked', 0)
            if isinstance(last_check, str):
                # 如果是字符串时间戳，转换为时间戳
                try:
                    last_check = datetime.fromisoformat(last_check.replace('Z', '+00:00')).timestamp()
                except:
                    last_check = 0
            
            success_rate = proxy.get('success_rate', 0)
            latency = proxy.get('latency', 300)  # 默认延迟300ms
            priority = proxy.get('priority', 'medium')
            
            # 更严格的筛选条件
            is_recent = current_time - last_check < 1800  # 30分钟内检查过
            is_high_success = success_rate > 0.75  # 成功率>75%
            is_low_latency = latency < 300  # 延迟<300ms
            
            # 根据优先级调整筛选条件
            if priority == 'high':
                # 高优先级代理：放宽条件
                if is_recent and success_rate > 0.65:
                    available_proxies.append(proxy)
            elif priority == 'medium':
                # 中优先级代理：标准条件
                if is_recent and is_high_success and is_low_latency:
                    available_proxies.append(proxy)
            else:
                # 低优先级代理：严格条件
                if is_recent and success_rate > 0.85 and latency < 200:
                    available_proxies.append(proxy)
        
        if not available_proxies:
            logger.warning("没有可用的高质量代理，将使用直连模式")
            return None
        
        # 非洲网站特殊处理 - 优化区域匹配
        if target_url and self._is_africa_website(target_url):
            # 获取网站所在地区
            target_region = self._detect_website_region(target_url)
            
            # 优先选择匹配地区的代理
            regional_proxies = [p for p in available_proxies if p.get('region') == target_region]
            if regional_proxies:
                # 按延迟和成功率综合排序
                regional_proxies.sort(key=lambda x: (x.get('latency', 300), -x.get('success_rate', 0)))
                selected_proxy = regional_proxies[0]
                logger.info(f"非洲网站检测到，选择区域优化代理: {selected_proxy['host']} (地区: {target_region}, 延迟: {selected_proxy.get('latency', 0)}ms)")
                return selected_proxy
            
            # 如果没有精确匹配，选择非洲地区代理
            africa_proxies = [p for p in available_proxies if p.get('country') in ['ZA', 'KE', 'NG', 'GH', 'EG']]
            if africa_proxies:
                # 按延迟和成功率综合排序
                africa_proxies.sort(key=lambda x: (x.get('latency', 300), -x.get('success_rate', 0)))
                selected_proxy = africa_proxies[0]
                logger.info(f"非洲网站检测到，选择非洲地区代理: {selected_proxy['host']} (延迟: {selected_proxy.get('latency', 0)}ms)")
                return selected_proxy
        
        # 通用代理选择策略：按延迟和成功率综合排序
        available_proxies.sort(key=lambda x: (x.get('latency', 300), -x.get('success_rate', 0)))
        
        # 选择最优代理
        best_proxy = available_proxies[0]
        logger.info(f"智能代理选择: {best_proxy['host']} (成功率: {best_proxy.get('success_rate', 0):.2f}, 延迟: {best_proxy.get('latency', 0)}ms)")
        
        return best_proxy
    
    def _detect_website_region(self, url: str) -> str:
        """检测网站所在地区"""
        try:
            domain = url.replace('https://', '').replace('http://', '').split('/')[0]
            
            # 南非网站
            if any(tld in domain for tld in ['.co.za', '.za']):
                return 'south_africa'
            
            # 东非网站
            if any(tld in domain for tld in ['.co.ke', '.ke', '.ug', '.tz']):
                return 'east_africa'
            
            # 西非网站
            if any(tld in domain for tld in ['.com.gh', '.gh', '.ng', '.com.ng']):
                return 'west_africa'
            
            # 北非网站
            if any(tld in domain for tld in ['.eg', '.ma', '.dz', '.tn']):
                return 'north_africa'
            
            return 'unknown'
        except:
            return 'unknown'

    def _is_africa_website(self, url: str) -> bool:
        """判断是否为非洲网站"""
        try:
            # 非洲国家顶级域名列表
            africa_tlds = {
                '.ss', '.bi', '.dj', '.er', '.et', '.ke', '.km', '.mg', '.mw', '.mu', '.yt', 
                '.mz', '.re', '.rw', '.sc', '.so', '.tz', '.ug', '.zm', '.zw', '.ao', '.cf', 
                '.cg', '.cd', '.gq', '.ga', '.st', '.td', '.ne', '.bj', '.bf', '.ci', '.gw', 
                '.ml', '.mr', '.sn', '.tg', '.gh', '.gn', '.lr', '.ng', '.sl', '.cm', '.cv', 
                '.gm', '.sh', '.ly', '.tn', '.dz', '.eh', '.ma', '.sd', '.eg', '.et'
            }
            
            # 非洲相关关键词
            africa_keywords = {
                'africa', 'southafrica', 'northafrica', 'westafrica', 'eastafrica',
                'centralafrica', 'subsaharan', 'african', 'nigeria', 'kenya', 'ghana',
                'ethiopia', 'tanzania', 'uganda', 'zimbabwe', 'zambia', 'mozambique',
                'angola', 'cameroon', 'congo', 'senegal', 'mali', 'morocco', 'algeria',
                'tunisia', 'libya', 'egypt', 'sudan', 'somalia', 'rwanda', 'burundi'
            }
            
            # 解析URL
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # 检查顶级域名
            for tld in africa_tlds:
                if domain.endswith(tld):
                    return True
            
            # 检查域名中的关键词
            for keyword in africa_keywords:
                if keyword in domain:
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"非洲网站检测失败: {e}")
            return False
    
    def get_rotating_headers(self, url: str = None) -> Dict[str, str]:
        """获取轮换的请求头，模拟真实浏览器行为 - 公共方法"""
        return self._get_rotating_headers(url)
    
    def _get_rotating_headers(self, url: str = None) -> Dict[str, str]:
        """获取轮换的请求头，模拟真实浏览器行为"""
        # 基础请求头模板
        base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # 用户代理轮换池
        user_agents = [
            # Chrome Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            
            # Firefox Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            
            # Safari macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            
            # Edge Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        ]
        
        # 根据URL选择不同的用户代理策略
        if url and self._is_africa_website(url):
            # 非洲网站：使用更保守的用户代理
            user_agent_index = hash(url) % len(user_agents)
        else:
            # 其他网站：随机轮换
            user_agent_index = random.randint(0, len(user_agents) - 1)
        
        headers = base_headers.copy()
        headers['User-Agent'] = user_agents[user_agent_index]
        
        # 添加Referer头（如果可能）
        if url:
            headers['Referer'] = self._generate_referer(url)
        
        return headers
    
    def _generate_referer(self, url: str) -> str:
        """生成合理的Referer头"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # 生成合理的来源页面
            referers = [
                f"https://www.google.com/search?q={domain.replace('.', '+')}",
                f"https://{domain}",
                f"https://{domain}/news",
                f"https://{domain}/home",
                f"https://{domain}/index.html"
            ]
            
            return random.choice(referers)
        except:
            return f"https://www.google.com"
    
    def _simulate_human_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """模拟人类浏览延迟"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        
        # 偶尔添加更长的延迟（模拟阅读时间）
        if random.random() < 0.1:  # 10%的概率
            extra_delay = random.uniform(2.0, 5.0)
            time.sleep(extra_delay)

    def get_proxies(self, target_url: str = None) -> Dict[str, str]:
        """获取代理配置 - 智能代理选择和非洲网站特殊处理"""
        try:
            # 加载代理配置
            proxy_config_file = 'proxy_config.json'
            if os.path.exists(proxy_config_file):
                with open(proxy_config_file, 'r', encoding='utf-8') as f:
                    proxy_config = json.load(f)
                
                # 获取代理服务器列表
                proxies = proxy_config.get('proxies', [])
                if proxies:
                    # 智能代理选择策略
                    selected_proxy = self._select_smart_proxy_for_url(proxies, target_url)
                    
                    if selected_proxy:
                        proxy_url = f"http://{selected_proxy['host']}:{selected_proxy['port']}"
                        
                        # 设置代理
                        proxy_dict = {
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
                        
                        return proxy_dict
                    else:
                        logger.warning("智能代理选择失败，将使用直连模式")
                        return {}
                else:
                    logger.warning("代理配置文件中没有可用的代理服务器")
                    return {}
            else:
                logger.warning(f"代理配置文件不存在: {proxy_config_file}")
                return {}
        except Exception as e:
            logger.warning(f"代理配置失败: {e}，将使用直连模式")
            return {}

    def send_heartbeat(self):
        """发送心跳到主节点 - 优化版，包含系统资源监控"""
        # 使用update_worker_status方法获取完整的状态信息
        heartbeat_data = self.update_worker_status()
        
        # 确保包含主节点期望的字段
        heartbeat_data['timestamp'] = datetime.now().isoformat()
        
        response = self.connection_manager.make_request(
            'POST', 
            f"{MASTER_URL}/workers/heartbeat",
            json=heartbeat_data
        )
        
        if response and response.status_code == 200:
            logger.debug(f"心跳发送成功 - CPU: {heartbeat_data['load']['cpu_percent']:.1f}%, 内存: {heartbeat_data['load']['memory_usage']['percent']:.1f}%")
            return True
        else:
            logger.warning(f"心跳发送失败")
            return False
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """从主节点获取下一个任务"""
        response = self.connection_manager.make_request(
            'GET', 
            f"{MASTER_URL}/tasks/next?worker_id={self.worker_id}"
        )
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success' and data.get('task'):
                task = data['task']
                logger.info(f"获取到任务: {task.get('keyword', 'Unknown')}")
                return task
        
        return None
    
    def is_search_page(self, url: str) -> bool:
        """判断URL是否为搜索页面"""
        search_patterns = [
            r'/search',
            r'\?q=',
            r'\?s=',
            r'\?query=',
            r'\?keyword=',
            r'\?search=',
            r'/results',
            r'/find',
            r'/query',
            r'/lookup'
        ]
        
        for pattern in search_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False
    
    def extract_article_links(self, html_content: str, base_url: str) -> List[str]:
        """从搜索结果页面提取具体文章链接"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            article_links = []
            
            # 针对不同网站的特定URL模式
            site_patterns = {
                'allafrica.com': [
                    r'/stories/.*\.html',
                    r'/view/.*',
                    r'/news/.*'
                ],
                'news24.com': [
                    r'/Africa/News/.*',
                    r'/News24/.*',
                    r'/article/.*'
                ],
                'modernghana.com': [
                    r'/news/.*',
                    r'/article/.*',
                    r'/story/.*'
                ],
                'ghanaweb.com': [
                    r'/GhanaHomePage/.*',
                    r'/newsarchive/.*',
                    r'/article/.*'
                ],
                'punchng.com': [
                    r'/.*/.*',
                    r'/news/.*',
                    r'/article/.*'
                ]
            }
            
            # 获取基础域名
            domain = base_url.replace('https://', '').replace('http://', '').split('/')[0]
            
            # 查找所有链接
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                
                # 处理相对路径
                if href.startswith('/'):
                    href = f"https://{domain}{href}"
                elif not href.startswith('http'):
                    continue
                
                # 检查是否为文章链接
                is_article_link = False
                
                # 检查特定网站模式
                for site_domain, patterns in site_patterns.items():
                    if site_domain in domain:
                        for pattern in patterns:
                            if re.search(pattern, href, re.IGNORECASE):
                                is_article_link = True
                                break
                        if is_article_link:
                            break
                
                # 通用文章链接模式
                if not is_article_link:
                    article_patterns = [
                        r'/news/',
                        r'/article/',
                        r'/story/',
                        r'/202[0-9]/',  # 年份模式
                        r'/\d{4}/\d{2}/\d{2}/'  # 日期模式
                    ]
                    
                    for pattern in article_patterns:
                        if re.search(pattern, href, re.IGNORECASE):
                            is_article_link = True
                            break
                
                if is_article_link and href not in article_links:
                    article_links.append(href)
            
            # 去重并限制数量
            article_links = list(set(article_links))
            article_links = article_links[:10]  # 最多10篇文章
            
            logger.info(f"从搜索结果中提取到 {len(article_links)} 篇文章链接")
            return article_links
            
        except Exception as e:
            logger.error(f"提取文章链接失败: {e}")
            return []
    
    def crawl_search_page_and_extract_articles(self, search_url: str, keyword: str, year: int, max_attempts: int = 3) -> List[Dict[str, Any]]:
        """爬取搜索页面并提取具体文章"""
        try:
            logger.info(f"开始处理搜索页面: {search_url}")
            
            # 使用智能请求头生成方法
            headers = self.get_rotating_headers(search_url)
            
            # 爬取搜索页面
            search_response = self.connection_manager.session.get(
                search_url,
                headers=headers,
                timeout=(30, 60)
            )
            
            if search_response.status_code != 200:
                logger.warning(f"搜索页面爬取失败: {search_response.status_code}")
                return []
            
            # 提取文章链接
            article_links = self.extract_article_links(search_response.text, search_url)
            
            if not article_links:
                logger.warning(f"未从搜索页面提取到文章链接")
                return []
            
            # 爬取具体文章
            articles = []
            for article_url in article_links:
                logger.info(f"开始爬取具体文章: {article_url}")
                
                # 递归调用crawl_url方法爬取具体文章
                article_results = self.crawl_url(article_url, keyword, year, max_attempts)
                
                if article_results:
                    articles.extend(article_results)
                
                # 文章间延迟
                time.sleep(random.uniform(2.0, 4.0))
            
            logger.info(f"成功从搜索页面提取并爬取 {len(articles)} 篇具体文章")
            return articles
            
        except Exception as e:
            logger.error(f"处理搜索页面失败: {e}")
            return []
    
    def crawl_url(self, url: str, keyword: str, year: int, max_attempts: int = 5) -> List[Dict[str, Any]]:
        """爬取单个URL - 增强版支持搜索页面自动提取文章链接"""
        try:
            # 检查是否为搜索页面
            if self.is_search_page(url):
                logger.info(f"检测到搜索页面，自动提取具体文章链接: {url}")
                return self.crawl_search_page_and_extract_articles(url, keyword, year, max_attempts)
            
            logger.info(f"开始爬取URL: {url} (最大尝试次数: {max_attempts})")
            
            # 检查网站是否被标记为顽固网站
            domain = url.replace('https://', '').replace('http://', '').split('/')[0]
            if self.anti_crawler_manager.is_site_banned(domain):
                logger.warning(f"网站 {domain} 被标记为顽固网站，跳过爬取")
                return []
            
            # 检查是否为Modern Ghana网站，应用专用优化策略
            if self.modernghana_optimizer.is_modernghana_url(url):
                connect_timeout, read_timeout = self.modernghana_optimizer.calculate_smart_timeout(url)
                timeout = (connect_timeout, read_timeout)
                logger.info(f"Modern Ghana网站专用优化: 连接{connect_timeout}秒, 读取{read_timeout}秒")
            else:
                # 动态超时设置 - 优化超时时间（针对非洲网站优化）
                timeout = (30, 60)  # 连接超时30秒，读取超时60秒（针对非洲网站增加）
            
            # 智能重试机制 - 根据错误类型调整重试策略
            if self.modernghana_optimizer.is_modernghana_url(url):
                max_retries = self.modernghana_optimizer.optimization_config['max_retries']
                logger.info(f"Modern Ghana网站专用重试策略: 最大重试{max_retries}次")
            else:
                max_retries = max_attempts  # 使用传入的最大尝试次数
            
            for attempt in range(max_attempts):
                try:
                    # 智能延迟策略 - 根据尝试次数动态调整
                    if attempt == 0:
                        if self.modernghana_optimizer.is_modernghana_url(url):
                            delay_time = self.modernghana_optimizer.calculate_smart_delay(url, attempt)
                        else:
                            delay_time = random.uniform(1.0, 3.0)  # 首次尝试延迟1-3秒
                    else:
                        if self.modernghana_optimizer.is_modernghana_url(url):
                            delay_time = self.modernghana_optimizer.calculate_smart_delay(url, attempt)
                        else:
                            delay_time = random.uniform(2.0, 5.0)  # 重试时延迟2-5秒
                    
                    logger.info(f"第{attempt + 1}次尝试，等待 {delay_time:.1f} 秒后开始")
                    time.sleep(delay_time)
                        
                    # 智能请求头生成 - 根据网站类型使用不同策略
                    if self.modernghana_optimizer.is_modernghana_url(url):
                        # Modern Ghana网站专用请求头
                        headers = self.modernghana_optimizer.get_optimized_headers(url)
                        logger.info("使用Modern Ghana网站专用请求头")
                    else:
                        # 使用智能请求头生成方法
                        headers = self.get_rotating_headers(url)
                        logger.info("使用智能轮换请求头")
                    
                    # 智能代理配置 - 根据目标URL智能选择代理
                    proxies = self.get_proxies(url)
                    
                    # 执行请求 - 使用直接连接
                    logger.info(f"发送请求到 {url} (超时: {timeout}秒)")
                    try:
                        response = self.connection_manager.session.get(url, headers=headers, timeout=timeout)
                        response.raise_for_status()
                    except requests.exceptions.ConnectTimeout:
                        logger.warning(f"连接超时，尝试 {attempt + 1}/{max_attempts}")
                        if attempt < max_attempts - 1:
                            continue
                        else:
                            logger.error(f"达到最大尝试次数 {max_attempts}，放弃爬取")
                            return []
                    except requests.exceptions.ReadTimeout:
                        logger.warning(f"读取超时，尝试 {attempt + 1}/{max_attempts}")
                        if attempt < max_attempts - 1:
                            continue
                        else:
                            logger.error(f"达到最大尝试次数 {max_attempts}，放弃爬取")
                            return []
                    except requests.exceptions.ConnectionError as e:
                        logger.warning(f"连接错误: {str(e)}，尝试 {attempt + 1}/{max_attempts}")
                        if attempt < max_attempts - 1:
                            continue
                        else:
                            logger.error(f"达到最大尝试次数 {max_attempts}，放弃爬取")
                            return []
                    except requests.exceptions.HTTPError as e:
                        # 检查响应状态 - 使用高级反爬虫模块智能处理
                        if hasattr(e.response, 'status_code'):
                            status_code = e.response.status_code
                            logger.warning(f"HTTP状态码异常: {status_code}")
                            
                            # 使用高级反爬虫模块处理响应
                            anti_crawler_action = advanced_anti_crawler.handle_anti_crawler_response(
                                url, status_code, dict(e.response.headers)
                            )
                            
                            logger.info(f"高级反爬虫处理建议: {anti_crawler_action['recommendation']}")
                            
                            # 根据反爬虫策略决定下一步行动
                            if anti_crawler_action['should_retry'] and attempt < max_attempts - 1:
                                # 应用智能延迟
                                if anti_crawler_action['delay_before_retry'] > 0:
                                    delay = anti_crawler_action['delay_before_retry']
                                    logger.info(f"智能延迟 {delay:.1f} 秒后重试")
                                    time.sleep(delay)
                                
                                # 如果需要更换指纹，重新生成请求头
                                if anti_crawler_action['change_fingerprint']:
                                    logger.info("更换浏览器指纹和User-Agent")
                                    anti_crawler_headers = advanced_anti_crawler.get_optimized_headers(url)
                                    headers = {**anti_crawler_headers, **headers}
                                
                                continue
                            
                            # 如果检测到封禁，标记网站
                            if anti_crawler_action['ban_detected']:
                                logger.error(f"网站 {url} 检测到封禁，放弃爬取")
                                domain = url.replace('https://', '').replace('http://', '').split('/')[0]
                                self.anti_crawler_manager.mark_site_as_banned(domain)
                                return []
                            
                            # 其他情况继续重试
                            if attempt < max_attempts - 1:
                                continue
                            else:
                                logger.error(f"达到最大尝试次数 {max_attempts}，放弃爬取")
                                return []
                        else:
                            if attempt < max_attempts - 1:
                                continue
                            else:
                                logger.error(f"达到最大尝试次数 {max_attempts}，放弃爬取")
                                return []
                    
                    # 检查内容类型
                    content_type = response.headers.get('content-type', '')
                    if 'text/html' not in content_type:
                        logger.warning(f"非HTML内容类型: {content_type}")
                        if attempt < max_attempts - 1:
                            continue
                        else:
                            logger.error(f"达到最大尝试次数 {max_attempts}，放弃爬取")
                            return []
                    
                    # 处理编码问题
                    content = response.text
                    if not content:
                        content = response.content
                        if isinstance(content, bytes):
                            try:
                                content = content.decode('utf-8')
                            except UnicodeDecodeError:
                                try:
                                    content = content.decode('latin-1')
                                except UnicodeDecodeError:
                                    content = str(content)
                    
                    # 智能反爬虫检测
                    anti_crawler_result = {
                        'detected': False,
                        'type': None,
                        'confidence': 0.0
                    }
                    
                    # 检查常见反爬虫标记
                    anti_crawler_keywords = ['access denied', 'bot detected', 'captcha', 'cloudflare', '403 forbidden']
                    if any(keyword in content.lower() for keyword in anti_crawler_keywords):
                        anti_crawler_result = {
                            'detected': True,
                            'type': 'waf_detected',
                            'confidence': 0.8
                        }
                    
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
                        'content': self.extract_content_from_html(content, url),
                        'source': url.split('//')[1].split('/')[0] if '//' in url else url,
                        'publish_date': self.extract_date_from_html(content, url),
                        'keyword': keyword,
                        'year': year,
                        'crawl_time': datetime.now().isoformat(),
                        'crawl_method': 'traditional',
                        'anti_crawler_detected': anti_crawler_result['detected'],
                        'anti_crawler_type': anti_crawler_result['type'] if anti_crawler_result['detected'] else None
                    }
                    
                    logger.info(f"成功爬取文章: {article['title']}")
                    
                    # 更新Modern Ghana优化器性能统计
                    if self.modernghana_optimizer.is_modernghana_url(url):
                        self.modernghana_optimizer.update_performance_stats(
                            success=True, 
                            response_time=time.time() - start_time
                        )
                    
                    return [article]
                    
                except Exception as e:
                    logger.error(f"第{attempt + 1}次尝试失败: {url}, 错误: {e}")
                    
                    # 更新Modern Ghana优化器性能统计（错误情况）
                    if self.modernghana_optimizer.is_modernghana_url(url):
                        error_type = 'unknown'
                        if isinstance(e, requests.exceptions.Timeout):
                            error_type = 'timeout'
                        elif isinstance(e, requests.exceptions.ConnectionError):
                            error_type = 'connection'
                        elif isinstance(e, requests.exceptions.RequestException):
                            error_type = 'request'
                        
                        self.modernghana_optimizer.update_performance_stats(
                            success=False, 
                            response_time=time.time() - start_time,
                            error_type=error_type
                        )
                    
                    # 如果是最后一次尝试，直接返回空结果
                    if attempt == max_attempts - 1:
                        logger.error(f"达到最大尝试次数，放弃爬取")
                        return []
                    
                    # 等待后重试
                    wait_time = random.uniform(5.0, 15.0)
                    logger.info(f"等待 {wait_time:.1f} 秒后重试")
                    time.sleep(wait_time)
            
            return []
            
        except Exception as e:
            logger.error(f"爬取URL失败: {url}, 错误: {e}")
            return []
    
    def extract_title_from_html(self, html_content: str, url: str) -> str:
        """从HTML内容中提取标题"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 尝试多种标题选择器
            title_selectors = [
                'h1', 'h2', '.title', '.headline', '.article-title',
                'meta[property="og:title"]', 'meta[name="title"]'
            ]
            
            for selector in title_selectors:
                if selector.startswith('meta'):
                    meta_tag = soup.select_one(selector)
                    if meta_tag and meta_tag.get('content'):
                        return meta_tag['content'].strip()
                else:
                    title_element = soup.select_one(selector)
                    if title_element:
                        return title_element.get_text(strip=True)
            
            # 如果找不到标题，使用URL作为标题
            return f"来自 {url.split('//')[1].split('/')[0]} 的文章"
            
        except Exception as e:
            logger.warning(f"提取标题失败: {e}")
            return f"来自 {url.split('//')[1].split('/')[0]} 的文章"
    
    def extract_content_from_html(self, html_content: str, url: str) -> str:
        """从HTML内容中提取正文 - 增强版数据质量优化"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 尝试多种内容选择器
            content_selectors = [
                '.article-content', '.content', '.post-content', '.entry-content',
                '.story-content', '.news-content', '.main-content', 'article',
                '.news-body', '.article-body', '.story-body', '.post-body'
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    # 清理内容，移除脚本和样式
                    for script in content_element(['script', 'style', 'nav', 'header', 'footer']):
                        script.decompose()
                    
                    content = content_element.get_text(separator='\n', strip=True)
                    
                    # 数据质量优化：清理HTML标签和无关内容
                    content = self.clean_content_quality(content)
                    
                    if len(content) > 100:  # 确保有足够的内容
                        return content
            
            # 如果找不到特定内容区域，提取所有文本
            for script in soup(['script', 'style', 'nav', 'header', 'footer']):
                script.decompose()
            
            content = soup.get_text(separator='\n', strip=True)
            
            # 数据质量优化：清理HTML标签和无关内容
            content = self.clean_content_quality(content)
            
            return content if len(content) > 50 else "内容提取失败"
            
        except Exception as e:
            logger.warning(f"提取内容失败: {e}")
            return "内容提取失败"
    
    def clean_content_quality(self, content: str) -> str:
        """清理内容质量 - 移除HTML标签、无关导航内容等"""
        
        # 移除HTML标签
        content = re.sub(r'<[^>]+>', '', content)
        
        # 移除常见的导航和无关文本
        navigation_patterns = [
            r'首页|主页|Home',
            r'联系我们|Contact Us',
            r'关于我们|About Us',
            r'隐私政策|Privacy Policy',
            r'使用条款|Terms of Use',
            r'版权声明|Copyright',
            r'返回顶部|Back to Top',
            r'分享到|Share on',
            r'阅读更多|Read More',
            r'下一页|Next Page',
            r'上一页|Previous Page'
        ]
        
        for pattern in navigation_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # 移除多余的空行和空格
        content = re.sub(r'\n\s*\n', '\n', content)
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        # 移除短行（可能是不完整的句子）
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            if len(line.strip()) > 20:  # 保留长度超过20个字符的行
                cleaned_lines.append(line.strip())
        
        content = '\n'.join(cleaned_lines)
        
        return content
    
    def extract_date_from_html(self, html_content: str, url: str) -> str:
        """从HTML内容中提取发布日期 - 增强版日期智能处理"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 尝试多种日期选择器
            date_selectors = [
                'time', '.date', '.publish-date', '.post-date', '.article-date',
                'meta[property="article:published_time"]', 'meta[name="publish_date"]',
                'meta[property="og:published_time"]', 'meta[name="DC.date.issued"]',
                '.timestamp', '.post-time', '.article-time', '.news-date'
            ]
            
            extracted_dates = []
            
            for selector in date_selectors:
                if selector.startswith('meta'):
                    meta_tag = soup.select_one(selector)
                    if meta_tag and meta_tag.get('content'):
                        date_text = meta_tag['content'].strip()
                        extracted_dates.append(date_text)
                else:
                    date_elements = soup.select(selector)
                    for date_element in date_elements:
                        date_text = date_element.get_text(strip=True)
                        if date_text:
                            extracted_dates.append(date_text)
            
            # 智能日期解析和验证
            best_date = self.validate_and_normalize_date(extracted_dates, url)
            
            if best_date:
                return best_date
            else:
                # 如果找不到有效日期，使用当前时间
                return datetime.now().isoformat()
            
        except Exception as e:
            logger.warning(f"提取日期失败: {e}")
            return datetime.now().isoformat()
    
    def validate_and_normalize_date(self, date_candidates: List[str], url: str) -> str:
        """验证和标准化日期 - 确保日期格式正确且合理"""
        from datetime import datetime
        
        # 日期格式模式
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
            r'\d{1,2}\s+\w+\s+\d{4}',  # DD Month YYYY
            r'\w+\s+\d{1,2},?\s+\d{4}',  # Month DD, YYYY
        ]
        
        valid_dates = []
        
        for candidate in date_candidates:
            # 清理日期字符串
            candidate = re.sub(r'[^\w\s/:-]', '', candidate)
            
            # 尝试匹配各种日期格式
            for pattern in date_patterns:
                matches = re.findall(pattern, candidate)
                for match in matches:
                    try:
                        # 尝试解析日期
                        if '-' in match and len(match) == 10:
                            parsed_date = datetime.strptime(match, '%Y-%m-%d')
                        elif '/' in match and len(match) == 10:
                            if match.count('/') == 2:
                                if match[:4].isdigit():  # YYYY/MM/DD
                                    parsed_date = datetime.strptime(match, '%Y/%m/%d')
                                else:  # MM/DD/YYYY
                                    parsed_date = datetime.strptime(match, '%m/%d/%Y')
                        else:
                            # 尝试其他格式
                            for fmt in ['%d %B %Y', '%B %d, %Y', '%b %d, %Y']:
                                try:
                                    parsed_date = datetime.strptime(match, fmt)
                                    break
                                except ValueError:
                                    continue
                        
                        # 验证日期合理性（不能是未来日期）
                        if parsed_date <= datetime.now():
                            # 标准化为ISO格式
                            normalized_date = parsed_date.isoformat()
                            valid_dates.append((normalized_date, parsed_date))
                            
                    except (ValueError, AttributeError):
                        continue
        
        # 选择最合理的日期（最近的日期）
        if valid_dates:
            # 按日期排序，选择最新的
            valid_dates.sort(key=lambda x: x[1], reverse=True)
            return valid_dates[0][0]
        
        return None
    
    def validate_article_quality(self, article: Dict[str, Any], target_year: int) -> tuple:
        """验证文章质量 - 使用数据质量优化模块进行智能质量评估"""
        
        try:
            # 使用数据质量优化模块进行质量评估
            quality_result = data_quality_optimizer.validate_article_quality(article)
            
            # 获取质量分数和问题列表
            quality_score = quality_result.get('quality_score', 0)
            quality_issues = quality_result.get('quality_issues', [])
            is_valid = quality_result.get('is_valid', False)
            
            # 额外检查年份一致性（数据质量模块可能未包含此检查）
            publish_date = article.get('publish_date', '')
            if publish_date:
                try:
                    # 提取年份
                    year_match = re.search(r'\b(\d{4})\b', publish_date)
                    if year_match:
                        article_year = int(year_match.group(1))
                        # 检查年份是否与目标年份匹配
                        if abs(article_year - target_year) > 1:  # 允许±1年的误差
                            quality_issues.append(f"年份不匹配: 目标{target_year}, 实际{article_year}")
                            # 如果年份不匹配，降低质量分数
                            quality_score = max(0, quality_score - 0.3)
                except (ValueError, AttributeError):
                    quality_issues.append("日期格式无效")
                    quality_score = max(0, quality_score - 0.2)
            
            # 根据质量分数重新判断有效性
            # 质量分数阈值：0.15分以上为有效文章（进一步降低阈值以适应非洲新闻数据特点）
            final_is_valid = is_valid and quality_score >= 0.15
            
            # 放宽年份检查：如果质量分数较高，允许更大的年份误差
            if quality_score >= 0.6 and abs(article_year - target_year) <= 5:  # 高质量文章允许±5年误差
                # 移除年份不匹配的问题
                quality_issues = [issue for issue in quality_issues if not issue.startswith("年份不匹配")]
                final_is_valid = True
            
            # 添加质量分数到问题列表
            quality_issues.append(f"质量分数: {quality_score:.2f}")
            
            return final_is_valid, quality_issues
            
        except Exception as e:
            # 如果数据质量模块失败，回退到原有逻辑
            logger.warning(f"数据质量优化模块调用失败: {e}，使用原有质量验证逻辑")
            
            # 原有质量验证逻辑
            quality_issues = []
            
            # 1. 检查必填字段
            required_fields = ['title', 'content', 'publish_date', 'source']
            for field in required_fields:
                if not article.get(field):
                    quality_issues.append(f"缺失必填字段: {field}")
            
            # 2. 检查内容长度
            content = article.get('content', '')
            if len(content.strip()) < 50:  # 降低内容长度要求至50字符
                quality_issues.append(f"内容过短: {len(content)} 字符")
            
            # 3. 检查HTML标签
            if '<' in content and '>' in content:
                # 检查是否包含过多HTML标签
                html_tags = re.findall(r'<[^>]+>', content)
                if len(html_tags) > 10:  # 如果超过10个HTML标签
                    quality_issues.append("包含过多HTML标签")
            
            # 4. 检查时间一致性
            publish_date = article.get('publish_date', '')
            if publish_date:
                try:
                    # 提取年份
                    year_match = re.search(r'\b(\d{4})\b', publish_date)
                    if year_match:
                        article_year = int(year_match.group(1))
                        # 放宽年份检查：允许±3年的误差
                        if abs(article_year - target_year) > 3:  
                            quality_issues.append(f"年份不匹配: 目标{target_year}, 实际{article_year}")
                except (ValueError, AttributeError):
                    quality_issues.append("日期格式无效")
            
            # 5. 检查标题质量
            title = article.get('title', '')
            if len(title.strip()) < 3:  # 降低标题长度要求
                quality_issues.append("标题过短")
            
            # 6. 检查重复内容
            if content and title:
                # 检查标题是否出现在内容中（可能是重复）
                if title.lower() in content.lower()[:200]:
                    quality_issues.append("标题与内容重复")
            
            # 7. 检查导航文本
            navigation_keywords = ['home', 'menu', 'navigation', 'sidebar', 'footer', 'header']
            if any(keyword in content.lower() for keyword in navigation_keywords):
                quality_issues.append("可能包含导航文本")
            
            # 8. 检查反爬虫检测
            if article.get('waf_detected', False):
                quality_issues.append("检测到反爬虫机制")
            
            # 判断文章是否有效
            # 放宽标准：允许最多3个轻微问题，且内容长度要求降低
            is_valid = len(quality_issues) <= 3  # 允许最多3个轻微问题
            
            return is_valid, quality_issues
    
    def clean_and_normalize_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """清理和标准化文章数据 - 使用数据质量优化模块进行智能清理"""
        
        try:
            # 使用数据质量优化模块进行智能清理
            cleaned_result = data_quality_optimizer.clean_content_quality(article)
            
            # 获取清理后的文章数据
            cleaned_article = cleaned_result.get('cleaned_article', article.copy())
            
            # 确保包含必要的元数据
            if 'title' not in cleaned_article and 'title' in article:
                cleaned_article['title'] = article['title']
            if 'content' not in cleaned_article and 'content' in article:
                cleaned_article['content'] = article['content']
            if 'publish_date' not in cleaned_article and 'publish_date' in article:
                cleaned_article['publish_date'] = article['publish_date']
            if 'source' not in cleaned_article and 'source' in article:
                cleaned_article['source'] = article['source']
            
            # 标准化日期格式（数据质量模块可能未处理）
            if 'publish_date' in cleaned_article:
                try:
                    date_str = cleaned_article['publish_date']
                    # 如果是ISO格式，保持原样
                    if not re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', date_str):
                        # 尝试解析并重新格式化为ISO
                        parsed_date = self.validate_and_normalize_date([date_str], '')
                        if parsed_date:
                            cleaned_article['publish_date'] = parsed_date
                except Exception:
                    pass  # 保持原样
            
            # 添加质量标记
            cleaned_article['quality_checked'] = True
            cleaned_article['cleaned_at'] = datetime.now().isoformat()
            cleaned_article['cleaned_by'] = 'data_quality_optimizer'
            
            return cleaned_article
            
        except Exception as e:
            # 如果数据质量模块失败，回退到原有逻辑
            logger.warning(f"数据质量优化模块清理失败: {e}，使用原有清理逻辑")
            
            cleaned_article = article.copy()
            
            # 1. 清理标题
            if 'title' in cleaned_article:
                cleaned_article['title'] = self.clean_content_quality(cleaned_article['title'])
            
            # 2. 清理内容
            if 'content' in cleaned_article:
                cleaned_article['content'] = self.clean_content_quality(cleaned_article['content'])
            
            # 3. 标准化日期格式
            if 'publish_date' in cleaned_article:
                try:
                    # 尝试标准化日期格式
                    date_str = cleaned_article['publish_date']
                    # 如果是ISO格式，保持原样
                    if not re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', date_str):
                        # 尝试解析并重新格式化为ISO
                        parsed_date = self.validate_and_normalize_date([date_str], '')
                        if parsed_date:
                            cleaned_article['publish_date'] = parsed_date
                except Exception:
                    pass  # 保持原样
            
            # 4. 添加质量标记
            cleaned_article['quality_checked'] = True
            cleaned_article['cleaned_at'] = datetime.now().isoformat()
            cleaned_article['cleaned_by'] = 'legacy_method'
            
            return cleaned_article
    
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理爬虫任务 - 优化版爬取逻辑"""
        start_time = time.time()
        
        try:
            keyword = task.get('keyword', '')
            task_id = task.get('task_id', '')
            year = task.get('year', 2024)
            
            logger.info(f"开始处理任务: {keyword} (ID: {task_id}, 年份: {year})")
            
            # 生成真实的非洲新闻网站URL
            african_news_sites = [
                'https://allafrica.com',
                'https://www.news24.com',
                'https://www.nation.co.ke',
                'https://www.punchng.com',
                'https://www.vanguardngr.com',
                'https://www.thisdaylive.com',
                'https://guardian.ng',
                'https://www.modernghana.com',
                'https://www.liberianobserver.com',
                'https://www.newsghana.com.gh'
            ]
            
            # 智能网站选择策略 - 优先选择响应速度快的网站
            prioritized_sites = self.prioritize_sites(african_news_sites)
            
            # 爬取多个网站，提高成功率
            max_sites_per_task = 3  # 限制每个任务最多爬取3个网站
            all_results = []
            
            for i, base_url in enumerate(prioritized_sites[:max_sites_per_task]):
                logger.info(f"爬取第 {i + 1}/{min(len(prioritized_sites), max_sites_per_task)} 个网站: {base_url}")
                
                # 检查网站是否被标记为顽固网站（连续403错误）
                domain = base_url.replace('https://', '').replace('http://', '')
                if self.anti_crawler_manager.is_site_banned(domain):
                    logger.warning(f"网站 {domain} 被标记为顽固网站，跳过处理")
                    continue
                
                # 构造搜索URL
                search_url = f"{base_url}/search?q={keyword}&year={year}"
                
                # 真实爬取URL（设置最大尝试次数限制）
                results = self.crawl_url(search_url, keyword, year, max_attempts=3)
                
                # 如果爬取失败，尝试备用URL
                if not results:
                    logger.warning(f"主URL爬取失败，尝试备用URL")
                    # 构造备用URL
                    alternate_url = f"{base_url}/news/{keyword.replace(' ', '-')}"
                    results = self.crawl_url(alternate_url, keyword, year, max_attempts=2)
                
                all_results.extend(results)
                
                # 智能任务间延迟 - 根据网站响应情况调整
                if len(results) > 0:  # 如果成功获取数据，延迟较短
                    delay_time = random.uniform(3.0, 8.0)
                else:  # 如果失败，延迟较长
                    delay_time = random.uniform(8.0, 15.0)
                    
                logger.info(f"网站爬取完成，等待 {delay_time:.1f} 秒后继续")
                time.sleep(delay_time)
            
            # 数据质量验证和清理 - 集成数据质量管理系统和智能页面过滤器
            validated_results = []
            quality_stats = {
                'total_articles': len(all_results),
                'valid_articles': 0,
                'invalid_articles': 0,
                'quality_issues': [],
                'dqm_processed': 0,
                'dqm_rejected': 0,
                'filter_processed': 0,
                'filter_rejected': 0
            }
            
            for article in all_results:
                if article:
                    # 1. 首先使用智能页面过滤器进行内容过滤
                    filter_result = self.smart_page_filter.filter_content(article)
                    if not filter_result['is_valid']:
                        quality_stats['filter_rejected'] += 1
                        quality_stats['quality_issues'].extend(filter_result['reasons'])
                        logger.warning(f"智能页面过滤器拒绝文章: {filter_result['reasons']}")
                        continue
                    
                    quality_stats['filter_processed'] += 1
                    
                    # 2. 使用数据质量管理系统进行深度质量评估
                    dqm_result = self.data_quality_system.evaluate_article_quality(article)
                    if not dqm_result['is_valid']:
                        quality_stats['dqm_rejected'] += 1
                        quality_stats['quality_issues'].extend(dqm_result['issues'])
                        logger.warning(f"数据质量管理系统拒绝文章: {dqm_result['issues']}")
                        continue
                    
                    quality_stats['dqm_processed'] += 1
                    
                    # 3. 传统质量验证（保持向后兼容）
                    is_valid, quality_issues = self.validate_article_quality(article, year)
                    
                    if is_valid:
                        # 清理和标准化文章数据
                        cleaned_article = self.clean_and_normalize_article(article)
                        
                        # 4. 使用数据质量管理系统进行数据增强
                        enhanced_article = self.data_quality_system.enhance_article_data(cleaned_article)
                        validated_results.append(enhanced_article)
                        quality_stats['valid_articles'] += 1
                    else:
                        quality_stats['invalid_articles'] += 1
                        quality_stats['quality_issues'].extend(quality_issues)
                        logger.warning(f"传统质量验证失败: {quality_issues}")
            
            # 构建结果
            result = {
                'task_id': task_id,
                'keyword': keyword,
                'year': year,
                'results': validated_results,
                'quality_stats': quality_stats,
                'processed_at': datetime.now().isoformat(),
                'worker_id': self.worker_id,
                'processing_time': time.time() - start_time,
                'crawl_method': 'traditional',
                'urls_attempted': min(len(prioritized_sites), max_sites_per_task),
                'urls_successful': len([r for r in all_results if r]),
                'data_quality_score': quality_stats['valid_articles'] / max(1, quality_stats['total_articles'])
            }
            
            # 更新统计
            processing_time = time.time() - start_time
            self.worker_stats['tasks_completed'] += 1
            self.worker_stats['total_processing_time'] += processing_time
            self.worker_stats['last_task_completed'] = time.time()
            self.worker_stats['last_active'] = time.time()
            
            # 记录响应时间
            self.worker_stats['response_times'].append(processing_time)
            
            # 计算平均响应时间（保留最近50个任务）
            if len(self.worker_stats['response_times']) > 50:
                self.worker_stats['response_times'] = self.worker_stats['response_times'][-50:]
            self.worker_stats['avg_response_time'] = sum(self.worker_stats['response_times']) / len(self.worker_stats['response_times'])
            
            # 计算成功率
            total_tasks = self.worker_stats['tasks_completed'] + self.worker_stats['tasks_failed']
            if total_tasks > 0:
                self.worker_stats['success_rate'] = self.worker_stats['tasks_completed'] / total_tasks
            
            logger.info(f"任务处理完成: {keyword}，尝试 {min(len(prioritized_sites), max_sites_per_task)} 个网站，找到 {len(all_results)} 篇文章，耗时: {processing_time:.2f}秒")
            
            return result
            
        except Exception as e:
            logger.error(f"任务处理失败: {e}")
            self.worker_stats['tasks_failed'] += 1
            self.worker_stats['last_active'] = time.time()
            
            # 计算成功率
            total_tasks = self.worker_stats['tasks_completed'] + self.worker_stats['tasks_failed']
            if total_tasks > 0:
                self.worker_stats['success_rate'] = self.worker_stats['tasks_completed'] / total_tasks
            
            # 返回错误结果
            return {
                'task_id': task.get('task_id', ''),
                'keyword': task.get('keyword', ''),
                'year': task.get('year', 2024),
                'error': str(e),
                'processed_at': datetime.now().isoformat(),
                'worker_id': self.worker_id
            }
    
    def prioritize_sites(self, sites: List[str]) -> List[str]:
        """智能网站排序 - 将响应速度快的网站放在前面"""
        # 基于历史经验的网站响应速度排序
        fast_sites = ['allafrica.com', 'www.news24.com', 'www.nation.co.ke', 
                     'www.punchng.com', 'www.vanguardngr.com', 'www.thisdaylive.com']
        
        medium_sites = ['guardian.ng', 'www.modernghana.com', 'www.liberianobserver.com',
                        'www.newsghana.com.gh']
        
        # 分类排序
        fast_urls = [site for site in sites if any(fast in site for fast in fast_sites)]
        medium_urls = [site for site in sites if any(medium in site for medium in medium_sites)]
        
        # 合并排序结果
        prioritized = fast_urls + medium_urls
        
        # 如果某些网站不在分类中，添加到末尾
        other_urls = [site for site in sites if site not in prioritized]
        prioritized.extend(other_urls)
        
        logger.info(f"网站智能排序完成: 快速站点 {len(fast_urls)} 个，中等站点 {len(medium_urls)} 个")
        
        return prioritized
    
    def submit_result(self, result: Dict[str, Any]) -> bool:
        """提交处理结果到主节点"""
        response = self.connection_manager.make_request(
            'POST', 
            f"{MASTER_URL}/results/submit",
            json=result
        )
        
        if response and response.status_code == 200:
            logger.info("结果提交成功")
            return True
        else:
            logger.warning("结果提交失败")
            return False
    
    def worker_loop(self):
        """工作节点主循环"""
        last_heartbeat = 0
        consecutive_failures = 0
        
        while self.running:
            current_time = time.time()
            
            # 发送心跳
            if current_time - last_heartbeat >= HEARTBEAT_INTERVAL:
                if self.send_heartbeat():
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    
                    # 如果连续失败次数过多，暂停一段时间
                    if consecutive_failures >= 5:
                        logger.warning("连续心跳失败过多，暂停30秒")
                        time.sleep(30)
                        consecutive_failures = 0
                
                last_heartbeat = current_time
            
            # 检查连接健康状态
            if not self.connection_manager.check_connection_health():
                logger.warning("连接不健康，等待恢复...")
                time.sleep(10)
                continue
            
            # 获取任务
            task = self.get_next_task()
            
            if task:
                # 处理任务
                result = self.process_task(task)
                
                # 提交结果
                if not self.submit_result(result):
                    # 如果提交失败，将任务重新加入队列
                    logger.warning("结果提交失败，任务将重新处理")
                    self.task_queue.append(task)
            else:
                # 没有任务，等待一段时间
                time.sleep(5)
            
            # 处理队列中的任务（如果有）
            if self.task_queue:
                task = self.task_queue.pop(0)
                result = self.process_task(task)
                self.submit_result(result)
    
    def start(self):
        """启动工作节点"""
        self.running = True
        
        # 启动工作循环
        worker_thread = threading.Thread(target=self.worker_loop)
        worker_thread.daemon = True
        worker_thread.start()
        
        logger.info(f"工作节点 {self.worker_id} 已启动")
        
        # 不阻塞主线程，让worker_loop线程独立运行
        # 主线程正常退出，worker_loop线程作为守护线程继续运行
    
    def stop(self):
        """停止工作节点"""
        self.running = False
        self.connection_manager.close()
        self.thread_pool.shutdown(wait=True)
        logger.info(f"工作节点 {self.worker_id} 已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取工作节点状态"""
        status = {
            'worker_id': self.worker_id,
            'running': self.running,
            'current_task': self.current_task,
            'task_queue_size': len(self.task_queue),
            'stats': self.worker_stats,
            'connection_stats': self.connection_manager.get_stats(),
            'uptime': time.time() - self.worker_stats['start_time']
        }
        
        # 添加Modern Ghana优化器性能报告
        status['modernghana_performance'] = self.modernghana_optimizer.get_performance_report()
        
        return status
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用率"""
        try:
            memory = psutil.virtual_memory()
            return {
                'total': memory.total / (1024 * 1024 * 1024),  # GB
                'used': memory.used / (1024 * 1024 * 1024),    # GB
                'available': memory.available / (1024 * 1024 * 1024),  # GB
                'percent': memory.percent
            }
        except Exception as e:
            logger.warning(f"获取内存使用率失败: {e}")
            return {'total': 0, 'used': 0, 'available': 0, 'percent': 0}
    
    def get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        try:
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            logger.warning(f"获取CPU使用率失败: {e}")
            return 0
    
    def get_local_ip(self) -> str:
        """获取本地IP地址"""
        try:
            # 尝试连接到外部地址以获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            logger.warning(f"获取本地IP失败: {e}")
            return "unknown"
    
    def update_worker_status(self) -> Dict[str, Any]:
        """更新工作节点状态"""
        # 更新统计信息
        self.worker_stats['last_active'] = time.time()
        
        # 计算运行时间
        uptime = time.time() - self.worker_stats['start_time']
        
        # 获取系统资源使用情况
        memory_usage = self.get_memory_usage()
        cpu_usage = self.get_cpu_usage()
        local_ip = self.get_local_ip()
        
        # 构建状态信息
        status = {
            'worker_id': self.worker_id,
            'status': 'running',
            'timestamp': time.time(),
            'load': {
                'cpu_percent': cpu_usage,
                'memory_usage': memory_usage,
                'uptime': uptime,
                'local_ip': local_ip
            },
            'stats': self.worker_stats,
            'connection_stats': self.connection_manager.get_stats(),
            'task_queue_size': len(self.task_queue),
            'current_task': self.current_task
        }
        
        return status

def main():
    """主函数"""
    logger.info("启动分布式爬虫工作节点（修复版）...")
    
    # 创建并启动工作节点
    worker = DistributedWorker()
    
    try:
        worker.start()
        
        # 等待信号以优雅关闭
        def signal_handler(signum, frame):
            logger.info("接收到关闭信号，正在停止工作节点...")
            worker.stop()
            sys.exit(0)
        
        # 注册信号处理
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 主线程等待，直到接收到关闭信号
        while worker.running:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"工作节点启动失败: {e}")
        worker.stop()

if __name__ == "__main__":
    main()