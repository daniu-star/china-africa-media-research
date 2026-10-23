#!/usr/bin/env python3
"""
results_5.json专用爬虫系统
专门处理results_5.json中的新任务，避免重复检测问题
"""

import json
import os
import time
import logging
import requests
import sys
from pathlib import Path
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('results5_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_results5_tasks():
    """检查results_5.json中的任务状态"""
    results5_path = Path("data/results/results_5.json")
    
    if not results5_path.exists():
        logger.error("results_5.json文件不存在")
        return None
    
    # 读取results_5.json中的任务
    with open(results5_path, 'r', encoding='utf-8') as f:
        results5_data = json.load(f)
    
    # 统计任务状态
    pending_tasks = []
    completed_tasks = []
    
    for task in results5_data:
        if task.get('status') == 'pending':
            pending_tasks.append(task)
        elif task.get('status') == 'completed':
            completed_tasks.append(task)
    
    logger.info(f"results_5.json任务统计: 待处理 {len(pending_tasks)}, 已完成 {len(completed_tasks)}")
    
    return {
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'total_tasks': len(results5_data)
    }

def check_master_availability():
    """检查主节点可用性"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"主节点状态: {data.get('status', 'unknown')}")
                return True
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                logger.warning(f"主节点检查失败，尝试 {attempt + 1}/{max_retries}: {e}")
                time.sleep(5)
            else:
                logger.error(f"主节点不可用: {e}")
                return False
    return False

def check_worker_availability():
    """检查工作节点可用性"""
    try:
        response = requests.get("http://localhost:8000/workers/status", timeout=10)
        if response.status_code == 200:
            workers = response.json()
            active_workers = [w for w in workers if w.get('status') == 'active']
            logger.info(f"活跃工作节点数量: {len(active_workers)}")
            return len(active_workers) > 0
    except requests.exceptions.RequestException:
        logger.warning("无法获取工作节点状态")
        return False

def submit_task_to_master(task_data):
    """将任务提交到主节点"""
    try:
        # 准备任务数据
        task_to_submit = {
            'task_id': task_data['task_id'],
            'keyword': task_data['keyword'],
            'year': task_data['year'],
            'language': task_data.get('language', 'unknown'),
            'priority': 'medium'
        }
        
        response = requests.post(
            "http://localhost:8000/tasks",
            json=task_to_submit,
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"成功提交任务: {task_data['task_id']}")
            return True
        elif response.status_code == 409:
            logger.warning(f"任务已存在（重复检测）: {task_data['task_id']}")
            return False
        else:
            logger.error(f"提交任务失败: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"提交任务时出错: {e}")
        return False

def update_results5_status(task_id, status, results=None):
    """更新results_5.json中的任务状态"""
    try:
        results5_path = Path("data/results/results_5.json")
        
        with open(results5_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 更新任务状态
        for task in data:
            if task['task_id'] == task_id:
                task['status'] = status
                task['processed_at'] = datetime.now().isoformat()
                task['worker_id'] = 'results5-crawler'
                
                if results:
                    task['results'] = results
                    task['quality_stats'] = {
                        'total_articles': len(results),
                        'valid_articles': len(results),
                        'invalid_articles': 0,
                        'quality_issues': []
                    }
                    task['data_quality_score'] = 1.0
                
                break
        
        # 写回文件
        with open(results5_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"已更新任务状态: {task_id} -> {status}")
        return True
        
    except Exception as e:
        logger.error(f"更新任务状态失败: {e}")
        return False

def monitor_task_progress(task_id, max_wait_time=600):
    """监控任务进度"""
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            # 检查任务状态
            response = requests.get(f"http://localhost:8000/tasks/{task_id}", timeout=10)
            
            if response.status_code == 200:
                task_info = response.json()
                status = task_info.get('status')
                
                if status == 'completed':
                    logger.info(f"任务完成: {task_id}")
                    return True
                elif status == 'failed':
                    logger.warning(f"任务失败: {task_id}")
                    return False
                else:
                    logger.debug(f"任务状态: {status}")
            
            time.sleep(30)  # 每30秒检查一次
            
        except Exception as e:
            logger.warning(f"检查任务状态失败: {e}")
            time.sleep(30)
    
    logger.warning(f"任务监控超时: {task_id}")
    return False

def start_results5_crawler():
    """启动results_5.json爬虫"""
    logger.info("=== 启动results_5.json专用爬虫系统 ===")
    
    # 1. 检查系统状态
    if not check_master_availability():
        logger.error("主节点不可用")
        return False
    
    if not check_worker_availability():
        logger.error("没有活跃的工作节点")
        return False
    
    # 2. 检查results_5.json中的任务
    task_info = check_results5_tasks()
    if not task_info:
        logger.error("无法获取任务信息")
        return False
    
    if len(task_info['pending_tasks']) == 0:
        logger.info("没有待处理的任务")
        return True
    
    logger.info(f"发现 {len(task_info['pending_tasks'])} 个待处理任务")
    
    # 3. 逐个处理任务
    successful_tasks = 0
    failed_tasks = 0
    
    for task in task_info['pending_tasks']:
        task_id = task['task_id']
        keyword = task['keyword']
        
        logger.info(f"开始处理任务: {task_id} - {keyword}")
        
        # 提交任务到主节点
        if submit_task_to_master(task):
            # 监控任务进度
            if monitor_task_progress(task_id):
                # 任务完成，更新状态
                update_results5_status(task_id, 'completed')
                successful_tasks += 1
                logger.info(f"任务处理成功: {task_id}")
            else:
                # 任务失败
                update_results5_status(task_id, 'failed')
                failed_tasks += 1
                logger.error(f"任务处理失败: {task_id}")
        else:
            # 提交失败
            failed_tasks += 1
            logger.error(f"任务提交失败: {task_id}")
        
        # 任务间延迟，避免过载
        time.sleep(10)
    
    # 4. 输出最终结果
    logger.info(f"处理完成: 成功 {successful_tasks}, 失败 {failed_tasks}")
    
    if successful_tasks > 0:
        logger.info("results_5.json爬虫任务完成！")
        return True
    else:
        logger.error("所有任务处理失败")
        return False

def main():
    """主函数"""
    logger.info("=== results_5.json专用爬虫系统启动 ===")
    
    try:
        success = start_results5_crawler()
        if success:
            logger.info("爬虫任务成功完成！")
        else:
            logger.error("爬虫任务失败")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()