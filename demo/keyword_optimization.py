#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词策略优化系统
用于分析和优化数据抓取的关键词策略，提高数据相关性
"""

import json
import os
import re
from collections import Counter
from typing import Dict, List, Tuple, Any
from datetime import datetime


class KeywordOptimizer:
    """关键词优化器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.keyword_stats = {}
        self.category_mapping = {
            'economic_framework': '经济框架',
            'technology_digital': '技术数字化', 
            'infrastructure': '基础设施',
            'social_development': '社会发展'
        }
        
    def load_existing_data(self) -> Dict[str, Any]:
        """加载现有数据进行分析"""
        
        data_files = []
        if os.path.exists(self.data_dir):
            for file in os.listdir(self.data_dir):
                if file.endswith('.json') and 'crawling_tasks' in file:
                    data_files.append(os.path.join(self.data_dir, file))
        
        all_keywords = []
        keyword_categories = {}
        
        for file_path in data_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if isinstance(data, list):
                    for task in data:
                        if isinstance(task, dict):
                            keyword = task.get('keyword', '')
                            category = task.get('category', '')
                            
                            if keyword:
                                all_keywords.append(keyword)
                                if category not in keyword_categories:
                                    keyword_categories[category] = []
                                keyword_categories[category].append(keyword)
            except Exception as e:
                print(f"加载文件 {file_path} 时出错: {e}")
        
        return {
            'all_keywords': all_keywords,
            'keyword_categories': keyword_categories,
            'total_keywords': len(all_keywords),
            'unique_keywords': len(set(all_keywords))
        }
    
    def analyze_keyword_effectiveness(self, keywords_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析关键词有效性"""
        
        all_keywords = keywords_data['all_keywords']
        keyword_categories = keywords_data['keyword_categories']
        
        # 关键词频率分析
        keyword_freq = Counter(all_keywords)
        
        # 关键词长度分析
        avg_length = sum(len(kw) for kw in all_keywords) / len(all_keywords) if all_keywords else 0
        
        # 关键词多样性分析
        diversity_score = len(set(all_keywords)) / len(all_keywords) if all_keywords else 0
        
        # 按类别分析
        category_analysis = {}
        for category, keywords in keyword_categories.items():
            cat_keywords = keywords
            cat_freq = Counter(cat_keywords)
            
            category_analysis[category] = {
                'total_keywords': len(cat_keywords),
                'unique_keywords': len(set(cat_keywords)),
                'diversity_score': len(set(cat_keywords)) / len(cat_keywords) if cat_keywords else 0,
                'top_keywords': cat_freq.most_common(10),
                'avg_length': sum(len(kw) for kw in cat_keywords) / len(cat_keywords) if cat_keywords else 0
            }
        
        return {
            'total_keywords': len(all_keywords),
            'unique_keywords': len(set(all_keywords)),
            'diversity_score': diversity_score,
            'avg_keyword_length': avg_length,
            'top_keywords': keyword_freq.most_common(20),
            'category_analysis': category_analysis
        }
    
    def generate_optimization_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        
        recommendations = []
        
        # 多样性建议
        if analysis['diversity_score'] < 0.3:
            recommendations.append("关键词多样性较低，建议增加更多独特关键词")
        elif analysis['diversity_score'] < 0.6:
            recommendations.append("关键词多样性中等，可进一步优化")
        else:
            recommendations.append("关键词多样性良好，继续保持")
        
        # 关键词长度建议
        if analysis['avg_keyword_length'] < 3:
            recommendations.append("关键词过短，建议使用更具体的关键词组合")
        elif analysis['avg_keyword_length'] > 10:
            recommendations.append("关键词过长，建议简化以提高搜索效果")
        
        # 类别分布建议
        category_distribution = {}
        for category, cat_analysis in analysis['category_analysis'].items():
            category_distribution[category] = cat_analysis['total_keywords']
        
        total_keywords = analysis['total_keywords']
        if total_keywords > 0:
            for category, count in category_distribution.items():
                percentage = (count / total_keywords) * 100
                if percentage < 10:
                    recommendations.append(f"{self.category_mapping.get(category, category)}类别关键词数量较少({percentage:.1f}%)，建议增加相关关键词")
        
        # 关键词质量建议
        top_keywords = analysis['top_keywords']
        if top_keywords:
            most_common_keyword, freq = top_keywords[0]
            if freq > len(top_keywords) * 0.1:  # 如果最高频关键词占比过高
                recommendations.append(f"关键词'{most_common_keyword}'使用过于频繁，建议增加更多相关变体")
        
        recommendations.append("建议定期更新关键词策略以适应数据变化")
        recommendations.append("考虑使用长尾关键词提高数据相关性")
        recommendations.append("结合具体国家和年份进行关键词优化")
        
        return recommendations
    
    def create_optimized_keyword_strategy(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """创建优化的关键词策略"""
        
        # 基于分析结果生成优化策略
        optimized_strategy = {
            'generated_at': datetime.now().isoformat(),
            'current_status': analysis,
            'optimization_targets': {},
            'recommended_keywords': {},
            'implementation_plan': []
        }
        
        # 设置优化目标
        optimized_strategy['optimization_targets'] = {
            'diversity_score': 0.7,  # 目标多样性分数
            'avg_keyword_length': 5,  # 目标平均长度
            'min_category_coverage': 15  # 每个类别最小关键词数量百分比
        }
        
        # 为每个类别推荐新关键词
        african_countries = ['埃及', '尼日利亚', '南非', '肯尼亚', '加纳', '坦桑尼亚', '埃塞俄比亚', '乌干达']
        
        category_keywords = {
            'economic_framework': {
                'base_keywords': ['经济', '发展', '增长', '投资', '贸易', 'GDP', '财政', '预算'],
                'combinations': ['经济政策', '经济发展', '经济增长', '投资环境', '贸易关系', '财政预算']
            },
            'technology_digital': {
                'base_keywords': ['技术', '数字', '互联网', 'AI', '人工智能', '区块链', '5G', '创新'],
                'combinations': ['技术创新', '数字化转型', '互联网发展', '人工智能应用', '区块链技术']
            },
            'infrastructure': {
                'base_keywords': ['基础设施', '建设', '交通', '能源', '电力', '水利', '通信', '港口'],
                'combinations': ['基础设施建设', '交通网络', '能源发展', '电力供应', '通信设施']
            },
            'social_development': {
                'base_keywords': ['社会', '发展', '教育', '医疗', '健康', '文化', '就业', '扶贫'],
                'combinations': ['社会发展', '教育改革', '医疗健康', '文化发展', '就业机会']
            }
        }
        
        # 生成推荐关键词
        for category, keywords_info in category_keywords.items():
            recommended = []
            
            # 基础关键词与国家组合
            for base in keywords_info['base_keywords']:
                for country in african_countries:
                    recommended.append(f"{base} {country}")
            
            # 组合关键词
            recommended.extend(keywords_info['combinations'])
            
            # 添加年份组合
            for year in range(2010, 2026):
                for base in keywords_info['base_keywords'][:3]:  # 每个类别取前3个基础关键词
                    recommended.append(f"{base} {year}")
            
            optimized_strategy['recommended_keywords'][category] = list(set(recommended))[:50]  # 限制每个类别50个
        
        # 实施计划
        optimized_strategy['implementation_plan'] = [
            "1. 逐步替换低效关键词",
            "2. 增加长尾关键词使用",
            "3. 优化关键词与国家/年份组合",
            "4. 定期监控关键词效果",
            "5. 根据数据质量调整策略"
        ]
        
        return optimized_strategy
    
    def save_optimization_report(self, analysis: Dict[str, Any], 
                                recommendations: List[str],
                                optimized_strategy: Dict[str, Any]) -> str:
        """保存优化报告"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.data_dir, f"keyword_optimization_report_{timestamp}.json")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'analysis_results': analysis,
            'optimization_recommendations': recommendations,
            'optimized_strategy': optimized_strategy,
            'summary': {
                'current_diversity_score': analysis.get('diversity_score', 0),
                'current_avg_length': analysis.get('avg_keyword_length', 0),
                'total_keywords_analyzed': analysis.get('total_keywords', 0),
                'unique_keywords_found': analysis.get('unique_keywords', 0)
            }
        }
        
        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report_file


