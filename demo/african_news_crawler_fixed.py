#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非洲新闻专业爬虫系统 - 修复版
专门针对非洲本地新闻网站优化，排除BBC、China Daily等非非洲新闻源
支持关键词搜索、真实数据爬取、断点续爬、并行处理
"""

import requests
import time
import random
import json
import os
import re
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urlencode, urljoin
import urllib3
from bs4 import BeautifulSoup

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('african_news_crawler_fixed.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AfricanNewsCrawlerFixed:
    """非洲新闻专业爬虫类 - 修复版"""
    
    def __init__(self, max_workers=3):
        self.max_workers = max_workers
        
        # 非洲本地新闻网站配置（排除BBC、China Daily等非非洲源）
        self.african_news_sites = [
            # 尼日利亚
            {
                'name': 'Premium Times Nigeria',
                'url': 'https://www.premiumtimesng.com',
                'search_url': 'https://www.premiumtimesng.com/search',
                'country': 'Nigeria',
                'language': 'english'
            },
            {
                'name': 'Vanguard Nigeria',
                'url': 'https://www.vanguardngr.com',
                'search_url': 'https://www.vanguardngr.com/search',
                'country': 'Nigeria',
                'language': 'english'
            },
            {
                'name': 'This Day Nigeria',
                'url': 'https://www.thisdaylive.com',
                'search_url': 'https://www.thisdaylive.com/index.php/search',
                'country': 'Nigeria',
                'language': 'english'
            },
            
            # 南非
            {
                'name': 'Mail & Guardian South Africa',
                'url': 'https://mg.co.za',
                'search_url': 'https://mg.co.za/search',
                'country': 'South Africa',
                'language': 'english'
            },
            {
                'name': 'News24 South Africa',
                'url': 'https://www.news24.com',
                'search_url': 'https://www.news24.com/search',
                'country': 'South Africa',
                'language': 'english'
            },
            {
                'name': 'IOL South Africa',
                'url': 'https://www.iol.co.za',
                'search_url': 'https://www.iol.co.za/search',
                'country': 'South Africa',
                'language': 'english'
            },
            
            # 肯尼亚
            {
                'name': 'Daily Nation Kenya',
                'url': 'https://nation.africa',
                'search_url': 'https://nation.africa/search',
                'country': 'Kenya',
                'language': 'english'
            },
            {
                'name': 'The Star Kenya',
                'url': 'https://www.the-star.co.ke',
                'search_url': 'https://www.the-star.co.ke/search',
                'country': 'Kenya',
                'language': 'english'
            },
            
            # 坦桑尼亚
            {
                'name': 'The Citizen Tanzania',
                'url': 'https://www.thecitizen.co.tz',
                'search_url': 'https://www.thecitizen.co.tz/search',
                'country': 'Tanzania',
                'language': 'english'
            },
            
            # 加纳
            {
                'name': 'GhanaWeb',
                'url': 'https://www.ghanaweb.com',
                'search_url': 'https://www.ghanaweb.com/search',
                'country': 'Ghana',
                'language': 'english'
            },
            {
                'name': 'Graphic Online Ghana',
                'url': 'https://www.graphic.com.gh',
                'search_url': 'https://www.graphic.com.gh/search',
                'country': 'Ghana',
                'language': 'english'
            },
            
            # 泛非洲
            {
                'name': 'AllAfrica',
                'url': 'https://allafrica.com',
                'search_url': 'https://allafrica.com/search',
                'country': 'Pan-African',
                'language': 'english'
            },
            {
                'name': 'Africanews',
                'url': 'https://www.africanews.com',
                'search_url': 'https://www.africanews.com/search',
                'country': 'Pan-African',
                'language': 'english'
            }
        ]
        
        # 用户代理列表
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # 数据存储配置
        self.data_dir = 'data/results'
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 请求配置
        self.timeout = (10, 30)
        
    def get_session(self, site_config):
        """获取针对特定非洲新闻网站优化的会话"""
        session = requests.Session()
        session.timeout = self.timeout
        session.verify = False  # 禁用SSL验证以应对某些非洲网站
        
        # 设置请求头
        session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Referer': site_config['url']
        })
        
        return session
    
    def search_african_news(self, keyword, year, max_results=10):
        """在非洲新闻网站中搜索关键词"""
        results = []
        
        logger.info(f"开始在非洲新闻网站搜索: {keyword} ({year})")
        
        # 并行搜索多个非洲新闻网站
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 为每个网站提交搜索任务
            future_to_site = {
                executor.submit(self._search_single_site, site, keyword, year, max_results): site 
                for site in self.african_news_sites
            }
            
            # 收集结果
            for future in as_completed(future_to_site):
                site = future_to_site[future]
                try:
                    site_results = future.result(timeout=60)
                    if site_results:
                        results.extend(site_results)
                        logger.info(f"从{site['name']}获取到{len(site_results)}条结果")
                except Exception as e:
                    logger.warning(f"搜索{site['name']}失败: {e}")
        
        # 去重并排序
        unique_results = self._deduplicate_results(results)
        
        logger.info(f"搜索完成，共获取{len(unique_results)}条非洲新闻")
        return unique_results
    
    def _search_single_site(self, site_config, keyword, year, max_results):
        """在单个非洲新闻网站搜索"""
        results = []
        
        try:
            session = self.get_session(site_config)
            
            # 构建搜索查询
            search_query = f"{keyword} {year} Africa"
            
            # 根据不同网站配置搜索参数
            search_params = {
                'q': search_query,
                'search': search_query,
                's': search_query,
                'query': search_query
            }
            
            # 发送搜索请求
            response = session.get(site_config['search_url'], params=search_params, timeout=self.timeout)
            response.raise_for_status()
            
            # 解析搜索结果
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 根据网站结构提取新闻链接
            article_links = self._extract_article_links(soup, site_config)
            
            # 限制结果数量
            article_links = article_links[:max_results]
            
            # 获取文章内容
            for link in article_links:
                try:
                    article_data = self._extract_article_content(session, link, site_config)
                    if article_data:
                        article_data.update({
                            'source': site_config['name'],
                            'country': site_config['country'],
                            'language': site_config['language'],
                            'crawl_method': 'traditional',
                            'crawl_time': datetime.now().isoformat()
                        })
                        results.append(article_data)
                        
                        # 添加随机延迟避免被封
                        time.sleep(random.uniform(1, 3))
                        
                except Exception as e:
                    logger.warning(f"提取文章内容失败 {link}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"搜索{site_config['name']}失败: {e}")
        
        return results
    
    def _extract_article_links(self, soup, site_config):
        """从搜索结果页面提取文章链接"""
        links = []
        
        # 根据网站结构提取链接
        selectors = [
            'a[href*="/news/"]',
            'a[href*="/article/"]',
            'a[href*="/story/"]',
            '.article-title a',
            '.news-item a',
            '.search-result a',
            'h2 a',
            'h3 a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href and self._is_article_url(href, site_config):
                    # 转换为绝对URL
                    full_url = urljoin(site_config['url'], href)
                    links.append(full_url)
        
        return list(set(links))  # 去重
    
    def _is_article_url(self, url, site_config):
        """判断URL是否为文章链接"""
        # 排除非文章链接
        exclude_patterns = [
            '/category/', '/tag/', '/author/', '/page/', 
            '/search/', '/contact/', '/about/', '/privacy/'
        ]
        
        url_lower = url.lower()
        
        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False
        
        # 包含文章标识
        article_patterns = [
            '/news/', '/article/', '/story/', '/202', '/20'
        ]
        
        for pattern in article_patterns:
            if pattern in url_lower:
                return True
        
        return False
    
    def _extract_article_content(self, session, article_url, site_config):
        """提取文章内容"""
        try:
            response = session.get(article_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取标题
            title_selectors = [
                'h1', '.article-title', '.news-title', '.headline',
                'title', 'h1.entry-title', '.post-title'
            ]
            title = self._extract_text(soup, title_selectors)
            
            # 提取内容
            content_selectors = [
                '.article-content', '.news-content', '.entry-content',
                '.post-content', '.story-content', 'article',
                '.content', '.main-content'
            ]
            content = self._extract_text(soup, content_selectors)
            
            # 提取发布日期
            date_selectors = [
                '.date', '.publish-date', '.post-date', '.article-date',
                'time', '.timestamp'
            ]
            publish_date = self._extract_text(soup, date_selectors)
            
            if not title or not content:
                return None
            
            return {
                'title': title.strip(),
                'url': article_url,
                'content': content.strip(),
                'publish_date': publish_date.strip() if publish_date else '',
                'keyword': '',  # 将在外部设置
                'year': ''  # 将在外部设置
            }
            
        except Exception as e:
            logger.warning(f"提取文章内容失败 {article_url}: {e}")
            return None
    
    def _extract_text(self, soup, selectors):
        """使用多个选择器提取文本"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return ''
    
    def _deduplicate_results(self, results):
        """去重结果"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        return unique_results
    
    def crawl_real_african_news(self, tasks_file='data/tasks_209.json', output_file='data/results/real_african_news.json'):
        """爬取真实的非洲新闻数据"""
        
        # 加载任务文件
        try:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
            logger.info(f"已加载{len(tasks)}个任务")
        except Exception as e:
            logger.error(f"加载任务文件失败: {e}")
            return False
        
        # 处理每个任务
        results = []
        processed_count = 0
        
        for task in tasks:
            if task.get('status') == 'completed':
                # 跳过已完成的任务
                continue
                
            try:
                keyword = task.get('keyword', '')
                year = task.get('year', '')
                
                if not keyword or not year:
                    continue
                
                logger.info(f"处理任务: {keyword} ({year})")
                
                # 搜索非洲新闻
                news_results = self.search_african_news(keyword, year, max_results=5)
                
                # 更新任务状态
                task.update({
                    'status': 'completed',
                    'processed_at': datetime.now().isoformat(),
                    'crawl_method': 'traditional',
                    'urls_attempted': len(news_results),
                    'urls_successful': len(news_results),
                    'data_quality_score': min(1.0, len(news_results) * 0.2),  # 基于结果数量计算质量分数
                    'results': news_results
                })
                
                results.append(task)
                processed_count += 1
                
                # 每处理5个任务保存一次进度
                if processed_count % 5 == 0:
                    self._save_progress(results, output_file)
                    logger.info(f"已处理{processed_count}个任务")
                
                # 添加延迟避免被封
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"处理任务失败 {task.get('task_id', 'unknown')}: {e}")
                # 标记为失败但继续处理其他任务
                task.update({
                    'status': 'failed',
                    'error': str(e)
                })
                results.append(task)
        
        # 保存最终结果
        self._save_progress(results, output_file)
        logger.info(f"爬取完成，共处理{processed_count}个任务")
        return True
    
    def _save_progress(self, results, output_file):
        """保存进度"""
        try:
            # 如果文件已存在，合并结果
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_results = json.load(f)
                
                # 创建任务ID映射以去重
                existing_map = {r['task_id']: r for r in existing_results}
                
                # 更新或添加新结果
                for result in results:
                    existing_map[result['task_id']] = result
                
                results = list(existing_map.values())
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存进度失败: {e}")

def main():
    """主函数"""
    crawler = AfricanNewsCrawlerFixed(max_workers=3)
    
    logger.info("开始爬取非洲新闻数据...")
    
    # 爬取真实的非洲新闻
    success = crawler.crawl_real_african_news(
        tasks_file='data/tasks_209.json',
        output_file='data/results/real_african_news.json'
    )
    
    if success:
        logger.info("非洲新闻爬取完成！")
    else:
        logger.error("非洲新闻爬取失败！")

if __name__ == "__main__":
    main()