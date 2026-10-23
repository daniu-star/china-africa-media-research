#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非洲新闻数据分析和可视化模块
用于分析爬取的非洲新闻数据，生成统计报告和可视化图表
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import re
from collections import Counter
import os
from pathlib import Path

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class AfricanNewsAnalyzer:
    """非洲新闻数据分析器"""
    
    def __init__(self, data_directory="crawler_results"):
        self.data_directory = Path(data_directory)
        self.data = []
        self.df = None
        
    def load_data(self):
        """加载所有爬虫结果数据"""
        print("正在加载爬虫数据...")
        
        # 查找所有JSON结果文件
        json_files = list(self.data_directory.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    if isinstance(file_data, list):
                        self.data.extend(file_data)
                        print(f"已加载 {json_file.name}: {len(file_data)} 条记录")
            except Exception as e:
                print(f"加载文件 {json_file} 时出错: {e}")
        
        print(f"总共加载了 {len(self.data)} 条新闻记录")
        
        # 转换为DataFrame
        if self.data:
            self.df = pd.DataFrame(self.data)
            self._preprocess_data()
        
    def _preprocess_data(self):
        """数据预处理"""
        if self.df is None or self.df.empty:
            return
            
        # 处理日期字段
        self.df['publish_date'] = pd.to_datetime(
            self.df['publish_date'], errors='coerce', format='%d %B %Y'
        )
        
        # 提取年份和月份
        self.df['year'] = self.df['publish_date'].dt.year
        self.df['month'] = self.df['publish_date'].dt.month
        
        # 处理关键词字段
        self.df['keywords'] = self.df['keywords'].apply(
            lambda x: x if isinstance(x, list) else []
        )
        
        # 提取搜索词
        self.df['search_term'] = self.df['search_term'].fillna('unknown')
        
        # 计算文章长度
        self.df['content_length'] = self.df['content'].str.len().fillna(0)
        
    def generate_summary_report(self):
        """生成数据摘要报告"""
        if self.df is None or self.df.empty:
            return {"error": "没有可用的数据"}
            
        report = {
            "report_generated_at": datetime.now().isoformat(),
            "total_articles": len(self.df),
            "date_range": {
                "earliest": self.df['publish_date'].min().isoformat() if not self.df['publish_date'].isna().all() else "N/A",
                "latest": self.df['publish_date'].max().isoformat() if not self.df['publish_date'].isna().all() else "N/A"
            },
            "search_terms_analysis": {
                "total_search_terms": self.df['search_term'].nunique(),
                "top_search_terms": self.df['search_term'].value_counts().head(10).to_dict()
            },
            "source_analysis": {
                "total_sources": self.df['source'].nunique() if 'source' in self.df.columns else 0,
                "top_sources": self.df['source'].value_counts().head(10).to_dict() if 'source' in self.df.columns else {}
            },
            "content_analysis": {
                "average_word_count": self.df['word_count'].mean() if 'word_count' in self.df.columns else 0,
                "average_content_length": self.df['content_length'].mean(),
                "articles_with_content": len(self.df[self.df['content_length'] > 0])
            },
            "temporal_analysis": {
                "articles_by_year": self.df['year'].value_counts().sort_index().to_dict(),
                "articles_by_month": self.df.groupby(['year', 'month']).size().to_dict()
            }
        }
        
        return report
    
    def analyze_keyword_trends(self):
        """分析关键词趋势"""
        if self.df is None or self.df.empty:
            return {}
            
        # 提取所有关键词
        all_keywords = []
        for keywords in self.df['keywords']:
            if isinstance(keywords, list):
                all_keywords.extend(keywords)
        
        keyword_counts = Counter(all_keywords)
        
        # 按年份分析关键词趋势
        yearly_keywords = {}
        for year in self.df['year'].unique():
            if pd.notna(year):
                year_data = self.df[self.df['year'] == year]
                year_keywords = []
                for keywords in year_data['keywords']:
                    if isinstance(keywords, list):
                        year_keywords.extend(keywords)
                yearly_keywords[int(year)] = Counter(year_keywords)
        
        return {
            "total_unique_keywords": len(keyword_counts),
            "top_keywords": dict(keyword_counts.most_common(20)),
            "yearly_trends": yearly_keywords
        }
    
    def create_visualizations(self, output_dir="analysis_results"):
        """创建可视化图表"""
        if self.df is None or self.df.empty:
            print("没有数据可用于可视化")
            return
            
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 1. 按年份的文章数量分布
        plt.figure(figsize=(12, 6))
        yearly_counts = self.df['year'].value_counts().sort_index()
        yearly_counts.plot(kind='bar')
        plt.title('非洲新闻文章按年份分布')
        plt.xlabel('年份')
        plt.ylabel('文章数量')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path / 'yearly_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. 搜索词分布
        plt.figure(figsize=(12, 8))
        search_term_counts = self.df['search_term'].value_counts().head(15)
        search_term_counts.plot(kind='pie', autopct='%1.1f%%')
        plt.title('搜索词分布')
        plt.ylabel('')
        plt.tight_layout()
        plt.savefig(output_path / 'search_term_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. 关键词词云数据准备
        keyword_counts = Counter()
        for keywords in self.df['keywords']:
            if isinstance(keywords, list):
                keyword_counts.update(keywords)
        
        # 保存关键词数据用于词云
        with open(output_path / 'keyword_frequencies.json', 'w', encoding='utf-8') as f:
            json.dump(dict(keyword_counts.most_common(50)), f, ensure_ascii=False, indent=2)
        
        # 4. 文章长度分布
        plt.figure(figsize=(10, 6))
        plt.hist(self.df['content_length'], bins=50, alpha=0.7, color='skyblue')
        plt.title('文章内容长度分布')
        plt.xlabel('内容长度（字符）')
        plt.ylabel('文章数量')
        plt.tight_layout()
        plt.savefig(output_path / 'content_length_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 5. 月度趋势分析（如果数据足够）
        if len(self.df['year'].unique()) > 1:
            monthly_data = self.df.groupby(['year', 'month']).size().reset_index(name='count')
            monthly_data['date'] = pd.to_datetime(
                monthly_data['year'].astype(str) + '-' + monthly_data['month'].astype(str) + '-01'
            )
            
            plt.figure(figsize=(15, 6))
            plt.plot(monthly_data['date'], monthly_data['count'], marker='o')
            plt.title('月度文章数量趋势')
            plt.xlabel('日期')
            plt.ylabel('文章数量')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(output_path / 'monthly_trend.png', dpi=300, bbox_inches='tight')
            plt.close()
    
    def export_analysis_results(self, output_dir="analysis_results"):
        """导出分析结果"""
        if self.df is None or self.df.empty:
            print("没有数据可用于分析")
            return
            
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 生成报告
        summary_report = self.generate_summary_report()
        keyword_analysis = self.analyze_keyword_trends()
        
        # 保存报告
        with open(output_path / 'summary_report.json', 'w', encoding='utf-8') as f:
            json.dump(summary_report, f, ensure_ascii=False, indent=2)
        
        with open(output_path / 'keyword_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(keyword_analysis, f, ensure_ascii=False, indent=2)
        
        # 创建可视化
        self.create_visualizations(output_dir)
        
        # 导出数据统计
        stats_df = pd.DataFrame({
            'metric': [
                '总文章数', '平均文章长度', '唯一搜索词数', 
                '唯一关键词数', '数据覆盖年份'
            ],
            'value': [
                len(self.df),
                self.df['content_length'].mean(),
                self.df['search_term'].nunique(),
                len(keyword_analysis.get('total_unique_keywords', 0)),
                len(self.df['year'].unique())
            ]
        })
        
        stats_df.to_csv(output_path / 'basic_statistics.csv', index=False, encoding='utf-8-sig')
        
        print(f"分析结果已导出到 {output_path}")
        
        return {
            "summary_report": summary_report,
            "keyword_analysis": keyword_analysis,
            "output_directory": str(output_path)
        }

def main():
    """主函数"""
    analyzer = AfricanNewsAnalyzer()
    
    # 加载数据
    analyzer.load_data()
    
    if analyzer.df is None or analyzer.df.empty:
        print("未找到可用的爬虫数据")
        return
    
    # 导出分析结果
    results = analyzer.export_analysis_results()
    
    # 打印简要报告
    print("\n=== 非洲新闻数据分析报告 ===")
    print(f"总文章数: {results['summary_report']['total_articles']}")
    print(f"数据覆盖年份: {len(results['summary_report']['temporal_analysis']['articles_by_year'])}")
    print(f"唯一搜索词: {results['summary_report']['search_terms_analysis']['total_search_terms']}")
    print(f"唯一关键词: {results['keyword_analysis']['total_unique_keywords']}")
    print(f"分析结果保存到: {results['output_directory']}")

if __name__ == "__main__":
    main()