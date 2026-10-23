"""
分布式爬虫系统启动器 - 简化版
专门解决Windows网络连接问题
"""

import time
import subprocess
import sys
import os
import signal
import requests
import threading
from datetime import datetime

class SimpleSystemStarter:
    """简化版系统启动器"""
    
    def __init__(self):
        self.master_process = None
        self.worker_processes = []
        self.master_url = "http://127.0.0.1:8000"
        self.running = False
        
        # 配置
        self.num_workers = 3  # 启动3个工作节点
        self.master_start_timeout = 30  # 主节点启动超时时间（秒）
        self.health_check_interval = 10  # 健康检查间隔（秒）
        
        print("=" * 60)
        print("分布式爬虫系统启动器 - 简化版")
        print("专门解决Windows网络连接问题")
        print("=" * 60)
    
    def check_port_available(self, port: int) -> bool:
        """检查端口是否可用"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', port))
                return result != 0  # 如果连接失败，说明端口可用
        except:
            return True
    
    def kill_process_on_port(self, port: int):
        """杀死占用端口的进程"""
        try:
            # Windows系统使用netstat命令查找占用端口的进程
            result = subprocess.run(
                ['netstat', '-ano', '-p', 'tcp'], 
                capture_output=True, 
                text=True
            )
            
            for line in result.stdout.split('\n'):
                if f':{port} ' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        print(f"发现占用端口 {port} 的进程 PID: {pid}")
                        
                        # 杀死进程
                        subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                        print(f"已杀死进程 PID: {pid}")
                        time.sleep(2)  # 等待进程完全退出
                        break
        except Exception as e:
            print(f"清理端口进程失败: {e}")
    
    def start_master(self) -> bool:
        """启动主节点"""
        print("\n[1/3] 启动主节点...")
        
        # 检查端口是否被占用
        if not self.check_port_available(8000):
            print("端口8000被占用，正在清理...")
            self.kill_process_on_port(8000)
            time.sleep(3)
        
        try:
            # 启动主节点
            self.master_process = subprocess.Popen(
                [sys.executable, "distributed_master_simple.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            print("主节点进程已启动，等待服务就绪...")
            
            # 等待主节点启动
            start_time = time.time()
            while time.time() - start_time < self.master_start_timeout:
                try:
                    response = requests.get(f"{self.master_url}/health", timeout=5)
                    if response.status_code == 200:
                        print("✓ 主节点启动成功")
                        return True
                except:
                    pass
                
                # 检查进程是否还在运行
                if self.master_process.poll() is not None:
                    # 进程已退出，读取输出
                    output, _ = self.master_process.communicate()
                    print("✗ 主节点启动失败:")
                    print(output)
                    return False
                
                time.sleep(2)
            
            print("✗ 主节点启动超时")
            return False
            
        except Exception as e:
            print(f"✗ 主节点启动异常: {e}")
            return False
    
    def start_workers(self) -> bool:
        """启动工作节点"""
        print(f"\n[2/3] 启动 {self.num_workers} 个工作节点...")
        
        try:
            for i in range(self.num_workers):
                worker_process = subprocess.Popen(
                    [sys.executable, "distributed_worker_simple.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                self.worker_processes.append(worker_process)
                print(f"✓ 工作节点 {i+1} 已启动")
                time.sleep(1)  # 避免同时启动过多节点
            
            # 等待工作节点连接验证
            print("等待工作节点连接主节点...")
            connected_workers = 0
            start_time = time.time()
            
            while time.time() - start_time < 30:  # 30秒超时
                try:
                    response = requests.get(f"{self.master_url}/health", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        current_workers = data.get('active_workers', 0)
                        
                        if current_workers >= self.num_workers:
                            print(f"✓ 所有工作节点连接成功 - 活跃工作节点: {current_workers}")
                            return True
                        elif current_workers > connected_workers:
                            connected_workers = current_workers
                            print(f"✓ 工作节点连接进度: {connected_workers}/{self.num_workers}")
                except:
                    pass
                
                time.sleep(2)
            
            print(f"✗ 工作节点连接超时 - 仅 {connected_workers}/{self.num_workers} 个节点连接成功")
            return False
            
        except Exception as e:
            print(f"✗ 工作节点启动异常: {e}")
            return False
    
    def health_check_loop(self):
        """健康检查循环"""
        while self.running:
            try:
                # 检查主节点健康状态 - 使用/stats端点获取真实数据
                response = requests.get(f"{self.master_url}/stats", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    task_stats = data.get('task_stats', {})
                    
                    print(f"[健康检查] 主节点正常 - 活跃工作节点: {data.get('active_workers', 0)}, "
                          f"待处理任务: {task_stats.get('pending', 0)}, "
                          f"已完成任务: {task_stats.get('completed', 0)}, "
                          f"失败任务: {task_stats.get('failed', 0)}, "
                          f"已开始任务: {task_stats.get('started', 0)}")
                else:
                    print(f"[健康检查] 主节点异常: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"[健康检查] 连接失败: {e}")
            
            time.sleep(self.health_check_interval)
    
    def monitor_system(self):
        """监控系统状态"""
        print("\n[3/3] 启动系统监控...")
        
        # 启动健康检查线程
        health_thread = threading.Thread(target=self.health_check_loop, daemon=True)
        health_thread.start()
        
        print("✓ 系统监控已启动")
        print("\n" + "=" * 60)
        print("分布式爬虫系统运行中...")
        print("按 Ctrl+C 停止系统")
        print("=" * 60)
        
        # 主循环
        try:
            while self.running:
                # 检查主节点进程状态
                if self.master_process and self.master_process.poll() is not None:
                    print("✗ 主节点进程异常退出")
                    self.cleanup()
                    return
                
                # 检查工作节点进程状态
                dead_workers = []
                for i, process in enumerate(self.worker_processes):
                    if process.poll() is not None:
                        dead_workers.append(i)
                
                # 重启死亡的工作节点
                for i in dead_workers:
                    print(f"工作节点 {i+1} 异常退出，正在重启...")
                    try:
                        new_process = subprocess.Popen(
                            [sys.executable, "distributed_worker_simple.py"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1,
                            universal_newlines=True
                        )
                        self.worker_processes[i] = new_process
                        print(f"✓ 工作节点 {i+1} 重启成功")
                    except Exception as e:
                        print(f"✗ 工作节点 {i+1} 重启失败: {e}")
                
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n收到停止信号，正在关闭系统...")
            self.cleanup()
    
    def cleanup(self):
        """清理进程"""
        print("\n正在清理进程...")
        
        # 停止工作节点
        for i, process in enumerate(self.worker_processes):
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                    print(f"✓ 工作节点 {i+1} 已停止")
                except:
                    process.kill()
                    print(f"✓ 工作节点 {i+1} 已强制停止")
        
        # 停止主节点
        if self.master_process and self.master_process.poll() is None:
            self.master_process.terminate()
            try:
                self.master_process.wait(timeout=5)
                print("✓ 主节点已停止")
            except:
                self.master_process.kill()
                print("✓ 主节点已强制停止")
        
        self.worker_processes.clear()
        print("✓ 系统清理完成")
    
    def start(self):
        """启动整个系统"""
        self.running = True
        
        try:
            # 启动主节点
            if not self.start_master():
                print("✗ 系统启动失败: 主节点启动失败")
                self.cleanup()
                return False
            
            # 启动工作节点
            if not self.start_workers():
                print("✗ 系统启动失败: 工作节点启动失败")
                self.cleanup()
                return False
            
            # 启动监控
            self.monitor_system()
            return True
            
        except Exception as e:
            print(f"✗ 系统启动异常: {e}")
            self.cleanup()
            return False
    
    def stop(self):
        """停止系统"""
        self.running = False
        self.cleanup()

def main():
    """主函数"""
    starter = SimpleSystemStarter()
    
    try:
        success = starter.start()
        if success:
            print("\n✓ 分布式爬虫系统已成功启动并运行")
        else:
            print("\n✗ 分布式爬虫系统启动失败")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n系统被用户中断")
        starter.stop()
    except Exception as e:
        print(f"\n系统异常: {e}")
        starter.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()