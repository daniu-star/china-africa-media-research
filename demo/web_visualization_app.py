#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非洲新闻数据Web可视化应用
基于Flask的交互式数据可视化界面
"""

from flask import Flask, render_template, jsonify, request, send_file
import json
import pandas as pd
import numpy as np
from datetime import datetime
import os
from pathlib import Path
from data_analysis_visualization import AfricanNewsAnalyzer

app = Flask(__name__)

# 全局分析器实例
analyzer = AfricanNewsAnalyzer()

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/load_data')
def load_data():
    """加载数据API"""
    try:
        analyzer.load_data()
        if analyzer.df is None or analyzer.df.empty:
            return jsonify({"success": False, "message": "未找到可用的数据"})
        
        return jsonify({
            "success": True, 
            "message": f"成功加载 {len(analyzer.df)} 条记录",
            "data_count": len(analyzer.df)
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/summary')
def get_summary():
    """获取数据摘要"""
    if analyzer.df is None or analyzer.df.empty:
        return jsonify({"error": "请先加载数据"})
    
    summary = analyzer.generate_summary_report()
    return jsonify(summary)

@app.route('/api/keyword_analysis')
def get_keyword_analysis():
    """获取关键词分析"""
    if analyzer.df is None or analyzer.df.empty:
        return jsonify({"error": "请先加载数据"})
    
    analysis = analyzer.analyze_keyword_trends()
    return jsonify(analysis)

@app.route('/api/temporal_analysis')
def get_temporal_analysis():
    """获取时间序列分析"""
    if analyzer.df is None or analyzer.df.empty:
        return jsonify({"error": "请先加载数据"})
    
    # 按年份统计
    yearly_data = analyzer.df['year'].value_counts().sort_index()
    yearly_data = yearly_data[yearly_data.index.notna()]
    
    # 按月份统计（最近2年）
    current_year = datetime.now().year
    recent_data = analyzer.df[analyzer.df['year'] >= current_year - 2]
    monthly_data = recent_data.groupby(['year', 'month']).size().reset_index(name='count')
    monthly_data['date'] = pd.to_datetime(
        monthly_data['year'].astype(str) + '-' + monthly_data['month'].astype(str) + '-01'
    )
    
    return jsonify({
        "yearly": {
            "labels": yearly_data.index.astype(int).tolist(),
            "values": yearly_data.values.tolist()
        },
        "monthly": {
            "dates": monthly_data['date'].dt.strftime('%Y-%m').tolist(),
            "values": monthly_data['count'].tolist()
        }
    })

@app.route('/api/search_term_analysis')
def get_search_term_analysis():
    """获取搜索词分析"""
    if analyzer.df is None or analyzer.df.empty:
        return jsonify({"error": "请先加载数据"})
    
    search_terms = analyzer.df['search_term'].value_counts().head(15)
    
    return jsonify({
        "labels": search_terms.index.tolist(),
        "values": search_terms.values.tolist()
    })

@app.route('/api/content_analysis')
def get_content_analysis():
    """获取内容分析"""
    if analyzer.df is None or analyzer.df.empty:
        return jsonify({"error": "请先加载数据"})
    
    # 文章长度分布
    content_lengths = analyzer.df['content_length']
    
    return jsonify({
        "average_length": content_lengths.mean(),
        "median_length": content_lengths.median(),
        "max_length": content_lengths.max(),
        "min_length": content_lengths.min(),
        "articles_with_content": len(analyzer.df[analyzer.df['content_length'] > 0])
    })

@app.route('/api/export_analysis')
def export_analysis():
    """导出完整分析报告"""
    if analyzer.df is None or analyzer.df.empty:
        return jsonify({"error": "请先加载数据"})
    
    try:
        results = analyzer.export_analysis_results()
        return jsonify({
            "success": True,
            "message": "分析报告已导出",
            "output_directory": results['output_directory']
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/word_cloud_data')
def get_word_cloud_data():
    """获取词云数据"""
    if analyzer.df is None or analyzer.df.empty:
        return jsonify({"error": "请先加载数据"})
    
    # 提取关键词频率
    keyword_counts = {}
    for keywords in analyzer.df['keywords']:
        if isinstance(keywords, list):
            for keyword in keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
    
    # 转换为词云格式
    word_cloud_data = [{"text": k, "value": v} for k, v in keyword_counts.items() if v >= 2]
    word_cloud_data.sort(key=lambda x: x["value"], reverse=True)
    
    return jsonify(word_cloud_data[:50])  # 返回前50个关键词

@app.route('/api/advanced_analysis')
def get_advanced_analysis():
    """获取高级分析数据"""
    if analyzer.df is None or analyzer.df.empty:
        return jsonify({"error": "请先加载数据"})
    
    # 关键词共现分析
    co_occurrence = {}
    for keywords in analyzer.df['keywords']:
        if isinstance(keywords, list) and len(keywords) >= 2:
            for i in range(len(keywords)):
                for j in range(i+1, len(keywords)):
                    pair = tuple(sorted([keywords[i], keywords[j]]))
                    co_occurrence[pair] = co_occurrence.get(pair, 0) + 1
    
    # 搜索词与关键词关联分析
    search_keyword_relation = {}
    for _, row in analyzer.df.iterrows():
        search_term = row['search_term']
        keywords = row['keywords'] if isinstance(row['keywords'], list) else []
        
        if search_term not in search_keyword_relation:
            search_keyword_relation[search_term] = {}
        
        for keyword in keywords:
            search_keyword_relation[search_term][keyword] = search_keyword_relation[search_term].get(keyword, 0) + 1
    
    return jsonify({
        "co_occurrence": co_occurrence,
        "search_keyword_relation": search_keyword_relation
    })

# 静态文件服务
@app.route('/static/<path:filename>')
def static_files(filename):
    """静态文件服务"""
    return send_file(Path('static') / filename)

# 模板目录
@app.route('/templates/<path:filename>')
def template_files(filename):
    """模板文件服务"""
    return send_file(Path('templates') / filename)

def create_static_files():
    """创建必要的静态文件目录和文件"""
    static_dir = Path('static')
    static_dir.mkdir(exist_ok=True)
    
    # 创建CSS文件
    css_content = """
    body {
        font-family: 'Microsoft YaHei', Arial, sans-serif;
        margin: 0;
        padding: 20px;
        background-color: #f5f5f5;
    }
    
    .container {
        max-width: 1200px;
        margin: 0 auto;
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .chart-container {
        height: 400px;
        margin: 20px 0;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }
    
    .stat-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 6px;
        text-align: center;
    }
    
    .stat-value {
        font-size: 24px;
        font-weight: bold;
        color: #007bff;
    }
    
    .stat-label {
        font-size: 14px;
        color: #666;
    }
    """
    
    with open(static_dir / 'style.css', 'w', encoding='utf-8') as f:
        f.write(css_content)

if __name__ == '__main__':
    # 创建静态文件
    create_static_files()
    
    # 运行应用
    print("启动非洲新闻数据可视化应用...")
    print("访问地址: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)