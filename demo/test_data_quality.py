#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量优化模块测试脚本
测试集成后的数据质量验证和清理功能
"""

import sys
import os
import json
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_quality_optimizer import data_quality_optimizer

def test_data_quality_optimizer():
    """测试数据质量优化模块的基本功能"""
    print("=== 数据质量优化模块测试 ===")
    
    # 测试用例1：正常文章数据
    test_article_1 = {
        "title": "人工智能在非洲的发展前景",
        "content": "人工智能技术正在非洲快速发展，为当地经济带来新的机遇。研究表明，AI应用在医疗、农业和教育领域具有巨大潜力。",
        "url": "https://example.com/article1",
        "source": "Example News",
        "published_date": "2024-01-15"
    }
    
    # 测试用例2：低质量文章数据
    test_article_2 = {
        "title": "点击这里查看更多",
        "content": "广告内容... 请注册会员... 联系我们...",
        "url": "https://example.com/ad",
        "source": "Advertisement",
        "published_date": "2023-12-01"
    }
    
    # 测试用例3：HTML格式内容
    test_html_content = """
    <html>
    <head>
        <title>重要新闻</title>
        <meta property="og:title" content="非洲数字化转型加速" />
        <meta property="article:published_time" content="2024-03-10" />
    </head>
    <body>
        <h1>非洲数字化转型加速</h1>
        <div class="article-content">
            <p>随着5G技术的普及，非洲各国正在加快数字化转型步伐。</p>
            <p>专家预测，到2025年，非洲互联网用户将超过10亿。</p>
        </div>
    </body>
    </html>
    """
    
    test_cases = [test_article_1, test_article_2]
    
    for i, article in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i} ---")
        print(f"原始文章: {json.dumps(article, ensure_ascii=False, indent=2)}")
        
        # 测试数据质量验证
        try:
            quality_result = data_quality_optimizer.validate_article_quality(article)
            print(f"质量验证结果: {json.dumps(quality_result, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"质量验证失败: {e}")
    
    # 测试HTML内容清理
    print(f"\n--- 测试用例 3 (HTML清理) ---")
    print(f"原始HTML内容: {test_html_content[:200]}...")
    
    try:
        cleaned_result = data_quality_optimizer.clean_content_quality(test_html_content)
        print(f"HTML内容清理结果: {json.dumps(cleaned_result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"HTML内容清理失败: {e}")

def test_integration_with_worker():
    """测试与工作节点的集成"""
    print("\n=== 工作节点集成测试 ===")
    
    # 模拟工作节点处理的数据
    sample_task_data = {
        "title": "非洲数字化转型加速",
        "content": "随着5G技术的普及，非洲各国正在加快数字化转型步伐。专家预测，到2025年，非洲互联网用户将超过10亿。",
        "url": "https://africanews.com/digital-transformation",
        "source": "African News",
        "published_date": "2024-03-10",
        "author": "John Smith",
        "language": "en"
    }
    
    print(f"模拟任务数据: {json.dumps(sample_task_data, ensure_ascii=False, indent=2)}")
    
    # 测试质量验证
    try:
        quality_result = data_quality_optimizer.validate_article_quality(sample_task_data)
        print(f"质量验证结果: {json.dumps(quality_result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"质量验证失败: {e}")

if __name__ == "__main__":
    print("开始数据质量优化模块测试...")
    
    try:
        test_data_quality_optimizer()
        test_integration_with_worker()
        print("\n=== 测试完成 ===")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()