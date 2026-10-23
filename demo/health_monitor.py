#!/usr/bin/env python3
import time
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_system_health():
    # 检查系统健康状态
    try:
        # 检查主节点
        response = requests.get('http://127.0.0.1:8000/health', timeout=10)
        if response.status_code != 200:
            return False
        
        # 检查工作节点
        response = requests.get('http://127.0.0.1:8000/workers/status', timeout=10)
        if response.status_code != 200:
            return False
            
        data = response.json()
        active_workers = [w for w in data.get('workers', []) if w.get('status') == 'active']
        
        return len(active_workers) > 0
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return False

def main():
    # 主监控循环
    consecutive_failures = 0
    max_failures = 3
    
    while True:
        if check_system_health():
            consecutive_failures = 0
            logger.info(f"[{datetime.now()}] 系统健康")
        else:
            consecutive_failures += 1
            logger.warning(f"[{datetime.now()}] 系统不健康，连续失败: {consecutive_failures}")
            
            if consecutive_failures >= max_failures:
                logger.error("系统严重不健康，需要重启")
                # 这里可以添加重启逻辑
                break
        
        time.sleep(60)  # 每分钟检查一次

if __name__ == "__main__":
    main()