def main():
    """主函数"""
    
    print("=" * 60)
    print("关键词策略优化系统")
    print("=" * 60)
    
    optimizer = KeywordOptimizer()
    
    # 1. 加载现有数据
    print("\n1. 加载现有关键词数据...")
    keywords_data = optimizer.load_existing_data()
    print(f"   总关键词数: {keywords_data['total_keywords']}")
    print(f"   唯一关键词数: {keywords_data['unique_keywords']}")
    
    # 2. 分析关键词有效性
    print("\n2. 分析关键词有效性...")
    analysis = optimizer.analyze_keyword_effectiveness(keywords_data)
    print(f"   多样性分数: {analysis['diversity_score']:.3f}")
    print(f"   平均关键词长度: {analysis['avg_keyword_length']:.1f}")
    
    # 3. 生成优化建议
    print("\n3. 生成优化建议...")
    recommendations = optimizer.generate_optimization_recommendations(analysis)
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    # 4. 创建优化策略
    print("\n4. 创建优化关键词策略...")
    optimized_strategy = optimizer.create_optimized_keyword_strategy(analysis)
    
    # 5. 保存报告
    print("\n5. 保存优化报告...")
    report_file = optimizer.save_optimization_report(analysis, recommendations, optimized_strategy)
    
    print(f"\n优化报告已保存到: {report_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()