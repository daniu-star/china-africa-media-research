#!/usr/bin/env python3
"""
分布式爬虫节点实时监控脚本
为每个工作节点创建独立的监控视图
"""

import os
import time
import threading
import subprocess
import sys
import argparse
from datetime import datetime

def monitor_worker_node(worker_id, log_file="distributed_worker.log"):
    """监控单个工作节点的日志"""
    print(f"=== 工作节点 {worker_id} 监控视图 ===")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # 持续监控该工作节点的日志
    while True:
        try:
            # 使用grep命令过滤特定工作节点的日志
            cmd = f"grep '{worker_id}' {log_file} | tail -10"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {worker_id} 最新动态:")
                print(result.stdout)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 等待 {worker_id} 的活动...")
            
            time.sleep(5)  # 每5秒更新一次
            
        except KeyboardInterrupt:
            print(f"\n=== 停止监控工作节点 {worker_id} ===")
            break
        except Exception as e:
            print(f"监控错误: {e}")
            time.sleep(10)

def monitor_master_node():
    """监控主节点状态"""
    print("=== 主节点监控视图 ===")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    while True:
        try:
            # 检查主节点日志
            cmd = "tail -5 distributed_master.log"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 主节点状态:")
                print(result.stdout)
            
            # 检查主节点API状态
            api_cmd = "curl -s http://localhost:8000/ | head -3"
            api_result = subprocess.run(api_cmd, shell=True, capture_output=True, text=True)
            
            if api_result.returncode == 0:
                print(f"主节点API: 正常运行")
            else:
                print(f"主节点API: 连接失败")
            
            time.sleep(10)  # 每10秒更新一次
            
        except KeyboardInterrupt:
            print("\n=== 停止监控主节点 ===")
            break
        except Exception as e:
            print(f"主节点监控错误: {e}")
            time.sleep(10)

def get_active_workers():
    """获取当前活跃的工作节点列表"""
    try:
        cmd = "grep 'worker-' distributed_worker.log | grep '已向主节点注册' | tail -10 | awk '{print $NF}' | sort -u"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            workers = [w.strip() for w in result.stdout.split('\n') if w.strip()]
            return workers
    except Exception as e:
        print(f"获取活跃工作节点错误: {e}")
    
    return []

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='分布式爬虫节点监控器')
    parser.add_argument('--worker', type=str, help='指定要监控的工作节点ID')
    parser.add_argument('--master', action='store_true', help='监控主节点')
    parser.add_argument('--all', action='store_true', help='监控所有节点')
    parser.add_argument('--interval', type=int, default=5, help='监控更新间隔（秒）')
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_arguments()
    
    print("分布式爬虫系统节点监控器")
    print("=" * 50)
    
    # 获取当前活跃的工作节点
    active_workers = get_active_workers()
    
    if args.worker:
        # 监控特定工作节点
        if args.worker in active_workers:
            print(f"开始监控工作节点: {args.worker}")
            monitor_worker_node(args.worker)
        else:
            print(f"工作节点 {args.worker} 未找到或未注册")
    
    elif args.master:
        # 只监控主节点
        print("开始监控主节点")
        monitor_master_node()
    
    elif args.all:
        # 监控所有节点
        if not active_workers:
            print("未找到活跃的工作节点，请检查系统状态")
            return
        
        print(f"发现 {len(active_workers)} 个活跃工作节点:")
        for i, worker in enumerate(active_workers, 1):
            print(f"{i}. {worker}")
        
        # 监控所有节点
        threads = []
        
        # 启动主节点监控线程
        master_thread = threading.Thread(target=monitor_master_node)
        master_thread.daemon = True
        threads.append(master_thread)
        master_thread.start()
        
        # 启动工作节点监控线程
        for worker in active_workers:
            thread = threading.Thread(target=monitor_worker_node, args=(worker,))
            thread.daemon = True
            threads.append(thread)
            thread.start()
        
        print("\n监控已启动，按 Ctrl+C 停止所有监控")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在停止所有监控...")
    
    else:
        # 交互式模式
        if not active_workers:
            print("未找到活跃的工作节点，请检查系统状态")
            return
        
        print(f"发现 {len(active_workers)} 个活跃工作节点:")
        for i, worker in enumerate(active_workers, 1):
            print(f"{i}. {worker}")
        
        print("\n选择监控模式:")
        print("1. 监控所有节点（综合视图）")
        print("2. 监控特定节点")
        print("3. 监控主节点")
        
        choice = input("请输入选择 (1-3): ").strip()
        
        if choice == "1":
            # 监控所有节点
            threads = []
            
            # 启动主节点监控线程
            master_thread = threading.Thread(target=monitor_master_node)
            master_thread.daemon = True
            threads.append(master_thread)
            master_thread.start()
            
            # 启动工作节点监控线程
            for worker in active_workers:
                thread = threading.Thread(target=monitor_worker_node, args=(worker,))
                thread.daemon = True
                threads.append(thread)
                thread.start()
            
            print("\n监控已启动，按 Ctrl+C 停止所有监控")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n正在停止所有监控...")
        
        elif choice == "2":
            # 监控特定节点
            print("\n选择要监控的节点:")
            for i, worker in enumerate(active_workers, 1):
                print(f"{i}. {worker}")
            
            worker_choice = input("请输入节点编号: ").strip()
            
            try:
                index = int(worker_choice) - 1
                if 0 <= index < len(active_workers):
                    monitor_worker_node(active_workers[index])
                else:
                    print("无效的选择")
            except ValueError:
                print("请输入有效的数字")
        
        elif choice == "3":
            # 只监控主节点
            monitor_master_node()
        
        else:
            print("无效的选择")

if __name__ == "__main__":
    main()