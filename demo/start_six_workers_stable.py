#!/usr/bin/env python3
"""
启动六个工作节点的稳定版本
确保节点连接的稳定性和负载均衡
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path

def start_worker_with_stability(worker_id, max_threads=5):
    """启动一个稳定的工作节点"""
    print(f"启动工作节点 {worker_id}...")
    
    # 设置环境变量确保稳定性
    env = os.environ.copy()
    env['WORKER_ID'] = worker_id
    env['MAX_THREADS'] = str(max_threads)
    env['HEARTBEAT_INTERVAL'] = '30'  # 稳定心跳间隔
    env['REQUEST_TIMEOUT'] = '60'    # 增加超时时间
    env['MAX_RETRY_ATTEMPTS'] = '10'  # 增加重试次数
    env['CONNECTION_TIMEOUT'] = '30'  # 连接超时
    env['MAX_CONNECTION_RETRIES'] = '5'  # 连接重试次数
    
    # 启动工作节点
    process = subprocess.Popen([
        sys.executable, "distributed_worker.py"
    ], env=env, cwd=os.getcwd())
    
    print(f"工作节点 {worker_id} 启动成功，PID: {process.pid}")
    return process

def check_master_availability():
    """检查主节点是否可用"""
    import requests
    
    print("检查主节点可用性...")
    
    for attempt in range(5):
        try:
            response = requests.get('http://localhost:8000/health', timeout=10)
            if response.status_code == 200:
                print("✅ 主节点运行正常")
                return True
        except Exception as e:
            print(f"❌ 主节点检查失败 (尝试 {attempt + 1}/5): {e}")
            if attempt < 4:
                time.sleep(3)  # 等待3秒后重试
    
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
                new_process = start_worker_with_stability(f"worker-{i+1}")
                processes[i] = new_process
        
        time.sleep(30)  # 每30秒检查一次

def main():
    """主函数"""
    print("=" * 60)
    print("分布式爬虫系统 - 启动六个稳定工作节点")
    print("=" * 60)
    
    # 检查主节点可用性
    if not check_master_availability():
        print("请先启动主节点: python distributed_master.py")
        return
    
    # 启动六个工作节点
    processes = []
    
    print("\n=== 启动工作节点 ===")
    
    for i in range(6):
        worker_id = f"worker-six-{i+1}"
        process = start_worker_with_stability(worker_id)
        processes.append(process)
        
        # 间隔启动，避免同时连接造成压力
        if i < 5:  # 最后一个节点不需要等待
            time.sleep(5)
    
    print(f"\n✅ 成功启动 {len(processes)} 个工作节点")
    
    # 启动监控线程
    monitor_thread = threading.Thread(target=monitor_workers, args=(processes,), daemon=True)
    monitor_thread.start()
    
    print("\n=== 系统运行状态 ===")
    print("主节点: http://localhost:8000")
    print("工作节点数量: 6")
    print("每个节点并行爬虫: 5")
    print("总并行爬虫数: 30")
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