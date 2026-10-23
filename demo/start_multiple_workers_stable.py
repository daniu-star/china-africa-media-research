#!/usr/bin/env python3
"""
稳定启动多个工作节点
"""

import subprocess
import time
import sys
import os

def start_workers(num_workers=4):
    """启动指定数量的工作节点"""
    
    print(f"=== 启动 {num_workers} 个工作节点 ===")
    
    processes = []
    
    for i in range(num_workers):
        try:
            # 使用subprocess启动工作节点
            process = subprocess.Popen(
                [sys.executable, "distributed_worker.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            processes.append(process)
            print(f"工作节点 {i+1} 已启动 (PID: {process.pid})")
            
            # 短暂延迟以避免端口冲突
            time.sleep(2)
            
        except Exception as e:
            print(f"启动工作节点 {i+1} 失败: {e}")
    
    print(f"\n成功启动 {len(processes)} 个工作节点")
    
    # 监控进程状态
    print("\n监控工作节点状态...")
    
    for i, process in enumerate(processes):
        try:
            # 检查进程是否仍在运行
            if process.poll() is None:
                print(f"工作节点 {i+1} (PID: {process.pid}) - 运行中")
            else:
                print(f"工作节点 {i+1} (PID: {process.pid}) - 已退出 (代码: {process.returncode})")
                
                # 获取错误输出
                stdout, stderr = process.communicate()
                if stderr:
                    print(f"错误信息: {stderr[:200]}...")
        except Exception as e:
            print(f"检查工作节点 {i+1} 状态失败: {e}")
    
    return processes

def check_system_status():
    """检查系统状态"""
    
    print("\n=== 系统状态检查 ===")
    
    # 检查主节点
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=30)  # 增加超时到30秒
        if response.status_code == 200:
            print("主节点: 运行正常")
        else:
            print(f"主节点: 异常 (状态码: {response.status_code})")
    except Exception as e:
        print(f"主节点: 无法连接 - {e}")
    
    # 检查数据目录
    if os.path.exists("data"):
        data_files = [f for f in os.listdir("data") if f.startswith("results")]
        print(f"数据文件: {len(data_files)} 个结果文件")
    
    # 检查任务队列
    if os.path.exists("data/tasks_expanded_0.json"):
        import json
        with open("data/tasks_expanded_0.json", 'r', encoding='utf-8') as f:
            tasks = json.load(f)
            if 'tasks' in tasks:
                completed = sum(1 for task in tasks['tasks'] if task.get('status') == 'completed')
                total = len(tasks['tasks'])
                print(f"任务队列: {completed}/{total} 已完成 ({completed/total*100:.1f}%)")

def main():
    """主函数"""
    
    print("分布式爬虫系统 - 稳定启动")
    print("=" * 50)
    
    # 解析命令行参数
    num_workers = 4  # 默认启动4个工作节点
    if len(sys.argv) > 1 and sys.argv[1] == "--workers":
        try:
            num_workers = int(sys.argv[2])
        except (IndexError, ValueError):
            print("错误: 请提供有效的工人数量，例如 --workers 6")
            sys.exit(1)
    
    # 检查系统状态
    check_system_status()
    
    # 启动工作节点
    processes = start_workers(num_workers)
    
    print(f"\n=== 启动完成 ===")
    print(f"总工作节点数: {len(processes)}")
    print("系统正在运行中...")
    print("按 Ctrl+C 停止所有工作节点")
    
    try:
        # 保持运行状态
        while True:
            time.sleep(10)
            
            # 定期检查进程状态
            running_count = sum(1 for p in processes if p.poll() is None)
            if running_count < num_workers:
                print(f"警告: {num_workers - running_count} 个工作节点已停止")
                # 重新启动停止的节点
                for i, process in enumerate(processes):
                    if process.poll() is not None:
                        print(f"重新启动工作节点 {i+1}...")
                        try:
                            new_process = subprocess.Popen(
                                [sys.executable, "distributed_worker.py"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                bufsize=1,
                                universal_newlines=True
                            )
                            processes[i] = new_process
                            print(f"工作节点 {i+1} 重新启动成功 (PID: {new_process.pid})")
                            time.sleep(2)
                        except Exception as e:
                            print(f"重新启动工作节点 {i+1} 失败: {e}")
                            
    except KeyboardInterrupt:
        print("\n正在停止所有工作节点...")
        
        # 停止所有进程
        for i, process in enumerate(processes):
            if process.poll() is None:
                process.terminate()
                print(f"工作节点 {i+1} 已停止")
        
        print("所有工作节点已停止")

if __name__ == "__main__":
    main()