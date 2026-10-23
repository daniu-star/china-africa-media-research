#!/usr/bin/env python3
"""
分布式爬虫系统 - 修复版启动脚本
专门解决Windows网络连接问题（WinError 64）
"""

import os
import sys
import time
import subprocess
import signal
import threading
from datetime import datetime
import psutil

# 配置
MASTER_URL = "http://127.0.0.1:8000"
NUM_WORKERS = 6
WORKER_PREFIX = "worker-fixed"

# 环境变量配置
ENV_VARS = {
    'MASTER_URL': MASTER_URL,
    'CONNECTION_POOL_SIZE': '10',
    'POOL_BLOCK': 'False',
    'REQUEST_TIMEOUT': '60',
    'HEARTBEAT_INTERVAL': '30',
    'TASK_PROCESSING_TIME': '5',
    'MAX_RETRY_ATTEMPTS': '3',
    'RETRY_DELAY_BASE': '5',
    'RETRY_DELAY_MAX': '60'
}

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        self.processes = {}
        self.monitoring = False
        self.health_check_thread = None
        
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        self.health_check_thread = threading.Thread(target=self._health_check_loop)
        self.health_check_thread.daemon = True
        self.health_check_thread.start()
        
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
    
    def _health_check_loop(self):
        """健康检查循环"""
        while self.monitoring:
            try:
                self.check_system_health()
                time.sleep(30)  # 每30秒检查一次
            except Exception as e:
                print(f"健康检查错误: {e}")
    
    def check_system_health(self):
        """检查系统健康状态"""
        print("\n=== 系统健康检查 ===")
        
        # 检查主节点
        master_status = self.check_process_health('master')
        print(f"主节点状态: {'运行中' if master_status else '已停止'}")
        
        # 检查工作节点
        active_workers = 0
        for i in range(NUM_WORKERS):
            worker_id = f"{WORKER_PREFIX}-{i+1}"
            if self.check_process_health(worker_id):
                active_workers += 1
        
        print(f"活跃工作节点: {active_workers}/{NUM_WORKERS}")
        
        # 检查系统资源
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        
        print(f"CPU使用率: {cpu_percent:.1f}%")
        print(f"内存使用率: {memory_info.percent:.1f}%")
        
        # 检查端口占用
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 8000))
            sock.close()
            print(f"主节点端口状态: {'已占用' if result == 0 else '空闲'}")
        except:
            print("端口检查失败")
        
        print("=== 检查完成 ===\n")
    
    def check_process_health(self, process_type: str) -> bool:
        """检查进程健康状态"""
        if process_type not in self.processes:
            return False
        
        process = self.processes[process_type]
        if process.poll() is None:  # 进程仍在运行
            return True
        
        return False

def start_master():
    """启动主节点"""
    print("启动主节点...")
    
    # 检查端口是否被占用
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()
        
        if result == 0:
            print("端口8000已被占用，尝试终止现有进程...")
            # 查找并终止占用端口的进程
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    for conn in proc.connections(kind='inet'):
                        if conn.laddr.port == 8000:
                            print(f"终止进程 {proc.info['name']} (PID: {proc.info['pid']})")
                            proc.terminate()
                            proc.wait(timeout=5)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 等待端口释放
            time.sleep(2)
    except Exception as e:
        print(f"端口检查失败: {e}")
    
    # 启动主节点
    try:
        master_process = subprocess.Popen(
            [sys.executable, "distributed_master_fixed.py"],
            env={**os.environ, **ENV_VARS},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待主节点启动
        print("等待主节点启动...")
        time.sleep(5)
        
        # 检查主节点是否成功启动
        if master_process.poll() is not None:
            stdout, stderr = master_process.communicate()
            print(f"主节点启动失败:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return None
        
        print("主节点启动成功")
        return master_process
        
    except Exception as e:
        print(f"主节点启动失败: {e}")
        return None

def start_workers(monitor):
    """启动工作节点"""
    print(f"启动 {NUM_WORKERS} 个工作节点...")
    
    worker_processes = {}
    
    for i in range(NUM_WORKERS):
        worker_id = f"{WORKER_PREFIX}-{i+1}"
        print(f"启动工作节点 {worker_id}...")
        
        try:
            # 为每个工作节点设置唯一ID
            worker_env = {**os.environ, **ENV_VARS, 'WORKER_ID': worker_id}
            
            worker_process = subprocess.Popen(
                [sys.executable, "distributed_worker_fixed.py"],
                env=worker_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            worker_processes[worker_id] = worker_process
            monitor.processes[worker_id] = worker_process
            
            # 避免同时启动过多进程
            time.sleep(1)
            
        except Exception as e:
            print(f"工作节点 {worker_id} 启动失败: {e}")
    
    print("所有工作节点启动完成")
    return worker_processes

def check_system_connectivity():
    """检查系统连接性"""
    print("检查系统连接性...")
    
    # 等待系统稳定
    time.sleep(3)
    
    # 检查主节点健康状态
    try:
        import requests
        response = requests.get(f"{MASTER_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✓ 主节点健康检查通过")
            return True
        else:
            print(f"✗ 主节点健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 主节点连接失败: {e}")
        return False

def graceful_shutdown(processes, monitor):
    """优雅关闭系统"""
    print("\n正在关闭系统...")
    
    # 停止监控
    monitor.stop_monitoring()
    
    # 先关闭工作节点
    print("关闭工作节点...")
    for worker_id, process in processes.items():
        if process and process.poll() is None:
            print(f"关闭 {worker_id}...")
            process.terminate()
    
    # 等待工作节点关闭
    time.sleep(3)
    
    # 强制终止未关闭的进程
    for worker_id, process in processes.items():
        if process and process.poll() is None:
            print(f"强制终止 {worker_id}...")
            process.kill()
    
    # 关闭主节点
    if 'master' in monitor.processes:
        master_process = monitor.processes['master']
        if master_process and master_process.poll() is None:
            print("关闭主节点...")
            master_process.terminate()
            master_process.wait(timeout=5)
    
    print("系统关闭完成")

def main():
    """主函数"""
    print("=== 分布式爬虫系统修复版启动 ===")
    print(f"主节点URL: {MASTER_URL}")
    print(f"工作节点数量: {NUM_WORKERS}")
    print(f"工作节点前缀: {WORKER_PREFIX}")
    print("=" * 50)
    
    # 创建系统监控器
    monitor = SystemMonitor()
    
    # 设置信号处理
    def signal_handler(signum, frame):
        print(f"\n接收到信号 {signum}，正在关闭系统...")
        graceful_shutdown({}, monitor)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动主节点
        master_process = start_master()
        if not master_process:
            print("主节点启动失败，系统无法启动")
            return
        
        monitor.processes['master'] = master_process
        
        # 启动工作节点
        worker_processes = start_workers(monitor)
        
        # 开始系统监控
        monitor.start_monitoring()
        
        # 检查系统连接性
        if check_system_connectivity():
            print("\n✓ 系统启动成功！")
            print("系统正在运行中...")
            print("按 Ctrl+C 停止系统")
            
            # 主循环
            while True:
                time.sleep(1)
                
                # 检查主节点是否仍在运行
                if master_process.poll() is not None:
                    print("主节点已停止，系统将关闭")
                    break
                    
        else:
            print("\n✗ 系统连接性检查失败")
            
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n系统错误: {e}")
    finally:
        # 优雅关闭
        graceful_shutdown(worker_processes, monitor)

if __name__ == "__main__":
    main()