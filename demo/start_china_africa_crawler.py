#!/usr/bin/env python3
"""
中国与非洲关系爬虫启动脚本
专门用于启动中国相关关键词的分布式爬虫任务
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
import subprocess
import threading
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChinaAfricaCrawlerStarter:
    """中国与非洲关系爬虫启动器"""
    
    def __init__(self):
        self.processes = {}
        self.is_running = False
        
        # 检查必要文件
        self.check_required_files()
    
    def check_required_files(self):
        """检查必要文件是否存在"""
        required_files = [
            'china_africa_keywords.json',
            'china_africa_crawler.py',
            'distributed_master_fixed.py',
            'start_system.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            logger.warning(f"缺少必要文件: {missing_files}")
            return False
        
        logger.info("所有必要文件检查通过")
        return True
    
    def start_china_africa_crawler(self):
        """启动中国与非洲关系爬虫"""
        try:
            # 首先运行中国与非洲关系爬虫生成任务
            logger.info("正在生成中国与非洲关系爬虫任务...")
            
            import china_africa_crawler
            crawler = china_africa_crawler.ChinaAfricaCrawler()
            
            # 生成任务并集成到分布式系统
            distributed_tasks = crawler.integrate_with_distributed_system()
            
            if not distributed_tasks:
                logger.error("生成中国与非洲关系爬虫任务失败")
                return False
            
            logger.info(f"成功生成 {len(distributed_tasks)} 个中国与非洲关系搜索任务")
            
            # 显示任务统计
            stats = crawler.get_statistics()
            print("=== 中国与非洲关系爬虫任务统计 ===")
            print(f"总任务数: {stats['total_tasks']}")
            print("语言分布:")
            for lang, count in stats['languages'].items():
                print(f"  {lang}: {count}")
            print("分类分布:")
            for cat, count in stats['categories'].items():
                print(f"  {cat}: {count}")
            
            # 启动分布式爬虫系统
            logger.info("正在启动分布式爬虫系统...")
            
            # 使用现有的启动脚本
            process = subprocess.Popen([
                sys.executable, 'start_system.py', '--china-africa'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            self.processes['distributed_system'] = process
            
            # 启动监控线程
            monitor_thread = threading.Thread(target=self.monitor_system)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            self.is_running = True
            logger.info("中国与非洲关系爬虫系统启动成功")
            
            return True
            
        except Exception as e:
            logger.error(f"启动中国与非洲关系爬虫失败: {e}")
            return False
    
    def monitor_system(self):
        """监控系统运行状态"""
        while self.is_running:
            try:
                # 检查进程状态
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        logger.warning(f"{name} 进程已停止")
                        # 重新启动进程
                        self.restart_process(name)
                
                # 检查任务文件更新
                self.check_task_progress()
                
                time.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                logger.error(f"监控系统出错: {e}")
                time.sleep(60)
    
    def restart_process(self, process_name: str):
        """重启进程"""
        try:
            if process_name == 'distributed_system':
                process = subprocess.Popen([
                    sys.executable, 'start_system.py', '--china-africa'
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                self.processes[process_name] = process
                logger.info(f"已重新启动 {process_name}")
            
        except Exception as e:
            logger.error(f"重启 {process_name} 失败: {e}")
    
    def check_task_progress(self):
        """检查任务进度"""
        try:
            # 检查结果目录
            results_dir = 'china_africa_results'
            if os.path.exists(results_dir):
                result_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
                
                total_results = 0
                for file in result_files:
                    file_path = os.path.join(results_dir, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'tasks' in data:
                            total_results += len(data['tasks'])
                
                logger.info(f"当前已完成 {total_results} 个中国与非洲关系搜索任务")
        
        except Exception as e:
            logger.error(f"检查任务进度失败: {e}")
    
    def stop_system(self):
        """停止系统"""
        self.is_running = False
        
        for name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=10)
                logger.info(f"已停止 {name} 进程")
            except Exception as e:
                logger.error(f"停止 {name} 进程失败: {e}")
                process.kill()
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            "is_running": self.is_running,
            "processes": {},
            "timestamp": datetime.now().isoformat()
        }
        
        for name, process in self.processes.items():
            status["processes"][name] = {
                "running": process.poll() is None,
                "exit_code": process.poll()
            }
        
        return status

def main():
    """主函数"""
    print("=== 中国与非洲关系爬虫启动器 ===")
    print("专门用于搜索中国相关关键词的分布式爬虫系统")
    print()
    
    starter = ChinaAfricaCrawlerStarter()
    
    try:
        # 启动系统
        print("正在启动中国与非洲关系爬虫系统...")
        success = starter.start_china_africa_crawler()
        
        if success:
            print("✅ 中国与非洲关系爬虫系统启动成功!")
            print("📊 系统正在运行中...")
            print("🔍 正在搜索中国相关关键词:")
            print("   - 中国、中国南海、一带一路")
            print("   - 中国共产党、中国人民解放军")
            print("   - 中国人、中国各省份")
            print("🌍 支持多种语言: 英文、斯瓦希里语、豪萨语等")
            print()
            print("按 Ctrl+C 停止系统")
            
            # 保持运行
            try:
                while True:
                    time.sleep(10)
                    # 显示状态更新
                    status = starter.get_system_status()
                    if status["is_running"]:
                        print(f"🟢 系统运行中 - {datetime.now().strftime('%H:%M:%S')}")
                    else:
                        print("🔴 系统已停止")
                        break
                        
            except KeyboardInterrupt:
                print("\n正在停止系统...")
                starter.stop_system()
                print("✅ 系统已安全停止")
        
        else:
            print("❌ 系统启动失败")
            return 1
    
    except Exception as e:
        logger.error(f"系统运行出错: {e}")
        print(f"❌ 错误: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())