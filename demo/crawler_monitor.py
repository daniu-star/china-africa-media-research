"""
爬虫监控仪表板
提供实时监控、性能分析和警报功能
"""

import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from flask import Flask, render_template, jsonify
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class CrawlerStatus(Enum):
    """爬虫状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class CrawlerMetrics:
    """爬虫性能指标"""
    timestamp: datetime
    articles_crawled: int
    articles_failed: int
    requests_made: int
    requests_failed: int
    avg_response_time: float
    memory_usage: float
    cpu_usage: float


@dataclass
class Alert:
    """警报信息"""
    id: str
    title: str
    message: str
    severity: str  # info, warning, error, critical
    timestamp: datetime
    acknowledged: bool = False


class CrawlerMonitor:
    """爬虫监控器"""
    
    def __init__(self, update_interval: int = 10):
        self.metrics_history: List[CrawlerMetrics] = []
        self.alerts: List[Alert] = []
        self.status = CrawlerStatus.IDLE
        self.current_task: Optional[Dict] = None
        self.update_interval = update_interval
        self.logger = logging.getLogger(__name__)
        
        # 启动监控线程
        self._monitoring_thread = None
        self._stop_monitoring = False
        self._start_monitoring()
    
    def _start_monitoring(self):
        """启动监控线程"""
        self._monitoring_thread = threading.Thread(target=self._monitor_loop)
        self._monitoring_thread.daemon = True
        self._monitoring_thread.start()
    
    def _monitor_loop(self):
        """监控循环"""
        while not self._stop_monitoring:
            try:
                self._collect_metrics()
                self._check_alerts()
                time.sleep(self.update_interval)
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                time.sleep(self.update_interval)
    
    def _collect_metrics(self):
        """收集性能指标"""
        # 这里可以集成实际的性能监控
        # 目前使用模拟数据
        metrics = CrawlerMetrics(
            timestamp=datetime.now(),
            articles_crawled=100,  # 模拟数据
            articles_failed=5,     # 模拟数据
            requests_made=150,     # 模拟数据
            requests_failed=8,     # 模拟数据
            avg_response_time=2.5,  # 模拟数据
            memory_usage=45.2,     # 模拟数据
            cpu_usage=23.1         # 模拟数据
        )
        
        self.metrics_history.append(metrics)
        
        # 限制历史记录大小
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
    
    def _check_alerts(self):
        """检查警报条件"""
        if not self.metrics_history:
            return
        
        latest_metrics = self.metrics_history[-1]
        
        # 检查错误率警报
        error_rate = latest_metrics.requests_failed / max(latest_metrics.requests_made, 1)
        if error_rate > 0.1:  # 错误率超过10%
            self._create_alert(
                "high_error_rate",
                "高错误率警报",
                f"当前错误率: {error_rate:.1%}",
                "warning"
            )
        
        # 检查响应时间警报
        if latest_metrics.avg_response_time > 10:  # 平均响应时间超过10秒
            self._create_alert(
                "slow_response",
                "响应时间过长",
                f"平均响应时间: {latest_metrics.avg_response_time:.1f}秒",
                "warning"
            )
        
        # 检查内存使用警报
        if latest_metrics.memory_usage > 80:  # 内存使用超过80%
            self._create_alert(
                "high_memory",
                "内存使用过高",
                f"内存使用率: {latest_metrics.memory_usage:.1f}%",
                "error"
            )
    
    def _create_alert(self, alert_id: str, title: str, message: str, severity: str):
        """创建警报"""
        # 检查是否已存在相同警报
        existing_alert = next((a for a in self.alerts if a.id == alert_id and not a.acknowledged), None)
        if existing_alert:
            return  # 警报已存在
        
        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            severity=severity,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        self.logger.warning(f"创建警报: {title} - {message}")
    
    def update_status(self, status: CrawlerStatus, task_info: Optional[Dict] = None):
        """更新爬虫状态"""
        self.status = status
        self.current_task = task_info
        
        if status == CrawlerStatus.ERROR:
            self._create_alert(
                "crawler_error",
                "爬虫错误",
                "爬虫遇到错误，已停止运行",
                "error"
            )
    
    def acknowledge_alert(self, alert_id: str):
        """确认警报"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                break
    
    def get_dashboard_data(self, hours: int = 24) -> Dict[str, Any]:
        """获取仪表板数据"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {
                'status': self.status.value,
                'current_task': self.current_task,
                'alerts': [a.__dict__ for a in self.alerts if not a.acknowledged],
                'metrics': {},
                'charts': {}
            }
        
        # 计算汇总指标
        total_articles = sum(m.articles_crawled for m in recent_metrics)
        total_failed = sum(m.articles_failed for m in recent_metrics)
        success_rate = (total_articles - total_failed) / max(total_articles, 1)
        
        metrics = {
            'total_articles': total_articles,
            'success_rate': success_rate,
            'avg_response_time': recent_metrics[-1].avg_response_time,
            'memory_usage': recent_metrics[-1].memory_usage,
            'cpu_usage': recent_metrics[-1].cpu_usage
        }
        
        # 生成图表数据
        charts = self._generate_charts(recent_metrics)
        
        return {
            'status': self.status.value,
            'current_task': self.current_task,
            'alerts': [a.__dict__ for a in self.alerts if not a.acknowledged],
            'metrics': metrics,
            'charts': charts
        }
    
    def _generate_charts(self, metrics: List[CrawlerMetrics]) -> Dict[str, Any]:
        """生成图表数据"""
        timestamps = [m.timestamp for m in metrics]
        articles_crawled = [m.articles_crawled for m in metrics]
        articles_failed = [m.articles_failed for m in metrics]
        response_times = [m.avg_response_time for m in metrics]
        memory_usage = [m.memory_usage for m in metrics]
        
        # 创建图表
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('文章爬取统计', '响应时间', '内存使用', 'CPU使用'),
            specs=[[{"secondary_y": True}, {}], [{}, {}]]
        )
        
        # 文章爬取统计
        fig.add_trace(
            go.Scatter(x=timestamps, y=articles_crawled, name='成功爬取'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=timestamps, y=articles_failed, name='爬取失败'),
            row=1, col=1, secondary_y=True
        )
        
        # 响应时间
        fig.add_trace(
            go.Scatter(x=timestamps, y=response_times, name='响应时间'),
            row=1, col=2
        )
        
        # 内存使用
        fig.add_trace(
            go.Scatter(x=timestamps, y=memory_usage, name='内存使用率'),
            row=2, col=1
        )
        
        # CPU使用（模拟数据）
        cpu_usage = [m.cpu_usage for m in metrics]
        fig.add_trace(
            go.Scatter(x=timestamps, y=cpu_usage, name='CPU使用率'),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=True)
        
        return {
            'performance_chart': fig.to_json()
        }
    
    def export_report(self, filename: str) -> bool:
        """导出监控报告"""
        try:
            report = {
                'export_timestamp': datetime.now().isoformat(),
                'status': self.status.value,
                'current_task': self.current_task,
                'recent_alerts': [a.__dict__ for a in self.alerts[-20:]],
                'summary_metrics': self.get_dashboard_data()['metrics'],
                'metrics_history': [
                    {
                        'timestamp': m.timestamp.isoformat(),
                        'articles_crawled': m.articles_crawled,
                        'articles_failed': m.articles_failed,
                        'avg_response_time': m.avg_response_time,
                        'memory_usage': m.memory_usage,
                        'cpu_usage': m.cpu_usage
                    }
                    for m in self.metrics_history[-100:]
                ]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"监控报告已导出到: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出监控报告失败: {e}")
            return False
    
    def stop_monitoring(self):
        """停止监控"""
        self._stop_monitoring = True
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)


# Web仪表板应用
app = Flask(__name__)
monitor = CrawlerMonitor()


@app.route('/')
def dashboard():
    """主仪表板页面"""
    return render_template('dashboard.html')


@app.route('/api/stats')
def get_stats():
    """获取统计数据的API接口"""
    data = monitor.get_dashboard_data()
    return jsonify(data)


@app.route('/api/alerts/acknowledge/<alert_id>', methods=['POST'])
def acknowledge_alert(alert_id):
    """确认警报的API接口"""
    monitor.acknowledge_alert(alert_id)
    return jsonify({'success': True})


@app.route('/api/export')
def export_report():
    """导出报告的API接口"""
    filename = f"crawler_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    success = monitor.export_report(filename)
    return jsonify({'success': success, 'filename': filename})


if __name__ == "__main__":
    # 启动Web服务器
    app.run(host='0.0.0.0', port=8000, debug=True)