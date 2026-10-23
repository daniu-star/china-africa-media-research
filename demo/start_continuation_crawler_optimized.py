#!/usr/bin/env python3
"""
优化的断点续爬系统 - 解决数据重合问题
从results_4.json继续爬取，保存到results_5.json
确保任务ID不重复，避免数据重合
"""

import json
import os
import time
import logging
from pathlib import Path
from datetime import datetime
import requests
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('continuation_crawler_optimized.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_results_progress():
    """检查爬取进度，确保任务ID不重复"""
    results_dir = Path("data/results")
    results_4_path = results_dir / "results_4.json"
    results_5_path = results_dir / "results_5.json"
    
    if not results_4_path.exists():
        logger.error("results_4.json文件不存在，无法继续爬取")
        return None
    
    # 读取results_4.json中的任务ID
    with open(results_4_path, 'r', encoding='utf-8') as f:
        results_4_data = json.load(f)
    
    existing_task_ids = set()
    for task in results_4_data:
        if task.get('status') == 'completed':
            existing_task_ids.add(task['task_id'])
    
    logger.info(f"results_4.json中已完成的task_id数量: {len(existing_task_ids)}")
    
    # 检查results_5.json是否存在，如果存在则读取已处理的任务
    processed_task_ids = set()
    if results_5_path.exists():
        with open(results_5_path, 'r', encoding='utf-8') as f:
            results_5_data = json.load(f)
        for task in results_5_data:
            if task.get('status') == 'completed':
                processed_task_ids.add(task['task_id'])
    
    # 计算需要处理的任务
    pending_task_ids = existing_task_ids - processed_task_ids
    logger.info(f"需要处理的任务数量: {len(pending_task_ids)}")
    
    return {
        'existing_task_ids': existing_task_ids,
        'processed_task_ids': processed_task_ids,
        'pending_task_ids': pending_task_ids,
        'results_4_path': results_4_path,
        'results_5_path': results_5_path
    }

def start_worker_optimized():
    """启动优化的工作节点"""
    try:
        # 检查工作节点是否已经在运行
        response = requests.get("http://localhost:8001/workers/status", timeout=10)
        if response.status_code == 200:
            logger.info("工作节点已在运行")
            return True
    except requests.exceptions.RequestException:
        logger.info("工作节点未运行，正在启动...")
        
        # 启动工作节点
        import subprocess
        try:
            worker_process = subprocess.Popen([
                sys.executable, "distributed_worker_fixed.py"
            ], cwd=os.getcwd())
            logger.info("工作节点启动成功")
            time.sleep(5)  # 等待工作节点启动完成
            return True
        except Exception as e:
            logger.error(f"启动工作节点失败: {e}")
            return False

def check_master_availability():
    """检查主节点可用性，增加重试机制"""
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
                time.sleep(5)  # 等待5秒后重试
            else:
                logger.error(f"主节点不可用: {e}")
                return False
    return False

def monitor_workers():
    """监控工作节点状态"""
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

def start_continuation_crawl():
    """开始断点续爬"""
    logger.info("=== 开始优化断点续爬系统 ===")
    
    # 1. 检查爬取进度
    progress_info = check_results_progress()
    if not progress_info:
        logger.error("无法获取爬取进度信息")
        return False
    
    if len(progress_info['pending_task_ids']) == 0:
        logger.info("所有任务已完成，无需继续爬取")
        return True
    
    # 2. 检查主节点可用性
    if not check_master_availability():
        logger.error("主节点不可用，请先启动主节点")
        return False
    
    # 3. 启动工作节点
    if not start_worker_optimized():
        logger.error("无法启动工作节点")
        return False
    
    # 4. 监控爬取进度
    logger.info("开始监控爬取进度...")
    max_wait_time = 3600  # 最大等待时间：1小时
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        # 检查工作节点状态
        if not monitor_workers():
            logger.warning("没有活跃的工作节点")
            time.sleep(30)
            continue
        
        # 检查爬取进度
        progress_info = check_results_progress()
        if not progress_info:
            time.sleep(60)
            continue
        
        pending_count = len(progress_info['pending_task_ids'])
        processed_count = len(progress_info['processed_task_ids'])
        total_count = len(progress_info['existing_task_ids'])
        
        logger.info(f"爬取进度: {processed_count}/{total_count} (剩余: {pending_count})")
        
        if pending_count == 0:
            logger.info("所有任务已完成！")
            break
        
        time.sleep(60)  # 每分钟检查一次进度
    
    # 5. 检查最终结果
    progress_info = check_results_progress()
    if progress_info and len(progress_info['pending_task_ids']) == 0:
        logger.info("断点续爬完成！")
        return True
    else:
        logger.warning("断点续爬超时或未完成")
        return False

def main():
    """主函数"""
    logger.info("=== 优化的断点续爬系统启动 ===")
    logger.info("从results_4.json继续爬取，保存到results_5.json")
    logger.info("确保任务ID不重复，避免数据重合问题")
    
    try:
        success = start_continuation_crawl()
        if success:
            logger.info("断点续爬成功完成！")
        else:
            logger.error("断点续爬失败")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()