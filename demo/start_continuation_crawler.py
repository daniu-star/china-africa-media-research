#!/usr/bin/env python3
"""
断点续爬启动脚本
从results_3.json的断点继续爬取，将新数据保存到results_4.json
优化代理池和反爬虫策略，确保系统稳定运行
"""

import os
import sys
import time
import subprocess
import threading
import json
from pathlib import Path
import requests

def check_results_progress():
    """检查当前爬取进度"""
    print("\n=== 检查爬取进度 ===")
    
    results_dir = Path("data/results")
    if not results_dir.exists():
        print("❌ 结果目录不存在，将从头开始爬取")
        return 0
    
    # 查找最新的results文件
    results_files = list(results_dir.glob("results_*.json"))
    if not results_files:
        print("❌ 未找到结果文件，将从头开始爬取")
        return 0
    
    # 按文件名排序
    results_files.sort(key=lambda x: int(x.stem.split('_')[1]) if x.stem.split('_')[1].isdigit() else 0)
    latest_file = results_files[-1]
    
    print(f"📊 最新结果文件: {latest_file.name}")
    
    # 统计已完成任务数
    completed_tasks = 0
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line.strip())
                        if isinstance(data, dict) and data.get('status') == 'completed':
                            completed_tasks += 1
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"❌ 读取结果文件失败: {e}")
        return 0
    
    print(f"✅ 已完成任务数: {completed_tasks}")
    
    # 检查待处理任务
    tasks_dir = Path("data")
    pending_tasks = 0
    for task_file in tasks_dir.glob("tasks_*.json"):
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
                # 尝试解析为JSON对象
                try:
                    data = json.loads(content)
                    if isinstance(data, dict) and 'tasks' in data:
                        for task in data['tasks']:
                            if isinstance(task, dict) and task.get('status') == 'pending':
                                pending_tasks += 1
                    elif isinstance(data, list):
                        for task in data:
                            if isinstance(task, dict) and task.get('status') == 'pending':
                                pending_tasks += 1
                except json.JSONDecodeError:
                    # 按行解析
                    for line in content.split('\n'):
                        if line.strip():
                            try:
                                task_data = json.loads(line.strip())
                                if isinstance(task_data, dict) and task_data.get('status') == 'pending':
                                    pending_tasks += 1
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            print(f"❌ 读取任务文件 {task_file.name} 失败: {e}")
    
    print(f"📋 待处理任务数: {pending_tasks}")
    
    if pending_tasks == 0:
        print("✅ 所有任务已完成，无需继续爬取")
        return -1
    
    return pending_tasks

def start_worker_optimized(worker_id, max_threads=5):
    """启动优化的工作节点"""
    print(f"启动优化工作节点 {worker_id}...")
    
    # 使用优化的环境变量配置
    env = os.environ.copy()
    env['WORKER_ID'] = worker_id
    env['MAX_THREADS'] = str(max_threads)
    env['HEARTBEAT_INTERVAL'] = '30'
    env['REQUEST_TIMEOUT'] = '60'
    env['MAX_RETRY_ATTEMPTS'] = '5'
    env['CONNECTION_TIMEOUT'] = '45'
    env['MAX_CONNECTION_RETRIES'] = '3'
    env['CONNECTION_POOL_SIZE'] = '10'
    env['POOL_BLOCK'] = 'False'
    
    # 使用优化的代理池和反爬虫配置
    env['PROXY_ROTATION_INTERVAL'] = '60'  # 代理轮换间隔60秒
    env['ANTI_CRAWLER_ENABLED'] = 'True'
    env['HUMAN_BEHAVIOR_SIMULATION'] = 'True'
    env['HEADER_ROTATION_ENABLED'] = 'True'
    
    # 使用127.0.0.1避免DNS问题
    env['MASTER_URL'] = 'http://127.0.0.1:8000'
    
    # 启动优化的工作节点
    process = subprocess.Popen([
        sys.executable, "distributed_worker_fixed.py"
    ], env=env, cwd=os.getcwd())
    
    print(f"✅ 工作节点 {worker_id} 启动成功，PID: {process.pid}")
    return process

def check_master_availability():
    """检查主节点是否可用"""
    print("检查主节点可用性...")
    
    for attempt in range(5):
        try:
            response = requests.get('http://127.0.0.1:8000/health', timeout=10)
            if response.status_code == 200:
                print("✅ 主节点运行正常")
                return True
        except Exception as e:
            print(f"❌ 主节点检查失败 (尝试 {attempt + 1}/5): {e}")
            if attempt < 4:
                time.sleep(3)
    
    print("❌ 无法连接到主节点，请确保主节点正在运行")
    return False

def monitor_workers(processes):
    """监控工作节点状态"""
    print("\n=== 工作节点监控开始 ===")
    
    while True:
        active_count = sum(1 for p in processes if p.poll() is None)
        print(f"[{time.strftime('%H:%M:%S')}] 活跃工作节点: {active_count}/{len(processes)}")
        
        # 检查是否有节点停止
        for i, process in enumerate(processes):
            if process.poll() is not None:
                print(f"⚠️  工作节点 {i+1} 已停止，尝试重新启动...")
                new_process = start_worker_optimized(f"worker-continuation-{i+1}")
                processes[i] = new_process
        
        time.sleep(30)

def main():
    """主函数"""
    print("=" * 70)
    print("断点续爬系统 - 从results_3.json继续爬取，保存到results_4.json")
    print("=" * 70)
    
    # 检查爬取进度
    pending_tasks = check_results_progress()
    
    if pending_tasks == -1:
        print("\n✅ 所有任务已完成，无需继续爬取")
        return
    
    if pending_tasks == 0:
        print("\n❌ 未找到待处理任务，请检查任务文件")
        return
    
    print(f"\n📊 预计需要处理 {pending_tasks} 个任务")
    
    # 检查主节点可用性
    if not check_master_availability():
        print("请先启动主节点: python distributed_master_fixed.py")
        return
    
    # 启动优化的工作节点
    processes = []
    
    print("\n=== 启动优化工作节点 ===")
    
    # 根据任务数量动态调整工作节点数量
    worker_count = min(6, max(3, pending_tasks // 100 + 1))
    
    for i in range(worker_count):
        worker_id = f"worker-continuation-{i+1}"
        process = start_worker_optimized(worker_id)
        processes.append(process)
        
        # 间隔启动，避免同时连接造成压力
        if i < worker_count - 1:
            time.sleep(5)
    
    print(f"\n✅ 成功启动 {len(processes)} 个优化工作节点")
    
    # 启动监控线程
    monitor_thread = threading.Thread(target=monitor_workers, args=(processes,), daemon=True)
    monitor_thread.start()
    
    print("\n=== 断点续爬系统运行状态 ===")
    print("主节点: http://127.0.0.1:8000")
    print(f"工作节点数量: {worker_count}")
    print("每个节点并行爬虫: 5")
    print(f"总并行爬虫数: {worker_count * 5}")
    print("数据保存到: results_4.json")
    print("优化特性: 智能代理轮换、反爬虫规避、人类行为模拟")
    print("\n系统正在稳定运行中...")
    print("按 Ctrl+C 停止所有工作节点")
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n正在停止所有工作节点...")
        
        for i, process in enumerate(processes):
            if process.poll() is None:
                process.terminate()
                print(f"已停止工作节点 {i+1}")
        
        print("所有工作节点已停止")

if __name__ == "__main__":
    main()