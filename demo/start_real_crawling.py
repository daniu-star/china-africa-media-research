#!/usr/bin/env python3
"""
真正的爬取任务启动器
启动分布式爬虫系统并执行实际的数据爬取
"""

import os
import sys
import time
import json
import requests
import subprocess
import threading
from datetime import datetime
from typing import Dict, List, Any

class RealCrawlingStarter:
    def __init__(self):
        self.master_url = "http://127.0.0.1:8000"
        self.data_dir = "data"
        self.tasks_file = os.path.join(self.data_dir, "tasks_0.json")
        
    def check_system_status(self) -> bool:
        """检查系统状态"""
        try:
            response = requests.get(f"{self.master_url}/health", timeout=10)
            if response.status_code == 200:
                print("✓ 主节点运行正常")
                return True
        except Exception as e:
            print(f"✗ 无法连接到主节点: {e}")
            return False
    
    def check_workers_status(self) -> bool:
        """检查工作节点状态"""
        try:
            response = requests.get(f"{self.master_url}/stats", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                active_workers = stats.get('active_workers', 0)
                print(f"✓ 活跃工作节点: {active_workers}")
                return active_workers > 0
        except Exception as e:
            print(f"✗ 无法获取工作节点状态: {e}")
            return False
    
    def load_tasks(self) -> List[Dict[str, Any]]:
        """加载爬取任务"""
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
            
            if isinstance(tasks_data, dict) and 'tasks' in tasks_data:
                tasks = tasks_data['tasks']
            elif isinstance(tasks_data, list):
                tasks = tasks_data
            else:
                tasks = []
            
            print(f"✓ 加载任务数量: {len(tasks)}")
            return tasks
        except Exception as e:
            print(f"✗ 加载任务失败: {e}")
            return []
    
    def start_crawling_tasks(self) -> bool:
        """启动爬取任务"""
        print("🚀 开始启动爬取任务...")
        
        try:
            # 使用主节点的submit-tasks接口自动加载任务
            response = requests.post(f"{self.master_url}/submit-tasks", timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                submitted = result.get('submitted_tasks', 0)
                print(f"✓ 成功提交 {submitted} 个任务")
                
                # 检查任务队列状态
                time.sleep(2)
                response = requests.get(f"{self.master_url}/stats", timeout=10)
                if response.status_code == 200:
                    stats = response.json()
                    queue_size = stats.get('task_queue_size', 0)
                    print(f"📊 当前任务队列大小: {queue_size}")
                
                return True
            else:
                print(f"✗ 提交任务失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ 提交任务异常: {e}")
            return False
    
    def monitor_crawling_progress(self, duration_minutes: int = 30):
        """监控爬取进度"""
        print(f"📊 开始监控爬取进度 ({duration_minutes} 分钟)...")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            try:
                # 检查任务状态
                response = requests.get(f"{self.master_url}/stats", timeout=10)
                if response.status_code == 200:
                    stats = response.json()
                    task_queue_size = stats.get('task_queue_size', 0)
                    results_queue_size = stats.get('results_queue_size', 0)
                    failed_tasks_queue_size = stats.get('failed_tasks_queue_size', 0)
                    
                    # 估算进度（基于队列大小变化）
                    total_tasks = 25  # 初始任务数量
                    processed = total_tasks - task_queue_size
                    progress = (processed / total_tasks * 100) if total_tasks > 0 else 0
                    
                    print(f"📈 进度: {progress:.1f}% | 待处理: {task_queue_size} | 结果队列: {results_queue_size} | 失败任务: {failed_tasks_queue_size}")
                
                # 检查工作节点状态
                response = requests.get(f"{self.master_url}/stats", timeout=10)
                if response.status_code == 200:
                    stats = response.json()
                    active_workers = stats.get('active_workers', 0)
                    print(f"👥 活跃工作节点: {active_workers}")
                
                # 检查新生成的数据文件
                self.check_new_data_files()
                
            except Exception as e:
                print(f"⚠️ 监控异常: {e}")
            
            # 每30秒检查一次
            time.sleep(30)
    
    def check_new_data_files(self):
        """检查新生成的数据文件"""
        results_dir = os.path.join(self.data_dir, "results")
        if os.path.exists(results_dir):
            files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
            if files:
                print(f"📄 结果文件数量: {len(files)}")
                
                # 检查最新文件的内容
                latest_file = max([os.path.join(results_dir, f) for f in files], 
                                key=os.path.getmtime)
                
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        print(f"📊 最新文件包含 {len(data)} 条记录")
                    elif isinstance(data, dict):
                        articles = data.get('articles', [])
                        print(f"📊 最新文件包含 {len(articles)} 篇文章")
                except:
                    pass
    
    def run(self):
        """运行爬取任务启动器"""
        print("=" * 60)
        print("真正的爬取任务启动器")
        print("启动分布式爬虫系统并执行实际数据爬取")
        print("=" * 60)
        
        # 1. 检查系统状态
        print("\n1. 检查系统状态...")
        if not self.check_system_status():
            print("❌ 系统未就绪，请先启动分布式系统")
            return False
        
        if not self.check_workers_status():
            print("❌ 没有活跃的工作节点")
            return False
        
        # 2. 加载任务
        print("\n2. 加载爬取任务...")
        tasks = self.load_tasks()
        if not tasks:
            print("❌ 没有可用的爬取任务")
            return False
        
        # 3. 启动爬取任务
        print("\n3. 启动爬取任务...")
        if not self.start_crawling_tasks():
            print("❌ 启动爬取任务失败")
            return False
        
        # 4. 监控进度
        print("\n4. 监控爬取进度...")
        self.monitor_crawling_progress(duration_minutes=300)
        
        print("\n✅ 爬取任务启动完成")
        return True

def main():
    """主函数"""
    starter = RealCrawlingStarter()
    
    try:
        starter.run()
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断爬取任务")
    except Exception as e:
        print(f"\n\n❌ 爬取任务异常: {e}")

if __name__ == "__main__":
    main()