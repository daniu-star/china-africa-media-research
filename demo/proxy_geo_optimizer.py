#!/usr/bin/env python3
"""
智能代理质量评估和动态选择系统
基于多维度指标实现代理性能优化和自适应选择
"""

import random
import logging
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from urllib.parse import urlparse
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)

class SmartProxyManager:
    """智能代理管理器 - 基于多维度质量评估和动态选择"""
    
    def __init__(self, config_file: str = None):
        # 代理质量评估指标权重
        self.quality_weights = {
            'latency': 0.25,      # 延迟权重
            'success_rate': 0.30, # 成功率权重
            'stability': 0.20,    # 稳定性权重
            'geographic': 0.15,   # 地理位置权重
            'freshness': 0.10     # 新鲜度权重
        }
        
        # 代理池配置
        self.proxy_pool = self._initialize_smart_proxy_pool()
        
        # 性能监控数据
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_latency': 0.0,
            'success_rate_history': [],  # 成功率历史记录
            'latency_history': [],        # 延迟历史记录
            'proxy_usage_stats': {}      # 代理使用统计
        }
        
        # 智能学习配置
        self.learning_config = {
            'window_size': 100,           # 学习窗口大小
            'decay_factor': 0.95,         # 历史数据衰减因子
            'adaptive_threshold': 0.7,    # 自适应阈值
            'exploration_rate': 0.1      # 探索率
        }
        
        # 代理健康状态
        self.proxy_health = {}
        
        # 地域优化配置
        self.geo_optimization = self._initialize_geo_optimization()
        
        # 负载均衡配置
        self.load_balancing = {
            'max_concurrent_per_proxy': 5,
            'proxy_usage_limit': 1000,
            'cool_down_period': 300  # 冷却期5分钟
        }
        
        # 配置持久化
        self.config_file = config_file
        self._load_config()
    
    def _initialize_smart_proxy_pool(self) -> Dict[str, Dict]:
        """初始化智能代理池"""
        return {
            'south-africa': {
                'proxies': ['proxy1.south-africa.example.com:8080', 'proxy2.south-africa.example.com:8080'],
                'region': 'southern-africa',
                'latency_baseline': 200,
                'priority': 0.9
            },
            'kenya': {
                'proxies': ['proxy1.kenya.example.com:8080', 'proxy2.kenya.example.com:8080'],
                'region': 'east-africa',
                'latency_baseline': 300,
                'priority': 0.8
            },
            'nigeria': {
                'proxies': ['proxy1.nigeria.example.com:8080', 'proxy2.nigeria.example.com:8080'],
                'region': 'west-africa',
                'latency_baseline': 400,
                'priority': 0.85
            },
            'egypt': {
                'proxies': ['proxy1.egypt.example.com:8080', 'proxy2.egypt.example.com:8080'],
                'region': 'north-africa',
                'latency_baseline': 250,
                'priority': 0.9
            },
            'europe': {
                'proxies': ['proxy1.europe.example.com:8080', 'proxy2.europe.example.com:8080'],
                'region': 'europe',
                'latency_baseline': 150,
                'priority': 0.7
            },
            'asia': {
                'proxies': ['proxy1.asia.example.com:8080', 'proxy2.asia.example.com:8080'],
                'region': 'asia',
                'latency_baseline': 350,
                'priority': 0.6
            }
        }
    
    def _initialize_geo_optimization(self) -> Dict[str, Any]:
        """初始化地域优化配置"""
        return {
            'country_mapping': {
                '.za': 'south-africa', '.co.za': 'south-africa',
                '.ke': 'kenya', '.co.ke': 'kenya',
                '.ng': 'nigeria', '.com.ng': 'nigeria',
                '.gh': 'ghana', '.com.gh': 'ghana',
                '.tz': 'tanzania', '.co.tz': 'tanzania',
                '.ug': 'uganda', '.co.ug': 'uganda',
                '.zm': 'zambia', '.co.zm': 'zambia',
                '.zw': 'zimbabwe', '.co.zw': 'zimbabwe',
                '.eg': 'egypt', '.com.eg': 'egypt'
            },
            'region_preferences': {
                'southern-africa': ['south-africa', 'europe'],
                'east-africa': ['kenya', 'europe', 'asia'],
                'west-africa': ['nigeria', 'europe'],
                'north-africa': ['egypt', 'europe'],
                'default': ['europe', 'asia']
            },
            'latency_thresholds': {
                'critical': 1000,   # 关键阈值
                'warning': 500,     # 警告阈值
                'optimal': 200      # 最优阈值
            }
        }
    
    def _load_config(self):
        """加载配置文件"""
        if self.config_file:
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 更新配置
                    self.quality_weights.update(config.get('quality_weights', {}))
                    self.learning_config.update(config.get('learning_config', {}))
                    self.load_balancing.update(config.get('load_balancing', {}))
                    logger.info("配置加载成功")
            except FileNotFoundError:
                logger.warning("配置文件不存在，使用默认配置")
            except Exception as e:
                logger.error(f"配置加载失败: {e}")
    
    def save_config(self):
        """保存配置到文件"""
        if self.config_file:
            try:
                config = {
                    'quality_weights': self.quality_weights,
                    'learning_config': self.learning_config,
                    'load_balancing': self.load_balancing,
                    'performance_metrics': self.performance_metrics
                }
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                logger.info("配置保存成功")
            except Exception as e:
                logger.error(f"配置保存失败: {e}")
    
    def select_optimal_proxy(self, url: str, target_region: str = None) -> Dict[str, Any]:
        """选择最优代理 - 基于多维度质量评估"""
        # 获取目标地域
        if not target_region:
            target_region = self._get_target_region_from_url(url)
        
        # 获取候选代理组
        candidate_groups = self._get_candidate_proxy_groups(target_region)
        
        # 评估每个代理组的质量分数
        proxy_scores = {}
        for group_name in candidate_groups:
            score = self._calculate_proxy_group_score(group_name, url)
            proxy_scores[group_name] = score
        
        # 选择最高分数的代理组
        if proxy_scores:
            best_group = max(proxy_scores.items(), key=lambda x: x[1])[0]
            proxy_address = self._select_proxy_from_group(best_group)
            
            return {
                'proxy': proxy_address,
                'group': best_group,
                'score': proxy_scores[best_group],
                'region': target_region,
                'strategy': 'quality_based'
            }
        
        # 如果没有可用代理，返回直接连接
        return {'proxy': None, 'strategy': 'direct', 'reason': 'no_available_proxies'}
    
    def _get_target_region_from_url(self, url: str) -> str:
        """从URL获取目标地域"""
        try:
            domain = urlparse(url).netloc.lower()
            for suffix, region in self.geo_optimization['country_mapping'].items():
                if domain.endswith(suffix):
                    return region
            
            # 根据域名关键词推断地域
            if any(keyword in domain for keyword in ['south', 'za', 'johannesburg']):
                return 'southern-africa'
            elif any(keyword in domain for keyword in ['kenya', 'nairobi', 'east']):
                return 'east-africa'
            elif any(keyword in domain for keyword in ['nigeria', 'lagos', 'west']):
                return 'west-africa'
            elif any(keyword in domain for keyword in ['egypt', 'cairo', 'north']):
                return 'north-africa'
            
            return 'default'
        except Exception as e:
            logger.warning(f"地域推断失败: {e}")
            return 'default'
    
    def _get_candidate_proxy_groups(self, target_region: str) -> List[str]:
        """获取候选代理组"""
        # 获取地域偏好配置
        preferred_groups = self.geo_optimization['region_preferences'].get(
            target_region, self.geo_optimization['region_preferences']['default']
        )
        
        # 过滤可用的代理组
        available_groups = []
        for group in preferred_groups:
            if group in self.proxy_pool and self._is_proxy_group_healthy(group):
                available_groups.append(group)
        
        # 如果没有可用代理组，尝试所有健康代理组
        if not available_groups:
            available_groups = [group for group in self.proxy_pool 
                              if self._is_proxy_group_healthy(group)]
        
        return available_groups
    
    def _is_proxy_group_healthy(self, group_name: str) -> bool:
        """检查代理组是否健康"""
        if group_name not in self.proxy_health:
            return True  # 默认健康
        
        health_data = self.proxy_health[group_name]
        
        # 检查连续失败次数
        if health_data.get('consecutive_failures', 0) >= 3:
            return False
        
        # 检查最后成功时间
        last_success = health_data.get('last_success')
        if last_success:
            time_since_success = (datetime.now() - last_success).total_seconds()
            if time_since_success > 3600:  # 1小时无成功
                return False
        
        # 检查成功率
        success_rate = health_data.get('success_rate', 1.0)
        if success_rate < 0.3:  # 成功率低于30%
            return False
        
        return True
    
    def _calculate_proxy_group_score(self, group_name: str, url: str) -> float:
        """计算代理组质量分数 - 多维度评估"""
        score = 0.0
        
        # 1. 延迟评估 (25%权重)
        latency_score = self._evaluate_latency(group_name)
        score += latency_score * self.quality_weights['latency']
        
        # 2. 成功率评估 (30%权重)
        success_score = self._evaluate_success_rate(group_name)
        score += success_score * self.quality_weights['success_rate']
        
        # 3. 稳定性评估 (20%权重)
        stability_score = self._evaluate_stability(group_name)
        score += stability_score * self.quality_weights['stability']
        
        # 4. 地理位置评估 (15%权重)
        geographic_score = self._evaluate_geographic_fit(group_name, url)
        score += geographic_score * self.quality_weights['geographic']
        
        # 5. 新鲜度评估 (10%权重)
        freshness_score = self._evaluate_freshness(group_name)
        score += freshness_score * self.quality_weights['freshness']
        
        # 应用探索率 - 随机探索新代理
        if random.random() < self.learning_config['exploration_rate']:
            score *= random.uniform(0.8, 1.2)
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_latency(self, group_name: str) -> float:
        """评估延迟性能"""
        if group_name not in self.proxy_health:
            return 0.8  # 默认分数
        
        health_data = self.proxy_health[group_name]
        avg_latency = health_data.get('average_latency', 1000)
        
        # 基于延迟阈值计算分数
        thresholds = self.geo_optimization['latency_thresholds']
        
        if avg_latency <= thresholds['optimal']:
            return 1.0
        elif avg_latency <= thresholds['warning']:
            return 0.7
        elif avg_latency <= thresholds['critical']:
            return 0.3
        else:
            return 0.1
    
    def _evaluate_success_rate(self, group_name: str) -> float:
        """评估成功率"""
        if group_name not in self.proxy_health:
            return 0.8  # 默认分数
        
        health_data = self.proxy_health[group_name]
        success_rate = health_data.get('success_rate', 0.5)
        
        # 成功率越高分数越高
        if success_rate >= 0.9:
            return 1.0
        elif success_rate >= 0.7:
            return 0.8
        elif success_rate >= 0.5:
            return 0.6
        elif success_rate >= 0.3:
            return 0.4
        else:
            return 0.1
    
    def _evaluate_stability(self, group_name: str) -> float:
        """评估稳定性"""
        if group_name not in self.proxy_health:
            return 0.7  # 默认分数
        
        health_data = self.proxy_health[group_name]
        
        # 检查连续失败次数
        consecutive_failures = health_data.get('consecutive_failures', 0)
        if consecutive_failures >= 5:
            return 0.1
        elif consecutive_failures >= 3:
            return 0.3
        elif consecutive_failures >= 1:
            return 0.6
        
        # 检查请求波动性
        request_count = health_data.get('total_requests', 0)
        if request_count < 10:
            return 0.7  # 数据不足
        
        # 计算标准差（简化版）
        latency_history = health_data.get('latency_history', [])
        if len(latency_history) >= 5:
            avg_latency = statistics.mean(latency_history)
            std_dev = statistics.stdev(latency_history)
            
            # 标准差越小越稳定
            if std_dev < avg_latency * 0.1:
                return 1.0
            elif std_dev < avg_latency * 0.3:
                return 0.8
            else:
                return 0.5
        
        return 0.7
    
    def _evaluate_geographic_fit(self, group_name: str, url: str) -> float:
        """评估地理位置匹配度"""
        target_region = self._get_target_region_from_url(url)
        group_region = self.proxy_pool[group_name]['region']
        
        # 相同地域最高分
        if group_region == target_region:
            return 1.0
        
        # 检查地域偏好
        preferred_groups = self.geo_optimization['region_preferences'].get(
            target_region, self.geo_optimization['region_preferences']['default']
        )
        
        if group_name in preferred_groups:
            return 0.8
        
        # 相邻地域
        region_hierarchy = {
            'southern-africa': ['east-africa', 'west-africa'],
            'east-africa': ['southern-africa', 'north-africa'],
            'west-africa': ['southern-africa', 'north-africa'],
            'north-africa': ['east-africa', 'west-africa']
        }
        
        if target_region in region_hierarchy and group_region in region_hierarchy[target_region]:
            return 0.6
        
        return 0.3
    
    def _evaluate_freshness(self, group_name: str) -> float:
        """评估新鲜度（最近使用情况）"""
        if group_name not in self.proxy_health:
            return 1.0  # 新代理最高分
        
        health_data = self.proxy_health[group_name]
        last_used = health_data.get('last_used')
        
        if not last_used:
            return 1.0
        
        # 计算时间间隔
        time_since_used = (datetime.now() - last_used).total_seconds()
        
        # 时间间隔越短分数越高
        if time_since_used < 300:  # 5分钟内
            return 0.3  # 避免过度使用
        elif time_since_used < 1800:  # 30分钟内
            return 0.6
        elif time_since_used < 3600:  # 1小时内
            return 0.8
        else:
            return 1.0
    
    def _select_proxy_from_group(self, group_name: str) -> str:
        """从代理组中选择具体代理"""
        proxies = self.proxy_pool[group_name]['proxies']
        
        # 负载均衡：选择使用最少的代理
        usage_stats = self.performance_metrics.get('proxy_usage_stats', {})
        
        # 计算每个代理的使用次数
        proxy_usage = {}
        for proxy in proxies:
            proxy_usage[proxy] = usage_stats.get(proxy, 0)
        
        # 选择使用最少的代理
        if proxy_usage:
            selected_proxy = min(proxy_usage.items(), key=lambda x: x[1])[0]
        else:
            selected_proxy = random.choice(proxies)
        
        # 更新使用统计
        self.performance_metrics['proxy_usage_stats'][selected_proxy] = \
            self.performance_metrics['proxy_usage_stats'].get(selected_proxy, 0) + 1
        
        return selected_proxy
    
    def update_proxy_performance(self, proxy_info: Dict[str, Any], success: bool, 
                                latency: float, response_code: int = None):
        """更新代理性能数据"""
        group_name = proxy_info.get('group')
        proxy_address = proxy_info.get('proxy')
        
        if not group_name or not proxy_address:
            return
        
        # 初始化代理组健康数据
        if group_name not in self.proxy_health:
            self.proxy_health[group_name] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'average_latency': 0.0,
                'latency_history': [],
                'consecutive_failures': 0,
                'last_success': None,
                'last_used': datetime.now()
            }
        
        health_data = self.proxy_health[group_name]
        
        # 更新基本统计
        health_data['total_requests'] += 1
        health_data['last_used'] = datetime.now()
        
        if success:
            health_data['successful_requests'] += 1
            health_data['consecutive_failures'] = 0
            health_data['last_success'] = datetime.now()
            
            # 更新延迟数据
            health_data['latency_history'].append(latency)
            if len(health_data['latency_history']) > self.learning_config['window_size']:
                health_data['latency_history'].pop(0)
            
            # 计算平均延迟
            if health_data['latency_history']:
                health_data['average_latency'] = statistics.mean(health_data['latency_history'])
        else:
            health_data['failed_requests'] += 1
            health_data['consecutive_failures'] += 1
        
        # 计算成功率
        if health_data['total_requests'] > 0:
            health_data['success_rate'] = health_data['successful_requests'] / health_data['total_requests']
        
        # 更新全局性能指标
        self._update_global_metrics(success, latency)
        
        # 自适应调整权重
        self._adaptive_weight_adjustment()
    
    def _update_global_metrics(self, success: bool, latency: float):
        """更新全局性能指标"""
        self.performance_metrics['total_requests'] += 1
        
        if success:
            self.performance_metrics['successful_requests'] += 1
        else:
            self.performance_metrics['failed_requests'] += 1
        
        # 更新延迟历史
        self.performance_metrics['latency_history'].append(latency)
        if len(self.performance_metrics['latency_history']) > self.learning_config['window_size']:
            self.performance_metrics['latency_history'].pop(0)
        
        # 计算平均延迟
        if self.performance_metrics['latency_history']:
            self.performance_metrics['average_latency'] = statistics.mean(
                self.performance_metrics['latency_history']
            )
        
        # 更新成功率历史
        if self.performance_metrics['total_requests'] > 0:
            current_success_rate = self.performance_metrics['successful_requests'] / self.performance_metrics['total_requests']
            self.performance_metrics['success_rate_history'].append(current_success_rate)
            
            # 限制历史记录长度
            if len(self.performance_metrics['success_rate_history']) > self.learning_config['window_size']:
                self.performance_metrics['success_rate_history'].pop(0)
    
    def _adaptive_weight_adjustment(self):
        """自适应权重调整"""
        # 基于最近性能调整权重
        if len(self.performance_metrics['success_rate_history']) < 10:
            return  # 数据不足
        
        recent_success_rate = statistics.mean(
            self.performance_metrics['success_rate_history'][-10:]
        )
        
        # 如果成功率低于阈值，增加延迟权重
        if recent_success_rate < 0.6:
            self.quality_weights['latency'] = min(0.4, self.quality_weights['latency'] + 0.05)
            self.quality_weights['success_rate'] = max(0.2, self.quality_weights['success_rate'] - 0.05)
        
        # 如果延迟过高，增加稳定性权重
        if self.performance_metrics['average_latency'] > 500:
            self.quality_weights['stability'] = min(0.3, self.quality_weights['stability'] + 0.05)
            self.quality_weights['geographic'] = max(0.1, self.quality_weights['geographic'] - 0.05)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        total_requests = self.performance_metrics['total_requests']
        successful_requests = self.performance_metrics['successful_requests']
        
        if total_requests == 0:
            return {
                'status': 'no_data',
                'message': '暂无性能数据'
            }
        
        success_rate = successful_requests / total_requests
        
        # 代理组健康统计
        healthy_groups = []
        unhealthy_groups = []
        
        for group_name, health_data in self.proxy_health.items():
            group_info = {
                'name': group_name,
                'success_rate': health_data.get('success_rate', 0),
                'average_latency': health_data.get('average_latency', 0),
                'total_requests': health_data.get('total_requests', 0),
                'consecutive_failures': health_data.get('consecutive_failures', 0)
            }
            
            if self._is_proxy_group_healthy(group_name):
                healthy_groups.append(group_info)
            else:
                unhealthy_groups.append(group_info)
        
        return {
            'status': 'success',
            'summary': {
                'total_requests': total_requests,
                'success_rate': round(success_rate, 3),
                'average_latency': round(self.performance_metrics['average_latency'], 2),
                'healthy_proxy_groups': len(healthy_groups),
                'unhealthy_proxy_groups': len(unhealthy_groups)
            },
            'healthy_groups': healthy_groups,
            'unhealthy_groups': unhealthy_groups,
            'quality_weights': self.quality_weights,
            'optimization_suggestions': self._generate_optimization_suggestions()
        }
    
    def _generate_optimization_suggestions(self) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 成功率建议
        success_rate = self.performance_metrics['successful_requests'] / max(1, self.performance_metrics['total_requests'])
        if success_rate < 0.7:
            suggestions.append("成功率较低，建议检查代理可用性或增加延迟容忍度")
        
        # 延迟建议
        avg_latency = self.performance_metrics['average_latency']
        if avg_latency > 500:
            suggestions.append(f"平均延迟较高({avg_latency:.2f}ms)，建议优化网络连接或选择更近的代理")
        
        # 健康代理数量建议
        healthy_count = sum(1 for group in self.proxy_pool if self._is_proxy_group_healthy(group))
        if healthy_count < 2:
            suggestions.append("健康代理数量不足，建议添加更多代理或检查现有代理状态")
        
        # 权重配置建议
        if self.quality_weights['latency'] > 0.4:
            suggestions.append("延迟权重过高，可能影响成功率，建议平衡权重配置")
        
        return suggestions
    
    def reset_proxy_health(self, group_name: str = None):
        """重置代理健康状态"""
        if group_name:
            if group_name in self.proxy_health:
                self.proxy_health[group_name] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'average_latency': 0.0,
                    'latency_history': [],
                    'consecutive_failures': 0,
                    'last_success': None,
                    'last_used': datetime.now()
                }
        else:
            # 重置所有代理组
            for group in self.proxy_pool:
                self.proxy_health[group] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'average_latency': 0.0,
                    'latency_history': [],
                    'consecutive_failures': 0,
                    'last_success': None,
                    'last_used': datetime.now()
                }
    
    def add_proxy_group(self, group_name: str, proxies: List[str], 
                       region: str, latency_baseline: int = 300, priority: float = 0.8):
        """添加新的代理组"""
        self.proxy_pool[group_name] = {
            'proxies': proxies,
            'region': region,
            'latency_baseline': latency_baseline,
            'priority': priority
        }
        
        # 初始化健康数据
        self.proxy_health[group_name] = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_latency': 0.0,
            'latency_history': [],
            'consecutive_failures': 0,
            'last_success': None,
            'last_used': datetime.now()
        }
    
    def remove_proxy_group(self, group_name: str):
        """移除代理组"""
        if group_name in self.proxy_pool:
            del self.proxy_pool[group_name]
        if group_name in self.proxy_health:
            del self.proxy_health[group_name]

