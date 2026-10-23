#!/usr/bin/env python3
"""
分布式爬虫系统监控脚本
实时监控系统状态和性能指标
"""

import requests
import json
import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

class SystemMonitor:
    def __init__(self, master_url="http://localhost:8000", worker_url="http://localhost:5000"):
        self.master_url = master_url
        self.worker_url = worker_url
        self.monitoring_data = []
        
    def get_master_status(self) -> Dict[str, Any]:
        """获取主节点状态"""
        try:
            response = requests.get(f"{self.master_url}/queue-status", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_worker_status(self) -> Dict[str, Any]:
        """获取工作节点状态"""
        try:
            response = requests.get(f"{self.worker_url}/health", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_workers_info(self) -> List[Dict[str, Any]]:
        """获取所有工作节点信息"""
        workers_file = os.path.join('data', 'workers.json')
        workers = []
        
        if os.path.exists(workers_file):
            current_time = datetime.now()
            with open(workers_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            worker = json.loads(line.strip())
                            
                            # 计算活跃状态
                            last_heartbeat = datetime.fromisoformat(worker['last_heartbeat'])
                            time_diff = (current_time - last_heartbeat).total_seconds()
                            worker['active'] = time_diff < 60  # 60秒内活跃
                            worker['last_seen_seconds'] = int(time_diff)
                            
                            workers.append(worker)
                        except Exception as e:
                            print(f"解析工作节点信息失败: {e}")
        
        return workers
    
    def get_results_info(self) -> Dict[str, Any]:
        """获取结果文件信息"""
        results_file = os.path.join('data', 'results.json')
        
        if os.path.exists(results_file):
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    results = []
                    for line in f:
                        if line.strip():
                            try:
                                result = json.loads(line.strip())
                                results.append(result)
                            except:
                                pass
                
                return {
                    'total_results': len(results),
                    'successful_results': len([r for r in results if r.get('status') == 'completed']),
                    'failed_results': len([r for r in results if r.get('status') == 'failed']),
                    'latest_results': results[-5:] if results else []
                }
            except Exception as e:
                return {"error": str(e)}
        else:
            return {"total_results": 0, "successful_results": 0, "failed_results": 0, "latest_results": []}
    
    def collect_metrics(self):
        """收集系统指标"""
        timestamp = datetime.now()
        
        metrics = {
            'timestamp': timestamp.isoformat(),
            'master': self.get_master_status(),
            'worker': self.get_worker_status(),
            'workers': self.get_workers_info(),
            'results': self.get_results_info()
        }
        
        self.monitoring_data.append(metrics)
        
        # 保持最近100个数据点
        if len(self.monitoring_data) > 100:
            self.monitoring_data = self.monitoring_data[-100:]
        
        return metrics
    
    def display_dashboard(self, metrics: Dict[str, Any]):
        """显示监控仪表板"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 80)
        print("分布式爬虫系统监控仪表板")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # 主节点状态
        print("\n📊 主节点状态:")
        print("-" * 40)
        
        master_status = metrics['master']
        if 'error' not in master_status:
            print(f"   待处理任务: {master_status.get('pending_tasks', 0)}")
            print(f"   已完成结果: {master_status.get('completed_results', 0)}")
            print(f"   活跃工作节点: {master_status.get('active_workers', 0)}")
            print(f"   总提交任务: {master_status.get('total_submitted', 0)}")
            print(f"   已完成任务: {master_status.get('completed_tasks', 0)}")
            print(f"   失败任务: {master_status.get('failed_tasks', 0)}")
        else:
            print(f"   ❌ 连接失败: {master_status['error']}")
        
        # 工作节点状态
        print("\n🔧 工作节点状态:")
        print("-" * 40)
        
        worker_status = metrics['worker']
        if 'error' not in worker_status:
            print(f"   状态: {worker_status.get('status', 'unknown')}")
            print(f"   工作节点ID: {worker_status.get('worker_id', 'unknown')}")
            print(f"   最后心跳: {worker_status.get('last_heartbeat', 'unknown')}")
        else:
            print(f"   ❌ 连接失败: {worker_status['error']}")
        
        # 所有工作节点
        print("\n👥 所有工作节点:")
        print("-" * 40)
        
        workers = metrics['workers']
        if workers:
            for worker in workers:
                status = "🟢 活跃" if worker['active'] else "🔴 离线"
                print(f"   {worker['worker_id']}: {status} (最后活跃: {worker['last_seen_seconds']}秒前)")
        else:
            print("   暂无工作节点信息")
        
        # 结果统计
        print("\n📈 结果统计:")
        print("-" * 40)
        
        results_info = metrics['results']
        if 'error' not in results_info:
            print(f"   总结果数: {results_info['total_results']}")
            print(f"   成功结果: {results_info['successful_results']}")
            print(f"   失败结果: {results_info['failed_results']}")
            
            if results_info['latest_results']:
                print("\n   最新结果:")
                for result in results_info['latest_results'][-3:]:
                    status_icon = "✅" if result.get('status') == 'completed' else "❌"
                    task_id = result.get('task_id', 'unknown')[:8]
                    print(f"     {status_icon} {task_id}: {result.get('status', 'unknown')}")
        else:
            print(f"   ❌ 获取结果失败: {results_info['error']}")
        
        # 性能趋势
        print("\n📊 性能趋势:")
        print("-" * 40)
        
        if len(self.monitoring_data) > 1:
            recent_data = self.monitoring_data[-10:]  # 最近10个数据点
            
            if all('error' not in data['master'] for data in recent_data):
                pending_tasks = [data['master'].get('pending_tasks', 0) for data in recent_data]
                completed_tasks = [data['master'].get('completed_tasks', 0) for data in recent_data]
                
                print(f"   待处理任务趋势: {min(pending_tasks)} → {max(pending_tasks)}")
                print(f"   完成任务趋势: {min(completed_tasks)} → {max(completed_tasks)}")
                
                if len(pending_tasks) > 1:
                    trend = "↗️ 上升" if pending_tasks[-1] > pending_tasks[-2] else "↘️ 下降"
                    print(f"   任务队列趋势: {trend}")
            else:
                print("   数据不足或连接异常")
        
        print("\n" + "=" * 80)
        print("按 Ctrl+C 退出监控")
    
    def run_monitoring(self, interval: int = 5):
        """运行监控循环"""
        print("启动分布式爬虫系统监控...")
        print(f"监控间隔: {interval}秒")
        print("按 Ctrl+C 退出\n")
        
        try:
            while True:
                metrics = self.collect_metrics()
                self.display_dashboard(metrics)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n监控已停止")
        except Exception as e:
            print(f"监控异常: {e}")
    
    def generate_report(self, hours: int = 1):
        """生成监控报告"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        relevant_data = [
            data for data in self.monitoring_data
            if datetime.fromisoformat(data['timestamp']) >= cutoff_time
        ]
        
        if not relevant_data:
            print(f"过去{hours}小时内无监控数据")
            return
        
        print(f"\n📋 过去{hours}小时监控报告")
        print("=" * 60)
        
        # 统计信息
        successful_connections = len([d for d in relevant_data if 'error' not in d['master']])
        connection_rate = (successful_connections / len(relevant_data)) * 100
        
        print(f"监控数据点: {len(relevant_data)}")
        print(f"连接成功率: {connection_rate:.1f}%")
        
        # 任务统计
        if successful_connections > 0:
            master_data = [d['master'] for d in relevant_data if 'error' not in d['master']]
            
            avg_pending = sum(d.get('pending_tasks', 0) for d in master_data) / len(master_data)
            max_pending = max(d.get('pending_tasks', 0) for d in master_data)
            
            total_completed = master_data[-1].get('completed_tasks', 0) - master_data[0].get('completed_tasks', 0)
            
            print(f"平均待处理任务: {avg_pending:.1f}")
            print(f"最大待处理任务: {max_pending}")
            print(f"完成任务数量: {total_completed}")
        
        # 工作节点统计
        active_workers_counts = []
        for data in relevant_data:
            if 'error' not in data['master']:
                active_workers_counts.append(data['master'].get('active_workers', 0))
        
        if active_workers_counts:
            avg_workers = sum(active_workers_counts) / len(active_workers_counts)
            max_workers = max(active_workers_counts)
            
            print(f"平均活跃工作节点: {avg_workers:.1f}")
            print(f"最大活跃工作节点: {max_workers}")
        
        print("=" * 60)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='分布式爬虫系统监控')
    parser.add_argument('--interval', type=int, default=5, help='监控间隔（秒）')
    parser.add_argument('--report', type=int, help='生成报告（小时数）')
    parser.add_argument('--master-url', default='http://localhost:8000', help='主节点URL')
    parser.add_argument('--worker-url', default='http://localhost:5000', help='工作节点URL')
    
    args = parser.parse_args()
    
    monitor = SystemMonitor(args.master_url, args.worker_url)
    
    if args.report:
        # 先收集一些数据
        print("收集监控数据...")
        for _ in range(3):
            monitor.collect_metrics()
            time.sleep(2)
        
        monitor.generate_report(args.report)
    else:
        monitor.run_monitoring(args.interval)

if __name__ == "__main__":
    main()