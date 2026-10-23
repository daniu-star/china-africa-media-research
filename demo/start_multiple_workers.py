#!/usr/bin/env python3
"""
批量启动多个优化工作节点
"""
import subprocess
import time
import sys
import os

def start_workers(num_workers: int = 5):
    """启动指定数量的工作节点"""
    processes = []
    
    print(f"正在启动 {num_workers} 个工作节点...")
    
    for i in range(1, num_workers + 1):
        worker_id = f"worker-optimized-{i}"
        
        # 使用subprocess启动工作节点
        try:
            process = subprocess.Popen(
                [sys.executable, "optimized_worker.py", worker_id],
                stdout=None,  # 直接输出到控制台
                stderr=None,  # 直接输出到控制台
                text=True
            )
            processes.append((worker_id, process))
            print(f"✓ 启动工作节点: {worker_id} (PID: {process.pid})")
            
            # 短暂延迟以避免同时启动过多进程
            time.sleep(0.5)
            
        except Exception as e:
            print(f"✗ 启动工作节点 {worker_id} 失败: {e}")
    
    print(f"\n成功启动 {len(processes)} 个工作节点")
    print("工作节点正在后台运行...")
    
    # 等待一段时间让工作节点初始化
    print("等待工作节点初始化...")
    time.sleep(3)
    
    # 检查工作节点状态
    print("\n检查工作节点状态:")
    for worker_id, process in processes:
        if process.poll() is None:
            print(f"✓ {worker_id} 运行正常")
        else:
            print(f"✗ {worker_id} 已停止 (退出码: {process.returncode})")
    
    return processes

def main():
    """主函数"""
    # 默认启动5个工作节点
    num_workers = 5
    
    if len(sys.argv) > 1:
        try:
            num_workers = int(sys.argv[1])
        except ValueError:
            print(f"错误: 参数 '{sys.argv[1]}' 不是有效的数字")
            sys.exit(1)
    
    print("=== 分布式爬虫系统 - 批量启动工作节点 ===")
    print(f"目标工作节点数量: {num_workers}")
    print()
    
    processes = start_workers(num_workers)
    
    print(f"\n=== 启动完成 ===")
    print(f"总启动工作节点: {len(processes)}")
    print("\n工作节点将在后台持续运行")
    print("要停止工作节点，请使用任务管理器或Ctrl+C")
    
    # 保持脚本运行，让工作节点继续在后台运行
    try:
        while True:
            time.sleep(10)
            # 定期检查工作节点状态
            active_count = sum(1 for _, p in processes if p.poll() is None)
            if active_count < len(processes):
                print(f"警告: {len(processes) - active_count} 个工作节点已停止")
    except KeyboardInterrupt:
        print("\n正在停止所有工作节点...")
        for worker_id, process in processes:
            if process.poll() is None:
                process.terminate()
                print(f"已停止: {worker_id}")
        print("所有工作节点已停止")

if __name__ == "__main__":
    main()