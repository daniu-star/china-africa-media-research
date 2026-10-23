#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分布式爬虫系统实时监控器
实时显示爬虫进度、数据更新状态和系统运行情况
"""

import os
import json
import time
import psutil
import threading
from datetime import datetime
from pathlib import Path

def get_file_size(file_path):
    """获取文件大小，返回MB格式"""
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    return 0

def get_file_lines(file_path):
    """获取文件行数"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except:
            return 0
    return 0

def get_file_mod_time(file_path):
    """获取文件最后修改时间"""
    if os.path.exists(file_path):
        mod_time = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mod_time)
    return None

def get_task_stats():
    """获取任务统计信息"""
    data_dir = Path("data")
    task_files = list(data_dir.glob("tasks_*.json"))
    
    total_tasks = 0
    pending_tasks = 0
    completed_tasks = 0
    failed_tasks = 0
    
    for task_file in task_files:
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        task = json.loads(line)
                        total_tasks += 1
                        if task.get('status') == 'completed':
                            completed_tasks += 1
                        elif task.get('status') == 'failed':
                            failed_tasks += 1
                        else:
                            pending_tasks += 1
        except:
            continue
    
    return {
        'total': total_tasks,
        'pending': pending_tasks,
        'completed': completed_tasks,
        'failed': failed_tasks,
        'progress': round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0
    }

def get_system_status():
    """获取系统运行状态"""
    # 检查主节点进程
    master_running = False
    worker_count = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and 'distributed_master.py' in ' '.join(cmdline):
                master_running = True
            elif cmdline and 'distributed_worker.py' in ' '.join(cmdline):
                worker_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return {
        'master_running': master_running,
        'worker_count': worker_count,
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent
    }

def display_status():
    """显示系统状态"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("🚀 分布式爬虫系统实时监控")
    print("=" * 60)
    
    # 系统状态
    system_status = get_system_status()
    print(f"📊 系统状态: {'✅ 运行中' if system_status['master_running'] else '❌ 停止'}")
    print(f"👥 工作节点: {system_status['worker_count']} 个")
    print(f"💻 CPU使用率: {system_status['cpu_percent']}%")
    print(f"🧠 内存使用率: {system_status['memory_percent']}%")
    print()
    
    # 数据文件状态
    result_files = ["c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\data\\results_0.json.backup", "data/results_1.json"]
    for file_path in result_files:
        if os.path.exists(file_path):
            mod_time = get_file_mod_time(file_path)
            size_mb = get_file_size(file_path)
            lines = get_file_lines(file_path)
            time_diff = datetime.now() - mod_time if mod_time else None
            hours_diff = round(time_diff.total_seconds() / 3600, 2) if time_diff else None
            
            print(f"📁 {os.path.basename(file_path)}:")
            print(f"   大小: {size_mb} MB, 行数: {lines:,}")
            print(f"   最后更新: {mod_time.strftime('%Y-%m-%d %H:%M:%S') if mod_time else 'N/A'}")
            print(f"   距离现在: {hours_diff} 小时")
            print(f"   状态: {'🟢 正常更新' if hours_diff and hours_diff < 0.5 else '🟡 更新缓慢' if hours_diff and hours_diff < 2 else '🔴 停止更新'}")
            print()
    
    # 任务统计
    task_stats = get_task_stats()
    print(f"📋 任务统计:")
    print(f"   总任务数: {task_stats['total']:,}")
    print(f"   已完成: {task_stats['completed']:,} ({task_stats['progress']}%)")
    print(f"   待处理: {task_stats['pending']:,}")
    print(f"   失败: {task_stats['failed']:,}")
    print()
    
    # 进度条
    progress_bar_length = 30
    completed_blocks = int(task_stats['progress'] / 100 * progress_bar_length)
    progress_bar = "🟩" * completed_blocks + "⬜" * (progress_bar_length - completed_blocks)
    print(f"📈 总体进度: [{progress_bar}] {task_stats['progress']}%")
    print()
    
    print(f"⏰ 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def main():
    """主函数"""
    print("启动分布式爬虫系统实时监控...")
    print("按 Ctrl+C 停止监控")
    time.sleep(2)
    
    try:
        while True:
            display_status()
            time.sleep(10)  # 每10秒更新一次
    except KeyboardInterrupt:
        print("\n监控已停止")

if __name__ == "__main__":
    main()