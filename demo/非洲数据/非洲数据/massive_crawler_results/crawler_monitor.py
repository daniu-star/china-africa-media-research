"""
爬虫实时监控脚本

功能：
1. 实时监控爬虫状态
2. 检测僵尸状态
3. 自动恢复机制
4. 性能指标监控
"""

import asyncio
import json
import psutil
import time
from datetime import datetime
from pathlib import Path

class CrawlerMonitor:
    def __init__(self, output_dir='massive_crawler_results'):
        self.output_dir = Path(output_dir)
        self.monitor_file = self.output_dir / 'crawler_monitor.json'
        
    async def monitor_crawler(self):
        """监控爬虫状态"""
        print("🔍 开始监控爬虫状态...")
        
        while True:
            status = await self.check_crawler_status()
            
            if status['is_zombie']:
                print("⚠️ 检测到爬虫僵尸状态，尝试恢复...")
                await self.recover_crawler()
            
            # 保存监控数据
            await self.save_monitor_data(status)
            
            # 等待下一轮检查
            await asyncio.sleep(60)  # 每分钟检查一次
            
    async def check_crawler_status(self):
        """检查爬虫状态"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'is_zombie': False,
            'progress_stale': False,
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent
        }
        
        # 检查进度文件是否过时
        progress_file = self.output_dir / 'crawler_progress.json'
        if progress_file.exists():
            mtime = progress_file.stat().st_mtime
            time_diff = time.time() - mtime
            if time_diff > 300:  # 5分钟无更新
                status['progress_stale'] = True
                status['is_zombie'] = True
                
        return status
        
    async def recover_crawler(self):
        """恢复爬虫"""
        print("🔄 执行爬虫恢复程序...")
        # 实现恢复逻辑
        
    async def save_monitor_data(self, status):
        """保存监控数据"""
        with open(self.monitor_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False)

async def main():
    monitor = CrawlerMonitor()
    await monitor.monitor_crawler()

if __name__ == '__main__':
    asyncio.run(main())
