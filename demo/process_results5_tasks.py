#!/usr/bin/env python3
"""
直接处理results_5.json任务的系统
基于现有的工作节点架构，直接处理非洲本地语言关键词任务
"""

import json
import time
import logging
from datetime import datetime
import os
import sys
import requests
from bs4 import BeautifulSoup

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from distributed_worker_fixed import DistributedWorker  # 导入正确的爬虫类

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('results5_processor')

class Results5Processor:
    def __init__(self, results_file_path="data/results/results_5.json"):
        self.results_file_path = results_file_path
        
    def load_results5_tasks(self):
        """加载results_5.json中的任务"""
        try:
            with open(self.results_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 筛选出pending状态的任务
            pending_tasks = [task for task in data if task.get('status') == 'pending']
            logger.info(f"找到 {len(pending_tasks)} 个待处理的results_5.json任务")
            
            for task in pending_tasks:
                logger.info(f"任务ID: {task['task_id']}, 关键词: {task['keyword']}")
            
            return pending_tasks
            
        except Exception as e:
            logger.error(f"加载results_5.json失败: {e}")
            return []
    
    def extract_article_links(self, html_content, website):
        """从搜索结果页面提取实际的文章链接"""
        article_links = []
        
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 针对不同网站的链接提取策略
            if website == "allafrica.com":
                # AllAfrica.com的文章链接通常包含/stories/路径
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if '/stories/' in href and href.endswith('.html'):
                        full_url = href if href.startswith('http') else f"https://allafrica.com{href}"
                        article_links.append(full_url)
                        
            elif website == "news24.com":
                # News24.com的文章链接通常包含特定模式
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if '/news24/' in href and '/article/' in href:
                        full_url = href if href.startswith('http') else f"https://news24.com{href}"
                        article_links.append(full_url)
                        
            elif website == "sabcnews.com":
                # SABC News的文章链接
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if '/sabcnews/' in href and href.endswith('/'):
                        full_url = href if href.startswith('http') else f"https://sabcnews.com{href}"
                        article_links.append(full_url)
                        
            elif website == "nation.africa":
                # Nation Africa的文章链接
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if '/nation/' in href and '/news/' in href:
                        full_url = href if href.startswith('http') else f"https://nation.africa{href}"
                        article_links.append(full_url)
                        
            elif website == "punchng.com":
                # Punch Nigeria的文章链接
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if '/punchng/' in href and '/news/' in href:
                        full_url = href if href.startswith('http') else f"https://punchng.com{href}"
                        article_links.append(full_url)
            
            # 去重并限制数量
            article_links = list(set(article_links))[:10]  # 最多取10篇文章
            logger.info(f"从 {website} 搜索结果中提取到 {len(article_links)} 个文章链接")
            
        except Exception as e:
            logger.error(f"提取 {website} 文章链接失败: {e}")
        
        return article_links

    def crawl_search_page(self, url, website):
        """爬取搜索页面并返回HTML内容"""
        try:
            import requests
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            return response.text
            
        except Exception as e:
            logger.error(f"爬取搜索页面 {url} 失败: {e}")
            return None

    def process_single_task(self, task):
        """处理单个任务 - 修复版：先提取文章链接，再爬取实际文章"""
        try:
            logger.info(f"开始处理任务: {task['task_id']}")
            
            # 导入爬虫模块
            from distributed_worker_fixed import DistributedWorker
            
            # 创建爬虫实例
            crawler = DistributedWorker()
            
            # 构建搜索URL
            keyword = task['keyword']
            year = task['year']
            
            # 主要非洲新闻网站
            websites = [
                "allafrica.com",
                "news24.com", 
                "sabcnews.com",
                "nation.africa",
                "punchng.com"
            ]
            
            results = []
            
            for website in websites[:2]:  # 先处理前2个网站
                try:
                    # 构建搜索URL
                    if website == "allafrica.com":
                        search_url = f"https://{website}/search?q={keyword}&year={year}"
                    elif website == "news24.com":
                        search_url = f"https://{website}/search?q={keyword}&year={year}"
                    else:
                        search_url = f"https://{website}/search?q={keyword}"
                    
                    logger.info(f"处理网站: {website}, 搜索URL: {search_url}")
                    
                    # 第一步：爬取搜索页面
                    search_html = self.crawl_search_page(search_url, website)
                    if not search_html:
                        logger.warning(f"无法获取 {website} 的搜索结果页面")
                        continue
                    
                    # 第二步：从搜索结果页面提取实际文章链接
                    article_links = self.extract_article_links(search_html, website)
                    if not article_links:
                        logger.warning(f"从 {website} 搜索结果中未找到文章链接")
                        continue
                    
                    # 第三步：爬取实际的文章内容
                    crawled_articles = []
                    for article_url in article_links[:3]:  # 每个网站最多爬取3篇文章
                        try:
                            logger.info(f"爬取实际文章: {article_url}")
                            articles = crawler.crawl_url(article_url, keyword, year)
                            
                            if articles:
                                crawled_articles.extend(articles)
                                logger.info(f"成功爬取文章: {articles[0].get('title', '无标题')[:50]}...")
                            
                            # 延迟避免过快请求
                            time.sleep(2)
                            
                        except Exception as e:
                            logger.error(f"爬取文章 {article_url} 失败: {e}")
                            continue
                    
                    if crawled_articles:
                        results.extend(crawled_articles)
                        logger.info(f"从 {website} 成功爬取 {len(crawled_articles)} 篇实际文章")
                    else:
                        logger.warning(f"从 {website} 未成功爬取任何实际文章")
                        
                    # 延迟避免过快请求
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"处理网站 {website} 失败: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"处理任务 {task['task_id']} 失败: {e}")
            return []
    
    def update_task_status(self, task_id, status, results=None, worker_id=None):
        """更新任务状态"""
        try:
            with open(self.results_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 更新任务状态
            for task in data:
                if task['task_id'] == task_id:
                    task['status'] = status
                    task['processed_at'] = datetime.now().isoformat()
                    if results is not None:
                        task['results'] = results
                    if worker_id:
                        task['worker_id'] = worker_id
                    
                    # 更新质量统计
                    if results:
                        task['quality_stats']['total_articles'] = len(results)
                        task['quality_stats']['valid_articles'] = len(results)
                        task['data_quality_score'] = 1.0 if len(results) > 0 else 0.0
                    
                    break
            
            # 保存更新后的数据
            with open(self.results_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"更新任务 {task_id} 状态为 {status}")
            
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
    
    def process_all_tasks(self):
        """处理所有任务"""
        logger.info("=== 开始处理results_5.json任务 ===")
        
        # 加载待处理任务
        tasks = self.load_results5_tasks()
        if not tasks:
            logger.info("没有找到待处理的results_5.json任务")
            return True
        
        total_tasks = len(tasks)
        completed_tasks = 0
        
        # 处理每个任务
        for task in tasks:
            try:
                # 更新状态为处理中
                self.update_task_status(task['task_id'], 'processing')
                
                # 处理任务
                results = self.process_single_task(task)
                
                # 更新状态为完成
                self.update_task_status(
                    task['task_id'], 
                    'completed', 
                    results=results,
                    worker_id='results5-processor'
                )
                
                completed_tasks += 1
                logger.info(f"任务 {task['task_id']} 处理完成 ({completed_tasks}/{total_tasks})")
                logger.info(f"爬取到 {len(results)} 篇文章")
                
                # 显示部分结果
                if results:
                    for i, article in enumerate(results[:2]):
                        logger.info(f"文章 {i+1}: {article.get('title', '无标题')[:50]}...")
                
                # 延迟避免过快请求
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"处理任务 {task['task_id']} 时发生异常: {e}")
                # 更新状态为失败
                self.update_task_status(task['task_id'], 'failed')
                continue
        
        logger.info(f"所有任务处理完成! 成功处理 {completed_tasks}/{total_tasks} 个任务")
        return completed_tasks == total_tasks

def main():
    """主函数"""
    processor = Results5Processor()
    
    try:
        success = processor.process_all_tasks()
        if success:
            logger.info("results_5.json任务处理完成!")
        else:
            logger.warning("部分results_5.json任务处理失败")
    except KeyboardInterrupt:
        logger.info("用户中断处理过程")
    except Exception as e:
        logger.error(f"处理过程中发生异常: {e}")

if __name__ == "__main__":
    main()