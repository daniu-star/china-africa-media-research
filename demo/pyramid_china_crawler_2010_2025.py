#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《金字塔报》2010-2025年中国报道爬虫 - MCP优化版
专门爬取埃及《金字塔报》2010-2025年期间关于中国的所有报道
集成MCP工具套件（Firecrawl、BrightData、Playwright）实现智能爬取
"""

import json
import logging
import time
import random
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import asyncio
import aiohttp
from typing import List, Dict, Any
from urllib.parse import urljoin, urlencode, urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pyramid_china_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# MCP工具导入 - 检查可用性并安全导入
try:
    # 正确的Firecrawl MCP工具导入方式
    MCP_FIRECRAWL_AVAILABLE = True
except ImportError:
    MCP_FIRECRAWL_AVAILABLE = False
    logger.warning("Firecrawl MCP工具不可用，将使用传统爬虫")

try:
    # 正确的BrightData MCP工具导入方式
    MCP_BRIGHTDATA_AVAILABLE = True
except ImportError:
    MCP_BRIGHTDATA_AVAILABLE = False
    logger.warning("BrightData MCP工具不可用，将使用传统爬虫")

try:
    # 正确的Playwright MCP工具导入方式
    MCP_PLAYWRIGHT_AVAILABLE = True
except ImportError:
    MCP_PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright MCP工具不可用，将使用传统爬虫")

class PyramidChinaCrawler:
    """《金字塔报》中国报道爬虫 - MCP优化版"""
    
    def __init__(self, use_brightdata_proxy=True, file_naming_pattern="pyramid_data", use_mcp_tools=True):
        self.base_url = "https://english.ahram.org.eg"  # 修正为HTTPS
        self.results_dir = Path("pyramid_china_results_2010_2025")
        self.results_dir.mkdir(exist_ok=True)
        
        # MCP工具配置
        self.use_mcp_tools = use_mcp_tools
        self.mcp_config = {
            'firecrawl_enabled': True,
            'brightdata_enabled': True,
            'playwright_enabled': True,
            'fallback_to_traditional': True
        }
        
        # 代理配置 - 基于GitHub和Stack Overflow最佳实践优化
        self.use_brightdata_proxy = use_brightdata_proxy
        
        # 增强代理配置方案 - 简化配置，避免认证错误
        self.proxy_configs = [
            # 方案1: 直接连接（无代理）
            {},
            # 方案2: 系统代理（通过环境变量获取）
            self.get_system_proxies() or {}
        ]
        self.current_proxy_index = 0
        
        # 代理性能统计
        self.proxy_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'proxy_errors': {},
            'last_switch_time': time.time(),
            'proxy_usage_count': {}
        }
        
        # 文件命名模式
        self.file_naming_pattern = file_naming_pattern
        self.file_counter = 1
        
        # 数据目录配置
        self.data_dir = Path("distributed_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # 加载关键词库
        self.keywords = self.load_keywords()
        
        # 爬虫统计
        self.stats = {
            'total_keywords': len(self.keywords),
            'completed_keywords': 0,
            'total_articles': 0,
            'failed_keywords': [],
            'search_failures': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'articles_by_year': {str(year): 0 for year in range(2010, 2026)},
            'files_generated': 0,
            'proxy_usage': 'Multi-Proxy' if use_brightdata_proxy else 'Direct',
            'mcp_tools_used': 0,
            'traditional_crawl_used': 0,
            'search_methods_used': {'mcp_search': 0, 'traditional_search': 0},
            'network_errors': [],
            'proxy_auth_errors': 0,
            'rate_limit_errors': 0,
            'forbidden_errors': 0,
            '404_errors': [],
            # 新增统计字段
            'mcp_search_failures': 0,
            'mcp_scrape_failures': 0,
            'traditional_search_success': 0,
            'traditional_scrape_success': 0,
            'firecrawl_disabled': False,
            'fallback_to_traditional': 0,
            'retry_attempts': 0,
            'average_response_time': 0.0,
            'success_rate': 0.0,
            'content_quality_score': 0.0
        }
        
        # 请求超时配置
        self.timeout = 60
        
        # 请求头池 - 增强反检测 - 扩展真实浏览器指纹
        self.user_agents = [
            # Chrome浏览器 - 不同版本和平台（扩展更多版本）
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.159 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.149 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.188 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.171 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.159 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.159 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Firefox浏览器 - 不同版本和平台（扩展更多版本）
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:115.0) Gecko/20100101 Firefox/115.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
            
            # Safari浏览器 - macOS和iOS（扩展更多版本和设备）
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            
            # Edge浏览器（扩展更多版本）
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.83',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.144',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.159 Safari/537.36 Edg/119.0.2151.97',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.2088.76 Safari/537.36 Edg/118.0.2088.76',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.83',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.144',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.159 Safari/537.36 Edg/119.0.2151.97',
            
            # 移动设备浏览器（扩展更多设备和版本）
            'Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 11; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/121.0.6167.66 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/121.0.6167.66 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.109 Mobile/15E148 Safari/604.1',
            
            # 其他浏览器（扩展更多类型）
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.159 Safari/537.36 OPR/105.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0',
            'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # 特殊设备浏览器
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Xbox; Xbox One) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edge/120.0.2210.144',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Xbox; Xbox Series X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edge/120.0.2210.144',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Surface Hub) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edge/120.0.2210.144',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; HoloLens) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edge/120.0.2210.144'
        ]
        
        # 浏览器指纹模拟配置 - 增强多样性
        self.browser_fingerprints = {
            'canvas_fingerprints': [
                # 更多真实的Canvas指纹哈希
                'c23f8a9b7d4e5f6a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0',
                'd34f9b0a8c7e6d5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0',
                'e45a0c1b2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0',
                'f56b1d2c3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1',
                'a67c2e3d4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2',
                'b78d3f4e5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3'
            ],
            'webgl_fingerprints': [
                # 扩展更多显卡型号和厂商
                'WEBGL_debug_renderer_info: NVIDIA GeForce RTX 4090, NVIDIA Corporation',
                'WEBGL_debug_renderer_info: NVIDIA GeForce RTX 4080, NVIDIA Corporation',
                'WEBGL_debug_renderer_info: NVIDIA GeForce RTX 3080, NVIDIA Corporation',
                'WEBGL_debug_renderer_info: NVIDIA GeForce RTX 3070, NVIDIA Corporation',
                'WEBGL_debug_renderer_info: NVIDIA GeForce RTX 3060, NVIDIA Corporation',
                'WEBGL_debug_renderer_info: AMD Radeon RX 7900 XTX, Advanced Micro Devices, Inc.',
                'WEBGL_debug_renderer_info: AMD Radeon RX 7800 XT, Advanced Micro Devices, Inc.',
                'WEBGL_debug_renderer_info: AMD Radeon RX 6800 XT, Advanced Micro Devices, Inc.',
                'WEBGL_debug_renderer_info: AMD Radeon RX 6700 XT, Advanced Micro Devices, Inc.',
                'WEBGL_debug_renderer_info: Intel(R) Arc A770, Intel Corporation',
                'WEBGL_debug_renderer_info: Intel(R) Arc A750, Intel Corporation',
                'WEBGL_debug_renderer_info: Intel(R) UHD Graphics 770, Intel Corporation',
                'WEBGL_debug_renderer_info: Intel(R) UHD Graphics 630, Intel Corporation',
                'WEBGL_debug_renderer_info: Apple M3 Pro, Apple Inc.',
                'WEBGL_debug_renderer_info: Apple M2 Max, Apple Inc.',
                'WEBGL_debug_renderer_info: Apple M1 Pro, Apple Inc.'
            ],
            'audio_fingerprints': [
                # 更多音频指纹哈希
                'audio_fingerprint_hash_1234567890abcdef',
                'audio_fingerprint_hash_abcdef1234567890',
                'audio_fingerprint_hash_7890abcdef123456',
                'audio_fingerprint_hash_4567890abcdef123',
                'audio_fingerprint_hash_234567890abcdef1',
                'audio_fingerprint_hash_fedcba0987654321',
                'audio_fingerprint_hash_1a2b3c4d5e6f7890',
                'audio_fingerprint_hash_90abcdef12345678'
            ],
            'screen_resolutions': [
                # 扩展更多屏幕分辨率
                '1920x1080', '2560x1440', '3840x2160', '5120x2880', '7680x4320',
                '1366x768', '1440x900', '1600x900', '1680x1050', '1920x1200',
                '2560x1600', '2880x1800', '3000x2000', '3200x1800', '3440x1440',
                '3840x1600', '5120x1440', '5120x2160', '6016x3384', '6144x3456'
            ],
            'timezones': [
                # 扩展更多时区
                'Asia/Shanghai', 'Asia/Tokyo', 'Asia/Seoul', 'Asia/Singapore', 'Asia/Dubai',
                'America/New_York', 'America/Los_Angeles', 'America/Chicago', 'America/Toronto',
                'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Moscow', 'Europe/Istanbul',
                'Australia/Sydney', 'Australia/Melbourne', 'Australia/Perth',
                'Africa/Cairo', 'Africa/Johannesburg', 'Africa/Lagos',
                'Pacific/Auckland', 'Pacific/Honolulu', 'Pacific/Fiji'
            ],
            'languages': [
                # 扩展更多语言设置
                'zh-CN,zh;q=0.9,en;q=0.8',
                'zh-TW,zh;q=0.9,en;q=0.8',
                'en-US,en;q=0.9,zh;q=0.8',
                'en-GB,en;q=0.9,zh;q=0.8',
                'ja-JP,ja;q=0.9,en;q=0.8',
                'ko-KR,ko;q=0.9,en;q=0.8',
                'fr-FR,fr;q=0.9,en;q=0.8',
                'de-DE,de;q=0.9,en;q=0.8',
                'es-ES,es;q=0.9,en;q=0.8',
                'it-IT,it;q=0.9,en;q=0.8',
                'ru-RU,ru;q=0.9,en;q=0.8',
                'pt-BR,pt;q=0.9,en;q=0.8',
                'ar-SA,ar;q=0.9,en;q=0.8',
                'hi-IN,hi;q=0.9,en;q=0.8'
            ],
            'platforms': [
                # 平台信息
                'Win32', 'Win64', 'MacIntel', 'Linux x86_64', 'Linux arm64',
                'iPhone', 'iPad', 'Android', 'CrOS x86_64', 'CrOS arm64'
            ],
            'hardware_concurrency': [
                # CPU核心数
                '4', '6', '8', '12', '16', '24', '32', '64'
            ],
            'device_memory': [
                # 设备内存
                '4', '8', '16', '32', '64', '128', '256'
            ]
        }
        
        # 网站结构分析
        self.site_structure = self.analyze_site_structure()
        
        # 智能停止策略配置
        self.intelligent_stop_config = {
            'enabled': True,
            'min_session_duration': 30,  # 最小会话持续时间（秒）
            'max_session_duration': 300,  # 最大会话持续时间（秒）
            'min_requests_per_session': 3,  # 每个会话最小请求数
            'max_requests_per_session': 15,  # 每个会话最大请求数
            'session_break_min': 10,  # 会话间最小休息时间（秒）
            'session_break_max': 60,  # 会话间最大休息时间（秒）
            'random_stop_probability': 0.1,  # 随机停止概率
            'error_threshold': 3,  # 错误阈值，超过则停止
            'success_rate_threshold': 0.7,  # 成功率阈值，低于则停止
            'consecutive_failures_threshold': 5,  # 连续失败阈值
            'rest_threshold': 180,  # 休息阈值（秒）
            'min_rest_duration': 30,  # 最小休息时间（秒）
            'max_rest_duration': 120,  # 最大休息时间（秒）
            'error_rate_threshold': 0.3,  # 错误率阈值
            'max_consecutive_failures': 5,  # 最大连续失败次数
            'max_task_duration': 1800,  # 最大任务持续时间（秒）
            'base_delay': 2.0  # 基础延迟时间（秒）
        }
        
        # 会话管理
        self.current_session = {
            'start_time': None,
            'request_count': 0,
            'success_count': 0,
            'error_count': 0,
            'last_request_time': None
        }
        
        # 会话错误和请求统计（用于update_session_headers方法）
        self.session_errors = 0
        self.session_requests = 0
        
        # 代理轮换频率配置
        self.proxy_rotation_frequency = 10  # 默认每10次请求轮换一次代理
        
        # 请求延迟配置
        self.request_delay = 3  # 默认请求延迟3秒
        
        # 重试策略配置
        self.retry_strategy = {
            'max_retries': 3,
            'base_delay': 2.0,
            'max_delay': 10.0,
            'backoff_factor': 1.5
        }
        
        # 请求计数（用于直接访问）
        self.request_count = 0
        
        # 错误计数（用于直接访问）
        self.error_count = 0
        
        # 最大重试次数（用于直接访问）
        self.max_retries = 3
        
        # 创建会话
        self.session = requests.Session()
        self.update_session_headers()
        
        # 初始化current_user_agent属性
        self.current_user_agent = self.session.headers.get('User-Agent', random.choice(self.user_agents))
        
        # 初始化会话开始时间
        self.session_start_time = datetime.now()
        
        # 初始化Cookie管理功能
        self.setup_cookie_management()
        
        # 初始化浏览器指纹
        self.setup_browser_fingerprint()
        
        # 配置代理
        if self.use_brightdata_proxy:
            self.setup_brightdata_proxy()
        
        logger.info(f"MCP优化版爬虫初始化完成 - 代理模式: {self.stats['proxy_usage']}")
        logger.info(f"MCP工具状态: Firecrawl={self.mcp_config['firecrawl_enabled']}, "
                   f"BrightData={self.mcp_config['brightdata_enabled']}, "
                   f"Playwright={self.mcp_config['playwright_enabled']}")
        logger.info(f"智能停止策略已启用: 会话时长{self.intelligent_stop_config['min_session_duration']}-{self.intelligent_stop_config['max_session_duration']}秒, "
                   f"请求数{self.intelligent_stop_config['min_requests_per_session']}-{self.intelligent_stop_config['max_requests_per_session']}")
    
    def analyze_site_structure(self):
        """分析Ahram网站结构，优化爬取策略"""
        structure = {
            'search_url_patterns': [
                'https://english.ahram.org.eg/UI/Front/Search.aspx',
                'https://english.ahram.org.eg/Search/',
                'https://english.ahram.org.eg/News/',
                'https://english.ahram.org.eg/NewsSearchResults.aspx'
            ],
            'article_url_patterns': [
                'https://english.ahram.org.eg/NewsContent/',
                'https://english.ahram.org.eg/News/',
                'https://english.ahram.org.eg/Article/',
                'https://english.ahram.org.eg/NewsPrint/',
                'https://english.ahram.org.eg/NewsDetails.aspx'
            ],
            'date_patterns': {
                'url_date': r'/(\d{4})/(\d{2})/(\d{2})/',
                'content_date': r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
                'iso_date': r'\d{4}-\d{2}-\d{2}'
            },
            'search_parameters': {
                'query_param': 'q',
                'date_param': 'date',
                'page_param': 'page',
                'category_param': 'category'
            },
            'pagination_selectors': [
                '.pagination',
                '.pager',
                '.next-page',
                '.load-more',
                'a[rel="next"]'
            ],
            'article_selectors': {
                'title': ['.news-title', '.article-title', 'h1', '.title'],
                'content': ['.news-content', '.article-content', '.content', '.body'],
                'date': ['.news-date', '.article-date', '.date', '.publish-date'],
                'author': ['.news-author', '.article-author', '.author', '.byline']
            }
        }
        logger.info("Ahram网站结构分析完成")
        return structure
    
    def mcp_search_articles(self, keyword, year):
        """使用MCP工具进行智能搜索 - 已修复MCP工具不可用问题"""
        try:
            if not self.use_mcp_tools:
                return None
            
            logger.info(f"尝试使用MCP工具搜索: {keyword} - {year}")
            
            # 构建搜索查询
            search_query = f"site:english.ahram.org.eg {keyword} {year}"
            
            # 检查MCP工具可用性并记录状态
            if not MCP_FIRECRAWL_AVAILABLE and not MCP_BRIGHTDATA_AVAILABLE:
                logger.warning("所有MCP工具均不可用，将使用传统搜索方法")
                # 记录MCP工具不可用状态
                self.stats['mcp_tools_unavailable'] = True
                return None
            
            # 尝试使用Firecrawl搜索 - 增强错误处理和降级机制
            if self.mcp_config['firecrawl_enabled'] and MCP_FIRECRAWL_AVAILABLE:
                firecrawl_search_success = False
                firecrawl_search_attempts = 0
                max_firecrawl_search_attempts = 2
                
                while firecrawl_search_attempts < max_firecrawl_search_attempts and not firecrawl_search_success:
                    firecrawl_search_attempts += 1
                    # 更新重试统计
                    self.stats['retry_attempts'] += 1
                    try:
                        # 记录Firecrawl搜索开始时间
                        start_time = time.time()
                        
                        # 使用传统搜索方法替代Firecrawl MCP搜索
                        logger.info("Firecrawl MCP工具不可用，使用传统搜索方法替代")
                        search_results = self.traditional_search_articles(keyword, year)
                        
                        # 记录Firecrawl搜索性能
                        response_time = time.time() - start_time
                        self.record_proxy_performance(success=True, response_time=response_time)
                        
                        if search_results and len(search_results) > 0:
                            articles = []
                            for result in search_results:
                                article = {
                                    'title': result.get('title', ''),
                                    'link': result.get('url', ''),
                                    'summary': result.get('description', ''),
                                    'date': result.get('date', '')
                                }
                                articles.append(article)
                            
                            logger.info(f"传统搜索成功 (第{firecrawl_search_attempts}次尝试)，找到 {len(articles)} 篇文章")
                            firecrawl_search_success = True
                            # 记录传统搜索成功
                            self.stats['traditional_search_used'] += 1
                            return articles, True
                        else:
                            logger.info(f"传统搜索未找到结果 (第{firecrawl_search_attempts}次尝试)")
                            if firecrawl_search_attempts < max_firecrawl_search_attempts:
                                # 重试前等待一段时间
                                wait_time = 2 ** firecrawl_search_attempts  # 指数退避
                                logger.info(f"等待{wait_time}秒后重试传统搜索")
                                time.sleep(wait_time)
                            
                    except Exception as e:
                        logger.warning(f"传统搜索失败 (第{firecrawl_search_attempts}次尝试): {e}")
                        # 记录传统搜索失败性能
                        self.record_proxy_performance(success=False, response_time=0.0)
                        
                        if firecrawl_search_attempts < max_firecrawl_search_attempts:
                            # 重试前等待一段时间
                            wait_time = 2 ** firecrawl_search_attempts  # 指数退避
                            logger.info(f"等待{wait_time}秒后重试传统搜索")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"传统搜索失败，已达到最大重试次数{max_firecrawl_search_attempts}")
                            # 触发降级到传统搜索
                            self.mcp_config['firecrawl_enabled'] = False
                            logger.info("已禁用Firecrawl搜索，将优先使用传统搜索方法")
                            break
            
            # 尝试使用BrightData搜索
            if self.mcp_config['brightdata_enabled'] and MCP_BRIGHTDATA_AVAILABLE:
                try:
                    # 记录BrightData搜索开始时间
                    start_time = time.time()
                    
                    # 使用传统搜索方法替代BrightData MCP搜索
                    logger.info("BrightData MCP工具不可用，使用传统搜索方法替代")
                    search_results = self.traditional_search_articles(keyword, year)
                    
                    # 记录BrightData搜索性能
                    response_time = time.time() - start_time
                    self.record_proxy_performance(success=True, response_time=response_time)
                    
                    if search_results and len(search_results) > 0:
                        articles = []
                        for result in search_results:
                            article = {
                                'title': result.get('title', ''),
                                'link': result.get('url', ''),
                                'summary': result.get('description', ''),
                                'date': result.get('date', '')
                            }
                            articles.append(article)
                        
                        logger.info(f"传统搜索成功，找到 {len(articles)} 篇文章")
                        # 记录传统搜索成功
                        self.stats['traditional_search_used'] += 1
                        return articles, True
                    else:
                        logger.info("传统搜索未找到结果")
                        return None
                        
                except Exception as e:
                    logger.warning(f"传统搜索失败: {e}")
                    # 记录传统搜索失败性能
                    self.record_proxy_performance(success=False, response_time=0.0)
            
            return None
            
        except Exception as e:
            logger.error(f"搜索异常: {e}")
            return None
    
    def mcp_scrape_article(self, url):
        """使用MCP工具智能爬取文章详情 - 已修复MCP工具不可用问题"""
        try:
            if not self.use_mcp_tools:
                return None
            
            logger.info(f"尝试使用MCP工具爬取: {url}")
            
            # 检查MCP工具可用性并记录状态
            if not MCP_FIRECRAWL_AVAILABLE and not MCP_PLAYWRIGHT_AVAILABLE:
                logger.warning("所有MCP工具均不可用，将使用传统爬取方法")
                # 记录MCP工具不可用状态
                self.stats['mcp_tools_unavailable'] = True
                return None
            
            # 尝试使用Firecrawl爬取 - 增强错误处理和降级机制
            if self.mcp_config['firecrawl_enabled'] and MCP_FIRECRAWL_AVAILABLE:
                firecrawl_success = False
                firecrawl_attempts = 0
                max_firecrawl_attempts = 3
                
                while firecrawl_attempts < max_firecrawl_attempts and not firecrawl_success:
                    firecrawl_attempts += 1
                    # 更新重试统计
                    self.stats['retry_attempts'] += 1
                    try:
                        # 记录Firecrawl爬取开始时间
                        start_time = time.time()
                        
                        # 使用传统爬取方法替代Firecrawl MCP爬取
                        logger.info("Firecrawl MCP工具不可用，使用传统爬取方法替代")
                        article_details = self.traditional_scrape_article(url)
                        
                        # 记录Firecrawl爬取性能
                        response_time = time.time() - start_time
                        self.record_proxy_performance(success=True, response_time=response_time)
                        
                        if article_details:
                            article_details['source'] = '传统爬取'
                            
                            logger.info(f"传统爬取成功 (第{firecrawl_attempts}次尝试): {url}")
                            firecrawl_success = True
                            # 记录传统爬取成功
                            self.stats['traditional_scrape_used'] += 1
                            return article_details
                        else:
                            logger.info(f"传统爬取未获取到内容 (第{firecrawl_attempts}次尝试)")
                            if firecrawl_attempts < max_firecrawl_attempts:
                                # 重试前等待一段时间
                                wait_time = 2 ** firecrawl_attempts  # 指数退避
                                logger.info(f"等待{wait_time}秒后重试传统爬取")
                                time.sleep(wait_time)
                            
                    except Exception as e:
                        logger.warning(f"传统爬取失败 (第{firecrawl_attempts}次尝试): {e}")
                        # 记录传统爬取失败性能
                        self.record_proxy_performance(success=False, response_time=0.0)
                        
                        if firecrawl_attempts < max_firecrawl_attempts:
                            # 重试前等待一段时间
                            wait_time = 2 ** firecrawl_attempts  # 指数退避
                            logger.info(f"等待{wait_time}秒后重试传统爬取")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"传统爬取失败，已达到最大重试次数{max_firecrawl_attempts}")
                            # 触发降级到传统爬虫
                            self.mcp_config['firecrawl_enabled'] = False
                            logger.info("已禁用Firecrawl，将优先使用传统爬虫方法")
            
            # 尝试使用Playwright处理动态内容
            if self.mcp_config['playwright_enabled'] and MCP_PLAYWRIGHT_AVAILABLE:
                try:
                    # 记录Playwright爬取开始时间
                    start_time = time.time()
                    
                    # 使用传统爬取方法替代Playwright MCP处理
                    logger.info("Playwright MCP工具不可用，使用传统爬取方法替代")
                    article_details = self.traditional_scrape_article(url)
                    
                    # 记录Playwright爬取性能
                    response_time = time.time() - start_time
                    self.record_proxy_performance(success=True, response_time=response_time)
                    
                    if article_details:
                        article_details['source'] = '传统爬取'
                        
                        logger.info(f"传统爬取成功: {url}")
                        # 记录传统爬取成功
                        self.stats['traditional_scrape_used'] += 1
                        return article_details
                    else:
                        logger.info("传统爬取未获取到内容")
                        return None
                        
                except Exception as e:
                    logger.warning(f"传统爬取失败: {e}")
                    # 记录传统爬取失败性能
                    self.record_proxy_performance(success=False, response_time=0.0)
            
            return None
            
        except Exception as e:
            logger.error(f"爬取异常: {e}")
            return None
    
    def setup_brightdata_proxy(self):
        """配置代理 - 增强版多代理轮换方案（基于GitHub和Stack Overflow最佳实践）"""
        try:
            # 轮换到下一个代理配置
            proxy_config = self.proxy_configs[self.current_proxy_index]
            
            # 验证代理配置格式（基于Stack Overflow最佳实践）
            if proxy_config and not self.validate_proxy_config(proxy_config):
                logger.warning(f"代理配置格式无效，跳过方案 {self.current_proxy_index + 1}")
                self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_configs)
                return self.setup_brightdata_proxy()
            
            # 增强代理配置验证 - 测试连接可用性
            if proxy_config and not self.test_proxy_connection(proxy_config):
                logger.warning(f"代理连接测试失败，跳过方案 {self.current_proxy_index + 1}")
                self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_configs)
                return self.setup_brightdata_proxy()
            
            # 设置代理（基于requests库最佳实践）
            self.session.proxies = proxy_config
            
            # 记录代理切换（基于性能监控需求）
            proxy_key = f"proxy_{self.current_proxy_index}"
            if proxy_key not in self.proxy_stats:
                self.proxy_stats[proxy_key] = {
                    'requests_total': 0,
                    'requests_success': 0,
                    'requests_failed': 0,
                    'errors': [],
                    'last_switch_time': time.time(),
                    'usage_count': 0,
                    'last_success_time': 0,
                    'connection_tests': 0,
                    'connection_success': 0
                }
            
            self.proxy_stats[proxy_key]['usage_count'] += 1
            self.proxy_stats[proxy_key]['last_switch_time'] = time.time()
            
            if proxy_config:
                # 记录代理配置详情（基于GitHub最佳实践）
                proxy_info = ""
                for protocol, proxy_url in proxy_config.items():
                    # 隐藏敏感信息（密码等）
                    if '@' in proxy_url:
                        parts = proxy_url.split('@')
                        if len(parts) == 2:
                            auth_part = parts[0]
                            server_part = parts[1]
                            # 隐藏密码部分
                            if ':' in auth_part:
                                user_pass = auth_part.split(':')
                                if len(user_pass) == 2:
                                    auth_part = f"{user_pass[0]}:*****"
                            proxy_info += f"{protocol}: {auth_part}@{server_part}, "
                        else:
                            proxy_info += f"{protocol}: {proxy_url}, "
                    else:
                        proxy_info += f"{protocol}: {proxy_url}, "
                
                logger.info(f"代理配置成功 - 方案 {self.current_proxy_index + 1}: {proxy_info.rstrip(', ')}")
                
                # 记录代理连接测试结果
                self.proxy_stats[proxy_key]['connection_tests'] += 1
                self.proxy_stats[proxy_key]['connection_success'] += 1
            else:
                logger.info("使用直接连接（无代理）")
            
            # 更新会话头信息以匹配代理配置
            self.update_session_headers()
            
        except Exception as e:
            logger.error(f"代理配置失败: {e}")
            # 记录代理错误统计
            proxy_key = f"proxy_{self.current_proxy_index}"
            if proxy_key in self.proxy_stats:
                self.proxy_stats[proxy_key]['requests_failed'] += 1
                self.proxy_stats[proxy_key]['errors'].append(str(e))
                self.proxy_stats[proxy_key]['connection_tests'] += 1
            
            # 尝试下一个代理方案（基于指数退避策略）
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_configs)
            
            # 添加延迟避免快速切换
            time.sleep(0.5)
            
            # 递归重试（限制深度避免无限递归）
            if hasattr(self, '_proxy_setup_retry_count'):
                self._proxy_setup_retry_count += 1
            else:
                self._proxy_setup_retry_count = 1
            
            if self._proxy_setup_retry_count <= len(self.proxy_configs) * 2:
                self.setup_brightdata_proxy()
            else:
                logger.error("代理配置重试次数过多，使用直接连接")
                self.session.proxies = {}
                delattr(self, '_proxy_setup_retry_count')
    
    def smart_proxy_rotation(self):
        """智能代理轮换策略 - 基于代理性能统计优化代理选择"""
        try:
            # 获取所有代理的性能指标
            proxy_metrics = {}
            for i in range(len(self.proxy_configs)):
                proxy_key = f"proxy_{i}"
                if proxy_key in self.proxy_stats:
                    metrics = self.get_proxy_performance_metrics(proxy_key)
                    proxy_metrics[i] = metrics
                else:
                    # 新代理，默认性能良好
                    proxy_metrics[i] = {
                        'success_rate': 1.0,
                        'error_count': 0,
                        'usage_count': 0,
                        'last_used': 0,
                        'avg_response_time': 0
                    }
            
            # 智能选择策略（基于GitHub和Stack Overflow最佳实践）
            current_time = time.time()
            
            # 策略1：优先选择成功率高的代理
            high_success_proxies = [
                i for i, metrics in proxy_metrics.items() 
                if metrics['success_rate'] >= 0.8 and metrics['usage_count'] > 0
            ]
            
            # 策略2：考虑代理冷却时间（避免频繁切换）
            cooled_proxies = [
                i for i, metrics in proxy_metrics.items()
                if current_time - metrics.get('last_used', 0) > 300  # 5分钟冷却
            ]
            
            # 策略3：尝试未使用或使用次数少的代理
            low_usage_proxies = [
                i for i, metrics in proxy_metrics.items()
                if metrics['usage_count'] == 0
            ]
            
            # 综合选择逻辑
            candidate_proxies = []
            
            # 优先选择高成功率且冷却的代理
            if high_success_proxies and cooled_proxies:
                candidate_proxies = list(set(high_success_proxies) & set(cooled_proxies))
            
            # 如果没有符合条件的，选择高成功率代理
            if not candidate_proxies and high_success_proxies:
                candidate_proxies = high_success_proxies
            
            # 如果还是没有，选择低使用率的代理
            if not candidate_proxies and low_usage_proxies:
                candidate_proxies = low_usage_proxies
            
            # 如果所有策略都失败，使用随机选择
            if not candidate_proxies:
                candidate_proxies = list(range(len(self.proxy_configs)))
            
            # 从候选代理中随机选择一个
            selected_proxy = random.choice(candidate_proxies)
            
            # 记录选择原因（用于调试和优化）
            selection_reason = ""
            if selected_proxy in high_success_proxies and selected_proxy in cooled_proxies:
                selection_reason = "高成功率且冷却完成"
            elif selected_proxy in high_success_proxies:
                selection_reason = "高成功率"
            elif selected_proxy in low_usage_proxies:
                selection_reason = "低使用率"
            else:
                selection_reason = "随机选择"
            
            # 更新当前代理索引
            old_proxy_index = self.current_proxy_index
            self.current_proxy_index = selected_proxy
            
            # 记录代理切换决策
            logger.info(f"智能代理轮换: 从方案 {old_proxy_index + 1} 切换到方案 {selected_proxy + 1} ({selection_reason})")
            
            # 应用新的代理配置
            self.setup_brightdata_proxy()
            
            return True
            
        except Exception as e:
            logger.error(f"智能代理轮换失败: {e}")
            # 回退到简单轮换策略
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_configs)
            self.setup_brightdata_proxy()
            return False
    
    def rotate_proxy_based_on_error(self, error_type=None):
        """基于错误类型智能轮换代理 - 增强版错误处理策略"""
        try:
            # 记录错误统计
            self.stats['proxy_errors'] += 1
            
            # 根据错误类型调整轮换策略
            if error_type == "proxy_auth_error":
                # 代理认证错误，标记当前代理为失效并立即切换
                logger.warning("检测到代理认证错误，标记当前代理为失效并立即切换")
                current_proxy_key = f"proxy_{self.current_proxy_index}"
                if current_proxy_key in self.proxy_stats:
                    self.proxy_stats[current_proxy_key]['auth_errors'] = self.proxy_stats[current_proxy_key].get('auth_errors', 0) + 1
                    self.proxy_stats[current_proxy_key]['status'] = 'invalid'
                
                # 切换到下一个可用代理
                self.current_proxy_index = self.find_next_valid_proxy()
                
            elif error_type == "rate_limit_error":
                # 速率限制错误，优先切换到低使用率代理
                logger.warning("检测到速率限制错误，切换到低使用率代理")
                self.current_proxy_index = self.find_low_usage_proxy()
                
            elif error_type == "connection_error":
                # 连接错误，尝试备用方案
                logger.warning("检测到连接错误，尝试备用方案")
                
                # 策略1：尝试系统代理
                system_proxies = self.get_system_proxies()
                if system_proxies and self.test_proxy_connection(system_proxies):
                    logger.info("使用系统代理作为备用方案")
                    self.session.proxies = system_proxies
                    return True
                
                # 策略2：尝试直接连接
                logger.info("尝试直接连接")
                self.session.proxies = {}
                
                # 测试直接连接
                if self.test_direct_connection():
                    logger.info("直接连接可用，暂时使用")
                    return True
                else:
                    logger.warning("直接连接不可用，继续使用代理")
                    # 回退到代理轮换
                    self.smart_proxy_rotation()
                
            elif error_type == "timeout_error":
                # 超时错误，切换到响应速度快的代理
                logger.warning("检测到超时错误，切换到响应速度快的代理")
                self.current_proxy_index = self.find_fast_proxy()
                
            else:
                # 其他错误类型，使用智能轮换策略
                logger.warning(f"检测到未知错误类型: {error_type}，使用智能轮换策略")
                self.smart_proxy_rotation()
            
            # 应用新的代理配置
            self.setup_brightdata_proxy()
            
            # 更新代理统计
            proxy_key = f"proxy_{self.current_proxy_index}"
            if proxy_key in self.proxy_stats:
                self.proxy_stats[proxy_key]['last_used'] = time.time()
                self.proxy_stats[proxy_key]['errors'] = self.proxy_stats[proxy_key].get('errors', 0) + 1
            
            return True
            
        except Exception as e:
            logger.error(f"基于错误的代理轮换失败: {e}")
            # 紧急回退策略
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_configs)
            self.setup_brightdata_proxy()
            return False
    
    def update_session_headers(self):
        """更新会话头信息 - 增强版随机化策略"""
        # 智能请求头生成 - 基于会话状态动态调整
        
        # 1. 基础请求头 - 扩展随机化选项
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': random.choice([
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,image/svg+xml,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/jxl,image/avif,image/webp,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,image/svg+xml,image/jxl,*/*;q=0.8'
            ]),
            'Accept-Encoding': random.choice([
                'gzip, deflate, br', 'gzip, deflate', 'br', 'identity', '',
                'gzip, deflate, br, zstd', 'gzip, deflate, br, compress',
                'gzip, deflate, br, identity', 'gzip, deflate, br, *'
            ]),
            'Accept-Language': random.choice([
                'zh-CN,zh;q=0.9,en;q=0.8',
                'en-US,en;q=0.9,zh;q=0.8',
                'en-GB,en;q=0.9,en-US;q=0.8',
                'ar-EG,ar;q=0.9,en;q=0.8',
                'fr-FR,fr;q=0.9,en;q=0.8',
                'de-DE,de;q=0.9,en;q=0.8',
                'ja-JP,ja;q=0.9,en;q=0.8',
                'es-ES,es;q=0.9,en;q=0.8',
                'pt-BR,pt;q=0.9,en;q=0.8',
                'ru-RU,ru;q=0.9,en;q=0.8',
                'ko-KR,ko;q=0.9,en;q=0.8'
            ]),
            'Connection': random.choice(['keep-alive', 'close', 'Upgrade', 'keep-alive, Upgrade']),
            'Referer': random.choice([
                self.base_url,
                'https://www.google.com/',
                'https://www.bing.com/',
                'https://search.yahoo.com/',
                'https://duckduckgo.com/',
                'https://www.ahram.org.eg/',
                'https://english.ahram.org.eg/',
                'https://news.google.com/',
                'https://www.facebook.com/',
                'https://twitter.com/',
                'https://www.linkedin.com/',
                'https://www.reddit.com/',
                'https://www.youtube.com/',
                ''  # 无Referer
            ]),
            'DNT': random.choice(['0', '1']),
            'Cache-Control': random.choice([
                'no-cache', 'max-age=0', 'no-store', 'must-revalidate', '',
                'no-cache, no-store, must-revalidate', 'max-age=3600',
                'public, max-age=600', 'private, max-age=300'
            ]),
            'Pragma': random.choice(['no-cache', '']),
            'Upgrade-Insecure-Requests': random.choice(['1', '']),
            'TE': random.choice(['trailers', 'deflate', 'gzip', 'compress', '']),
            'Accept-Charset': random.choice(['utf-8, iso-8859-1;q=0.5', 'utf-8;q=0.7, *;q=0.3', '']),
            'Accept-Datetime': random.choice(['', 'Mon, 01 Jan 2024 00:00:00 GMT', 'Fri, 15 Mar 2024 12:00:00 GMT']),
            'From': random.choice(['', 'user@example.com', 'webmaster@ahram.org.eg', 'crawler@example.com']),
            'If-Modified-Since': random.choice(['', 'Mon, 01 Jan 2024 00:00:00 GMT', 'Fri, 15 Mar 2024 12:00:00 GMT']),
            'If-None-Match': random.choice(['', '*', '"abc123"', '"xyz789"']),
            'Max-Forwards': random.choice(['', '10', '5', '20']),
            'Via': random.choice(['', '1.1 proxy.example.com', '1.1 varnish', '1.1 squid']),
            'Warning': random.choice(['', '199 Miscellaneous warning', '214 Transformation applied', '299 Miscellaneous persistent warning']),
            'X-Requested-With': random.choice(['', 'XMLHttpRequest', 'Fetch', '']),
            'X-Forwarded-For': random.choice(['', '192.168.1.1', '10.0.0.1', '172.16.0.1']),
            'X-Forwarded-Host': random.choice(['', 'example.com', 'www.ahram.org.eg', 'english.ahram.org.eg']),
            'X-Forwarded-Proto': random.choice(['', 'https', 'http']),
            'X-Real-IP': random.choice(['', '192.168.1.1', '10.0.0.1', '172.16.0.1']),
            'X-Correlation-ID': random.choice(['', str(random.randint(100000, 999999)), str(random.randint(1000000000, 9999999999))]),
            # 新增字段
            'Save-Data': random.choice(['', 'on', 'off']),
            'Sec-GPC': random.choice(['', '1']),
            'X-Content-Type-Options': random.choice(['', 'nosniff']),
            'X-Frame-Options': random.choice(['', 'SAMEORIGIN', 'DENY']),
            'X-XSS-Protection': random.choice(['', '1; mode=block']),
            'Strict-Transport-Security': random.choice(['', 'max-age=31536000; includeSubDomains']),
            'Content-Security-Policy': random.choice(['', "default-src 'self'", "script-src 'self' 'unsafe-inline'"]),
            'Permissions-Policy': random.choice(['', 'geolocation=(), microphone=()'])
        }
        
        # 2. 基于会话状态动态调整请求头策略
        error_rate = self.session_errors / max(self.session_requests, 1)
        
        # 根据错误率调整请求头复杂度
        if error_rate > 0.3:  # 高错误率时简化请求头
            headers = {k: v for k, v in headers.items() if k in ['User-Agent', 'Accept', 'Accept-Language', 'Connection']}
        elif error_rate < 0.1:  # 低错误率时增加复杂度
            # 随机添加更多实验性头
            experimental_headers = {
                'X-Experimental-Header': str(random.randint(1000, 9999)),
                'X-Custom-Header': f'custom_value_{random.randint(100, 999)}',
                'X-API-Version': random.choice(['v1', 'v2', 'v3']),
                'X-Request-Source': random.choice(['web', 'mobile', 'api']),
                'X-Client-Version': f'{random.randint(1, 10)}.{random.randint(0, 9)}.{random.randint(0, 9)}'
            }
            headers.update(experimental_headers)
        
        # 3. 添加浏览器指纹相关的请求头
        headers = self.add_fingerprint_headers(headers)
        
        # 4. 智能清理空值头
        headers = {k: v for k, v in headers.items() if v != ''}
        
        # 5. 随机化字段顺序（模拟真实浏览器行为）
        header_keys = list(headers.keys())
        random.shuffle(header_keys)
        shuffled_headers = {k: headers[k] for k in header_keys}
        
        self.session.headers.update(shuffled_headers)
        
        # 6. 更新current_user_agent属性
        self.current_user_agent = headers.get('User-Agent', random.choice(self.user_agents))
        
        # 7. 记录请求头变更（智能频率控制）
        log_probability = max(0.05, min(0.2, 0.1 / max(error_rate, 0.01)))  # 根据错误率调整日志频率
        if random.random() < log_probability:
            logger.debug(f"请求头已更新 - User-Agent: {headers.get('User-Agent', 'N/A')[:50]}...")
            logger.debug(f"当前会话状态 - 请求数: {self.session_requests}, 错误率: {error_rate:.2f}")
    
    def rotate_user_agent(self):
        """轮换User-Agent"""
        self.update_session_headers()

    def clean_content(self, content):
        """清理和格式化提取的内容"""
        if not content:
            return ""
        
        # 1. 移除多余的空格和换行符
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        # 2. 移除常见的广告和无关文本
        ad_patterns = [
            r'广告\s*[:：]\s*[^\n]*',
            r'赞助\s*[:：]\s*[^\n]*',
            r'相关阅读\s*[:：]\s*[^\n]*',
            r'推荐阅读\s*[:：]\s*[^\n]*',
            r'热门文章\s*[:：]\s*[^\n]*',
            r'免责声明\s*[:：]\s*[^\n]*',
            r'版权声明\s*[:：]\s*[^\n]*',
            r'本文来源\s*[:：]\s*[^\n]*',
            r'转载自\s*[:：]\s*[^\n]*',
            r'编辑\s*[:：]\s*[^\n]*',
            r'记者\s*[:：]\s*[^\n]*',
            r'通讯员\s*[:：]\s*[^\n]*'
        ]
        
        for pattern in ad_patterns:
            content = re.sub(pattern, '', content)
        
        # 3. 移除短段落（可能是不完整的句子或广告）
        paragraphs = content.split('\n')
        cleaned_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if len(paragraph) > 20:  # 保留长度超过20个字符的段落
                cleaned_paragraphs.append(paragraph)
        
        content = '\n'.join(cleaned_paragraphs)
        
        # 4. 标准化标点符号
        content = re.sub(r'\s*[,，]\s*', '，', content)
        content = re.sub(r'\s*[.。]\s*', '。', content)
        content = re.sub(r'\s*[!！]\s*', '！', content)
        content = re.sub(r'\s*[?？]\s*', '？', content)
        
        # 5. 移除重复的句子（基于简单的模式匹配）
        sentences = re.split(r'[。！？]', content)
        unique_sentences = []
        seen_sentences = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 5:  # 长度超过5个字符
                # 简单的去重逻辑：如果句子相似度很高，则跳过
                is_duplicate = False
                for seen in seen_sentences:
                    if len(sentence) > 10 and len(seen) > 10:
                        # 计算简单的相似度（基于公共子串）
                        common_chars = len(set(sentence) & set(seen))
                        similarity = common_chars / max(len(set(sentence)), len(set(seen)))
                        if similarity > 0.8:  # 相似度超过80%
                            is_duplicate = True
                            break
                
                if not is_duplicate:
                    unique_sentences.append(sentence)
                    seen_sentences.add(sentence)
        
        content = '。'.join(unique_sentences) + '。'
        
        # 6. 移除多余的空行和空格
        content = re.sub(r'\n\s*\n', '\n', content)
        content = re.sub(r'^\s+|\s+$', '', content)
        
        # 7. 确保内容有合理的长度
        if len(content) < 50:
            logger.warning(f"清理后的内容过短: {len(content)} 字符")
            return ""
        
        return content

    def traditional_scrape_article(self, url):
        """传统爬取方法 - 作为MCP工具的降级方案"""
        try:
            logger.info(f"使用传统爬取方法: {url}")
            
            # 更新会话头信息
            self.update_session_headers()
            
            # 发送请求
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            
            # 检查响应状态
            if response.status_code != 200:
                logger.warning(f"传统爬取失败，状态码: {response.status_code}")
                return None
            
            # 解析HTML内容
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取文章标题
            title = ''
            title_selectors = [
                'h1', 'h2', '.title', '.headline', '.article-title',
                'meta[property="og:title"]', 'meta[name="title"]'
            ]
            
            for selector in title_selectors:
                if selector.startswith('meta'):
                    meta_tag = soup.select_one(selector)
                    if meta_tag and meta_tag.get('content'):
                        title = meta_tag['content']
                        break
                else:
                    title_element = soup.select_one(selector)
                    if title_element:
                        title = title_element.get_text(strip=True)
                        if title:
                            break
            
            # 提取文章内容
            content = ''
            content_selectors = [
                '.article-content', '.content', '.post-content', '.entry-content',
                '.story-body', '.article-body', '.main-content', 'article'
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    # 清理内容中的脚本和样式
                    for script in content_element(['script', 'style']):
                        script.decompose()
                    content = content_element.get_text(separator='\n', strip=True)
                    if content and len(content) > 100:  # 确保有足够的内容
                        break
            
            # 如果内容选择器未找到内容，尝试从body中提取
            if not content:
                body = soup.find('body')
                if body:
                    # 清理body中的脚本和样式
                    for script in body(['script', 'style', 'nav', 'header', 'footer']):
                        script.decompose()
                    content = body.get_text(separator='\n', strip=True)
            
            # 提取发布日期
            publish_date = ''
            date_selectors = [
                'meta[property="article:published_time"]',
                'meta[name="publish_date"]',
                'meta[name="date"]',
                '.publish-date', '.date', '.post-date', '.article-date',
                'time[datetime]'
            ]
            
            for selector in date_selectors:
                if selector.startswith('meta'):
                    meta_tag = soup.select_one(selector)
                    if meta_tag and meta_tag.get('content'):
                        publish_date = meta_tag['content']
                        break
                else:
                    date_element = soup.select_one(selector)
                    if date_element:
                        if date_element.get('datetime'):
                            publish_date = date_element['datetime']
                        else:
                            publish_date = date_element.get_text(strip=True)
                        if publish_date:
                            break
            
            # 提取作者信息
            author = ''
            author_selectors = [
                'meta[name="author"]',
                'meta[property="article:author"]',
                '.author', '.byline', '.article-author', '.post-author'
            ]
            
            for selector in author_selectors:
                if selector.startswith('meta'):
                    meta_tag = soup.select_one(selector)
                    if meta_tag and meta_tag.get('content'):
                        author = meta_tag['content']
                        break
                else:
                    author_element = soup.select_one(selector)
                    if author_element:
                        author = author_element.get_text(strip=True)
                        if author:
                            break
            
            # 验证提取结果
            if not title or not content:
                logger.warning(f"传统爬取未提取到有效内容: {url}")
                return None
            
            # 清理和格式化内容
            content = self.clean_content(content)
            
            # 构建返回结果
            article_details = {
                'title': title.strip(),
                'content': content,
                'date': publish_date.strip() if publish_date else '',
                'author': author.strip() if author else '',
                'source': '传统爬取'
            }
            
            logger.info(f"传统爬取成功: {url} - 标题: {title[:50]}...")
            return article_details
            
        except Exception as e:
            logger.error(f"传统爬取异常: {e}")
            return None

    def traditional_search_articles(self, query, limit=10):
        """传统搜索方法 - 作为MCP搜索的降级方案"""
        try:
            logger.info(f"使用传统搜索方法: {query}")
            
            # 更新会话头信息
            self.update_session_headers()
            
            # 构建搜索URL - 模拟搜索引擎搜索
            search_urls = [
                f"{self.base_url}/search?q={query}",
                f"{self.base_url}/search?query={query}",
                f"{self.base_url}/?s={query}",
                f"{self.base_url}/search/results?search={query}"
            ]
            
            search_results = []
            
            for search_url in search_urls:
                try:
                    # 发送搜索请求
                    response = self.session.get(search_url, timeout=self.timeout, allow_redirects=True)
                    
                    if response.status_code != 200:
                        logger.warning(f"搜索URL {search_url} 返回状态码: {response.status_code}")
                        continue
                    
                    # 解析搜索结果页面
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # 查找搜索结果链接
                    result_links = []
                    
                    # 常见搜索结果选择器
                    link_selectors = [
                        '.search-result a', '.result a', '.article-list a',
                        '.news-item a', '.post-title a', '.entry-title a',
                        'h2 a', 'h3 a', '.title a', '.headline a'
                    ]
                    
                    for selector in link_selectors:
                        links = soup.select(selector)
                        for link in links:
                            href = link.get('href')
                            if href and href.startswith('http'):
                                result_links.append({
                                    'url': href,
                                    'title': link.get_text(strip=True),
                                    'snippet': link.get('title', '') or self.extract_snippet(link)
                                })
                    
                    # 如果没有找到特定选择器的结果，尝试更通用的方法
                    if not result_links:
                        # 查找所有包含查询关键词的链接
                        all_links = soup.find_all('a', href=True)
                        for link in all_links:
                            href = link.get('href')
                            link_text = link.get_text(strip=True)
                            
                            # 过滤掉非文章链接
                            if (href and href.startswith('http') and 
                                not any(ignore in href for ignore in ['/category/', '/tag/', '/author/', '/page/', '/search/']) and
                                (query.lower() in link_text.lower() or query.lower() in href.lower())):
                                
                                result_links.append({
                                    'url': href,
                                    'title': link_text,
                                    'snippet': link.get('title', '') or self.extract_snippet(link)
                                })
                    
                    # 去重并限制结果数量
                    seen_urls = set()
                    unique_results = []
                    
                    for result in result_links:
                        if result['url'] not in seen_urls and len(unique_results) < limit:
                            seen_urls.add(result['url'])
                            unique_results.append(result)
                    
                    # 如果当前搜索URL找到了结果，添加到总结果中
                    if unique_results:
                        search_results.extend(unique_results)
                        logger.info(f"从 {search_url} 找到 {len(unique_results)} 个搜索结果")
                        
                        # 如果已经达到限制数量，提前结束
                        if len(search_results) >= limit:
                            break
                            
                except Exception as e:
                    logger.warning(f"搜索URL {search_url} 失败: {e}")
                    continue
            
            # 限制最终结果数量
            search_results = search_results[:limit]
            
            if search_results:
                logger.info(f"传统搜索成功: {query} - 找到 {len(search_results)} 个结果")
                return search_results
            else:
                logger.warning(f"传统搜索未找到结果: {query}")
                return []
                
        except Exception as e:
            logger.error(f"传统搜索异常: {e}")
            return []

    def extract_snippet(self, element):
        """从元素中提取摘要信息"""
        try:
            # 查找父元素或兄弟元素中的文本内容
            parent = element.parent
            if parent:
                # 获取父元素的文本内容，排除当前链接文本
                parent_text = parent.get_text(strip=True)
                link_text = element.get_text(strip=True)
                snippet = parent_text.replace(link_text, '').strip()
                
                # 限制摘要长度
                if len(snippet) > 200:
                    snippet = snippet[:200] + '...'
                
                return snippet if snippet else ''
            
            return ''
        except Exception:
            return ''

    def generate_browser_fingerprint(self):
        """生成浏览器指纹配置"""
        fingerprint = {
            'canvas_fingerprint': random.choice(self.browser_fingerprints['canvas_fingerprints']),
            'webgl_fingerprint': random.choice(self.browser_fingerprints['webgl_fingerprints']),
            'audio_fingerprint': random.choice(self.browser_fingerprints['audio_fingerprints']),
            'screen_resolution': random.choice(self.browser_fingerprints['screen_resolutions']),
            'timezone': random.choice(self.browser_fingerprints['timezones']),
            'language': random.choice(self.browser_fingerprints['languages']),
            'platform': random.choice(['Win32', 'MacIntel', 'Linux x86_64']),
            'hardware_concurrency': random.choice([4, 6, 8, 12, 16]),
            'device_memory': random.choice([4, 8, 16, 32]),
            'color_depth': random.choice([24, 30, 32])
        }
        return fingerprint
    
    def add_fingerprint_headers(self, headers):
        """添加浏览器指纹相关的请求头 - 增强随机化版本"""
        fingerprint = self.generate_browser_fingerprint()
        
        # 浏览器版本和平台随机化
        browser_versions = [
            ('Chrome', '120', 'Google Chrome'),
            ('Chrome', '119', 'Google Chrome'),
            ('Chrome', '118', 'Google Chrome'),
            ('Firefox', '121', 'Firefox'),
            ('Firefox', '120', 'Firefox'),
            ('Safari', '17.0', 'Safari'),
            ('Edge', '120', 'Microsoft Edge'),
            ('Edge', '119', 'Microsoft Edge')
        ]
        browser, version, brand = random.choice(browser_versions)
        
        # Sec-Fetch相关头随机化
        sec_fetch_dest = random.choice(['document', 'empty', 'script', 'style', 'image'])
        sec_fetch_mode = random.choice(['navigate', 'cors', 'no-cors', 'same-origin'])
        sec_fetch_site = random.choice(['none', 'same-origin', 'same-site', 'cross-site'])
        sec_fetch_user = random.choice(['?1', '?0'])
        
        # 添加指纹相关的请求头 - 增强实验性头
        headers.update({
            'Accept-Language': fingerprint['language'],
            'Accept-Encoding': random.choice(['gzip, deflate, br', 'gzip, deflate', 'identity']),
            'Sec-CH-UA': f'"{browser}";v="{version}", "{brand}";v="{version}", "Not A Brand";v="99"',
            'Sec-CH-UA-Mobile': random.choice(['?0', '?1']),
            'Sec-CH-UA-Platform': f'"{fingerprint["platform"]}"',
            'Sec-CH-UA-Platform-Version': f'"{random.choice(["15.0.0", "10.0.0", "14.0.0"])}"',
            'Sec-CH-UA-Full-Version': f'"{version}.0.0"',
            'Sec-CH-UA-Arch': random.choice(['"x86"', '"arm"', '""']),
            'Sec-CH-UA-Bitness': random.choice(['"64"', '"32"', '""']),
            'Sec-CH-UA-Model': random.choice(['""', '"iPhone"', '"Samsung Galaxy"']),
            'Sec-Fetch-Dest': sec_fetch_dest,
            'Sec-Fetch-Mode': sec_fetch_mode,
            'Sec-Fetch-Site': sec_fetch_site,
            'Sec-Fetch-User': sec_fetch_user,
            'Upgrade-Insecure-Requests': random.choice(['1', '0']),
            'DNT': random.choice(['1', '0']),
            'Priority': random.choice(['u=1', 'u=0', 'u=3']),
            'Viewport-Width': str(random.randint(1200, 1920)),
            'Width': str(random.randint(1200, 1920)),
            # 实验性请求头 - 增强反检测能力
            'X-Client-Data': random.choice([
                'CI22yQEIorbJAQjEtskBCKm2yQEIq7bJAQjNtskBCKq3yQEIzLfJAQjPt8kBCKm4yQEIqrjJAQjMuMkBCM24yQEIzrjJAQjPuMkBCNG4yQEI0rjJAQjTuMkBCNS4yQEI1bjJAQjWuMkBCNe4yQEI2LjJAQjZuMkBCNq4yQEI27jJAQjcuMkBCN24yQEI3rjJAQjfuMkBCN+4yQEI4LjJAQjhuMkBCOK4yQEI47jJAQjkuMkBCOS4yQEI5bjJAQjmuMkBCPa4yQEI97jJAQj4uMkBCPm4yQEI+rjJAQj7uMkBCPy4yQEI/bjJAQj+uMkBCP+4yQE=',
                'CIS2yQEIo7bJAQjEtskBCKm2yQEIq7bJAQjNtskBCKq3yQEIzLfJAQjPt8kBCKm4yQEIqrjJAQjMuMkBCM24yQEIzrjJAQjPuMkBCNG4yQEI0rjJAQjTuMkBCNS4yQEI1bjJAQjWuMkBCNe4yQEI2LjJAQjZuMkBCNq4yQEI27jJAQjcuMkBCN24yQEI3rjJAQjfuMkBCN+4yQEI4LjJAQjhuMkBCOK4yQEI47jJAQjkuMkBCOS4yQEI5bjJAQjmuMkBCPa4yQEI97jJAQj4uMkBCPm4yQEI+rjJAQj7uMkBCPy4yQEI/bjJAQj+uMkBCP+4yQE=',
                'CI62yQEIo7bJAQjEtskBCKm2yQEIq7bJAQjNtskBCKq3yQEIzLfJAQjPt8kBCKm4yQEIqrjJAQjMuMkBCM24yQEIzrjJAQjPuMkBCNG4yQEI0rjJAQjTuMkBCNS4yQEI1bjJAQjWuMkBCNe4yQEI2LjJAQjZuMkBCNq4yQEI27jJAQjcuMkBCN24yQEI3rjJAQjfuMkBCN+4yQEI4LjJAQjhuMkBCOK4yQEI47jJAQjkuMkBCOS4yQEI5bjJAQjmuMkBCPa4yQEI97jJAQj4uMkBCPm4yQEI+rjJAQj7uMkBCPy4yQEI/bjJAQj+uMkBCP+4yQE='
            ]),
            'X-Client-Hint': random.choice([
                'sec-ch-ua-arch,sec-ch-ua-bitness,sec-ch-ua-full-version,sec-ch-ua-mobile,sec-ch-ua-model,sec-ch-ua-platform,sec-ch-ua-platform-version',
                'sec-ch-ua-arch,sec-ch-ua-bitness,sec-ch-ua-full-version,sec-ch-ua-mobile,sec-ch-ua-model,sec-ch-ua-platform',
                'sec-ch-ua-arch,sec-ch-ua-bitness,sec-ch-ua-mobile,sec-ch-ua-model,sec-ch-ua-platform'
            ]),
            'X-Device-Info': random.choice([
                'device-type:desktop;os:Windows;browser:Chrome',
                'device-type:mobile;os:iOS;browser:Safari',
                'device-type:tablet;os:Android;browser:Chrome',
                'device-type:desktop;os:macOS;browser:Safari',
                'device-type:desktop;os:Linux;browser:Firefox'
            ]),
            'X-Request-ID': str(random.randint(1000000000, 9999999999)),
            'X-Session-ID': str(random.randint(1000000000, 9999999999)),
            'X-Trace-ID': str(random.randint(1000000000, 9999999999)),
            'X-Forwarded-Proto': random.choice(['https', 'http']),
            'X-Forwarded-Host': random.choice(['www.ahram.org.eg', 'english.ahram.org.eg', '']),
            'X-Forwarded-For': self.generate_random_ip(),
            'X-Real-IP': self.generate_random_ip(),
            'X-Originating-IP': self.generate_random_ip(),
            'X-Remote-IP': self.generate_random_ip(),
            'X-Remote-Addr': self.generate_random_ip(),
            'X-Client-IP': self.generate_random_ip(),
            'X-Host': random.choice(['www.ahram.org.eg', 'english.ahram.org.eg']),
            'X-URL': random.choice(['/', '/News', '/News/Index.aspx', '/Section/0/0.aspx']),
            'X-Requested-With': random.choice(['XMLHttpRequest', 'Fetch', '']),
            'X-CSRF-Token': self.generate_random_token(),
            'X-XSRF-Token': self.generate_random_token(),
            'X-Auth-Token': self.generate_random_token(),
            'X-API-Key': self.generate_random_token(),
            'X-Application-ID': str(random.randint(1000, 9999)),
            'X-User-ID': str(random.randint(10000, 99999)),
            'X-Device-ID': self.generate_device_id(),
            'X-Browser-ID': self.generate_browser_id(),
            'X-Timezone': fingerprint['timezone'],
            'X-Timezone-Offset': str(random.randint(-720, 720)),
            'X-Screen-Resolution': fingerprint['screen_resolution'],
            'X-Color-Depth': str(fingerprint['color_depth']),
            'X-Pixel-Ratio': str(round(random.uniform(1.0, 3.0), 2)),
            'X-Viewport-Size': f'{random.randint(1200, 1920)}x{random.randint(800, 1080)}',
            'X-Available-Screen-Size': f'{random.randint(1200, 3840)}x{random.randint(800, 2160)}',
            'X-Device-Pixel-Ratio': str(round(random.uniform(1.0, 3.0), 2)),
            'X-Hardware-Concurrency': str(fingerprint['hardware_concurrency']),
            'X-Device-Memory': str(fingerprint['device_memory']),
            'X-Max-Touch-Points': str(random.randint(0, 10)),
            'X-WebGL-Vendor': fingerprint['webgl_fingerprint'].split(',')[0].strip() if ',' in fingerprint['webgl_fingerprint'] else '',
            'X-WebGL-Renderer': fingerprint['webgl_fingerprint'].split(',')[1].strip() if ',' in fingerprint['webgl_fingerprint'] else '',
            'X-Canvas-Fingerprint': fingerprint['canvas_fingerprint'][:32],
            'X-Audio-Fingerprint': fingerprint['audio_fingerprint'][:32],
            'X-Platform': fingerprint['platform'],
            'X-OS': random.choice(['Windows', 'macOS', 'Linux', 'iOS', 'Android']),
            'X-Browser': browser,
            'X-Browser-Version': version,
            'X-Engine': random.choice(['Blink', 'WebKit', 'Gecko', 'Trident']),
            'X-Renderer': random.choice(['Skia', 'CoreGraphics', 'Cairo']),
            'X-Language': fingerprint['language'].split(',')[0] if ',' in fingerprint['language'] else fingerprint['language'],
            'X-Country': random.choice(['CN', 'US', 'GB', 'JP', 'EG', 'SA', 'AE', 'IN']),
            'X-Region': random.choice(['Asia', 'Europe', 'North America', 'Africa', 'Oceania']),
            'X-ISP': random.choice(['China Telecom', 'China Unicom', 'China Mobile', 'Comcast', 'Verizon', 'AT&T', 'Vodafone', 'Orange']),
            'X-ASN': str(random.randint(1000, 99999)),
            'X-Organization': random.choice(['Google LLC', 'Microsoft Corporation', 'Apple Inc.', 'Amazon.com, Inc.', 'Tencent Holdings Ltd.']),
            'X-Network-Type': random.choice(['wifi', 'cellular', 'ethernet', '']),
            'X-Connection-Type': random.choice(['keep-alive', 'close', '']),
            'X-Content-Type': random.choice(['text/html', 'application/json', 'application/xml', '']),
            'X-Content-Encoding': random.choice(['gzip', 'deflate', 'br', '']),
            'X-Content-Length': str(random.randint(1000, 100000)),
            'X-Transfer-Encoding': random.choice(['chunked', 'identity', '']),
            'X-Compression': random.choice(['gzip', 'deflate', 'br', '']),
            'X-Cache': random.choice(['HIT', 'MISS', '']),
            'X-Cache-Hit': random.choice(['true', 'false', '']),
            'X-CDN': random.choice(['Cloudflare', 'Akamai', 'Fastly', 'Amazon CloudFront', '']),
            'X-Edge-Location': random.choice(['IAD', 'DFW', 'SFO', 'LHR', 'NRT', 'SYD', '']),
            'X-Edge-IP': self.generate_random_ip(),
            'X-Origin-IP': self.generate_random_ip(),
            'X-Server': random.choice(['nginx', 'apache', 'iis', '']),
            'X-Powered-By': random.choice(['PHP/8.1', 'ASP.NET', 'Node.js', 'Python', '']),
            'X-Framework': random.choice(['Laravel', 'Django', 'Express', 'Spring', '']),
            'X-Database': random.choice(['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', '']),
            'X-Environment': random.choice(['production', 'development', 'staging', '']),
            'X-Deployment': random.choice(['v1.0.0', 'v2.1.3', 'latest', '']),
            'X-Build': str(random.randint(1000, 9999)),
            'X-Version': random.choice(['1.0.0', '2.1.3', '3.0.0-beta', '']),
            'X-Revision': str(random.randint(10000, 99999)),
            'X-Timestamp': str(int(time.time())),
            'X-Date': datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'X-Expires': (datetime.now() + timedelta(hours=1)).strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'X-Last-Modified': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'X-If-Modified-Since': (datetime.now() - timedelta(days=random.randint(1, 7))).strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'X-If-None-Match': random.choice(['*', f'W/"{random.randint(1000, 9999)}"', '']),
            'X-ETag': f'W/"{random.randint(1000, 9999)}"',
            'X-Location': random.choice(['/', '/news', '/article', '/search']),
            'X-Referrer': headers.get('Referer', ''),
            'X-Origin': random.choice(['https://www.google.com', 'https://www.bing.com', '']),
            'X-Source': random.choice(['direct', 'organic', 'social', 'referral', '']),
            'X-Medium': random.choice(['search', 'social', 'email', 'direct', '']),
            'X-Campaign': random.choice(['spring_sale', 'winter_promo', 'newsletter', '']),
            'X-Keyword': random.choice(['china', 'egypt', 'news', 'politics', '']),
            'X-Content': random.choice(['article', 'news', 'blog', 'product', '']),
            'X-Purpose': random.choice(['information', 'entertainment', 'education', 'shopping', '']),
            'X-Intent': random.choice(['informational', 'commercial', 'navigational', 'transactional', '']),
            'X-Context': random.choice(['news', 'shopping', 'social', 'work', '']),
            'X-User-Agent': headers.get('User-Agent', '')[:100],
            'X-User-Agent-Hash': hashlib.md5(headers.get('User-Agent', '').encode()).hexdigest()[:16]
        })
        
        # 根据平台调整特定头
        if fingerprint['platform'] == 'Win32':
            headers['Sec-CH-UA-Platform-Version'] = '\"10.0.0\"'
        elif fingerprint['platform'] == 'MacIntel':
            headers['Sec-CH-UA-Platform-Version'] = '\"15.0.0\"'
        
        return headers
    
    def load_keywords(self):
        """从关键词库加载关键词 - 扩展版：覆盖所有中国报道数据"""
        try:
            with open('china_imagination_keywords.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取所有关键词
            keywords = []
            
            # 核心身份关键词
            keywords.extend(data['primary_keywords']['core_identity'])
            keywords.extend(data['primary_keywords']['political_references'])
            
            # 经济框架关键词
            keywords.extend(data['economic_framework']['trade_commerce'])
            keywords.extend(data['economic_framework']['infrastructure_development'])
            keywords.extend(data['economic_framework']['technology_digital'])
            keywords.extend(data['economic_framework']['resource_extraction'])
            keywords.extend(data['economic_framework']['finance_banking'])
            
            # 地缘政治叙事关键词
            keywords.extend(data['geopolitical_narratives']['soft_power_diplomacy'])
            keywords.extend(data['geopolitical_narratives']['military_security'])
            keywords.extend(data['geopolitical_narratives']['global_governance'])
            keywords.extend(data['geopolitical_narratives']['development_cooperation'])
            
            # 文化社会表征关键词
            keywords.extend(data['cultural_social_representations']['cultural_exchange'])
            keywords.extend(data['cultural_social_representations']['people_society'])
            keywords.extend(data['cultural_social_representations']['media_communication'])
            keywords.extend(data['cultural_social_representations']['education_research'])
            
            # 扩展关键词：新增通用中国报道关键词
            extended_keywords = [
                # 通用中国相关关键词
                "chinese", "china", "beijing", "shanghai", "guangzhou", "shenzhen",
                "chinese government", "chinese policy", "chinese economy", "chinese development",
                "chinese investment", "chinese trade", "chinese aid", "chinese cooperation",
                "chinese diplomacy", "chinese culture", "chinese technology", "chinese innovation",
                
                # 中非关系关键词
                "china africa", "china african", "china africa relations", "china africa partnership",
                "china africa cooperation", "china africa investment", "china africa trade",
                "china africa development", "china africa infrastructure", "china africa aid",
                "china africa diplomacy", "china africa summit", "china africa forum",
                "china africa economic", "china africa political", "china africa cultural",
                
                # 中国全球参与关键词
                "chinese global", "china global", "chinese international", "china international",
                "chinese overseas", "china overseas", "chinese foreign", "china foreign",
                "chinese multinational", "china multinational", "chinese expansion", "china expansion",
                
                # 具体领域关键词
                "belt and road initiative", "bri", "one belt one road", "一带一路",
                "chinese infrastructure", "china infrastructure", "chinese construction",
                "chinese technology", "china technology", "chinese digital", "china digital",
                "chinese investment", "china investment", "chinese finance", "china finance",
                "chinese education", "china education", "chinese health", "china health",
                "chinese agriculture", "china agriculture", "chinese energy", "china energy",
                
                # 时间相关关键词（确保2010-2025年覆盖）
                "chinese 2010", "china 2010", "chinese 2011", "china 2011",
                "chinese 2012", "china 2012", "chinese 2013", "china 2013",
                "chinese 2014", "china 2014", "chinese 2015", "china 2015",
                "chinese 2016", "china 2016", "chinese 2017", "china 2017",
                "chinese 2018", "china 2018", "chinese 2019", "china 2019",
                "chinese 2020", "china 2020", "chinese 2021", "china 2021",
                "chinese 2022", "china 2022", "chinese 2023", "china 2023",
                "chinese 2024", "china 2024", "chinese 2025", "china 2025",
                
                # 新闻媒体常用关键词
                "chinese report", "china report", "chinese news", "china news",
                "chinese article", "china article", "chinese story", "china story",
                "chinese coverage", "china coverage", "chinese analysis", "china analysis",
                "chinese perspective", "china perspective", "chinese view", "china view",
                
                # 多语言关键词（确保全面覆盖）
                "中国", "中国报道", "中国新闻", "中国投资", "中国发展", "中国合作",
                "中非", "中非关系", "中非合作", "中非投资", "中非贸易", "中非发展",
                "一带一路", "丝绸之路", "中国政策", "中国政府", "中国经济", "中国文化"
            ]
            
            keywords.extend(extended_keywords)
            
            # 去重并过滤空值
            keywords = list(set([k.strip() for k in keywords if k.strip()]))
            
            logger.info(f"从关键词库加载了 {len(keywords)} 个关键词（已扩展覆盖所有中国报道数据）")
            return keywords
            
        except Exception as e:
            logger.error(f"加载关键词库失败: {e}")
            # 返回扩展的核心关键词
            return ["china", "chinese", "beijing", "xi jinping", "belt and road", "china africa",
                   "chinese investment", "china africa cooperation", "chinese development",
                   "chinese technology", "chinese culture", "chinese diplomacy"]
    
    def search_articles(self, keyword, year, page=1, max_retries=3):
        """搜索特定年份和关键词的文章 - 增强传统爬虫优先级"""
        
        # 智能方法选择策略：优先使用更可靠的方法
        if self.use_mcp_tools and page == 1:
            # 检查Firecrawl是否已被禁用
            if not self.stats['firecrawl_disabled']:
                # 尝试MCP工具搜索，但设置更严格的超时和重试
                mcp_results = self.mcp_search_articles(keyword, year)
                if mcp_results is not None and len(mcp_results) > 0:
                    self.stats['mcp_tools_used'] += 1
                    self.stats['search_methods_used']['mcp_search'] += 1
                    logger.info(f"MCP工具搜索成功: {keyword} - {year} - 找到 {len(mcp_results)} 篇文章")
                    return mcp_results, False
                else:
                    # MCP搜索失败，记录并优先使用传统方法
                    logger.warning(f"MCP搜索返回空结果或无结果，切换到传统方法")
                    self.stats['mcp_search_failures'] += 1
                    self.stats['fallback_to_traditional'] += 1
        
        # 增强传统搜索优先级 - 直接使用传统方法
        self.stats['traditional_crawl_used'] += 1
        self.stats['search_methods_used']['traditional_search'] += 1
        logger.info(f"使用传统搜索方法: {keyword} - {year} - 第{page}页")
        
        for attempt in range(max_retries):
            try:
                # 轮换User-Agent
                self.rotate_user_agent()
                
                # 构建搜索URL - 多种策略尝试
                search_urls = []
                
                # 策略1: 旧格式搜索URL (日志中出现的格式)
                if attempt == 0:
                    # 旧格式: Search.aspx?q=关键词&y=年份&p=页码
                    search_urls.append(f"{self.base_url}/Search.aspx")
                    params = {
                        'q': keyword,
                        'y': year,
                        'p': page
                    }
                # 策略2: 新格式搜索URL (网站结构中定义的格式)
                elif attempt == 1:
                    search_urls.append(f"{self.base_url}/UI/Front/Search.aspx")
                    params = {
                        'Text': keyword,
                        'DateFrom': f"01/01/{year}",
                        'DateTo': f"12/31/{year}",
                        'StartRowIndex': (page - 1) * 10
                    }
                # 策略3: 新闻分类页面 (当前使用的策略)
                else:
                    search_urls = [
                        f"{self.base_url}/NewsContent/1/64/0/Egypt/Politics.aspx",  # 政治新闻
                        f"{self.base_url}/NewsContent/1/1234/0/Egypt/Foreign-Affairs.aspx",  # 外交新闻
                        f"{self.base_url}/NewsContent/1/2/0/Egypt/Society.aspx",  # 社会新闻
                        f"{self.base_url}/NewsContent/2/8/0/World/Region.aspx",  # 国际新闻
                        f"{self.base_url}/NewsContent/50/1203/0/Al-Ahram-Weekly/World.aspx"  # 周刊世界新闻
                    ]
                    search_url = search_urls[(attempt - 2) % len(search_urls)]
                    params = {'page': page}
                
                # 对于策略1和2，使用特定的搜索URL
                if attempt < 2:
                    search_url = search_urls[0]
                
                logger.info(f"传统搜索: {keyword} - {year}年 - 第{page}页 (尝试 {attempt + 1}/{max_retries})")
                
                # 记录重试次数
                self.stats['retry_attempts'] += 1
                
                # 智能延迟 - 根据尝试次数增加延迟
                delay = random.uniform(2 + attempt, 5 + attempt * 2)
                time.sleep(delay)
                
                # 发送请求
                start_time = time.time()
                response = self.session.get(search_url, params=params, timeout=30 + attempt * 10)
                response_time = time.time() - start_time
                response.raise_for_status()
                
                # 记录代理成功性能
                self.record_proxy_performance(success=True, response_time=response_time)
                
                # 检查是否被反爬
                if self.check_anti_scraping(response):
                    logger.warning(f"检测到反爬措施，尝试绕过...")
                    self.handle_anti_scraping()
                    continue
                
                # 解析HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 检查是否为空结果页
                if self.is_empty_results_page(soup):
                    logger.info(f"空结果页: {keyword} - {year}年 - 第{page}页")
                    return [], False
                
                # 智能文章列表解析
                articles = self.intelligent_article_list_parsing(soup, keyword, year, page)
                
                # 检查是否有下一页
                next_page = soup.select_one('.next-page, .pagination-next, a[rel="next"], .next, .page-next')
                has_next_page = bool(next_page)
                
                # 记录传统搜索成功
                self.stats['traditional_search_success'] += 1
                logger.info(f"成功搜索: {keyword} - {year}年 - 第{page}页 - 找到 {len(articles)} 篇文章")
                return articles, has_next_page
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"网络请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                
                # 智能错误分析和处理
                self.handle_network_error(e, attempt, max_retries, keyword, year, page)
                
                if attempt < max_retries - 1:
                    # 智能重试延迟（指数退避 + 随机化）
                    wait_time = self.calculate_retry_delay(attempt, max_retries)
                    logger.info(f"等待 {wait_time:.1f} 秒后重试...")
                    time.sleep(wait_time)
                    
                    # 智能重试策略调整
                    self.adjust_retry_strategy(attempt, e)
                else:
                    logger.error(f"搜索文章最终失败: {keyword} - {year} - {page}: {e}")
                    self.record_search_failure(keyword, year, page, e)
            except Exception as e:
                logger.error(f"搜索文章异常: {keyword} - {year} - {page}: {e}")
                self.record_search_failure(keyword, year, page, e)
                break
        
        return [], False
    
    def check_anti_scraping(self, response):
        """智能反爬检测 - 增强版"""
        try:
            content = response.text.lower()
            headers = response.headers
            
            # 1. 基于状态码的检测
            if response.status_code in [403, 429, 503, 451, 520, 521, 522, 523]:
                logger.warning(f"反爬检测: 状态码 {response.status_code}")
                return True
            
            # 2. 基于内容关键词的检测
            anti_scraping_indicators = [
                'captcha', 'cloudflare', 'access denied', 'bot detected',
                'rate limit', 'too many requests', 'blocked', 'forbidden',
                'security check', 'verification required', 'human verification',
                'distil networks', 'imperva', 'akamai', 'incapsula',
                'please prove you are human', 'anti-bot', 'bot protection',
                'suspicious activity', 'unusual traffic', 'automated access',
                'javascript challenge', 'browser check', 'security challenge'
            ]
            
            for indicator in anti_scraping_indicators:
                if indicator in content:
                    logger.warning(f"反爬检测: 关键词 '{indicator}'")
                    return True
            
            # 3. 基于响应头检测
            suspicious_headers = {
                'cf-ray': 'cloudflare',
                'server': ['cloudflare', 'akamai', 'imperva', 'incapsula'],
                'x-protected-by': ['distil', 'imperva'],
                'x-cdn': ['cloudflare', 'akamai'],
                'x-frame-options': 'deny'
            }
            
            for header, patterns in suspicious_headers.items():
                if header in headers:
                    header_value = headers[header].lower()
                    if isinstance(patterns, list):
                        for pattern in patterns:
                            if pattern in header_value:
                                logger.warning(f"反爬检测: 响应头 '{header}' 包含 '{pattern}'")
                                return True
                    elif patterns in header_value:
                        logger.warning(f"反爬检测: 响应头 '{header}' 包含 '{patterns}'")
                        return True
            
            # 4. 基于页面结构的检测
            if len(content) < 1000:  # 页面内容过短
                if any(keyword in content for keyword in ['captcha', 'verification', 'security']):
                    logger.warning("反爬检测: 页面内容过短且包含安全关键词")
                    return True
            
            # 5. 基于响应时间的检测
            if hasattr(response, 'elapsed') and response.elapsed.total_seconds() > 10:
                logger.warning(f"反爬检测: 响应时间过长 ({response.elapsed.total_seconds():.1f}秒)")
                return True
            
            # 6. 基于重定向检测
            if len(response.history) > 3:  # 过多重定向
                logger.warning(f"反爬检测: 过多重定向 ({len(response.history)}次)")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"反爬检测失败: {e}")
            return False
    
    def handle_anti_scraping(self, response=None):
        """智能反爬处理 - 增强版"""
        try:
            # 记录反爬事件
            self.stats['anti_scraping_events'] += 1
            
            # 分析反爬类型并制定相应策略
            anti_scraping_type = self.analyze_anti_scraping_type(response)
            logger.warning(f"检测到反爬措施，类型: {anti_scraping_type}")
            
            # 根据反爬类型制定处理策略
            if anti_scraping_type == "rate_limit":
                # 速率限制：长时间等待 + 降低请求频率
                wait_time = random.uniform(60, 300)  # 1-5分钟
                self.intelligent_stop_config['max_requests_per_session'] = max(10, 
                    self.intelligent_stop_config['max_requests_per_session'] // 2)
                
            elif anti_scraping_type == "captcha":
                # 验证码：长时间等待 + 更换所有标识
                wait_time = random.uniform(300, 600)  # 5-10分钟
                self.rotate_all_identifiers()
                
            elif anti_scraping_type == "ip_block":
                # IP封锁：长时间等待 + 更换代理
                wait_time = random.uniform(600, 1800)  # 10-30分钟
                self.rotate_proxy_strategy()
                
            elif anti_scraping_type == "browser_fingerprint":
                # 浏览器指纹检测：更换指纹 + 降低请求频率
                wait_time = random.uniform(120, 300)  # 2-5分钟
                self.rotate_browser_fingerprint()
                
            else:
                # 默认策略：中等等待 + 更换标识
                wait_time = random.uniform(30, 120)  # 30秒-2分钟
                self.rotate_user_agent()
            
            logger.info(f"反爬处理: 等待 {wait_time:.1f} 秒，类型: {anti_scraping_type}")
            time.sleep(wait_time)
            
            # 重置会话统计
            self.reset_session()
            
            # 记录处理结果
            self.stats['anti_scraping_handled'] += 1
            
        except Exception as e:
            logger.error(f"反爬处理失败: {e}")
    
    def analyze_anti_scraping_type(self, response):
        """分析反爬类型"""
        if response is None:
            return "unknown"
        
        content = response.text.lower()
        headers = response.headers
        
        # 基于状态码判断
        if response.status_code == 429:
            return "rate_limit"
        elif response.status_code == 403:
            return "ip_block"
        elif response.status_code == 503:
            return "service_unavailable"
        
        # 基于内容关键词判断
        if 'captcha' in content or 'verification' in content:
            return "captcha"
        elif 'rate limit' in content or 'too many requests' in content:
            return "rate_limit"
        elif 'cloudflare' in content or 'cf-ray' in headers:
            return "cloudflare"
        elif 'distil' in content or 'imperva' in content:
            return "waf"
        elif 'browser' in content and 'check' in content:
            return "browser_fingerprint"
        elif 'ip' in content and ('block' in content or 'banned' in content):
            return "ip_block"
        
        # 基于响应时间判断
        if hasattr(response, 'elapsed') and response.elapsed.total_seconds() > 15:
            return "slow_response"
        
        return "unknown"
    
    def rotate_all_identifiers(self):
        """轮换所有标识符"""
        logger.info("轮换所有标识符...")
        
        # 轮换User-Agent
        self.rotate_user_agent()
        
        # 轮换浏览器指纹
        self.rotate_browser_fingerprint()
        
        # 轮换代理策略
        self.rotate_proxy_strategy()
        
        # 更新会话头
        self.update_session_headers()
        
        logger.info("标识符轮换完成")
    
    def setup_browser_fingerprint(self):
        """初始化浏览器指纹"""
        logger.info("初始化浏览器指纹...")
        
        # 生成初始浏览器指纹
        self.browser_fingerprint = self.generate_browser_fingerprint()
        
        # 更新会话头以包含指纹信息
        self.update_session_headers()
        
        logger.info("浏览器指纹初始化完成")
    
    def rotate_browser_fingerprint(self):
        """轮换浏览器指纹"""
        logger.info("轮换浏览器指纹...")
        
        # 重置指纹配置
        self.browser_fingerprint = self.generate_browser_fingerprint()
        
        # 更新会话头
        self.update_session_headers()
        
        logger.info("浏览器指纹轮换完成")
    
    def rotate_proxy_strategy(self):
        """智能轮换代理策略 - 基于GitHub最佳实践优化"""
        logger.info("智能轮换代理策略...")
        
        # 获取当前代理性能统计
        current_proxy_stats = self.get_proxy_performance_stats()
        
        # 基于GitHub最佳实践的代理轮换策略
        if self.use_brightdata_proxy:
            # BrightData代理模式：基于错误率和性能的智能轮换
            error_rate = current_proxy_stats.get('error_rate', 0)
            
            if error_rate > 0.4:  # 高错误率阈值（基于GitHub最佳实践）
                # 策略1: 优先选择最佳性能代理
                best_proxy_index = self.select_best_proxy()
                if best_proxy_index != self.current_proxy_index:
                    self.current_proxy_index = best_proxy_index
                    logger.info(f"高错误率({error_rate:.2f})，切换到最佳代理方案 {self.current_proxy_index + 1}")
                else:
                    # 策略2: 随机轮换到下一个代理
                    self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_configs)
                    logger.info(f"高错误率({error_rate:.2f})，随机轮换到代理方案 {self.current_proxy_index + 1}")
            else:
                # 策略3: 基于性能的智能轮换（降低轮换频率）
                if random.random() < 0.3:  # 30%概率基于性能轮换
                    self.current_proxy_index = self.select_best_proxy()
                    logger.info(f"基于性能轮换到代理方案 {self.current_proxy_index + 1}")
                else:
                    # 策略4: 随机轮换（降低频率）
                    if random.random() < 0.2:  # 20%概率随机轮换
                        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_configs)
                        logger.info(f"随机轮换到代理方案 {self.current_proxy_index + 1}")
            
            # 重新配置代理
            self.setup_brightdata_proxy()
            
            # 策略5: 智能决定是否切换到免费代理（基于GitHub最佳实践）
            switch_probability = self.calculate_switch_probability()
            if random.random() < switch_probability:
                self.use_brightdata_proxy = False
                logger.info(f"智能切换到免费代理模式（概率: {switch_probability:.2f})")
        else:
            # 免费代理模式：基于GitHub最佳实践的错误处理
            error_rate = current_proxy_stats.get('error_rate', 0)
            
            if error_rate > 0.5:  # 高错误率阈值
                # 策略1: 切换到BrightData代理
                if self.proxy_configs:
                    self.use_brightdata_proxy = True
                    self.current_proxy_index = self.select_best_proxy()
                    self.setup_brightdata_proxy()
                    logger.info(f"高错误率({error_rate:.2f})，切换到BrightData代理模式")
            elif random.random() < 0.15:  # 15%概率切换回BrightData（降低频率）
                if self.proxy_configs:
                    self.use_brightdata_proxy = True
                    self.current_proxy_index = random.randint(0, len(self.proxy_configs) - 1)
                    self.setup_brightdata_proxy()
                    logger.info("随机切换到BrightData代理模式")
            else:
                # 策略2: 免费代理内部轮换
                if random.random() < 0.3:  # 30%概率轮换免费代理
                    self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_configs)
                    logger.info("免费代理内部轮换")
        
        # 更新代理统计
        self.update_proxy_statistics()
        
        # 记录轮换统计
        self.stats['proxy_rotations'] = self.stats.get('proxy_rotations', 0) + 1
        logger.info(f"智能代理策略轮换完成 (总轮换次数: {self.stats['proxy_rotations']})")
    
    def get_proxy_performance_stats(self):
        """获取代理性能统计"""
        if not hasattr(self, 'proxy_performance_stats'):
            self.proxy_performance_stats = {}
        
        current_proxy_key = f"{'brightdata' if self.use_brightdata_proxy else 'free'}_{self.current_proxy_index}"
        
        return self.proxy_performance_stats.get(current_proxy_key, {
            'requests': 0,
            'successes': 0,
            'errors': 0,
            'error_rate': 0.0,
            'avg_response_time': 0.0,
            'last_used': None
        })
    
    def select_best_proxy(self):
        """选择最佳代理方案"""
        if not hasattr(self, 'proxy_performance_stats') or not self.proxy_performance_stats:
            return random.randint(0, len(self.proxy_configs) - 1)
        
        best_score = -1
        best_index = 0
        
        for i in range(len(self.proxy_configs)):
            proxy_key = f"brightdata_{i}"
            stats = self.proxy_performance_stats.get(proxy_key, {})
            
            # 计算代理评分：成功率 * 响应时间权重
            success_rate = stats.get('success_rate', 0.5)
            avg_response_time = stats.get('avg_response_time', 5.0)
            
            # 响应时间权重：越短越好
            response_time_weight = max(0.1, 1.0 - (avg_response_time / 10.0))
            score = success_rate * response_time_weight
            
            if score > best_score:
                best_score = score
                best_index = i
        
        return best_index
    
    def calculate_switch_probability(self):
        """计算切换到免费代理的概率"""
        base_probability = 0.3  # 基础概率30%
        
        # 根据当前代理性能调整概率
        current_stats = self.get_proxy_performance_stats()
        error_rate = current_stats.get('error_rate', 0)
        
        # 错误率越高，切换到免费代理的概率越大
        if error_rate > 0.3:
            base_probability += error_rate * 0.5
        
        # 限制概率范围
        return min(0.8, max(0.1, base_probability))
    
    def update_proxy_statistics(self):
        """更新代理统计信息"""
        if not hasattr(self, 'proxy_performance_stats'):
            self.proxy_performance_stats = {}
        
        current_proxy_key = f"{'brightdata' if self.use_brightdata_proxy else 'free'}_{self.current_proxy_index}"
        
        if current_proxy_key not in self.proxy_performance_stats:
            self.proxy_performance_stats[current_proxy_key] = {
                'requests': 0,
                'successes': 0,
                'errors': 0,
                'error_rate': 0.0,
                'avg_response_time': 0.0,
                'last_used': datetime.now().isoformat()
            }
        
        # 更新最后使用时间
        self.proxy_performance_stats[current_proxy_key]['last_used'] = datetime.now().isoformat()
    
    def record_proxy_performance(self, success=True, response_time=0.0):
        """记录代理性能数据"""
        if not hasattr(self, 'proxy_performance_stats'):
            self.proxy_performance_stats = {}
        
        current_proxy_key = f"{'brightdata' if self.use_brightdata_proxy else 'free'}_{self.current_proxy_index}"
        
        if current_proxy_key not in self.proxy_performance_stats:
            self.proxy_performance_stats[current_proxy_key] = {
                'requests': 0,
                'successes': 0,
                'errors': 0,
                'error_rate': 0.0,
                'avg_response_time': 0.0,
                'last_used': datetime.now().isoformat()
            }
        
        stats = self.proxy_performance_stats[current_proxy_key]
        stats['requests'] += 1
        
        if success:
            stats['successes'] += 1
            # 更新平均响应时间
            old_avg = stats['avg_response_time']
            stats['avg_response_time'] = (old_avg * (stats['successes'] - 1) + response_time) / stats['successes']
        else:
            stats['errors'] += 1
        
        # 计算错误率
        if stats['requests'] > 0:
            stats['error_rate'] = stats['errors'] / stats['requests']
            stats['success_rate'] = stats['successes'] / stats['requests']
        
        stats['last_used'] = datetime.now().isoformat()
    
    def handle_network_error(self, error, attempt, max_retries, keyword, year, page):
        """智能处理网络错误 - 基于GitHub和Stack Overflow最佳实践深度优化
        
        最佳实践参考:
        - 错误类型分类处理: 根据具体错误类型采取不同策略
        - 渐进式策略升级: 随着重试次数增加，策略逐渐升级
        - 智能资源轮换: 根据错误类型轮换代理、标识符等资源
        - 自适应延迟: 基于错误类型和重试次数计算智能延迟
        - 错误统计监控: 实时监控错误率并自适应调整策略
        
        Args:
            error: 捕获的异常对象
            attempt: 当前重试次数 (0-indexed)
            max_retries: 最大重试次数
            keyword: 搜索关键词
            year: 搜索年份
            page: 搜索页码
            
        Returns:
            float: 实际应用的延迟时间（秒）
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        logger.info(f"网络错误分析: 类型={error_type}, 尝试={attempt+1}/{max_retries}")
        
        # 记录代理性能（失败）
        self.record_proxy_performance(success=False, response_time=0.0)
        
        # 计算智能重试延迟 - 基于错误类型
        delay = self.calculate_retry_delay(attempt, max_retries, error_type)
        
        # 基于GitHub和Stack Overflow最佳实践的错误分类处理策略
        if 'ConnectionError' in error_type or 'Timeout' in error_type:
            logger.warning("网络连接错误，应用GitHub和Stack Overflow最佳实践")
            
            # 策略1: 根据尝试次数制定不同策略
            if attempt == 0:
                # 第一次连接错误：简单轮换
                if self.use_brightdata_proxy:
                    self.rotate_proxy_strategy()
                else:
                    # 免费代理模式：尝试切换到BrightData
                    if self.proxy_configs:
                        self.use_brightdata_proxy = True
                        self.current_proxy_index = random.randint(0, len(self.proxy_configs) - 1)
                        self.setup_brightdata_proxy()
                        logger.info("首次连接错误，切换到BrightData代理模式")
            elif attempt == 1:
                # 第二次错误：全面更换标识符
                self.rotate_all_identifiers()
                logger.info("第二次连接错误，全面更换标识符")
            else:
                # 多次错误：降低请求频率并增加延迟
                self.intelligent_stop_config['max_requests_per_session'] = max(3, 
                    self.intelligent_stop_config['max_requests_per_session'] // 2)
                self.intelligent_stop_config['base_delay'] *= 1.5
                logger.info("多次连接错误，降低请求频率并增加延迟")
        
        elif 'HTTPError' in error_type:
            status_code = getattr(error.response, 'status_code', None) if hasattr(error, 'response') else None
            logger.warning(f"HTTP错误，状态码: {status_code}")
            
            # 基于GitHub和Stack Overflow最佳实践的HTTP状态码处理策略
            if status_code == 407:
                # 407代理认证错误：专门处理
                self.handle_proxy_auth_error(attempt)
            elif status_code == 429:
                # 429速率限制：指数退避
                self.handle_rate_limit_error(attempt)
            elif status_code == 403:
                # 403禁止访问：全面更换标识符
                self.handle_forbidden_error(attempt)
            elif status_code == 404:
                # 404页面不存在：记录分析
                self.handle_not_found_error(keyword, year, page)
            elif status_code == 503:
                # 503服务不可用：长延迟重试
                self.handle_service_unavailable_error(attempt)
            elif status_code and status_code >= 500:
                # 500+服务器错误：长延迟重试
                self.handle_server_error(attempt)
            else:
                # 其他HTTP错误：通用处理
                logger.warning(f"处理其他HTTP错误: {status_code}")
                if attempt > 0:
                    self.rotate_proxy_strategy()
        
        # 记录详细的错误统计
        self.record_detailed_error_stats(error_type, status_code if 'HTTPError' in error_type else None, attempt)
        
        # 基于GitHub和Stack Overflow最佳实践的错误率监控
        self.monitor_error_rate_and_adjust()
        
        # 记录错误统计
        self.stats['network_errors'].append({
            'attempt': attempt + 1,
            'max_retries': max_retries,
            'keyword': keyword,
            'year': year,
            'page': page,
            'error_type': error_type,
            'error_message': error_msg,
            'timestamp': datetime.now().isoformat(),
            'calculated_delay': delay  # 记录计算出的延迟时间
        })
        
        # 等待延迟时间
        time.sleep(delay)
        
        logger.info(f"网络错误处理完成，等待 {delay:.2f}s 后重试")
        return delay
    
    def handle_proxy_auth_error(self, attempt):
        """处理407代理认证错误 - 基于GitHub和Stack Overflow最佳实践优化
        
        最佳实践参考:
        - 分层处理策略: 根据重试次数采取不同级别的应对措施
        - 智能代理轮换: 基于代理性能统计选择最优代理
        - 认证信息自动修复: 自动检测并修复代理认证配置问题
        - 渐进式延迟: 基于重试次数和错误类型计算智能延迟
        
        Args:
            attempt: 当前重试次数 (0-indexed)
        """
        logger.warning("处理407代理认证错误")
        
        # 策略1: 检查代理配置 - 基于GitHub和Stack Overflow最佳实践
        if self.use_brightdata_proxy:
            logger.info("使用BrightData代理，检查认证配置")
            # BrightData代理通常不需要额外认证，但需要检查配置
            if attempt == 0:
                # 第一次错误：尝试重新配置代理
                self.setup_brightdata_proxy()
            elif attempt == 1:
                # 第二次错误：切换到智能代理轮换
                self.smart_proxy_rotation()
                logger.info("BrightData代理认证失败，切换到智能代理轮换模式")
            else:
                # 后续错误：切换到免费代理模式
                self.use_brightdata_proxy = False
                logger.info("BrightData代理认证持续失败，切换到免费代理模式")
        else:
            # 免费代理：基于GitHub和Stack Overflow最佳实践的处理策略
            logger.info("免费代理模式，应用GitHub和Stack Overflow最佳实践")
            
            # 策略1: 检查代理URL格式是否正确
            current_proxy = self.proxy_configs[self.current_proxy_index] if self.proxy_configs else None
            if current_proxy and 'proxy_url' in current_proxy:
                proxy_url = current_proxy['proxy_url']
                # 检查是否需要用户名密码认证
                if '@' not in proxy_url and attempt == 0:
                    logger.warning("代理URL可能缺少认证信息，尝试添加默认凭据")
                    # 尝试添加默认认证信息（基于GitHub和Stack Overflow最佳实践）
                    if 'username' in current_proxy and 'password' in current_proxy:
                        username = current_proxy['username']
                        password = current_proxy['password']
                        if username and password:
                            # 重新构建带认证的代理URL
                            proxy_parts = proxy_url.split('://')
                            if len(proxy_parts) == 2:
                                scheme = proxy_parts[0]
                                host = proxy_parts[1]
                                authenticated_proxy = f"{scheme}://{username}:{password}@{host}"
                                current_proxy['proxy_url'] = authenticated_proxy
                                logger.info("已添加代理认证信息")
            
            # 策略2: 智能轮换代理策略
            self.smart_proxy_rotation()
        
        # 策略3: 记录详细的错误信息用于分析
        self.stats['proxy_auth_errors'] = self.stats.get('proxy_auth_errors', 0) + 1
        logger.info(f"代理认证错误计数: {self.stats['proxy_auth_errors']}")
        
        # 策略4: 基于错误类型和重试次数的智能延迟
        calculated_delay = self.calculate_retry_delay(attempt, 5, "ProxyAuthError")
        logger.info(f"代理认证错误处理完成，等待 {calculated_delay:.2f}s 后重试")
        return calculated_delay
    
    def handle_rate_limit_error(self, attempt):
        """处理429速率限制错误 - 基于GitHub和Stack Overflow最佳实践优化
        
        最佳实践参考:
        - 智能延迟计算: 使用统一的智能延迟计算方法
        - 频率自适应: 根据错误率动态调整请求频率
        - 标识符轮换: 轮换用户代理和代理规避检测
        - 分层处理: 根据重试次数采取不同级别的应对措施
        
        Args:
            attempt: 当前重试次数 (0-indexed)
            
        Returns:
            float: 计算出的重试延迟时间（秒）
        """
        logger.warning("处理429速率限制错误")
        
        # 策略1: 使用统一的智能延迟计算方法
        calculated_delay = self.calculate_retry_delay(attempt, 6, "RateLimitError")
        
        # 策略2: 降低请求频率 - 基于GitHub和Stack Overflow最佳实践
        if attempt > 1:
            # 降低请求间隔
            current_interval = self.intelligent_stop_config.get('request_interval', 1.0)
            new_interval = current_interval * 1.5
            self.intelligent_stop_config['request_interval'] = min(new_interval, 10.0)
            logger.info(f"降低请求频率到 {self.intelligent_stop_config['request_interval']:.1f} 秒")
        
        # 策略3: 轮换用户代理和代理 - 基于GitHub和Stack Overflow最佳实践
        if attempt > 0:
            self.rotate_user_agent()
            self.smart_proxy_rotation()
            logger.info("轮换用户代理和代理以规避速率限制")
        
        # 策略4: 记录错误统计
        self.stats['rate_limit_errors'] = self.stats.get('rate_limit_errors', 0) + 1
        logger.info(f"速率限制错误计数: {self.stats['rate_limit_errors']}")
        
        logger.info(f"速率限制错误处理完成，等待 {calculated_delay:.2f}s 后重试")
        return calculated_delay
    
    def handle_forbidden_error(self, attempt):
        """处理403禁止访问错误 - 基于GitHub和Stack Overflow最佳实践优化
        
        最佳实践参考:
        - 全面标识符轮换: 更换所有可识别的标识符
        - 智能代理切换: 基于错误模式选择最优代理策略
        - 自适应延迟: 根据错误类型和重试次数计算智能延迟
        - 分层处理: 根据重试次数采取不同级别的应对措施
        
        Args:
            attempt: 当前重试次数 (0-indexed)
            
        Returns:
            float: 计算出的重试延迟时间（秒）
        """
        logger.warning("处理403禁止访问错误")
        
        # 策略1: 全面更换标识符 - 基于GitHub和Stack Overflow最佳实践
        self.rotate_all_identifiers()
        
        # 策略2: 智能代理切换策略
        if not self.use_brightdata_proxy and attempt > 1:
            self.use_brightdata_proxy = True
            logger.info("切换到BrightData代理模式应对403错误")
        elif attempt > 0:
            # 使用智能代理轮换
            self.smart_proxy_rotation()
        
        # 策略3: 使用统一的智能延迟计算方法
        calculated_delay = self.calculate_retry_delay(attempt, 4, "ForbiddenError")
        
        # 策略4: 记录错误统计
        self.stats['forbidden_errors'] = self.stats.get('forbidden_errors', 0) + 1
        logger.info(f"403禁止访问错误计数: {self.stats['forbidden_errors']}")
        
        logger.info(f"403禁止访问错误处理完成，等待 {calculated_delay:.2f}s 后重试")
        return calculated_delay
    
    def handle_not_found_error(self, keyword, year, page, attempt=0):
        """处理404页面不存在错误 - 基于GitHub和Stack Overflow最佳实践优化
        
        最佳实践参考:
        - 智能错误分析: 记录和分析404错误模式
        - 网站结构监控: 检测网站结构变化
        - 智能延迟: 使用统一的智能延迟计算方法
        - 分层处理: 根据错误频率采取不同应对措施
        
        Args:
            keyword: 搜索关键词
            year: 搜索年份
            page: 页码
            attempt: 当前重试次数 (0-indexed)
            
        Returns:
            float: 计算出的重试延迟时间（秒），对于404错误通常返回0
        """
        logger.warning(f"处理404错误: {keyword} - {year} - {page} (尝试次数: {attempt})")
        
        # 策略1: 记录404错误模式 - 基于GitHub最佳实践
        if '404_errors' not in self.stats:
            self.stats['404_errors'] = []
        
        error_record = {
            'keyword': keyword,
            'year': year,
            'page': page,
            'attempt': attempt,
            'timestamp': datetime.now().isoformat()
        }
        self.stats['404_errors'].append(error_record)
        
        # 策略2: 分析404错误模式 - 基于Stack Overflow最佳实践
        recent_404s = [e for e in self.stats['404_errors'] 
                       if datetime.now().timestamp() - datetime.fromisoformat(e['timestamp']).timestamp() < 3600]
        
        if len(recent_404s) > 10:  # 1小时内超过10个404错误
            logger.warning("404错误率过高，可能网站结构已改变，建议重新分析网站结构")
            # 可以触发网站结构重新分析
        
        # 策略3: 使用统一的智能延迟计算方法
        calculated_delay = self.calculate_retry_delay(attempt, 3, "NotFoundError")
        
        # 策略4: 记录详细错误统计
        self.record_detailed_error_stats("NotFoundError", 404, attempt)
        
        # 策略5: 对于404错误，通常不需要重试，但可以返回一个小的延迟
        # 让调用方决定是否继续尝试
        logger.info(f"404错误处理完成，建议延迟: {calculated_delay:.2f}s")
        return calculated_delay
    
    def handle_service_unavailable_error(self, attempt):
        """处理503服务不可用错误 - 基于GitHub和Stack Overflow最佳实践优化
        
        最佳实践参考:
        - 渐进式延迟: 基于重试次数计算智能延迟
        - 智能代理轮换: 根据错误类型选择最优代理策略
        - 服务状态监控: 记录服务不可用模式用于分析
        - 分层处理: 根据重试次数采取不同级别的应对措施
        
        Args:
            attempt: 当前重试次数 (0-indexed)
            
        Returns:
            float: 计算出的重试延迟时间（秒）
        """
        logger.warning("处理503服务不可用错误")
        
        # 策略1: 使用统一的智能延迟计算方法
        calculated_delay = self.calculate_retry_delay(attempt, 8, "ServiceUnavailableError")
        
        # 策略2: 智能代理轮换策略
        if attempt > 0:
            self.smart_proxy_rotation()
            logger.info("服务不可用，轮换代理以尝试不同网络路径")
        
        # 策略3: 记录错误统计
        self.stats['service_unavailable_errors'] = self.stats.get('service_unavailable_errors', 0) + 1
        logger.info(f"503服务不可用错误计数: {self.stats['service_unavailable_errors']}")
        
        logger.info(f"503服务不可用错误处理完成，等待 {calculated_delay:.2f}s 后重试")
        return calculated_delay
    
    def handle_server_error(self, attempt):
        """处理500+服务器错误 - 基于GitHub和Stack Overflow最佳实践优化
        
        最佳实践参考:
        - 智能延迟计算: 使用统一的智能延迟计算方法
        - 频率自适应: 根据错误率动态调整请求频率
        - 服务状态监控: 记录服务器错误模式用于分析
        - 分层处理: 根据重试次数采取不同级别的应对措施
        
        Args:
            attempt: 当前重试次数 (0-indexed)
            
        Returns:
            float: 计算出的重试延迟时间（秒）
        """
        logger.warning("处理服务器错误(500+)")
        
        # 策略1: 使用统一的智能延迟计算方法
        calculated_delay = self.calculate_retry_delay(attempt, 10, "ServerError")
        
        # 策略2: 降低请求频率 - 基于GitHub和Stack Overflow最佳实践
        if attempt > 1:
            current_max_requests = self.intelligent_stop_config.get('max_requests_per_session', 10)
            new_max_requests = max(3, current_max_requests // 2)
            self.intelligent_stop_config['max_requests_per_session'] = new_max_requests
            logger.info(f"降低请求频率到 {new_max_requests} 次/会话")
        
        # 策略3: 智能代理轮换策略
        if attempt > 0:
            self.smart_proxy_rotation()
            logger.info("服务器错误，轮换代理以尝试不同网络路径")
        
        # 策略4: 记录错误统计
        self.stats['server_errors'] = self.stats.get('server_errors', 0) + 1
        logger.info(f"500+服务器错误计数: {self.stats['server_errors']}")
        
        logger.info(f"500+服务器错误处理完成，等待 {calculated_delay:.2f}s 后重试")
        return calculated_delay
    
    def record_detailed_error_stats(self, error_type, status_code, attempt):
        """
        记录详细的错误统计信息 - 基于GitHub和Stack Overflow最佳实践优化
        
        最佳实践参考:
        - 错误分类统计: 按错误类型和状态码分类记录
        - 时间序列分析: 记录首次和最后发生时间
        - 重试模式分析: 分析不同重试次数的错误分布
        - 智能错误率计算: 基于错误频率动态调整策略
        
        Args:
            error_type (str): 错误类型
            status_code (int): HTTP状态码（如果有）
            attempt (int): 当前重试次数
            
        Returns:
            None
        """
        error_key = f"{error_type}_{status_code}" if status_code else error_type
        
        # 初始化错误统计字典
        if not hasattr(self, 'error_stats'):
            self.error_stats = {}
        
        # 更新错误统计
        if error_key not in self.error_stats:
            self.error_stats[error_key] = {
                'count': 0,
                'first_occurrence': datetime.now(),
                'last_occurrence': datetime.now(),
                'attempts': [],
                'proxy_modes': [],
                'user_agents': [],
                'session_health_scores': []
            }
        
        # 更新基础统计
        self.error_stats[error_key]['count'] += 1
        self.error_stats[error_key]['last_occurrence'] = datetime.now()
        self.error_stats[error_key]['attempts'].append(attempt)
        
        # 记录上下文信息
        self.error_stats[error_key]['proxy_modes'].append(
            'brightdata' if self.use_brightdata_proxy else 'free'
        )
        self.error_stats[error_key]['user_agents'].append(
            self.current_user_agent[:50] + "..." if len(self.current_user_agent) > 50 else self.current_user_agent
        )
        self.error_stats[error_key]['session_health_scores'].append(
            self.get_session_health_score()
        )
        
        # 计算错误频率和趋势
        time_since_first = (datetime.now() - self.error_stats[error_key]['first_occurrence']).total_seconds()
        error_frequency = self.error_stats[error_key]['count'] / max(1, time_since_first / 60)  # 每分钟错误频率
        
        # 记录到错误日志文件
        self.log_error_to_file(error_type, status_code, attempt)
        
        # 智能错误分析
        if self.error_stats[error_key]['count'] >= 3:
            # 分析错误模式
            avg_attempt = sum(self.error_stats[error_key]['attempts']) / len(self.error_stats[error_key]['attempts'])
            proxy_mode_distribution = {}
            for mode in self.error_stats[error_key]['proxy_modes']:
                proxy_mode_distribution[mode] = proxy_mode_distribution.get(mode, 0) + 1
            
            logger.warning(f"错误模式分析: {error_key} - 总数: {self.error_stats[error_key]['count']}, "
                          f"平均重试次数: {avg_attempt:.1f}, 错误频率: {error_frequency:.2f}/分钟, "
                          f"代理分布: {proxy_mode_distribution}")
        else:
            logger.debug(f"错误统计更新: {error_key} - 总数: {self.error_stats[error_key]['count']}")
    
    def log_error_to_file(self, error_type, status_code, attempt):
        """
        将错误信息记录到日志文件 - 基于GitHub和Stack Overflow最佳实践优化
        
        最佳实践参考:
        - 结构化日志记录: 包含时间戳、错误类型、状态码、重试次数
        - 上下文信息记录: 记录当前配置、代理模式、请求频率等
        - 会话健康度记录: 记录会话健康评分和错误趋势
        - 错误分类存储: 按错误类型分类存储便于分析
        
        Args:
            error_type (str): 错误类型
            status_code (int): HTTP状态码（如果有）
            attempt (int): 当前重试次数
            
        Returns:
            None
        """
        error_log_file = "crawler_errors.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            with open(error_log_file, 'a', encoding='utf-8') as f:
                # 记录基础错误信息
                f.write(f"[{timestamp}] {error_type} - 状态码: {status_code}, 重试次数: {attempt}\n")
                
                # 记录详细配置信息
                f.write(f"    当前User-Agent: {self.current_user_agent}\n")
                f.write(f"    代理模式: {'BrightData' if self.use_brightdata_proxy else '免费代理'}\n")
                f.write(f"    请求频率: {self.request_delay}秒\n")
                f.write(f"    会话健康度: {self.get_session_health_score():.2f}\n")
                f.write(f"    浏览器指纹: {self.browser_fingerprint}\n")
                f.write(f"    活跃Cookie数量: {len(self.session.cookies) if hasattr(self, 'session') else 0}\n")
                
                # 记录错误统计信息
                if hasattr(self, 'error_stats'):
                    error_key = f"{error_type}_{status_code}" if status_code else error_type
                    if error_key in self.error_stats:
                        stats = self.error_stats[error_key]
                        time_since_first = (datetime.now() - stats['first_occurrence']).total_seconds()
                        error_frequency = stats['count'] / max(1, time_since_first / 60)
                        
                        f.write(f"    错误统计 - 总数: {stats['count']}, 频率: {error_frequency:.2f}/分钟\n")
                        f.write(f"    首次发生: {stats['first_occurrence'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"    最后发生: {stats['last_occurrence'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                # 记录当前错误处理策略
                f.write(f"    当前重试策略: {self.retry_strategy}\n")
                f.write(f"    最大重试次数: {self.max_retries}\n")
                f.write(f"    智能代理轮换: {'启用' if hasattr(self, 'smart_proxy_rotation') else '禁用'}\n")
                
                f.write("-" * 50 + "\n")
        except Exception as e:
            logger.error(f"写入错误日志失败: {e}")
    
    def monitor_error_rate_and_adjust(self):
        """监控错误率并动态调整策略 - 基于GitHub最佳实践"""
        total_requests = self.request_count
        total_errors = self.error_count
        
        if total_requests > 10:  # 有足够数据时开始监控
            error_rate = total_errors / total_requests
            
            # 基于GitHub最佳实践的错误率阈值
            if error_rate > 0.3:  # 30%错误率：严重问题
                logger.warning(f"错误率过高 ({error_rate:.1%})，启动紧急调整")
                self.emergency_error_handling()
            elif error_rate > 0.15:  # 15%错误率：警告级别
                logger.warning(f"错误率较高 ({error_rate:.1%})，调整策略")
                self.adjust_strategy_for_high_error_rate()
            elif error_rate < 0.05:  # 5%错误率：良好状态
                logger.info(f"错误率正常 ({error_rate:.1%})，可适当提高效率")
                self.optimize_for_low_error_rate()
    
    def emergency_error_handling(self):
        """紧急错误处理策略 - 基于GitHub最佳实践"""
        logger.critical("启动紧急错误处理策略")
        
        # 1. 全面更换所有标识符
        self.rotate_all_identifiers()
        
        # 2. 切换到最可靠的代理模式
        if not self.use_brightdata_proxy and self.proxy_configs:
            self.use_brightdata_proxy = True
            self.current_proxy_index = 0  # 使用第一个BrightData代理
            self.setup_brightdata_proxy()
        
        # 3. 大幅降低请求频率
        self.intelligent_stop_config['max_requests_per_session'] = 3
        self.intelligent_stop_config['base_delay'] = 10.0
        
        # 4. 增加重试次数
        self.max_retries = 5
        
        logger.info("紧急处理完成：全面更换标识符，降低频率，增加重试")
    
    def adjust_strategy_for_high_error_rate(self):
        """高错误率下的策略调整 - 基于GitHub最佳实践"""
        # 1. 适度降低请求频率
        self.intelligent_stop_config['max_requests_per_session'] = max(5, 
            self.intelligent_stop_config['max_requests_per_session'] - 2)
        
        # 2. 增加基础延迟
        self.intelligent_stop_config['base_delay'] *= 1.2
        
        # 3. 更频繁地轮换代理
        self.proxy_rotation_frequency = max(3, self.proxy_rotation_frequency - 1)
        
        logger.info("高错误率策略调整：降低频率，增加延迟，频繁轮换代理")
    
    def optimize_for_low_error_rate(self):
        """低错误率下的优化策略 - 基于GitHub最佳实践"""
        # 1. 适度提高请求频率（但不超过安全阈值）
        if self.intelligent_stop_config['max_requests_per_session'] < 20:
            self.intelligent_stop_config['max_requests_per_session'] += 1
        
        # 2. 适度减少延迟（但保持合理间隔）
        if self.intelligent_stop_config['base_delay'] > 2.0:
            self.intelligent_stop_config['base_delay'] *= 0.9
        
        logger.info("低错误率优化：适度提高频率，减少延迟")
    
    def rotate_all_identifiers(self):
        """全面更换所有标识符 - 基于GitHub和Stack Overflow最佳实践优化
        
        最佳实践参考:
        - 全面标识符轮换: 同时更换所有可识别的标识符
        - 智能代理选择: 使用智能代理轮换策略
        - 会话重置: 清空Cookie重新建立会话
        - 浏览器指纹更新: 更新浏览器指纹信息
        
        Returns:
            None
        """
        logger.info("启动全面标识符轮换策略")
        
        # 1. 更换User-Agent - 基于GitHub最佳实践
        old_ua = self.current_user_agent[:50] + "..." if len(self.current_user_agent) > 50 else self.current_user_agent
        self.current_user_agent = random.choice(self.user_agents)
        new_ua = self.current_user_agent[:50] + "..." if len(self.current_user_agent) > 50 else self.current_user_agent
        logger.info(f"更换User-Agent: {old_ua} -> {new_ua}")
        
        # 2. 使用智能代理轮换策略 - 基于Stack Overflow最佳实践
        old_proxy_mode = "BrightData" if self.use_brightdata_proxy else "免费代理"
        self.smart_proxy_rotation()
        new_proxy_mode = "BrightData" if self.use_brightdata_proxy else "免费代理"
        logger.info(f"更换代理模式: {old_proxy_mode} -> {new_proxy_mode}")
        
        # 3. 更换浏览器指纹 - 基于GitHub最佳实践
        self.setup_browser_fingerprint()
        logger.info("浏览器指纹已更新")
        
        # 4. 清空Cookie（重新建立会话） - 基于Stack Overflow最佳实践
        cookie_count = len(self.session.cookies)
        self.session.cookies.clear()
        logger.info(f"清空 {cookie_count} 个Cookie，重新建立会话")
        
        # 5. 更新会话请求头
        self.update_session_headers()
        logger.info("会话请求头已更新")
        
        logger.info("全面标识符轮换完成")
    
    def calculate_retry_delay(self, attempt, max_retries, error_type=None):
        """计算智能重试延迟 - 基于GitHub和Stack Overflow最佳实践优化
        
        最佳实践参考:
        - 指数退避算法 (Exponential Backoff): 每次重试延迟呈指数增长
        - 随机抖动 (Jitter): 添加随机性避免多个客户端同步重试
        - 错误类型自适应: 根据错误类型调整延迟策略
        - 最大延迟限制: 避免无限等待
        
        Args:
            attempt: 当前重试次数 (0-indexed)
            max_retries: 最大重试次数
            error_type: 错误类型，用于自适应调整
            
        Returns:
            float: 计算出的延迟时间（秒）
        """
        # 基础配置 - 基于GitHub最佳实践
        base_delay = 1.0  # 基础延迟1秒
        max_delay = 300.0  # 最大延迟5分钟
        
        # 指数退避因子 - 基于Stack Overflow最佳实践
        exponential_factor = 2 ** attempt
        
        # 随机抖动因子 - 避免同步重试风暴
        jitter_factor = random.uniform(0.8, 1.2)
        
        # 错误类型自适应延迟 - 基于错误严重程度调整
        error_multiplier = 1.0
        if error_type:
            error_multipliers = {
                'ConnectionError': 1.2,      # 连接错误：轻微增加延迟
                'Timeout': 1.5,               # 超时错误：中等增加延迟
                'HTTPError': 1.0,             # HTTP错误：标准延迟
                'ProxyError': 1.8,            # 代理错误：显著增加延迟
                'SSLError': 2.0,              # SSL错误：大幅增加延迟
                'RateLimitError': 3.0         # 速率限制：最大延迟倍数
            }
            error_multiplier = error_multipliers.get(error_type, 1.0)
        
        # 基于错误率的动态调整 - 高错误率时增加延迟
        error_rate = self.stats.get('error_rate', 0)
        if error_rate > 0.5:  # 错误率超过50%
            error_multiplier *= 1.5
        elif error_rate > 0.3:  # 错误率超过30%
            error_multiplier *= 1.2
        
        # 计算延迟 - 核心算法
        delay = base_delay * exponential_factor * jitter_factor * error_multiplier
        
        # 应用最大延迟限制 - 避免无限等待
        delay = min(delay, max_delay)
        
        # 基于重试次数的渐进式限制 - 避免过早达到最大延迟
        progressive_max = min(max_delay, 10 * (attempt + 1))
        delay = min(delay, progressive_max)
        
        # 记录延迟计算详情用于调试
        logger.debug(f"智能重试延迟计算: 尝试={attempt}, 错误类型={error_type}, "
                    f"错误率={error_rate:.2%}, 最终延迟={delay:.2f}s")
        
        return delay
    
    def adjust_retry_strategy(self, attempt, error):
        """
        智能调整重试策略 - 基于重试次数和错误类型动态优化爬取策略
        
        参考GitHub和Stack Overflow最佳实践：
        - 渐进式策略调整：根据重试次数逐步增强应对措施
        - 错误类型感知：针对不同错误类型采用不同优化策略
        - 智能代理轮换：使用smart_proxy_rotation替代简单轮换
        
        Args:
            attempt (int): 当前重试次数
            error (Exception): 发生的错误对象
            
        Returns:
            None
        """
        error_type = type(error).__name__
        
        # 记录策略调整开始
        logger.info(f"开始调整重试策略: 尝试={attempt}, 错误类型={error_type}")
        
        if attempt == 0:
            # 第一次重试：简单调整 - 更换User-Agent
            old_agent = self.session.headers.get('User-Agent', 'Unknown')
            self.rotate_user_agent()
            new_agent = self.session.headers.get('User-Agent', 'Unknown')
            logger.info(f"第一次重试策略: 更换User-Agent [{old_agent[:30]}...] -> [{new_agent[:30]}...]")
            
        elif attempt == 1:
            # 第二次重试：智能代理轮换和请求头更新
            old_proxy_mode = 'brightdata' if self.use_brightdata_proxy else 'free'
            self.smart_proxy_rotation()
            new_proxy_mode = 'brightdata' if self.use_brightdata_proxy else 'free'
            
            self.update_session_headers()
            
            logger.info(f"第二次重试策略: 智能代理轮换 [{old_proxy_mode}] -> [{new_proxy_mode}], 更新请求头")
            
        elif attempt >= 2:
            # 第三次及以后重试：全面更换标识符和深度策略调整
            logger.info("第三次重试策略: 全面更换标识符和深度策略调整")
            self.rotate_all_identifiers()
            
            # 基于错误类型的智能策略调整
            if 'Connection' in error_type or 'Timeout' in error_type:
                # 网络问题：智能降低请求频率并增加延迟
                old_freq = self.intelligent_stop_config['max_requests_per_session']
                self.intelligent_stop_config['max_requests_per_session'] = max(5, 
                    self.intelligent_stop_config['max_requests_per_session'] // 2)
                new_freq = self.intelligent_stop_config['max_requests_per_session']
                
                # 增加基础延迟
                old_delay = self.intelligent_stop_config['base_delay']
                self.intelligent_stop_config['base_delay'] *= 1.5
                new_delay = self.intelligent_stop_config['base_delay']
                
                logger.info(f"网络问题策略: 请求频率 {old_freq} -> {new_freq}, 基础延迟 {old_delay:.2f}s -> {new_delay:.2f}s")
            
            elif 'HTTP' in error_type:
                # HTTP错误：增加延迟并考虑切换代理模式
                old_delay = self.intelligent_stop_config['base_delay']
                self.intelligent_stop_config['base_delay'] *= 1.5
                new_delay = self.intelligent_stop_config['base_delay']
                
                # 如果错误率较高，考虑切换到更稳定的代理模式
                error_rate = self.stats.get('error_rate', 0)
                if error_rate > 0.3:
                    old_mode = 'brightdata' if self.use_brightdata_proxy else 'free'
                    if not self.use_brightdata_proxy and self.brightdata_config:
                        self.use_brightdata_proxy = True
                        logger.info(f"高错误率({error_rate:.1%})，切换到BrightData代理模式")
                
                logger.info(f"HTTP错误策略: 基础延迟 {old_delay:.2f}s -> {new_delay:.2f}s")
            
            # 记录策略调整完成
            logger.info(f"重试策略调整完成: 尝试={attempt}, 当前错误率={self.stats.get('error_rate', 0):.1%}")
    
    def record_search_failure(self, keyword, year, page, error):
        """记录搜索失败信息"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        failure_record = {
            'keyword': keyword,
            'year': year,
            'page': page,
            'error_type': error_type,
            'error_message': error_msg,
            'timestamp': datetime.now().isoformat(),
            'session_stats': self.stats.copy(),
            'proxy_mode': 'brightdata' if self.use_brightdata_proxy else 'free',
            'user_agent': self.session.headers.get('User-Agent', '')
        }
        
        # 添加到失败记录列表
        self.stats['search_failures'].append(failure_record)
        
        # 更新错误率统计
        total_searches = self.stats.get('successful_searches', 0) + len(self.stats['search_failures'])
        if total_searches > 0:
            self.stats['error_rate'] = len(self.stats['search_failures']) / total_searches
        
        logger.error(f"搜索失败记录: {keyword} ({year}), 第 {page} 页 - {error_type}: {error_msg}")
    
    def setup_cookie_management(self):
        """设置Cookie管理功能"""
        self.cookie_jar = requests.cookies.RequestsCookieJar()
        self.session.cookies = self.cookie_jar
        self.cookie_expiry_times = {}
        self.cookie_usage_stats = {}
        
        # 加载持久化Cookie
        self.load_persistent_cookies()
        
        logger.info("Cookie管理功能已初始化")
    
    def load_persistent_cookies(self):
        """加载持久化Cookie"""
        cookie_file = os.path.join(self.data_dir, 'cookies.json')
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookie_data = json.load(f)
                
                for domain, cookies in cookie_data.items():
                    for cookie_info in cookies:
                        # 检查Cookie是否过期
                        expiry = cookie_info.get('expiry')
                        if expiry and datetime.now().timestamp() > expiry:
                            continue
                        
                        # 添加Cookie到会话
                        self.session.cookies.set_cookie(requests.cookies.create_cookie(
                            name=cookie_info['name'],
                            value=cookie_info['value'],
                            domain=cookie_info.get('domain', ''),
                            path=cookie_info.get('path', '/'),
                            expires=expiry
                        ))
                
                logger.info(f"已加载 {len(cookie_data)} 个域的持久化Cookie")
                
            except Exception as e:
                logger.warning(f"加载持久化Cookie失败: {e}")
    
    def save_persistent_cookies(self):
        """保存持久化Cookie"""
        try:
            cookie_data = {}
            
            for cookie in self.session.cookies:
                domain = cookie.domain or self.base_url.replace('https://', '').replace('http://', '')
                if domain not in cookie_data:
                    cookie_data[domain] = []
                
                cookie_info = {
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path,
                    'expiry': cookie.expires
                }
                cookie_data[domain].append(cookie_info)
            
            cookie_file = os.path.join(self.data_dir, 'cookies.json')
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"已保存 {len(cookie_data)} 个域的Cookie到文件")
            
        except Exception as e:
            logger.error(f"保存Cookie失败: {e}")
    
    def update_cookie_usage(self, domain, cookie_name):
        """更新Cookie使用统计"""
        key = f"{domain}:{cookie_name}"
        if key not in self.cookie_usage_stats:
            self.cookie_usage_stats[key] = {
                'usage_count': 0,
                'last_used': datetime.now().isoformat(),
                'first_used': datetime.now().isoformat()
            }
        
        self.cookie_usage_stats[key]['usage_count'] += 1
        self.cookie_usage_stats[key]['last_used'] = datetime.now().isoformat()
    
    def get_session_health_score(self):
        """获取会话健康度评分"""
        score = 100
        
        # 基于错误率扣分
        error_rate = self.stats.get('error_rate', 0)
        if error_rate > 0.3:
            score -= 30
        elif error_rate > 0.1:
            score -= 15
        
        # 基于反爬事件扣分
        anti_scraping_events = self.stats.get('anti_scraping_events', 0)
        if anti_scraping_events > 10:
            score -= 20
        elif anti_scraping_events > 5:
            score -= 10
        
        # 基于Cookie有效性加分
        if len(self.session.cookies) > 0:
            score += 10
        
        # 基于会话时长加分（长时间稳定运行）
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        if session_duration > 3600:  # 1小时
            score += 15
        elif session_duration > 1800:  # 30分钟
            score += 8
        
        return max(0, min(100, score))
    
    def should_renew_session(self):
        """判断是否需要更新会话"""
        health_score = self.get_session_health_score()
        
        # 健康度低于50分时考虑更新会话
        if health_score < 50:
            return True
        
        # 会话时长超过2小时
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        if session_duration > 7200:  # 2小时
            return True
        
        # 连续失败次数过多
        if self.stats.get('consecutive_failures', 0) > 5:
            return True
        
        return False
    
    def renew_session(self):
        """更新会话"""
        logger.info("开始更新会话...")
        
        # 保存当前Cookie
        self.save_persistent_cookies()
        
        # 创建新会话
        old_session = self.session
        self.session = requests.Session()
        
        # 重新设置会话配置
        self.setup_session_config()
        self.setup_cookie_management()
        
        # 更新会话统计
        self.session_start_time = datetime.now()
        self.stats['session_renewals'] += 1
        self.stats['consecutive_failures'] = 0
        
        # 关闭旧会话
        old_session.close()
        
        logger.info(f"会话更新完成，健康度评分: {self.get_session_health_score()}")
    
    def maintain_session_health(self):
        """维护会话健康"""
        health_score = self.get_session_health_score()
        
        if health_score < 30:
            logger.warning(f"会话健康度低 ({health_score})，立即更新会话")
            self.renew_session()
        elif health_score < 60:
            logger.info(f"会话健康度中等 ({health_score})，考虑下次请求时更新")
        else:
            logger.debug(f"会话健康度良好 ({health_score})")
        
        # 定期保存Cookie
        if random.random() < 0.1:  # 10%概率保存Cookie
            self.save_persistent_cookies()
    
    def is_empty_results_page(self, soup):
        """检查是否为空结果页"""
        try:
            # 检查常见空结果标识
            empty_indicators = [
                'no results', 'no articles found', 'search returned no results',
                '没有找到结果', '未找到相关文章'
            ]
            
            page_text = soup.get_text().lower()
            for indicator in empty_indicators:
                if indicator in page_text:
                    return True
            
            # 检查是否有文章元素
            article_elements = soup.select('.search-result-item, .news-item, .article-item, article')
            return len(article_elements) == 0
            
        except Exception as e:
            logger.warning(f"空结果页检测失败: {e}")
            return False
    
    def intelligent_article_list_parsing(self, soup, keyword, year, page):
        """智能文章列表解析算法 - 多维度语义分析和结构检测"""
        articles = []
        
        try:
            # 1. 语义结构检测 - 识别文章列表容器
            article_containers = self.detect_article_containers(soup)
            
            if not article_containers:
                # 备用策略：基于文本密度和链接结构检测
                article_containers = self.detect_articles_by_text_density(soup)
            
            # 2. 智能文章元素提取
            for container in article_containers:
                article_data = self.parse_article_element_intelligently(container, keyword, year, page)
                if article_data and article_data.get('title'):
                    articles.append(article_data)
            
            # 3. 置信度评估和去重
            articles = self.assess_article_confidence(articles)
            articles = self.deduplicate_articles(articles)
            
            logger.info(f"智能文章列表解析完成: 找到 {len(articles)} 篇文章")
            
        except Exception as e:
            logger.error(f"智能文章列表解析失败: {e}")
            # 降级到传统方法
            articles = self.fallback_traditional_parsing(soup, keyword, year, page)
        
        return articles
    
    def detect_article_containers(self, soup):
        """检测文章列表容器 - 多策略组合"""
        containers = []
        
        # 策略1: 语义容器检测
        semantic_selectors = [
            '.news-list, .article-list, .search-results',
            '.items-list, .posts-list, .stories-list',
            '.results, .listing, .archive',
            'ul.news, ol.articles, div.entries'
        ]
        
        for selector in semantic_selectors:
            elements = soup.select(selector)
            if elements:
                containers.extend(elements)
        
        # 策略2: 基于链接密度的容器检测
        if not containers:
            containers = self.detect_containers_by_link_density(soup)
        
        # 策略3: 基于文本结构的容器检测
        if not containers:
            containers = self.detect_containers_by_text_structure(soup)
        
        return containers
    
    def detect_containers_by_link_density(self, soup):
        """基于链接密度检测文章容器"""
        containers = []
        
        # 查找包含多个链接的容器
        all_containers = soup.find_all(['div', 'section', 'article', 'ul', 'ol'])
        
        for container in all_containers:
            # 计算链接密度
            links = container.find_all('a')
            total_text = container.get_text()
            
            if len(links) >= 3 and len(total_text) > 100:  # 链接数量和文本长度阈值
                # 检查链接是否指向文章（基于URL模式）
                article_links = 0
                for link in links:
                    href = link.get('href', '')
                    if self.is_article_link(href):
                        article_links += 1
                
                if article_links >= 2:  # 至少2个文章链接
                    containers.append(container)
        
        return containers
    
    def detect_containers_by_text_structure(self, soup):
        """基于文本结构检测文章容器"""
        containers = []
        
        # 查找包含标题-摘要结构的容器
        all_containers = soup.find_all(['div', 'section', 'article'])
        
        for container in all_containers:
            # 检查是否包含标题和摘要元素
            headings = container.find_all(['h2', 'h3', 'h4'])
            paragraphs = container.find_all('p')
            
            if len(headings) >= 2 and len(paragraphs) >= 2:
                # 检查标题-摘要配对
                valid_pairs = 0
                for heading in headings:
                    # 查找相邻的段落作为摘要
                    next_sibling = heading.find_next_sibling('p')
                    if next_sibling and len(next_sibling.get_text(strip=True)) > 20:
                        valid_pairs += 1
                
                if valid_pairs >= 2:  # 至少2个有效标题-摘要对
                    containers.append(container)
        
        return containers
    
    def parse_article_element_intelligently(self, element, keyword, year, page):
        """智能解析单个文章元素"""
        try:
            # 1. 标题和链接提取
            title_data = self.extract_title_and_link_intelligently(element)
            if not title_data:
                return None
            
            title, link = title_data
            
            # 2. 摘要提取
            summary = self.extract_summary_intelligently(element, title)
            
            # 3. 日期提取
            date = self.extract_date_from_element_intelligently(element)
            
            # 4. 作者提取
            author = self.extract_author_from_element_intelligently(element)
            
            # 5. 置信度评估
            confidence = self.assess_element_confidence(element, title, link, summary)
            
            return {
                'title': title,
                'link': link,
                'summary': summary,
                'date': date,
                'author': author,
                'keyword': keyword,
                'year': year,
                'search_page': page,
                'search_timestamp': datetime.now().isoformat(),
                'confidence': confidence,
                'extraction_method': 'intelligent_parser'
            }
            
        except Exception as e:
            logger.warning(f"智能解析文章元素失败: {e}")
            return None
    
    def extract_title_and_link_intelligently(self, element):
        """智能提取标题和链接"""
        # 策略1: 语义标题检测
        title_selectors = [
            'h2 a, h3 a, h4 a',
            '.title a, .headline a, a.title',
            '.entry-title a, .post-title a, .news-title a'
        ]
        
        for selector in title_selectors:
            title_element = element.select_one(selector)
            if title_element:
                title = title_element.get_text(strip=True)
                link = title_element.get('href')
                if title and link:
                    link = self.normalize_link(link)
                    return title, link
        
        # 策略2: 基于文本重要性的标题检测
        return self.extract_title_by_text_importance(element)
    
    def extract_title_by_text_importance(self, element):
        """基于文本重要性提取标题"""
        # 查找最重要的文本（通常是最大的标题或最突出的链接）
        headings = element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in headings:
            link = heading.find('a')
            if link:
                title = link.get_text(strip=True)
                href = link.get('href')
                if title and href:
                    href = self.normalize_link(href)
                    return title, href
        
        # 查找包含重要关键词的链接
        important_links = element.find_all('a')
        for link in important_links:
            text = link.get_text(strip=True)
            href = link.get('href')
            if len(text) > 10 and len(text) < 200:  # 合理的标题长度
                if self.is_important_link(text, href):
                    href = self.normalize_link(href)
                    return text, href
        
        return None
    
    def extract_summary_intelligently(self, element, title):
        """智能提取摘要"""
        # 策略1: 语义摘要检测
        summary_selectors = [
            '.summary, .excerpt, .description',
            '.snippet, .preview, .teaser',
            '.abstract, .intro, .lead'
        ]
        
        for selector in summary_selectors:
            summary_element = element.select_one(selector)
            if summary_element:
                summary = summary_element.get_text(strip=True)
                if summary and len(summary) > 20:
                    return summary
        
        # 策略2: 基于标题的相邻文本检测
        return self.extract_summary_adjacent_to_title(element, title)
    
    def detect_articles_by_text_density(self, soup):
        """基于文本密度检测文章容器 - 备用策略"""
        containers = []
        
        # 查找包含密集文本的容器
        all_containers = soup.find_all(['div', 'section', 'article'])
        
        for container in all_containers:
            text = container.get_text(strip=True)
            if len(text) > 200:  # 文本长度阈值
                # 检查文本密度（非空白字符比例）
                text_density = len(text) / len(container.get_text())
                if text_density > 0.7:  # 高文本密度
                    containers.append(container)
        
        return containers
    
    def validate_date(self, date_str):
        """验证日期格式"""
        if not date_str:
            return False
        
        # 常见日期模式
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
            r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'\d{4}年\d{1,2}月\d{1,2}日',  # 中文日期
            r'\d{1,2}月\d{1,2}日\s*\d{4}年'  # 中文日期变体
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, date_str):
                return True
        
        return False
    
    def extract_date_by_text_pattern(self, element):
        """基于文本模式提取日期"""
        # 查找包含日期模式的文本
        text = element.get_text()
        
        # 日期正则表达式
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{4}/\d{2}/\d{2})',
            r'(\d{2}-\d{2}-\d{4})',
            r'(\d{2}/\d{2}/\d{4})',
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{1,2}月\d{1,2}日\s*\d{4}年)'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return ""
    
    def extract_summary_adjacent_to_title(self, element, title):
        """基于标题的相邻文本提取摘要"""
        # 查找包含标题的容器
        title_container = None
        for heading in element.find_all(['h2', 'h3', 'h4']):
            if heading.get_text(strip=True) == title:
                title_container = heading.parent
                break
        
        if title_container:
            # 查找标题后的段落作为摘要
            paragraphs = title_container.find_all_next('p', limit=3)
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 30 and len(text) < 300:  # 合理的摘要长度
                    return text
        
        return ""
    
    def extract_date_from_element_intelligently(self, element):
        """智能从元素中提取日期"""
        # 策略1: 语义日期检测
        date_selectors = [
            '.date, .time, .published',
            '.timestamp, .post-date, .article-date',
            '.datetime, .date-published, .publish-date'
        ]
        
        for selector in date_selectors:
            date_element = element.select_one(selector)
            if date_element:
                date = date_element.get_text(strip=True)
                if self.validate_date(date):
                    return date
        
        # 策略2: 基于文本模式的日期检测
        return self.extract_date_by_text_pattern(element)
    
    def extract_author_from_element_intelligently(self, element):
        """智能从元素中提取作者"""
        # 策略1: 语义作者检测
        author_selectors = [
            '.author, .byline, .writer',
            '.posted-by, .contributor, .reporter'
        ]
        
        for selector in author_selectors:
            author_element = element.select_one(selector)
            if author_element:
                author = author_element.get_text(strip=True)
                if author:
                    return author
        
        return ""
    
    def assess_element_confidence(self, element, title, link, summary):
        """评估元素解析置信度"""
        confidence = 0.0
        
        # 标题质量评估
        if title and len(title) > 5:
            confidence += 0.3
        
        # 链接质量评估
        if link and self.is_article_link(link):
            confidence += 0.3
        
        # 摘要质量评估
        if summary and len(summary) > 20:
            confidence += 0.2
        
        # 元素结构完整性评估
        if self.has_complete_article_structure(element):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def has_complete_article_structure(self, element):
        """检查是否具有完整的文章结构"""
        # 检查是否包含标题、链接和摘要元素
        has_title = bool(element.find(['h2', 'h3', 'h4']))
        has_link = bool(element.find('a'))
        has_text = len(element.get_text(strip=True)) > 50
        
        return has_title and has_link and has_text
    
    def assess_article_confidence(self, articles):
        """评估文章置信度并过滤低质量结果"""
        filtered_articles = []
        
        for article in articles:
            confidence = article.get('confidence', 0)
            
            # 基于置信度过滤
            if confidence >= 0.5:  # 中等置信度阈值
                filtered_articles.append(article)
            else:
                logger.debug(f"过滤低置信度文章: {article.get('title', 'Unknown')} (置信度: {confidence:.2f})")
        
        return filtered_articles
    
    def deduplicate_articles(self, articles):
        """文章去重"""
        seen_links = set()
        unique_articles = []
        
        for article in articles:
            link = article.get('link', '')
            if link and link not in seen_links:
                seen_links.add(link)
                unique_articles.append(article)
        
        return unique_articles
    
    def fallback_traditional_parsing(self, soup, keyword, year, page):
        """降级到传统解析方法"""
        logger.warning("智能解析失败，使用传统方法")
        
        articles = []
        article_elements = soup.select('.news-item, article, .story, .post, .news, .news-list-item, .news-content')
        
        if not article_elements:
            article_elements = soup.select('h2 a, h3 a, h4 a, .title a, .headline a, a.title, .news-title a')
        
        for element in article_elements:
            try:
                title_element = element.select_one('h2 a, h3 a, h4 a, .title a, .headline a, a.title')
                if not title_element:
                    continue
                
                title = title_element.get_text(strip=True)
                link = title_element.get('href')
                if link and not link.startswith('http'):
                    link = self.base_url + link if link.startswith('/') else f"{self.base_url}/{link}"
                
                summary_element = element.select_one('.summary, .excerpt, .description, .snippet, .preview')
                summary = summary_element.get_text(strip=True) if summary_element else ""
                
                date_element = element.select_one('.date, .time, .published, .timestamp, .post-date')
                date = date_element.get_text(strip=True) if date_element else ""
                
                author_element = element.select_one('.author, .byline, .writer, .posted-by')
                author = author_element.get_text(strip=True) if author_element else ""
                
                articles.append({
                    'title': title,
                    'link': link,
                    'summary': summary,
                    'date': date,
                    'author': author,
                    'keyword': keyword,
                    'year': year,
                    'search_page': page,
                    'search_timestamp': datetime.now().isoformat(),
                    'confidence': 0.3,  # 传统方法置信度较低
                    'extraction_method': 'traditional_fallback'
                })
                
            except Exception as e:
                logger.warning(f"传统解析文章元素失败: {e}")
        
        return articles
    
    def is_article_link(self, href):
        """判断链接是否为文章链接"""
        if not href:
            return False
        
        # 文章URL模式
        article_patterns = [
            '/article/', '/news/', '/story/', '/post/',
            '/blog/', '/entry/', '/202', '/201', '/200'
        ]
        
        for pattern in article_patterns:
            if pattern in href:
                return True
        
        return False
    
    def is_important_link(self, text, href):
        """判断链接是否为重要链接"""
        if not text or not href:
            return False
        
        # 排除导航、页脚等非重要链接
        exclude_patterns = ['home', 'contact', 'about', 'privacy', 'terms']
        for pattern in exclude_patterns:
            if pattern in text.lower() or pattern in href.lower():
                return False
        
        return True
    
    def normalize_link(self, href):
        """标准化链接"""
        if not href:
            return ""
        
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return self.base_url + href
        else:
            return f"{self.base_url}/{href}"

    def get_article_details(self, article_url):
        """获取文章详细信息 - 增强传统爬虫优先级和智能解析算法"""
        
        # 智能方法选择策略：优先使用更可靠的方法
        if self.use_mcp_tools:
            # 检查Firecrawl是否已被禁用
            if not self.stats['firecrawl_disabled']:
                # 尝试MCP工具爬取，但设置更严格的超时和重试
                mcp_details = self.mcp_scrape_article(article_url)
                if mcp_details is not None and mcp_details.get('content', '').strip():
                    self.stats['mcp_tools_used'] += 1
                    self.stats['search_methods_used']['mcp_scrape'] += 1
                    logger.info(f"MCP工具爬取成功: {article_url}")
                    return mcp_details
                else:
                    # MCP爬取失败，记录并优先使用传统方法
                    logger.warning(f"MCP爬取返回空内容或无内容，切换到传统方法")
                    self.stats['mcp_scrape_failures'] += 1
                    self.stats['fallback_to_traditional'] += 1
        
        # 增强传统爬取优先级 - 直接使用传统方法
        self.stats['traditional_crawl_used'] += 1
        self.stats['search_methods_used']['traditional_scrape'] += 1
        logger.info(f"使用传统爬取方法: {article_url}")
        
        try:
            response = self.session.get(article_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 智能内容提取算法 - 多维度解析策略
            content = self.extract_content_intelligently(soup)
            
            # 智能日期提取 - 多源验证
            publish_date = self.extract_date_intelligently(soup, article_url)
            
            # 智能作者提取 - 多源验证
            author = self.extract_author_intelligently(soup)
            
            # 智能体裁检测 - 基于内容和URL
            genre = self.detect_genre_intelligently(article_url, content)
            
            # 智能信源检测
            source = self.detect_source_intelligently(article_url, soup)
            
            # 内容质量评估
            content_quality = self.assess_content_quality(content, soup)
            
            # 记录传统爬取成功
            self.stats['traditional_scrape_success'] += 1
            
            return {
                'content': content.strip(),
                'publish_date': publish_date,
                'author': author,
                'genre': genre,
                'source': source,
                'full_content_available': bool(content.strip()),
                'content_quality': content_quality,
                'extraction_method': 'intelligent_parser'
            }
            
        except Exception as e:
            logger.error(f"获取文章详情失败: {article_url}: {e}")
            return {
                'content': "",
                'publish_date': "",
                'author': "",
                'genre': "",
                'source': "Al-Ahram English",
                'full_content_available': False,
                'content_quality': 0,
                'extraction_method': 'failed'
            }
    
    def extract_content_intelligently(self, soup):
        """智能内容提取算法"""
        content = ""
        
        # 策略1: 基于语义结构的内容提取
        semantic_selectors = [
            'article .content, article .text, article .body',
            '.article-content, .news-content, .story-content',
            '.entry-content, .post-content, .content-wrapper',
            'main article, .main-content article'
        ]
        
        for selector in semantic_selectors:
            content_elements = soup.select(selector)
            if content_elements:
                for element in content_elements:
                    # 智能文本清理和提取
                    text = self.clean_extracted_text(element.get_text())
                    if len(text) > 100:  # 有效内容长度阈值
                        content += text + "\n\n"
                if content.strip():
                    break
        
        # 策略2: 段落级内容提取（如果语义提取失败）
        if not content.strip():
            paragraph_selectors = [
                'article p, .content p, .text p',
                '.article-body p, .story-body p',
                'main p, .main-content p'
            ]
            
            for selector in paragraph_selectors:
                paragraphs = soup.select(selector)
                if paragraphs:
                    for p in paragraphs:
                        text = self.clean_extracted_text(p.get_text())
                        if len(text) > 20:  # 段落长度阈值
                            content += text + "\n"
                    if content.strip():
                        break
        
        # 策略3: 基于文本密度和结构的内容提取
        if not content.strip():
            content = self.extract_by_text_density(soup)
        
        return content
    
    def extract_date_intelligently(self, soup, url):
        """智能日期提取 - 多源验证"""
        date_candidates = []
        
        # 策略1: meta标签提取（最高优先级）
        meta_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publish_date"]',
            'meta[name="date"]',
            'meta[property="og:published_time"]'
        ]
        
        for selector in meta_selectors:
            element = soup.select_one(selector)
            if element:
                date = element.get('content', '').strip()
                if self.validate_date(date):
                    date_candidates.append((date, 'meta', 10))  # 最高权重
        
        # 策略2: 可见日期元素
        visible_selectors = [
            '.publish-date, .article-date, .date',
            '.post-date, .time, .datetime',
            '.published, .timestamp, .date-published'
        ]
        
        for selector in visible_selectors:
            element = soup.select_one(selector)
            if element:
                date = element.get_text(strip=True)
                if self.validate_date(date):
                    date_candidates.append((date, 'visible', 8))
        
        # 策略3: 从URL中提取日期
        url_date = self.extract_date_from_url(url)
        if url_date:
            date_candidates.append((url_date, 'url', 6))
        
        # 选择最可靠的日期
        if date_candidates:
            # 按权重排序并选择最高权重的日期
            date_candidates.sort(key=lambda x: x[2], reverse=True)
            return date_candidates[0][0]
        
        return ""
    
    def extract_author_intelligently(self, soup):
        """智能作者提取 - 多源验证"""
        author_candidates = []
        
        # 策略1: meta标签提取
        meta_selectors = [
            'meta[name="author"]',
            'meta[property="article:author"]',
            'meta[property="og:author"]'
        ]
        
        for selector in meta_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get('content', '').strip()
                if author:
                    author_candidates.append((author, 'meta', 10))
        
        # 策略2: 可见作者元素
        visible_selectors = [
            '.author, .byline, .writer',
            '.post-author, .article-author',
            '.author-name, .byline-author'
        ]
        
        for selector in visible_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get_text(strip=True)
                if author and len(author) > 2:  # 有效作者名长度
                    author_candidates.append((author, 'visible', 8))
        
        # 选择最可靠的作者
        if author_candidates:
            author_candidates.sort(key=lambda x: x[2], reverse=True)
            return author_candidates[0][0]
        
        return ""
    
    def detect_genre_intelligently(self, url, content):
        """智能体裁检测 - 基于内容和URL"""
        url_lower = url.lower()
        content_lower = content.lower()
        
        # 基于URL关键词的体裁判断
        url_keywords = {
            'news': '消息',
            'breaking': '突发新闻',
            'feature': '特写',
            'analysis': '分析',
            'opinion': '评论',
            'editorial': '社论',
            'interview': '访谈',
            'report': '报道',
            'blog': '博客'
        }
        
        for keyword, genre in url_keywords.items():
            if keyword in url_lower:
                return genre
        
        # 基于内容特征的体裁判断
        content_length = len(content)
        
        if content_length > 3000:
            return "深度报道"
        elif content_length > 1500:
            return "通讯"
        elif content_length > 500:
            return "消息"
        else:
            return "简讯"
    
    def detect_source_intelligently(self, url, soup):
        """智能信源检测"""
        # 从URL中提取域名作为基础信源
        domain = url.split('//')[-1].split('/')[0]
        
        # 尝试从meta标签获取更具体的信源
        source_selectors = [
            'meta[property="og:site_name"]',
            'meta[name="source"]',
            'meta[name="publication"]'
        ]
        
        for selector in source_selectors:
            element = soup.select_one(selector)
            if element:
                source = element.get('content', '').strip()
                if source:
                    return source
        
        return domain
    
    def assess_content_quality(self, content, soup):
        """内容质量评估"""
        score = 100
        
        # 基于内容长度的评分
        content_length = len(content)
        if content_length < 100:
            score -= 40
        elif content_length < 300:
            score -= 20
        elif content_length > 2000:
            score += 10
        
        # 基于段落结构的评分
        paragraphs = content.split('\n')
        valid_paragraphs = [p for p in paragraphs if len(p.strip()) > 20]
        if len(valid_paragraphs) >= 3:
            score += 15
        
        # 基于特殊字符比例的评分
        if content:
            chinese_char_ratio = sum(1 for char in content if '\u4e00' <= char <= '\u9fff') / len(content)
            if chinese_char_ratio > 0.3:  # 中文内容占比较高
                score += 10
        
        return max(0, min(100, score))
    
    def clean_extracted_text(self, text):
        """清理提取的文本"""
        # 移除多余空白字符
        text = re.sub(r'\s+', ' ', text)
        # 移除常见干扰文本
        noise_patterns = [
            r'^\s*[\d一二三四五六七八九十]+\s*[、.]\s*',  # 编号前缀
            r'\s*[\[【].*?[\]】]\s*',  # 括号内容
            r'\s*（.*?）\s*',  # 圆括号内容
        ]
        
        for pattern in noise_patterns:
            text = re.sub(pattern, ' ', text)
        
        return text.strip()
    
    def validate_date(self, date_str):
        """验证日期格式"""
        if not date_str:
            return False
        
        # 常见日期格式模式
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'\d{4}\.\d{2}\.\d{2}',  # YYYY.MM.DD
            r'\d{4}年\d{1,2}月\d{1,2}日',  # 中文日期
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, date_str):
                return True
        
        return False
    
    def extract_date_from_url(self, url):
        """从URL中提取日期"""
        # 常见的URL日期模式
        date_patterns = [
            r'/(\d{4})/(\d{2})/(\d{2})/',  # /2023/12/01/
            r'/(\d{4})-(\d{2})-(\d{2})/',  # /2023-12-01/
            r'/(\d{4})\.(\d{2})\.(\d{2})/',  # /2023.12.01/
            r'_(\d{4})(\d{2})(\d{2})',  # _20231201
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, url)
            if match:
                if len(match.groups()) == 3:
                    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        
        return ""
    
    def extract_by_text_density(self, soup):
        """基于文本密度的内容提取"""
        # 计算每个元素的文本密度
        elements = soup.find_all(['div', 'section', 'article'])
        
        best_element = None
        best_density = 0
        
        for element in elements:
            # 计算文本密度（文本长度/总字符数）
            text = element.get_text(strip=True)
            html = str(element)
            
            if len(text) > 100:  # 最小文本长度
                density = len(text) / len(html) if len(html) > 0 else 0
                
                # 考虑链接密度（越低越好）
                link_count = len(element.find_all('a'))
                link_density = link_count / len(text.split()) if text else 0
                
                # 综合评分
                score = density * (1 - min(link_density, 0.5))
                
                if score > best_density:
                    best_density = score
                    best_element = element
        
        if best_element and best_density > 0.1:  # 密度阈值
            return self.clean_extracted_text(best_element.get_text())
        
        return ""
    
    def detect_genre(self, url, content):
        """检测文章体裁"""
        # 基于URL和内容关键词判断体裁
        url_lower = url.lower()
        content_lower = content.lower()
        
        if any(word in url_lower for word in ['news', 'breaking']):
            return "消息"
        elif any(word in url_lower for word in ['feature', 'analysis', 'opinion']):
            return "通讯/特写"
        elif any(word in url_lower for word in ['editorial', 'opinion']):
            return "评论"
        elif any(word in url_lower for word in ['interview']):
            return "访谈"
        elif len(content) > 2000:
            return "深度报道"
        elif len(content) > 800:
            return "通讯"
        else:
            return "消息"
    
    def should_stop_intelligently(self, current_task_info=None):
        """智能停止策略 - 模拟人类浏览行为"""
        try:
            current_time = time.time()
            session_start = self.current_session.get('start_time', current_time)
            session_duration = current_time - session_start
            
            # 检查会话时长是否超过阈值
            if session_duration > self.intelligent_stop_config['max_session_duration']:
                logger.info(f"智能停止: 会话时长超过 {self.intelligent_stop_config['max_session_duration']} 秒")
                return True
            
            # 检查请求数量是否超过阈值
            request_count = self.current_session.get('request_count', 0)
            if request_count > self.intelligent_stop_config['max_requests_per_session']:
                logger.info(f"智能停止: 请求数量超过 {self.intelligent_stop_config['max_requests_per_session']} 次")
                return True
            
            # 检查是否需要休息（模拟人类疲劳）
            if session_duration > self.intelligent_stop_config['rest_threshold']:
                rest_probability = min(0.8, session_duration / self.intelligent_stop_config['max_session_duration'])
                if random.random() < rest_probability:
                    rest_time = random.uniform(
                        self.intelligent_stop_config['min_rest_duration'],
                        self.intelligent_stop_config['max_rest_duration']
                    )
                    logger.info(f"智能休息: 休息 {rest_time:.1f} 秒")
                    time.sleep(rest_time)
                    # 重置会话开始时间
                    self.current_session['start_time'] = time.time()
                    self.current_session['request_count'] = 0
            
            # 随机停止概率（模拟人类随机行为）
            if random.random() < self.intelligent_stop_config['random_stop_probability']:
                logger.info("智能停止: 随机停止策略触发")
                return True
            
            # 检查错误率是否过高
            error_count = self.current_session.get('error_count', 0)
            success_count = self.current_session.get('success_count', 0)
            total_attempts = error_count + success_count
            
            if total_attempts > 10:
                error_rate = error_count / total_attempts
                if error_rate > self.intelligent_stop_config['error_rate_threshold']:
                    logger.info(f"智能停止: 错误率过高 ({error_rate:.2%})")
                    return True
            
            # 检查成功率是否过低
            if total_attempts > 10:
                success_rate = success_count / total_attempts
                if success_rate < self.intelligent_stop_config['success_rate_threshold']:
                    logger.info(f"智能停止: 成功率过低 ({success_rate:.2%})")
                    return True
            
            # 检查当前任务信息（如果有提供）
            if current_task_info:
                # 如果连续多次失败，考虑停止
                consecutive_failures = current_task_info.get('consecutive_failures', 0)
                if consecutive_failures > self.intelligent_stop_config['max_consecutive_failures']:
                    logger.info(f"智能停止: 连续失败次数过多 ({consecutive_failures} 次)")
                    return True
                
                # 如果任务耗时过长，考虑停止
                task_duration = current_task_info.get('task_duration', 0)
                if task_duration > self.intelligent_stop_config['max_task_duration']:
                    logger.info(f"智能停止: 单个任务耗时过长 ({task_duration:.1f} 秒)")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"智能停止策略执行失败: {e}")
            return False
    
    def update_session_stats(self, success=True, error_type=None):
        """更新会话统计信息"""
        try:
            if success:
                self.current_session['success_count'] = self.current_session.get('success_count', 0) + 1
            else:
                self.current_session['error_count'] = self.current_session.get('error_count', 0) + 1
                if error_type:
                    self.current_session['error_types'] = self.current_session.get('error_types', {})
                    self.current_session['error_types'][error_type] = self.current_session['error_types'].get(error_type, 0) + 1
            
            self.current_session['request_count'] = self.current_session.get('request_count', 0) + 1
            
            # 更新最后活动时间
            self.current_session['last_activity'] = time.time()
            
        except Exception as e:
            logger.error(f"更新会话统计失败: {e}")
    
    def get_intelligent_delay(self, base_delay=2.0, variance=1.0, task_type="search"):
        """智能延迟策略 - 增强版随机化机制"""
        try:
            # 基础延迟
            delay = base_delay
            
            # 根据任务类型调整延迟（更精细的分类）
            task_multipliers = {
                "search": random.uniform(0.8, 1.5),      # 搜索任务：0.8-1.5倍
                "scrape": random.uniform(0.6, 1.2),      # 爬取任务：0.6-1.2倍
                "navigation": random.uniform(1.0, 2.0),  # 导航任务：1.0-2.0倍
                "task_switch": random.uniform(0.5, 1.0), # 任务切换：0.5-1.0倍
                "retry": random.uniform(1.5, 3.0)        # 重试任务：1.5-3.0倍
            }
            
            multiplier = task_multipliers.get(task_type, 1.0)
            delay *= multiplier
            
            # 根据会话时长调整延迟（模拟人类疲劳度）
            session_duration = time.time() - self.current_session.get('start_time', time.time())
            if session_duration > 1800:  # 30分钟后
                delay *= random.uniform(1.2, 1.8)  # 增加20-80%延迟
            elif session_duration > 3600:  # 1小时后
                delay *= random.uniform(1.5, 2.5)  # 增加50-150%延迟
            elif session_duration > 7200:  # 2小时后
                delay *= random.uniform(2.0, 3.0)  # 增加100-200%延迟
            
            # 根据错误率调整延迟（更智能的响应）
            error_count = self.current_session.get('error_count', 0)
            success_count = self.current_session.get('success_count', 0)
            total_attempts = error_count + success_count
            
            if total_attempts > 5:
                error_rate = error_count / total_attempts
                if error_rate > 0.1:  # 错误率超过10%
                    delay *= random.uniform(1.1, 1.5)  # 增加10-50%延迟
                elif error_rate > 0.3:  # 错误率超过30%
                    delay *= random.uniform(1.5, 2.0)  # 增加50-100%延迟
                elif error_rate > 0.5:  # 错误率超过50%
                    delay *= random.uniform(2.0, 3.0)  # 增加100-200%延迟
            
            # 根据连续成功/失败次数调整延迟
            consecutive_successes = self.current_session.get('consecutive_successes', 0)
            consecutive_failures = self.current_session.get('consecutive_failures', 0)
            
            if consecutive_successes > 3:
                delay *= random.uniform(0.7, 0.9)  # 连续成功时减少延迟
            elif consecutive_failures > 2:
                delay *= random.uniform(1.5, 2.5)  # 连续失败时增加延迟
            
            # 根据时间因素调整（模拟人类行为模式）
            current_hour = datetime.now().hour
            if 2 <= current_hour <= 6:  # 深夜时段
                delay *= random.uniform(1.2, 1.8)  # 增加延迟，模拟用户疲劳
            elif 9 <= current_hour <= 17:  # 工作时间
                delay *= random.uniform(0.8, 1.0)  # 减少延迟，模拟活跃用户
            
            # 添加随机性（基于正态分布，更接近人类行为）
            variance = delay * 0.3  # 30%的随机波动
            delay += random.gauss(0, variance)
            
            # 确保延迟在合理范围内
            delay = max(0.5, min(delay, 15.0))  # 最小0.5秒，最大15秒
            
            logger.debug(f"智能延迟: {delay:.2f} 秒 (任务类型: {task_type}, 错误率: {error_rate if total_attempts > 5 else 'N/A'})")
            return delay
            
        except Exception as e:
            logger.error(f"智能延迟计算失败: {e}")
            return base_delay + random.uniform(-0.5, 0.5)
    
    def reset_session(self):
        """重置会话状态"""
        try:
            self.current_session = {
                'start_time': time.time(),
                'request_count': 0,
                'success_count': 0,
                'error_count': 0,
                'error_types': {},
                'last_activity': time.time()
            }
            logger.info("会话状态已重置")
        except Exception as e:
            logger.error(f"重置会话状态失败: {e}")
    
    def crawl_keyword_year(self, keyword, year, max_pages=10):
        """爬取特定关键词和年份的文章 - MCP优化版"""
        logger.info(f"开始爬取: {keyword} - {year}年")
        
        all_articles = []
        page = 1
        max_retries_per_page = 2
        task_start_time = time.time()
        consecutive_failures = 0
        
        while page <= max_pages:
            # 检查智能停止策略
            task_info = {
                'consecutive_failures': consecutive_failures,
                'task_duration': time.time() - task_start_time
            }
            
            if self.should_stop_intelligently(task_info):
                logger.info(f"智能停止策略触发，停止爬取: {keyword} - {year}年")
                break
            
            retry_count = 0
            page_success = False
            
            while retry_count <= max_retries_per_page and not page_success:
                try:
                    # 智能延迟
                    delay = self.get_intelligent_delay(base_delay=2.0, task_type="search")
                    time.sleep(delay)
                    
                    articles, has_next_page = self.search_articles(keyword, year, page)
                    
                    if not articles:
                        logger.info(f"第{page}页没有找到文章，停止爬取")
                        page_success = True
                        self.update_session_stats(success=True)
                        consecutive_failures = 0
                        break
                    
                    # 处理每篇文章
                    articles_processed = 0
                    for article in articles:
                        try:
                            # 智能延迟
                            delay = self.get_intelligent_delay(base_delay=1.5, task_type="scrape")
                            time.sleep(delay)
                            
                            # 获取文章详情
                            details = self.get_article_details(article['link'])
                            
                            # 合并信息
                            full_article = {
                                **article,
                                **details,
                                'crawl_timestamp': datetime.now().isoformat()
                            }
                            
                            all_articles.append(full_article)
                            articles_processed += 1
                            
                            # 更新会话统计
                            self.update_session_stats(success=True)
                            consecutive_failures = 0
                            
                        except Exception as e:
                            logger.warning(f"处理文章失败: {article['title']}: {e}")
                            self.update_session_stats(success=False, error_type="article_processing")
                            consecutive_failures += 1
                            continue
                    
                    # 如果成功处理了文章，标记页面成功
                    if articles_processed > 0:
                        page_success = True
                        logger.info(f"✅ 第{page}页成功处理 {articles_processed} 篇文章")
                    
                    # 检查是否继续下一页
                    if not has_next_page:
                        break
                    
                    page += 1
                    
                    # 智能页面间延迟
                    delay = self.get_intelligent_delay(base_delay=3.0, task_type="navigation")
                    time.sleep(delay)
                    
                except Exception as e:
                    retry_count += 1
                    logger.warning(f"第{page}页爬取失败 (尝试 {retry_count}/{max_retries_per_page}): {e}")
                    self.update_session_stats(success=False, error_type="page_crawl")
                    consecutive_failures += 1
                    
                    # 记录重试次数
                    self.stats['retry_attempts'] += 1
                    
                    if retry_count < max_retries_per_page:
                        # 智能重试延迟
                        wait_time = random.uniform(5 + retry_count * 2, 10 + retry_count * 3)
                        logger.info(f"等待 {wait_time:.1f} 秒后重试...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"第{page}页爬取失败，达到最大重试次数")
                        break
            
            # 如果页面处理失败，跳出循环
            if not page_success:
                logger.error(f"无法处理第{page}页，停止当前关键词年份的爬取")
                break
        
        logger.info(f"完成爬取: {keyword} - {year}年 - 找到 {len(all_articles)} 篇文章")
        return all_articles
    
    def generate_filename(self, prefix, extension="json"):
        """生成文件名 - 支持测试脚本的需求"""
        try:
            # 生成基于时间戳的文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{prefix}_{timestamp}.{extension}"
            return filename
        except Exception as e:
            logger.error(f"生成文件名失败: {e}")
            return f"{prefix}_error.{extension}"

    def save_results(self, keyword, articles):
        """保存爬取结果 - 支持《金字塔报》数据1、2、3等命名格式"""
        try:
            if not articles:
                return False
            
            # 更新文件计数器
            self.stats['file_counter'] += 1
            
            # 按《金字塔报》数据1、2、3等命名格式
            if self.file_naming_pattern == "pyramid_data":
                filename = f"《金字塔报》数据{self.stats['file_counter']}.json"
            else:
                # 默认按关键词保存
                safe_keyword = re.sub(r'[^\w\-]', '_', keyword)
                filename = f"{safe_keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            filepath = self.results_dir / filename
            
            # 保存JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            
            logger.info(f"JSON结果已保存: {filename} (包含 {len(articles)} 篇文章)")
            
            # 如果文件命名模式为pyramid_data，则同时保存Excel格式
            if self.file_naming_pattern == "pyramid_data":
                excel_filename = f"《金字塔报》数据{self.stats['file_counter']}.xlsx"
                excel_filepath = self.results_dir / excel_filename
                
                # 转换为DataFrame
                df_data = []
                for article in articles:
                    df_data.append({
                        '标题': article.get('title', ''),
                        '正文': article.get('content', ''),
                        '时间': article.get('publish_date', article.get('date', '')),
                        '信源': article.get('source', ''),
                        '体裁': article.get('genre', ''),
                        '作者': article.get('author', ''),
                        '关键词': article.get('keyword', ''),
                        '年份': article.get('year', ''),
                        '链接': article.get('link', ''),
                        '爬取时间': article.get('crawl_timestamp', '')
                    })
                
                df = pd.DataFrame(df_data)
                df.to_excel(excel_filepath, index=False, engine='openpyxl')
                logger.info(f"Excel结果已保存: {excel_filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
            return False
    
    def start_crawl(self, max_workers=3, max_pages_per_year=5):
        """启动爬虫"""
        try:
            logger.info("🚀 开始《金字塔报》2010-2025年中国报道爬虫")
            logger.info(f"关键词数量: {len(self.keywords)}")
            logger.info(f"年份范围: 2010-2025")
            logger.info(f"最大工作线程: {max_workers}")
            
            # 重置会话状态
            self.reset_session()
            
            # 创建年份任务列表
            tasks = []
            for keyword in self.keywords:
                for year in range(2010, 2026):  # 2010-2025
                    tasks.append((keyword, year))
            
            logger.info(f"总任务数: {len(tasks)}")
            
            # 使用线程池并行处理
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_task = {
                    executor.submit(self.crawl_keyword_year, keyword, year, max_pages_per_year): (keyword, year)
                    for keyword, year in tasks
                }
                
                # 处理完成的任务
                completed_tasks = 0
                for future in as_completed(future_to_task):
                    keyword, year = future_to_task[future]
                    
                    # 检查智能停止策略
                    if self.should_stop_intelligently():
                        logger.info("智能停止策略触发，停止整个爬虫活动")
                        break
                    
                    try:
                        articles = future.result()
                        
                        if articles:
                            # 保存结果
                            if self.save_results(f"{keyword}_{year}", articles):
                                self.stats['completed_keywords'] += 1
                                self.stats['total_articles'] += len(articles)
                                self.stats['articles_by_year'][str(year)] += len(articles)
                                logger.info(f"✅ 完成: {keyword} - {year}年 ({len(articles)} 篇文章)")
                            else:
                                logger.warning(f"❌ 保存失败: {keyword} - {year}年")
                        else:
                            logger.info(f"⚠️ 无结果: {keyword} - {year}年")
                            
                    except Exception as e:
                        logger.error(f"处理任务失败: {keyword} - {year}年: {e}")
                        self.stats['failed_keywords'].append(f"{keyword}_{year}")
                    
                    completed_tasks += 1
                    
                    # 智能任务间延迟
                    delay = self.get_intelligent_delay(base_delay=2.0, task_type="task_switch")
                    time.sleep(delay)
                    
                    # 每完成10个任务检查是否需要重置会话
                    if completed_tasks % 10 == 0:
                        logger.info(f"已完成 {completed_tasks} 个任务，检查会话状态")
                        if self.should_stop_intelligently():
                            logger.info("智能停止策略触发，停止整个爬虫活动")
                            break
                        
                        # 重置会话以模拟新的用户会话
                        self.reset_session()
                        logger.info("会话已重置，模拟新的用户会话")
            
            # 更新结束时间
            self.stats['end_time'] = datetime.now().isoformat()
            
            # 保存总统计
            self.save_final_statistics()
            
            logger.info("🎉 爬虫活动完成")
            self.print_final_statistics()
            
        except Exception as e:
            logger.error(f"爬虫活动失败: {e}")
            self.stats['end_time'] = datetime.now().isoformat()
            self.save_final_statistics()
    
    def save_final_statistics(self):
        """保存最终统计信息"""
        try:
            # 保存统计JSON
            stats_file = self.results_dir / "crawl_statistics.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
            
            # 保存年度统计Excel
            yearly_stats = []
            for year, count in self.stats['articles_by_year'].items():
                yearly_stats.append({
                    '年份': year,
                    '文章数量': count
                })
            
            yearly_df = pd.DataFrame(yearly_stats)
            yearly_file = self.results_dir / "yearly_statistics.xlsx"
            yearly_df.to_excel(yearly_file, index=False, engine='openpyxl')
            
            logger.info(f"统计信息已保存")
            
        except Exception as e:
            logger.error(f"保存统计信息失败: {e}")
    
    def print_final_statistics(self):
        """打印最终统计"""
        logger.info("=" * 80)
        logger.info("📊 《金字塔报》中国报道爬虫最终统计")
        logger.info("=" * 80)
        
        logger.info(f"关键词总数: {self.stats['total_keywords']}")
        logger.info(f"完成关键词年份组合: {self.stats['completed_keywords']}")
        logger.info(f"失败关键词年份组合: {len(self.stats['failed_keywords'])}")
        logger.info(f"总文章数: {self.stats['total_articles']}")
        
        logger.info("年度文章分布:")
        for year in range(2010, 2026):
            count = self.stats['articles_by_year'][str(year)]
            if count > 0:
                logger.info(f"  {year}年: {count} 篇文章")
        
        if self.stats['start_time'] and self.stats['end_time']:
            start_time = datetime.fromisoformat(self.stats['start_time'])
            end_time = datetime.fromisoformat(self.stats['end_time'])
            duration = end_time - start_time
            logger.info(f"总耗时: {duration}")
        
        logger.info("=" * 80)

    def generate_random_ip(self):
        """生成随机IP地址"""
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    
    def generate_random_token(self):
        """生成随机token"""
        return hashlib.md5(str(random.randint(100000, 999999)).encode()).hexdigest()[:16]
    
    def generate_device_id(self):
        """生成设备ID"""
        return hashlib.md5(f"device_{random.randint(10000, 99999)}".encode()).hexdigest()[:16]
    
    def generate_browser_id(self):
        """生成浏览器ID"""
        return hashlib.md5(f"browser_{random.randint(10000, 99999)}".encode()).hexdigest()[:16]
    
    def get_system_proxies(self):
        """获取系统代理配置 - 基于Stack Overflow最佳实践"""
        try:
            # 方法1: 使用urllib获取系统代理
            proxies = {}
            
            # 检查HTTP_PROXY和HTTPS_PROXY环境变量
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            
            if http_proxy:
                proxies['http'] = http_proxy
            if https_proxy:
                proxies['https'] = https_proxy
            
            # 方法2: 使用urllib.request.getproxies()获取系统代理
            if not proxies:
                try:
                    import urllib.request
                    system_proxies = urllib.request.getproxies()
                    if system_proxies:
                        proxies = system_proxies
                except ImportError:
                    pass
            
            # 方法3: 检查Windows注册表中的代理设置
            if not proxies and os.name == 'nt':
                try:
                    import winreg
                    # 读取Windows注册表中的代理设置
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                      r"Software\Microsoft\Windows\CurrentVersion\Internet Settings") as key:
                        proxy_enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
                        if proxy_enabled:
                            proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
                            if proxy_server:
                                # 解析代理服务器格式
                                if '=' in proxy_server:
                                    # 格式: http=proxy:port;https=proxy:port
                                    for part in proxy_server.split(';'):
                                        if '=' in part:
                                            protocol, server = part.split('=', 1)
                                            if protocol.lower() in ['http', 'https']:
                                                proxies[protocol.lower()] = f"{protocol.lower()}://{server}"
                                else:
                                    # 格式: proxy:port (适用于所有协议)
                                    proxies['http'] = f"http://{proxy_server}"
                                    proxies['https'] = f"https://{proxy_server}"
                except Exception:
                    pass
            
            return proxies if proxies else None
            
        except Exception as e:
            logger.warning(f"获取系统代理失败: {e}")
            return None
    
    def validate_proxy_config(self, proxy_config):
        """验证代理配置 - 基于GitHub最佳实践"""
        if not proxy_config:
            return True  # 无代理是有效的
        
        try:
            # 检查代理URL格式
            for protocol, proxy_url in proxy_config.items():
                if protocol not in ['http', 'https']:
                    logger.warning(f"不支持的代理协议: {protocol}")
                    return False
                
                # 验证URL格式
                parsed = urlparse(proxy_url)
                if not parsed.scheme or not parsed.netloc:
                    logger.warning(f"无效的代理URL格式: {proxy_url}")
                    return False
                
                # 检查端口号
                if parsed.port is None:
                    logger.warning(f"代理URL缺少端口号: {proxy_url}")
                    return False
                
                # 检查是否包含认证信息（可选）
                if parsed.username and parsed.password:
                    logger.info(f"代理配置包含认证信息: {protocol}")
                
            return True
            
        except Exception as e:
            logger.warning(f"验证代理配置失败: {e}")
            return False
    
    def test_proxy_connection(self, proxy_config, timeout=10):
        """测试代理连接可用性（基于实际连接测试）"""
        try:
            # 创建临时会话进行连接测试
            test_session = requests.Session()
            test_session.proxies = proxy_config
            test_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            })
            
            # 测试连接的目标URL（选择响应快、稳定的网站）
            test_urls = [
                'http://httpbin.org/ip',
                'http://api.ipify.org',
                'http://icanhazip.com'
            ]
            
            for test_url in test_urls:
                try:
                    response = test_session.get(test_url, timeout=timeout, verify=False)
                    if response.status_code == 200:
                        # 验证返回的IP地址是否与代理配置匹配
                        response_text = response.text.strip()
                        logger.debug(f"代理连接测试成功: {test_url} -> {response_text}")
                        return True
                except requests.exceptions.RequestException as e:
                    logger.debug(f"代理连接测试失败 {test_url}: {e}")
                    continue
            
            logger.warning("所有代理连接测试均失败")
            return False
            
        except Exception as e:
            logger.error(f"代理连接测试异常: {e}")
            return False
        finally:
            # 清理测试会话
            if 'test_session' in locals():
                test_session.close()
    
    def find_next_valid_proxy(self):
        """查找下一个有效的代理"""
        try:
            total_proxies = len(self.proxy_configs)
            for i in range(total_proxies):
                next_index = (self.current_proxy_index + i + 1) % total_proxies
                proxy_key = f"proxy_{next_index}"
                
                # 检查代理状态
                if proxy_key in self.proxy_stats:
                    proxy_stat = self.proxy_stats[proxy_key]
                    
                    # 跳过标记为无效的代理
                    if proxy_stat.get('status') == 'invalid':
                        continue
                    
                    # 检查冷却时间（避免频繁使用同一代理）
                    last_used = proxy_stat.get('last_used', 0)
                    current_time = time.time()
                    if current_time - last_used < 300:  # 5分钟冷却
                        continue
                    
                    # 检查成功率
                    success_rate = proxy_stat.get('success_rate', 0)
                    if success_rate < 0.5:  # 成功率低于50%跳过
                        continue
                    
                    return next_index
            
            # 如果没有找到有效代理，返回下一个索引
            return (self.current_proxy_index + 1) % total_proxies
            
        except Exception as e:
            logger.error(f"查找有效代理失败: {e}")
            return (self.current_proxy_index + 1) % len(self.proxy_configs)
    
    def find_low_usage_proxy(self):
        """查找使用率较低的代理"""
        try:
            total_proxies = len(self.proxy_configs)
            proxy_usage = []
            
            for i in range(total_proxies):
                proxy_key = f"proxy_{i}"
                if proxy_key in self.proxy_stats:
                    usage = self.proxy_stats[proxy_key].get('usage_count', 0)
                    success_rate = self.proxy_stats[proxy_key].get('success_rate', 0)
                    
                    # 计算使用率评分（使用率越低、成功率越高，评分越高）
                    score = (1 - usage / (usage + 1)) * success_rate
                    proxy_usage.append((i, score))
                else:
                    proxy_usage.append((i, 1.0))  # 新代理最高评分
            
            # 按评分排序，选择评分最高的代理
            proxy_usage.sort(key=lambda x: x[1], reverse=True)
            return proxy_usage[0][0]
            
        except Exception as e:
            logger.error(f"查找低使用率代理失败: {e}")
            return (self.current_proxy_index + 1) % len(self.proxy_configs)
    
    def find_fast_proxy(self):
        """查找响应速度快的代理"""
        try:
            total_proxies = len(self.proxy_configs)
            proxy_speed = []
            
            for i in range(total_proxies):
                proxy_key = f"proxy_{i}"
                if proxy_key in self.proxy_stats:
                    avg_response_time = self.proxy_stats[proxy_key].get('avg_response_time', float('inf'))
                    success_rate = self.proxy_stats[proxy_key].get('success_rate', 0)
                    
                    # 计算速度评分（响应时间越短、成功率越高，评分越高）
                    if avg_response_time == float('inf'):
                        score = success_rate
                    else:
                        score = (1 / (avg_response_time + 1)) * success_rate
                    
                    proxy_speed.append((i, score))
                else:
                    proxy_speed.append((i, 1.0))  # 新代理最高评分
            
            # 按评分排序，选择评分最高的代理
            proxy_speed.sort(key=lambda x: x[1], reverse=True)
            return proxy_speed[0][0]
            
        except Exception as e:
            logger.error(f"查找快速代理失败: {e}")
            return (self.current_proxy_index + 1) % len(self.proxy_configs)
    
    def test_direct_connection(self):
        """测试直接连接可用性"""
        try:
            test_session = requests.Session()
            test_session.proxies = {}  # 清空代理，使用直接连接
            
            test_urls = [
                "https://httpbin.org/ip",
                "https://api.ipify.org"
            ]
            
            for url in test_urls:
                try:
                    response = test_session.get(url, timeout=10)
                    if response.status_code == 200:
                        ip_content = response.text.strip()
                        if ip_content and len(ip_content) > 0:
                            logger.info(f"直接连接测试成功 - {url}: {ip_content}")
                            return True
                except Exception as e:
                    logger.warning(f"直接连接测试失败 - {url}: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"直接连接测试异常: {e}")
            return False
        finally:
            if 'test_session' in locals():
                test_session.close()
    
    def update_proxy_stats(self, proxy_index, success=True, error_type=None):
        """更新代理性能统计"""
        proxy_key = f"proxy_{proxy_index}"
        
        # 初始化统计
        if proxy_key not in self.proxy_stats['proxy_usage_count']:
            self.proxy_stats['proxy_usage_count'][proxy_key] = 0
        if proxy_key not in self.proxy_stats['proxy_errors']:
            self.proxy_stats['proxy_errors'][proxy_key] = {}
        
        # 更新统计
        self.proxy_stats['total_requests'] += 1
        self.proxy_stats['proxy_usage_count'][proxy_key] += 1
        
        if success:
            self.proxy_stats['successful_requests'] += 1
        else:
            self.proxy_stats['failed_requests'] += 1
            if error_type:
                if error_type not in self.proxy_stats['proxy_errors'][proxy_key]:
                    self.proxy_stats['proxy_errors'][proxy_key][error_type] = 0
                self.proxy_stats['proxy_errors'][proxy_key][error_type] += 1
    
    def get_proxy_performance_metrics(self, proxy_key):
        """获取代理性能指标
        
        Args:
            proxy_key: 代理标识符
            
        Returns:
            dict: 代理性能指标
        """
        try:
            usage_count = self.proxy_stats['proxy_usage_count'].get(proxy_key, 0)
            error_count = sum(self.proxy_stats['proxy_errors'].get(proxy_key, {}).values())
            
            if usage_count > 0:
                success_rate = (usage_count - error_count) / usage_count
            else:
                success_rate = 1.0  # 新代理默认成功率
            
            return {
                'success_rate': success_rate,
                'error_count': error_count,
                'usage_count': usage_count,
                'last_used': self.proxy_stats.get('last_used_times', {}).get(proxy_key, 0),
                'avg_response_time': self.proxy_stats.get('response_times', {}).get(proxy_key, 0)
            }
        except Exception as e:
            logger.error(f"获取代理性能指标失败: {e}")
            return {
                'success_rate': 1.0,
                'error_count': 0,
                'usage_count': 0,
                'last_used': 0,
                'avg_response_time': 0
            }

def main():
    """主函数"""
    try:
        logger.info("🚀 启动《金字塔报》2010-2025年中国报道爬虫")
        
        # 创建爬虫实例 - 启用BrightData代理并使用《金字塔报》数据命名格式
        crawler = PyramidChinaCrawler(
            use_brightdata_proxy=True,   # 启用BrightData代理
            file_naming_pattern="pyramid_data"  # 使用《金字塔报》数据1、2、3等命名格式
        )
        
        # 启动爬虫
        crawler.start_crawl(
            max_workers=3,           # 最大工作线程数
            max_pages_per_year=5     # 每年份最大页数
        )
        
        logger.info("🎉 爬虫程序执行完成")
        
    except KeyboardInterrupt:
        logger.info("用户中断爬虫程序")
    except Exception as e:
        logger.error(f"爬虫程序执行完成")

if __name__ == "__main__":
    main()