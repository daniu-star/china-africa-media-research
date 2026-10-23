#!/usr/bin/env python3
"""系统监控脚本 - 确保爬虫系统稳定运行"""

import json
import time
import psutil
import subprocess
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.monitor_log = []
        self.worker_processes = []
        
    def check_system_resources(self) -> Dict:
        """检查系统资源使用情况"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict()
        }
    
    def check_worker_status(self) -> Dict:
        """检查工作进程状态"""
        worker_status = {
            'master_running': False,
            'workers_running': 0,
            'worker_details': []
        }
        
        # 检查主进程
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'distributed_master.py' in ' '.join(cmdline):
                    worker_status['master_running'] = True
                    worker_status['master_pid'] = proc.info['pid']
                elif cmdline and 'distributed_worker.py' in ' '.join(cmdline):
                    worker_status['workers_running'] += 1
                    worker_status['worker_details'].append({
                        'pid': proc.info['pid'],
                        'cmdline': cmdline
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return worker_status
    
    def check_data_collection(self) -> Dict:
        """检查数据收集情况"""
        data_dir = 'data'
        if not os.path.exists(data_dir):
            return {'status': 'no_data_directory'}
        
        data_files = {}
        for file in os.listdir(data_dir):
            if file.endswith('.json'):
                file_path = os.path.join(data_dir, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, dict) and 'articles' in data:
                        article_count = len(data['articles'])
                    elif isinstance(data, list):
                        article_count = len(data)
                    else:
                        article_count = 0
                    
                    data_files[file] = {
                        'article_count': article_count,
                        'file_size': os.path.getsize(file_path),
                        'modified_time': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    }
                except Exception as e:
                    data_files[file] = {'error': str(e)}
        
        return {
            'data_files': data_files,
            'total_articles': sum(f.get('article_count', 0) for f in data_files.values() if 'article_count' in f)
        }
    
    def check_errors_and_warnings(self) -> Dict:
        """检查错误和警告"""
        # 检查最近的日志文件
        log_files = [f for f in os.listdir('.') if f.endswith('.log')]
        recent_errors = []
        
        for log_file in log_files[:3]:  # 只检查前3个日志文件
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-100:]  # 检查最后100行
                
                for line in lines:
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in ['error', 'exception', 'failed', 'timeout']):
                        recent_errors.append({
                            'file': log_file,
                            'line': line.strip(),
                            'timestamp': datetime.now().isoformat()
                        })
            except Exception:
                continue
        
        return {
            'recent_errors': recent_errors,
            'error_count': len(recent_errors)
        }
    
    def generate_health_report(self) -> Dict:
        """生成健康报告"""
        resources = self.check_system_resources()
        workers = self.check_worker_status()
        data = self.check_data_collection()
        errors = self.check_errors_and_warnings()
        
        # 计算健康分数
        health_score = 100
        
        # 资源使用扣分
        if resources['cpu_percent'] > 80:
            health_score -= 10
        if resources['memory_percent'] > 80:
            health_score -= 10
        
        # 进程状态扣分
        if not workers['master_running']:
            health_score -= 30
        if workers['workers_running'] < 2:  # 至少需要2个工作进程
            health_score -= 20
        
        # 数据收集扣分
        if data['total_articles'] == 0:
            health_score -= 20
        
        # 错误扣分
        health_score -= min(errors['error_count'] * 5, 20)
        
        health_score = max(0, health_score)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
            'health_score': health_score,
            'health_status': 'excellent' if health_score >= 90 else 'good' if health_score >= 70 else 'fair' if health_score >= 50 else 'poor',
            'resources': resources,
            'workers': workers,
            'data_collection': data,
            'errors': errors,
            'recommendations': self.generate_recommendations(resources, workers, data, errors)
        }
        
        self.monitor_log.append(report)
        return report
    
    def generate_recommendations(self, resources: Dict, workers: Dict, data: Dict, errors: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 资源建议
        if resources['cpu_percent'] > 80:
            recommendations.append("CPU使用率过高，考虑减少工作进程数量或优化爬虫策略")
        if resources['memory_percent'] > 80:
            recommendations.append("内存使用率过高，考虑增加内存或优化内存使用")
        
        # 进程建议
        if not workers['master_running']:
            recommendations.append("主进程未运行，需要启动分布式主进程")
        if workers['workers_running'] < 2:
            recommendations.append(f"工作进程数量不足({workers['workers_running']})，建议启动更多工作进程")
        
        # 数据建议
        if data['total_articles'] == 0:
            recommendations.append("未收集到任何数据，检查爬虫配置和目标网站")
        
        # 错误建议
        if errors['error_count'] > 10:
            recommendations.append(f"发现{errors['error_count']}个错误，需要检查日志文件并修复问题")
        
        return recommendations
    
    def save_report(self, report: Dict):
        """保存报告到文件"""
        report_file = f"system_monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"系统监控报告已保存到: {report_file}")
        
        # 同时保存到监控日志
        log_file = "system_monitor_log.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.monitor_log[-100:], f, ensure_ascii=False, indent=2)  # 只保存最近100条记录

def monitor_system_continuously(interval_minutes: int = 30, duration_hours: int = 24):
    """持续监控系统"""
    monitor = SystemMonitor()
    end_time = datetime.now() + timedelta(hours=duration_hours)
    
    print(f"开始系统监控，将持续{duration_hours}小时，每{interval_minutes}分钟检查一次")
    print(f"监控结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    while datetime.now() < end_time:
        try:
            print(f"\n=== 系统检查 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
            
            report = monitor.generate_health_report()
            
            # 打印摘要信息
            print(f"健康分数: {report['health_score']}/100 ({report['health_status']})")
            print(f"运行时间: {report['uptime_hours']:.1f} 小时")
            print(f"CPU使用率: {report['resources']['cpu_percent']}%")
            print(f"内存使用率: {report['resources']['memory_percent']}%")
            print(f"主进程运行: {'是' if report['workers']['master_running'] else '否'}")
            print(f"工作进程数量: {report['workers']['workers_running']}")
            print(f"总文章数量: {report['data_collection']['total_articles']}")
            print(f"错误数量: {report['errors']['error_count']}")
            
            # 打印建议
            if report['recommendations']:
                print("\n改进建议:")
                for rec in report['recommendations']:
                    print(f"  • {rec}")
            
            # 保存报告
            monitor.save_report(report)
            
            # 如果健康状态较差，采取行动
            if report['health_score'] < 50:
                print("\n⚠️ 系统健康状态较差，需要立即处理！")
                # 这里可以添加自动恢复逻辑
            
            # 等待下一次检查
            print(f"\n等待{interval_minutes}分钟后进行下一次检查...")
            time.sleep(interval_minutes * 60)
            
        except KeyboardInterrupt:
            print("\n监控被用户中断")
            break
        except Exception as e:
            print(f"监控过程中发生错误: {e}")
            time.sleep(60)  # 出错后等待1分钟再继续
    
    print(f"\n系统监控完成，总运行时间: {(datetime.now() - monitor.start_time).total_seconds() / 3600:.1f} 小时")

def quick_system_check():
    """快速系统检查"""
    monitor = SystemMonitor()
    report = monitor.generate_health_report()
    
    print("=== 快速系统检查报告 ===")
    print(f"健康状态: {report['health_status']} ({report['health_score']}/100)")
    print(f"主进程: {'运行中' if report['workers']['master_running'] else '未运行'}")
    print(f"工作进程: {report['workers']['workers_running']} 个")
    print(f"总文章: {report['data_collection']['total_articles']} 篇")
    print(f"CPU使用率: {report['resources']['cpu_percent']}%")
    print(f"内存使用率: {report['resources']['memory_percent']}%")
    
    if report['recommendations']:
        print("\n建议:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    return report

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='系统监控工具')
    parser.add_argument('--mode', choices=['continuous', 'quick'], default='quick',
                       help='监控模式: continuous(持续监控) 或 quick(快速检查)')
    parser.add_argument('--interval', type=int, default=30,
                       help='持续监控的检查间隔(分钟)')
    parser.add_argument('--duration', type=int, default=24,
                       help='持续监控的持续时间(小时)')
    
    args = parser.parse_args()
    
    if args.mode == 'continuous':
        monitor_system_continuously(args.interval, args.duration)
    else:
        quick_system_check()