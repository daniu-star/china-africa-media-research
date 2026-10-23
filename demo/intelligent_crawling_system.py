#!/usr/bin/env python3
"""
智能爬虫系统 - 整合自适应学习引擎和现有策略模块
实现端到端的智能爬虫决策和优化
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# 导入现有模块
from intelligent_crawling_strategy import IntelligentCrawlingStrategy
from smart_retry_handler import SmartRetryHandler
from proxy_geo_optimizer import SmartProxyManager
from adaptive_learning_engine import AdaptiveLearningEngine
from data_storage_manager import DataStorageManager

logger = logging.getLogger(__name__)

class IntelligentCrawlingSystem:
    """智能爬虫系统 - 整合所有智能模块"""
    
    def __init__(self, config_file: str = "adaptive_learning_config.json", 
                 storage_config: Dict[str, Any] = None):
        # 初始化各个智能模块
        self.strategy_manager = IntelligentCrawlingStrategy()
        self.retry_handler = SmartRetryHandler()
        self.proxy_manager = SmartProxyManager()
        self.learning_engine = AdaptiveLearningEngine(config_file)
        
        # 初始化数据存储管理器
        if storage_config is None:
            storage_config = {
                'base_dir': 'data',
                'backup_dir': 'backup'
            }
        self.storage_manager = DataStorageManager(
            base_dir=storage_config.get('base_dir', 'data'),
            backup_dir=storage_config.get('backup_dir', 'backup')
        )
        
        # 系统状态
        self.system_status = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_latency': 0.0,
            'last_optimization': None,
            'current_strategy': 'balanced',
            'performance_trend': 'stable'
        }
        
        # 实时监控数据
        self.realtime_metrics = {
            'requests_per_minute': 0,
            'success_rate_5m': 0.0,
            'average_latency_5m': 0.0,
            'error_distribution': {},
            'strategy_effectiveness': {}
        }
        
        # 性能历史记录
        self.performance_history = []
        
        # 加载保存的系统状态（如果存在）
        self._load_system_state()
        
        logger.info("智能爬虫系统初始化完成")
    
    def _load_system_state(self):
        """加载保存的系统状态"""
        try:
            # 尝试加载系统状态
            state_data = self.storage_manager.load_data('system_state.json')
            if state_data:
                self.system_status = state_data.get('system_status', self.system_status)
                self.realtime_metrics = state_data.get('realtime_metrics', self.realtime_metrics)
                self.performance_history = state_data.get('performance_history', self.performance_history)
                logger.info("系统状态加载成功")
            else:
                logger.info("未找到保存的系统状态，使用默认状态")
        except Exception as e:
            logger.warning(f"加载系统状态失败: {e}，使用默认状态")
    
    def _save_system_state(self):
        """保存系统状态"""
        try:
            state_data = {
                'system_status': self.system_status,
                'realtime_metrics': self.realtime_metrics,
                'performance_history': self.performance_history,
                'timestamp': datetime.now().isoformat()
            }
            
            self.storage_manager.save_data(state_data, 'system_state.json')
            logger.debug("系统状态保存成功")
        except Exception as e:
            logger.error(f"保存系统状态失败: {e}")
    
    def _save_crawl_result(self, url: str, strategy: str, result: Dict, proxy_info: Dict):
        """保存爬虫结果"""
        try:
            # 创建爬虫结果记录
            crawl_record = {
                'url': url,
                'strategy': strategy,
                'success': result['success'],
                'status_code': result.get('status_code', 0),
                'latency': result['latency'],
                'proxy_info': proxy_info,
                'timestamp': datetime.now().isoformat(),
                'content_length': len(result.get('content', '')) if result.get('content') else 0
            }
            
            # 生成文件名（使用URL的哈希值）
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"crawl_results/crawl_{url_hash}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # 保存爬虫结果
            self.storage_manager.save_data(crawl_record, filename)
            logger.debug(f"爬虫结果保存成功: {filename}")
            
        except Exception as e:
            logger.error(f"保存爬虫结果失败: {e}")
    
    def load_crawl_history(self, limit: int = 100) -> List[Dict]:
        """加载爬虫历史记录"""
        try:
            # 获取爬虫结果目录下的所有文件
            crawl_files = self.storage_manager.list_files('crawl_results/')
            
            if not crawl_files:
                logger.info("未找到爬虫历史记录")
                return []
            
            # 按时间排序（最新的在前）
            crawl_files.sort(reverse=True)
            
            # 加载指定数量的记录
            history = []
            for filename in crawl_files[:limit]:
                try:
                    record = self.storage_manager.load_data(filename)
                    if record:
                        history.append(record)
                except Exception as e:
                    logger.warning(f"加载爬虫记录失败 {filename}: {e}")
            
            logger.info(f"成功加载 {len(history)} 条爬虫历史记录")
            return history
            
        except Exception as e:
            logger.error(f"加载爬虫历史失败: {e}")
            return []
    
    def crawl_url(self, url: str, use_learning: bool = True, 
                  custom_strategy: str = None) -> Dict[str, Any]:
        """智能爬取URL"""
        start_time = time.time()
        
        # 智能重试机制
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # 1. 选择最优策略
                if use_learning and custom_strategy is None:
                    strategy_decision = self._select_optimal_strategy(url)
                    strategy = strategy_decision['strategy']
                    strategy_reason = strategy_decision['reason']
                else:
                    strategy = custom_strategy or 'balanced'
                    strategy_reason = '自定义策略'
                
                # 2. 选择最优代理
                proxy_decision = self.proxy_manager.select_optimal_proxy(url)
                proxy_info = proxy_decision
                
                # 3. 获取爬取参数
                crawl_params = self.strategy_manager.select_crawling_strategy(url)
                
                # 4. 执行爬取（模拟）
                result = self._execute_crawl(url, crawl_params, proxy_info, strategy)
                
                # 5. 记录性能数据
                self._record_performance(url, strategy, result, proxy_info, start_time)
                
                # 6. 更新学习引擎
                if use_learning:
                    self.learning_engine.record_performance(
                        url, strategy, result['success'], 
                        result['latency'], proxy_info
                    )
                
                # 7. 更新系统状态
                self._update_system_status(result)
                
                # 8. 保存系统状态
                self._save_system_state()
                
                # 9. 保存爬虫结果
                self._save_crawl_result(url, strategy, result, proxy_info)
                
                # 如果成功或达到最大尝试次数，返回结果
                if result['success'] or attempt == max_attempts - 1:
                    return {
                        'success': True,
                        'url': url,
                        'strategy_used': strategy,
                        'strategy_reason': strategy_reason,
                        'proxy_used': proxy_info,
                        'result': result,
                        'performance_data': {
                            'latency': result['latency'],
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                
                # 失败时进行智能调整
                if not result['success']:
                    # 根据错误类型调整策略
                    self._handle_failed_attempt(result, strategy, attempt)
                    
                    # 智能延迟
                    delay = self._calculate_retry_delay(attempt, result.get('status_code'))
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"爬取尝试 {attempt + 1} 失败: {url}, 错误: {e}")
                
                # 记录失败
                self._record_failure(url, str(e))
                
                if attempt == max_attempts - 1:
                    return {
                        'success': False,
                        'url': url,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                
                # 异常时延迟重试
                time.sleep(self._calculate_retry_delay(attempt, None))
        
        return {
            'success': False,
            'url': url,
            'error': '所有尝试均失败',
            'timestamp': datetime.now().isoformat()
        }
    
    def _select_optimal_strategy(self, url: str) -> Dict[str, Any]:
        """选择最优策略"""
        # 获取当前策略
        current_strategy = self.system_status['current_strategy']
        
        # 获取代理信息（用于学习引擎）
        proxy_decision = self.proxy_manager.select_optimal_proxy(url)
        # 直接使用proxy_decision，而不是proxy_decision['proxy_info']
        proxy_info = proxy_decision
        
        # 使用学习引擎优化策略
        optimization = self.learning_engine.optimize_strategy(
            url, current_strategy, proxy_info
        )
        
        # 检查置信度
        if optimization['prediction']['confidence'] > 0.7:
            recommended_strategy = optimization['recommended_strategy']
            reason = f"学习引擎推荐 ({optimization['reason']})"
        else:
            # 置信度低时使用基础策略选择
            website_profile = self.strategy_manager.get_website_profile(url)
            recommended_strategy = website_profile['preferred_strategy']
            reason = "基础策略选择 (低置信度)"
        
        return {
            'strategy': recommended_strategy,
            'reason': reason,
            'optimization_data': optimization
        }
    
    def _execute_crawl(self, url: str, crawl_params: Dict, proxy_info: Dict, strategy: str = 'balanced') -> Dict[str, Any]:
        """执行爬取（模拟实现）"""
        # 模拟爬取过程
        import random
        import time
        
        # 模拟网络延迟
        base_delay = crawl_params.get('timeout', 30) / 1000  # 转换为秒
        additional_delay = random.uniform(0.1, 1.0)
        time.sleep(base_delay + additional_delay)
        
        # 模拟成功率（基于策略和代理质量）
        strategy_success_rate = {
            'aggressive': 0.6,
            'balanced': 0.8,
            'conservative': 0.9,
            'ultra_conservative': 0.95
        }
        
        # 使用传入的策略名称，而不是从crawl_params中获取
        base_success_rate = strategy_success_rate.get(strategy, 0.8)
        
        # 代理质量影响（处理proxy_info可能缺少score字段的情况）
        proxy_quality = 0.8  # 默认质量
        if proxy_info and 'score' in proxy_info:
            proxy_quality = proxy_info.get('score', 0.8)
        elif proxy_info and proxy_info.get('strategy') == 'direct':
            # 直接连接时使用较低的成功率
            proxy_quality = 0.6
        
        success_rate = base_success_rate * proxy_quality
        
        # 随机决定成功/失败
        success = random.random() < success_rate
        
        # 计算延迟
        latency = (base_delay + additional_delay) * 1000  # 转换为毫秒
        
        # 模拟响应内容
        if success:
            content = f"模拟成功爬取 {url} 的内容"
            status_code = 200
        else:
            # 模拟不同类型的错误
            error_types = [
                ("连接超时", 408),
                ("访问被拒绝", 403), 
                ("页面不存在", 404),
                ("服务器错误", 500)
            ]
            error_msg, status_code = random.choice(error_types)
            content = f"错误: {error_msg}"
        
        return {
            'success': success,
            'status_code': status_code,
            'content': content,
            'latency': latency,
            'strategy_used': strategy,
            'proxy_used': proxy_info
        }
    
    def _record_performance(self, url: str, strategy: str, result: Dict, 
                           proxy_info: Dict, start_time: float):
        """记录性能数据"""
        latency = result['latency']
        success = result['success']
        
        # 更新系统统计
        self.system_status['total_requests'] += 1
        
        if success:
            self.system_status['successful_requests'] += 1
        else:
            self.system_status['failed_requests'] += 1
        
        # 更新平均延迟
        total_reqs = self.system_status['total_requests']
        current_avg = self.system_status['average_latency']
        self.system_status['average_latency'] = (
            (current_avg * (total_reqs - 1) + latency) / total_reqs
        )
        
        # 记录性能历史
        performance_record = {
            'timestamp': datetime.now(),
            'url': url,
            'strategy': strategy,
            'success': success,
            'latency': latency,
            'proxy_info': proxy_info
        }
        
        self.performance_history.append(performance_record)
        
        # 限制历史记录大小
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
        
        # 更新策略有效性
        self._update_strategy_effectiveness(strategy, success)
    
    def _record_failure(self, url: str, error: str):
        """记录失败"""
        self.system_status['total_requests'] += 1
        self.system_status['failed_requests'] += 1
        
        # 记录错误分布
        error_type = error.split(':')[0] if ':' in error else error
        self.realtime_metrics['error_distribution'][error_type] = \
            self.realtime_metrics['error_distribution'].get(error_type, 0) + 1
    
    def _update_strategy_effectiveness(self, strategy: str, success: bool):
        """更新策略有效性统计"""
        if strategy not in self.realtime_metrics['strategy_effectiveness']:
            self.realtime_metrics['strategy_effectiveness'][strategy] = {
                'total': 0,
                'successful': 0,
                'success_rate': 0.0
            }
        
        stats = self.realtime_metrics['strategy_effectiveness'][strategy]
        stats['total'] += 1
        
        if success:
            stats['successful'] += 1
        
        stats['success_rate'] = stats['successful'] / stats['total'] if stats['total'] > 0 else 0.0
    
    def _handle_failed_attempt(self, result: Dict, strategy: str, attempt: int):
        """处理失败的爬取尝试"""
        status_code = result.get('status_code')
        
        # 根据状态码调整策略
        if status_code == 403:
            # 403错误：切换代理和指纹
            logger.info(f"尝试 {attempt + 1} 遇到403错误，切换代理和指纹")
            self.proxy_manager.rotate_proxy()
            # 触发深度指纹变更
            self.strategy_manager.enable_deep_fingerprint = True
            
        elif status_code == 429:
            # 429错误：增加延迟和减少并发
            logger.info(f"尝试 {attempt + 1} 遇到429错误，增加延迟")
            self.strategy_manager.increase_delay_multiplier(1.5)
            
        elif status_code == 500:
            # 服务器错误：短暂等待后重试
            logger.info(f"尝试 {attempt + 1} 遇到500错误，短暂等待")
        
        # 记录失败模式
        self.learning_engine.record_failure_pattern(strategy, status_code, attempt)
    
    def _calculate_retry_delay(self, attempt: int, status_code: int = None) -> float:
        """计算重试延迟"""
        import random
        base_delay = 2.0  # 基础延迟2秒
        
        # 基于尝试次数的指数退避
        delay = base_delay * (2 ** attempt)
        
        # 基于状态码的调整
        if status_code == 429:
            # 429错误需要更长延迟
            delay *= 3.0
        elif status_code == 403:
            # 403错误中等延迟
            delay *= 1.5
        elif status_code == 500:
            # 服务器错误较短延迟
            delay *= 0.5
        
        # 随机化延迟以避免模式检测
        jitter = random.uniform(0.8, 1.2)
        delay *= jitter
        
        # 最大延迟限制
        max_delay = 60.0  # 最大60秒
        return min(delay, max_delay)
    
    def _update_system_status(self, result: Dict):
        """更新系统状态"""
        # 更新性能趋势
        recent_success_rate = self._calculate_recent_success_rate()
        
        if recent_success_rate > 0.9:
            self.system_status['performance_trend'] = 'excellent'
        elif recent_success_rate > 0.7:
            self.system_status['performance_trend'] = 'good'
        elif recent_success_rate > 0.5:
            self.system_status['performance_trend'] = 'fair'
        else:
            self.system_status['performance_trend'] = 'poor'
        
        # 更新实时指标
        self._update_realtime_metrics()
    
    def _calculate_recent_success_rate(self, minutes: int = 5) -> float:
        """计算最近成功率"""
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        
        recent_records = [
            record for record in self.performance_history
            if record['timestamp'].timestamp() >= cutoff_time
        ]
        
        if not recent_records:
            return 0.8  # 默认值
        
        success_count = sum(1 for record in recent_records if record['success'])
        return success_count / len(recent_records)
    
    def _update_realtime_metrics(self):
        """更新实时指标"""
        # 计算每分钟请求数（简化版）
        current_minute = datetime.now().minute
        
        if not hasattr(self, '_last_minute_count'):
            self._last_minute_count = {'minute': current_minute, 'count': 0}
        
        if current_minute == self._last_minute_count['minute']:
            self._last_minute_count['count'] += 1
        else:
            # 新的一分钟，更新指标
            self.realtime_metrics['requests_per_minute'] = self._last_minute_count['count']
            self._last_minute_count = {'minute': current_minute, 'count': 1}
        
        # 更新5分钟成功率
        self.realtime_metrics['success_rate_5m'] = self._calculate_recent_success_rate(5)
        
        # 更新5分钟平均延迟
        self.realtime_metrics['average_latency_5m'] = self._calculate_recent_average_latency(5)
    
    def _calculate_recent_average_latency(self, minutes: int) -> float:
        """计算最近平均延迟"""
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        
        recent_records = [
            record for record in self.performance_history
            if record['timestamp'].timestamp() >= cutoff_time and record['success']
        ]
        
        if not recent_records:
            return 300.0  # 默认值
        
        return sum(record['latency'] for record in recent_records) / len(recent_records)
    
    def get_system_report(self) -> Dict[str, Any]:
        """获取系统报告"""
        # 获取各个模块的报告
        strategy_report = self.strategy_manager.get_performance_report()
        retry_report = self.retry_handler.get_error_report()
        proxy_report = self.proxy_manager.get_performance_report()
        learning_report = self.learning_engine.get_learning_report()
        
        # 计算总体指标
        total_requests = self.system_status['total_requests']
        success_rate = (
            self.system_status['successful_requests'] / total_requests 
            if total_requests > 0 else 0.0
        )
        
        return {
            'system_overview': {
                'total_requests': total_requests,
                'successful_requests': self.system_status['successful_requests'],
                'failed_requests': self.system_status['failed_requests'],
                'overall_success_rate': round(success_rate, 3),
                'average_latency': round(self.system_status['average_latency'], 2),
                'performance_trend': self.system_status['performance_trend'],
                'current_strategy': self.system_status['current_strategy']
            },
            'realtime_metrics': self.realtime_metrics,
            'module_reports': {
                'strategy_manager': strategy_report,
                'retry_handler': retry_report,
                'proxy_manager': proxy_report,
                'learning_engine': learning_report
            },
            'optimization_recommendations': self._generate_optimization_recommendations(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_optimization_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 基于成功率
        success_rate = self.system_status['successful_requests'] / self.system_status['total_requests']
        
        if success_rate < 0.6:
            recommendations.append("成功率较低，建议切换到更保守的策略")
        elif success_rate > 0.9:
            recommendations.append("成功率很高，可以尝试更激进的策略以提高效率")
        
        # 基于延迟
        avg_latency = self.system_status['average_latency']
        if avg_latency > 500:
            recommendations.append("平均延迟较高，建议优化代理选择和网络配置")
        
        # 基于策略有效性
        strategy_effectiveness = self.realtime_metrics['strategy_effectiveness']
        if strategy_effectiveness:
            best_strategy = max(strategy_effectiveness.items(), 
                              key=lambda x: x[1]['success_rate'])
            current_strategy = self.system_status['current_strategy']
            
            if best_strategy[0] != current_strategy:
                recommendations.append(
                    f"检测到更有效的策略: {best_strategy[0]} "
                    f"(成功率: {best_strategy[1]['success_rate']:.1%})"
                )
        
        # 基于学习引擎
        learning_report = self.learning_engine.get_learning_report()
        if learning_report.get('status') == 'success':
            if learning_report['summary']['model_training_count'] == 0:
                recommendations.append("学习引擎尚未训练，建议收集更多数据后启用学习功能")
        
        return recommendations
    
    def optimize_system(self) -> Dict[str, Any]:
        """优化系统配置"""
        # 分析当前性能
        system_report = self.get_system_report()
        
        # 基于性能调整策略
        success_rate = system_report['system_overview']['overall_success_rate']
        avg_latency = system_report['system_overview']['average_latency']
        
        # 策略调整逻辑
        if success_rate < 0.6:
            new_strategy = 'conservative'
            reason = "低成功率，切换到保守策略"
        elif success_rate > 0.9 and avg_latency < 300:
            new_strategy = 'aggressive'
            reason = "高性能状态，切换到激进策略"
        else:
            new_strategy = 'balanced'
            reason = "保持平衡策略"
        
        # 更新系统策略
        self.system_status['current_strategy'] = new_strategy
        self.system_status['last_optimization'] = datetime.now()
        
        return {
            'optimization_applied': True,
            'new_strategy': new_strategy,
            'reason': reason,
            'previous_strategy': system_report['system_overview']['current_strategy'],
            'performance_analysis': {
                'success_rate': success_rate,
                'average_latency': avg_latency
            }
        }

# 使用示例
def test_intelligent_crawling_system():
    """测试智能爬虫系统"""
    system = IntelligentCrawlingSystem()
    
    # 测试URL列表
    test_urls = [
        "https://www.news24.com",
        "https://www.nation.co.ke",
        "https://www.punchng.com",
        "https://www.iol.co.za",
        "https://www.standardmedia.co.ke"
    ]
    
    print("开始智能爬虫系统测试...")
    
    # 执行多次爬取
    for i in range(20):
        url = test_urls[i % len(test_urls)]
        
        print(f"\n第 {i+1} 次爬取: {url}")
        
        result = system.crawl_url(url, use_learning=True)
        
        if result['success']:
            print(f"  成功 - 策略: {result['strategy_used']}, "
                  f"延迟: {result['performance_data']['latency']:.2f}ms")
        else:
            print(f"  失败 - 错误: {result['error']}")
    
    print("\n" + "="*50)
    print("系统测试完成，生成报告...")
    
    # 获取系统报告
    report = system.get_system_report()
    
    print("\n系统概览:")
    overview = report['system_overview']
    print(f"  总请求数: {overview['total_requests']}")
    print(f"  成功率: {overview['overall_success_rate']:.1%}")
    print(f"  平均延迟: {overview['average_latency']:.2f}ms")
    print(f"  性能趋势: {overview['performance_trend']}")
    
    print("\n优化建议:")
    for i, recommendation in enumerate(report['optimization_recommendations'], 1):
        print(f"  {i}. {recommendation}")
    
    # 执行系统优化
    optimization = system.optimize_system()
    print(f"\n系统优化结果:")
    print(f"  新策略: {optimization['new_strategy']}")
    print(f"  原因: {optimization['reason']}")

if __name__ == "__main__":
    test_intelligent_crawling_system()