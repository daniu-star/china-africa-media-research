"""
20000条高质量数据抓取策略方案
基于现有12,129条数据，制定补充7,871条高质量数据的策略
"""

import json
import os
from datetime import datetime, timedelta
import random

class DataCrawlingStrategy:
    def __init__(self, target_total=20000, current_data_count=12129):
        self.target_total = target_total
        self.current_data_count = current_data_count
        self.needed_data_count = target_total - current_data_count
        
        # 时间范围配置
        self.start_year = 2010
        self.end_year = 2025
        self.years_range = list(range(self.start_year, self.end_year + 1))
        
        # 关键词策略
        self.keyword_categories = {
            "economic_framework": {
                "keywords": ["investment", "economy", "trade", "business", "finance", "market"],
                "weight": 0.4
            },
            "technology_digital": {
                "keywords": ["big data", "data analytics", "digital", "technology", "innovation", "AI"],
                "weight": 0.3
            },
            "infrastructure": {
                "keywords": ["infrastructure", "construction", "development", "project", "transport"],
                "weight": 0.2
            },
            "social_development": {
                "keywords": ["education", "healthcare", "poverty", "employment", "social"],
                "weight": 0.1
            }
        }
        
        # 非洲国家列表
        self.african_countries = [
            "Egypt", "Nigeria", "South Africa", "Kenya", "Ethiopia", "Ghana",
            "Tanzania", "Uganda", "Algeria", "Morocco", "Angola", "Mozambique",
            "Zambia", "Zimbabwe", "Senegal", "Ivory Coast", "Cameroon", "Tunisia"
        ]
        
        # 数据源优先级
        self.data_sources_priority = [
            "english.ahram.org.eg",  # 埃及金字塔报
            "guardian.ng",           # 尼日利亚卫报
            "allafrica.com",         # 全非洲网
            "africanews.com",        # 非洲新闻
            "businessdailyafrica.com", # 非洲商业日报
            "theeastafrican.co.ke",  # 东非人报
            "mg.co.za",              # 南非邮卫报
            "premiumtimesng.com"      # 尼日利亚高级时报
        ]
    
    def calculate_distribution_strategy(self):
        """计算数据分布策略"""
        
        # 按年份分布
        years_distribution = {}
        total_years = len(self.years_range)
        base_per_year = self.needed_data_count // total_years
        
        # 近5年权重更高
        recent_years = self.years_range[-5:]
        for year in self.years_range:
            if year in recent_years:
                years_distribution[year] = int(base_per_year * 1.5)
            else:
                years_distribution[year] = base_per_year
        
        # 调整总数
        total_distributed = sum(years_distribution.values())
        if total_distributed < self.needed_data_count:
            # 将剩余数据分配给最近年份
            remaining = self.needed_data_count - total_distributed
            years_distribution[2025] += remaining
        
        # 按关键词类别分布
        keywords_distribution = {}
        for category, config in self.keyword_categories.items():
            keywords_distribution[category] = {
                "count": int(self.needed_data_count * config["weight"]),
                "keywords": config["keywords"],
                "weight": config["weight"]  # 添加weight字段
            }
        
        return {
            "total_needed": self.needed_data_count,
            "years_distribution": years_distribution,
            "keywords_distribution": keywords_distribution,
            "countries_focus": self.african_countries[:8],  # 重点8个国家
            "sources_priority": self.data_sources_priority
        }
    
    def generate_crawling_tasks(self):
        """生成具体的抓取任务"""
        
        strategy = self.calculate_distribution_strategy()
        tasks = []
        task_id_counter = 1
        
        # 按年份和关键词生成任务
        for year, year_count in strategy["years_distribution"].items():
            for category, cat_config in strategy["keywords_distribution"].items():
                # 计算该年份该类别的任务数量
                category_year_count = int(year_count * cat_config["weight"])
                
                # 每个任务抓取10-20条数据
                tasks_per_category = max(1, category_year_count // 15)
                
                for task_num in range(tasks_per_category):
                    # 选择关键词
                    keyword = random.choice(cat_config["keywords"])
                    
                    # 选择国家
                    country = random.choice(strategy["countries_focus"])
                    
                    # 选择数据源
                    source = random.choice(strategy["sources_priority"])
                    
                    task = {
                        "task_id": f"20000_strategy_{year}_{category}_{task_num}",
                        "keyword": f"{keyword} {country}",
                        "category": category,
                        "year": year,
                        "country": country,
                        "source_preference": source,
                        "target_count": random.randint(10, 20),
                        "priority": "high" if year >= 2020 else "medium",
                        "created_at": datetime.now().isoformat(),
                        "status": "pending"
                    }
                    tasks.append(task)
                    task_id_counter += 1
        
        return tasks
    
    def get_quality_requirements(self):
        """获取数据质量要求"""
        return {
            "min_content_length": 500,  # 最小内容长度
            "max_content_length": 5000, # 最大内容长度
            "required_fields": ["title", "content", "source", "publish_date"],
            "language_requirements": ["en", "fr"],  # 英语和法语
            "quality_threshold": 0.7,  # 质量阈值
            "duplicate_threshold": 0.8,  # 重复度阈值
            "login_page_filter": True,  # 启用登录页面过滤
            "navigation_page_filter": True  # 启用导航页面过滤
        }
    
    def get_monitoring_metrics(self):
        """获取监控指标"""
        return {
            "progress_tracking": {
                "daily_target": 500,  # 每日目标
                "weekly_target": 3500, # 每周目标
                "completion_eta": "14 days"  # 预计完成时间
            },
            "quality_metrics": {
                "acceptable_quality_rate": 0.85,  # 可接受质量率
                "target_quality_score": 0.8,     # 目标质量分数
                "rejection_rate_threshold": 0.15  # 拒绝率阈值
            },
            "system_metrics": {
                "worker_utilization_target": 0.8,  # 工作节点利用率
                "error_rate_threshold": 0.05,      # 错误率阈值
                "throughput_target": 50            # 每分钟处理目标
            }
        }

def main():
    """主函数 - 生成20000条数据抓取策略"""
    
    strategy = DataCrawlingStrategy()
    
    # 计算策略
    distribution_strategy = strategy.calculate_distribution_strategy()
    
    # 生成任务
    crawling_tasks = strategy.generate_crawling_tasks()
    
    # 输出策略报告
    report = {
        "strategy_overview": {
            "current_data_count": strategy.current_data_count,
            "target_total": strategy.target_total,
            "needed_data_count": strategy.needed_data_count,
            "time_range": f"{strategy.start_year}-{strategy.end_year}",
            "estimated_completion_time": "14 days"
        },
        "distribution_strategy": distribution_strategy,
        "quality_requirements": strategy.get_quality_requirements(),
        "monitoring_metrics": strategy.get_monitoring_metrics(),
        "total_tasks_generated": len(crawling_tasks),
        "sample_tasks": crawling_tasks[:5]  # 显示前5个任务作为示例
    }
    
    # 保存策略文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    strategy_file = f"data/20000_data_strategy_{timestamp}.json"
    
    os.makedirs("data", exist_ok=True)
    
    with open(strategy_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 保存任务文件
    tasks_file = f"data/20000_crawling_tasks_{timestamp}.json"
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(crawling_tasks, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print("20000条高质量数据抓取策略报告")
    print("=" * 60)
    print(f"当前数据量: {strategy.current_data_count:,} 条")
    print(f"目标数据量: {strategy.target_total:,} 条")
    print(f"需要补充: {strategy.needed_data_count:,} 条")
    print(f"时间范围: {strategy.start_year}-{strategy.end_year}")
    print(f"生成任务数: {len(crawling_tasks)} 个")
    print(f"预计完成时间: 14天")
    print(f"策略文件: {strategy_file}")
    print(f"任务文件: {tasks_file}")
    print("=" * 60)
    
    # 显示分布详情
    print("\n数据分布策略:")
    for year, count in distribution_strategy["years_distribution"].items():
        print(f"  {year}年: {count}条")
    
    print("\n关键词类别分布:")
    for category, config in distribution_strategy["keywords_distribution"].items():
        print(f"  {category}: {config['count']}条")
    
    print("\n重点国家:")
    print(f"  {', '.join(distribution_strategy['countries_focus'])}")
    
    return report

if __name__ == "__main__":
    main()