#!/usr/bin/env python3
"""
为每个工作节点启动独立的监控终端
"""

import subprocess
import time
import os

def get_active_workers():
    """获取当前活跃的工作节点列表"""
    try:
        # 方法1：查找已注册的工作节点
        cmd1 = "grep 'worker-' distributed_worker.log | grep '已向主节点注册' | tail -10 | awk '{print $NF}' | sort -u"
        result1 = subprocess.run(cmd1, shell=True, capture_output=True, text=True)
        
        # 方法2：查找最近启动的工作节点
        cmd2 = "grep '启动分布式爬虫工作节点:' distributed_worker.log | tail -10 | awk -F': ' '{print $NF}' | sort -u"
        result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
        
        workers = []
        
        if result1.stdout:
            workers.extend([w.strip() for w in result1.stdout.split('\n') if w.strip()])
        
        if result2.stdout:
            workers.extend([w.strip() for w in result2.stdout.split('\n') if w.strip()])
        
        # 去重
        workers = list(set(workers))
        
        return workers
    except Exception as e:
        print(f"获取活跃工作节点错误: {e}")
    
    return []

def start_worker_monitor(worker_id):
    """为单个工作节点启动监控终端"""
    # 创建监控脚本
    monitor_script = f'''
import time
import subprocess
from datetime import datetime

print("=== 工作节点 {worker_id} 实时监控 ===")
print(f"开始时间: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
print("-" * 50)

while True:
    try:
        # 获取该工作节点的最新日志
        cmd = f"grep '{worker_id}' distributed_worker.log | tail -5"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        print(f"\\n[{{datetime.now().strftime('%H:%M:%S')}}] {worker_id} 最新动态:")
        if result.stdout:
            print(result.stdout)
        else:
            print("等待活动...")
        
        # 检查任务完成情况
        task_cmd = f"grep '{worker_id}' distributed_worker.log | grep '任务完成' | tail -3"
        task_result = subprocess.run(task_cmd, shell=True, capture_output=True, text=True)
        
        if task_result.stdout:
            print("最近完成的任务:")
            print(task_result.stdout)
        
        time.sleep(5)
        
    except KeyboardInterrupt:
        print(f"\\n=== 停止监控 {worker_id} ===")
        break
    except Exception as e:
        print(f"监控错误: {{e}}")
        time.sleep(10)
'''
    
    # 写入临时脚本文件
    script_file = f"monitor_{worker_id}.py"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(monitor_script)
    
    # 启动新的终端窗口
    title = f"监控节点 {worker_id}"
    cmd = f'start "{title}" cmd /k "python {script_file}"'
    subprocess.run(cmd, shell=True)
    
    return script_file

def start_master_monitor():
    """启动主节点监控终端"""
    monitor_script = '''
import time
import subprocess
from datetime import datetime

print("=== 主节点实时监控 ===")
print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("-" * 50)

while True:
    try:
        # 检查主节点状态
        cmd = "tail -3 distributed_master.log"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        print(f"\\n[{datetime.now().strftime('%H:%M:%S')}] 主节点状态:")
        if result.stdout:
            print(result.stdout)
        
        # 检查API状态
        api_cmd = "curl -s http://localhost:8000/"
        api_result = subprocess.run(api_cmd, shell=True, capture_output=True, text=True)
        
        if api_result.returncode == 0:
            print("主节点API: 正常运行")
        else:
            print("主节点API: 连接失败")
        
        # 检查工作节点连接
        worker_cmd = "grep '心跳更新' distributed_master.log | tail -3"
        worker_result = subprocess.run(worker_cmd, shell=True, capture_output=True, text=True)
        
        if worker_result.stdout:
            print("最近心跳更新:")
            print(worker_result.stdout)
        
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\\n=== 停止监控主节点 ===")
        break
    except Exception as e:
        print(f"监控错误: {e}")
        time.sleep(10)
'''
    
    # 写入临时脚本文件
    script_file = "monitor_master.py"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(monitor_script)
    
    # 启动新的终端窗口
    title = "监控主节点"
    cmd = f'start "{title}" cmd /k "python {script_file}"'
    subprocess.run(cmd, shell=True)
    
    return script_file

def main():
    """主函数"""
    print("分布式爬虫系统 - 独立节点监控器")
    print("=" * 50)
    
    # 获取当前活跃的工作节点
    active_workers = get_active_workers()
    
    if not active_workers:
        print("未找到活跃的工作节点")
        return
    
    print(f"发现 {len(active_workers)} 个活跃工作节点:")
    for worker in active_workers:
        print(f"- {worker}")
    
    print("\n正在启动独立监控终端...")
    
    # 启动主节点监控
    print("启动主节点监控终端...")
    start_master_monitor()
    time.sleep(2)
    
    # 启动每个工作节点的监控
    script_files = []
    for worker in active_workers:
        print(f"启动工作节点 {worker} 监控终端...")
        script_file = start_worker_monitor(worker)
        script_files.append(script_file)
        time.sleep(1)  # 避免同时启动过多窗口
    
    print(f"\n已启动 {len(active_workers) + 1} 个独立监控终端:")
    print("- 1个主节点监控终端")
    print(f"- {len(active_workers)}个工作节点监控终端")
    print("\n每个终端将独立显示对应节点的实时爬取动态")
    print("按 Ctrl+C 退出此脚本（监控终端将继续运行）")
    
    try:
        # 保持脚本运行
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n正在退出...")
        
        # 清理临时脚本文件
        for script_file in script_files:
            try:
                os.remove(script_file)
            except:
                pass
        try:
            os.remove("monitor_master.py")
        except:
            pass

if __name__ == "__main__":
    main()