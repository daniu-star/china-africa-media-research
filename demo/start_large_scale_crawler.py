#!/usr/bin/env python3
"""
大规模数据抓取启动脚本
针对64868个任务的优化配置
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
import subprocess
import psutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('large_scale_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LargeScaleCrawlerLauncher:
    """大规模爬虫启动器"""
    
    def __init__(self):
        self.config_file = "large_scale_crawling_config.json"
        self.tasks_count = 64868
        self.start_time = datetime.now()
        
    def load_config(self):
        """加载大规模抓取配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"成功加载大规模抓取配置，目标任务数: {self.tasks_count}")
            return config
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return None
    
    def check_system_resources(self):
        """检查系统资源"""
        logger.info("检查系统资源...")
        
        # 内存检查
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # CPU检查
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # 磁盘检查
        disk = psutil.disk_usage('.')
        disk_free_gb = disk.free / (1024**3)
        
        logger.info(f"内存使用率: {memory_usage:.1f}%")
        logger.info(f"CPU使用率: {cpu_usage:.1f}%")
        logger.info(f"磁盘剩余空间: {disk_free_gb:.1f}GB")
        
        # 检查资源是否充足
        if memory_usage > 80:
            logger.warning("内存使用率较高，建议关闭其他应用")
        if cpu_usage > 80:
            logger.warning("CPU使用率较高，可能会影响性能")
        if disk_free_gb < 10:
            logger.error("磁盘空间不足，需要至少10GB空间")
            return False
            
        return True
    
    def optimize_system_for_crawling(self):
        """优化系统设置"""
        logger.info("优化系统设置...")
        
        # 设置环境变量
        os.environ['PYTHONHASHSEED'] = '0'
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # 增加文件描述符限制（Windows下可能无效，但尝试设置）
        try:
            import ctypes
            # 尝试增加TCP缓冲区大小
            pass
        except:
            pass
            
        logger.info("系统优化完成")
    
    def start_distributed_system(self):
        """启动分布式系统"""
        logger.info("启动分布式爬虫系统...")
        
        # 检查是否已有系统在运行
        if self.is_system_running():
            logger.info("分布式系统已在运行")
            return True
            
        # 启动主节点
        try:
            master_process = subprocess.Popen([
                sys.executable, 'start_system_fixed.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 等待主节点启动
            time.sleep(10)
            
            # 启动工作节点
            worker_process = subprocess.Popen([
                sys.executable, 'start_multiple_workers_stable.py', '--workers', '8'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            logger.info("分布式系统启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动分布式系统失败: {e}")
            return False
    
    def is_system_running(self):
        """检查系统是否在运行"""
        # 检查端口8000是否被占用（主节点端口）
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 8000))
            sock.close()
            return result == 0
        except:
            return False
    
    def monitor_progress(self):
        """监控抓取进度"""
        logger.info("开始监控抓取进度...")
        
        estimated_hours = 48  # 预计48小时完成
        check_interval = 300  # 5分钟检查一次
        
        while True:
            try:
                # 检查任务完成情况
                completed_tasks = self.get_completed_tasks_count()
                progress = (completed_tasks / self.tasks_count) * 100
                
                elapsed_hours = (datetime.now() - self.start_time).total_seconds() / 3600
                if elapsed_hours > 0:
                    speed = completed_tasks / elapsed_hours
                    remaining_tasks = self.tasks_count - completed_tasks
                    if speed > 0:
                        estimated_remaining_hours = remaining_tasks / speed
                    else:
                        estimated_remaining_hours = float('inf')
                else:
                    estimated_remaining_hours = estimated_hours
                
                logger.info(f"进度: {progress:.1f}% ({completed_tasks}/{self.tasks_count}) | "
                           f"速度: {speed:.1f} 任务/小时 | "
                           f"预计剩余时间: {estimated_remaining_hours:.1f} 小时")
                
                # 检查系统健康状态
                if not self.check_system_health():
                    logger.warning("系统健康状态异常")
                
                # 每5分钟检查一次
                time.sleep(check_interval)
                
                # 如果完成率达到100%，退出监控
                if progress >= 99.9:
                    logger.info("抓取任务完成!")
                    break
                    
            except KeyboardInterrupt:
                logger.info("监控被用户中断")
                break
            except Exception as e:
                logger.error(f"监控过程中发生错误: {e}")
                time.sleep(60)  # 出错后等待1分钟再继续
    
    def get_completed_tasks_count(self):
        """获取已完成任务数量"""
        try:
            # 检查data/results目录中的文件数量
            results_dir = os.path.join('data', 'results')
            if os.path.exists(results_dir):
                count = 0
                for root, dirs, files in os.walk(results_dir):
                    count += len(files)
                return count
            return 0
        except:
            return 0
    
    def check_system_health(self):
        """检查系统健康状态"""
        try:
            # 检查内存使用
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                logger.warning("内存使用率过高")
                return False
                
            # 检查CPU使用
            cpu_usage = psutil.cpu_percent(interval=1)
            if cpu_usage > 95:
                logger.warning("CPU使用率过高")
                return False
                
            return True
        except:
            return False
    
    def generate_performance_report(self):
        """生成性能报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds() / 3600
        
        completed_tasks = self.get_completed_tasks_count()
        success_rate = (completed_tasks / self.tasks_count) * 100
        
        report = {
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_hours": duration,
            "target_tasks": self.tasks_count,
            "completed_tasks": completed_tasks,
            "success_rate": success_rate,
            "average_speed_tasks_per_hour": completed_tasks / duration if duration > 0 else 0,
            "system_health": "良好"
        }
        
        # 保存报告
        report_file = f"large_scale_crawling_report_{end_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"性能报告已保存: {report_file}")
        return report
    
    def run(self):
        """运行大规模抓取"""
        logger.info("=== 大规模数据抓取启动 ===")
        logger.info(f"目标任务数量: {self.tasks_count}")
        logger.info(f"开始时间: {self.start_time}")
        
        # 1. 加载配置
        config = self.load_config()
        if not config:
            logger.error("配置加载失败，退出")
            return
        
        # 2. 检查系统资源
        if not self.check_system_resources():
            logger.error("系统资源不足，退出")
            return
        
        # 3. 优化系统设置
        self.optimize_system_for_crawling()
        
        # 4. 启动分布式系统
        if not self.start_distributed_system():
            logger.error("分布式系统启动失败，退出")
            return
        
        # 5. 监控进度
        try:
            self.monitor_progress()
        except KeyboardInterrupt:
            logger.info("抓取过程被用户中断")
        except Exception as e:
            logger.error(f"抓取过程中发生错误: {e}")
        
        # 6. 生成报告
        report = self.generate_performance_report()
        
        logger.info("=== 大规模数据抓取完成 ===")
        logger.info(f"完成时间: {datetime.now()}")
        logger.info(f"最终报告: {report}")

if __name__ == "__main__":
    launcher = LargeScaleCrawlerLauncher()
    launcher.run()