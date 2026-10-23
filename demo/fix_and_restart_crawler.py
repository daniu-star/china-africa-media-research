import json
import os
import subprocess
import time
from datetime import datetime

def fix_json_files():
    """修复JSON文件格式错误"""
    print("🔧 开始修复JSON文件格式错误...")
    
    # 修复任务文件
    task_files = [f for f in os.listdir('data') if f.startswith('tasks_') and f.endswith('.json')]
    fixed_count = 0
    
    for task_file in task_files:
        file_path = os.path.join('data', task_file)
        try:
            # 尝试读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否是有效的JSON
            try:
                json.loads(content)
                print(f"  ✅ {task_file}: 格式正常")
                continue
            except json.JSONDecodeError as e:
                print(f"  ⚠️ {task_file}: 格式错误 - {e}")
                
            # 备份原文件
            backup_path = file_path + '.backup'
            if not os.path.exists(backup_path):
                os.rename(file_path, backup_path)
                print(f"    已创建备份: {backup_path}")
            
            # 修复JSON格式
            # 方法1: 尝试解析每行JSON对象
            lines = content.strip().split('\n')
            valid_objects = []
            
            for line in lines:
                line = line.strip()
                if line and line not in ['[', ']', ',']:
                    try:
                        obj = json.loads(line)
                        valid_objects.append(obj)
                    except:
                        pass
            
            # 如果找到有效对象，保存为JSON数组
            if valid_objects:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(valid_objects, f, ensure_ascii=False, indent=2)
                print(f"    ✅ 修复成功: 找到 {len(valid_objects)} 个有效对象")
                fixed_count += 1
            else:
                print(f"    ❌ 无法修复: 未找到有效JSON对象")
                
        except Exception as e:
            print(f"  ❌ {task_file}: 修复失败 - {e}")
    
    print(f"\n📊 修复完成: 共修复 {fixed_count} 个任务文件")
    return fixed_count

def check_crawler_status():
    """检查爬虫系统状态"""
    print("\n🔍 检查爬虫系统状态...")
    
    # 检查主节点是否运行
    try:
        import requests
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("  ✅ 分布式主节点: 运行正常")
            return True
        else:
            print("  ⚠️ 分布式主节点: 响应异常")
            return False
    except:
        print("  ❌ 分布式主节点: 无法连接")
        return False

def restart_crawler_system():
    """重启爬虫系统"""
    print("\n🔄 重启爬虫系统...")
    
    # 停止现有进程
    print("  停止现有进程...")
    try:
        # 查找并终止相关Python进程
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                      capture_output=True, timeout=10)
        time.sleep(2)
    except:
        pass
    
    # 重新启动系统
    print("  启动分布式主节点...")
    master_process = subprocess.Popen(['python', 'distributed_master.py'], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
    
    time.sleep(5)  # 等待主节点启动
    
    print("  启动工作节点...")
    worker_process = subprocess.Popen(['python', 'start_multiple_workers_stable.py', '--workers', '6'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
    
    print("  ⏳ 等待系统初始化...")
    time.sleep(10)
    
    # 检查系统状态
    if check_crawler_status():
        print("  ✅ 爬虫系统重启成功")
        return True
    else:
        print("  ❌ 爬虫系统重启失败")
        return False

def main():
    print("=== 分布式爬虫系统修复与重启 ===\n")
    
    # 1. 修复JSON文件
    fixed_count = fix_json_files()
    
    # 2. 检查当前状态
    current_status = check_crawler_status()
    
    # 3. 重启系统
    if fixed_count > 0 or not current_status:
        print("\n🚀 需要重启系统以应用修复...")
        if restart_crawler_system():
            print("\n🎉 系统修复和重启完成！")
            print("📊 建议检查:")
            print("  - 数据文件是否开始更新")
            print("  - 任务队列是否正常处理")
            print("  - 系统日志是否有错误信息")
        else:
            print("\n❌ 系统重启失败，请手动检查")
    else:
        print("\n✅ 系统运行正常，无需重启")
        print("💡 如果数据仍未更新，请检查:")
        print("  - 网络连接状态")
        print("  - 目标网站可访问性")
        print("  - 反爬虫限制")

if __name__ == "__main__":
    main()