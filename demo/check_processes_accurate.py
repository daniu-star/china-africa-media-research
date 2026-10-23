#!/usr/bin/env python3
"""
准确的分布式爬虫系统进程检查脚本
解决进程统计显示为0的问题
"""

import psutil
import os

def find_process_by_commandline(keywords):
    """通过命令行参数查找进程"""
    matching_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline:
                # 将命令行参数列表转换为字符串
                cmdline_str = ' '.join(cmdline)
                # 检查是否包含所有关键词
                if all(keyword in cmdline_str for keyword in keywords):
                    matching_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return matching_processes

def main():
    print("=== 分布式爬虫系统进程检查 ===\n")
    
    # 检查主节点进程
    master_processes = find_process_by_commandline(['distributed_master.py'])
    print(f"主节点进程: {len(master_processes)}个")
    for proc in master_processes:
        print(f"  - PID {proc.info['pid']}: {proc.info['cmdline']}")
    
    # 检查工作节点进程
    worker_processes = find_process_by_commandline(['distributed_worker.py'])
    print(f"\n工作节点进程: {len(worker_processes)}个")
    for proc in worker_processes:
        print(f"  - PID {proc.info['pid']}: {proc.info['cmdline']}")
    
    # 检查修复版启动脚本进程
    fixed_script_processes = find_process_by_commandline(['start_six_workers_fixed.py'])
    print(f"\n修复版启动脚本进程: {len(fixed_script_processes)}个")
    for proc in fixed_script_processes:
        print(f"  - PID {proc.info['pid']}: {proc.info['cmdline']}")
    
    # 统计所有Python进程
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                python_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    print(f"\n总Python进程: {len(python_processes)}个")
    
    # 显示系统状态摘要
    print("\n=== 系统状态摘要 ===")
    print(f"主节点运行状态: {'正常运行' if master_processes else '未运行'}")
    print(f"工作节点数量: {len(worker_processes)}")
    print(f"修复版脚本状态: {'运行中' if fixed_script_processes else '未运行'}")
    print(f"系统整体健康度: {'良好' if master_processes and worker_processes else '异常'}")

if __name__ == "__main__":
    main()