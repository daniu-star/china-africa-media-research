#!/usr/bin/env python3
"""
分布式爬虫系统启动脚本
支持启动主节点和工作节点
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path

def start_master():
    """启动主节点"""
    print("启动分布式爬虫主节点（修复版）...")
    
    # 设置环境变量
    env = os.environ.copy()
    
    # 启动修复版主节点
    master_process = subprocess.Popen([
        sys.executable, "distributed_master_fixed.py"
    ], env=env, cwd=os.getcwd())
    
    print(f"主节点启动成功，PID: {master_process.pid}")
    return master_process

def start_worker(worker_id=None, max_threads=3):
    """启动工作节点"""
    if worker_id:
        print(f"启动工作节点 {worker_id}（修复版）...")
    else:
        print("启动工作节点（修复版）...")
    
    # 设置环境变量
    env = os.environ.copy()
    if worker_id:
        env['WORKER_ID'] = worker_id
    if max_threads:
        env['MAX_THREADS'] = str(max_threads)
    
    # 启动修复版工作节点
    worker_process = subprocess.Popen([
        sys.executable, "distributed_worker_fixed.py"
    ], env=env, cwd=os.getcwd())
    
    print(f"工作节点启动成功，PID: {worker_process.pid}")
    return worker_process

def start_system():
    """启动完整的分布式爬虫系统"""
    print("=" * 60)
    print("分布式爬虫系统启动")
    print("=" * 60)
    
    processes = []
    
    try:
        # 启动主节点
        master_process = start_master()
        processes.append(master_process)
        
        # 等待主节点启动
        print("等待主节点启动...")
        time.sleep(5)
        
        # 启动3个工作节点
        for i in range(3):
            worker_process = start_worker(f"worker-{i+1}", max_threads=2)
            processes.append(worker_process)
            time.sleep(2)  # 间隔启动
        
        print("\n分布式爬虫系统启动完成！")
        print("主节点: http://localhost:8000")
        print("工作节点监控: http://localhost:5000")
        print("\n按 Ctrl+C 停止系统")
        
        # 等待所有进程
        for process in processes:
            process.wait()
            
    except KeyboardInterrupt:
        print("\n正在停止系统...")
        
        # 终止所有进程
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        
        print("系统已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        
        # 终止所有进程
        for process in processes:
            try:
                process.terminate()
            except:
                pass

def start_master_only():
    """仅启动主节点"""
    print("启动主节点...")
    
    master_process = start_master()
    
    print("\n主节点启动完成！")
    print("访问: http://localhost:8000")
    print("\n按 Ctrl+C 停止主节点")
    
    try:
        master_process.wait()
    except KeyboardInterrupt:
        print("\n正在停止主节点...")
        master_process.terminate()
        master_process.wait()
        print("主节点已停止")

def start_workers_only(count=3):
    """仅启动工作节点"""
    print(f"启动 {count} 个工作节点...")
    
    processes = []
    
    try:
        for i in range(count):
            worker_process = start_worker(f"worker-{i+1}", max_threads=2)
            processes.append(worker_process)
            time.sleep(1)
        
        print(f"\n{count} 个工作节点启动完成！")
        print("\n按 Ctrl+C 停止工作节点")
        
        # 等待所有进程
        for process in processes:
            process.wait()
            
    except KeyboardInterrupt:
        print("\n正在停止工作节点...")
        
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        
        print("工作节点已停止")

def show_help():
    """显示帮助信息"""
    print("""
分布式爬虫系统启动脚本

使用方法:
    python start_system.py [选项]

选项:
    --full       启动完整系统（主节点 + 3个工作节点）
    --master     仅启动主节点
    --workers    仅启动工作节点（默认3个）
    --count N    指定工作节点数量（与--workers一起使用）
    --help       显示此帮助信息

示例:
    python start_system.py --full          # 启动完整系统
    python start_system.py --master        # 仅启动主节点
    python start_system.py --workers       # 启动3个工作节点
    python start_system.py --workers --count 5  # 启动5个工作节点
    """)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='分布式爬虫系统启动脚本')
    parser.add_argument('--full', action='store_true', help='启动完整系统')
    parser.add_argument('--master', action='store_true', help='仅启动主节点')
    parser.add_argument('--workers', action='store_true', help='仅启动工作节点')
    parser.add_argument('--count', type=int, default=3, help='工作节点数量')
    
    args = parser.parse_args()
    
    if args.full:
        start_system()
    elif args.master:
        start_master_only()
    elif args.workers:
        start_workers_only(args.count)
    else:
        show_help()