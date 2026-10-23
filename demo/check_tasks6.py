import json
import os

def check_tasks6_status():
    file_path = 'data/tasks_6.json'
    
    if not os.path.exists(file_path):
        print(f"文件 {file_path} 不存在")
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"tasks_6.json 文件大小: {len(data)} 条记录")
        
        # 统计状态分布
        status_counts = {}
        year_counts = {}
        
        for item in data:
            status = item.get('status', '无状态')
            year = item.get('year', '无年份')
            
            status_counts[status] = status_counts.get(status, 0) + 1
            year_counts[year] = year_counts.get(year, 0) + 1
        
        print("\n状态分布:")
        for status, count in status_counts.items():
            print(f"  {status}: {count} 条")
        
        print("\n年份分布:")
        for year, count in sorted(year_counts.items()):
            print(f"  {year}: {count} 条")
        
        # 检查pending状态的任务
        pending_tasks = [task for task in data if task.get('status') == 'pending']
        print(f"\n待处理任务 (pending): {len(pending_tasks)} 条")
        
        if pending_tasks:
            print("\n前5个待处理任务:")
            for i, task in enumerate(pending_tasks[:5]):
                title = task.get('title', '无标题')
                year = task.get('year', '无年份')
                print(f"  {i+1}. {title[:60]}... - {year}")
                
    except Exception as e:
        print(f"读取文件时出错: {e}")

if __name__ == "__main__":
    check_tasks6_status()