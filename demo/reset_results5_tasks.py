#!/usr/bin/env python3
"""
重置results_5.json任务状态为pending，以便重新爬取
"""

import json
import os

def reset_results5_tasks():
    """重置results_5.json任务状态为pending"""
    results_file = "data/results/results_5.json"
    
    try:
        # 读取文件
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 重置所有任务状态为pending
        for task in data:
            task['status'] = 'pending'
            # 清除之前的处理信息
            if 'processed_at' in task:
                del task['processed_at']
            if 'worker_id' in task:
                del task['worker_id']
            if 'processing_time' in task:
                del task['processing_time']
            if 'crawl_method' in task:
                del task['crawl_method']
            if 'urls_attempted' in task:
                del task['urls_attempted']
            if 'urls_successful' in task:
                del task['urls_successful']
            if 'data_quality_score' in task:
                del task['data_quality_score']
            
            # 重置结果数组
            task['results'] = []
            
            # 重置质量统计
            task['quality_stats'] = {
                "total_articles": 0,
                "valid_articles": 0,
                "invalid_articles": 0,
                "quality_issues": []
            }
        
        # 保存文件
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 成功重置 {len(data)} 个任务状态为pending")
        
        # 显示任务列表
        for task in data:
            print(f"   - {task['task_id']}: {task['keyword']}")
            
        return True
        
    except Exception as e:
        print(f"❌ 重置任务失败: {e}")
        return False

if __name__ == "__main__":
    reset_results5_tasks()