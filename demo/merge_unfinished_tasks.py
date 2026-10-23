import json
import os
import glob
from datetime import datetime
import hashlib

def load_tasks_from_file(file_path):
    """从文件加载任务"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 检查数据类型
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'tasks' in data:
            return data['tasks']
        else:
            print(f"文件 {file_path} 格式不支持")
            return []
            
    except Exception as e:
        print(f"读取 {file_path} 失败: {e}")
        return []

def is_valid_task(task):
    """检查任务是否有效"""
    if not isinstance(task, dict):
        return False
    
    required_fields = ['task_id', 'title', 'year']
    for field in required_fields:
        if field not in task:
            return False
    
    return True

def generate_task_id(title, year):
    """生成唯一的任务ID"""
    unique_str = f"{title}_{year}_{datetime.now().timestamp()}"
    return hashlib.md5(unique_str.encode()).hexdigest()

def merge_unfinished_tasks():
    """合并所有未完成任务到任务库"""
    print("=== 开始合并未完成任务 ===")
    
    # 加载现有的任务库
    existing_tasks = []
    if os.path.exists("data/tasks_6.json"):
        with open("data/tasks_6.json", 'r', encoding='utf-8') as f:
            existing_tasks = json.load(f)
    
    existing_task_ids = {task['task_id'] for task in existing_tasks if 'task_id' in task}
    print(f"现有任务库: {len(existing_tasks)} 个任务")
    
    # 收集所有未完成任务
    all_unfinished_tasks = []
    
    # 1. 从任务文件中收集
    task_files = glob.glob("data/tasks_*.json")
    for task_file in task_files:
        tasks = load_tasks_from_file(task_file)
        
        # 过滤出未完成的任务
        unfinished = [t for t in tasks if isinstance(t, dict) and t.get('status') == 'pending']
        
        # 去重并添加到总列表
        for task in unfinished:
            if is_valid_task(task) and task['task_id'] not in existing_task_ids:
                all_unfinished_tasks.append(task)
                existing_task_ids.add(task['task_id'])
        
        print(f"从 {os.path.basename(task_file)} 提取 {len(unfinished)} 个未完成任务")
    
    # 2. 从特殊文件中收集
    special_files = [
        "data/20000_crawling_tasks_20251126_100526.json"
    ]
    
    for file_path in special_files:
        if os.path.exists(file_path):
            tasks = load_tasks_from_file(file_path)
            
            # 过滤出未完成的任务
            unfinished = [t for t in tasks if isinstance(t, dict) and t.get('status') == 'pending']
            
            # 去重并添加到总列表
            for task in unfinished:
                if is_valid_task(task) and task['task_id'] not in existing_task_ids:
                    all_unfinished_tasks.append(task)
                    existing_task_ids.add(task['task_id'])
            
            print(f"从 {os.path.basename(file_path)} 提取 {len(unfinished)} 个未完成任务")
    
    # 3. 添加年份较早的新任务（如果未完成任务不足）
    if len(all_unfinished_tasks) < 1000:
        print("未完成任务较少，添加年份较早的新任务...")
        
        # 添加2000-2009年的早期任务
        early_years = list(range(2000, 2010))
        for year in early_years:
            for i in range(10):  # 每个年份添加10个任务
                task_id = generate_task_id(f"早期非洲新闻_{year}_第{i+1}篇", year)
                
                new_task = {
                    'task_id': task_id,
                    'title': f"早期非洲新闻_{year}_第{i+1}篇",
                    'year': year,
                    'status': 'pending',
                    'created_at': datetime.now().isoformat(),
                    'priority': 'high' if year <= 2005 else 'medium'
                }
                
                if task_id not in existing_task_ids:
                    all_unfinished_tasks.append(new_task)
                    existing_task_ids.add(task_id)
        
        print(f"添加了 {len(early_years) * 10} 个早期年份任务")
    
    # 合并所有任务
    merged_tasks = existing_tasks + all_unfinished_tasks
    
    print(f"\n合并后总任务数: {len(merged_tasks)}")
    print(f"新增任务数: {len(all_unfinished_tasks)}")
    
    # 按年份统计
    year_stats = {}
    for task in merged_tasks:
        year = task.get('year', 'unknown')
        year_stats[year] = year_stats.get(year, 0) + 1
    
    print(f"年份分布: {dict(sorted(year_stats.items()))}")
    
    # 保存合并后的任务库
    with open("data/tasks_6.json", 'w', encoding='utf-8') as f:
        json.dump(merged_tasks, f, ensure_ascii=False, indent=2)
    
    print(f"\n任务库已更新并保存到 data/tasks_6.json")
    
    return merged_tasks

def update_results_file():
    """更新results_6.json文件以匹配新的任务库"""
    print("\n=== 更新结果文件 ===")
    
    # 加载现有的结果文件
    existing_results = []
    if os.path.exists("data/results/results_6.json"):
        with open("data/results/results_6.json", 'r', encoding='utf-8') as f:
            existing_results = json.load(f)
    
    # 加载新的任务库
    with open("data/tasks_6.json", 'r', encoding='utf-8') as f:
        new_tasks = json.load(f)
    
    # 创建任务ID到结果的映射
    result_map = {}
    for result in existing_results:
        if 'task_id' in result:
            result_map[result['task_id']] = result
    
    # 创建新的结果列表
    new_results = []
    for task in new_tasks:
        task_id = task['task_id']
        
        if task_id in result_map:
            # 保留现有的结果
            new_results.append(result_map[task_id])
        else:
            # 创建新的待处理结果
            new_result = {
                'task_id': task_id,
                'title': task.get('title', ''),
                'year': task.get('year', 2024),
                'status': 'pending',
                'results': [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            new_results.append(new_result)
    
    # 保存更新后的结果文件
    with open("data/results/results_6.json", 'w', encoding='utf-8') as f:
        json.dump(new_results, f, ensure_ascii=False, indent=2)
    
    print(f"结果文件已更新: {len(new_results)} 个任务")
    
    # 统计状态
    completed = sum(1 for r in new_results if r.get('status') == 'completed')
    pending = sum(1 for r in new_results if r.get('status') == 'pending')
    
    print(f"已完成: {completed}, 待处理: {pending}")

def main():
    """主函数"""
    print("开始整合未完成任务到任务库...\n")
    
    # 合并未完成任务
    merged_tasks = merge_unfinished_tasks()
    
    # 更新结果文件
    update_results_file()
    
    print("\n=== 整合完成 ===")
    print(f"任务库现在包含 {len(merged_tasks)} 个任务")
    print("持续监控爬虫系统将自动处理这些任务")

if __name__ == "__main__":
    main()