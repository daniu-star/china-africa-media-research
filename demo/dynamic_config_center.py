#!/usr/bin/env python3
"""
动态配置中心 - 实现爬虫配置的实时管理和优化
支持配置热更新、性能驱动的自适应调整和配置版本管理
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

class DynamicConfigCenter:
    """动态配置中心"""
    
    def __init__(self, config_file: str = "adaptive_learning_config.json"):
        self.config_file = config_file
        self.base_config = self._load_base_config()
        
        # 动态配置状态
        self.dynamic_config = self._initialize_dynamic_config()
        self.config_history = []
        self.last_config_update = datetime.now()
        
        # 性能监控
        self.performance_data = {
            'requests': [],
            'errors': [],
            'latencies': [],
            'success_rates': []
        }
        
        # 配置监听器
        self.config_listeners = []
        
        # 自动优化线程
        self.optimization_thread = None
        self.optimization_running = False
        
        logger.info("动态配置中心初始化完成")
    
    def _load_base_config(self) -> Dict[str, Any]:
        """加载基础配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件 {self.config_file} 不存在，使用默认配置")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "learning_config": {
                "learning_window_size": 1000,
                "decay_factor": 0.95,
                "min_training_samples": 100,
                "retraining_interval": 3600
            },
            "feature_config": {
                "time_features": ["hour", "day_of_week", "is_weekend"],
                "performance_features": ["success_rate", "average_latency", "error_rate"],
                "website_features": ["anti_crawler_level", "response_time", "stability"],
                "proxy_features": ["latency", "success_rate", "stability", "geographic_match"],
                "strategy_features": ["strategy_type", "timeout_multiplier", "delay_multiplier"]
            },
            "african_websites": {
                "south_africa": {
                    "news24.com": {
                        "anti_crawler_level": 3,
                        "response_time": 2000,
                        "stability": 0.85
                    },
                    "iol.co.za": {
                        "anti_crawler_level": 2,
                        "response_time": 1500,
                        "stability": 0.90
                    }
                },
                "kenya": {
                    "nation.co.ke": {
                        "anti_crawler_level": 2,
                        "response_time": 1800,
                        "stability": 0.88
                    },
                    "standardmedia.co.ke": {
                        "anti_crawler_level": 1,
                        "response_time": 1200,
                        "stability": 0.92
                    }
                },
                "nigeria": {
                    "punchng.com": {
                        "anti_crawler_level": 3,
                        "response_time": 2200,
                        "stability": 0.82
                    },
                    "vanguardngr.com": {
                        "anti_crawler_level": 2,
                        "response_time": 1600,
                        "stability": 0.89
                    }
                }
            },
            "proxy_optimization_rules": {
                "latency_thresholds": {
                    "excellent": 500,
                    "good": 1000,
                    "fair": 2000,
                    "poor": 3000
                },
                "success_rate_thresholds": {
                    "excellent": 0.95,
                    "good": 0.85,
                    "fair": 0.70,
                    "poor": 0.50
                }
            },
            "strategy_optimization_rules": {
                "aggressive": {
                    "min_success_rate": 0.80,
                    "max_latency": 1000,
                    "applicable_websites": ["low_anti_crawler", "high_stability"]
                },
                "balanced": {
                    "min_success_rate": 0.70,
                    "max_latency": 2000,
                    "applicable_websites": ["medium_anti_crawler", "medium_stability"]
                },
                "conservative": {
                    "min_success_rate": 0.60,
                    "max_latency": 3000,
                    "applicable_websites": ["high_anti_crawler", "low_stability"]
                },
                "ultra_conservative": {
                    "min_success_rate": 0.50,
                    "max_latency": 5000,
                    "applicable_websites": ["very_high_anti_crawler", "very_low_stability"]
                }
            }
        }
    
    def _initialize_dynamic_config(self) -> Dict[str, Any]:
        """初始化动态配置"""
        return {
            'current_optimizations': {},
            'performance_thresholds': {
                'success_rate': {
                    'warning': 0.70,
                    'critical': 0.50,
                    'excellent': 0.90
                },
                'latency': {
                    'warning': 2000,
                    'critical': 5000,
                    'excellent': 500
                },
                'error_rate': {
                    'warning': 0.20,
                    'critical': 0.40,
                    'excellent': 0.05
                }
            },
            'adaptive_parameters': {
                'timeout_multiplier': 1.0,
                'delay_multiplier': 1.0,
                'retry_multiplier': 1.0,
                'proxy_quality_threshold': 0.7
            },
            'website_specific_configs': {},
            'strategy_effectiveness': {},
            'last_optimization_time': datetime.now().isoformat(),
            'config_version': '1.0.0'
        }
    
    def get_config(self, config_type: str, key: Optional[str] = None) -> Any:
        """获取配置"""
        if config_type == 'base':
            config_source = self.base_config
        elif config_type == 'dynamic':
            config_source = self.dynamic_config
        else:
            raise ValueError(f"未知配置类型: {config_type}")
        
        if key:
            return config_source.get(key)
        else:
            return config_source
    
    def update_config(self, config_type: str, updates: Dict[str, Any], 
                     reason: str = "手动更新") -> bool:
        """更新配置"""
        try:
            if config_type == 'base':
                config_source = self.base_config
            elif config_type == 'dynamic':
                config_source = self.dynamic_config
            else:
                raise ValueError(f"未知配置类型: {config_type}")
            
            # 记录配置变更历史
            change_record = {
                'timestamp': datetime.now().isoformat(),
                'config_type': config_type,
                'changes': updates.copy(),
                'reason': reason,
                'previous_state': self._get_config_snapshot(config_type)
            }
            
            # 应用更新
            self._deep_update(config_source, updates)
            
            # 更新动态配置的时间戳
            if config_type == 'dynamic':
                config_source['last_optimization_time'] = datetime.now().isoformat()
            
            # 保存变更历史
            self.config_history.append(change_record)
            
            # 限制历史记录大小
            if len(self.config_history) > 100:
                self.config_history = self.config_history[-100:]
            
            # 通知监听器
            self._notify_listeners(config_type, updates, reason)
            
            logger.info(f"配置更新成功: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"配置更新失败: {e}")
            return False
    
    def _deep_update(self, target: Dict, updates: Dict):
        """深度更新字典"""
        for key, value in updates.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def _get_config_snapshot(self, config_type: str) -> Dict:
        """获取配置快照"""
        if config_type == 'base':
            return self.base_config.copy()
        else:
            return self.dynamic_config.copy()
    
    def _notify_listeners(self, config_type: str, changes: Dict, reason: str):
        """通知配置监听器"""
        for listener in self.config_listeners:
            try:
                listener(config_type, changes, reason)
            except Exception as e:
                logger.error(f"配置监听器通知失败: {e}")
    
    def add_config_listener(self, listener):
        """添加配置监听器"""
        self.config_listeners.append(listener)
    
    def record_performance(self, performance_data: Dict[str, Any]):
        """记录性能数据"""
        timestamp = datetime.now()
        
        # 记录请求数据
        if 'success' in performance_data:
            self.performance_data['requests'].append({
                'timestamp': timestamp,
                'success': performance_data['success'],
                'latency': performance_data.get('latency', 0),
                'url': performance_data.get('url', ''),
                'strategy': performance_data.get('strategy', '')
            })
        
        # 记录错误数据
        if 'error' in performance_data:
            self.performance_data['errors'].append({
                'timestamp': timestamp,
                'error': performance_data['error'],
                'url': performance_data.get('url', ''),
                'strategy': performance_data.get('strategy', '')
            })
        
        # 记录延迟数据
        if 'latency' in performance_data and performance_data['success']:
            self.performance_data['latencies'].append({
                'timestamp': timestamp,
                'latency': performance_data['latency'],
                'url': performance_data.get('url', '')
            })
        
        # 清理旧数据（保留最近24小时）
        self._cleanup_old_data()
        
        # 检查是否需要自动优化
        self._check_auto_optimization()
    
    def _cleanup_old_data(self):
        """清理旧数据"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for data_type in ['requests', 'errors', 'latencies']:
            self.performance_data[data_type] = [
                record for record in self.performance_data[data_type]
                if record['timestamp'] > cutoff_time
            ]
    
    def _check_auto_optimization(self):
        """检查是否需要自动优化"""
        # 检查数据量是否足够
        if len(self.performance_data['requests']) < 50:
            return
        
        # 计算关键指标
        recent_requests = self.performance_data['requests'][-100:]  # 最近100个请求
        
        if not recent_requests:
            return
        
        success_count = sum(1 for req in recent_requests if req['success'])
        success_rate = success_count / len(recent_requests)
        
        avg_latency = sum(req['latency'] for req in recent_requests if req['success']) / success_count
        
        # 检查是否超过阈值
        thresholds = self.dynamic_config['performance_thresholds']
        
        needs_optimization = False
        optimization_reason = ""
        
        if success_rate < thresholds['success_rate']['critical']:
            needs_optimization = True
            optimization_reason = f"成功率过低: {success_rate:.1%}"
        elif avg_latency > thresholds['latency']['critical']:
            needs_optimization = True
            optimization_reason = f"延迟过高: {avg_latency:.0f}ms"
        elif success_rate < thresholds['success_rate']['warning']:
            needs_optimization = True
            optimization_reason = f"成功率警告: {success_rate:.1%}"
        
        if needs_optimization:
            self._perform_auto_optimization(success_rate, avg_latency, optimization_reason)
    
    def _perform_auto_optimization(self, success_rate: float, avg_latency: float, reason: str):
        """执行自动优化"""
        logger.info(f"执行自动优化: {reason}")
        
        # 基于性能指标调整参数
        updates = {}
        
        # 调整超时倍数
        if success_rate < 0.6:
            updates['timeout_multiplier'] = 1.5
        elif success_rate > 0.9:
            updates['timeout_multiplier'] = 0.8
        else:
            updates['timeout_multiplier'] = 1.0
        
        # 调整延迟倍数
        if avg_latency > 2000:
            updates['delay_multiplier'] = 1.3
        elif avg_latency < 500:
            updates['delay_multiplier'] = 0.7
        else:
            updates['delay_multiplier'] = 1.0
        
        # 调整重试倍数
        if success_rate < 0.7:
            updates['retry_multiplier'] = 1.2
        else:
            updates['retry_multiplier'] = 1.0
        
        # 调整代理质量阈值
        if success_rate < 0.8:
            updates['proxy_quality_threshold'] = 0.8
        else:
            updates['proxy_quality_threshold'] = 0.7
        
        # 应用更新
        if updates:
            self.update_config('dynamic', {
                'adaptive_parameters': updates,
                'current_optimizations': {
                    'reason': reason,
                    'success_rate': success_rate,
                    'avg_latency': avg_latency,
                    'applied_changes': updates
                }
            }, f"自动优化: {reason}")
    
    def start_auto_optimization(self, interval_minutes: int = 5):
        """启动自动优化线程"""
        if self.optimization_running:
            logger.warning("自动优化线程已在运行")
            return
        
        self.optimization_running = True
        self.optimization_thread = threading.Thread(
            target=self._auto_optimization_loop,
            args=(interval_minutes,),
            daemon=True
        )
        self.optimization_thread.start()
        
        logger.info(f"自动优化线程已启动，间隔: {interval_minutes} 分钟")
    
    def stop_auto_optimization(self):
        """停止自动优化线程"""
        self.optimization_running = False
        if self.optimization_thread:
            self.optimization_thread.join(timeout=5)
        
        logger.info("自动优化线程已停止")
    
    def _auto_optimization_loop(self, interval_minutes: int):
        """自动优化循环"""
        while self.optimization_running:
            try:
                # 执行定期优化检查
                self._perform_periodic_optimization()
                
                # 等待指定间隔
                time.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"自动优化循环错误: {e}")
                time.sleep(60)  # 错误后等待1分钟
    
    def _perform_periodic_optimization(self):
        """执行定期优化"""
        # 分析性能趋势
        performance_trend = self._analyze_performance_trend()
        
        if performance_trend['needs_optimization']:
            # 基于趋势进行优化
            updates = self._generate_trend_based_optimizations(performance_trend)
            
            if updates:
                self.update_config('dynamic', {
                    'adaptive_parameters': updates,
                    'current_optimizations': {
                        'reason': performance_trend['analysis'],
                        'trend_data': performance_trend,
                        'applied_changes': updates
                    }
                }, f"趋势优化: {performance_trend['analysis']}")
    
    def _analyze_performance_trend(self) -> Dict[str, Any]:
        """分析性能趋势"""
        if len(self.performance_data['requests']) < 100:
            return {
                'needs_optimization': False,
                'analysis': '数据不足，无法分析趋势'
            }
        
        # 分析最近30分钟的性能
        cutoff_time = datetime.now() - timedelta(minutes=30)
        recent_requests = [
            req for req in self.performance_data['requests']
            if req['timestamp'] > cutoff_time
        ]
        
        if len(recent_requests) < 20:
            return {
                'needs_optimization': False,
                'analysis': '近期数据不足'
            }
        
        # 计算趋势指标
        success_rates = []
        latencies = []
        
        # 按5分钟窗口分析
        for i in range(6):  # 6个5分钟窗口
            window_start = cutoff_time + timedelta(minutes=i*5)
            window_end = window_start + timedelta(minutes=5)
            
            window_requests = [
                req for req in recent_requests
                if window_start <= req['timestamp'] <= window_end
            ]
            
            if window_requests:
                success_count = sum(1 for req in window_requests if req['success'])
                success_rates.append(success_count / len(window_requests))
                
                successful_reqs = [req for req in window_requests if req['success']]
                if successful_reqs:
                    avg_latency = sum(req['latency'] for req in successful_reqs) / len(successful_reqs)
                    latencies.append(avg_latency)
        
        # 分析趋势
        analysis = ""
        needs_optimization = False
        
        if len(success_rates) >= 2:
            # 检查成功率趋势
            if success_rates[-1] < success_rates[0] * 0.8:  # 下降超过20%
                analysis += "成功率呈下降趋势; "
                needs_optimization = True
            
            # 检查延迟趋势
            if len(latencies) >= 2 and latencies[-1] > latencies[0] * 1.2:  # 上升超过20%
                analysis += "延迟呈上升趋势; "
                needs_optimization = True
        
        if not analysis:
            analysis = "性能稳定"
        
        return {
            'needs_optimization': needs_optimization,
            'analysis': analysis,
            'success_rates': success_rates,
            'latencies': latencies
        }
    
    def _generate_trend_based_optimizations(self, trend_data: Dict) -> Dict[str, Any]:
        """基于趋势生成优化参数"""
        updates = {}
        analysis = trend_data['analysis']
        
        if "下降趋势" in analysis:
            # 成功率下降，增加保守性
            updates['timeout_multiplier'] = 1.3
            updates['delay_multiplier'] = 1.2
            updates['retry_multiplier'] = 1.1
        
        if "上升趋势" in analysis:
            # 延迟上升，增加超时和延迟
            updates['timeout_multiplier'] = max(
                updates.get('timeout_multiplier', 1.0), 1.2
            )
            updates['delay_multiplier'] = max(
                updates.get('delay_multiplier', 1.0), 1.3
            )
        
        return updates
    
    def get_config_report(self) -> Dict[str, Any]:
        """获取配置报告"""
        # 计算性能统计
        total_requests = len(self.performance_data['requests'])
        
        if total_requests > 0:
            success_count = sum(1 for req in self.performance_data['requests'] if req['success'])
            overall_success_rate = success_count / total_requests
            
            successful_reqs = [req for req in self.performance_data['requests'] if req['success']]
            if successful_reqs:
                avg_latency = sum(req['latency'] for req in successful_reqs) / len(successful_reqs)
            else:
                avg_latency = 0
        else:
            overall_success_rate = 0
            avg_latency = 0
        
        return {
            'config_status': {
                'base_config_loaded': bool(self.base_config),
                'dynamic_config_active': bool(self.dynamic_config),
                'config_history_count': len(self.config_history),
                'last_config_update': self.last_config_update.isoformat(),
                'auto_optimization_running': self.optimization_running
            },
            'performance_summary': {
                'total_requests': total_requests,
                'overall_success_rate': round(overall_success_rate, 3),
                'average_latency': round(avg_latency, 2),
                'recent_errors': len(self.performance_data['errors'][-100:]),
                'data_retention_period': '24小时'
            },
            'current_optimizations': self.dynamic_config.get('current_optimizations', {}),
            'adaptive_parameters': self.dynamic_config.get('adaptive_parameters', {}),
            'config_recommendations': self._generate_config_recommendations(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_config_recommendations(self) -> List[str]:
        """生成配置建议"""
        recommendations = []
        
        # 基于性能数据生成建议
        if len(self.performance_data['requests']) < 50:
            recommendations.append("数据量不足，建议收集更多性能数据后再进行优化")
        
        # 检查配置历史
        recent_changes = [
            change for change in self.config_history[-10:]
            if change['config_type'] == 'dynamic'
        ]
        
        if len(recent_changes) > 5:
            recommendations.append("配置变更频繁，建议稳定运行一段时间")
        
        # 检查性能阈值
        report = self.get_config_report()
        success_rate = report['performance_summary']['overall_success_rate']
        
        if success_rate < 0.6:
            recommendations.append("成功率过低，建议检查目标网站的反爬虫机制")
        
        return recommendations
    
    def save_config_snapshot(self, snapshot_file: str = None):
        """保存配置快照"""
        if snapshot_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_file = f"config_snapshot_{timestamp}.json"
        
        snapshot = {
            'base_config': self.base_config,
            'dynamic_config': self.dynamic_config,
            'performance_summary': self.get_config_report()['performance_summary'],
            'snapshot_time': datetime.now().isoformat()
        }
        
        try:
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置快照已保存: {snapshot_file}")
            return True
            
        except Exception as e:
            logger.error(f"配置快照保存失败: {e}")
            return False

# 使用示例
def test_dynamic_config_center():
    """测试动态配置中心"""
    config_center = DynamicConfigCenter()
    
    # 添加配置监听器
    def config_listener(config_type, changes, reason):
        print(f"配置变更通知 - 类型: {config_type}, 原因: {reason}")
        print(f"变更内容: {json.dumps(changes, indent=2, ensure_ascii=False)}")
    
    config_center.add_config_listener(config_listener)
    
    print("动态配置中心测试开始...")
    
    # 测试配置获取
    base_config = config_center.get_config('base')
    dynamic_config = config_center.get_config('dynamic')
    
    print(f"基础配置加载: {bool(base_config)}")
    print(f"动态配置加载: {bool(dynamic_config)}")
    
    # 测试配置更新
    updates = {
        'adaptive_parameters': {
            'timeout_multiplier': 1.2,
            'delay_multiplier': 1.1
        }
    }
    
    success = config_center.update_config('dynamic', updates, "测试更新")
    print(f"配置更新结果: {'成功' if success else '失败'}")
    
    # 模拟性能数据记录
    print("\n模拟性能数据记录...")
    
    for i in range(50):
        success = i % 10 != 0  # 90% 成功率
        latency = 200 + i * 10  # 逐渐增加的延迟
        
        config_center.record_performance({
            'success': success,
            'latency': latency,
            'url': f'https://example.com/page{i}',
            'strategy': 'balanced'
        })
    
    # 获取配置报告
    report = config_center.get_config_report()
    
    print("\n配置报告:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # 测试自动优化
    print("\n启动自动优化...")
    config_center.start_auto_optimization(interval_minutes=1)  # 1分钟间隔用于测试
    
    # 等待优化执行
    time.sleep(70)  # 等待70秒（超过1分钟）
    
    # 停止优化
    config_center.stop_auto_optimization()
    
    # 保存配置快照
    config_center.save_config_snapshot()
    
    print("\n动态配置中心测试完成")

if __name__ == "__main__":
    test_dynamic_config_center()