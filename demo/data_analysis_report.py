#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析和可视化方案系统
生成全面的数据分析报告和可视化方案
"""

import json
import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from collections import Counter


class DataAnalysisReport:
    """数据分析报告生成器"""
    
    def __init__(self, data_dir: str = "data", db_path: str = "data/articles.db"):
        self.data_dir = data_dir
        self.db_path = db_path
        
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 基本统计
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT country) FROM articles")
            unique_countries = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT category) FROM articles")
            unique_categories = cursor.fetchone()[0]
            
            cursor.execute("SELECT MIN(year), MAX(year) FROM articles WHERE year IS NOT NULL")
            year_range = cursor.fetchone()
            min_year, max_year = year_range if year_range[0] else (None, None)
            
            # 质量分布
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN quality_score >= 0.8 THEN '优秀'
                        WHEN quality_score >= 0.6 THEN '良好'
                        WHEN quality_score >= 0.4 THEN '一般'
                        ELSE '较差'
                    END as quality_level,
                    COUNT(*) as count
                FROM articles 
                GROUP BY quality_level
                ORDER BY count DESC
            """)
            quality_distribution = dict(cursor.fetchall())
            
            # 国家分布
            cursor.execute("""
                SELECT country, COUNT(*) as count 
                FROM articles 
                WHERE country != '未知'
                GROUP BY country 
                ORDER BY count DESC 
                LIMIT 10
            """)
            country_distribution = dict(cursor.fetchall())
            
            # 类别分布
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM articles 
                WHERE category != '其他'
                GROUP BY category 
                ORDER BY count DESC
            """)
            category_distribution = dict(cursor.fetchall())
            
            # 年份分布
            cursor.execute("""
                SELECT year, COUNT(*) as count 
                FROM articles 
                WHERE year IS NOT NULL
                GROUP BY year 
                ORDER BY year
            """)
            year_distribution = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_articles': total_articles,
                'unique_countries': unique_countries,
                'unique_categories': unique_categories,
                'year_range': {'min': min_year, 'max': max_year},
                'quality_distribution': quality_distribution,
                'country_distribution': country_distribution,
                'category_distribution': category_distribution,
                'year_distribution': year_distribution
            }
            
        except Exception as e:
            print(f"获取数据库统计信息时出错: {e}")
            return {}
    
    def analyze_data_completeness(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """分析数据完整性"""
        
        total_articles = stats.get('total_articles', 0)
        
        completeness_metrics = {
            'total_count': total_articles,
            'target_count': 20000,
            'completion_rate': (total_articles / 20000) * 100 if total_articles > 0 else 0,
            'remaining_count': max(0, 20000 - total_articles),
            'data_gaps': []
        }
        
        # 检查数据缺口
        if total_articles < 10000:
            completeness_metrics['data_gaps'].append("数据总量不足，需要大量补充")
        
        year_distribution = stats.get('year_distribution', {})
        if year_distribution:
            recent_years = [year for year in year_distribution.keys() if year and year >= 2020]
            if len(recent_years) < 3:
                completeness_metrics['data_gaps'].append("近期年份数据不足")
        
        country_distribution = stats.get('country_distribution', {})
        if len(country_distribution) < 5:
            completeness_metrics['data_gaps'].append("国家覆盖范围有限")
        
        return completeness_metrics
    
    def generate_visualization_plan(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """生成可视化方案"""
        
        visualization_plan = {
            'charts': [],
            'dashboards': [],
            'reports': []
        }
        
        # 基础图表
        visualization_plan['charts'].extend([
            {
                'type': '饼图',
                'title': '数据质量分布',
                'data_source': 'quality_distribution',
                'description': '显示优秀、良好、一般、较差质量文章的比例'
            },
            {
                'type': '柱状图', 
                'title': '国家分布统计',
                'data_source': 'country_distribution',
                'description': '显示各非洲国家文章数量分布'
            },
            {
                'type': '折线图',
                'title': '年份趋势分析',
                'data_source': 'year_distribution', 
                'description': '显示2010-2025年文章数量变化趋势'
            },
            {
                'type': '环形图',
                'title': '类别分布',
                'data_source': 'category_distribution',
                'description': '显示经济框架、技术数字化等类别的分布'
            }
        ])
        
        # 仪表板设计
        visualization_plan['dashboards'].extend([
            {
                'name': '数据概览仪表板',
                'components': [
                    '数据总量统计卡片',
                    '质量分布饼图',
                    '国家分布柱状图',
                    '年份趋势折线图'
                ],
                'purpose': '提供数据整体情况的快速概览'
            },
            {
                'name': '深度分析仪表板',
                'components': [
                    '关键词热度词云',
                    '数据完整性雷达图',
                    '时间序列分析',
                    '相关性热力图'
                ],
                'purpose': '提供深入的数据分析和洞察'
            }
        ])
        
        # 报告设计
        visualization_plan['reports'].extend([
            {
                'name': '数据质量报告',
                'sections': [
                    '数据完整性分析',
                    '质量评分分布',
                    '数据缺口识别',
                    '改进建议'
                ],
                'frequency': '每月'
            },
            {
                'name': '趋势分析报告',
                'sections': [
                    '年度趋势分析',
                    '国家对比分析',
                    '类别热点分析', 
                    '预测和建议'
                ],
                'frequency': '每季度'
            }
        ])
        
        return visualization_plan
    
    def create_analysis_recommendations(self, stats: Dict[str, Any], 
                                       completeness: Dict[str, Any]) -> List[str]:
        """创建分析建议"""
        
        recommendations = []
        
        # 基于数据完整性的建议
        completion_rate = completeness.get('completion_rate', 0)
        if completion_rate < 50:
            recommendations.append("数据收集优先级：重点补充缺失数据，特别是近期年份数据")
        elif completion_rate < 80:
            recommendations.append("数据优化：在现有基础上提高数据质量和多样性")
        else:
            recommendations.append("数据分析重点：深入挖掘数据价值，进行趋势和模式分析")
        
        # 基于数据分布的建议
        country_distribution = stats.get('country_distribution', {})
        if len(country_distribution) < 8:
            recommendations.append("扩大国家覆盖：增加对数据较少国家的关注")
        
        year_distribution = stats.get('year_distribution', {})
        if year_distribution:
            recent_count = sum(count for year, count in year_distribution.items() 
                             if year and year >= 2020)
            if recent_count < 1000:
                recommendations.append("加强近期数据收集：重点关注2020年后的数据")
        
        # 分析技术建议
        recommendations.extend([
            "使用时间序列分析识别发展趋势和周期性模式",
            "应用文本挖掘技术提取关键词和主题",
            "建立数据质量监控体系，定期评估数据完整性",
            "开发交互式可视化工具，支持动态数据探索",
            "建立数据预警机制，及时发现数据异常和缺口"
        ])
        
        return recommendations
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合分析报告"""
        
        # 获取统计数据
        stats = self.get_database_stats()
        
        # 分析数据完整性
        completeness = self.analyze_data_completeness(stats)
        
        # 生成可视化方案
        visualization_plan = self.generate_visualization_plan(stats)
        
        # 创建分析建议
        recommendations = self.create_analysis_recommendations(stats, completeness)
        
        # 综合报告
        comprehensive_report = {
            'generated_at': datetime.now().isoformat(),
            'executive_summary': {
                'total_data_points': stats.get('total_articles', 0),
                'completion_rate': completeness.get('completion_rate', 0),
                'data_quality_overview': stats.get('quality_distribution', {}),
                'key_insights': [
                    f"数据收集完成度: {completeness.get('completion_rate', 0):.1f}%",
                    f"覆盖国家数量: {stats.get('unique_countries', 0)}",
                    f"数据年份范围: {stats.get('year_range', {}).get('min', 'N/A')}-{stats.get('year_range', {}).get('max', 'N/A')}"
                ]
            },
            'detailed_analysis': {
                'data_statistics': stats,
                'completeness_analysis': completeness,
                'data_gaps_identified': completeness.get('data_gaps', [])
            },
            'visualization_strategy': visualization_plan,
            'recommendations_and_next_steps': recommendations,
            'implementation_timeline': [
                {
                    'phase': '立即执行',
                    'tasks': [
                        '建立数据质量监控',
                        '开发基础可视化图表',
                        '识别关键数据缺口'
                    ],
                    'duration': '1-2周'
                },
                {
                    'phase': '短期目标',
                    'tasks': [
                        '完善数据收集策略',
                        '开发交互式仪表板',
                        '建立定期报告机制'
                    ],
                    'duration': '1个月'
                },
                {
                    'phase': '中长期规划',
                    'tasks': [
                        '实现高级分析功能',
                        '建立预测模型',
                        '开发自动化报告系统'
                    ],
                    'duration': '3-6个月'
                }
            ]
        }
        
        return comprehensive_report
    
    def save_analysis_report(self, report: Dict[str, Any]) -> str:
        """保存分析报告"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.data_dir, f"data_analysis_report_{timestamp}.json")
        
        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report_file


def main():
    """主函数"""
    
    print("=" * 60)
    print("数据分析和可视化方案系统")
    print("=" * 60)
    
    analyzer = DataAnalysisReport()
    
    # 生成综合分析报告
    print("\n1. 生成综合分析报告...")
    report = analyzer.generate_comprehensive_report()
    
    # 保存报告
    print("\n2. 保存分析报告...")
    report_file = analyzer.save_analysis_report(report)
    
    # 显示关键信息
    summary = report['executive_summary']
    print(f"\n关键统计信息:")
    print(f"  总数据点: {summary['total_data_points']}")
    print(f"  完成度: {summary['completion_rate']:.1f}%")
    print(f"  质量分布: {summary['data_quality_overview']}")
    
    print(f"\n分析报告已保存到: {report_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()