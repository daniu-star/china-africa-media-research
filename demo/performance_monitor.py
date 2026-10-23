"""
实时性能监控和可视化模块
提供爬虫系统的实时性能监控、数据可视化和告警功能
"""

import json
import time
import statistics
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import deque
import threading
import logging
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标数据结构"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    queue_size: int
    active_workers: int
    tasks_processed: int
    tasks_failed: int
    avg_response_time: float
    throughput: float
    error_rate: float
    # 新增爬虫特定指标
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_latency: float = 0.0
    proxy_success_rate: Dict[str, float] = None
    anti_crawler_detections: int = 0
    retry_count: int = 0
    data_volume: int = 0  # 数据量（字节）

class RealTimeMonitor:
    """实时性能监控器"""
    
    def __init__(self, window_size: int = 1000, alert_threshold: float = 0.7):
        """
        初始化实时性能监控器
        
        Args:
            window_size: 滑动窗口大小
            alert_threshold: 告警阈值
        """
        self.window_size = window_size
        self.alert_threshold = alert_threshold
        
        # 性能数据存储
        self.metrics_history = deque(maxlen=window_size)
        self.proxy_performance = {}
        self.website_performance = {}
        self.anti_crawler_stats = {}
        
        # 实时统计
        self.start_time = datetime.now()
        self.current_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_latency': 0.0,
            'proxy_success_rates': {},
            'anti_crawler_detections': 0,
            'retry_count': 0,
            'data_volume': 0
        }
        
        # 响应时间统计
        self.response_count = 0
        self.total_response_time = 0.0
        
        # 任务统计
        self.total_tasks_processed = 0
        self.total_tasks_failed = 0
        
        # 告警系统
        self.alerts = deque(maxlen=50)
        self.alert_rules = {
            'low_success_rate': {'threshold': 0.7, 'window': 100},
            'high_latency': {'threshold': 500, 'window': 50},
            'proxy_failure': {'threshold': 0.5, 'window': 20},
            'anti_crawler_spike': {'threshold': 10, 'window': 10}
        }
        
        # 监控线程
        self.monitoring_thread = None
        self.is_monitoring = False
        self.lock = threading.Lock()
        
        logger.info("实时性能监控器初始化完成")
    
    def collect_metrics(self, queue_size: int, active_workers: int, 
                       tasks_processed: int, tasks_failed: int, 
                       response_time: Optional[float] = None) -> PerformanceMetrics:
        """
        收集性能指标
        
        Args:
            queue_size: 队列大小
            active_workers: 活跃工作节点数
            tasks_processed: 处理的任务数
            tasks_failed: 失败的任务数
            response_time: 响应时间（可选）
            
        Returns:
            PerformanceMetrics: 性能指标
        """
        # 获取系统资源使用情况
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.percent
        
        # 计算吞吐量和错误率
        throughput = self._calculate_throughput(tasks_processed)
        error_rate = self._calculate_error_rate(tasks_processed, tasks_failed)
        
        # 计算平均响应时间
        avg_response_time = self._calculate_avg_response_time(response_time)
        
        # 创建性能指标
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            queue_size=queue_size,
            active_workers=active_workers,
            tasks_processed=tasks_processed,
            tasks_failed=tasks_failed,
            avg_response_time=avg_response_time,
            throughput=throughput,
            error_rate=error_rate
        )
        
        # 添加到历史记录
        with self.lock:
            self.metrics_history.append(metrics)
            
            # 更新总统计
            self.total_tasks_processed += tasks_processed
            self.total_tasks_failed += tasks_failed
            if response_time:
                self.total_response_time += response_time
                self.response_count += 1
        
        # 检查性能告警
        self._check_alerts(metrics)
        
        return metrics

    def collect_request_metrics(self, url: str, proxy: str, success: bool, 
                                latency: float, data_size: int = 0, 
                                anti_crawler_detected: bool = False, 
                                retry_count: int = 0) -> PerformanceMetrics:
        """
        收集爬虫请求性能指标
        
        Args:
            url: 请求URL
            proxy: 使用的代理
            success: 是否成功
            latency: 延迟时间(ms)
            data_size: 数据大小(字节)
            anti_crawler_detected: 是否检测到反爬虫
            retry_count: 重试次数
            
        Returns:
            PerformanceMetrics: 性能指标对象
        """
        with self.lock:
            # 更新实时统计
            self.current_stats['total_requests'] += 1
            if success:
                self.current_stats['successful_requests'] += 1
            else:
                self.current_stats['failed_requests'] += 1
            
            # 更新延迟统计
            total_latency = self.current_stats['avg_latency'] * max(1, self.current_stats['total_requests'] - 1)
            self.current_stats['avg_latency'] = (total_latency + latency) / self.current_stats['total_requests']
            
            # 更新代理性能
            if proxy:
                if proxy not in self.current_stats['proxy_success_rates']:
                    self.current_stats['proxy_success_rates'][proxy] = {'success': 0, 'total': 0}
                self.current_stats['proxy_success_rates'][proxy]['total'] += 1
                if success:
                    self.current_stats['proxy_success_rates'][proxy]['success'] += 1
            
            # 更新反爬虫统计
            if anti_crawler_detected:
                self.current_stats['anti_crawler_detections'] += 1
            
            self.current_stats['retry_count'] += retry_count
            self.current_stats['data_volume'] += data_size
            
            # 创建性能指标对象
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_usage=psutil.cpu_percent(interval=0.1),
                memory_usage=psutil.virtual_memory().percent,
                queue_size=0,  # 需要从外部获取
                active_workers=0,  # 需要从外部获取
                tasks_processed=self.current_stats['successful_requests'],
                tasks_failed=self.current_stats['failed_requests'],
                avg_response_time=self.current_stats['avg_latency'],
                throughput=self.current_stats['total_requests'] / max(1, (datetime.now() - self.start_time).total_seconds()),
                error_rate=(self.current_stats['failed_requests'] / max(1, self.current_stats['total_requests'])) * 100,
                request_count=self.current_stats['total_requests'],
                success_count=self.current_stats['successful_requests'],
                failure_count=self.current_stats['failed_requests'],
                avg_latency=self.current_stats['avg_latency'],
                proxy_success_rate={k: v['success']/max(1, v['total']) for k, v in self.current_stats['proxy_success_rates'].items()},
                anti_crawler_detections=self.current_stats['anti_crawler_detections'],
                retry_count=self.current_stats['retry_count'],
                data_volume=self.current_stats['data_volume']
            )
            
            # 添加到历史记录
            self.metrics_history.append(metrics)
            
            # 检查性能告警
            self._check_alerts(metrics)
            
            return metrics
    
    def _calculate_throughput(self, tasks_processed: int) -> float:
        """计算吞吐量（任务/秒）"""
        if len(self.metrics_history) < 2:
            return 0.0
        
        # 计算最近两个时间点的吞吐量
        recent_metrics = list(self.metrics_history)[-2:]
        time_diff = (recent_metrics[1].timestamp - recent_metrics[0].timestamp).total_seconds()
        task_diff = recent_metrics[1].tasks_processed - recent_metrics[0].tasks_processed
        
        if time_diff > 0:
            return task_diff / time_diff
        return 0.0
    
    def _calculate_error_rate(self, tasks_processed: int, tasks_failed: int) -> float:
        """计算错误率"""
        if tasks_processed == 0:
            return 0.0
        return (tasks_failed / tasks_processed) * 100
    
    def _calculate_avg_response_time(self, response_time: Optional[float]) -> float:
        """计算平均响应时间"""
        if self.response_count == 0:
            return 0.0
        return self.total_response_time / self.response_count
    
    def _check_alerts(self, metrics: PerformanceMetrics):
        """检查性能告警"""
        recent_metrics = list(self.metrics_history)[-self.alert_rules['low_success_rate']['window']:]
        
        # 检查成功率告警
        if len(recent_metrics) >= 10:
            success_rate = metrics.success_count / max(1, metrics.request_count)
            if success_rate < self.alert_rules['low_success_rate']['threshold']:
                self._add_alert('low_success_rate', f"成功率过低: {success_rate:.2%}")
        
        # 检查延迟告警
        if metrics.avg_latency > self.alert_rules['high_latency']['threshold']:
            self._add_alert('high_latency', f"延迟过高: {metrics.avg_latency:.2f}ms")
        
        # 检查代理失败告警
        if metrics.proxy_success_rate:
            for proxy, rate in metrics.proxy_success_rate.items():
                if rate < self.alert_rules['proxy_failure']['threshold']:
                    self._add_alert('proxy_failure', f"代理 {proxy} 失败率过高: {rate:.2%}")
        
        # 检查反爬虫检测峰值
        recent_detections = sum(m.anti_crawler_detections for m in recent_metrics)
        if recent_detections > self.alert_rules['anti_crawler_spike']['threshold']:
            self._add_alert('anti_crawler_spike', f"反爬虫检测峰值: {recent_detections}次")
    
    def _add_alert(self, alert_type: str, message: str):
        """添加告警"""
        alert = {
            'timestamp': datetime.now(),
            'type': alert_type,
            'message': message,
            'level': 'WARNING'
        }
        self.alerts.append(alert)
        logger.warning(f"性能告警: {message}")
    
    def get_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前性能指标"""
        with self.lock:
            if not self.metrics_history:
                return None
            return self.metrics_history[-1]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.metrics_history:
            return {}
        
        latest = self.metrics_history[-1]
        return {
            'uptime': str(datetime.now() - self.start_time),
            'total_requests': latest.request_count,
            'success_rate': latest.success_count / max(1, latest.request_count),
            'avg_latency': latest.avg_latency,
            'throughput': latest.throughput,
            'data_volume_mb': latest.data_volume / (1024 * 1024),
            'active_alerts': len(self.alerts),
            'proxy_count': len(latest.proxy_success_rate) if latest.proxy_success_rate else 0
        }
    
    def get_trend_analysis(self, period_minutes: int = 5) -> Dict[str, Any]:
        """获取趋势分析"""
        if not self.metrics_history:
            return {}
        
        cutoff_time = datetime.now() - timedelta(minutes=period_minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {}
        
        return {
            'period_minutes': period_minutes,
            'success_rate_trend': [m.success_count / max(1, m.request_count) for m in recent_metrics],
            'latency_trend': [m.avg_latency for m in recent_metrics],
            'throughput_trend': [m.throughput for m in recent_metrics],
            'sample_count': len(recent_metrics)
        }


class PerformanceVisualizer:
    """性能可视化器"""
    
    def __init__(self, monitor: RealTimeMonitor):
        self.monitor = monitor
        plt.style.use('seaborn-v0_8')
        
    def create_dashboard(self, save_path: str = None):
        """创建性能仪表板"""
        if not self.monitor.metrics_history:
            print("没有性能数据可显示")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('爬虫系统性能监控仪表板', fontsize=16)
        
        # 成功率趋势图
        self._plot_success_rate(axes[0, 0])
        
        # 延迟趋势图
        self._plot_latency(axes[0, 1])
        
        # 吞吐量趋势图
        self._plot_throughput(axes[1, 0])
        
        # 代理性能图
        self._plot_proxy_performance(axes[1, 1])
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"仪表板已保存到: {save_path}")
        
        plt.show()
    
    def _plot_success_rate(self, ax):
        """绘制成功率趋势图"""
        timestamps = [m.timestamp for m in self.monitor.metrics_history]
        success_rates = [m.success_count / max(1, m.request_count) for m in self.monitor.metrics_history]
        
        ax.plot(timestamps, success_rates, 'b-', linewidth=2, label='成功率')
        ax.axhline(y=0.7, color='r', linestyle='--', alpha=0.7, label='告警阈值')
        ax.set_title('请求成功率趋势')
        ax.set_ylabel('成功率')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_latency(self, ax):
        """绘制延迟趋势图"""
        timestamps = [m.timestamp for m in self.monitor.metrics_history]
        latencies = [m.avg_latency for m in self.monitor.metrics_history]
        
        ax.plot(timestamps, latencies, 'g-', linewidth=2, label='平均延迟')
        ax.axhline(y=500, color='r', linestyle='--', alpha=0.7, label='告警阈值')
        ax.set_title('请求延迟趋势')
        ax.set_ylabel('延迟 (ms)')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_throughput(self, ax):
        """绘制吞吐量趋势图"""
        timestamps = [m.timestamp for m in self.monitor.metrics_history]
        throughputs = [m.throughput for m in self.monitor.metrics_history]
        
        ax.plot(timestamps, throughputs, 'orange', linewidth=2, label='吞吐量')
        ax.set_title('系统吞吐量趋势')
        ax.set_ylabel('请求/秒')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_proxy_performance(self, ax):
        """绘制代理性能图"""
        if not self.monitor.metrics_history:
            return
        
        latest = self.monitor.metrics_history[-1]
        if not latest.proxy_success_rate:
            ax.text(0.5, 0.5, '暂无代理数据', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('代理性能')
            return
        
        proxies = list(latest.proxy_success_rate.keys())
        success_rates = [latest.proxy_success_rate[p] for p in proxies]
        
        colors = ['green' if rate > 0.7 else 'orange' if rate > 0.5 else 'red' for rate in success_rates]
        
        bars = ax.bar(proxies, success_rates, color=colors, alpha=0.7)
        ax.set_title('代理成功率')
        ax.set_ylabel('成功率')
        ax.tick_params(axis='x', rotation=45)
        
        # 添加数值标签
        for bar, rate in zip(bars, success_rates):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                   f'{rate:.1%}', ha='center', va='bottom', fontsize=9)
    
    def generate_report(self, output_path: str = None) -> str:
        """生成性能报告"""
        summary = self.monitor.get_performance_summary()
        trend = self.monitor.get_trend_analysis(10)
        
        report = {
            'summary': summary,
            'trend_analysis': trend,
            'alerts': list(self.monitor.alerts)[-10:],  # 最近10个告警
            'timestamp': datetime.now().isoformat()
        }
        
        report_str = json.dumps(report, indent=2, default=str)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_str)
            print(f"性能报告已保存到: {output_path}")
        
        return report_str
    
    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势（上升/下降/稳定）"""
        if len(values) < 2:
            return 'stable'
        
        # 使用线性回归判断趋势
        x = list(range(len(values)))
        y = values
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def clear_metrics(self):
        """清空指标历史"""
        with self.lock:
            self.metrics_history.clear()
            self.start_time = datetime.now()
            self.total_tasks_processed = 0
            self.total_tasks_failed = 0
            self.total_response_time = 0.0
            self.response_count = 0
            logger.info("性能指标已清空")


