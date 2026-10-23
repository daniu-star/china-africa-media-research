#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫系统健康检查脚本
"""

import psutil
import os
import json
import time
from datetime import datetime

def check_system_resources():
    """检查系统资源使用情况"""
    print("=== 系统资源检查 ===")
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage(".").percent
    
    print(f"CPU使用率: {cpu_usage}%")
    print(f"内存使用率: {memory_usage}%")
    print(f"磁盘使用率: {disk_usage}%")
    
    # 健康评估
    if cpu_usage > 90:
        print("⚠️ CPU使用率过高")
    elif cpu_usage > 70:
        print("⚠️ CPU使用率较高")
    else:
        print("✅ CPU使用率正常")
        
    if memory_usage > 90:
        print("⚠️ 内存使用率过高")
    elif memory_usage > 80:
        print("⚠️ 内存使用率较高")
    else:
        print("✅ 内存使用率正常")

def check_process_status():
    """检查爬虫进程状态"""
    print("\n=== 进程状态检查 ===")
    
    # 检查中国报道爬虫进程
    china_crawler_running = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'] and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'pyramid_china_crawler' in cmdline:
                    china_crawler_running = True
                    print(f"✅ 中国报道爬虫运行中 (PID: {proc.info['pid']})")
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if not china_crawler_running:
        print("❌ 中国报道爬虫未运行")
    
    # 检查分布式系统进程
    distributed_running = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'] and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'start_system' in cmdline or 'start_multiple_workers' in cmdline:
                    distributed_running = True
                    print(f"✅ 分布式系统运行中 (PID: {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if not distributed_running:
        print("❌ 分布式系统未运行")

def check_data_files():
    """检查数据文件状态"""
    print("\n=== 数据文件检查 ===")
    
    # 检查结果文件
    results_files = []
    for d in ['crawler_results', 'data']:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.endswith(('.json', '.xlsx')):
                    results_files.append(os.path.join(d, f))
    
    print(f"结果文件数: {len(results_files)}")
    
    if results_files:
        latest_file = max(results_files, key=lambda x: os.path.getmtime(x))
        file_size = os.path.getsize(latest_file)
        mtime = datetime.fromtimestamp(os.path.getmtime(latest_file))
        
        print(f"最新文件: {os.path.basename(latest_file)}")
        print(f"文件大小: {file_size} bytes")
        print(f"修改时间: {mtime}")
        
        # 检查文件是否为空
        if file_size < 100:
            print("⚠️ 最新文件可能为空")
        else:
            print("✅ 数据文件正常")
    else:
        print("❌ 未找到结果文件")

def check_task_progress():
    """检查任务进度"""
    print("\n=== 任务进度检查 ===")
    
    task_files = [f for f in os.listdir('data') if f.startswith('tasks_') and f.endswith('.json')]
    print(f"任务文件数: {len(task_files)}")
    
    if task_files:
        total_tasks = 0
        completed_tasks = 0
        
        for tf in task_files:
            try:
                with open(os.path.join('data', tf), 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
                    total_tasks += len(tasks)
                    completed_tasks += sum(1 for task in tasks if task.get('completed', False))
            except Exception as e:
                print(f"读取任务文件 {tf} 时出错: {e}")
        
        print(f"总任务数: {total_tasks}")
        print(f"已完成: {completed_tasks}")
        
        if total_tasks > 0:
            completion_rate = completed_tasks / total_tasks * 100
            print(f"完成率: {completion_rate:.1f}%")
            
            if completion_rate > 90:
                print("✅ 任务进度良好")
            elif completion_rate > 50:
                print("⚠️ 任务进度中等")
            else:
                print("❌ 任务进度较慢")
        else:
            print("❌ 无有效任务")
    else:
        print("❌ 未找到任务文件")

def check_network_connectivity():
    """检查网络连接"""
    print("\n=== 网络连接检查 ===")
    
    try:
        # 检查是否能访问外部网站
        import urllib.request
        urllib.request.urlopen('http://www.baidu.com', timeout=5)
        print("✅ 网络连接正常")
    except Exception as e:
        print(f"❌ 网络连接异常: {e}")

def main():
    """主函数"""
    print("爬虫系统健康检查报告")
    print("=" * 50)
    
    check_system_resources()
    check_process_status()
    check_data_files()
    check_task_progress()
    check_network_connectivity()
    
    print("\n" + "=" * 50)
    print("健康检查完成")

if __name__ == "__main__":
    main()