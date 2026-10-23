#!/usr/bin/env python3
"""
修复tasks_6.json中2000-2009年早期任务缺少keyword字段的问题
"""

import json
import os
from datetime import datetime

def fix_tasks_keyword():
    """修复tasks_6.json中缺少keyword字段的任务"""
    
    # 文件路径
    tasks_file = "data/tasks_6.json"
    backup_file = "data/tasks_6.json.backup"
    
    # 读取tasks_6.json
    if not os.path.exists(tasks_file):
        print(f"错误: 文件 {tasks_file} 不存在")
        return False
    
    # 创建备份
    import shutil
    shutil.copy2(tasks_file, backup_file)
    print(f"已创建备份文件: {backup_file}")
    
    # 读取数据
    with open(tasks_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    print(f"原始任务数量: {len(tasks)}")
    
    # 定义早期非洲相关关键词
    early_africa_keywords = [
        "african development", "china africa cooperation", "african infrastructure", 
        "african trade", "african investment", "african economy", "african politics",
        "african conflicts", "african peacekeeping", "african health", "african education",
        "african agriculture", "african technology", "african culture", "african environment"
    ]
    
    # 修复缺少keyword字段的任务
    fixed_count = 0
    for task in tasks:
        # 检查是否缺少keyword字段
        if 'keyword' not in task:
            # 根据title推断合适的keyword
            title = task.get('title', '')
            year = task.get('year', 2000)
            
            # 为早期非洲新闻任务选择合适的keyword
            if '早期非洲新闻' in title:
                # 根据年份选择不同的关键词
                keyword_index = (year - 2000) % len(early_africa_keywords)
                task['keyword'] = early_africa_keywords[keyword_index]
                
                # 添加其他必要字段
                task['category'] = 'early_africa_news'
                task['priority_weight'] = 1
                task['attempts'] = 0
                
                fixed_count += 1
                print(f"修复任务: {task['task_id']} - 添加keyword: {task['keyword']}")
    
    print(f"修复了 {fixed_count} 个任务的keyword字段")
    
    # 保存修复后的数据
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
    
    print(f"已保存修复后的数据到: {tasks_file}")
    
    # 验证修复结果
    with open(tasks_file, 'r', encoding='utf-8') as f:
        updated_tasks = json.load(f)
    
    # 检查是否还有缺少keyword的任务
    missing_keyword_count = sum(1 for task in updated_tasks if 'keyword' not in task)
    print(f"修复后缺少keyword的任务数量: {missing_keyword_count}")
    
    if missing_keyword_count == 0:
        print("✅ 所有任务都已修复，keyword字段完整")
        return True
    else:
        print("❌ 仍有任务缺少keyword字段")
        return False

def verify_tasks_structure():
    """验证任务结构完整性"""
    
    tasks_file = "data/tasks_6.json"
    
    with open(tasks_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    print("\n=== 任务结构验证 ===")
    
    # 检查关键字段
    required_fields = ['task_id', 'keyword', 'year', 'status']
    optional_fields = ['category', 'priority', 'priority_weight', 'attempts', 'created_at']
    
    for field in required_fields:
        missing_count = sum(1 for task in tasks if field not in task)
        print(f"缺少 {field} 字段的任务数量: {missing_count}")
    
    # 显示前5个任务的结构
    print("\n前5个任务的结构示例:")
    for i, task in enumerate(tasks[:5]):
        print(f"任务 {i+1}:")
        for key, value in task.items():
            print(f"  {key}: {value}")
        print()
    
    # 显示修复后的早期任务示例
    early_tasks = [task for task in tasks if task.get('year', 0) < 2010]
    if early_tasks:
        print(f"\n早期任务示例 (共{len(early_tasks)}个):")
        for i, task in enumerate(early_tasks[:3]):
            print(f"早期任务 {i+1}:")
            for key, value in task.items():
                print(f"  {key}: {value}")
            print()

if __name__ == "__main__":
    print("=== 开始修复tasks_6.json中缺少keyword字段的任务 ===")
    
    # 修复任务
    success = fix_tasks_keyword()
    
    if success:
        # 验证修复结果
        verify_tasks_structure()
        print("\n✅ 修复完成！")
    else:
        print("\n❌ 修复失败！")