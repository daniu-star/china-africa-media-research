#!/usr/bin/env python3
"""
清理并重启分布式爬虫系统
"""

import os
import sys
import time
import subprocess
import signal

def kill_all_python_processes():
    """杀死所有Python进程"""
    print("=== 清理Python进程 ===")
    
    try:
        # Windows下杀死Python进程
        result = subprocess.run(
            'taskkill /F /IM python.exe', 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 已杀死所有Python进程")
        else:
            print("⚠️  杀死Python进程结果:", result.stdout)
            
        # 等待进程清理完成
        time.sleep(3)
        
    except Exception as e:
        print(f"❌ 清理进程失败: {e}")

def check_port_usage(port=8000):
    """检查端口使用情况"""
    try:
        result = subprocess.run(
            f'netstat -ano | findstr ":{port}"', 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0 and result.stdout:
            print(f"⚠️  端口 {port} 被占用:")
            print(result.stdout)
            return True
        else:
            print(f"✅ 端口 {port} 空闲")
            return False
            
    except Exception as e:
        print(f"❌ 检查端口失败: {e}")
        return False

def start_master():
    """启动主节点"""
    print("\n=== 启动主节点 ===")
    
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
        return None
    
    print(f"📁 使用主节点文件: {master_file}")
    
    try:
        # 启动主节点
        process = subprocess.Popen([
            sys.executable, master_file
        ], cwd=os.getcwd())
        
        print("⏳ 等待主节点启动...")
        time.sleep(10)
        
        # 检查主节点是否启动成功
        try:
            import requests
            response = requests.get('http://127.0.0.1:8000/health', timeout=5)
            if response.status_code == 200:
                print("✅ 主节点启动成功")
                return process
            else:
                print(f"❌ 主节点响应异常: {response.status_code}")
                process.terminate()
                return None
        except:
            print("❌ 无法连接到主节点")
            process.terminate()
            return None
            
    except Exception as e:
        print(f"❌ 启动主节点失败: {e}")
        return None

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
        return None
    
    print(f"📁 使用工作节点文件: {worker_file}")
    
    try:
        # 启动工作节点
        process = subprocess.Popen([
            sys.executable, worker_file
        ], cwd=os.getcwd())
        
        print("⏳ 等待工作节点启动...")
        time.sleep(15)
        
        # 检查工作节点连接
        try:
            import requests
            response = requests.get('http://127.0.0.1:8000/workers/status', timeout=10)
            if response.status_code == 200:
                data = response.json()
                workers = data.get('workers', [])
                active_workers = [w for w in workers if w.get('status') == 'active']
                
                print(f"✅ 工作节点启动成功 - 发现 {len(active_workers)} 个活跃工作节点")
                return process
            else:
                print(f"❌ 工作节点响应异常: {response.status_code}")
                process.terminate()
                return None
        except Exception as e:
            print(f"❌ 检查工作节点失败: {e}")
            process.terminate()
            return None
            
    except Exception as e:
        print(f"❌ 启动工作节点失败: {e}")
        return None

def check_system_health():
    """检查系统健康状态"""
    print("\n=== 检查系统健康状态 ===")
    
    try:
        import requests
        
        # 检查主节点
        try:
            response = requests.get('http://127.0.0.1:8000/health', timeout=5)
            if response.status_code == 200:
                print("✅ 主节点运行正常")
                master_ok = True
            else:
                print(f"❌ 主节点异常: {response.status_code}")
                master_ok = False
        except:
            print("❌ 无法连接到主节点")
            master_ok = False
        
        # 检查工作节点
        try:
            response = requests.get('http://127.0.0.1:8000/workers/status', timeout=5)
            if response.status_code == 200:
                data = response.json()
                workers = data.get('workers', [])
                active_workers = [w for w in workers if w.get('status') == 'active']
                
                print(f"✅ 工作节点正常 - {len(active_workers)} 个活跃")
                workers_ok = True
            else:
                print(f"❌ 工作节点异常: {response.status_code}")
                workers_ok = False
        except:
            print("❌ 无法获取工作节点状态")
            workers_ok = False
        
        return master_ok and workers_ok
        
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("分布式爬虫系统清理重启")
    print("=" * 60)
    
    # 步骤1: 检查当前状态
    print("\n=== 当前系统状态 ===")
    current_health = check_system_health()
    
    if current_health:
        print("✅ 系统当前运行正常")
        return True
    
    # 步骤2: 清理系统
    kill_all_python_processes()
    check_port_usage()
    
    # 步骤3: 启动主节点
    master_process = start_master()
    if not master_process:
        print("❌ 主节点启动失败")
        return False
    
    # 步骤4: 启动工作节点
    worker_process = start_workers()
    if not worker_process:
        print("❌ 工作节点启动失败")
        master_process.terminate()
        return False
    
    # 步骤5: 最终检查
    print("\n=== 最终系统状态 ===")
    final_health = check_system_health()
    
    if final_health:
        print("\n🎉 系统重启成功！")
        print("\n📋 系统状态:")
        print("  - 主节点: 运行正常")
        print("  - 工作节点: 连接正常")
        print("\n💡 系统已准备好处理爬虫任务")
        return True
    else:
        print("\n⚠️  系统重启部分成功")
        print("\n🔧 建议检查:")
        print("  - 网络连接配置")
        print("  - 防火墙设置")
        print("  - 端口占用情况")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)