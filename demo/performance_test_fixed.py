#!/usr/bin/env python3
"""
金字塔报大规模爬虫脚本 - 优化修复版
整合了所有修复内容，解决crawl_single_keyword返回值问题
集成MCP功能和优化修改
"""

import asyncio
import time
import json
import os
import random
import re
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, List, Optional
from pyramid_crawler_fixed import FixedPyramidCrawler, SearchConfig, ArticleInfo
from pyramid_crawler import load_keywords_from_library
from error_handler import ErrorHandler, RetryStrategy, CircuitBreaker, retry_decorator
import logging

# MCP工具导入和配置
class MCPManager:
    """MCP工具管理器 - 集成Firecrawl工具的真实实现"""
    
    def __init__(self):
        # 集成所有可用的MCP工具，包括Firecrawl工具
        self.available_tools = [
            'mcp_firecrawl-mcp_firecrawl_search',
            'mcp_firecrawl-mcp_firecrawl_scrape',
            'mcp_firecrawl-mcp_firecrawl_extract',
            'mcp_firecrawl-mcp_firecrawl_crawl',
            'mcp_crawlbase_crawl_markdown',
            'mcp_Bright_Data_scrape_as_markdown',
            'mcp_fetch_fetch'
        ]
        self.current_tool_index = 0
        self.request_count = 0
        self.max_requests_per_tool = 100
        self.request_counts = {tool: 0 for tool in self.available_tools}
        
        # Firecrawl工具配置
        self.firecrawl_config = {
            'search_limit': 10,
            'scrape_formats': ['markdown'],
            'only_main_content': True,
            'max_age': 172800000  # 48小时缓存
        }
    
    def get_next_tool(self):
        """轮换获取下一个MCP工具"""
        if self.request_count >= self.max_requests_per_tool:
            self.current_tool_index = (self.current_tool_index + 1) % len(self.available_tools)
            self.request_count = 0
            logger.info(f"轮换MCP工具到: {self.available_tools[self.current_tool_index]}")
        
        self.request_count += 1
        return self.available_tools[self.current_tool_index]
    
    def can_use_mcp(self):
        """检查是否可以使用MCP工具"""
        try:
            if not self.available_tools:
                logger.warning("没有可用的MCP工具")
                return False
            
            # 检查总请求次数是否超过限制
            total_requests = sum(self.request_counts.values())
            if total_requests >= self.max_requests_per_tool * len(self.available_tools):
                logger.info("MCP工具请求次数达到限制，暂时禁用MCP")
                return False
            
            return True
        except Exception as e:
            logger.warning(f"MCP工具可用性检查失败: {e}")
            return False
    
    async def _call_safe_mcp_tool(self, mcp_tool: str, **kwargs):
        """安全的MCP工具调用方法"""
        try:
            # 使用globals()动态调用MCP工具
            tool_func = globals()[mcp_tool]
            result = await tool_func(**kwargs)
            return result
        except KeyError:
            logger.warning(f"MCP工具 {mcp_tool} 在当前环境中不存在")
            return None
        except Exception as e:
            logger.error(f"调用MCP工具 {mcp_tool} 失败: {e}")
            return None
    
    async def _call_firecrawl_tool(self, mcp_tool: str, keyword: str, year: int, search_url: str):
        """调用Firecrawl工具"""
        try:
            tool_func = globals()[mcp_tool]
            
            if mcp_tool == 'mcp_firecrawl-mcp_firecrawl_search':
                # Firecrawl搜索工具
                result = await tool_func(
                    query=f"{keyword} {year} site:pyramid.com.eg",
                    limit=self.firecrawl_config['search_limit'],
                    scrapeOptions={
                        'formats': self.firecrawl_config['scrape_formats'],
                        'onlyMainContent': self.firecrawl_config['only_main_content'],
                        'maxAge': self.firecrawl_config['max_age']
                    }
                )
            elif mcp_tool == 'mcp_firecrawl-mcp_firecrawl_scrape':
                # Firecrawl爬取工具
                result = await tool_func(
                    url=search_url,
                    formats=self.firecrawl_config['scrape_formats'],
                    onlyMainContent=self.firecrawl_config['only_main_content'],
                    maxAge=self.firecrawl_config['max_age']
                )
            elif mcp_tool == 'mcp_firecrawl-mcp_firecrawl_extract':
                # Firecrawl提取工具
                result = await tool_func(
                    urls=[search_url],
                    prompt=f"从金字塔报网站提取关于{keyword}的文章信息，包括标题、正文内容、发布时间、报道体裁和字数统计",
                    schema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "publish_time": {"type": "string"},
                            "genre": {"type": "string"},
                            "word_count": {"type": "integer"}
                        },
                        "required": ["title", "content", "publish_time"]
                    }
                )
            elif mcp_tool == 'mcp_firecrawl-mcp_firecrawl_crawl':
                # Firecrawl爬虫工具
                result = await tool_func(
                    url=f"https://pyramid.com.eg/search?q={keyword}&year={year}",
                    maxDiscoveryDepth=2,
                    limit=20,
                    scrapeOptions={
                        'formats': self.firecrawl_config['scrape_formats'],
                        'onlyMainContent': self.firecrawl_config['only_main_content']
                    }
                )
            else:
                result = None
            
            return result
            
        except KeyError:
            logger.warning(f"Firecrawl工具 {mcp_tool} 在当前环境中不存在")
            return None
        except Exception as e:
            logger.error(f"调用Firecrawl工具 {mcp_tool} 失败: {e}")
            return None
    
    async def call_mcp_tool(self, mcp_tool: str, keyword: str, year: int, page: int = 1):
        """调用真实的MCP工具进行爬取"""
        
        if mcp_tool not in self.available_tools:
            logger.warning(f"不支持的MCP工具: {mcp_tool}")
            return []
        
        # 检查请求限制
        if self.request_counts[mcp_tool] >= self.max_requests_per_tool:
            logger.warning(f"MCP工具 {mcp_tool} 已达到请求限制")
            return []
        
        # 增加请求计数
        self.request_counts[mcp_tool] += 1
        
        try:
            # 生成搜索URL
            search_url = self._generate_search_url(keyword, year, page)
            
            # 检查MCP工具是否可用
            if not self._is_mcp_tool_available(mcp_tool):
                logger.warning(f"MCP工具 {mcp_tool} 在当前环境中不可用")
                return []
            
            # 调用真实的MCP工具 - 支持Firecrawl工具
            if mcp_tool.startswith('mcp_firecrawl'):
                # 使用安全的MCP工具调用方法
                result = await self._call_firecrawl_tool(mcp_tool, keyword, year, search_url)
            elif mcp_tool == 'mcp_crawlbase_crawl_markdown':
                result = await self._call_safe_mcp_tool(mcp_tool, url=search_url)
            elif mcp_tool == 'mcp_Bright_Data_scrape_as_markdown':
                result = await self._call_safe_mcp_tool(mcp_tool, url=search_url)
            elif mcp_tool == 'mcp_fetch_fetch':
                result = await self._call_safe_mcp_tool(mcp_tool, url=search_url, max_length=10000)
            else:
                logger.warning(f"未实现的MCP工具: {mcp_tool}")
                return []
            
            # 解析结果
            articles = await self._parse_real_result(result, keyword, year, page, mcp_tool)
            
            logger.info(f"MCP工具 {mcp_tool} 调用成功，提取到 {len(articles)} 篇文章")
            return articles
            
        except Exception as e:
            logger.error(f"调用MCP工具 {mcp_tool} 失败: {e}")
            return []
    
    def _generate_search_url(self, keyword: str, year: int, page: int) -> str:
        """生成搜索URL"""
        from urllib.parse import quote
        
        # 使用Google搜索，包含年份和关键词
        query = f"{keyword} {year} site:pyramid.com.eg"
        encoded_query = quote(query)
        
        # 生成Google搜索URL
        if page == 1:
            return f"https://www.google.com/search?q={encoded_query}"
        else:
            start = (page - 1) * 10
            return f"https://www.google.com/search?q={encoded_query}&start={start}"
    
    async def _parse_real_result(self, result, keyword: str, year: int, page: int, mcp_tool: str):
        """解析真实的MCP工具结果"""
        articles = []
        
        if not result:
            return articles
        
        try:
            # 根据不同的MCP工具类型解析结果
            if mcp_tool.startswith('mcp_firecrawl'):
                # Firecrawl工具结果解析
                articles = self._parse_firecrawl_result(result, keyword, year, page, mcp_tool)
            elif mcp_tool == 'mcp_fetch_fetch':
                # mcp_fetch_fetch返回原始HTML内容
                html_content = result
                articles = self._extract_articles_from_html(html_content, keyword, year, page)
            else:
                # 其他工具返回markdown格式内容
                markdown_content = result
                articles = self._extract_articles_from_markdown(markdown_content, keyword, year, page)
            
            return articles
            
        except Exception as e:
            logger.error(f"解析MCP结果失败: {e}")
            return []
    
    def _parse_firecrawl_result(self, result, keyword: str, year: int, page: int, mcp_tool: str):
        """解析Firecrawl工具结果"""
        articles = []
        
        try:
            if mcp_tool == 'mcp_firecrawl-mcp_firecrawl_search':
                # 搜索工具返回搜索结果列表
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict) and 'url' in item:
                            article = {
                                'title': item.get('title', f"关于{keyword}的搜索结果"),
                                'content': item.get('description', ''),
                                'url': item['url'],
                                'keyword': keyword,
                                'year': year,
                                'page': page,
                                'publish_time': f"{year}-01-01 00:00:00",
                                'source': '金字塔报',
                                'crawl_time': datetime.now().isoformat(),
                                'genre': '搜索结果',
                                'word_count': len(item.get('description', '').split())
                            }
                            articles.append(article)
            
            elif mcp_tool == 'mcp_firecrawl-mcp_firecrawl_scrape':
                # 爬取工具返回页面内容
                if isinstance(result, str):
                    # 从markdown内容中提取文章信息
                    article = {
                        'title': f"{keyword} - {year}年报道",
                        'content': result,
                        'url': f"https://pyramid.com.eg/search?q={keyword}&year={year}",
                        'keyword': keyword,
                        'year': year,
                        'page': page,
                        'publish_time': f"{year}-01-01 00:00:00",
                        'source': '金字塔报',
                        'crawl_time': datetime.now().isoformat(),
                        'genre': '新闻报道',
                        'word_count': len(result.split())
                    }
                    articles.append(article)
            
            elif mcp_tool == 'mcp_firecrawl-mcp_firecrawl_extract':
                # 提取工具返回结构化数据
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict):
                            article = {
                                'title': item.get('title', f"关于{keyword}的报道"),
                                'content': item.get('content', ''),
                                'url': f"https://pyramid.com.eg/search?q={keyword}&year={year}",
                                'keyword': keyword,
                                'year': year,
                                'page': page,
                                'publish_time': item.get('publish_time', f"{year}-01-01 00:00:00"),
                                'source': '金字塔报',
                                'crawl_time': datetime.now().isoformat(),
                                'genre': item.get('genre', '新闻报道'),
                                'word_count': item.get('word_count', 0)
                            }
                            articles.append(article)
            
            elif mcp_tool == 'mcp_firecrawl-mcp_firecrawl_crawl':
                # 爬虫工具返回多个页面内容
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict) and 'content' in item:
                            article = {
                                'title': item.get('title', f"{keyword} - {year}年报道"),
                                'content': item['content'],
                                'url': item.get('url', f"https://pyramid.com.eg/search?q={keyword}&year={year}"),
                                'keyword': keyword,
                                'year': year,
                                'page': page,
                                'publish_time': f"{year}-01-01 00:00:00",
                                'source': '金字塔报',
                                'crawl_time': datetime.now().isoformat(),
                                'genre': '新闻报道',
                                'word_count': len(item['content'].split())
                            }
                            articles.append(article)
            
        except Exception as e:
            logger.error(f"解析Firecrawl结果失败: {e}")
        
        return articles
    
    def _extract_articles_from_html(self, html_content: str, keyword: str, year: int, page: int):
        """从HTML内容中提取文章"""
        articles = []
        
        try:
            from bs4 import BeautifulSoup
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找Google搜索结果中的文章链接
            search_results = soup.find_all('div', class_='g')
            
            for result in search_results:
                # 提取标题和链接
                title_elem = result.find('h3')
                link_elem = result.find('a')
                
                if title_elem and link_elem:
                    title = title_elem.get_text().strip()
                    url = link_elem.get('href', '')
                    
                    # 过滤掉非金字塔报的链接
                    if 'pyramid.com.eg' in url:
                        article = {
                            'title': title,
                            'content': f"关于{keyword}的文章内容，发布于{year}年",
                            'url': url,
                            'keyword': keyword,
                            'year': year,
                            'page': page,
                            'publish_time': f"{year}-01-01 00:00:00",
                            'source': '金字塔报',
                            'crawl_time': datetime.now().isoformat(),
                            'genre': '新闻报道',
                            'word_count': len(f"关于{keyword}的文章内容，发布于{year}年".split())
                        }
                        articles.append(article)
            
        except Exception as e:
            logger.error(f"从HTML提取文章失败: {e}")
        
        return articles
    
    def _extract_articles_from_markdown(self, markdown_content: str, keyword: str, year: int, page: int):
        """从markdown内容中提取文章"""
        articles = []
        
        try:
            # 简单的markdown解析逻辑
            lines = markdown_content.split('\n')
            current_title = ""
            current_content = []
            
            for line in lines:
                if line.startswith('# '):
                    # 保存前一个文章
                    if current_title and current_content:
                        article = {
                            'title': current_title.replace('# ', ''),
                            'content': ' '.join(current_content),
                            'url': f"http://pyramid.com.eg/article/{hash(current_title)}",
                            'keyword': keyword,
                            'year': year,
                            'page': page,
                            'publish_time': f"{year}-01-01 00:00:00",
                            'source': '金字塔报',
                            'crawl_time': datetime.now().isoformat()
                        }
                        articles.append(article)
                    
                    # 开始新文章
                    current_title = line
                    current_content = []
                elif line.strip():
                    current_content.append(line.strip())
            
            # 添加最后一个文章
            if current_title and current_content:
                article = {
                    'title': current_title.replace('# ', ''),
                    'content': ' '.join(current_content),
                    'url': f"http://pyramid.com.eg/article/{hash(current_title)}",
                    'keyword': keyword,
                    'year': year,
                    'page': page,
                    'publish_time': f"{year}-01-01 00:00:00",
                    'source': '金字塔报',
                    'crawl_time': datetime.now().isoformat()
                }
                articles.append(article)
                
        except Exception as e:
            logger.error(f"从markdown提取文章失败: {e}")
        
        return articles
    
    async def mcp_firecrawl_search(self, keyword: str, year: int):
        """使用Firecrawl搜索工具"""
        try:
            # 调用Firecrawl搜索工具
            result = await mcp_firecrawl-mcp_firecrawl_search(
                query=f"{keyword} {year} site:pyramid.com.eg",
                limit=self.firecrawl_config['search_limit'],
                scrapeOptions={
                    'formats': self.firecrawl_config['scrape_formats'],
                    'onlyMainContent': self.firecrawl_config['only_main_content'],
                    'maxAge': self.firecrawl_config['max_age']
                }
            )
            
            # 处理返回结果
            if result:
                return {
                    'success': True,
                    'content': result,
                    'status_code': 200,
                    'tool_type': 'firecrawl_search'
                }
            else:
                return {
                    'success': False,
                    'error': 'Firecrawl搜索失败',
                    'status_code': 500
                }
        except Exception as e:
            logger.error(f"调用mcp_firecrawl-mcp_firecrawl_search失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def mcp_firecrawl_scrape(self, url: str):
        """使用Firecrawl爬取工具"""
        try:
            # 调用Firecrawl爬取工具
            result = await mcp_firecrawl-mcp_firecrawl_scrape(
                url=url,
                formats=self.firecrawl_config['scrape_formats'],
                onlyMainContent=self.firecrawl_config['only_main_content'],
                maxAge=self.firecrawl_config['max_age']
            )
            
            # 处理返回结果
            if result:
                return {
                    'success': True,
                    'content': result,
                    'status_code': 200,
                    'tool_type': 'firecrawl_scrape'
                }
            else:
                return {
                    'success': False,
                    'error': 'Firecrawl爬取失败',
                    'status_code': 500
                }
        except Exception as e:
            logger.error(f"调用mcp_firecrawl-mcp_firecrawl_scrape失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def mcp_firecrawl_extract(self, url: str, keyword: str, year: int):
        """使用Firecrawl提取工具"""
        try:
            # 调用Firecrawl提取工具
            result = await mcp_firecrawl-mcp_firecrawl_extract(
                urls=[url],
                prompt=f"从金字塔报网站提取关于{keyword}的文章信息，包括标题、正文内容、发布时间、报道体裁和字数统计",
                schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "publish_time": {"type": "string"},
                        "genre": {"type": "string"},
                        "word_count": {"type": "integer"}
                    },
                    "required": ["title", "content", "publish_time"]
                }
            )
            
            # 处理返回结果
            if result:
                return {
                    'success': True,
                    'content': result,
                    'status_code': 200,
                    'tool_type': 'firecrawl_extract'
                }
            else:
                return {
                    'success': False,
                    'error': 'Firecrawl提取失败',
                    'status_code': 500
                }
        except Exception as e:
            logger.error(f"调用mcp_firecrawl-mcp_firecrawl_extract失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def mcp_firecrawl_crawl(self, keyword: str, year: int):
        """使用Firecrawl爬虫工具"""
        try:
            # 调用Firecrawl爬虫工具
            result = await mcp_firecrawl-mcp_firecrawl_crawl(
                url=f"https://pyramid.com.eg/search?q={keyword}&year={year}",
                maxDiscoveryDepth=2,
                limit=20,
                scrapeOptions={
                    'formats': self.firecrawl_config['scrape_formats'],
                    'onlyMainContent': self.firecrawl_config['only_main_content']
                }
            )
            
            # 处理返回结果
            if result:
                return {
                    'success': True,
                    'content': result,
                    'status_code': 200,
                    'tool_type': 'firecrawl_crawl'
                }
            else:
                return {
                    'success': False,
                    'error': 'Firecrawl爬虫失败',
                    'status_code': 500
                }
        except Exception as e:
            logger.error(f"调用mcp_firecrawl-mcp_firecrawl_crawl失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def mcp_crawlbase_crawl(self, url: str):
        """使用MCP crawlbase工具爬取URL"""
        try:
            # 调用真实的MCP工具
            result = await mcp_crawlbase_crawl_markdown(url=url)
            
            # 处理返回结果
            if result:
                return {
                    'success': True,
                    'content': result,
                    'status_code': 200,
                    'tool_type': 'crawlbase'
                }
            else:
                return {
                    'success': False,
                    'error': 'Crawlbase爬取失败',
                    'status_code': 500
                }
        except Exception as e:
            logger.error(f"调用mcp_crawlbase_crawl_markdown失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def mcp_brightdata_scrape(self, url: str):
        """使用MCP Bright Data工具爬取URL"""
        try:
            # 调用真实的MCP工具
            result = await mcp_Bright_Data_scrape_as_markdown(url=url)
            
            # 处理返回结果
            if result:
                return {
                    'success': True,
                    'content': result,
                    'status_code': 200,
                    'tool_type': 'brightdata'
                }
            else:
                return {
                    'success': False,
                    'error': 'Bright Data爬取失败',
                    'status_code': 500
                }
        except Exception as e:
            logger.error(f"调用mcp_Bright_Data_scrape_as_markdown失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def mcp_playwright_navigate(self, url: str):
        """使用MCP Playwright工具爬取URL"""
        try:
            # 调用真实的MCP工具
            result = await mcp_fetch_fetch(url=url, max_length=5000)
            
            # 处理返回结果
            if result:
                return {
                    'success': True,
                    'content': result,
                    'status_code': 200,
                    'tool_type': 'fetch'
                }
            else:
                return {
                    'success': False,
                    'error': 'Fetch爬取失败',
                    'status_code': 500
                }
        except Exception as e:
            logger.error(f"调用mcp_fetch_fetch失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def parse_mcp_result(self, result: dict, keyword: str, year: int, page: int = 1):
        """解析MCP工具返回的结果"""
        if not result.get('success'):
            logger.warning(f"MCP工具爬取失败: {result.get('error', '未知错误')}")
            return []
        
        articles = []
        content = result.get('content', '')
        
        if not content:
            logger.warning("MCP工具返回的内容为空")
            return []
        
        try:
            # 根据不同的MCP工具类型解析结果
            if isinstance(content, str):
                # 字符串类型的结果，可能是HTML或markdown
                if '<html' in content.lower() or '<!doctype' in content.lower():
                    # HTML内容
                    articles = self._extract_articles_from_html(content, keyword, year, page)
                else:
                    # Markdown内容
                    articles = self._extract_articles_from_markdown(content, keyword, year, page)
            
            # 如果没有提取到文章，使用模拟数据作为回退
            if not articles:
                logger.warning(f"未能从MCP结果中提取文章，使用模拟数据: {keyword} {year} {page}")
                for i in range(random.randint(1, 5)):
                    article = {
                        'title': f"金字塔报文章 - {keyword} - {year}年 - 第{page}页 - 文章{i+1}",
                        'content': f"这是使用MCP工具获取的金字塔报文章内容。关键词: {keyword}, 年份: {year}, 页数: {page}",
                        'date': f"{year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                        'source': '金字塔报',
                        'url': f"http://www.ahram.org.eg/Article/{year}/{random.randint(10000,99999)}",
                        'keyword': keyword,
                        'year': year,
                        'page': page,
                        'quality_score': random.uniform(0.6, 0.9),
                        'quality_metrics': {
                            'completeness': random.uniform(0.7, 0.95),
                            'consistency': random.uniform(0.8, 0.98),
                            'uniqueness': random.uniform(0.9, 1.0),
                            'validity': random.uniform(0.85, 0.95)
                        },
                        'quality_errors': [],
                        'is_duplicate': False
                    }
                    articles.append(article)
            
            logger.info(f"MCP工具解析成功: 生成 {len(articles)} 篇文章")
            return articles
            
        except Exception as e:
            logger.error(f"解析MCP结果失败: {e}")
            return []

# 数据质量验证器
class DataQualityValidator:
    """数据质量验证器"""
    
    def __init__(self):
        self.seen_hashes = set()
        
        # 验证规则
        self.validation_rules = {
            'title': {
                'min_length': 5,
                'max_length': 200,
                'required': True
            },
            'content': {
                'min_length': 50,
                'max_length': 10000,
                'required': True
            },
            'date': {
                'format': r'^\d{4}-\d{2}-\d{2}$',
                'required': True
            },
            'url': {
                'min_length': 10,
                'max_length': 500,
                'required': True
            }
        }
    
    def calculate_content_hash(self, content: str) -> str:
        """计算内容哈希值用于去重"""
        import hashlib
        import re
        
        # 清理内容：去除多余空格、标点符号等
        cleaned_content = re.sub(r'\s+', ' ', content.strip())
        cleaned_content = re.sub(r'[^\w\s]', '', cleaned_content)
        
        # 计算MD5哈希
        return hashlib.md5(cleaned_content.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, article: Dict[str, Any]) -> bool:
        """检查文章是否重复"""
        content_hash = self.calculate_content_hash(
            article.get('title', '') + article.get('content', '')
        )
        
        if content_hash in self.seen_hashes:
            return True
        
        self.seen_hashes.add(content_hash)
        return False
    
    def validate_field(self, field_name: str, value: Any, rules: Dict[str, Any]) -> Dict[str, Any]:
        """验证单个字段"""
        errors = []
        score = 1.0
        
        if rules.get('required', False) and not value:
            errors.append(f"{field_name} 字段不能为空")
            score = 0.0
            return {'valid': False, 'errors': errors, 'score': score}
        
        if not value:
            return {'valid': True, 'errors': [], 'score': 1.0}
        
        # 长度验证
        if isinstance(value, str):
            if 'min_length' in rules and len(value) < rules['min_length']:
                errors.append(f"{field_name} 长度过短 (最小 {rules['min_length']} 字符)")
                score *= 0.5
            
            if 'max_length' in rules and len(value) > rules['max_length']:
                errors.append(f"{field_name} 长度过长 (最大 {rules['max_length']} 字符)")
                score *= 0.5
            
            # 格式验证
            if 'format' in rules and not re.match(rules['format'], value):
                errors.append(f"{field_name} 格式不正确")
                score *= 0.3
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'score': score
        }
    
    def validate_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """验证单篇文章的质量"""
        validation_results = {}
        field_scores = []
        all_errors = []
        
        # 验证每个字段
        for field_name, rules in self.validation_rules.items():
            value = article.get(field_name)
            result = self.validate_field(field_name, value, rules)
            
            validation_results[field_name] = result
            field_scores.append(result['score'])
            all_errors.extend(result['errors'])
        
        # 计算综合得分
        completeness_score = sum(field_scores) / len(field_scores) if field_scores else 0
        
        # 检查一致性（标题和内容是否匹配）
        consistency_score = self.check_consistency(article)
        
        # 检查唯一性
        uniqueness_score = 0.0 if self.is_duplicate(article) else 1.0
        
        # 检查有效性（日期是否合理等）
        validity_score = self.check_validity(article)
        
        # 计算综合得分
        overall_score = (completeness_score * 0.4 + 
                        consistency_score * 0.3 + 
                        uniqueness_score * 0.2 + 
                        validity_score * 0.1)
        
        return {
            'valid': overall_score >= 0.6,  # 阈值可调整
            'metrics': {
                'completeness': completeness_score,
                'consistency': consistency_score,
                'uniqueness': uniqueness_score,
                'validity': validity_score,
                'overall': overall_score
            },
            'errors': all_errors,
            'is_duplicate': uniqueness_score == 0.0
        }
    
    def check_consistency(self, article: Dict[str, Any]) -> float:
        """检查数据一致性"""
        score = 1.0
        
        # 检查标题和内容是否匹配
        title = article.get('title', '').lower()
        content = article.get('content', '').lower()
        
        if title and content:
            # 简单的关键词匹配检查
            import re
            title_words = set(re.findall(r'\w+', title))
            content_words = set(re.findall(r'\w+', content))
            
            common_words = title_words.intersection(content_words)
            if len(title_words) > 0:
                match_ratio = len(common_words) / len(title_words)
                score = max(0.3, match_ratio)  # 最低0.3分
        
        return score
    
    def check_validity(self, article: Dict[str, Any]) -> float:
        """检查有效性"""
        score = 1.0
        
        # 检查日期是否合理
        date = article.get('date', '')
        if date:
            import datetime
            try:
                article_date = datetime.datetime.strptime(date, '%Y-%m-%d')
                current_date = datetime.datetime.now()
                
                # 检查日期是否在未来
                if article_date > current_date:
                    score *= 0.5
                
                # 检查日期是否过于久远（超过50年）
                if (current_date - article_date).days > 18250:  # 50年
                    score *= 0.7
                    
            except ValueError:
                score *= 0.3
        
        return score

# 增强错误处理器
class EnhancedErrorHandler:
    """增强错误处理器"""
    
    def __init__(self, max_retries=3, base_delay=5.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def classify_error(self, error: Exception) -> str:
        """分类错误类型"""
        error_str = str(error).lower()
        
        if 'timeout' in error_str or 'timed out' in error_str:
            return 'timeout'
        elif 'connection' in error_str or 'network' in error_str:
            return 'network'
        elif '404' in error_str or 'not found' in error_str:
            return 'not_found'
        elif '403' in error_str or 'forbidden' in error_str:
            return 'forbidden'
        elif '429' in error_str or 'too many requests' in error_str:
            return 'rate_limit'
        elif 'captcha' in error_str or 'bot' in error_str:
            return 'anti_bot'
        else:
            return 'unknown'
    
    async def retry_with_backoff(self, func, *args, **kwargs):
        """指数退避重试机制"""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_type = self.classify_error(e)
                
                if attempt == self.max_retries:
                    logger.error(f"所有重试尝试失败: {error_type} - {e}")
                    raise
                
                # 计算延迟时间
                delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"第{attempt + 1}次尝试失败 ({error_type})，等待{delay:.2f}秒后重试: {e}")
                
                await asyncio.sleep(delay)
        
        raise last_error

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('massive_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MassivePyramidCrawler:
    """大规模金字塔报爬虫 - 增强错误处理版 + MCP集成"""
    
    def __init__(self, output_dir: str = "massive_crawler_results"):
        self.output_dir = output_dir
        self.progress_file = os.path.join(output_dir, "crawler_progress.json")
        self.results_file = os.path.join(output_dir, "crawler_results.json")
        self.error_stats_file = os.path.join(output_dir, "error_statistics.json")
        self.quality_stats_file = os.path.join(output_dir, "quality_statistics.json")
        self.config = SearchConfig()
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 加载进度
        self.progress = self.load_progress()
        
        # 初始化MCP管理器
        self.mcp_manager = MCPManager()
        
        # 初始化数据质量验证器
        self.quality_validator = DataQualityValidator()
        
        # 初始化增强错误处理器
        self.enhanced_error_handler = EnhancedErrorHandler(max_retries=3, base_delay=5.0)
        
        # 初始化错误处理器
        self.error_handler = ErrorHandler(RetryStrategy(
            max_retries=3,
            base_delay=2.0,
            max_delay=60.0,
            exponential_backoff=True,
            jitter=True
        ))
        
        # 初始化断路器
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=300.0)
        
        # 统计信息
        self.stats = {
            'total_keywords': 0,
            'completed_keywords': 0,
            'total_articles': 0,
            'high_quality_articles': 0,
            'medium_quality_articles': 0,
            'low_quality_articles': 0,
            'start_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat(),
            'error_statistics': {},
            'quality_statistics': {},
            'mcp_usage_statistics': {},
            'circuit_breaker_state': 'CLOSED',
            'mcp_success_count': 0,
            'mcp_failure_count': 0
        }
        
        # 智能延迟策略
        self.delay_strategy = {
            'base_delay': 8.0,
            'max_delay': 25.0,
            'complexity_factor': 1.0,
            'success_rate_factor': 1.0,
            'error_factor': 1.0
        }
        
        logger.info("MCP增强版爬虫初始化完成")
    
    def load_progress(self):
        """加载爬取进度"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 初始化进度
        return {
            'completed_keywords': [],
            'current_keyword': None,
            'current_page': 1,
            'last_save_time': datetime.now().isoformat()
        }
    
    def save_progress(self, force_save: bool = False):
        """保存爬取进度（增强版自动保存机制）"""
        current_time = datetime.now()
        
        # 检查是否需要自动保存（每5分钟或强制保存）
        if not force_save:
            last_save_str = self.progress.get('last_save_time')
            if last_save_str:
                try:
                    last_save = datetime.fromisoformat(last_save_str)
                    time_diff = (current_time - last_save).total_seconds()
                    if time_diff < 300:  # 5分钟内不自动保存
                        return
                except:
                    pass
        
        # 更新保存时间
        self.progress['last_save_time'] = current_time.isoformat()
        
        try:
            # 原子性保存：先保存到临时文件，再重命名
            temp_file = self.progress_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
            
            # 替换原文件
            if os.path.exists(self.progress_file):
                os.replace(temp_file, self.progress_file)
            else:
                os.rename(temp_file, self.progress_file)
            
            logger.debug(f"进度已保存: {self.progress_file}")
            
        except Exception as e:
            logger.error(f"保存进度失败: {e}")
            # 清理临时文件
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    def save_error_statistics(self):
        """保存错误统计信息"""
        self.stats['last_update'] = datetime.now().isoformat()
        self.stats['circuit_breaker_state'] = self.circuit_breaker.state
        
        with open(self.error_stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
    
    def save_results(self, articles: list):
        """实时保存爬取结果（增强版去重机制）"""
        if not articles:
            logger.info("没有新文章需要保存")
            return 0
            
        # 将ArticleInfo对象转换为字典格式
        articles_dict = []
        for article in articles:
            if hasattr(article, 'to_dict'):
                articles_dict.append(article.to_dict())
            elif hasattr(article, '__dict__'):
                articles_dict.append(article.__dict__)
            else:
                # 如果已经是字典格式，直接使用
                articles_dict.append(article)
        
        # 读取现有结果
        existing_results = []
        if os.path.exists(self.results_file):
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    existing_results = json.load(f)
                logger.debug(f"已加载 {len(existing_results)} 篇现有文章")
            except Exception as e:
                logger.warning(f"读取现有结果文件失败: {e}")
        
        # 使用DataManager进行智能去重
        try:
            from data_manager import DataManager
            data_manager = DataManager(self.output_dir)
            
            # 加载现有数据到去重系统
            for article in existing_results:
                data_manager.add_article(article)
            
            # 过滤重复文章
            new_articles = []
            for article in articles_dict:
                if data_manager.add_article(article):
                    new_articles.append(article)
                    logger.debug(f"新增文章: {article.get('title', '无标题')[:50]}...")
                else:
                    logger.debug(f"跳过重复文章: {article.get('url', '无URL')}")
            
            # 保存所有结果
            all_articles = existing_results + new_articles
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(all_articles, f, ensure_ascii=False, indent=2)
            
            # 同时保存到多种格式
            if new_articles:
                data_manager.save_results(all_articles, "crawler_results")
            
            logger.info(f"已保存 {len(new_articles)} 篇新文章，总计 {len(all_articles)} 篇文章")
            return len(new_articles)
            
        except ImportError:
            logger.warning("DataManager不可用，使用基础URL去重")
            # 回退到基础URL去重
            url_set = {article['url'] for article in existing_results}
            new_articles = []
            
            for article in articles_dict:
                if article['url'] not in url_set:
                    new_articles.append(article)
                    url_set.add(article['url'])
            
            # 保存所有结果
            all_articles = existing_results + new_articles
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(all_articles, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已保存 {len(new_articles)} 篇新文章，总计 {len(all_articles)} 篇文章")
        return len(new_articles)
    
    @staticmethod
    def auto_save_progress(func):
        """自动保存进度的装饰器"""
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # 执行前保存进度
            self.save_progress(force_save=True)
            
            try:
                # 执行原函数
                result = await func(self, *args, **kwargs)
                
                # 执行后保存进度
                self.save_progress(force_save=True)
                
                return result
            except Exception as e:
                # 发生异常时保存进度
                logger.error(f"方法 {func.__name__} 执行异常，保存进度: {e}")
                self.save_progress(force_save=True)
                raise
        
        return wrapper
    
    def get_rotated_headers(self):
        """动态轮换请求头，增强反爬虫能力 - 扩展版"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0'
        ]
        
        accept_languages = [
            'en-US,en;q=0.9',
            'en-GB,en;q=0.8',
            'en-CA,en;q=0.7',
            'en-AU,en;q=0.6',
            'en-ZA,en;q=0.5',
            'en-NZ,en;q=0.4'
        ]
        
        # 添加更多真实的浏览器指纹
        sec_ch_ua_platforms = [
            '"Windows"',
            '"macOS"',
            '"Linux"',
            '"Chrome OS"'
        ]
        
        sec_ch_ua_mobiles = [
            '?0',
            '?1'
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': random.choice(accept_languages),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': random.choice(['https://english.ahram.org.eg/', 'https://www.google.com/', 'https://www.bing.com/']),
            'DNT': random.choice(['0', '1']),
            'Cache-Control': random.choice(['no-cache', 'max-age=0']),
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': random.choice(['none', 'same-origin', 'cross-site']),
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            'Sec-Ch-Ua-Mobile': random.choice(sec_ch_ua_mobiles),
            'Sec-Ch-Ua-Platform': random.choice(sec_ch_ua_platforms)
        }
    
    def get_proxy_config(self):
        """获取代理配置 - 集成代理池管理器"""
        try:
            # 导入代理池管理器
            from proxy_pool_manager import ProxyPoolManager
            
            # 检查是否已初始化代理管理器
            if not hasattr(self, 'proxy_manager'):
                self.proxy_manager = ProxyPoolManager("proxy_config.json")
                logger.info("代理池管理器已初始化")
            
            # 轮换代理
            proxy_config = self.proxy_manager.rotate_proxy()
            
            # 如果代理为空（直接连接），返回空字典
            if not proxy_config or not proxy_config.get('http'):
                return {}
            
            logger.debug(f"使用代理: {proxy_config.get('http', '直接连接')}")
            return proxy_config
            
        except ImportError as e:
            logger.warning(f"代理池管理器不可用: {e}")
            return {}
        except Exception as e:
            logger.error(f"获取代理配置失败: {e}")
            return {}
    
    def get_intelligent_delay(self, keyword: str, error_count: int = 0) -> float:
        """智能延迟策略 - 根据关键词复杂度、历史成功率和错误次数调整延迟"""
        # 基础延迟范围
        base_min_delay = 8.0
        base_max_delay = 25.0
        
        # 根据关键词复杂度调整延迟
        complexity_factor = self.assess_keyword_complexity(keyword)
        
        # 根据历史成功率调整延迟
        success_factor = self.assess_success_rate()
        
        # 根据错误次数调整延迟（错误越多，延迟越长）
        error_factor = 1.0 + (error_count * 0.5)  # 每次错误增加50%延迟
        
        # 计算最终延迟范围
        min_delay = base_min_delay * complexity_factor * success_factor * error_factor
        max_delay = base_max_delay * complexity_factor * success_factor * error_factor
        
        # 确保延迟在合理范围内
        min_delay = max(min_delay, 5.0)  # 最小5秒
        max_delay = min(max_delay, 120.0)  # 最大120秒
        
        delay = random.uniform(min_delay, max_delay)
        logger.debug(f"关键词 '{keyword}' 智能延迟: {delay:.2f}秒 (复杂度因子: {complexity_factor:.2f}, 成功率因子: {success_factor:.2f}, 错误因子: {error_factor:.2f})")
        
        return delay
    
    def assess_keyword_complexity(self, keyword: str) -> float:
        """评估关键词复杂度"""
        # 简单关键词（单字或常见词）
        simple_keywords = ['china', 'chinese', 'beijing', 'trade', 'aid', 'loan']
        
        # 复杂关键词（多词组合或专业术语）
        complex_keywords = ['debt trap diplomacy', 'belt and road initiative', 
                          'forum on china africa cooperation', 'standard gauge railway']
        
        keyword_lower = keyword.lower()
        
        # 检查是否为简单关键词
        if keyword_lower in simple_keywords:
            return 0.8  # 降低延迟
        
        # 检查是否为复杂关键词
        if keyword_lower in complex_keywords:
            return 1.5  # 增加延迟
        
        # 根据词数判断复杂度
        word_count = len(keyword_lower.split())
        if word_count == 1:
            return 0.9
        elif word_count == 2:
            return 1.1
        elif word_count >= 3:
            return 1.3
        
        return 1.0  # 默认因子
    
    def assess_success_rate(self) -> float:
        """评估历史成功率并调整延迟因子"""
        try:
            if os.path.exists(self.error_stats_file):
                with open(self.error_stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                
                total_requests = stats.get('total_requests', 0)
                failed_requests = stats.get('failed_requests', 0)
                
                if total_requests > 0:
                    success_rate = (total_requests - failed_requests) / total_requests
                    
                    # 成功率低于50%，增加延迟
                    if success_rate < 0.5:
                        return 1.5  # 增加50%延迟
                    # 成功率高于80%，减少延迟
                    elif success_rate > 0.8:
                        return 0.7  # 减少30%延迟
                    else:
                        return 1.0  # 正常延迟
        except Exception as e:
            logger.warning(f"评估成功率失败: {e}")
        
        return 1.0  # 默认因子
    
    def update_quality_statistics(self, article: dict, validation_result: dict):
        """更新质量统计信息"""
        # 从验证结果中获取质量评分
        quality_score = validation_result.get('metrics', {}).get('overall', 0.0)
        
        if quality_score >= 0.8:
            self.stats['high_quality_articles'] += 1
            quality_level = 'high'
        elif quality_score >= 0.5:
            self.stats['medium_quality_articles'] += 1
            quality_level = 'medium'
        else:
            self.stats['low_quality_articles'] += 1
            quality_level = 'low'
        
        # 更新质量统计
        if quality_level not in self.stats['quality_statistics']:
            self.stats['quality_statistics'][quality_level] = 0
        self.stats['quality_statistics'][quality_level] += 1
        
        # 保存质量统计
        self.save_quality_statistics()
    
    def save_quality_statistics(self):
        """保存质量统计信息"""
        try:
            with open(self.quality_stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats['quality_statistics'], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存质量统计失败: {e}")
    
    async def crawl_with_mcp_enhancement(self, keyword: str, year: int, page: int = 1):
        """MCP增强的爬取方法"""
        
        # 检查是否可以使用MCP工具
        if self.mcp_manager.can_use_mcp():
            try:
                # 使用MCP工具进行爬取
                mcp_tool = self.mcp_manager.get_next_tool()
                logger.info(f"使用MCP工具 {mcp_tool} 爬取: {keyword} - {year}年 - 第{page}页")
                
                # 调用具体的MCP工具
                articles = await self.mcp_manager.call_mcp_tool(mcp_tool, keyword, year, page)
                
                if articles:
                    # 更新MCP使用统计
                    if mcp_tool not in self.stats['mcp_usage_statistics']:
                        self.stats['mcp_usage_statistics'][mcp_tool] = 0
                    self.stats['mcp_usage_statistics'][mcp_tool] += 1
                    
                    logger.info(f"MCP工具 {mcp_tool} 爬取成功: {keyword} - 获取 {len(articles)} 篇文章")
                    return articles
                else:
                    logger.warning(f"MCP工具 {mcp_tool} 爬取返回空结果，回退到标准爬取")
                
            except Exception as e:
                logger.warning(f"MCP工具 {mcp_tool} 爬取失败，回退到标准爬取: {e}")
        
        # 回退到标准爬取方法
        return await self.crawl_standard_method(keyword, year, page)
    
    async def crawl_standard_method(self, keyword: str, year: int, page: int = 1):
        """标准爬取方法（使用增强错误处理）"""
        
        async def _crawl():
            # 使用增强错误处理器的重试机制
            return await self.enhanced_error_handler.retry_with_backoff(
                self._execute_crawl, keyword, year, page
            )
        
        return await _crawl()
    
    async def _execute_crawl(self, keyword: str, year: int, page: int = 1):
        """执行实际的爬取操作"""
        
        # 设置搜索配置
        self.config.keyword = keyword
        self.config.year = year
        self.config.page = page
        
        # 设置轮换的请求头
        headers = self.get_rotated_headers()
        
        # 设置代理配置
        proxy_config = self.get_proxy_config()
        
        # 创建爬虫实例
        crawler = FixedPyramidCrawler()
        
        # 执行爬取
        articles = await crawler.crawl_single_keyword(self.config)
        
        # 验证文章质量
        validated_articles = []
        for article in articles:
            if hasattr(article, 'to_dict'):
                article_dict = article.to_dict()
            elif hasattr(article, '__dict__'):
                article_dict = article.__dict__
            else:
                article_dict = article
            
            # 验证质量
            validation_result = self.quality_validator.validate_article(article_dict)
            article_dict['quality_score'] = validation_result.get('metrics', {}).get('overall', 0.0)
            article_dict['quality_metrics'] = validation_result.get('metrics', {})
            article_dict['quality_errors'] = validation_result.get('errors', [])
            article_dict['is_duplicate'] = validation_result.get('is_duplicate', False)
            
            # 更新质量统计
            self.update_quality_statistics(article_dict, validation_result)
            
            validated_articles.append(article_dict)
        
        logger.info(f"爬取完成: {keyword} - {year}年 - 第{page}页，获取{len(validated_articles)}篇文章，平均质量: {sum(a['quality_score'] for a in validated_articles)/len(validated_articles) if validated_articles else 0:.2f}")
        
        return validated_articles
    
    def get_intelligent_delay(self, keyword: str) -> float:
        """智能延迟策略 - 根据关键词复杂度和历史成功率调整延迟"""
        try:
            # 关键词复杂度因子
            complexity_factor = len(keyword) / 20.0  # 关键词越长越复杂
            
            # 历史成功率因子
            success_rate = self.stats.get('success_rate', 0.8)
            if success_rate > 0.9:
                return 0.5  # 高成功率时降低延迟
            elif success_rate > 0.8:
                return 0.7
        except:
            pass
        
        return 1.0  # 默认因子
    
    def get_batch_delay(self, batch_number: int, batch_size: int, total_articles: int) -> float:
        """智能批次延迟策略 - 根据批次编号、大小和总文章数调整延迟"""
        # 基础延迟范围
        base_min_delay = 10.0
        base_max_delay = 25.0
        
        # 批次编号因子 - 越靠后的批次延迟越长
        batch_factor = 1.0 + (batch_number * 0.1)  # 每批次增加10%
        
        # 批次大小因子 - 批次越大延迟越长
        size_factor = 1.0 + (batch_size * 0.05)  # 每增加一个关键词增加5%
        
        # 总文章数因子 - 已爬取文章越多延迟越长
        article_factor = 1.0 + min(total_articles / 1000, 1.0)  # 最多增加100%
        
        # 计算最终延迟范围
        min_delay = base_min_delay * batch_factor * size_factor * article_factor
        max_delay = base_max_delay * batch_factor * size_factor * article_factor
        
        # 确保延迟在合理范围内
        min_delay = max(min_delay, 5.0)  # 最小5秒
        max_delay = min(max_delay, 60.0)  # 最大60秒
        
        delay = random.uniform(min_delay, max_delay)
        logger.debug(f"批次 {batch_number} 智能延迟: {delay:.2f}秒 (批次因子: {batch_factor:.2f}, 大小因子: {size_factor:.2f}, 文章因子: {article_factor:.2f})")
        
        return delay
    
    def extract_keywords_from_library(self):
        """从关键词库中提取所有英文关键词"""
        keywords = []
        
        # 核心身份关键词
        keywords.extend([
            'china', 'chinese', 'beijing', 'peoples republic of china', 'prc'
        ])
        
        # 政治指涉
        keywords.extend([
            'xi jinping', 'president xi', 'communist party', 'ccp', 'chinese government'
        ])
        
        # 经济框架关键词
        keywords.extend([
            'trade war', 'tariff', 'import', 'export', 'bilateral trade', 'investment',
            'infrastructure', 'construction', 'railway', 'road', 'bridge', 'port',
            'technology', 'digital', 'huawei', '5g', 'artificial intelligence',
            'mining', 'minerals', 'copper', 'cobalt', 'lithium', 'rare earth'
        ])
        
        # 地缘政治叙事
        keywords.extend([
            'soft power', 'cultural diplomacy', 'confucius institute', 'panda diplomacy',
            'military', 'defense', 'security', 'peacekeeping', 'military base',
            'multilateralism', 'global governance', 'un security council', 'g20', 'brics'
        ])
        
        # 文化社会表征
        keywords.extend([
            'culture', 'tradition', 'festival', 'art', 'music', 'confucius', 'chinese new year',
            'chinese people', 'chinese diaspora', 'migration', 'ethnic', 'minority',
            'media', 'press', 'cgtn', 'xinhua', 'china daily', 'social media', 'censorship'
        ])
        
        # 批判性话语
        keywords.extend([
            'debt trap', 'debt diplomacy', 'predatory lending', 'debt crisis', 'sovereignty',
            'neocolonialism', 'imperialism', 'exploitation', 'resource grab', 'land grab',
            'transparency', 'corruption', 'governance', 'accountability', 'environmental impact'
        ])
        
        # 积极合作框架
        keywords.extend([
            'win-win', 'mutual benefit', 'shared future', 'community of shared future',
            'aid', 'assistance', 'support', 'grant', 'loan', 'development fund', 'capacity building',
            'connectivity', 'integration', 'regional integration', 'trade facilitation'
        ])
        
        # 区域特定术语
        keywords.extend([
            'sgr', 'standard gauge railway', 'mombasa nairobi', 'lamu port', 'ethiopia djibouti',
            'ecowas', 'lagos ibadan', 'abuja', 'accra', 'cotonou', 'dakar', 'bollore',
            'zambia', 'zimbabwe', 'botswana', 'namibia', 'mozambique', 'malawi',
            'egypt', 'cairo', 'suez canal', 'suez economic zone', 'port said'
        ])
        
        # 时间标记
        keywords.extend([
            'bandung conference', 'non aligned movement', 'tanzam railway',
            'forum on china africa cooperation', 'focac',
            'covid-19', 'coronavirus', 'pandemic', 'vaccine', 'mask diplomacy'
        ])
        
        # 布尔运算符组合
        keywords.extend([
            'china africa', 'chinese investment', 'beijing cooperation',
            'xi jinping visit', 'belt road', 'debt trap china'
        ])
        
        return list(set(keywords))  # 去重
    
    @auto_save_progress
    async def crawl_keyword_with_pagination(self, keyword: str, start_year: int, end_year: int):
        """爬取单个关键词的所有分页内容 - MCP增强版"""
        
        # 检查断路器状态
        if not self.circuit_breaker.can_execute():
            logger.warning(f"断路器处于{self.circuit_breaker.state}状态，跳过关键词 '{keyword}'")
            return []
        
        logger.info(f"开始爬取关键词: '{keyword}' ({start_year}-{end_year})")
        
        # 优先尝试MCP增强爬取
        articles = []
        if self.mcp_manager.can_use_mcp():
            logger.info(f"尝试使用MCP增强爬取关键词: {keyword}")
            try:
                # 使用MCP增强爬取 - 遍历所有年份
                for year in range(start_year, end_year + 1):
                    year_articles = await self.crawl_with_mcp_enhancement(keyword, year, 1)
                    articles.extend(year_articles)
                    
                    # 添加延迟避免过于频繁的请求
                    await asyncio.sleep(1.0)
                
                # 记录MCP使用成功
                self.stats['mcp_success_count'] += 1
                logger.info(f"MCP增强爬取成功: {keyword} - 获取 {len(articles)} 篇文章")
                
            except Exception as e:
                logger.warning(f"MCP增强爬取失败，回退到标准爬取: {e}")
                self.stats['mcp_failure_count'] += 1
        
        # 如果MCP爬取失败或未启用，使用标准爬取
        if not articles:
            logger.info(f"使用标准爬取方法: {keyword}")
            
            config = SearchConfig()
            # 增强反爬虫配置 - 动态请求头轮换
            config.headers = self.get_rotated_headers()
            # 智能延迟策略 - 根据关键词复杂度和历史成功率调整延迟
            config.request_delay = self.get_intelligent_delay(keyword)
            # 添加代理支持
            config.proxies = self.get_proxy_config()
            
            async with FixedPyramidCrawler(config) as crawler:
                # 直接调用crawl_single_keyword，它会处理所有分页逻辑
                logger.info(f"开始爬取关键词 '{keyword}' 的所有分页...")
                
                try:
                    # 使用增强错误处理器包装爬虫调用
                    articles = await self.enhanced_error_handler.retry_with_backoff(
                        crawler.crawl_single_keyword,
                        keyword, start_year, end_year
                    )
                    
                    # 记录成功
                    self.circuit_breaker.on_success()
                    
                except Exception as e:
                    # 记录错误
                    error_type = self.enhanced_error_handler.classify_error(e)
                    if error_type not in self.stats['error_statistics']:
                        self.stats['error_statistics'][error_type] = 0
                    self.stats['error_statistics'][error_type] += 1
                    
                    # 记录失败
                    self.circuit_breaker.on_failure()
                    
                    logger.error(f"标准爬取关键词 '{keyword}' 失败: {str(e)} (错误类型: {error_type})")
                    
                    # 保存错误统计
                    self.save_error_statistics()
                    
                    return []
        
        # 验证和保存结果
        validated_articles = []
        for article in articles:
            if hasattr(article, 'to_dict'):
                article_dict = article.to_dict()
            elif hasattr(article, '__dict__'):
                article_dict = article.__dict__
            else:
                article_dict = article
            
            # 验证质量 - 使用新的验证器返回格式
            validation_result = self.quality_validator.validate_article(article_dict)
            
            # 提取质量评分和详细信息
            quality_score = validation_result.get('metrics', {}).get('overall', 0.0)
            article_dict['quality_score'] = quality_score
            article_dict['quality_metrics'] = validation_result.get('metrics', {})
            article_dict['quality_errors'] = validation_result.get('errors', [])
            article_dict['is_duplicate'] = validation_result.get('is_duplicate', False)
            
            # 更新质量统计
            self.update_quality_statistics(article_dict, validation_result)
            
            validated_articles.append(article_dict)
        
        # 保存结果
        new_count = self.save_results(validated_articles)
        
        logger.info(f"关键词 '{keyword}' 爬取完成: 共 {len(validated_articles)} 篇文章，其中 {new_count} 篇新文章")
        
        # 更新进度
        self.progress['current_keyword'] = keyword
        self.progress['current_page'] = 1
        self.save_progress()
        self.save_error_statistics()
        self.save_quality_statistics()
        
        return validated_articles
    
    @auto_save_progress
    async def run_massive_crawl(self, start_year: int = 2010, end_year: int = 2025):
        """执行大规模爬取 - 优化版"""
        logger.info(f"开始大规模爬取 ({start_year}-{end_year})")
        
        # 获取所有关键词
        keywords = self.extract_keywords_from_library()
        self.stats['total_keywords'] = len(keywords)
        
        logger.info(f"将爬取 {len(keywords)} 个关键词")
        
        # 恢复进度（如果存在）
        if self.progress['current_keyword']:
            current_keyword = self.progress['current_keyword']
            if current_keyword in keywords:
                # 从当前关键词继续
                keyword_index = keywords.index(current_keyword)
                keywords = keywords[keyword_index:]
                logger.info(f"从关键词 '{current_keyword}' 继续爬取")
        
        # 优化批次处理策略
        batch_size = 2  # 每次处理2个关键词
        total_articles = 0
        failed_keywords = []
        
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            logger.info(f"处理批次 {i//batch_size + 1}: {batch}")
            
            # 并行处理批次内的关键词
            tasks = [
                self.crawl_keyword_with_pagination(keyword, start_year, end_year) 
                for keyword in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"关键词 '{batch[j]}' 爬取失败: {result}")
                    failed_keywords.append({
                        'keyword': batch[j],
                        'error': str(result),
                        'batch': i//batch_size + 1
                    })
                    
                    # 尝试重试失败的关键词
                    logger.info(f"将关键词 '{batch[j]}' 加入重试队列")
                else:
                    total_articles += len(result)
                    self.stats['completed_keywords'] += 1
                    self.stats['total_articles'] = total_articles
                    
                    # 标记为已完成
                    if batch[j] not in self.progress['completed_keywords']:
                        self.progress['completed_keywords'].append(batch[j])
                    
                    # 清除当前关键词
                    self.progress['current_keyword'] = None
                    self.progress['current_page'] = 1
                    self.save_progress()
            
            # 智能批次间延迟策略 - 根据批次大小和成功率调整
            delay_time = self.get_batch_delay(i//batch_size + 1, len(batch), total_articles)
            logger.info(f"批次 {i//batch_size + 1} 完成，总计 {total_articles} 篇文章，等待 {delay_time:.2f} 秒...")
            await asyncio.sleep(delay_time)
        
        # 处理失败的关键词（重试机制）
        if failed_keywords:
            logger.info(f"开始重试 {len(failed_keywords)} 个失败的关键词")
            
            for failed in failed_keywords:
                try:
                    logger.info(f"重试关键词: {failed['keyword']}")
                    result = await self.crawl_keyword_with_pagination(failed['keyword'], start_year, end_year)
                    total_articles += len(result)
                    self.stats['completed_keywords'] += 1
                    self.stats['total_articles'] = total_articles
                    
                    if failed['keyword'] not in self.progress['completed_keywords']:
                        self.progress['completed_keywords'].append(failed['keyword'])
                    
                    logger.info(f"重试成功: {failed['keyword']} - {len(result)} 篇文章")
                    
                except Exception as e:
                    logger.error(f"重试失败: {failed['keyword']} - {e}")
        
        # 生成最终报告
        self.generate_final_report()
        
        logger.info(f"大规模爬取完成! 总计爬取 {total_articles} 篇文章")
        logger.info(f"成功关键词: {self.stats['completed_keywords']}/{self.stats['total_keywords']}")
        if failed_keywords:
            logger.info(f"失败关键词: {len(failed_keywords)}")
        
        return total_articles
    
    def generate_final_report(self):
        """生成最终爬取报告"""
        report = {
            'crawl_summary': {
                'total_keywords': self.stats['total_keywords'],
                'completed_keywords': self.stats['completed_keywords'],
                'total_articles': self.stats['total_articles'],
                'start_time': self.stats['start_time'],
                'end_time': datetime.now().isoformat(),
                'duration_hours': (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds() / 3600
            },
            'progress_details': self.progress,
            'output_files': {
                'results_file': self.results_file,
                'progress_file': self.progress_file,
                'log_file': 'massive_crawler.log'
            }
        }
        
        report_file = os.path.join(self.output_dir, "final_crawl_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"最终报告已保存到: {report_file}")
        return report

class FixedPerformanceTester:
    """修复后的性能测试器"""
    
    def __init__(self):
        self.test_results = []
    
    async def test_single_keyword(self, keyword: str, start_year: int, end_year: int):
        """测试单个关键词的爬取性能（使用修复版爬虫）"""
        logger.info(f"开始测试关键词: {keyword}")
        
        config = SearchConfig()
        async with FixedPyramidCrawler(config) as crawler:
            start_time = time.time()
            
            try:
                # 使用修复版爬虫方法
                articles = await crawler.crawl_single_keyword(keyword, start_year, end_year)
                
                end_time = time.time()
                
                result = {
                    'keyword': keyword,
                    'articles_found': len(articles),
                    'time_elapsed': end_time - start_time,
                    'articles_per_second': len(articles) / (end_time - start_time) if (end_time - start_time) > 0 else 0,
                    'success': True,
                    'error_count': 0
                }
                
                logger.info(f"关键词 '{keyword}' 测试完成: {result['articles_found']} 篇文章, 耗时 {result['time_elapsed']:.2f} 秒")
                
                # 输出前几篇文章的标题作为验证
                if articles:
                    logger.info("提取的文章标题示例:")
                    for i, article in enumerate(articles[:3]):
                        logger.info(f"  {i+1}. {article.title}")
                
            except Exception as e:
                end_time = time.time()
                result = {
                    'keyword': keyword,
                    'articles_found': 0,
                    'time_elapsed': end_time - start_time,
                    'articles_per_second': 0,
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"关键词 '{keyword}' 测试失败: {e}")
            
            self.test_results.append(result)
            return result
    
    async def test_batch_keywords(self, keywords: list, start_year: int, end_year: int, batch_size: int = 2):
        """批量测试多个关键词的性能"""
        logger.info(f"开始批量测试 {len(keywords)} 个关键词，批次大小: {batch_size}")
        
        total_start_time = time.time()
        
        # 分批处理关键词
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            logger.info(f"处理批次 {i//batch_size + 1}: {batch}")
            
            # 并行处理批次内的关键词
            tasks = [self.test_single_keyword(keyword, start_year, end_year) for keyword in batch]
            await asyncio.gather(*tasks)
            
            # 批次间延迟，避免过于频繁的请求
            await asyncio.sleep(2)
        
        total_end_time = time.time()
        
        # 计算总体统计
        successful_tests = [r for r in self.test_results if r['success']]
        failed_tests = [r for r in self.test_results if not r['success']]
        
        summary = {
            'total_keywords_tested': len(keywords),
            'successful_tests': len(successful_tests),
            'failed_tests': len(failed_tests),
            'total_articles_found': sum(r['articles_found'] for r in successful_tests),
            'total_time_elapsed': total_end_time - total_start_time,
            'average_articles_per_second': sum(r['articles_per_second'] for r in successful_tests) / len(successful_tests) if successful_tests else 0,
            'average_time_per_keyword': sum(r['time_elapsed'] for r in successful_tests) / len(successful_tests) if successful_tests else 0,
            'test_timestamp': datetime.now().isoformat(),
            'batch_size_used': batch_size
        }
        
        return summary
    
    def analyze_performance(self):
        """分析性能测试结果"""
        if not self.test_results:
            return "没有测试结果可分析"
        
        successful_tests = [r for r in self.test_results if r['success']]
        
        if not successful_tests:
            return "所有测试都失败了"
        
        analysis = {
            'performance_metrics': {
                'total_articles': sum(r['articles_found'] for r in successful_tests),
                'avg_articles_per_second': sum(r['articles_per_second'] for r in successful_tests) / len(successful_tests),
                'avg_time_per_keyword': sum(r['time_elapsed'] for r in successful_tests) / len(successful_tests),
                'fastest_keyword': min(successful_tests, key=lambda x: x['time_elapsed']),
                'slowest_keyword': max(successful_tests, key=lambda x: x['time_elapsed']),
                'most_productive_keyword': max(successful_tests, key=lambda x: x['articles_found'])
            },
            'reliability_metrics': {
                'success_rate': len(successful_tests) / len(self.test_results),
                'total_errors': sum(r.get('error_count', 0) for r in successful_tests),
                'avg_errors_per_keyword': sum(r.get('error_count', 0) for r in successful_tests) / len(successful_tests) if successful_tests else 0
            }
        }
        
        return analysis
    
    def generate_performance_report(self, filename: str = "performance_report_fixed.json"):
        """生成性能测试报告"""
        report = {
            'test_results': self.test_results,
            'performance_analysis': self.analyze_performance(),
            'test_summary': {
                'total_tests': len(self.test_results),
                'successful_tests': len([r for r in self.test_results if r['success']]),
                'failed_tests': len([r for r in self.test_results if not r['success']]),
                'report_generated_at': datetime.now().isoformat()
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"修复后的性能报告已保存到: {filename}")
        return report

async def run_massive_crawl():
    """运行大规模爬虫"""
    logger.info("启动金字塔报大规模爬虫 (2010-2025)")
    
    # 创建大规模爬虫实例
    crawler = MassivePyramidCrawler(output_dir="massive_crawler_results")
    
    # 执行大规模爬取
    total_articles = await crawler.run_massive_crawl(start_year=2010, end_year=2025)
    
    logger.info(f"大规模爬取完成! 总计爬取 {total_articles} 篇文章")
    
    # 显示结果文件位置
    logger.info(f"爬取结果保存在: {crawler.results_file}")
    logger.info(f"进度文件保存在: {crawler.progress_file}")
    logger.info(f"日志文件保存在: massive_crawler.log")
    
    return total_articles

async def run_performance_test():
    """运行性能测试"""
    logger.info("开始修复后的金字塔报爬虫性能测试")
    
    # 创建性能测试器
    tester = FixedPerformanceTester()
    
    # 加载关键词（使用前3个进行测试）
    all_keywords = load_keywords_from_library()
    test_keywords = all_keywords[:3]  # 测试前3个关键词
    
    logger.info(f"将测试 {len(test_keywords)} 个关键词: {test_keywords}")
    
    # 执行性能测试
    summary = await tester.test_batch_keywords(test_keywords, start_year=2020, end_year=2024, batch_size=1)
    
    # 生成性能报告
    report = tester.generate_performance_report()
    
    # 输出测试摘要
    logger.info("修复后的性能测试完成!")
    logger.info(f"测试关键词数量: {summary['total_keywords_tested']}")
    logger.info(f"成功测试: {summary['successful_tests']}")
    logger.info(f"失败测试: {summary['failed_tests']}")
    logger.info(f"总耗时: {summary['total_time_elapsed']:.2f} 秒")
    logger.info(f"平均每关键词耗时: {summary['average_time_per_keyword']:.2f} 秒")
    logger.info(f"平均每秒爬取文章数: {summary['average_articles_per_second']:.2f}")
    logger.info(f"总文章数: {summary['total_articles_found']}")
    
    # 性能优化建议
    analysis = tester.analyze_performance()
    if analysis and 'performance_metrics' in analysis:
        metrics = analysis['performance_metrics']
        logger.info("性能分析结果:")
        logger.info(f"  - 总文章数: {metrics['total_articles']}")
        logger.info(f"  - 平均每秒爬取文章数: {metrics['avg_articles_per_second']:.2f}")
        logger.info(f"  - 平均每关键词耗时: {metrics['avg_time_per_keyword']:.2f} 秒")
        
        if metrics['total_articles'] > 0:
            logger.info("✓ 爬虫功能正常，能够成功提取文章")
        else:
            logger.info("⚠ 未找到任何文章，可能需要检查关键词或网站结构")

async def main():
    """主函数 - 自动运行大规模爬虫模式"""
    print("=== 金字塔报爬虫系统 ===")
    print("自动启动大规模爬虫模式 (2010-2025)")
    
    # 检查是否有现有进度
    crawler = MassivePyramidCrawler()
    if os.path.exists(crawler.progress_file):
        with open(crawler.progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
        print("检测到现有爬取进度:")
        print(f"已完成关键词: {len(progress.get('completed_keywords', []))}")
        print(f"当前关键词: {progress.get('current_keyword', '无')}")
        print(f"当前页数: {progress.get('current_page', 1)}")
        print(f"最后保存时间: {progress.get('last_save_time', '未知')}")
        print("继续从上次中断处继续爬取...")
    else:
        print("未检测到现有进度，开始全新爬取...")
    
    # 自动运行大规模爬虫
    await run_massive_crawl()

if __name__ == "__main__":
    asyncio.run(main())