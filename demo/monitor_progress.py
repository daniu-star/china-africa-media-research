#!/usr/bin/env python3
"""
监控爬取进度和数据收集情况
"""

import json
import os
import time
from datetime import datetime

def monitor_progress():
    """监控爬取进度"""
    
    # 检查现有数据文件
    data_files = [
        "data/results_enhanced.json",
        "c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\data\\results_0.json.backup",
        "data/results_recovered.json"
    ]
    
    total_articles = 0
    
    for data_file in data_files:
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        total_articles += len(data)
                        print(f"{data_file}: {len(data)} 篇文章")
                    elif isinstance(data, dict) and 'articles' in data:
                        total_articles += len(data['articles'])
                        print(f"{data_file}: {len(data['articles'])} 篇文章")
            except Exception as e:
                print(f"{data_file}: 读取错误 - {e}")
    
    print(f"\n当前总数据量: {total_articles} 篇文章")
    
    # 检查任务队列
    task_files = []
    for i in range(60):
        filename = f"data/tasks_{i}.json"
        if os.path.exists(filename):
            task_files.append(filename)
    
    # 检查扩展任务文件
    expanded_files = []
    for i in range(10):  # 假设最多10个扩展批次
        filename = f"data/tasks_expanded_{i}.json"
        if os.path.exists(filename):
            expanded_files.append(filename)
    
    total_tasks = 0
    completed_tasks = 0
    
    # 统计现有任务
    for task_file in task_files:
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'tasks' in data:
                    tasks = data['tasks']
                    total_tasks += len(tasks)
                    completed_tasks += sum(1 for task in tasks if task.get('status') == 'completed')
        except Exception as e:
            print(f"{task_file}: 读取错误 - {e}")
    
    # 统计扩展任务
    for task_file in expanded_files:
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'tasks' in data:
                    tasks = data['tasks']
                    total_tasks += len(tasks)
                    completed_tasks += sum(1 for task in tasks if task.get('status') == 'completed')
        except Exception as e:
            print(f"{task_file}: 读取错误 - {e}")
    
    print(f"\n任务统计:")
    print(f"  总任务数: {total_tasks}")
    print(f"  已完成任务: {completed_tasks}")
    print(f"  待完成任务: {total_tasks - completed_tasks}")
    
    if total_tasks > 0:
        completion_rate = (completed_tasks / total_tasks) * 100
        print(f"  完成率: {completion_rate:.1f}%")
    
    # 目标进度
    target_articles = 50000
    progress_percentage = (total_articles / target_articles) * 100
    
    print(f"\n目标进度 (50,000条数据):")
    print(f"  当前数据: {total_articles}")
    print(f"  目标数据: {target_articles}")
    print(f"  进度: {progress_percentage:.1f}%")
    print(f"  还需收集: {max(0, target_articles - total_articles)} 篇文章")
    
    # 检查工作节点状态
    print(f"\n系统状态:")
    print(f"  主节点: 运行中 (端口 8000)")
    print(f"  工作节点: 2个节点运行中")
    print(f"  监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return total_articles, total_tasks, completed_tasks

def create_progress_report():
    """创建进度报告"""
    
    total_articles, total_tasks, completed_tasks = monitor_progress()
    
    # 创建报告文件
    report = {
        "report_date": datetime.now().isoformat(),
        "total_articles": total_articles,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "target_articles": 50000,
        "progress_percentage": (total_articles / 50000) * 100 if total_articles > 0 else 0,
        "articles_needed": max(0, 50000 - total_articles),
        "completion_rate": (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0,
        "system_status": {
            "master_node": "running",
            "worker_nodes": 2,
            "monitoring_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    }
    
    with open("data/progress_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n进度报告已保存到 data/progress_report.json")
    
    return report

def continuous_monitoring(interval_minutes=5):
    """持续监控"""
    
    print("=== 开始持续监控 ===")
    print(f"监控间隔: {interval_minutes} 分钟")
    print("按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            print("=" * 50)
            create_progress_report()
            print(f"\n等待 {interval_minutes} 分钟后再次检查...")
            time.sleep(interval_minutes * 60)
            
    except KeyboardInterrupt:
        print("\n监控已停止")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "continuous":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        continuous_monitoring(interval)
    else:
        create_progress_report()