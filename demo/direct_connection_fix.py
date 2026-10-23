#!/usr/bin/env python3
"""
直接修复分布式爬虫系统连接问题
"""

import os
import sys
import time
import socket
import requests
import subprocess
import threading
from pathlib import Path

def check_port_availability(port=8000, host='127.0.0.1'):
    """检查端口是否可用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0  # 0表示端口被占用
    except Exception as e:
        print(f"❌ 检查端口 {host}:{port} 失败: {e}")
        return False

def kill_process_on_port(port=8000):
    """杀死占用端口的进程"""
    try:
        # Windows下使用netstat和taskkill
        result = subprocess.run(
            f'netstat -ano | findstr ":{port}"', 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    print(f"🔍 发现占用端口 {port} 的进程 PID: {pid}")
                    
                    # 杀死进程
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True)
                    print(f"✅ 已杀死进程 PID: {pid}")
                    time.sleep(2)  # 等待进程完全退出
        else:
            print(f"✅ 端口 {port} 未被占用")
            
    except Exception as e:
        print(f"❌ 杀死进程失败: {e}")

def start_master_node():
    """启动主节点"""
    print("\n=== 启动主节点 ===")
    
    # 先检查并杀死占用端口的进程
    if check_port_availability():
        print("⚠️  端口8000被占用，尝试释放...")
        kill_process_on_port()
    
    # 检查主节点文件
    master_files = [
        "distributed_master_fixed.py",
        "distributed_master.py",
        "distributed_master_simple.py"
    ]
    
    master_file = None
    for file in master_files:
        if os.path.exists(file):
            master_file = file
            break
    
    if not master_file:
        print("❌ 未找到主节点文件")
        return False
    
    print(f"📁 使用主节点文件: {master_file}")
    
    try:
        # 启动主节点
        process = subprocess.Popen([
            sys.executable, master_file
        ], cwd=os.getcwd())
        
        # 等待主节点启动
        print("⏳ 等待主节点启动...")
        time.sleep(10)
        
        # 检查主节点是否正常
        if check_master_health():
            print("✅ 主节点启动成功")
            return process
        else:
            print("❌ 主节点启动失败")
            process.terminate()
            return False
            
    except Exception as e:
        print(f"❌ 启动主节点失败: {e}")
        return False

def check_master_health():
    """检查主节点健康状态"""
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 主节点运行正常 - 状态: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ 主节点响应异常 - 状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到主节点: {e}")
        return False

def start_workers():
    """启动工作节点"""
    print("\n=== 启动工作节点 ===")
    
    worker_files = [
        "start_six_workers_fixed.py",
        "start_system_fixed.py",
        "start_system.py"
    ]
    
    worker_file = None
    for file in worker_files:
        if os.path.exists(file):
            worker_file = file
            break
    
    if not worker_file:
        print("❌ 未找到工作节点启动文件")
        return False
    
    print(f"📁 使用工作节点文件: {worker_file}")
    
    try:
        # 启动工作节点
        process = subprocess.Popen([
            sys.executable, worker_file
        ], cwd=os.getcwd())
        
        # 等待工作节点启动
        print("⏳ 等待工作节点启动...")
        time.sleep(15)
        
        # 检查工作节点连接
        if check_worker_connections():
            print("✅ 工作节点启动成功")
            return process
        else:
            print("❌ 工作节点启动失败")
            process.terminate()
            return False
            
    except Exception as e:
        print(f"❌ 启动工作节点失败: {e}")
        return False

def check_worker_connections():
    """检查工作节点连接状态"""
    try:
        response = requests.get('http://127.0.0.1:8000/workers/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            workers = data.get('workers', [])
            active_workers = [w for w in workers if w.get('status') == 'active']
            
            print(f"🔍 发现 {len(workers)} 个工作节点，其中 {len(active_workers)} 个活跃")
            
            if active_workers:
                for worker in active_workers:
                    print(f"   - {worker.get('id', 'unknown')}: {worker.get('status', 'unknown')}")
                return True
            else:
                print("⚠️  没有活跃的工作节点")
                return False
        else:
            print(f"❌ 无法获取工作节点状态 - 状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 检查工作节点连接失败: {e}")
        return False

def optimize_network_config():
    """优化网络配置"""
    print("\n=== 优化网络配置 ===")
    
    # 创建优化的配置文件
    config_content = """# 网络优化配置
