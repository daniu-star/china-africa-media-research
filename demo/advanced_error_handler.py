"""
高级错误处理与重试机制优化模块
为非洲报纸爬虫提供智能错误恢复、监控和优化建议功能
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import json


class ErrorSeverity(Enum):
    """错误严重程度级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """错误上下文信息"""
    url: str
    method: str
    timestamp: datetime
    error_type: str
    error_message: str
    severity: ErrorSeverity
    retry_count: int
    response_code: Optional[int] = None
    response_headers: Optional[Dict] = None
    request_headers: Optional[Dict] = None
    proxy_used: Optional[str] = None
    user_agent: Optional[str] = None


class AdvancedErrorHandler:
    """高级错误处理器"""
    
    def __init__(self, max_error_history: int = 1000):
        self.error_history: List[ErrorContext] = []
        self.max_error_history = max_error_history
        self.error_patterns: Dict[str, Dict] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化恢复策略
        self._initialize_recovery_strategies()
    
    def _initialize_recovery_strategies(self):
        """初始化错误恢复策略"""
        self.recovery_strategies = {
            "timeout": self._handle_timeout_error,
            "connection": self._handle_connection_error,
            "rate_limit": self._handle_rate_limit_error,
            "server_error": self._handle_server_error,
            "client_error": self._handle_client_error,
            "anti_crawler": self._handle_anti_crawler_error
        }
    
    def record_error(self, error_context: ErrorContext):
        """记录错误信息"""
        self.error_history.append(error_context)
        
        # 限制历史记录大小
        if len(self.error_history) > self.max_error_history:
            self.error_history = self.error_history[-self.max_error_history:]
        
        # 更新错误模式分析
        self._update_error_patterns(error_context)
        
        self.logger.warning(f"记录错误: {error_context.error_type} - {error_context.error_message}")
    
    def _update_error_patterns(self, error_context: ErrorContext):
        """更新错误模式分析"""
        error_type = error_context.error_type
        domain = self._extract_domain(error_context.url)
        
        if error_type not in self.error_patterns:
            self.error_patterns[error_type] = {}
        
        if domain not in self.error_patterns[error_type]:
            self.error_patterns[error_type][domain] = {
                'count': 0,
                'first_occurrence': error_context.timestamp,
                'last_occurrence': error_context.timestamp,
                'severity_distribution': {}
            }
        
        pattern = self.error_patterns[error_type][domain]
        pattern['count'] += 1
        pattern['last_occurrence'] = error_context.timestamp
        
        severity = error_context.severity.value
        if severity not in pattern['severity_distribution']:
            pattern['severity_distribution'][severity] = 0
        pattern['severity_distribution'][severity] += 1
    
    def _extract_domain(self, url: str) -> str:
        """从URL中提取域名"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    
    def get_recovery_strategy(self, error_type: str, url: str) -> Optional[Callable]:
        """获取错误恢复策略"""
        domain = self._extract_domain(url)
        
        # 检查是否有特定域名的恢复策略
        if error_type in self.error_patterns:
            if domain in self.error_patterns[error_type]:
                pattern = self.error_patterns[error_type][domain]
                
                # 如果错误频率过高，可能需要更激进的策略
                if pattern['count'] > 10:
                    return self._get_aggressive_recovery_strategy(error_type)
        
        # 返回默认恢复策略
        return self.recovery_strategies.get(error_type)
    
    def _get_aggressive_recovery_strategy(self, error_type: str) -> Callable:
        """获取更激进的恢复策略"""
        aggressive_strategies = {
            "timeout": self._handle_timeout_error_aggressive,
            "connection": self._handle_connection_error_aggressive,
            "anti_crawler": self._handle_anti_crawler_error_aggressive
        }
        return aggressive_strategies.get(error_type, self.recovery_strategies.get(error_type))
    
    # 错误恢复策略实现
    def _handle_timeout_error(self, error_context: ErrorContext) -> Dict[str, Any]:
        """处理超时错误"""
        return {
            'action': 'retry',
            'delay': 5,
            'adjust_timeout': True,
            'change_proxy': error_context.retry_count > 2,
            'message': '增加超时时间并重试'
        }
    
    def _handle_timeout_error_aggressive(self, error_context: ErrorContext) -> Dict[str, Any]:
        """激进处理超时错误"""
        return {
            'action': 'retry',
            'delay': 10,
            'adjust_timeout': True,
            'timeout_multiplier': 2.0,
            'change_proxy': True,
            'rotate_user_agent': True,
            'message': '激进策略：大幅增加超时时间并更换代理'
        }
    
    def _handle_connection_error(self, error_context: ErrorContext) -> Dict[str, Any]:
        """处理连接错误"""
        return {
            'action': 'retry',
            'delay': 3,
            'change_proxy': True,
            'verify_ssl': False if error_context.retry_count > 1 else None,
            'message': '更换代理并重试'
        }
    
    def _handle_connection_error_aggressive(self, error_context: ErrorContext) -> Dict[str, Any]:
        """激进处理连接错误"""
        return {
            'action': 'retry',
            'delay': 8,
            'change_proxy': True,
            'rotate_user_agent': True,
            'verify_ssl': False,
            'use_tor_proxy': True,
            'message': '激进策略：使用Tor代理并禁用SSL验证'
        }
    
    def _handle_rate_limit_error(self, error_context: ErrorContext) -> Dict[str, Any]:
        """处理速率限制错误"""
        return {
            'action': 'wait_and_retry',
            'delay': 60,  # 等待1分钟
            'change_proxy': True,
            'reduce_request_rate': True,
            'message': '检测到速率限制，等待后重试'
        }
    
    def _handle_server_error(self, error_context: ErrorContext) -> Dict[str, Any]:
        """处理服务器错误"""
        return {
            'action': 'retry',
            'delay': 10,
            'change_proxy': error_context.retry_count > 1,
            'message': '服务器错误，稍后重试'
        }
    
    def _handle_client_error(self, error_context: ErrorContext) -> Dict[str, Any]:
        """处理客户端错误"""
        if error_context.response_code == 404:
            return {
                'action': 'skip',
                'message': '页面不存在，跳过'
            }
        elif error_context.response_code == 403:
            return {
                'action': 'retry',
                'delay': 5,
                'change_proxy': True,
                'rotate_user_agent': True,
                'message': '访问被拒绝，更换身份重试'
            }
        else:
            return {
                'action': 'skip',
                'message': '客户端错误，跳过'
            }
    
    def _handle_anti_crawler_error(self, error_context: ErrorContext) -> Dict[str, Any]:
        """处理反爬虫错误"""
        return {
            'action': 'retry',
            'delay': 15,
            'change_proxy': True,
            'rotate_user_agent': True,
            'use_headless_browser': True,
            'message': '检测到反爬虫，使用无头浏览器重试'
        }
    
    def _handle_anti_crawler_error_aggressive(self, error_context: ErrorContext) -> Dict[str, Any]:
        """激进处理反爬虫错误"""
        return {
            'action': 'retry',
            'delay': 30,
            'change_proxy': True,
            'rotate_user_agent': True,
            'use_headless_browser': True,
            'simulate_human_behavior': True,
            'message': '激进策略：完全模拟人类行为重试'
        }
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误统计信息"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [
            error for error in self.error_history 
            if error.timestamp >= cutoff_time
        ]
        
        stats = {
            'total_errors': len(recent_errors),
            'error_types': {},
            'domains': {},
            'severity_distribution': {},
            'recovery_success_rate': self._calculate_recovery_success_rate(recent_errors)
        }
        
        for error in recent_errors:
            # 按错误类型统计
            stats['error_types'][error.error_type] = stats['error_types'].get(error.error_type, 0) + 1
            
            # 按域名统计
            domain = self._extract_domain(error.url)
            stats['domains'][domain] = stats['domains'].get(domain, 0) + 1
            
            # 按严重程度统计
            severity = error.severity.value
            stats['severity_distribution'][severity] = stats['severity_distribution'].get(severity, 0) + 1
        
        return stats
    
    def _calculate_recovery_success_rate(self, errors: List[ErrorContext]) -> float:
        """计算恢复成功率"""
        if not errors:
            return 0.0
        
        # 简单估算：假设重试次数少的错误恢复成功率高
        successful_recoveries = sum(1 for error in errors if error.retry_count <= 2)
        return successful_recoveries / len(errors)
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        recommendations = []
        
        # 分析错误模式，生成建议
        for error_type, domains in self.error_patterns.items():
            for domain, pattern in domains.items():
                if pattern['count'] > 5:  # 频繁错误
                    rec = {
                        'domain': domain,
                        'error_type': error_type,
                        'frequency': pattern['count'],
                        'recommendation': self._generate_recommendation(error_type, pattern),
                        'priority': self._calculate_priority(pattern)
                    }
                    recommendations.append(rec)
        
        # 按优先级排序
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        return recommendations
    
    def _generate_recommendation(self, error_type: str, pattern: Dict) -> str:
        """生成优化建议"""
        recommendations = {
            'timeout': '增加请求超时时间，优化网络连接',
            'connection': '更换代理服务器，检查网络稳定性',
            'rate_limit': '降低请求频率，实现智能限速',
            'anti_crawler': '增强反反爬虫能力，使用更真实的用户行为模拟',
            'server_error': '实现服务器错误自动恢复机制',
            'client_error': '优化请求参数，处理认证问题'
        }
        
        base_recommendation = recommendations.get(error_type, '优化错误处理逻辑')
        
        # 根据错误频率调整建议
        if pattern['count'] > 20:
            base_recommendation += '（高优先级）'
        elif pattern['count'] > 10:
            base_recommendation += '（中优先级）'
        
        return base_recommendation
    
    def _calculate_priority(self, pattern: Dict) -> int:
        """计算优化优先级"""
        priority = pattern['count']  # 错误频率
        
        # 考虑严重程度
        severity_dist = pattern.get('severity_distribution', {})
        if 'critical' in severity_dist:
            priority += severity_dist['critical'] * 10
        if 'high' in severity_dist:
            priority += severity_dist['high'] * 5
        
        return priority
    
    def export_error_report(self, filename: str) -> bool:
        """导出错误报告"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'statistics': self.get_error_statistics(),
                'recommendations': self.get_optimization_recommendations(),
                'recent_errors': [
                    {
                        'url': error.url,
                        'error_type': error.error_type,
                        'timestamp': error.timestamp.isoformat(),
                        'severity': error.severity.value
                    }
                    for error in self.error_history[-50:]  # 最近50个错误
                ]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"错误报告已导出到: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出错误报告失败: {e}")
            return False


