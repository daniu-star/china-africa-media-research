#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目状态监控器
实时监控非洲数据研究项目的运行状态
"""

import os
import json
import sqlite3
import psutil
import time
from datetime import datetime
from typing import Dict, List, Any


class ProjectStatusMonitor:
    """项目状态监控器"""
    
    def __init__(self, data_dir: str = "data", db_path: str = "data/africa_articles.db"):
        self.data_dir = data_dir
        self.db_path = db_path
        
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'system_resources': {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            },
            'running_processes': []
        }
        
        # 检查相关进程
        target_processes = ['python', 'start_system_fixed.py', 'start_multiple_workers_stable.py']
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if any(target in ' '.join(proc.info['cmdline'] or []) for target in target_processes):
                    status['running_processes'].append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': proc.info['cmdline']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return status
    
    def get_database_status(self) -> Dict[str, Any]:
        """获取数据库状态"""
        
        # 使用正确的数据库路径
        db_path = os.path.join('data', 'articles.db')
        
        status = {
            'database_exists': os.path.exists(db_path),
            'database_size_mb': 0,
            'total_articles': 0,
            'countries_count': 0,
            'categories_count': 0,
            'years_range': {},
            'last_update': None
        }
        
        if status['database_exists']:
            # 获取数据库大小
            status['database_size_mb'] = round(os.path.getsize(db_path) / (1024 * 1024), 2)
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 获取文章总数
                cursor.execute("SELECT COUNT(*) FROM articles")
                status['total_articles'] = cursor.fetchone()[0]
                
                # 获取国家数量
                cursor.execute("SELECT COUNT(DISTINCT country) FROM articles")
                status['countries_count'] = cursor.fetchone()[0]
                
                # 获取类别数量
                cursor.execute("SELECT COUNT(DISTINCT category) FROM articles")
                status['categories_count'] = cursor.fetchone()[0]
                
                # 获取年份范围
                cursor.execute("SELECT MIN(publish_year), MAX(publish_year) FROM articles")
                min_year, max_year = cursor.fetchone()
                status['years_range'] = {'min': min_year, 'max': max_year}
                
                # 获取最后更新时间
                cursor.execute("SELECT MAX(created_at) FROM articles")
                last_update = cursor.fetchone()[0]
                status['last_update'] = last_update
                
                conn.close()
                
            except Exception as e:
                status['error'] = str(e)
        
        return status
    
    def get_report_status(self) -> Dict[str, Any]:
        """获取报告状态"""
        
        status = {
            'reports_found': [],
            'latest_reports': {}
        }
        
        if os.path.exists(self.data_dir):
            # 查找所有报告文件
            report_types = {
                'sources_inventory': '数据源清单',
                'backup_inventory': '备份清单',
                'storage_optimization_report': '存储优化报告',
                'keyword_optimization_report': '关键词优化报告',
                'data_analysis_report': '数据分析报告',
                'final_comprehensive_report': '最终综合报告'
            }
            
            for pattern, description in report_types.items():
                report_files = [f for f in os.listdir(self.data_dir) 
                              if f.startswith(pattern) and f.endswith('.json')]
                
                if report_files:
                    # 获取最新报告
                    latest_report = max(report_files, 
                                      key=lambda x: os.path.getmtime(os.path.join(self.data_dir, x)))
                    
                    status['reports_found'].append({
                        'type': pattern,
                        'description': description,
                        'file': latest_report,
                        'size_mb': round(os.path.getsize(os.path.join(self.data_dir, latest_report)) / (1024 * 1024), 3),
                        'modified': datetime.fromtimestamp(os.path.getmtime(os.path.join(self.data_dir, latest_report))).isoformat()
                    })
                    
                    status['latest_reports'][pattern] = latest_report
        
        return status
    
    def get_overall_status(self) -> Dict[str, Any]:
        """获取整体状态"""
        
        system_status = self.get_system_status()
        database_status = self.get_database_status()
        report_status = self.get_report_status()
        
        overall_status = {
            'timestamp': datetime.now().isoformat(),
            'system': system_status,
            'database': database_status,
            'reports': report_status,
            'health_score': self.calculate_health_score(database_status, report_status),
            'recommendations': self.generate_recommendations(database_status, report_status)
        }
        
        return overall_status
    
    def calculate_health_score(self, database_status: Dict[str, Any], report_status: Dict[str, Any]) -> float:
        """计算健康分数（0-100）"""
        
        score = 0
        
        # 数据库存在性（20分）
        if database_status['database_exists']:
            score += 20
        
        # 数据量（30分）
        if database_status['total_articles'] > 0:
            data_score = min(30, database_status['total_articles'] / 100)
            score += data_score
        
        # 报告完整性（30分）
        report_count = len(report_status['reports_found'])
        report_score = min(30, report_count * 5)
        score += report_score
        
        # 系统资源（20分）
        system_status = self.get_system_status()
        system_score = max(0, 20 - (system_status['system_resources']['memory_percent'] / 5))
        score += system_score
        
        return round(min(100, score), 1)
    
    def generate_recommendations(self, database_status: Dict[str, Any], report_status: Dict[str, Any]) -> List[str]:
        """生成建议"""
        
        recommendations = []
        
        # 数据量建议
        if database_status['total_articles'] < 1000:
            recommendations.append("需要扩大数据收集规模，目标达到1000篇文章以上")
        elif database_status['total_articles'] < 5000:
            recommendations.append("数据收集进展良好，建议继续扩大规模至5000篇文章")
        
        # 报告建议
        if len(report_status['reports_found']) < 4:
            recommendations.append("建议运行缺失的报告生成器以完善项目文档")
        
        # 系统资源建议
        if self.get_system_status()['system_resources']['memory_percent'] > 80:
            recommendations.append("系统内存使用率较高，建议优化或增加内存")
        
        if not recommendations:
            recommendations.append("系统运行状态良好，继续保持当前工作流程")
        
        return recommendations
    
    def save_status_report(self, status: Dict[str, Any]) -> str:
        """保存状态报告"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"project_status_report_{timestamp}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def print_status_summary(self, status: Dict[str, Any]):
        """打印状态摘要"""
        
        print("=" * 60)
        print("非洲数据研究项目 - 实时状态监控")
        print("=" * 60)
        
        print(f"\n📊 系统健康分数: {status['health_score']}/100")
        
        # 系统资源
        system = status['system']
        print(f"\n💻 系统资源:")
        print(f"   CPU使用率: {system['system_resources']['cpu_percent']}%")
        print(f"   内存使用率: {system['system_resources']['memory_percent']}%")
        print(f"   磁盘使用率: {system['system_resources']['disk_usage']}%")
        print(f"   运行进程数: {len(system['running_processes'])}")
        
        # 数据库状态
        db = status['database']
        print(f"\n🗄️  数据库状态:")
        print(f"   数据库存在: {'✅' if db['database_exists'] else '❌'}")
        if db['database_exists']:
            print(f"   文章总数: {db['total_articles']:,} 篇")
            print(f"   覆盖国家: {db['countries_count']} 个")
            print(f"   类别数量: {db['categories_count']} 个")
            print(f"   年份范围: {db['years_range'].get('min', 'N/A')} - {db['years_range'].get('max', 'N/A')}")
            print(f"   数据库大小: {db['database_size_mb']} MB")
            if db['last_update']:
                print(f"   最后更新: {db['last_update']}")
        
        # 报告状态
        reports = status['reports']
        print(f"\n📋 报告状态:")
        print(f"   发现报告: {len(reports['reports_found'])} 个")
        for report in reports['reports_found']:
            print(f"   • {report['description']}: {report['file']} ({report['size_mb']}MB)")
        
        # 建议
        print(f"\n💡 建议:")
        for i, rec in enumerate(status['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        print(f"\n⏰ 检查时间: {status['timestamp']}")
        print("=" * 60)


def main():
    """主函数"""
    
    monitor = ProjectStatusMonitor()
    
    print("正在检查项目状态...")
    
    # 获取整体状态
    status = monitor.get_overall_status()
    
    # 打印状态摘要
    monitor.print_status_summary(status)
    
    # 保存状态报告
    report_path = monitor.save_status_report(status)
    print(f"\n状态报告已保存到: {report_path}")
    
    return status


if __name__ == "__main__":
    main()