#!/usr/bin/env python3
"""
专门处理results_5.json任务的爬虫系统
直接与主节点交互，确保非洲本地语言关键词任务能够正确处理
"""

import json
import time
import requests
import logging
from datetime import datetime
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('results5_crawler')

class Results5Crawler:
    def __init__(self, results_file_path="data/results/results_5.json"):
        self.results_file_path = results_file_path
        self.master_url = "http://localhost:8000"
        self.tasks = []
        
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
    
    def check_master_health(self):
        """检查主节点健康状态"""
        try:
            response = requests.get(f"{self.master_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("主节点健康状态正常")
                return True
            else:
                logger.warning(f"主节点健康检查失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"主节点健康检查异常: {e}")
            return False
    
    def submit_task_to_master(self, task):
        """向主节点提交任务"""
        try:
            # 构建任务数据
            task_data = {
                "task_id": task['task_id'],
                "keyword": task['keyword'],
                "year": task['year'],
                "priority": "high"  # 非洲本地语言任务设置为高优先级
            }
            
            response = requests.post(
                f"{self.master_url}/tasks",
                json=task_data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"成功提交任务 {task['task_id']} 到主节点")
                return True
            else:
                logger.warning(f"提交任务 {task['task_id']} 失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"提交任务 {task['task_id']} 异常: {e}")
            return False
    
    def check_task_status(self, task_id):
        """检查任务状态"""
        try:
            response = requests.get(f"{self.master_url}/tasks/{task_id}/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            logger.error(f"检查任务 {task_id} 状态异常: {e}")
            return None
    
    def update_results5_status(self, task_id, status, results=None):
        """更新results_5.json中的任务状态"""
        try:
            with open(self.results_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 更新任务状态
            for task in data:
                if task['task_id'] == task_id:
                    task['status'] = status
                    task['processed_at'] = datetime.now().isoformat()
                    if results:
                        task['results'] = results
                    break
            
            # 保存更新后的数据
            with open(self.results_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"更新任务 {task_id} 状态为 {status}")
            
        except Exception as e:
            logger.error(f"更新results_5.json状态失败: {e}")
    
    def start_worker_for_results5(self):
        """启动专门处理results_5.json任务的工作节点"""
        try:
            # 启动工作节点
            import subprocess
            worker_process = subprocess.Popen([
                'python', 'distributed_worker_fixed.py',
                '--worker-id', 'worker-results5-special',
                '--master-url', self.master_url
            ])
            
            logger.info("启动专门处理results_5.json任务的工作节点")
            return worker_process
            
        except Exception as e:
            logger.error(f"启动工作节点失败: {e}")
            return None
    
    def monitor_progress(self, tasks):
        """监控任务进度"""
        completed_tasks = 0
        total_tasks = len(tasks)
        
        logger.info(f"开始监控 {total_tasks} 个任务的进度")
        
        # 每30秒检查一次进度
        check_interval = 30
        max_wait_time = 3600  # 最大等待1小时
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # 检查每个任务的状态
            for task in tasks:
                if task.get('status') == 'pending':
                    task_status = self.check_task_status(task['task_id'])
                    if task_status and task_status.get('status') == 'completed':
                        # 任务完成，更新状态
                        self.update_results5_status(
                            task['task_id'], 
                            'completed',
                            task_status.get('results', [])
                        )
                        completed_tasks += 1
                        logger.info(f"任务 {task['task_id']} 已完成 ({completed_tasks}/{total_tasks})")
            
            # 检查是否所有任务都已完成
            if completed_tasks >= total_tasks:
                logger.info("所有results_5.json任务已完成!")
                return True
            
            # 等待下一次检查
            logger.info(f"进度: {completed_tasks}/{total_tasks} 任务已完成，等待 {check_interval} 秒后继续检查...")
            time.sleep(check_interval)
        
        logger.warning(f"监控超时，已完成 {completed_tasks}/{total_tasks} 个任务")
        return completed_tasks >= total_tasks
    
    def start_crawling(self):
        """开始爬取results_5.json任务"""
        logger.info("=== 开始处理results_5.json任务 ===")
        
        # 1. 检查主节点状态
        if not self.check_master_health():
            logger.error("主节点不可用，无法继续处理")
            return False
        
        # 2. 加载待处理任务
        tasks = self.load_results5_tasks()
        if not tasks:
            logger.info("没有找到待处理的results_5.json任务")
            return True
        
        # 3. 启动专门的工作节点
        worker_process = self.start_worker_for_results5()
        if not worker_process:
            logger.error("无法启动工作节点")
            return False
        
        # 等待工作节点启动
        logger.info("等待工作节点启动...")
        time.sleep(10)
        
        # 4. 提交所有任务到主节点
        submitted_tasks = 0
        for task in tasks:
            if self.submit_task_to_master(task):
                submitted_tasks += 1
                # 短暂延迟，避免请求过快
                time.sleep(2)
        
        logger.info(f"成功提交 {submitted_tasks}/{len(tasks)} 个任务到主节点")
        
        # 5. 监控任务进度
        success = self.monitor_progress(tasks)
        
        # 6. 清理工作节点
        if worker_process:
            worker_process.terminate()
            logger.info("工作节点已停止")
        
        return success

def main():
    """主函数"""
    crawler = Results5Crawler()
    
    try:
        success = crawler.start_crawling()
        if success:
            logger.info("results_5.json任务处理完成!")
        else:
            logger.error("results_5.json任务处理失败")
    except KeyboardInterrupt:
        logger.info("用户中断处理过程")
    except Exception as e:
        logger.error(f"处理过程中发生异常: {e}")

if __name__ == "__main__":
    main()