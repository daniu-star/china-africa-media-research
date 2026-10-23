#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非洲报纸专业爬虫系统
专门针对五家非洲报纸优化：Ahram Online, The Citizen, Vanguard, Nation Africa, Mail & Guardian
支持关键词搜索、翻页爬取、断点续爬、并行处理
集成高级反反爬虫技术：浏览器指纹模拟、智能代理轮换、动态行为模拟
"""

import requests
import time
import random
import json
import os
import re
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urlencode, urljoin
import logging
import urllib3
from bs4 import BeautifulSoup
import threading

# 导入优化后的反反爬虫模块
from advanced_anti_anti_crawler import AdvancedAntiAntiCrawler, AdvancedProxyManager, IntelligentRetryStrategy
from data_quality_optimizer import data_quality_optimizer
from smart_retry_handler import SmartRetryHandler

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('african_newspaper_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AfricanNewspaperCrawler:
    """非洲报纸专业爬虫类"""
    
    def __init__(self, max_workers=3):
        self.max_workers = max_workers
        
        # 初始化高级反反爬虫系统
        self.anti_crawler = AdvancedAntiAntiCrawler()
        self.proxy_manager = AdvancedProxyManager()
        self.retry_strategy = IntelligentRetryStrategy()
        self.smart_retry_handler = SmartRetryHandler()
        
        # 报纸配置
        self.newspapers = {
            'ahram': {
                'name': 'Ahram Online (埃及)',
                'base_url': 'https://english.ahram.org.eg',
                'search_url': 'https://english.ahram.org.eg/UI/Front/Search.aspx',
                'timeout': (10, 25),
                'verify_ssl': True,
                'search_params': {
                    'Text': '',  # 关键词
                    'StartRowIndex': 0
                }
            },
            'citizen': {
                'name': 'The Citizen (坦桑尼亚)',
                'base_url': 'https://www.citizen.digital',
                'search_url': 'https://www.citizen.digital/search',
                'timeout': (15, 30),  # 连接困难，设置更长超时
                'verify_ssl': True,
                'search_params': {
                    'q': '',
                    'page': 1
                }
            },
            'vanguard': {
                'name': 'Vanguard (尼日利亚)',
                'base_url': 'https://www.vanguardngr.com',
                'search_url': 'https://www.vanguardngr.com/search',
                'timeout': (12, 28),
                'verify_ssl': False,
                'search_params': {
                    's': '',  # 搜索关键词
                    'paged': 1
                }
            },
            'nation': {
                'name': 'Nation Africa (肯尼亚)',
                'base_url': 'https://nation.africa',
                'search_url': 'https://nation.africa/',
                'timeout': (8, 20),
                'verify_ssl': True,
                'search_params': {
                    's': '',
                    'page': 1
                }
            },
            'mg': {
                'name': 'Mail & Guardian (南非)',
                'base_url': 'https://mg.co.za',
                'search_url': 'https://mg.co.za/',
                'timeout': (10, 22),
                'verify_ssl': True,
                'search_params': {
                    's': '',  # WordPress搜索参数
                    'page': 1
                }
            }
        }
        
        # 用户代理列表
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # 数据存储配置
        self.data_dir = 'african_newspaper_data'
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 断点续爬状态文件
        self.state_file = os.path.join(self.data_dir, 'crawler_state.json')
        
    def get_session(self, newspaper_key):
        """获取针对特定报纸优化的会话，集成高级反反爬虫技术和智能错误统计"""
        config = self.newspapers[newspaper_key]
        
        session = requests.Session()
        session.timeout = config['timeout']
        session.verify = config['verify_ssl']
        
        # 使用高级反反爬虫技术生成隐身请求头
        stealth_headers = self.anti_crawler.generate_stealth_headers("")
        
        # 设置请求头，优先使用反反爬虫生成的隐身头
        session.headers.update({
            'User-Agent': stealth_headers.get('User-Agent', random.choice(self.user_agents)),
            'Accept': stealth_headers.get('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
            'Accept-Language': stealth_headers.get('Accept-Language', 'en-US,en;q=0.5'),
            'Accept-Encoding': stealth_headers.get('Accept-Encoding', 'gzip, deflate'),
            'Connection': stealth_headers.get('Connection', 'keep-alive'),
            'Cache-Control': stealth_headers.get('Cache-Control', 'max-age=0'),
            'Referer': config['base_url'],
            # 添加高级反爬虫头
            'Sec-CH-UA': stealth_headers.get('Sec-CH-UA', ''),
            'Sec-CH-UA-Mobile': stealth_headers.get('Sec-CH-UA-Mobile', ''),
            'Sec-CH-UA-Platform': stealth_headers.get('Sec-CH-UA-Platform', '')
        })
        
        # 配置代理轮换
        proxy = self.proxy_manager.get_next_proxy()
        if proxy:
            session.proxies = {
                'http': proxy,
                'https': proxy
            }
        
        # 配置智能重试策略
        adapter = requests.adapters.HTTPAdapter(
            max_retries=self.retry_strategy.get_retry_config()
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        # 集成智能重试处理器的错误统计功能
        # 为会话添加错误统计属性
        session.error_stats = {
            'newspaper': newspaper_key,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'error_types': {},
            'last_error': None,
            'last_success': None
        }
        
        # 重写会话的请求方法以集成错误统计
        original_request = session.request
        
        def request_with_stats(*args, **kwargs):
            session.error_stats['total_requests'] += 1
            
            try:
                response = original_request(*args, **kwargs)
                
                # 检查响应状态
                if response.status_code >= 400:
                    session.error_stats['failed_requests'] += 1
                    error_category = self.smart_retry_handler.classify_error(
                        Exception(f"HTTP {response.status_code}"), response, args[1] if len(args) > 1 else ''
                    )
                    
                    # 记录错误类型
                    error_type = error_category.value
                    if error_type not in session.error_stats['error_types']:
                        session.error_stats['error_types'][error_type] = 0
                    session.error_stats['error_types'][error_type] += 1
                    
                    session.error_stats['last_error'] = {
                        'timestamp': datetime.now().isoformat(),
                        'error_type': error_type,
                        'status_code': response.status_code,
                        'url': args[1] if len(args) > 1 else ''
                    }
                else:
                    session.error_stats['successful_requests'] += 1
                    session.error_stats['last_success'] = datetime.now().isoformat()
                
                return response
                
            except Exception as e:
                session.error_stats['failed_requests'] += 1
                
                # 分类错误类型
                error_category = self.smart_retry_handler.classify_error(
                    e, None, args[1] if len(args) > 1 else ''
                )
                
                # 记录错误类型
                error_type = error_category.value
                if error_type not in session.error_stats['error_types']:
                    session.error_stats['error_types'][error_type] = 0
                session.error_stats['error_types'][error_type] += 1
                
                session.error_stats['last_error'] = {
                    'timestamp': datetime.now().isoformat(),
                    'error_type': error_type,
                    'exception': str(e),
                    'url': args[1] if len(args) > 1 else ''
                }
                
                # 更新智能重试处理器的错误统计
                self.smart_retry_handler.update_error_stats(error_category, False)
                
                raise
        
        session.request = request_with_stats
        
        return session
    
    def parse_article_ahram(self, soup, url):
        """解析Ahram Online文章 - 基于浏览器分析优化"""
        try:
            # 标题 - 使用浏览器分析确认的选择器
            title_elem = soup.find('h1', id='ContentPlaceHolder1_hd') or soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else ""
            
            # 发布时间 - 使用浏览器分析确认的选择器
            date_elem = soup.find('h6', id='ContentPlaceHolder1_sourceWr') or soup.find('h6')
            publish_time = ""
            if date_elem:
                # 尝试从元素文本或属性获取日期
                date_text = date_elem.get_text().strip()
                if date_text:
                    publish_time = date_text
                else:
                    # 如果日期元素为空，尝试其他选择器
                    alt_date_elem = soup.find(class_=re.compile(r'date|time|source'))
                    if alt_date_elem:
                        publish_time = alt_date_elem.get_text().strip()
            
            # 正文内容 - 使用浏览器分析确认的结构
            content = ""
            # 首先尝试找到主要内容区域
            main_content = soup.find('div', id='mainContent') or soup.find('article') or soup.find('div', class_='content')
            if main_content:
                # 提取所有段落文本，过滤空段落
                paragraphs = main_content.find_all('p')
                valid_paragraphs = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                content = ' '.join(valid_paragraphs)
            else:
                # 如果没有找到主要内容区域，尝试通用方法
                paragraphs = soup.find_all('p')
                valid_paragraphs = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                content = ' '.join(valid_paragraphs)
            
            # 作者 - 使用浏览器分析确认的选择器
            author_elem = soup.find('a', href=re.compile(r'WriterArticles')) or soup.find(class_=re.compile(r'author|byline'))
            author = "Ahram Online"
            if author_elem:
                author_text = author_elem.get_text().strip()
                if author_text:
                    author = author_text
            
            # 字数统计
            word_count = len(content.split()) if content else 0
            
            # 提取图片信息（可选）
            images = []
            img_elements = soup.find_all('img', class_='img-fluid')
            for img in img_elements:
                img_src = img.get('src', '')
                img_alt = img.get('alt', '')
                if img_src and not img_src.endswith('logo.png') and not img_src.endswith('x-twitter.svg'):
                    images.append({
                        'src': img_src,
                        'alt': img_alt
                    })
            
            return {
                'title': title,
                'content': content,
                'source': author,
                'publish_time': publish_time,
                'genre': self.detect_genre(title, content),
                'newspaper': 'Ahram Online',
                'word_count': word_count,
                'url': url,
                'images': images[:5]  # 限制图片数量
            }
        except Exception as e:
            logger.error(f"解析Ahram文章失败: {e}")
            return None
    
    def parse_article_nation(self, soup, url):
        """解析Nation Africa文章"""
        try:
            # 标题
            title_elem = soup.find('h1') or soup.find(class_=re.compile(r'title|headline'))
            title = title_elem.get_text().strip() if title_elem else ""
            
            # 发布时间
            date_elem = soup.find('time') or soup.find(class_=re.compile(r'timestamp|date'))
            publish_time = date_elem.get('datetime') if date_elem else ""
            if not publish_time and date_elem:
                publish_time = date_elem.get_text().strip()
            
            # 正文内容
            content_elem = soup.find('article') or soup.find(class_=re.compile(r'story-body|article-content'))
            content = ""
            if content_elem:
                paragraphs = content_elem.find_all('p')
                content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            # 作者
            author_elem = soup.find(class_=re.compile(r'author|byline'))
            author = author_elem.get_text().strip() if author_elem else "Nation Africa"
            
            word_count = len(content.split())
            
            return {
                'title': title,
                'content': content,
                'source': author,
                'publish_time': publish_time,
                'genre': self.detect_genre(title, content),
                'newspaper': 'Nation Africa',
                'word_count': word_count,
                'url': url
            }
        except Exception as e:
            logger.error(f"解析Nation文章失败: {e}")
            return None
    
    def parse_article_mg(self, soup, url):
        """解析Mail & Guardian文章"""
        try:
            # 标题
            title_elem = soup.find('h1') or soup.find(class_=re.compile(r'entry-title|headline'))
            title = title_elem.get_text().strip() if title_elem else ""
            
            # 发布时间
            date_elem = soup.find('time') or soup.find(class_=re.compile(r'entry-date|timestamp'))
            publish_time = date_elem.get('datetime') if date_elem else ""
            if not publish_time and date_elem:
                publish_time = date_elem.get_text().strip()
            
            # 正文内容
            content_elem = soup.find('article') or soup.find(class_=re.compile(r'entry-content|article-body'))
            content = ""
            if content_elem:
                paragraphs = content_elem.find_all('p')
                content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            # 作者
            author_elem = soup.find(class_=re.compile(r'author|byline'))
            author = author_elem.get_text().strip() if author_elem else "Mail & Guardian"
            
            word_count = len(content.split())
            
            return {
                'title': title,
                'content': content,
                'source': author,
                'publish_time': publish_time,
                'genre': self.detect_genre(title, content),
                'newspaper': 'Mail & Guardian',
                'word_count': word_count,
                'url': url
            }
        except Exception as e:
            logger.error(f"解析Mail & Guardian文章失败: {e}")
            return None
    
    def detect_genre(self, title, content):
        """检测报道体裁"""
        text = f"{title} {content}".lower()
        
        if any(word in text for word in ['opinion', 'comment', 'view', 'analysis']):
            return '评论'
        elif any(word in text for word in ['news', 'report', 'update']):
            return '消息'
        elif any(word in text for word in ['feature', 'story', 'profile']):
            return '通讯'
        elif any(word in text for word in ['interview', 'q&a']):
            return '访谈'
        else:
            return '其他'
    
    def search_articles(self, newspaper_key, keyword, max_articles=10):
        """搜索文章，返回文章链接列表"""
        config = self.newspapers[newspaper_key]
        
        # 构建搜索URL
        search_url = config['search_url']
        params = config['search_params'].copy()
        params['q'] = keyword
        
        full_url = f"{search_url}?{urlencode(params)}"
        
        def search_function():
            """搜索函数，用于智能重试"""
            session = self.get_session(newspaper_key)
            
            # 发送搜索请求
            response = session.get(full_url)
            
            if response.status_code == 200:
                # 检测反爬虫措施
                risk_result = self.anti_crawler.detect_anti_crawler_measures(response.headers, response.text)
                risk_score = risk_result.get('overall_risk_score', 0)
                if risk_score > 0.3:
                    logger.info(f"{config['name']} 检测到反爬虫措施，风险评分: {risk_score}")
                    
                    # 根据风险等级触发规避策略
                    evasion_strategy = self.anti_crawler.generate_evasion_strategy(risk_result)
                    logger.info(f"应用规避策略: {evasion_strategy}")
                
                # 解析搜索结果页面
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 根据报纸类型提取文章链接
                article_links = []
                
                if newspaper_key == 'ahram':
                    # 埃及金字塔报链接提取
                    link_pattern = re.compile(r'/Article/')
                    links = soup.find_all('a', href=link_pattern)
                    article_links = [link.get('href') for link in links if link.get('href')]
                    
                elif newspaper_key == 'citizen':
                    # 坦桑尼亚公民报链接提取
                    link_pattern = re.compile(r'/news/')
                    links = soup.find_all('a', href=link_pattern)
                    article_links = [link.get('href') for link in links if link.get('href')]
                    
                elif newspaper_key == 'vanguard':
                    # 尼日利亚先锋报链接提取
                    link_pattern = re.compile(r'/\d{4}/\d{2}/')
                    links = soup.find_all('a', href=link_pattern)
                    article_links = [link.get('href') for link in links if link.get('href')]
                    
                elif newspaper_key == 'nation':
                    # 肯尼亚民族报链接提取
                    link_pattern = re.compile(r'/news/')
                    links = soup.find_all('a', href=link_pattern)
                    article_links = [link.get('href') for link in links if link.get('href')]
                    
                elif newspaper_key == 'mg':
                    # 南非Mail & Guardian链接提取
                    # 使用日期格式匹配文章链接，如：/2024/01/15/article-title/
                    link_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
                    links = soup.find_all('a', href=link_pattern)
                    article_links = [link.get('href') for link in links if link.get('href')]
                
                # 处理相对链接
                article_links = [urljoin(config['base_url'], link) for link in article_links]
                
                # 去重
                article_links = list(set(article_links))
                
                # 限制返回数量
                article_links = article_links[:max_articles]
                
                logger.info(f"{config['name']} 搜索到 {len(article_links)} 篇文章")
                return article_links
            else:
                # 返回响应对象以便错误分类
                return response
        
        # 使用智能重试处理器执行搜索
        result = self.smart_retry_handler.execute_with_retry(
            search_function,
            url=full_url,
            description=f"搜索 {config['name']} 中的 '{keyword}'"
        )
        
        # 处理结果
        if isinstance(result, list):
            return result
        else:
            logger.warning(f"搜索失败，返回空列表")
            return []
    
    def crawl_article(self, newspaper_key, article_url):
        """爬取单篇文章内容，集成动态行为模拟和智能重试"""
        config = self.newspapers[newspaper_key]
        
        def crawl_function():
            """内部爬取函数，包装爬取逻辑"""
            session = self.get_session(newspaper_key)
            
            # 发送请求获取文章内容
            response = session.get(article_url)
            
            if response.status_code == 200:
                # 检测反爬虫措施
                risk_result = self.anti_crawler.detect_anti_crawler_measures(response.headers, response.text)
                risk_score = risk_result.get('overall_risk_score', 0)
                if risk_score > 0.3:
                    logger.info(f"{config['name']} 检测到反爬虫措施，风险评分: {risk_score}")
                    
                    # 根据风险等级触发行为模拟
                    if risk_score > 0.7:
                        # 高风险：模拟完整浏览会话
                        logger.info("触发完整浏览会话模拟")
                        self.anti_crawler.simulate_human_interaction(article_url)
                    elif risk_score > 0.5:
                        # 中等风险：模拟滚动行为
                        logger.info("触发滚动行为模拟")
                        self.anti_crawler.behavior_simulator.generate_scroll_pattern()
                
                # 解析文章内容
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 根据报纸类型调用不同的解析方法
                if newspaper_key == 'ahram':
                    article_data = self.parse_article_ahram(soup, article_url)
                elif newspaper_key == 'nation':
                    article_data = self.parse_article_nation(soup, article_url)
                elif newspaper_key == 'mg':
                    article_data = self.parse_article_mg(soup, article_url)
                else:
                    # 通用解析方法
                    article_data = self.parse_article_generic(soup, article_url, config['name'])
                
                if article_data:
                    # 数据质量验证和清洗
                    article_data = self._validate_and_clean_article_data(article_data, response.text)
                    
                    # 添加爬取时间
                    article_data['crawl_time'] = datetime.now().isoformat()
                    return article_data
                else:
                    logger.warning(f"无法解析文章内容: {article_url}")
                    return None
            else:
                logger.warning(f"获取文章失败，状态码: {response.status_code}, URL: {article_url}")
                # 返回响应对象以便错误分类
                return response
        
        # 使用智能重试处理器执行爬取
        result = self.smart_retry_handler.execute_with_retry(
            crawl_function,
            url=article_url,
            description=f"爬取 {config['name']} 文章"
        )
        
        # 处理结果
        if isinstance(result, dict):  # 成功返回文章数据
            return result
        else:
            logger.warning(f"爬取文章失败，返回None")
            return None
    
    def parse_article_generic(self, soup, article_url, newspaper_name):
        """通用文章解析方法"""
        try:
            article_data = {
                'url': article_url,
                'newspaper': newspaper_name,
                'title': '',
                'publish_time': '',
                'content': '',
                'author': '',
                'genre': ''
            }
            
            # 提取标题
            title_selectors = ['h1', '.title', '.headline', 'h2', 'h3']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.get_text().strip():
                    article_data['title'] = title_elem.get_text().strip()
                    break
            
            # 提取发布时间
            time_selectors = ['.date', '.time', '.publish-date', 'time', '[datetime]']
            for selector in time_selectors:
                time_elem = soup.select_one(selector)
                if time_elem:
                    time_text = time_elem.get_text().strip()
                    if time_text:
                        article_data['publish_time'] = time_text
                        break
                    
                    # 尝试从datetime属性获取
                    datetime_attr = time_elem.get('datetime')
                    if datetime_attr:
                        article_data['publish_time'] = datetime_attr
                        break
            
            # 提取正文内容
            content_selectors = ['.content', '.article-body', '.story-content', 'article', 'main']
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 清理内容中的脚本和样式
                    for script in content_elem(['script', 'style']):
                        script.decompose()
                    
                    content_text = content_elem.get_text().strip()
                    if content_text and len(content_text) > 50:  # 确保有足够的内容
                        article_data['content'] = content_text
                        break
            
            # 提取作者
            author_selectors = ['.author', '.byline', '.writer']
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author_text = author_elem.get_text().strip()
                    if author_text:
                        article_data['author'] = author_text
                        break
            
            # 检测文章类型
            article_data['genre'] = self.detect_genre(article_data['title'], article_data['content'])
            
            # 验证必要字段
            if not article_data['title'] or not article_data['content']:
                logger.warning(f"文章缺少必要字段: {article_url}")
                return None
            
            return article_data
            
        except Exception as e:
            logger.error(f"解析文章失败: {e}, URL: {article_url}")
            return None
    
    def _validate_and_clean_article_data(self, article_data, raw_html):
        """数据验证和清洗方法"""
        try:
            # 使用数据质量优化器进行质量评估
            quality_result = data_quality_optimizer.clean_content_quality(raw_html)
            
            # 添加质量评分信息
            article_data['quality_score'] = quality_result.get('quality_score', {}).get('overall', 0)
            article_data['quality_issues'] = []  # 暂时设为空列表
            article_data['quality_suggestions'] = []  # 暂时设为空列表
            
            # 根据质量评分进行数据清洗
            if article_data['quality_score'] < 0.6:
                logger.warning(f"文章质量评分较低: {article_data['quality_score']}")
                
                # 尝试从质量结果中获取更好的数据
                if quality_result.get('title') and not article_data.get('title'):
                    article_data['title'] = quality_result['title']
                
                if quality_result.get('content') and len(quality_result['content']) > len(article_data.get('content', '')):
                    article_data['content'] = quality_result['content']
            
            # 清理和标准化数据
            article_data = self._clean_article_fields(article_data)
            
            # 验证数据完整性
            if not self._validate_article_completeness(article_data):
                logger.warning(f"文章数据不完整: {article_data.get('url', 'Unknown URL')}")
            
            return article_data
            
        except Exception as e:
            logger.error(f"数据验证和清洗失败: {e}")
            return article_data
    
    def _clean_article_fields(self, article_data):
        """清理和标准化文章字段"""
        # 清理标题
        if article_data.get('title'):
            article_data['title'] = re.sub(r'\s+', ' ', article_data['title']).strip()
            article_data['title'] = re.sub(r'^[\s\-\|]+|[\s\-\|]+$', '', article_data['title'])
        
        # 清理内容
        if article_data.get('content'):
            # 移除多余的空格和换行
            article_data['content'] = re.sub(r'\s+', ' ', article_data['content']).strip()
            # 移除HTML实体
            article_data['content'] = re.sub(r'&[a-z]+;', ' ', article_data['content'])
            # 移除特殊字符（使用更简单的字符类）
            article_data['content'] = re.sub(r'[^\w\s\u00C0-\u017F\u0400-\u04FF\u0600-\u06FF\s.,!?;:()\-]', '', article_data['content'])
        
        # 清理作者信息
        if article_data.get('author'):
            article_data['author'] = re.sub(r'^\s*(by|作者|writer|reporter)[:\s]*', '', 
                                          article_data['author'], flags=re.IGNORECASE).strip()
        
        # 标准化发布时间
        if article_data.get('publish_time'):
            article_data['publish_time'] = self._normalize_publish_time(article_data['publish_time'])
        
        return article_data
    
    def _normalize_publish_time(self, time_str):
        """标准化发布时间格式"""
        try:
            # 尝试解析常见日期格式
            date_formats = [
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%d/%m/%Y %H:%M',
                '%m/%d/%Y %H:%M',
                '%Y-%m-%d',
                '%d %B %Y',
                '%B %d, %Y'
            ]
            
            for fmt in date_formats:
                try:
                    dt = datetime.strptime(time_str, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            
            # 如果无法解析，返回原始字符串
            return time_str
            
        except Exception:
            return time_str
    
    def _validate_article_completeness(self, article_data):
        """验证文章数据完整性"""
        required_fields = ['title', 'content', 'url']
        
        for field in required_fields:
            if not article_data.get(field):
                return False
        
        # 验证内容长度
        if len(article_data.get('content', '')) < 100:
            return False
        
        # 验证标题长度
        if len(article_data.get('title', '')) < 10:
            return False
        
        return True
    
    def save_article_data(self, newspaper_key, article_data):
        """保存文章数据到JSON文件"""
        if not article_data:
            return
        
        # 按报纸和日期组织文件结构
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"{newspaper_key}_{date_str}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        # 读取现有数据
        existing_data = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except:
                existing_data = []
        
        # 避免重复添加相同URL的文章
        existing_urls = {item.get('url') for item in existing_data if item.get('url')}
        if article_data['url'] not in existing_urls:
            existing_data.append(article_data)
            
            # 保存数据
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"保存文章: {article_data['title'][:50]}...")
    
    def load_crawler_state(self):
        """加载爬虫状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_crawler_state(self, state):
        """保存爬虫状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

# 测试函数
def test_african_crawler():
    """测试非洲报纸爬虫"""
    print("=== 非洲报纸爬虫测试 ===")
    
    crawler = AfricanNewspaperCrawler()
    
    # 测试关键词
    test_keywords = ['China', 'Africa', 'trade']
    
    for keyword in test_keywords:
        print(f"\n测试关键词: {keyword}")
        
        for newspaper_key in ['ahram', 'nation', 'mg']:
            print(f"搜索 {crawler.newspapers[newspaper_key]['name']}...")
            
            # 搜索文章
            article_urls = crawler.search_articles(newspaper_key, keyword)
            print(f"找到 {len(article_urls)} 篇文章")
            
            # 爬取第一篇文章作为测试
            if article_urls:
                article_data = crawler.crawl_article(newspaper_key, article_urls[0])
                if article_data:
                    print(f"成功爬取: {article_data['title'][:50]}...")
                    # 保存测试数据
                    crawler.save_article_data(newspaper_key, article_data)

if __name__ == "__main__":
    test_african_crawler()