network:
  connection_timeout: 60
  request_timeout: 90
  max_retries: 5
  retry_delay: 10
  
worker:
  max_threads: 8
  heartbeat_interval: 30
  
windows_specific:
  use_localhost: true
  disable_ipv6: false
"""
    
    try:
        with open('network_optimized.yaml', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ 网络优化配置已创建")
        return True
    except Exception as e:
        print(f"❌ 创建网络配置失败: {e}")
        return False

def create_simple_monitor():
    """创建简单监控脚本"""
    print("\n=== 创建系统监控 ===")
    
    monitor_content = """#!/usr/bin/env python3
import time
import requests

def monitor_system():
    while True:
        try:
            # 检查主节点
            response = requests.get('http://127.0.0.1:8000/health', timeout=5)
            master_ok = response.status_code == 200
            
            # 检查工作节点
            response = requests.get('http://127.0.0.1:8000/workers/status', timeout=5)
            workers_ok = response.status_code == 200
            
            if master_ok and workers_ok:
                print(f"[{time.strftime('%H:%M:%S')}] ✅ 系统正常")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] ⚠️  系统异常")
                
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ 监控错误: {e}")
        
        time.sleep(30)  # 每30秒检查一次

if __name__ == "__main__":
    monitor_system()
"""
    
    try:
        with open('simple_monitor.py', 'w', encoding='utf-8') as f:
            f.write(monitor_content)
        print("✅ 简单监控脚本已创建")
        return True
    except Exception as e:
        print(f"❌ 创建监控脚本失败: {e}")
        return False

def main():
    """主修复函数"""
    print("=" * 60)
    print("分布式爬虫系统连接问题直接修复")
    print("=" * 60)
    
    # 步骤1: 检查当前状态
    print("\n=== 检查当前系统状态 ===")
    
    master_healthy = check_master_health()
    workers_connected = check_worker_connections()
    
    if master_healthy and workers_connected:
        print("✅ 系统连接正常，无需修复")
        return True
    
    # 步骤2: 修复主节点
    if not master_healthy:
        print("\n=== 修复主节点 ===")
        master_process = start_master_node()
        if not master_process:
            print("❌ 主节点修复失败")
            return False
    
    # 等待主节点稳定
    time.sleep(5)
    
    # 步骤3: 修复工作节点
    if not workers_connected:
        print("\n=== 修复工作节点 ===")
        worker_process = start_workers()
        if not worker_process:
            print("❌ 工作节点修复失败")
            return False
    
    # 步骤4: 优化网络配置
    optimize_network_config()
    
    # 步骤5: 创建监控
    create_simple_monitor()
    
    # 步骤6: 最终验证
    print("\n=== 最终验证 ===")
    
    final_master_ok = check_master_health()
    final_workers_ok = check_worker_connections()
    
    if final_master_ok and final_workers_ok:
        print("✅ 系统修复成功！")
        print("\n📋 修复完成:")
        print("  - 主节点: 运行正常")
        print("  - 工作节点: 连接正常") 
        print("  - 网络配置: 已优化")
        print("  - 监控脚本: 已创建")
        print("\n💡 建议运行: python simple_monitor.py 进行持续监控")
        return True
    else:
        print("⚠️  系统部分修复成功")
        print(f"  - 主节点: {'正常' if final_master_ok else '异常'}")
        print(f"  - 工作节点: {'正常' if final_workers_ok else '异常'}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)