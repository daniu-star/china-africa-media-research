"""
智能重试优化器
基于历史错误数据动态优化重试策略
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics


class RetryStrategy(Enum):
    """重试策略类型"""
    CONSERVATIVE = "conservative"  # 保守策略：重试次数少，延迟长
    BALANCED = "balanced"          # 平衡策略：中等重试次数和延迟
    AGGRESSIVE = "aggressive"      # 激进策略：重试次数多，延迟短
    ADAPTIVE = "adaptive"          # 自适应策略：根据错误模式动态调整


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int
    base_delay: float
    max_delay: float
    backoff_factor: float
    timeout_multiplier: float
    strategy: RetryStrategy


@dataclass
class DomainPerformance:
    """域名性能统计"""
    domain: str
    success_rate: float
    avg_response_time: float
    error_distribution: Dict[str, int]
    last_updated: datetime


class SmartRetryOptimizer:
    """智能重试优化器"""
    
    def __init__(self):
        self.domain_performance: Dict[str, DomainPerformance] = {}
        self.error_history: List[Dict] = []
        self.performance_thresholds = {
            'high_success_rate': 0.95,    # 高成功率阈值
            'low_success_rate': 0.80,     # 低成功率阈值
            'fast_response': 2.0,         # 快速响应阈值（秒）
            'slow_response': 10.0         # 慢速响应阈值（秒）
        }
        self.logger = logging.getLogger(__name__)
        
        # 默认重试策略配置
        self.default_strategies = {
            RetryStrategy.CONSERVATIVE: RetryConfig(
                max_retries=2,
                base_delay=5.0,
                max_delay=30.0,
                backoff_factor=2.0,
                timeout_multiplier=1.5,
                strategy=RetryStrategy.CONSERVATIVE
            ),
            RetryStrategy.BALANCED: RetryConfig(
                max_retries=3,
                base_delay=3.0,
                max_delay=20.0,
                backoff_factor=1.5,
                timeout_multiplier=1.2,
                strategy=RetryStrategy.BALANCED
            ),
            RetryStrategy.AGGRESSIVE: RetryConfig(
                max_retries=5,
                base_delay=1.0,
                max_delay=10.0,
                backoff_factor=1.2,
                timeout_multiplier=1.0,
                strategy=RetryStrategy.AGGRESSIVE
            )
        }
    
    def record_request(self, domain: str, success: bool, response_time: float, 
                      error_type: Optional[str] = None):
        """记录请求结果"""
        if domain not in self.domain_performance:
            self.domain_performance[domain] = DomainPerformance(
                domain=domain,
                success_rate=0.0,
                avg_response_time=0.0,
                error_distribution={},
                last_updated=datetime.now()
            )
        
        performance = self.domain_performance[domain]
        
        # 更新成功率（简化计算）
        total_requests = len([r for r in self.error_history if r.get('domain') == domain]) + 1
        successful_requests = len([r for r in self.error_history if r.get('domain') == domain and r.get('success')]) + (1 if success else 0)
        performance.success_rate = successful_requests / total_requests
        
        # 更新平均响应时间（移动平均）
        if performance.avg_response_time == 0:
            performance.avg_response_time = response_time
        else:
            alpha = 0.1  # 平滑因子
            performance.avg_response_time = (1 - alpha) * performance.avg_response_time + alpha * response_time
        
        # 更新错误分布
        if error_type:
            performance.error_distribution[error_type] = performance.error_distribution.get(error_type, 0) + 1
        
        performance.last_updated = datetime.now()
        
        # 记录到历史
        self.error_history.append({
            'domain': domain,
            'success': success,
            'response_time': response_time,
            'error_type': error_type,
            'timestamp': datetime.now()
        })
        
        # 限制历史记录大小
        if len(self.error_history) > 10000:
            self.error_history = self.error_history[-10000:]
    
    def get_optimal_retry_config(self, domain: str, error_type: Optional[str] = None) -> RetryConfig:
        """获取最优重试配置"""
        if domain not in self.domain_performance:
            # 新域名，使用平衡策略
            return self.default_strategies[RetryStrategy.BALANCED]
        
        performance = self.domain_performance[domain]
        
        # 根据性能指标选择策略
        strategy = self._select_strategy(performance, error_type)
        base_config = self.default_strategies[strategy]
        
        # 根据具体错误类型微调配置
        optimized_config = self._optimize_config(base_config, performance, error_type)
        
        return optimized_config
    
    def _select_strategy(self, performance: DomainPerformance, error_type: Optional[str]) -> RetryStrategy:
        """选择重试策略"""
        # 根据成功率选择策略
        if performance.success_rate >= self.performance_thresholds['high_success_rate']:
            # 高成功率域名，使用保守策略
            return RetryStrategy.CONSERVATIVE
        elif performance.success_rate <= self.performance_thresholds['low_success_rate']:
            # 低成功率域名，使用激进策略
            return RetryStrategy.AGGRESSIVE
        else:
            # 中等成功率，使用平衡策略
            return RetryStrategy.BALANCED
    
    def _optimize_config(self, base_config: RetryConfig, performance: DomainPerformance, 
                        error_type: Optional[str]) -> RetryConfig:
        """优化重试配置"""
        config = RetryConfig(
            max_retries=base_config.max_retries,
            base_delay=base_config.base_delay,
            max_delay=base_config.max_delay,
            backoff_factor=base_config.backoff_factor,
            timeout_multiplier=base_config.timeout_multiplier,
            strategy=base_config.strategy
        )
        
        # 根据响应时间调整超时倍数
        if performance.avg_response_time > self.performance_thresholds['slow_response']:
            config.timeout_multiplier *= 1.5
        elif performance.avg_response_time < self.performance_thresholds['fast_response']:
            config.timeout_multiplier *= 0.8
        
        # 根据错误类型调整配置
        if error_type:
            config = self._adjust_for_error_type(config, error_type, performance)
        
        return config
    
    def _adjust_for_error_type(self, config: RetryConfig, error_type: str, 
                              performance: DomainPerformance) -> RetryConfig:
        """根据错误类型调整配置"""
        error_frequency = performance.error_distribution.get(error_type, 0)
        
        if error_type in ['timeout', 'connection']:
            # 网络相关错误，增加重试次数和延迟
            config.max_retries = min(config.max_retries + 1, 10)
            config.base_delay = min(config.base_delay * 1.2, 15.0)
            
        elif error_type == 'rate_limit':
            # 速率限制错误，大幅增加延迟
            config.base_delay = max(config.base_delay * 2.0, 30.0)
            config.max_delay = max(config.max_delay * 1.5, 60.0)
            
        elif error_type == 'anti_crawler':
            # 反爬虫错误，减少重试次数但增加延迟
            config.max_retries = max(config.max_retries - 1, 1)
            config.base_delay = min(config.base_delay * 1.5, 20.0)
            
        elif error_type in ['server_error', 'client_error']:
            # 服务器/客户端错误，保守处理
            config.max_retries = min(config.max_retries, 2)
            config.base_delay = min(config.base_delay * 1.1, 10.0)
        
        # 根据错误频率进一步调整
        if error_frequency > 10:
            config.max_retries = min(config.max_retries + 1, 8)
            config.base_delay = min(config.base_delay * 1.3, 25.0)
        
        return config
    
    def get_domain_analysis(self, domain: str) -> Dict[str, Any]:
        """获取域名分析报告"""
        if domain not in self.domain_performance:
            return {'error': '域名不存在'}
        
        performance = self.domain_performance[domain]
        recent_errors = [
            e for e in self.error_history 
            if e['domain'] == domain and e['timestamp'] > datetime.now() - timedelta(hours=24)
        ]
        
        analysis = {
            'domain': domain,
            'success_rate': performance.success_rate,
            'avg_response_time': performance.avg_response_time,
            'total_requests': len([r for r in self.error_history if r['domain'] == domain]),
            'recent_errors_24h': len([e for e in recent_errors if not e['success']]),
            'error_distribution': performance.error_distribution,
            'recommended_strategy': self.get_optimal_retry_config(domain).strategy.value,
            'performance_rating': self._calculate_performance_rating(performance),
            'optimization_suggestions': self._generate_suggestions(performance)
        }
        
        return analysis
    
    def _calculate_performance_rating(self, performance: DomainPerformance) -> str:
        """计算性能评级"""
        if performance.success_rate >= 0.95 and performance.avg_response_time <= 3.0:
            return 'excellent'
        elif performance.success_rate >= 0.85 and performance.avg_response_time <= 5.0:
            return 'good'
        elif performance.success_rate >= 0.70:
            return 'fair'
        else:
            return 'poor'
    
    def _generate_suggestions(self, performance: DomainPerformance) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        if performance.success_rate < 0.80:
            suggestions.append("成功率较低，建议使用更激进的重试策略")
        
        if performance.avg_response_time > 10.0:
            suggestions.append("响应时间过长，建议增加超时设置")
        
        if 'rate_limit' in performance.error_distribution:
            suggestions.append("检测到速率限制错误，建议降低请求频率")
        
        if 'anti_crawler' in performance.error_distribution:
            suggestions.append("检测到反爬虫错误，建议增强反反爬虫能力")
        
        return suggestions
    
    def export_optimization_report(self, filename: str) -> bool:
        """导出优化报告"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'domain_analysis': {},
                'summary_statistics': self._get_summary_statistics(),
                'optimization_recommendations': self._get_global_recommendations()
            }
            
            for domain in self.domain_performance:
                report['domain_analysis'][domain] = self.get_domain_analysis(domain)
            
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"优化报告已导出到: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出优化报告失败: {e}")
            return False
    
    def _get_summary_statistics(self) -> Dict[str, Any]:
        """获取汇总统计"""
        if not self.domain_performance:
            return {}
        
        success_rates = [p.success_rate for p in self.domain_performance.values()]
        response_times = [p.avg_response_time for p in self.domain_performance.values()]
        
        return {
            'total_domains': len(self.domain_performance),
            'avg_success_rate': statistics.mean(success_rates) if success_rates else 0,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'best_performing_domain': max(self.domain_performance.items(), 
                                        key=lambda x: x[1].success_rate)[0] if self.domain_performance else None
        }
    
    def _get_global_recommendations(self) -> List[str]:
        """获取全局优化建议"""
        recommendations = []
        
        if not self.domain_performance:
            return recommendations
        
        # 分析整体性能
        avg_success_rate = self._get_summary_statistics()['avg_success_rate']
        
        if avg_success_rate < 0.85:
            recommendations.append("整体成功率较低，建议检查网络连接和代理设置")
        
        # 检查常见错误模式
        total_errors = sum(len(p.error_distribution) for p in self.domain_performance.values())
        if total_errors > 100:
            recommendations.append("错误数量较多，建议优化错误处理逻辑")
        
        return recommendations


# 使用示例
if __name__ == "__main__":
    # 创建优化器
    optimizer = SmartRetryOptimizer()
    
    # 模拟记录一些请求
    test_data = [
        ("example.com", True, 1.5, None),
        ("example.com", False, 5.0, "timeout"),
        ("test.org", True, 2.0, None),
        ("test.org", True, 1.8, None),
        ("example.com", True, 1.2, None),
    ]
    
    for domain, success, response_time, error_type in test_data:
        optimizer.record_request(domain, success, response_time, error_type)
    
    # 获取最优配置
    config = optimizer.get_optimal_retry_config("example.com", "timeout")
    print("最优重试配置:", config)
    
    # 获取域名分析
    analysis = optimizer.get_domain_analysis("example.com")
    print("域名分析:", analysis)
    
    # 导出报告
    optimizer.export_optimization_report("optimization_report.json")