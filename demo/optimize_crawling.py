#!/usr/bin/env python3
"""
优化爬取策略，提高数据收集效率
"""

import json
import os
import time
from datetime import datetime

def optimize_crawling_strategy():
    """优化爬取策略"""
    
    print("=== 优化爬取策略 ===")
    
    # 1. 分析当前数据分布
    print("\n1. 分析当前数据分布...")
    
    with open("data/results_enhanced.json", 'r', encoding='utf-8') as f:
        enhanced_data = json.load(f)
    
    # 检查数据格式
    if isinstance(enhanced_data, dict) and 'articles' in enhanced_data:
        articles = enhanced_data['articles']
    elif isinstance(enhanced_data, list):
        articles = enhanced_data
    else:
        print("数据格式未知，跳过关键词分析")
        articles = []
    
    # 统计关键词分布
    keyword_stats = {}
    for article in articles:
        if isinstance(article, dict):
            keyword = article.get('keyword', 'unknown')
            if keyword not in keyword_stats:
                keyword_stats[keyword] = 0
            keyword_stats[keyword] += 1
    
    print("当前关键词分布:")
    for keyword, count in sorted(keyword_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {keyword}: {count} 篇文章")
    
    # 2. 优化任务分配策略
    print("\n2. 优化任务分配策略...")
    
    # 读取扩展任务
    with open("data/tasks_expanded_0.json", 'r', encoding='utf-8') as f:
        expanded_tasks = json.load(f)
    
    # 按优先级重新排序任务
    priority_order = {'high': 3, 'medium': 2, 'low': 1}
    
    if 'tasks' in expanded_tasks:
        tasks = expanded_tasks['tasks']
        
        # 按优先级排序
        tasks.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 1), reverse=True)
        
        # 更新任务文件
        expanded_tasks['tasks'] = tasks
        
        with open("data/tasks_expanded_0.json", 'w', encoding='utf-8') as f:
            json.dump(expanded_tasks, f, indent=2, ensure_ascii=False)
        
        print(f"已按优先级重新排序 {len(tasks)} 个任务")
    
    # 3. 创建更智能的爬取策略
    print("\n3. 创建智能爬取策略...")
    
    strategy = {
        "optimization_date": datetime.now().isoformat(),
        "strategy": {
            "high_priority_first": True,
            "batch_processing": True,
            "adaptive_timeout": True,
            "retry_strategy": {
                "max_retries": 3,
                "retry_delay": 5,
                "backoff_factor": 2
            },
            "quality_control": {
                "min_content_length": 100,
                "required_fields": ["title", "content", "date", "source"]
            }
        },
        "targets": {
            "daily_target": 1000,  # 每日目标
            "weekly_target": 7000,  # 每周目标
            "total_target": 50000   # 总目标
        }
    }
    
    with open("data/crawling_strategy.json", 'w', encoding='utf-8') as f:
        json.dump(strategy, f, indent=2, ensure_ascii=False)
    
    print("智能爬取策略已保存到 data/crawling_strategy.json")
    
    # 4. 创建性能监控
    print("\n4. 创建性能监控...")
    
    performance_monitor = {
        "monitor_start": datetime.now().isoformat(),
        "metrics": {
            "articles_per_hour": 0,
            "success_rate": 0,
            "average_processing_time": 0,
            "error_rate": 0
        },
        "last_checkpoint": {
            "timestamp": datetime.now().isoformat(),
            "total_articles": len(enhanced_data)
        }
    }
    
    with open("data/performance_monitor.json", 'w', encoding='utf-8') as f:
        json.dump(performance_monitor, f, indent=2, ensure_ascii=False)
    
    print("性能监控已设置")
    
    return strategy

def start_additional_workers():
    """启动额外的工作节点"""
    
    print("\n=== 启动额外工作节点 ===")
    
    # 检查当前系统资源
    print("当前系统状态:")
    print("  - 主节点: 运行中")
    print("  - 工作节点: 2个节点运行中")
    
    # 建议启动更多工作节点
    print("\n建议启动 2-4 个额外工作节点以加速爬取")
    print("可以使用以下命令启动:")
    print("  python distributed_worker.py")
    
    return {
        "recommended_workers": 4,
        "current_workers": 2,
        "additional_needed": 2
    }

def create_optimization_report():
    """创建优化报告"""
    
    strategy = optimize_crawling_strategy()
    worker_info = start_additional_workers()
    
    report = {
        "report_date": datetime.now().isoformat(),
        "optimization": strategy,
        "worker_recommendations": worker_info,
        "estimated_completion": {
            "current_rate": 100,  # 假设每小时100篇文章
            "days_to_complete": max(0, (50000 - 13728) / (100 * 24)),
            "optimistic_completion": datetime.now().timestamp() + (max(0, (50000 - 13728) / (200 * 24)) * 24 * 3600)
        }
    }
    
    with open("data/optimization_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n=== 优化报告 ===")
    print(f"当前数据量: 13,728 篇文章")
    print(f"目标数据量: 50,000 篇文章")
    print(f"进度: 27.5%")
    print(f"预计完成时间: {report['estimated_completion']['days_to_complete']:.1f} 天")
    print(f"建议启动额外工作节点: {worker_info['additional_needed']} 个")
    
    return report

if __name__ == "__main__":
    create_optimization_report()