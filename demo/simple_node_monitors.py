#!/usr/bin/env python3
"""
简单节点监控器 - 为每个工作节点启动独立的监控终端
"""

import subprocess
import time
import os

def start_monitor_window(title, command):
    """启动一个监控窗口"""
    # 创建批处理文件
    bat_content = f'''@echo off
title {title}
echo {title}
echo 开始时间: %date% %time%
echo ------------------------------
{command}
pause
'''
    
    bat_file = f"monitor_{title.replace(' ', '_')}.bat"
    with open(bat_file, 'w', encoding='gbk') as f:  # 使用GBK编码避免中文乱码
        f.write(bat_content)
    
    # 启动新窗口
    subprocess.Popen(f'start "{title}" cmd /c "{bat_file}"', shell=True)
    return bat_file

def main():
    print("分布式爬虫系统 - 独立节点监控器")
    print("=" * 50)
    
    # 工作节点列表
    workers = [
        "worker-95ccd08a",
        "worker-dbb70d77", 
        "worker-22e43c87",
        "worker-977359c1",
        "worker-02385af4",
        "worker-a4a44531"
    ]
    
    print(f"发现 {len(workers)} 个工作节点")
    
    # 启动主节点监控
    print("\n启动主节点监控终端...")
    master_command = '''powershell -Command "while($true) { Get-Content distributed_master.log -Tail 3; Write-Host '[$(Get-Date -Format \"HH:mm:ss\")] 主节点状态'; Start-Sleep 10 }"'''
    start_monitor_window("监控主节点", master_command)
    time.sleep(2)
    
    # 启动工作节点监控
    print("启动工作节点监控终端...")
    bat_files = []
    
    for worker in workers:
        print(f"启动监控终端: {worker}")
        worker_command = f'''powershell -Command "while($true) {{ Get-Content distributed_worker.log | Select-String '{worker}' | Select-Object -Last 5; Write-Host '[$(Get-Date -Format \"HH:mm:ss\")] {worker} 最新动态'; Start-Sleep 5 }}"'''
        bat_file = start_monitor_window(f"监控节点 {worker}", worker_command)
        bat_files.append(bat_file)
        time.sleep(1)
    
    print(f"\n已启动 {len(workers) + 1} 个独立监控终端:")
    print("- 1个主节点监控终端")
    print(f"- {len(workers)}个工作节点监控终端")
    print("\n每个终端将独立显示对应节点的实时爬取动态")
    print("监控窗口已打开，请查看桌面上的新窗口")
    
    # 等待用户确认
    input("\n按Enter键退出此脚本（监控窗口将继续运行）...")
    
    # 清理临时文件
    print("清理临时文件...")
    for bat_file in bat_files:
        try:
            os.remove(bat_file)
        except:
            pass
    
    try:
        os.remove("monitor_监控主节点.bat")
    except:
        pass
    
    print("完成!")

if __name__ == "__main__":
    main()