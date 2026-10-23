#!/usr/bin/env python3
"""
智能爬取策略模块
基于网站特性和历史数据动态调整爬取策略
"""

import random
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class IntelligentCrawlingStrategy:
    """智能爬取策略管理器"""
    
    def __init__(self):
        # 网站特性数据库
        self.website_profiles = self._initialize_website_profiles()
        
        # 爬取策略模板
        self.crawling_strategies = {
            'aggressive': {
                'timeout': 60,
                'max_retries': 3,
                'delay_between_requests': 5,
                'concurrent_requests': 5,
                'risk_level': 'high'
            },
            'balanced': {
                'timeout': 120,
                'max_retries': 5,
                'delay_between_requests': 10,
                'concurrent_requests': 3,
                'risk_level': 'medium'
            },
            'conservative': {
                'timeout': 300,
                'max_retries': 8,
                'delay_between_requests': 20,
                'concurrent_requests': 2,
                'risk_level': 'low'
            },
            'ultra_conservative': {
                'timeout': 600,
                'max_retries': 10,
                'delay_between_requests': 30,
                'concurrent_requests': 1,
                'risk_level': 'very_low'
            }
        }
        
        # 性能统计
        self.performance_stats = {
            'total_crawls': 0,
            'successful_crawls': 0,
            'failed_crawls': 0,
            'average_success_rate': 0,
            'strategy_effectiveness': {},
            'website_success_rates': {}
        }
        
        # 实时调整参数
        self.dynamic_adjustments = {
            'current_risk_level': 'medium',
            'adaptive_timeout_multiplier': 1.0,
            'adaptive_delay_multiplier': 1.0,
            'last_adjustment_time': time.time()
        }
    
    def _initialize_website_profiles(self) -> Dict[str, Dict[str, Any]]:
        """初始化网站特性数据库"""
        return {
            # 南非新闻网站
            'news24.com': {
                'country': 'za',
                'category': 'news',
                'anti_crawler_level': 'medium',
                'network_stability': 'high',
                'response_time': 'fast',
                'preferred_strategy': 'balanced',
                'historical_success_rate': 0.85,
                'last_crawl_time': None,
                'consecutive_failures': 0
            },
            
            # 肯尼亚新闻网站
            'nation.co.ke': {
                'country': 'ke',
                'category': 'news',
                'anti_crawler_level': 'low',
                'network_stability': 'medium',
                'response_time': 'medium',
                'preferred_strategy': 'balanced',
                'historical_success_rate': 0.78,
                'last_crawl_time': None,
                'consecutive_failures': 0
            },
            
            # 尼日利亚新闻网站
            'punchng.com': {
                'country': 'ng',
                'category': 'news',
                'anti_crawler_level': 'high',
                'network_stability': 'low',
                'response_time': 'slow',
                'preferred_strategy': 'conservative',
                'historical_success_rate': 0.65,
                'last_crawl_time': None,
                'consecutive_failures': 0
            },
            
            # 埃及新闻网站
            'ahram.org.eg': {
                'country': 'eg',
                'category': 'news',
                'anti_crawler_level': 'medium',
                'network_stability': 'high',
                'response_time': 'fast',
                'preferred_strategy': 'balanced',
                'historical_success_rate': 0.82,
                'last_crawl_time': None,
                'consecutive_failures': 0
            },
            
            # 坦桑尼亚新闻网站
            'thecitizen.co.tz': {
                'country': 'tz',
                'category': 'news',
                'anti_crawler_level': 'low',
                'network_stability': 'medium',
                'response_time': 'medium',
                'preferred_strategy': 'balanced',
                'historical_success_rate': 0.75,
                'last_crawl_time': None,
                'consecutive_failures': 0
            }
        }
    
    def get_website_domain(self, url: str) -> str:
        """从URL提取域名"""
        try:
            domain = urlparse(url).netloc.lower()
            # 移除www前缀
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception as e:
            logger.warning(f"提取域名失败: {e}")
            return 'unknown'
    
    def get_website_profile(self, url: str) -> Dict[str, Any]:
        """获取网站特性配置"""
        domain = self.get_website_domain(url)
        
        if domain in self.website_profiles:
            profile = self.website_profiles[domain].copy()
            logger.info(f"找到网站 {domain} 的特性配置")
            return profile
        else:
            # 创建新的网站配置
            country_code = self._infer_country_from_domain(domain)
            
            default_profile = {
                'country': country_code,
                'category': 'unknown',
                'anti_crawler_level': 'unknown',
                'network_stability': 'unknown',
                'response_time': 'unknown',
                'preferred_strategy': 'balanced',
                'historical_success_rate': 0.5,
                'last_crawl_time': None,
                'consecutive_failures': 0
            }
            
            self.website_profiles[domain] = default_profile
            logger.info(f"为未知网站 {domain} 创建默认配置")
            return default_profile
    
    def _infer_country_from_domain(self, domain: str) -> str:
        """从域名推断国家"""
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
        
        return 'unknown'
    
    def select_crawling_strategy(self, url: str) -> Dict[str, Any]:
        """选择爬取策略"""
        website_profile = self.get_website_profile(url)
        
        # 基础策略选择
        strategy_name = website_profile['preferred_strategy']
        base_strategy = self.crawling_strategies[strategy_name].copy()
        
        # 根据网站特性调整策略
        adjusted_strategy = self._adjust_strategy_for_website(base_strategy, website_profile)
        
        # 根据实时性能动态调整
        final_strategy = self._apply_dynamic_adjustments(adjusted_strategy)
        
        logger.info(f"为 {url} 选择策略: {strategy_name}, 最终参数: {final_strategy}")
        return final_strategy
    
    def _adjust_strategy_for_website(self, strategy: Dict[str, Any], 
                                   profile: Dict[str, Any]) -> Dict[str, Any]:
        """根据网站特性调整策略"""
        adjusted = strategy.copy()
        
        # 根据反爬虫级别调整
        anti_crawler_multipliers = {
            'low': 0.8,
            'medium': 1.0,
            'high': 1.5,
            'very_high': 2.0,
            'unknown': 1.2
        }
        
        multiplier = anti_crawler_multipliers.get(profile['anti_crawler_level'], 1.0)
        adjusted['timeout'] = int(adjusted['timeout'] * multiplier)
        adjusted['delay_between_requests'] = int(adjusted['delay_between_requests'] * multiplier)
        
        # 根据网络稳定性调整
        if profile['network_stability'] == 'low':
            adjusted['max_retries'] = min(adjusted['max_retries'] + 2, 15)
        elif profile['network_stability'] == 'high':
            adjusted['max_retries'] = max(adjusted['max_retries'] - 1, 1)
        
        # 根据响应时间调整
        if profile['response_time'] == 'slow':
            adjusted['timeout'] = int(adjusted['timeout'] * 1.5)
        elif profile['response_time'] == 'fast':
            adjusted['timeout'] = max(int(adjusted['timeout'] * 0.8), 30)
        
        return adjusted
    
    def _apply_dynamic_adjustments(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """应用动态调整"""
        adjusted = strategy.copy()
        
        # 应用实时调整参数
        adjusted['timeout'] = int(adjusted['timeout'] * self.dynamic_adjustments['adaptive_timeout_multiplier'])
        adjusted['delay_between_requests'] = int(
            adjusted['delay_between_requests'] * self.dynamic_adjustments['adaptive_delay_multiplier']
        )
        
        return adjusted
    
    def update_website_profile(self, url: str, success: bool, 
                             response_time: float, error_type: str = None):
        """更新网站特性配置"""
        domain = self.get_website_domain(url)
        
        if domain not in self.website_profiles:
            self.get_website_profile(url)  # 确保配置存在
        
        profile = self.website_profiles[domain]
        
        # 更新爬取时间
        profile['last_crawl_time'] = datetime.now()
        
        # 更新连续失败次数
        if success:
            profile['consecutive_failures'] = 0
            
            # 更新历史成功率
            profile['historical_success_rate'] = (
                profile['historical_success_rate'] * 0.9 + 0.1
            )
        else:
            profile['consecutive_failures'] += 1
            
            # 更新历史成功率
            profile['historical_success_rate'] = (
                profile['historical_success_rate'] * 0.9
            )
        
        # 根据错误类型调整反爬虫级别
        if error_type in ['timeout', 'connection_error']:
            # 可能是网络问题，不调整反爬虫级别
            pass
        elif error_type in ['blocked', 'captcha', '403', '429']:
            # 反爬虫措施，提高反爬虫级别
            current_level = profile['anti_crawler_level']
            if current_level in ['low', 'unknown']:
                profile['anti_crawler_level'] = 'medium'
            elif current_level == 'medium':
                profile['anti_crawler_level'] = 'high'
            elif current_level == 'high':
                profile['anti_crawler_level'] = 'very_high'
        
        # 根据响应时间调整响应时间评级
        if response_time < 2:
            profile['response_time'] = 'fast'
        elif response_time < 5:
            profile['response_time'] = 'medium'
        else:
            profile['response_time'] = 'slow'
        
        # 更新首选策略
        self._update_preferred_strategy(profile)
        
        logger.info(f"更新网站 {domain} 配置: 成功率={profile['historical_success_rate']:.2f}, "
                   f"连续失败={profile['consecutive_failures']}")
    
    def _update_preferred_strategy(self, profile: Dict[str, Any]):
        """更新首选策略"""
        # 根据连续失败次数调整策略
        if profile['consecutive_failures'] >= 3:
            # 连续失败3次，切换到更保守的策略
            current_strategy = profile['preferred_strategy']
            strategy_sequence = ['aggressive', 'balanced', 'conservative', 'ultra_conservative']
            
            current_index = strategy_sequence.index(current_strategy)
            if current_index < len(strategy_sequence) - 1:
                profile['preferred_strategy'] = strategy_sequence[current_index + 1]
                logger.info(f"由于连续失败，切换策略到 {profile['preferred_strategy']}")
        
        # 根据成功率调整策略
        elif profile['historical_success_rate'] > 0.8 and profile['consecutive_failures'] == 0:
            # 高成功率，可以尝试更激进的策略
            current_strategy = profile['preferred_strategy']
            strategy_sequence = ['ultra_conservative', 'conservative', 'balanced', 'aggressive']
            
            current_index = strategy_sequence.index(current_strategy)
            if current_index > 0:
                profile['preferred_strategy'] = strategy_sequence[current_index - 1]
                logger.info(f"由于高成功率，切换策略到 {profile['preferred_strategy']}")
    
    def update_performance_stats(self, url: str, success: bool, 
                               strategy_name: str, response_time: float):
        """更新性能统计"""
        self.performance_stats['total_crawls'] += 1
        
        if success:
            self.performance_stats['successful_crawls'] += 1
        else:
            self.performance_stats['failed_crawls'] += 1
        
        # 更新策略有效性
        if strategy_name not in self.performance_stats['strategy_effectiveness']:
            self.performance_stats['strategy_effectiveness'][strategy_name] = {
                'total': 0,
                'successful': 0,
                'success_rate': 0
            }
        
        strategy_stats = self.performance_stats['strategy_effectiveness'][strategy_name]
        strategy_stats['total'] += 1
        if success:
            strategy_stats['successful'] += 1
        strategy_stats['success_rate'] = strategy_stats['successful'] / strategy_stats['total']
        
        # 更新网站成功率
        domain = self.get_website_domain(url)
        if domain not in self.performance_stats['website_success_rates']:
            self.performance_stats['website_success_rates'][domain] = {
                'total': 0,
                'successful': 0,
                'success_rate': 0
            }
        
        website_stats = self.performance_stats['website_success_rates'][domain]
        website_stats['total'] += 1
        if success:
            website_stats['successful'] += 1
        website_stats['success_rate'] = website_stats['successful'] / website_stats['total']
        
        # 更新平均成功率
        if self.performance_stats['total_crawls'] > 0:
            self.performance_stats['average_success_rate'] = (
                self.performance_stats['successful_crawls'] / self.performance_stats['total_crawls']
            )
    
    def adjust_dynamic_parameters(self):
        """动态调整全局参数"""
        current_time = time.time()
        
        # 每5分钟调整一次
        if current_time - self.dynamic_adjustments['last_adjustment_time'] < 300:
            return
        
        # 根据整体成功率调整
        overall_success_rate = self.performance_stats['average_success_rate']
        
        if overall_success_rate < 0.3:
            # 成功率很低，采用保守策略
            self.dynamic_adjustments['adaptive_timeout_multiplier'] = 2.0
            self.dynamic_adjustments['adaptive_delay_multiplier'] = 2.0
            self.dynamic_adjustments['current_risk_level'] = 'very_low'
        elif overall_success_rate < 0.6:
            # 成功率中等，采用平衡策略
            self.dynamic_adjustments['adaptive_timeout_multiplier'] = 1.5
            self.dynamic_adjustments['adaptive_delay_multiplier'] = 1.5
            self.dynamic_adjustments['current_risk_level'] = 'low'
        elif overall_success_rate < 0.8:
            # 成功率良好，采用标准策略
            self.dynamic_adjustments['adaptive_timeout_multiplier'] = 1.0
            self.dynamic_adjustments['adaptive_delay_multiplier'] = 1.0
            self.dynamic_adjustments['current_risk_level'] = 'medium'
        else:
            # 成功率很高，可以稍微激进
            self.dynamic_adjustments['adaptive_timeout_multiplier'] = 0.8
            self.dynamic_adjustments['adaptive_delay_multiplier'] = 0.8
            self.dynamic_adjustments['current_risk_level'] = 'high'
        
        self.dynamic_adjustments['last_adjustment_time'] = current_time
        
        logger.info(f"动态调整参数: 超时倍数={self.dynamic_adjustments['adaptive_timeout_multiplier']}, "
                   f"延迟倍数={self.dynamic_adjustments['adaptive_delay_multiplier']}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            'total_crawls': self.performance_stats['total_crawls'],
            'successful_crawls': self.performance_stats['successful_crawls'],
            'failed_crawls': self.performance_stats['failed_crawls'],
            'average_success_rate': round(self.performance_stats['average_success_rate'] * 100, 2),
            'strategy_effectiveness': {
                strategy: {
                    'total': stats['total'],
                    'successful': stats['successful'],
                    'success_rate': round(stats['success_rate'] * 100, 2)
                }
                for strategy, stats in self.performance_stats['strategy_effectiveness'].items()
            },
            'top_websites': dict(sorted(
                self.performance_stats['website_success_rates'].items(),
                key=lambda x: x[1]['success_rate'],
                reverse=True
            )[:10]),
            'dynamic_parameters': self.dynamic_adjustments,
            'recommendations': self.generate_optimization_recommendations()
        }
    
    def generate_optimization_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        overall_success_rate = self.performance_stats['average_success_rate']
        
        if overall_success_rate < 0.3:
            recommendations.append("整体成功率极低，建议检查网络连接和代理配置")
        elif overall_success_rate < 0.6:
            recommendations.append("整体成功率较低，建议优化爬取策略和增加重试次数")
        
        # 分析策略有效性
        for strategy, stats in self.performance_stats['strategy_effectiveness'].items():
            if stats['total'] > 10 and stats['success_rate'] < 0.5:
                recommendations.append(f"策略 {strategy} 成功率较低({stats['success_rate']:.1%})，建议调整参数")
        
        return recommendations

# 使用示例
def test_intelligent_crawling_strategy():
    """测试智能爬取策略"""
    strategy_manager = IntelligentCrawlingStrategy()
    
    # 测试不同网站
    test_urls = [
        "https://www.news24.com",
        "https://www.nation.co.ke", 
        "https://www.punchng.com",
        "https://www.unknown-site.com"
    ]
    
    for url in test_urls:
        print(f"\n测试网站: {url}")
        
        # 获取爬取策略
        strategy = strategy_manager.select_crawling_strategy(url)
        print(f"爬取策略: {strategy}")
        
        # 模拟爬取结果
        success = random.random() > 0.3  # 70%成功率
        response_time = random.uniform(1, 10)
        
        # 更新性能统计
        strategy_manager.update_website_profile(url, success, response_time)
        strategy_manager.update_performance_stats(url, success, strategy['risk_level'], response_time)
        
        print(f"爬取结果: {'成功' if success else '失败'}, 响应时间: {response_time:.2f}秒")
    
    # 获取性能报告
    report = strategy_manager.get_performance_report()
    print(f"\n性能报告: {json.dumps(report, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    test_intelligent_crawling_strategy()