#!/usr/bin/env python3
"""
简单诊断分布式爬虫系统连接问题
"""

import os
import sys
import time
import socket
import requests
import subprocess

def check_port(port=8000, host='127.0.0.1'):
    """检查端口是否开放"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_master():
    """检查主节点状态"""
    print("=== 检查主节点 ===")
    
    # 检查端口
    if check_port():
        print("✅ 端口8000已开放")
    else:
        print("❌ 端口8000未开放")
        return False
    
    # 检查HTTP服务
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 主节点运行正常 - 状态: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ 主节点响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到主节点: {e}")
        return False

def check_workers():
    """检查工作节点状态"""
    print("\n=== 检查工作节点 ===")
    
    try:
        response = requests.get('http://127.0.0.1:8000/workers/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            workers = data.get('workers', [])
            active_workers = [w for w in workers if w.get('status') == 'active']
            
            print(f"🔍 发现 {len(workers)} 个工作节点")
            print(f"✅ 活跃工作节点: {len(active_workers)} 个")
            
            if active_workers:
                for worker in active_workers:
                    print(f"   - {worker.get('id', 'unknown')}: {worker.get('status', 'unknown')}")
            
            return len(active_workers) > 0
        else:
            print(f"❌ 无法获取工作节点状态: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 检查工作节点失败: {e}")
        return False

def check_task_queue():
    """检查任务队列状态"""
    print("\n=== 检查任务队列 ===")
    
    try:
        response = requests.get('http://127.0.0.1:8000/tasks/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            total_tasks = data.get('total_tasks', 0)
            completed_tasks = data.get('completed_tasks', 0)
            
            print(f"📊 总任务数: {total_tasks}")
            print(f"✅ 已完成: {completed_tasks}")
            
            if total_tasks > 0:
                progress = (completed_tasks / total_tasks) * 100
                print(f"📈 完成进度: {progress:.1f}%")
            
            return True
        else:
            print(f"❌ 无法获取任务状态: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 检查任务队列失败: {e}")
        return False

def check_python_processes():
    """检查Python进程"""
    print("\n=== 检查Python进程 ===")
    
    try:
        result = subprocess.run(
            'tasklist | findstr python', 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print(f"🔍 发现 {len(lines)} 个Python进程")
            
            # 统计主节点和工作节点进程
            master_count = 0
            worker_count = 0
            
            for line in lines:
                if 'distributed_master' in line.lower():
                    master_count += 1
                elif 'worker' in line.lower():
                    worker_count += 1
            
            print(f"📊 主节点进程: {master_count}")
            print(f"📊 工作节点进程: {worker_count}")
            
            return master_count > 0 and worker_count > 0
        else:
            print("❌ 无法获取进程信息")
            return False
            
    except Exception as e:
        print(f"❌ 检查进程失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("分布式爬虫系统连接问题诊断")
    print("=" * 60)
    
    # 检查各项指标
    master_ok = check_master()
    workers_ok = check_workers()
    tasks_ok = check_task_queue()
    processes_ok = check_python_processes()
    
    # 总结诊断结果
    print("\n" + "=" * 60)
    print("诊断结果总结")
    print("=" * 60)
    
    print(f"主节点状态: {'✅ 正常' if master_ok else '❌ 异常'}")
    print(f"工作节点状态: {'✅ 正常' if workers_ok else '❌ 异常'}")
    print(f"任务队列状态: {'✅ 正常' if tasks_ok else '❌ 异常'}")
    print(f"进程状态: {'✅ 正常' if processes_ok else '❌ 异常'}")
    
    # 分析问题
    if master_ok and workers_ok and processes_ok:
        print("\n🎉 系统连接正常！")
        print("\n💡 系统正在正常运行中")
        return True
    else:
        print("\n⚠️  系统存在连接问题")
        
        if not master_ok:
            print("\n🔧 主节点问题:")
            print("  - 检查主节点是否启动")
            print("  - 检查端口8000是否被占用")
            print("  - 检查防火墙设置")
        
        if not workers_ok:
            print("\n🔧 工作节点问题:")
            print("  - 检查工作节点是否启动")
            print("  - 检查网络连接")
            print("  - 检查工作节点配置文件")
        
        if not processes_ok:
            print("\n🔧 进程问题:")
            print("  - 检查是否有足够的Python进程")
            print("  - 检查进程是否被意外终止")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)