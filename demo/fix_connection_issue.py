#!/usr/bin/env python3
"""
修复分布式爬虫系统连接问题
"""

import os
import sys
import time
import socket
import subprocess
import requests
from pathlib import Path

def kill_process_on_port(port=8000):
    """杀死占用指定端口的进程"""
    try:
        # 使用netstat查找占用端口的进程
        result = subprocess.run(
            f'netstat -ano | findstr ":{port}"', 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'LISTENING' in line:
                    parts = line.strip().split()
                    pid = parts[-1]
                    
                    print(f"🔍 发现端口{port}被进程 {pid} 占用")
                    
                    # 杀死进程
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True)
                    print(f"✅ 已杀死进程 {pid}")
                    time.sleep(2)
        else:
            print(f"✅ 端口{port}未被占用")
            
    except Exception as e:
        print(f"❌ 检查端口占用失败: {e}")

def start_master():
    """启动主节点"""
    print("\n=== 启动主节点 ===")
    
    # 检查主节点文件是否存在
    master_files = [
        'distributed_master_fixed.py',
        'distributed_master.py',
        'distributed_master_simple.py'
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
    
    # 启动主节点（后台运行）
    try:
        # 使用start命令在新窗口中启动主节点
        subprocess.Popen(
            ['start', 'python', master_file], 
            shell=True,
            cwd=os.getcwd()
        )
        print("✅ 主节点启动命令已发送")
        
        # 等待主节点启动
        print("⏳ 等待主节点启动...")
        time.sleep(10)
        
        # 检查主节点是否启动成功
        for i in range(5):
            try:
                response = requests.get('http://127.0.0.1:8000/health', timeout=5)
                if response.status_code == 200:
                    print("✅ 主节点启动成功")
                    return True
            except:
                print(f"⏳ 等待主节点响应... ({i+1}/5)")
                time.sleep(3)
        
        print("❌ 主节点启动超时")
        return False
        
    except Exception as e:
        print(f"❌ 启动主节点失败: {e}")
        return False

def start_workers():
    """启动工作节点"""
    print("\n=== 启动工作节点 ===")
    
    # 检查工作节点启动文件
    worker_files = [
        'start_six_workers_fixed.py',
        'start_workers.py'
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
    
    # 启动工作节点（后台运行）
    try:
        # 使用start命令在新窗口中启动工作节点
        subprocess.Popen(
            ['start', 'python', worker_file], 
            shell=True,
            cwd=os.getcwd()
        )
        print("✅ 工作节点启动命令已发送")
        
        # 等待工作节点启动
        print("⏳ 等待工作节点启动...")
        time.sleep(15)
        
        # 检查工作节点状态
        try:
            response = requests.get('http://127.0.0.1:8000/workers/status', timeout=10)
            if response.status_code == 200:
                data = response.json()
                workers = data.get('workers', [])
                active_workers = [w for w in workers if w.get('status') == 'active']
                
                print(f"✅ 工作节点启动成功 - 活跃节点: {len(active_workers)} 个")
                
                if active_workers:
                    for worker in active_workers:
                        print(f"   - {worker.get('id', 'unknown')}: {worker.get('status', 'unknown')}")
                
                return len(active_workers) > 0
            else:
                print(f"❌ 无法获取工作节点状态: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 检查工作节点状态失败: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 启动工作节点失败: {e}")
        return False

def check_system_health():
    """检查系统健康状态"""
    print("\n=== 系统健康检查 ===")
    
    health_checks = []
    
    # 检查主节点
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 主节点运行正常")
            health_checks.append(True)
        else:
            print(f"❌ 主节点异常: {response.status_code}")
            health_checks.append(False)
    except Exception as e:
        print(f"❌ 主节点不可达: {e}")
        health_checks.append(False)
    
    # 检查工作节点
    try:
        response = requests.get('http://127.0.0.1:8000/workers/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            workers = data.get('workers', [])
            active_workers = [w for w in workers if w.get('status') == 'active']
            
            if active_workers:
                print(f"✅ 工作节点正常 - 活跃节点: {len(active_workers)} 个")
                health_checks.append(True)
            else:
                print("❌ 无活跃工作节点")
                health_checks.append(False)
        else:
            print(f"❌ 工作节点异常: {response.status_code}")
            health_checks.append(False)
    except Exception as e:
        print(f"❌ 工作节点不可达: {e}")
        health_checks.append(False)
    
    # 检查任务队列
    try:
        response = requests.get('http://127.0.0.1:8000/tasks/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            total_tasks = data.get('total_tasks', 0)
            completed_tasks = data.get('completed_tasks', 0)
            
            print(f"📊 任务队列正常 - 总任务: {total_tasks}, 已完成: {completed_tasks}")
            health_checks.append(True)
        else:
            print(f"❌ 任务队列异常: {response.status_code}")
            health_checks.append(False)
    except Exception as e:
        print(f"❌ 任务队列不可达: {e}")
        health_checks.append(False)
    
    return all(health_checks)

def main():
    """主函数"""
    print("=" * 60)
    print("分布式爬虫系统连接问题修复")
    print("=" * 60)
    
    # 1. 清理端口占用
    print("\n步骤1: 清理端口占用")
    kill_process_on_port(8000)
    
    # 2. 启动主节点
    print("\n步骤2: 启动主节点")
    master_started = start_master()
    
    if not master_started:
        print("❌ 主节点启动失败，无法继续")
        return False
    
    # 3. 启动工作节点
    print("\n步骤3: 启动工作节点")
    workers_started = start_workers()
    
    # 4. 检查系统健康状态
    print("\n步骤4: 系统健康检查")
    system_healthy = check_system_health()
    
    # 总结结果
    print("\n" + "=" * 60)
    print("修复结果总结")
    print("=" * 60)
    
    if system_healthy:
        print("🎉 系统修复成功！")
        print("\n💡 系统现在可以正常运行")
        print("📊 建议监控系统运行状态")
    else:
        print("⚠️  系统部分修复")
        
        if master_started:
            print("✅ 主节点已启动")
        else:
            print("❌ 主节点启动失败")
        
        if workers_started:
            print("✅ 工作节点已启动")
        else:
            print("❌ 工作节点启动失败")
        
        print("\n🔧 可能需要手动检查以下问题:")
        print("  - 检查防火墙设置")
        print("  - 检查网络连接")
        print("  - 查看日志文件获取详细信息")
    
    return system_healthy

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)