#!/usr/bin/env python3
"""
任务调度优化模块
提供智能任务调度、负载均衡和重试策略优化
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """任务优先级枚举"""
    CRITICAL = 5    # 紧急任务（系统监控、关键数据）
    HIGH = 4        # 高优先级任务（实时数据、重要关键词）
    MEDIUM = 3      # 中等优先级任务（常规爬取）
    LOW = 2         # 低优先级任务（历史数据、批量处理）
    BACKGROUND = 1  # 后台任务（数据清理、统计）

class ErrorType(Enum):
    """错误类型枚举"""
    NETWORK = "network"      # 网络错误（可重试）
    PARSING = "parsing"      # 解析错误（有限重试）
    RESOURCE = "resource"    # 资源错误（需要调整）
    SYSTEM = "system"        # 系统错误（需要干预）
    CONTENT = "content"      # 内容错误（可能无法解决）

@dataclass
class WorkerPerformance:
    """工作节点性能指标"""
    worker_id: str
    success_rate: float           # 成功率（0-1）
    avg_response_time: float     # 平均响应时间（秒）
    current_load: int            # 当前负载（任务数）
    last_active: datetime        # 最后活动时间
    capabilities: List[str]      # 支持的能力（如：js_rendering, image_processing）
    
    @property
    def performance_score(self) -> float:
        """计算性能评分（0-100）"""
        # 成功率权重：40%
        success_score = self.success_rate * 40
        
        # 响应时间权重：30%（响应时间越短，分数越高）
        response_score = max(0, 30 - (self.avg_response_time * 10))
        
        # 负载权重：20%（负载越低，分数越高）
        load_score = max(0, 20 - (self.current_load * 2))
        
        # 活跃度权重：10%（最近活跃加分）
        time_diff = (datetime.now() - self.last_active).total_seconds()
        activity_score = max(0, 10 - (time_diff / 60))  # 每分钟衰减
        
        return success_score + response_score + load_score + activity_score

class IntelligentTaskScheduler:
    """智能任务调度器"""
    
    def __init__(self):
        self.worker_performance: Dict[str, WorkerPerformance] = {}
        self.task_history: List[Dict[str, Any]] = []
        self.error_stats: Dict[str, Dict[str, Any]] = {}
        self.scheduling_metrics = {
            'total_tasks_scheduled': 0,
            'successful_schedules': 0,
            'failed_schedules': 0,
            'avg_scheduling_time': 0.0,
            'load_balance_score': 0.0
        }
    
    def calculate_task_priority(self, task: Dict[str, Any]) -> TaskPriority:
        """智能计算任务优先级（支持中国相关关键词高优先级）"""
        base_priority = TaskPriority.MEDIUM
        
        # 关键词重要性分析
        keyword = task.get('keyword', '').lower()
        
        # 中国相关关键词 - 最高优先级
        china_keywords = [
            'china', 'chinese', 'beijing', 'shanghai', 'guangzhou', 'shenzhen',
            'belt and road', 'bri', 'one belt one road', '一带一路',
            'south china sea', 'scs', '中国南海', '南海',
            'taiwan', 'taiwan strait', '台湾', '台海',
            'xinjiang', 'tibet', '新疆', '西藏',
            'hong kong', 'macau', '香港', '澳门',
            'communist party of china', 'cpc', '中国共产党',
            'xi jinping', '习近平', 'chinese government', '中国政府',
            'people\'s liberation army', 'pla', '中国人民解放军',
            'chinese economy', '中国经济', 'chinese foreign policy', '中国外交政策'
        ]
        
        # 检查是否为中国相关关键词
        if any(china_keyword in keyword for china_keyword in china_keywords):
            base_priority = TaskPriority.HIGH
            logger.info(f"检测到中国相关关键词 '{keyword}'，设置为高优先级")
        
        # 紧急关键词（实时监控、重要事件）
        urgent_keywords = ['breaking', 'urgent', 'emergency', 'critical', '实时', '紧急']
        if any(urgent in keyword for urgent in urgent_keywords):
            base_priority = TaskPriority.CRITICAL
        
        # 高优先级关键词（重要数据源）
        high_priority_keywords = ['news', 'update', 'latest', 'trending', '新闻', '最新']
        if any(high in keyword for high in high_priority_keywords):
            base_priority = TaskPriority.HIGH
        
        # 任务属性调整
        pages = task.get('pages', 1)
        if pages > 10:  # 大量页面任务降低优先级
            base_priority = TaskPriority(max(base_priority.value - 1, TaskPriority.BACKGROUND.value))
        
        # 时间敏感性（最近创建的任务优先级更高）
        created_at = task.get('created_at')
        if created_at:
            try:
                task_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                time_diff = (datetime.now() - task_time).total_seconds()
                if time_diff > 3600:  # 超过1小时的任务降低优先级
                    base_priority = TaskPriority(max(base_priority.value - 1, TaskPriority.BACKGROUND.value))
            except:
                pass
        
        return base_priority
    
    def select_best_worker(self, task: Dict[str, Any], available_workers: List[str], worker_loads: Dict[str, int] = None) -> Optional[str]:
        """选择最适合的工作节点（基于负载均衡）"""
        if not available_workers:
            return None
        
        # 如果没有提供负载信息，使用默认策略
        if worker_loads is None:
            return available_workers[0]
        
        # 过滤出有负载记录的工作节点
        workers_with_loads = [w for w in available_workers if w in worker_loads]
        
        if not workers_with_loads:
            return available_workers[0]
        
        # 检查所有工作节点的负载是否都为0（初始状态）
        all_zero_load = all(worker_loads[w] == 0 for w in workers_with_loads)
        
        if all_zero_load:
            # 如果所有节点负载都为0，立即分配任务给第一个可用工作节点
            # 避免复杂的性能计算导致死锁
            return available_workers[0]
        
        # 选择负载最低的工作节点
        best_worker = min(workers_with_loads, key=lambda w: worker_loads[w])
        
        # 如果有多个负载相同的工作节点，考虑性能因素
        min_load = worker_loads[best_worker]
        candidates = [w for w in workers_with_loads if worker_loads[w] == min_load]
        
        if len(candidates) > 1:
            # 在负载相同的工作节点中，选择性能最好的
            candidate_scores = {}
            for worker_id in candidates:
                if worker_id in self.worker_performance:
                    performance = self.worker_performance[worker_id]
                    score = performance.performance_score
                    
                    # 任务特定调整
                    if 'js_rendering' in task.get('requirements', []) and 'js_rendering' in performance.capabilities:
                        score *= 1.2  # 有JS渲染能力的工作节点加分
                    
                    candidate_scores[worker_id] = score
                else:
                    candidate_scores[worker_id] = 50
            
            if candidate_scores:
                best_worker = max(candidate_scores.items(), key=lambda x: x[1])[0]
        
        return best_worker
    
    def update_worker_performance(self, worker_id: str, worker_stats: Dict[str, Any]):
        """更新工作节点性能数据（基于心跳统计）"""
        if worker_id not in self.worker_performance:
            # 初始化新工作节点
            self.worker_performance[worker_id] = WorkerPerformance(
                worker_id=worker_id,
                success_rate=0.8,  # 默认成功率
                avg_response_time=5.0,  # 默认响应时间
                current_load=0,
                last_active=datetime.now(),
                capabilities=[]
            )
        
        performance = self.worker_performance[worker_id]
        
        # 更新成功率（如果工作节点提供了成功率数据）
        if 'success_rate' in worker_stats:
            performance.success_rate = worker_stats['success_rate']
        elif 'tasks_completed' in worker_stats and 'tasks_failed' in worker_stats:
            # 计算成功率
            total_tasks = worker_stats['tasks_completed'] + worker_stats['tasks_failed']
            if total_tasks > 0:
                performance.success_rate = worker_stats['tasks_completed'] / total_tasks
        
        # 更新平均响应时间
        if 'avg_response_time' in worker_stats:
            performance.avg_response_time = worker_stats['avg_response_time']
        elif 'response_times' in worker_stats and worker_stats['response_times']:
            # 计算平均响应时间
            performance.avg_response_time = statistics.mean(worker_stats['response_times'])
        
        # 更新最后活动时间
        if 'last_active' in worker_stats:
            # 将时间戳转换为datetime对象
            last_active_ts = worker_stats['last_active']
            performance.last_active = datetime.fromtimestamp(last_active_ts)
        else:
            performance.last_active = datetime.now()
        
        # 更新当前负载（需要外部调用者提供）
        # performance.current_load = current_load
        
        logger.debug(f"更新工作节点 {worker_id} 性能数据: 成功率={performance.success_rate:.2f}, "
                    f"平均响应时间={performance.avg_response_time:.2f}s")
    
    def get_retry_delay(self, error_type: ErrorType, retry_count: int, task: Dict[str, Any]) -> float:
        """智能计算重试延迟时间"""
        base_delays = {
            ErrorType.NETWORK: [5, 15, 30, 60],      # 网络错误：逐步增加延迟
            ErrorType.PARSING: [10, 30, 60],        # 解析错误：中等延迟
            ErrorType.RESOURCE: [30, 60, 120],      # 资源错误：较长延迟
            ErrorType.SYSTEM: [60, 300, 600],       # 系统错误：很长延迟
            ErrorType.CONTENT: [10, 30, 60]         # 内容错误：中等延迟
        }
        
        delays = base_delays.get(error_type, [10, 30, 60])
        
        if retry_count < len(delays):
            base_delay = delays[retry_count]
        else:
            base_delay = delays[-1]  # 使用最后一个延迟
        
        # 根据任务优先级调整延迟
        priority = self.calculate_task_priority(task)
        priority_multiplier = {
            TaskPriority.CRITICAL: 0.5,    # 紧急任务：减少延迟
            TaskPriority.HIGH: 0.7,       # 高优先级：较小延迟
            TaskPriority.MEDIUM: 1.0,      # 中等优先级：标准延迟
            TaskPriority.LOW: 1.5,         # 低优先级：增加延迟
            TaskPriority.BACKGROUND: 2.0  # 后台任务：最大延迟
        }
        
        delay = base_delay * priority_multiplier.get(priority, 1.0)
        
        # 添加随机抖动（±20%）避免同步重试
        import random
        jitter = random.uniform(0.8, 1.2)
        delay *= jitter
        
        return max(1.0, delay)  # 最小延迟1秒
    
    def should_retry_task(self, error_type: ErrorType, retry_count: int, task: Dict[str, Any]) -> bool:
        """判断是否应该重试任务"""
        max_retries_by_type = {
            ErrorType.NETWORK: 5,      # 网络错误：最多重试5次
            ErrorType.PARSING: 2,     # 解析错误：最多重试2次
            ErrorType.RESOURCE: 3,    # 资源错误：最多重试3次
            ErrorType.SYSTEM: 1,      # 系统错误：最多重试1次
            ErrorType.CONTENT: 2      # 内容错误：最多重试2次
        }
        
        max_retries = max_retries_by_type.get(error_type, 3)
        
        if retry_count >= max_retries:
            return False
        
        # 根据任务优先级调整重试策略
        priority = self.calculate_task_priority(task)
        if priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]:
            # 高优先级任务增加重试机会
            max_retries += 1
        
        return retry_count < max_retries
    
    def get_scheduling_metrics(self) -> Dict[str, Any]:
        """获取调度性能指标"""
        # 计算负载均衡分数
        if self.worker_performance:
            loads = [perf.current_load for perf in self.worker_performance.values()]
            if loads:
                avg_load = statistics.mean(loads)
                if avg_load > 0:
                    # 负载均衡分数：1 - (标准差/平均值)
                    std_dev = statistics.stdev(loads) if len(loads) > 1 else 0
                    self.scheduling_metrics['load_balance_score'] = max(0, 1 - (std_dev / avg_load))
        
        return self.scheduling_metrics.copy()

# 创建全局调度器实例
scheduler = IntelligentTaskScheduler()

def classify_error(error: Exception) -> ErrorType:
    """分类错误类型"""
    error_name = type(error).__name__
    
    # 网络错误
    network_errors = ['ConnectionError', 'Timeout', 'HTTPError', 'SSLError', 'ProxyError']
    if any(network_error in error_name for network_error in network_errors):
        return ErrorType.NETWORK
    
    # 解析错误
    parsing_errors = ['JSONDecodeError', 'ParseError', 'XMLSyntaxError', 'HTMLParseError']
    if any(parsing_error in error_name for parsing_error in parsing_errors):
        return ErrorType.PARSING
    
    # 资源错误
    resource_errors = ['MemoryError', 'ResourceExhausted', 'TooManyRedirects']
    if any(resource_error in error_name for resource_error in resource_errors):
        return ErrorType.RESOURCE
    
    # 系统错误
    system_errors = ['OSError', 'IOError', 'PermissionError', 'FileNotFoundError']
    if any(system_error in error_name for system_error in system_errors):
        return ErrorType.SYSTEM
    
    # 默认归类为内容错误
    return ErrorType.CONTENT