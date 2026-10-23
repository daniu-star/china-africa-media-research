#!/usr/bin/env python3
"""
爬虫失败率优化器
专门针对非洲网站爬取的高失败率问题进行优化
"""

import json
import time
import requests
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FailureRateOptimizer:
    def __init__(self, config_file='crawler_optimization_config.json'):
        self.config = self.load_config(config_file)
        self.failure_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'failure_rate': 0.0,
            'last_check': datetime.now()
        }
        
    def load_config(self, config_file):
        """加载优化配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_file} 不存在，使用默认配置")
            return self.get_default_config()
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "failure_rate_optimization": {
                "enabled": True,
                "max_failure_rate": 0.3,
                "adaptive_timeout": {
                    "initial_timeout": 60,
                    "max_timeout": 180,
                    "timeout_multiplier": 1.5,
                    "min_timeout": 30
                },
                "retry_strategy": {
                    "max_retries": 3,
                    "backoff_factor": 2,
                    "retry_delay": 10,
                    "smart_retry": True
                }
            }
        }
    
    def calculate_failure_rate(self):
        """计算当前失败率"""
        if self.failure_stats['total_requests'] == 0:
            return 0.0
        
        self.failure_stats['failure_rate'] = (
            self.failure_stats['failed_requests'] / self.failure_stats['total_requests']
        )
        return self.failure_stats['failure_rate']
    
    def update_stats(self, success=True):
        """更新统计信息"""
        self.failure_stats['total_requests'] += 1
        if success:
            self.failure_stats['successful_requests'] += 1
        else:
            self.failure_stats['failed_requests'] += 1
        
        self.calculate_failure_rate()
        
        # 每10次请求检查一次失败率
        if self.failure_stats['total_requests'] % 10 == 0:
            self.check_and_adjust()
    
    def check_and_adjust(self):
        """检查失败率并调整策略"""
        current_rate = self.failure_stats['failure_rate']
        max_rate = self.config['failure_rate_optimization']['max_failure_rate']
        
        logger.info(f"当前失败率: {current_rate:.2%}, 阈值: {max_rate:.2%}")
        
        if current_rate > max_rate:
            logger.warning(f"失败率过高 ({current_rate:.2%} > {max_rate:.2%})，启动优化策略")
            self.activate_optimization_strategies()
        else:
            logger.info("失败率在可接受范围内")
    
    def activate_optimization_strategies(self):
        """激活优化策略"""
        strategies = [
            "增加请求延迟",
            "减少并发请求数", 
            "使用更保守的超时设置",
            "优先使用本地代理",
            "跳过已知问题网站"
        ]
        
        logger.info("激活以下优化策略:")
        for strategy in strategies:
            logger.info(f"  - {strategy}")
        
        # 这里可以添加具体的优化逻辑
        self.adjust_request_parameters()
    
    def adjust_request_parameters(self):
        """调整请求参数"""
        # 根据失败率动态调整参数
        failure_rate = self.failure_stats['failure_rate']
        
        if failure_rate > 0.5:
            # 高失败率：激进优化
            params = {
                'timeout': 180,
                'delay': 10,
                'max_retries': 2,
                'concurrent_requests': 1
            }
        elif failure_rate > 0.3:
            # 中等失败率：适度优化
            params = {
                'timeout': 120,
                'delay': 5,
                'max_retries': 3,
                'concurrent_requests': 2
            }
        else:
            # 低失败率：正常参数
            params = {
                'timeout': 60,
                'delay': 2,
                'max_retries': 5,
                'concurrent_requests': 4
            }
        
        logger.info(f"调整请求参数: {params}")
        return params
    
    def get_optimized_timeout(self, url):
        """获取优化后的超时时间"""
        base_timeout = self.config['failure_rate_optimization']['adaptive_timeout']['initial_timeout']
        
        # 根据失败率调整超时
        failure_rate = self.failure_stats['failure_rate']
        if failure_rate > 0.4:
            timeout_multiplier = 2.0
        elif failure_rate > 0.2:
            timeout_multiplier = 1.5
        else:
            timeout_multiplier = 1.0
        
        optimized_timeout = min(
            base_timeout * timeout_multiplier,
            self.config['failure_rate_optimization']['adaptive_timeout']['max_timeout']
        )
        
        # 网站特定设置
        website_settings = self.config.get('website_specific_settings', {}).get('high_failure_sites', {})
        for domain, settings in website_settings.items():
            if domain in url:
                optimized_timeout = max(optimized_timeout, settings.get('timeout', base_timeout))
                break
        
        return max(optimized_timeout, self.config['failure_rate_optimization']['adaptive_timeout']['min_timeout'])
    
    def should_skip_url(self, url):
        """判断是否应该跳过某个URL"""
        blocked_sites = self.config.get('website_specific_settings', {}).get('blocked_sites', {})
        
        for domain, settings in blocked_sites.items():
            if domain in url:
                logger.info(f"跳过已知问题网站: {url} (原因: {settings.get('reason', 'unknown')})")
                return True
        
        return False
    
    def get_system_stats(self):
        """获取系统统计信息"""
        try:
            response = requests.get('http://127.0.0.1:8000/stats', timeout=10)
            return response.json()
        except:
            return None
    
    def analyze_failure_patterns(self):
        """分析失败模式"""
        stats = self.get_system_stats()
        if stats:
            logger.info("系统统计信息:")
            logger.info(f"  任务队列大小: {stats.get('task_queue_size', 0)}")
            logger.info(f"  失败任务数: {stats.get('failed_tasks_queue_size', 0)}")
            logger.info(f"  活跃工作节点: {stats.get('active_workers', 0)}")
            
            error_stats = stats.get('error_stats', {})
            if error_stats.get('total_errors', 0) > 0:
                logger.warning(f"  总错误数: {error_stats['total_errors']}")
                logger.info(f"  错误类型分布: {error_stats.get('error_types', {})}")

def main():
    """主函数"""
    optimizer = FailureRateOptimizer()
    
    # 模拟一些请求来测试优化器
    test_urls = [
        "https://www.dailymaverick.co.za",
        "https://www.thecitizen.co.tz", 
        "https://www.businesslive.co.za",
        "https://httpbin.org/ip"
    ]
    
    logger.info("开始失败率优化器测试...")
    
    for i, url in enumerate(test_urls):
        logger.info(f"测试URL {i+1}: {url}")
        
        # 检查是否应该跳过
        if optimizer.should_skip_url(url):
            continue
        
        # 获取优化后的超时时间
        timeout = optimizer.get_optimized_timeout(url)
        logger.info(f"  优化超时时间: {timeout}秒")
        
        # 模拟请求（这里只是演示，实际应该使用真实的请求）
        success = True  # 假设成功
        optimizer.update_stats(success)
        
        time.sleep(1)  # 模拟请求间隔
    
    # 分析失败模式
    optimizer.analyze_failure_patterns()
    
    logger.info("优化器测试完成")
    logger.info(f"最终统计: 总请求数={optimizer.failure_stats['total_requests']}, "
                f"失败率={optimizer.failure_stats['failure_rate']:.2%}")

if __name__ == "__main__":
    main()