# 创建全局性能监控器实例
performance_monitor = RealTimeMonitor(alert_threshold=0.7)

# 测试代码：非洲网站性能监控示例
if __name__ == "__main__":
    # 创建实时监控器
    monitor = RealTimeMonitor(alert_threshold=0.7)
    
    # 模拟南非和肯尼亚网站请求
    print("开始模拟非洲网站性能监控...")
    
    # 模拟南非网站请求
    monitor.collect_request_metrics(
        url="https://www.southafrica.net/",
        proxy="proxy_za_1",
        success=True,
        latency=320,
        data_size=1500,
        anti_crawler_detected=False,
        retry_count=0
    )
    
    # 模拟肯尼亚网站请求
    monitor.collect_request_metrics(
        url="https://www.magicalkenya.com/",
        proxy="proxy_ke_1",
        success=True,
        latency=280,
        data_size=1200,
        anti_crawler_detected=False,
        retry_count=0
    )
    
    # 模拟一些失败的请求
    monitor.collect_request_metrics(
        url="https://www.nigeria.gov.ng/",
        proxy="proxy_ng_1",
        success=False,
        latency=650,
        data_size=0,
        anti_crawler_detected=True,
        retry_count=2
    )
    
    # 获取性能摘要
    summary = monitor.get_performance_summary()
    print("\n=== 性能摘要 ===")
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # 检查告警
    print("\n=== 告警信息 ===")
    for alert in monitor.alerts:
        print(f"- {alert}")
    
    # 创建可视化报告
    visualizer = PerformanceVisualizer(monitor)
    
    # 生成性能报告
    report = visualizer.generate_report("performance_report.json")
    print("\n性能报告已生成")
    
    # 显示仪表板（可选）
    print("\n正在生成性能仪表板...")
    visualizer.create_dashboard("performance_dashboard.png")
    
    print("\n非洲网站性能监控测试完成！")