def create_error_context(
    url: str,
    error_type: str,
    error_message: str,
    retry_count: int = 0,
    response_code: Optional[int] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
) -> ErrorContext:
    """创建错误上下文"""
    return ErrorContext(
        url=url,
        method="GET",  # 可以根据实际情况调整
        timestamp=datetime.now(),
        error_type=error_type,
        error_message=error_message,
        severity=severity,
        retry_count=retry_count,
        response_code=response_code
    )


# 使用示例
if __name__ == "__main__":
    # 创建错误处理器
    handler = AdvancedErrorHandler()
    
    # 模拟记录一些错误
    errors = [
        create_error_context(
            "https://example.com/page1",
            "timeout",
            "请求超时",
            severity=ErrorSeverity.MEDIUM
        ),
        create_error_context(
            "https://example.com/page2", 
            "connection",
            "连接被拒绝",
            severity=ErrorSeverity.HIGH
        )
    ]
    
    for error in errors:
        handler.record_error(error)
    
    # 获取统计信息
    stats = handler.get_error_statistics()
    print("错误统计:", json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 获取优化建议
    recommendations = handler.get_optimization_recommendations()
    print("优化建议:", json.dumps(recommendations, indent=2, ensure_ascii=False))
    
    # 导出报告
    handler.export_error_report("error_report.json")