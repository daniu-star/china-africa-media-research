#!/usr/bin/env python3
"""
优化的分布式爬虫系统启动器
专门解决Windows网络连接问题
"""

import os
import sys
import time
import socket
import subprocess
import threading
import psutil
import requests
from datetime import datetime
import signal
import atexit

class DistributedCrawlerOptimizer:
    def __init__(self):
        self.master_process = None
        self.worker_processes = []
        self.max_workers = 6
        self.master_port = 8000
        self.master_url = f"http://127.0.0.1:{self.master_port}"
        
        # Windows特定的优化参数
        self.windows_optimizations = {
            'socket_timeout': 60,
            'connection_pool_size': 50,
            'max_retries': 3,
            'retry_delay': 2,
            'heartbeat_interval': 30
        }
        
        # 注册退出处理
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """信号处理函数"""
        print(f"\n收到信号 {signum}，正在清理进程...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """清理所有进程"""
        print("正在清理分布式爬虫进程...")
        
        # 终止工作节点进程
        for process in self.worker_processes:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    try:
                        process.kill()
                    except:
                        pass
        
        # 终止主节点进程
        if self.master_process and self.master_process.poll() is None:
            try:
                self.master_process.terminate()
                self.master_process.wait(timeout=5)
            except:
                try:
                    self.master_process.kill()
                except:
                    pass
        
        print("清理完成")
    
    def check_port_availability(self, port):
        """检查端口是否可用"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result != 0
        except:
            return False
    
    def kill_process_on_port(self, port):
        """终止占用端口的进程"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    for conn in proc.info.get('connections', []):
                        if hasattr(conn, 'laddr') and conn.laddr.port == port:
                            print(f"终止占用端口 {port} 的进程: {proc.info['name']} (PID: {proc.info['pid']})")
                            psutil.Process(proc.info['pid']).terminate()
                            time.sleep(1)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            print(f"终止进程失败: {e}")
    
    def wait_for_master_ready(self, timeout=60):
        """等待主节点就绪"""
        print("等待主节点启动...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.master_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✓ 主节点已就绪")
                    return True
            except:
                pass
            
            time.sleep(2)
            print(".", end="", flush=True)
        
        print("\n✗ 主节点启动超时")
        return False
    
    def start_master_node(self):
        """启动主节点"""
        print("启动主节点...")
        
        # 确保端口可用
        if not self.check_port_availability(self.master_port):
            print(f"端口 {self.master_port} 被占用，正在清理...")
            self.kill_process_on_port(self.master_port)
            time.sleep(2)
        
        # 使用优化的主节点脚本
        master_script = "distributed_master_fixed.py"
        if not os.path.exists(master_script):
            master_script = "distributed_master.py"
        
        # 设置Windows优化环境变量
        env = os.environ.copy()
        env.update({
            'PYTHONUNBUFFERED': '1',
            'UVICORN_HOST': '127.0.0.1',
            'UVICORN_PORT': str(self.master_port),
            'UVICORN_WORKERS': '1',
            'UVICORN_LIMIT_CONCURRENCY': '100',
            'UVICORN_BACKLOG': '1024'
        })
        
        try:
            self.master_process = subprocess.Popen(
                [sys.executable, master_script],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 启动日志监控线程
            log_thread = threading.Thread(target=self.monitor_master_logs)
            log_thread.daemon = True
            log_thread.start()
            
            return True
            
        except Exception as e:
            print(f"启动主节点失败: {e}")
            return False
    
    def monitor_master_logs(self):
        """监控主节点日志"""
        if not self.master_process:
            return
        
        try:
            for line in iter(self.master_process.stdout.readline, ''):
                if line:
                    print(f"[主节点] {line.strip()}")
                if self.master_process.poll() is not None:
                    break
        except:
            pass
    
    def start_worker_nodes(self, worker_count=6):
        """启动工作节点"""
        print(f"启动 {worker_count} 个工作节点...")
        
        worker_script = "distributed_worker_fixed.py"
        if not os.path.exists(worker_script):
            worker_script = "distributed_worker.py"
        
        for i in range(worker_count):
            try:
                # 设置工作节点环境变量
                env = os.environ.copy()
                env.update({
                    'PYTHONUNBUFFERED': '1',
                    'MASTER_URL': self.master_url,
                    'WORKER_ID': f'optimized-worker-{i+1}',
                    'CONNECTION_POOL_SIZE': str(self.windows_optimizations['connection_pool_size']),
                    'REQUEST_TIMEOUT': str(self.windows_optimizations['socket_timeout']),
                    'MAX_RETRIES': str(self.windows_optimizations['max_retries']),
                    'RETRY_DELAY': str(self.windows_optimizations['retry_delay']),
                    'HEARTBEAT_INTERVAL': str(self.windows_optimizations['heartbeat_interval'])
                })
                
                process = subprocess.Popen(
                    [sys.executable, worker_script],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                self.worker_processes.append(process)
                
                # 启动日志监控线程
                log_thread = threading.Thread(target=self.monitor_worker_logs, args=(process, i+1))
                log_thread.daemon = True
                log_thread.start()
                
                print(f"✓ 工作节点 {i+1} 已启动")
                time.sleep(1)  # 避免同时启动过多进程
                
            except Exception as e:
                print(f"启动工作节点 {i+1} 失败: {e}")
    
    def monitor_worker_logs(self, process, worker_id):
        """监控工作节点日志"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(f"[工作节点{worker_id}] {line.strip()}")
                if process.poll() is not None:
                    break
        except:
            pass
    
    def check_system_health(self):
        """检查系统健康状态"""
        print("\n检查系统健康状态...")
        
        # 检查主节点健康
        try:
            response = requests.get(f"{self.master_url}/health", timeout=10)
            if response.status_code == 200:
                print("✓ 主节点健康检查通过")
            else:
                print(f"⚠ 主节点健康检查返回: {response.status_code}")
        except Exception as e:
            print(f"✗ 主节点健康检查失败: {e}")
        
        # 检查工作节点数量 - 使用/stats端点获取工作节点信息
        try:
            response = requests.get(f"{self.master_url}/stats", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                active_workers = stats.get('active_workers', 0)
                print(f"✓ 当前活跃工作节点: {active_workers}")
            else:
                print(f"⚠ 获取工作节点信息失败: {response.status_code}")
        except Exception as e:
            print(f"✗ 获取工作节点信息失败: {e}")
        
        # 检查系统资源
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            print(f"系统资源: CPU {cpu_percent:.1f}%, 内存 {memory.percent:.1f}%")
            
            if cpu_percent > 90:
                print("⚠ CPU使用率过高")
            if memory.percent > 90:
                print("⚠ 内存使用率过高")
                
        except Exception as e:
            print(f"系统资源检查失败: {e}")
    
    def run_distributed_system(self, worker_count=6):
        """运行分布式系统"""
        print("="*60)
        print("优化的分布式爬虫系统启动器")
        print("专门解决Windows网络连接问题")
        print("="*60)
        
        try:
            # 1. 启动主节点
            if not self.start_master_node():
                print("主节点启动失败，退出")
                return False
            
            # 2. 等待主节点就绪
            if not self.wait_for_master_ready():
                print("主节点启动超时，退出")
                return False
            
            # 3. 启动工作节点
            self.start_worker_nodes(worker_count)
            
            # 4. 检查系统健康
            self.check_system_health()
            
            print("\n" + "="*60)
            print("分布式爬虫系统启动成功！")
            print("系统正在运行中...")
            print("按 Ctrl+C 停止系统")
            print("="*60)
            
            # 5. 保持运行状态
            while True:
                # 检查进程状态
                if self.master_process and self.master_process.poll() is not None:
                    print("主节点进程已停止")
                    break
                
                # 定期检查系统健康
                time.sleep(30)
                self.check_system_health()
                
        except KeyboardInterrupt:
            print("\n收到中断信号，正在停止系统...")
        except Exception as e:
            print(f"系统运行异常: {e}")
        finally:
            self.cleanup()
    
    def test_network_connectivity(self):
        """测试网络连接性"""
        print("测试网络连接性...")
        
        test_cases = [
            (f"{self.master_url}/health", "主节点健康检查"),
            (f"{self.master_url}/workers", "工作节点列表"),
            (f"{self.master_url}/tasks", "任务列表"),
        ]
        
        for url, description in test_cases:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    print(f"✓ {description}: 成功 ({end_time-start_time:.2f}s)")
                else:
                    print(f"⚠ {description}: HTTP {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                print(f"✗ {description}: 连接失败")
            except requests.exceptions.Timeout:
                print(f"✗ {description}: 连接超时")
            except Exception as e:
                print(f"✗ {description}: {e}")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        worker_count = int(sys.argv[1])
    else:
        worker_count = 6
    
    optimizer = DistributedCrawlerOptimizer()
    
    try:
        # 运行分布式系统
        optimizer.run_distributed_system(worker_count)
    except KeyboardInterrupt:
        print("\n系统已停止")
    except Exception as e:
        print(f"系统运行失败: {e}")
    finally:
        optimizer.cleanup()

if __name__ == "__main__":
    main()