# 使用示例
def test_smart_proxy_manager():
    """测试智能代理管理器"""
    manager = SmartProxyManager()
    
    # 测试URL
    test_urls = [
        "https://www.news24.com",  # 南非
        "https://www.nation.co.ke",  # 肯尼亚
        "https://www.vanguardngr.com",  # 尼日利亚
        "https://www.ahram.org.eg"  # 埃及
    ]
    
    for url in test_urls:
        proxy_info = manager.select_optimal_proxy(url)
        print(f"URL: {url}")
        print(f"选择代理: {proxy_info}")
        print("-" * 50)
    
    # 获取性能报告
    report = manager.get_performance_report()
    print("性能报告:")
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_smart_proxy_manager()
    
    def get_country_code(self, url: str) -> str:
        """从URL获取国家代码"""
        try:
            domain = urlparse(url).netloc.lower()
            
            # 从域名后缀提取国家代码
            country_mapping = {
                '.co.za': 'za',  # 南非
                '.za': 'za',     # 南非
                '.ke': 'ke',     # 肯尼亚
                '.ug': 'ug',     # 乌干达
                '.tz': 'tz',     # 坦桑尼亚
                '.ng': 'ng',     # 尼日利亚
                '.gh': 'gh',     # 加纳
                '.ci': 'ci',     # 科特迪瓦
                '.eg': 'eg',     # 埃及
                '.ma': 'ma',     # 摩洛哥
                '.tn': 'tn',     # 突尼斯
                '.et': 'et',     # 埃塞俄比亚
                '.zm': 'zm',     # 赞比亚
                '.mw': 'mw'      # 马拉维
            }
            
            for suffix, country_code in country_mapping.items():
                if domain.endswith(suffix):
                    return country_code
            
            # 默认返回未知
            return 'unknown'
            
        except Exception as e:
            logger.warning(f"获取国家代码失败: {e}")
            return 'unknown'
    
    def get_geo_config(self, url: str) -> Dict[str, Any]:
        """根据URL获取地域配置"""
        country_code = self.get_country_code(url)
        
        if country_code in self.africa_proxy_configs:
            config = self.africa_proxy_configs[country_code]
            logger.info(f"检测到 {country_code} 网站，应用地域配置: {config}")
            return config
        else:
            # 默认配置
            default_config = {
                'preferred_proxies': ['europe'],
                'timezone': 'UTC',
                'language': 'en',
                'latency_threshold': 300,
                'proxy_required': False
            }
            logger.info(f"未知国家代码 {country_code}，使用默认配置")
            return default_config
    
    def select_optimal_proxy(self, url: str) -> Optional[Dict[str, Any]]:
        """选择最优代理"""
        geo_config = self.get_geo_config(url)
        
        # 如果不需要代理
        if not geo_config['proxy_required']:
            logger.info(f"网站 {url} 不需要代理，使用直连")
            return None
        
        # 获取首选代理类型
        preferred_types = geo_config['preferred_proxies']
        
        # 按优先级选择代理
        for proxy_type in preferred_types:
            if proxy_type in self.proxy_pool and self.proxy_pool[proxy_type]:
                # 选择健康的代理
                healthy_proxies = self._get_healthy_proxies(proxy_type)
                if healthy_proxies:
                    selected_proxy = random.choice(healthy_proxies)
                    
                    proxy_config = {
                        'http': f"http://{selected_proxy}",
                        'https': f"https://{selected_proxy}",
                        'proxy_type': proxy_type,
                        'country': self.get_country_code(url)
                    }
                    
                    logger.info(f"为 {url} 选择 {proxy_type} 代理: {selected_proxy}")
                    return proxy_config
        
        # 如果没有找到合适的代理，尝试其他类型
        for proxy_type, proxies in self.proxy_pool.items():
            if proxies and proxy_type not in preferred_types:
                healthy_proxies = self._get_healthy_proxies(proxy_type)
                if healthy_proxies:
                    selected_proxy = random.choice(healthy_proxies)
                    
                    proxy_config = {
                        'http': f"http://{selected_proxy}",
                        'https': f"https://{selected_proxy}",
                        'proxy_type': proxy_type,
                        'country': self.get_country_code(url)
                    }
                    
                    logger.warning(f"首选代理不可用，为 {url} 选择备用 {proxy_type} 代理: {selected_proxy}")
                    return proxy_config
        
        logger.warning(f"所有代理都不可用，为 {url} 使用直连")
        return None
    
    def _get_healthy_proxies(self, proxy_type: str) -> List[str]:
        """获取健康的代理列表"""
        if proxy_type not in self.proxy_pool:
            return []
        
        healthy_proxies = []
        for proxy in self.proxy_pool[proxy_type]:
            if self._is_proxy_healthy(proxy):
                healthy_proxies.append(proxy)
        
        return healthy_proxies
    
    def _is_proxy_healthy(self, proxy: str) -> bool:
        """检查代理是否健康"""
        # 简单的健康检查
        try:
            # 检查代理是否在健康记录中
            if proxy in self.proxy_health:
                health_info = self.proxy_health[proxy]
                
                # 如果最近失败次数过多，标记为不健康
                if health_info.get('consecutive_failures', 0) > 3:
                    return False
                
                # 检查最后成功时间
                last_success = health_info.get('last_success')
                if last_success and time.time() - last_success > 3600:  # 1小时未成功
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"检查代理健康状态失败: {e}")
            return False
    
    def update_proxy_health(self, proxy: str, success: bool, latency: float):
        """更新代理健康状态"""
        if proxy not in self.proxy_health:
            self.proxy_health[proxy] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'consecutive_failures': 0,
                'average_latency': 0,
                'last_success': None,
                'last_failure': None
            }
        
        health_info = self.proxy_health[proxy]
        health_info['total_requests'] += 1
        
        if success:
            health_info['successful_requests'] += 1
            health_info['consecutive_failures'] = 0
            health_info['last_success'] = time.time()
            
            # 更新平均延迟
            if health_info['average_latency'] == 0:
                health_info['average_latency'] = latency
            else:
                health_info['average_latency'] = (
                    health_info['average_latency'] * (health_info['successful_requests'] - 1) + latency
                ) / health_info['successful_requests']
        else:
            health_info['failed_requests'] += 1
            health_info['consecutive_failures'] += 1
            health_info['last_failure'] = time.time()
    
    def get_request_headers(self, url: str) -> Dict[str, str]:
        """获取地域适应的请求头"""
        geo_config = self.get_geo_config(url)
        country_code = self.get_country_code(url)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': geo_config['language'] + ',en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 添加地域特定的头信息
        if country_code != 'unknown':
            headers['X-Forwarded-For'] = self._generate_local_ip(country_code)
        
        return headers
    
    def _generate_local_ip(self, country_code: str) -> str:
        """生成地域适应的IP地址"""
        # 简单的IP地址生成（实际使用时应使用真实代理IP）
        ip_ranges = {
            'za': ['41.0.0.0', '41.255.255.255'],  # 南非
            'ke': ['197.0.0.0', '197.255.255.255'],  # 肯尼亚
            'ng': ['197.210.0.0', '197.210.255.255'],  # 尼日利亚
            'eg': ['197.0.0.0', '197.255.255.255'],  # 埃及
        }
        
        if country_code in ip_ranges:
            start_ip, end_ip = ip_ranges[country_code]
            # 简化IP生成（实际应使用更复杂的算法）
            return f"197.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        else:
            return f"197.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    
    def update_performance_stats(self, used_proxy: bool, success: bool, latency: float):
        """更新性能统计"""
        self.performance_stats['total_requests'] += 1
        
        if used_proxy:
            self.performance_stats['proxy_requests'] += 1
            if success:
                self.performance_stats['proxy_success_rate'] = (
                    (self.performance_stats['proxy_success_rate'] * (self.performance_stats['proxy_requests'] - 1) + 1) / 
                    self.performance_stats['proxy_requests']
                )
            else:
                self.performance_stats['proxy_failures'] += 1
        else:
            self.performance_stats['direct_requests'] += 1
            if success:
                self.performance_stats['direct_success_rate'] = (
                    (self.performance_stats['direct_success_rate'] * (self.performance_stats['direct_requests'] - 1) + 1) / 
                    self.performance_stats['direct_requests']
                )
        
        # 更新平均延迟
        if self.performance_stats['total_requests'] > 0:
            self.performance_stats['average_latency'] = (
                self.performance_stats['average_latency'] * (self.performance_stats['total_requests'] - 1) + latency
            ) / self.performance_stats['total_requests']
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            'total_requests': self.performance_stats['total_requests'],
            'proxy_requests': self.performance_stats['proxy_requests'],
            'direct_requests': self.performance_stats['direct_requests'],
            'proxy_success_rate': round(self.performance_stats['proxy_success_rate'] * 100, 2),
            'direct_success_rate': round(self.performance_stats['direct_success_rate'] * 100, 2),
            'average_latency': round(self.performance_stats['average_latency'], 2),
            'proxy_failures': self.performance_stats['proxy_failures'],
            'healthy_proxies': len([p for p in self.proxy_health if self._is_proxy_healthy(p)]),
            'recommendations': self.generate_optimization_recommendations()
        }
    
    def generate_optimization_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if self.performance_stats['proxy_success_rate'] < 50:
            recommendations.append("代理成功率较低，建议更换代理供应商或优化代理配置")
        
        if self.performance_stats['average_latency'] > 200:
            recommendations.append("平均延迟较高，建议优化网络连接或选择更近的代理")
        
        if self.performance_stats['proxy_failures'] > self.performance_stats['proxy_requests'] * 0.3:
            recommendations.append("代理失败率较高，建议加强代理健康检查和故障转移")
        
        return recommendations

# 使用示例
def test_proxy_geo_optimizer():
    """测试代理和地域优化器"""
    import time
    
    optimizer = ProxyGeoOptimizer()
    
    # 测试不同非洲网站
    test_urls = [
        "https://www.news24.com",  # 南非
        "https://www.nation.co.ke",  # 肯尼亚
        "https://www.punchng.com",  # 尼日利亚
        "https://www.google.com"  # 非非洲网站
    ]
    
    for url in test_urls:
        print(f"\n测试URL: {url}")
        
        # 获取地域配置
        geo_config = optimizer.get_geo_config(url)
        print(f"地域配置: {geo_config}")
        
        # 选择代理
        proxy_config = optimizer.select_optimal_proxy(url)
        print(f"代理配置: {proxy_config}")
        
        # 获取请求头
        headers = optimizer.get_request_headers(url)
        print(f"请求头: {headers}")
        
        # 模拟性能统计更新
        optimizer.update_performance_stats(
            used_proxy=proxy_config is not None,
            success=True,
            latency=random.uniform(50, 300)
        )

if __name__ == "__main__":
    test_proxy_geo_optimizer()