#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版工作节点 - 增强网络稳定性和任务处理能力
"""

import requests
import time
import json
import logging
import random
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimized_worker.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class OptimizedWorker:
    def __init__(self, worker_id, master_url="http://localhost:8000"):
        self.worker_id = worker_id
        self.master_url = master_url
        self.session = self._create_session()
        self.running = True
        self.task_executor = ThreadPoolExecutor(max_workers=5)  # 增加并行任务数
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'network_errors': 0,
            'success_rate': 0.0
        }
        
    def _create_session(self):
        """创建优化的HTTP会话"""
        session = requests.Session()
        
        # 优化请求头，模拟真实浏览器
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # 优化超时设置
        session.mount('http://', requests.adapters.HTTPAdapter(
            max_retries=3,  # 增加重试次数
            pool_connections=20,
            pool_maxsize=20
        ))
        session.mount('https://', requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=20,
            pool_maxsize=20
        ))
        
        return session
    
    def get_task(self):
        """从主节点获取任务 - 支持两种任务类型"""
        try:
            response = self.session.get(
                f"{self.master_url}/tasks/next",
                params={'worker_id': self.worker_id},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                task = result.get('task')
                
                # 检查任务数据有效性 - 支持两种任务类型
                if not task or not task.get('task_id'):
                    logger.warning(f"获取到无效任务数据: {task}")
                    return None
                
                # 检查任务类型：URL爬取任务或关键词搜索任务
                if task.get('url'):
                    # URL爬取任务
                    logger.info(f"获取到URL爬取任务: {task.get('task_id')}")
                elif task.get('keyword') and task.get('year'):
                    # 关键词搜索任务
                    logger.info(f"获取到关键词搜索任务: {task.get('keyword')} - {task.get('year')}")
                else:
                    logger.warning(f"获取到未知格式任务: {task}")
                    return None
                
                return task
            elif response.status_code == 204:
                # 没有任务可用
                return None
            else:
                logger.warning(f"获取任务失败: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"获取任务网络错误: {e}")
            return None
        except Exception as e:
            logger.error(f"获取任务异常: {e}")
            return None
    
    def build_search_urls(self, keyword, year):
        """基于关键词和年份构建搜索URL列表"""
        # 非洲新闻网站列表，按可靠性分级
        africa_news_sites = {
            'high_reliability': [
                'https://allafrica.com',
                'https://www.bbc.com/news/world/africa',
                'https://www.aljazeera.com/africa'
            ],
            'medium_reliability': [
                'https://www.news24.com',
                'https://www.dailymaverick.co.za',
                'https://www.theeastafrican.co.ke'
            ],
            'low_reliability': [
                'https://www.premiumtimesng.com',
                'https://www.ghanaweb.com',
                'https://www.monitor.co.ug'
            ]
        }
        
        # 对关键词进行URL编码
        encoded_keyword = quote(keyword)
        
        search_urls = []
        
        # 为每个网站构建搜索URL
        for reliability, sites in africa_news_sites.items():
            for site in sites:
                if 'allafrica.com' in site:
                    # AllAfrica搜索格式
                    search_url = f"{site}/search/?q={encoded_keyword}&year={year}"
                elif 'bbc.com' in site:
                    # BBC搜索格式
                    search_url = f"{site}/search?q={encoded_keyword}"
                elif 'aljazeera.com' in site:
                    # Al Jazeera搜索格式
                    search_url = f"{site}/search?q={encoded_keyword}"
                else:
                    # 通用搜索格式
                    search_url = f"{site}/search?q={encoded_keyword}&year={year}"
                
                search_urls.append({
                    'url': search_url,
                    'reliability': reliability,
                    'site': site
                })
        
        # 随机打乱URL顺序，避免模式化访问
        random.shuffle(search_urls)
        
        # 限制最大URL数量为15个
        return search_urls[:15]
    
    def crawl_url(self, url, method="traditional"):
        """优化版URL爬取方法"""
        try:
            # 随机延迟，避免被检测
            time.sleep(random.uniform(1, 3))
            
            # 根据URL类型选择不同的超时策略
            domain = urlparse(url).netloc
            timeout = 45 if 'allafrica.com' in domain else 30  # 对allafrica.com增加超时时间
            
            logger.info(f"开始爬取URL: {url} (超时: {timeout}秒)")
            
            response = self.session.get(url, timeout=timeout)
            
            if response.status_code == 200:
                # 简单的HTML解析，提取标题
                content = response.text
                title_start = content.find('<title>')
                title_end = content.find('</title>')
                
                if title_start != -1 and title_end != -1:
                    title = content[title_start+7:title_end].strip()
                else:
                    title = f"来自 {domain} 的文章"
                
                article = {
                    'title': title,
                    'url': url,
                    'source': domain,
                    'crawled_at': datetime.now().isoformat(),
                    'method': method
                }
                
                logger.info(f"成功爬取文章: {title}")
                return article
            else:
                logger.warning(f"URL返回非200状态码: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning(f"爬取URL超时: {url}")
            return None
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接错误: {url}, 错误: {e}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"爬取URL失败: {url}, 错误: {e}")
            return None
    
    def process_keyword_task(self, task):
        """处理关键词搜索任务"""
        task_id = task.get('task_id')
        keyword = task.get('keyword')
        year = task.get('year')
        
        logger.info(f"开始处理关键词搜索任务 {task_id}: 关键词='{keyword}', 年份={year}")
        
        # 构建搜索URL列表
        search_urls = self.build_search_urls(keyword, year)
        
        if not search_urls:
            logger.warning(f"关键词任务 {task_id} 无法构建搜索URL")
            return None
        
        logger.info(f"为关键词任务 {task_id} 构建了 {len(search_urls)} 个搜索URL")
        
        # 爬取搜索结果页面
        search_results = []
        for i, search_info in enumerate(search_urls):
            search_url = search_info['url']
            reliability = search_info['reliability']
            site = search_info['site']
            
            logger.info(f"爬取搜索URL {i+1}/{len(search_urls)}: {search_url} (可靠性: {reliability})")
            
            # 爬取搜索页面
            search_result = self.crawl_url(search_url, method="search")
            
            if search_result:
                # 添加搜索相关信息
                search_result['search_keyword'] = keyword
                search_result['search_year'] = year
                search_result['search_reliability'] = reliability
                search_result['search_site'] = site
                search_result['task_type'] = 'keyword_search'
                
                search_results.append(search_result)
                
                # 成功爬取后短暂休息
                time.sleep(random.uniform(0.5, 1.5))
            else:
                logger.warning(f"搜索URL爬取失败: {search_url}")
        
        if search_results:
            logger.info(f"关键词任务 {task_id} 完成，成功爬取 {len(search_results)} 个搜索结果")
            return {
                'task_id': task_id,
                'task_type': 'keyword_search',
                'keyword': keyword,
                'year': year,
                'search_results': search_results,
                'total_results': len(search_results),
                'crawled_at': datetime.now().isoformat()
            }
        else:
            logger.warning(f"关键词任务 {task_id} 完成，但未获取到任何搜索结果")
            return None
    
    def submit_result(self, task_id, result):
        """提交任务结果"""
        try:
            response = self.session.post(
                f"{self.master_url}/results/submit",
                json={
                    'worker_id': self.worker_id,
                    'task_id': task_id,
                    'result': result
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"任务 {task_id} 结果提交成功")
                return True
            else:
                logger.warning(f"任务结果提交失败，状态码: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"提交结果时网络错误: {e}")
            return False
    
    def send_heartbeat(self):
        """发送心跳信号"""
        try:
            response = self.session.post(
                f"{self.master_url}/workers/heartbeat",
                json={'worker_id': self.worker_id},
                timeout=5
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.warning(f"心跳发送失败，状态码: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"心跳发送网络错误: {e}")
            return False
    
    def process_tasks_batch(self):
        """批量处理任务"""
        futures = []
        
        # 一次获取多个任务
        for _ in range(3):  # 每次处理3个任务
            task = self.get_task()
            if task:
                future = self.task_executor.submit(self.process_single_task, task)
                futures.append(future)
            else:
                break
        
        # 等待所有任务完成
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"任务处理异常: {e}")
    
    def process_single_task(self, task):
        """处理单个任务"""
        task_id = task.get('id')
        
        # 检查任务ID是否有效
        if not task_id:
            logger.warning(f"无效任务数据: task_id={task_id}")
            self.stats['tasks_failed'] += 1
            return
        
        # 判断任务类型并处理
        if 'url' in task:
            # URL爬取任务
            url = task.get('url')
            method = task.get('method', 'traditional')
            
            logger.info(f"开始处理URL爬取任务 {task_id}: {url}")
            
            # 爬取URL
            result = self.crawl_url(url, method)
            
            if result:
                # 添加任务类型信息
                result['task_type'] = 'url_crawl'
                
                # 提交结果
                success = self.submit_result(task_id, result)
                if success:
                    self.stats['tasks_completed'] += 1
                    logger.info(f"URL爬取任务 {task_id} 完成并提交成功")
                else:
                    self.stats['tasks_failed'] += 1
                    logger.error(f"URL爬取任务 {task_id} 完成但提交失败")
            else:
                self.stats['tasks_failed'] += 1
                logger.error(f"URL爬取任务 {task_id} 爬取失败")
                
        elif 'keyword' in task:
            # 关键词搜索任务
            keyword = task.get('keyword')
            year = task.get('year')
            
            logger.info(f"开始处理关键词搜索任务 {task_id}: 关键词='{keyword}', 年份={year}")
            
            # 处理关键词搜索任务
            result = self.process_keyword_task(task)
            
            if result:
                # 提交结果
                success = self.submit_result(task_id, result)
                if success:
                    self.stats['tasks_completed'] += 1
                    logger.info(f"关键词搜索任务 {task_id} 完成并提交成功")
                else:
                    self.stats['tasks_failed'] += 1
                    logger.error(f"关键词搜索任务 {task_id} 完成但提交失败")
            else:
                self.stats['tasks_failed'] += 1
                logger.error(f"关键词搜索任务 {task_id} 处理失败")
        else:
            # 未知任务类型
            logger.warning(f"未知任务类型: task_id={task_id}, 任务数据: {task}")
            self.stats['tasks_failed'] += 1
            return
        
        # 更新成功率统计
        total = self.stats['tasks_completed'] + self.stats['tasks_failed']
        if total > 0:
            self.stats['success_rate'] = self.stats['tasks_completed'] / total
    
    def run(self):
        """主运行循环"""
        logger.info(f"优化版工作节点 {self.worker_id} 启动")
        
        last_heartbeat = time.time()
        
        while self.running:
            try:
                # 发送心跳（每30秒一次）
                current_time = time.time()
                if current_time - last_heartbeat > 30:
                    self.send_heartbeat()
                    last_heartbeat = current_time
                
                # 批量处理任务
                self.process_tasks_batch()
                
                # 如果没有任务，等待一段时间
                time.sleep(2)
                
                # 每处理10个任务打印一次统计信息
                if self.stats['tasks_completed'] % 10 == 0 and self.stats['tasks_completed'] > 0:
                    logger.info(f"统计信息: 完成 {self.stats['tasks_completed']} 个任务, "
                               f"失败 {self.stats['tasks_failed']} 个任务, "
                               f"成功率 {self.stats['success_rate']:.2%}")
                
            except KeyboardInterrupt:
                logger.info("收到中断信号，停止工作节点")
                self.running = False
            except Exception as e:
                logger.error(f"工作节点运行异常: {e}")
                time.sleep(5)  # 异常后等待5秒再继续
        
        # 清理资源
        self.task_executor.shutdown(wait=True)
        logger.info(f"工作节点 {self.worker_id} 停止")

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        worker_id = sys.argv[1]
    else:
        worker_id = f"optimized-worker-{int(time.time())}"
    
    worker = OptimizedWorker(worker_id)
    
    try:
        worker.run()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")

if __name__ == "__main__":
    main()