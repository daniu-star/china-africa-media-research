#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分布式爬虫系统综合诊断与修复脚本
解决连接不健康问题
"""

import os
import sys
import json
import time
import requests
import socket
import subprocess
import threading
from pathlib import Path
from datetime import datetime

def check_port_availability(host='127.0.0.1', port=8000):
    """检查端口是否可用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"❌ 端口检查失败: {e}")
        return False

def check_master_health():
    """检查主节点健康状态"""
    print("\n=== 检查主节点健康状态 ===")
    
    # 检查端口
    if not check_port_availability('127.0.0.1', 8000):
        print("❌ 主节点端口8000不可用")
        return False
    
    # 检查API端点
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 主节点运行正常")
            print(f"   状态: {data.get('status', 'unknown')}")
            print(f"   工作节点数: {data.get('worker_count', 0)}")
            return True
        else:
            print(f"❌ 主节点返回异常状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到主节点: {e}")
        return False

def check_worker_connections():
    """检查工作节点连接状态"""
    print("\n=== 检查工作节点连接状态 ===")
    
    try:
        response = requests.get('http://127.0.0.1:8000/workers/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            workers = data.get('workers', [])
            
            if not workers:
                print("❌ 没有活跃的工作节点")
                return False
            
            active_workers = [w for w in workers if w.get('status') == 'active']
            print(f"✅ 活跃工作节点: {len(active_workers)}/{len(workers)}")
            
            for worker in active_workers:
                print(f"   - {worker.get('id', 'unknown')}: {worker.get('status', 'unknown')}")
                
            return len(active_workers) > 0
        else:
            print(f"❌ 无法获取工作节点状态: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 检查工作节点连接失败: {e}")
        return False

def check_task_queue():
    """检查任务队列状态"""
    print("\n=== 检查任务队列状态 ===")
    
    try:
        response = requests.get('http://127.0.0.1:8000/tasks/queue', timeout=10)
        if response.status_code == 200:
            data = response.json()
            pending = data.get('pending_tasks', 0)
            completed = data.get('completed_tasks', 0)
            failed = data.get('failed_tasks', 0)
            
            print(f"✅ 任务队列状态:")
            print(f"   待处理: {pending}")
            print(f"   已完成: {completed}")
            print(f"   失败: {failed}")
            
            if pending > 0 and completed == 0:
                print("⚠️  有任务但未完成，可能存在处理问题")
                return False
                
            return True
        else:
            print(f"❌ 无法获取任务队列状态: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 检查任务队列失败: {e}")
        return False

def check_network_connectivity():
    """检查网络连接性"""
    print("\n=== 检查网络连接性 ===")
    
    # 检查本地连接
    try:
        socket.gethostbyname('127.0.0.1')
        print("✅ 本地网络连接正常")
    except Exception as e:
        print(f"❌ 本地网络连接异常: {e}")
        return False
    
    # 检查外部连接
    try:
        socket.gethostbyname('google.com')
        print("✅ 外部网络连接正常")
    except Exception as e:
        print(f"⚠️  外部网络连接异常: {e}")
    
    return True

def check_file_system():
    """检查文件系统状态"""
    print("\n=== 检查文件系统状态 ===")
    
    data_dir = Path("./data")
    
    # 检查数据目录
    if not data_dir.exists():
        print("❌ 数据目录不存在")
        return False
    
    # 检查任务文件
    task_files = list(data_dir.glob("tasks_*.json"))
    if not task_files:
        print("❌ 没有找到任务文件")
        return False
    
    print(f"✅ 找到 {len(task_files)} 个任务文件")
    
    # 检查结果文件
    results_dir = data_dir / "results"
    if results_dir.exists():
        result_files = list(results_dir.glob("results_*.json"))
        print(f"✅ 找到 {len(result_files)} 个结果文件")
    
    return True

def start_master_node():
    """启动主节点"""
    print("\n=== 启动主节点 ===")
    
    try:
        # 检查是否已运行
        if check_port_availability('127.0.0.1', 8000):
            print("✅ 主节点已在运行")
            return True
        
        # 启动主节点
        process = subprocess.Popen([
            sys.executable, "distributed_master_fixed.py"
        ], cwd=os.getcwd())
        
        # 等待启动
        for i in range(30):  # 等待30秒
            time.sleep(1)
            if check_port_availability('127.0.0.1', 8000):
                print("✅ 主节点启动成功")
                return True
        
        print("❌ 主节点启动超时")
        process.terminate()
        return False
        
    except Exception as e:
        print(f"❌ 启动主节点失败: {e}")
        return False

def start_workers():
    """启动工作节点"""
    print("\n=== 启动工作节点 ===")
    
    try:
        process = subprocess.Popen([
            sys.executable, "start_six_workers_fixed.py"
        ], cwd=os.getcwd())
        
        # 等待工作节点启动
        time.sleep(10)
        
        # 检查工作节点连接
        if check_worker_connections():
            print("✅ 工作节点启动成功")
            return True
        else:
            print("❌ 工作节点启动失败")
            process.terminate()
            return False
            
    except Exception as e:
        print(f"❌ 启动工作节点失败: {e}")
        return False

def optimize_network_settings():
    """优化网络设置"""
    print("\n=== 优化网络设置 ===")
    
    # 创建优化配置文件
    config = {
        "network_optimization": {
            "connection_timeout": 60,
            "request_timeout": 90,
            "max_retries": 5,
            "retry_delay": 10,
            "connection_pool_size": 20,
            "keep_alive": True,
            "dns_cache_ttl": 300
        },
        "windows_specific": {
            "use_127_0_0_1": True,
            "disable_ipv6": False,
            "socket_reuse": True
        }
    }
    
    with open("network_optimization.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ 网络优化配置已创建")
    return True

def create_health_monitor():
    """创建健康监控脚本"""
    print("\n=== 创建健康监控脚本 ===")
    
    script_content = """#!/usr/bin/env python3
import time
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_system_health():
    # 检查系统健康状态
    try:
        # 检查主节点
        response = requests.get('http://127.0.0.1:8000/health', timeout=10)
        if response.status_code != 200:
            return False
        
        # 检查工作节点
        response = requests.get('http://127.0.0.1:8000/workers/status', timeout=10)
        if response.status_code != 200:
            return False
            
        data = response.json()
        active_workers = [w for w in data.get('workers', []) if w.get('status') == 'active']
        
        return len(active_workers) > 0
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return False

def main():
    # 主监控循环
    consecutive_failures = 0
    max_failures = 3
    
    while True:
        if check_system_health():
            consecutive_failures = 0
            logger.info(f"[{datetime.now()}] 系统健康")
        else:
            consecutive_failures += 1
            logger.warning(f"[{datetime.now()}] 系统不健康，连续失败: {consecutive_failures}")
            
            if consecutive_failures >= max_failures:
                logger.error("系统严重不健康，需要重启")
                # 这里可以添加重启逻辑
                break
        
        time.sleep(60)  # 每分钟检查一次

if __name__ == "__main__":
    main()
"""
    
    with open("health_monitor.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("✅ 健康监控脚本已创建")
    return True

def main():
    """主诊断函数"""
    print("=" * 60)
    print("分布式爬虫系统综合诊断与修复")
    print("=" * 60)
    
    # 执行诊断检查
    checks = [
        ("网络连接性", check_network_connectivity),
        ("文件系统", check_file_system),
        ("主节点健康", check_master_health),
        ("工作节点连接", check_worker_connections),
        ("任务队列", check_task_queue)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} 检查异常: {e}")
            results.append((check_name, False))
    
    # 分析诊断结果
    print("\n=== 诊断结果分析 ===")
    
    passed_checks = sum(1 for _, result in results if result)
    total_checks = len(results)
    
    print(f"通过检查: {passed_checks}/{total_checks}")
    
    if passed_checks == total_checks:
        print("✅ 系统健康状态良好")
        return True
    
    # 执行修复措施
    print("\n=== 执行修复措施 ===")
    
    # 如果主节点不健康，尝试启动
    if not any(name == "主节点健康" and result for name, result in results):
        print("尝试启动主节点...")
        start_master_node()
    
    # 如果工作节点连接有问题，尝试启动工作节点
    if not any(name == "工作节点连接" and result for name, result in results):
        print("尝试启动工作节点...")
        start_workers()
    
    # 优化网络设置
    optimize_network_settings()
    
    # 创建健康监控
    create_health_monitor()
    
    # 最终验证
    print("\n=== 最终验证 ===")
    
    final_checks = [
        ("主节点健康", check_master_health),
        ("工作节点连接", check_worker_connections)
    ]
    
    final_results = []
    for check_name, check_func in final_checks:
        try:
            result = check_func()
            final_results.append((check_name, result))
        except Exception as e:
            final_results.append((check_name, False))
    
    final_passed = sum(1 for _, result in final_results if result)
    
    print(f"修复后通过检查: {final_passed}/{len(final_checks)}")
    
    if final_passed == len(final_checks):
        print("✅ 系统修复成功")
        return True
    else:
        print("⚠️  系统部分修复，可能需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)