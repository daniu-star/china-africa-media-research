import json
import os
import glob
from datetime import datetime

def analyze_task_files():
    """分析data文件夹中的所有任务文件"""
    print("=== 分析任务文件 ===")
    
    task_files = glob.glob("data/tasks_*.json")
    print(f"找到 {len(task_files)} 个任务文件")
    
    all_tasks = []
    unfinished_tasks = []
    
    for task_file in task_files:
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
                all_tasks.extend(tasks)
                
                # 统计未完成的任务
                pending_tasks = [t for t in tasks if t.get('status') == 'pending']
                unfinished_tasks.extend(pending_tasks)
                
                print(f"{os.path.basename(task_file)}: {len(tasks)} 个任务, {len(pending_tasks)} 个未完成")
                
        except Exception as e:
            print(f"读取 {task_file} 失败: {e}")
    
    print(f"\n总计: {len(all_tasks)} 个任务, {len(unfinished_tasks)} 个未完成")
    
    # 按年份统计未完成的任务
    year_stats = {}
    for task in unfinished_tasks:
        year = task.get('year', 'unknown')
        year_stats[year] = year_stats.get(year, 0) + 1
    
    print(f"未完成任务年份分布: {dict(sorted(year_stats.items()))}")
    
    return unfinished_tasks

def analyze_result_files():
    """分析所有结果文件"""
    print("\n=== 分析结果文件 ===")
    
    result_files = glob.glob("data/results_*.json")
    print(f"找到 {len(result_files)} 个结果文件")
    
    completed_tasks = []
    
    for result_file in result_files:
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
                
                # 统计已完成的任务
                completed = [r for r in results if r.get('status') == 'completed']
                completed_tasks.extend(completed)
                
                print(f"{os.path.basename(result_file)}: {len(results)} 个结果, {len(completed)} 个已完成")
                
        except Exception as e:
            print(f"读取 {result_file} 失败: {e}")
    
    print(f"\n总计: {len(completed_tasks)} 个已完成任务")
    
    return completed_tasks

def analyze_crawler_results():
    """分析crawler_results文件夹中的数据"""
    print("\n=== 分析爬取结果文件夹 ===")
    
    crawler_files = glob.glob("data/crawler_results/**/*.json.gz", recursive=True)
    print(f"找到 {len(crawler_files)} 个爬取结果文件")
    
    # 按文件夹分类统计
    folder_stats = {}
    for file_path in crawler_files:
        folder = os.path.dirname(file_path).split(os.sep)[-1]
        folder_stats[folder] = folder_stats.get(folder, 0) + 1
    
    print(f"文件夹分布: {folder_stats}")
    
    # 检查文件大小和修改时间
    recent_files = []
    for file_path in crawler_files:
        stat = os.stat(file_path)
        file_size = stat.st_size
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        
        if file_size > 1000:  # 只考虑有内容的文件
            recent_files.append({
                'path': file_path,
                'size': file_size,
                'modified': mod_time
            })
    
    print(f"有内容的文件: {len(recent_files)} 个")
    
    # 显示最近修改的文件
    recent_files.sort(key=lambda x: x['modified'], reverse=True)
    print("\n最近修改的5个文件:")
    for i, file_info in enumerate(recent_files[:5]):
        print(f"  {i+1}. {os.path.basename(file_info['path'])} - {file_info['size']} bytes - {file_info['modified']}")
    
    return recent_files

def analyze_special_data_files():
    """分析特殊数据文件"""
    print("\n=== 分析特殊数据文件 ===")
    
    special_files = [
        "data/20000_crawling_tasks_20251126_100526.json",
        "data/20000_data_strategy_20251126_100526.json",
        "data/results0.json",
        "data/articles_data_only_20251126_105235.json"
    ]
    
    for file_path in special_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if isinstance(data, list):
                    print(f"{os.path.basename(file_path)}: {len(data)} 条记录")
                    
                    # 如果是任务文件，统计状态
                    if 'tasks' in file_path.lower() or 'crawling' in file_path.lower():
                        pending = [t for t in data if t.get('status') == 'pending']
                        completed = [t for t in data if t.get('status') == 'completed']
                        print(f"  未完成: {len(pending)}, 已完成: {len(completed)}")
                    
                elif isinstance(data, dict):
                    print(f"{os.path.basename(file_path)}: 字典类型, {len(data)} 个键")
                    
            except Exception as e:
                print(f"读取 {file_path} 失败: {e}")
        else:
            print(f"{file_path}: 文件不存在")

def main():
    """主分析函数"""
    print("开始分析所有任务和数据文件...\n")
    
    # 分析任务文件
    unfinished_tasks = analyze_task_files()
    
    # 分析结果文件
    completed_tasks = analyze_result_files()
    
    # 分析爬取结果
    crawler_files = analyze_crawler_results()
    
    # 分析特殊数据文件
    analyze_special_data_files()
    
    # 总结
    print("\n=== 分析总结 ===")
    print(f"未完成任务总数: {len(unfinished_tasks)}")
    print(f"已完成任务总数: {len(completed_tasks)}")
    print(f"有内容的爬取文件: {len(crawler_files)}")
    
    # 建议
    if len(unfinished_tasks) > 0:
        print(f"\n建议: 将 {len(unfinished_tasks)} 个未完成任务导入任务库")
    else:
        print("\n建议: 需要创建新的任务，特别是年份较早的任务")

if __name__ == "__main__":
    main()