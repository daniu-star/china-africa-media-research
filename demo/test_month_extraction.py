#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试月份细化功能"""

from content_extraction_optimizer import DateParser

def test_month_extraction():
    """测试月份细化功能"""
    dp = DateParser()
    
    print("=== 测试月份细化功能 ===")
    
    # 测试用例1: 标准日期格式
    test_html1 = '<meta property="article:published_time" content="2024-03-15">'
    result1 = dp.extract_publish_date(test_html1)
    print("\n测试1 - 标准日期格式:")
    print(f"  日期: {result1.get('publish_date')}")
    print(f"  年份: {result1.get('year')}")
    print(f"  月份: {result1.get('month')}")
    print(f"  月份名称: {result1.get('month_name')}")
    print(f"  季度: {result1.get('quarter')}")
    
    # 测试用例2: 文本中的日期
    test_html2 = '<div>Published on March 15, 2024</div>'
    result2 = dp.extract_publish_date(test_html2)
    print("\n测试2 - 文本日期:")
    print(f"  日期: {result2.get('publish_date')}")
    print(f"  年份: {result2.get('year')}")
    print(f"  月份: {result2.get('month')}")
    print(f"  月份名称: {result2.get('month_name')}")
    print(f"  季度: {result2.get('quarter')}")
    
    # 测试用例3: 非洲本地化日期格式
    test_html3 = '<span>Publié le 15 mars 2024</span>'
    result3 = dp.extract_publish_date(test_html3)
    print("\n测试3 - 法语日期:")
    print(f"  日期: {result3.get('publish_date')}")
    print(f"  年份: {result3.get('year')}")
    print(f"  月份: {result3.get('month')}")
    print(f"  月份名称: {result3.get('month_name')}")
    print(f"  季度: {result3.get('quarter')}")
    
    # 测试用例4: 无日期的情况
    test_html4 = '<div>This is a test without date</div>'
    result4 = dp.extract_publish_date(test_html4)
    print("\n测试4 - 无日期:")
    print(f"  日期: {result4.get('publish_date')}")
    print(f"  年份: {result4.get('year')}")
    print(f"  月份: {result4.get('month')}")
    print(f"  月份名称: {result4.get('month_name')}")
    print(f"  季度: {result4.get('quarter')}")

if __name__ == "__main__":
    test_month_extraction()