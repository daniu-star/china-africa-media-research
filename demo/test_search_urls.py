#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有更新后的搜索URL
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from african_newspaper_crawler import AfricanNewspaperCrawler
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_search_urls():
    """测试所有报纸的搜索URL"""
    crawler = AfricanNewspaperCrawler()
    
    # 测试关键词
    test_keyword = "China"
    
    # 测试每个报纸
    newspapers_to_test = ['ahram', 'citizen', 'vanguard', 'nation', 'mg']
    
    for newspaper_key in newspapers_to_test:
        print(f"\n{'='*60}")
        print(f"测试 {newspaper_key.upper()} 搜索功能")
        print(f"{'='*60}")
        
        try:
            # 搜索文章
            articles = crawler.search_articles(newspaper_key, test_keyword, page=1)
            
            if articles:
                print(f"✓ 搜索成功！找到 {len(articles)} 篇文章")
                for i, article_url in enumerate(articles[:3], 1):  # 显示前3个结果
                    print(f"  {i}. {article_url}")
            else:
                print("✗ 搜索失败或未找到相关文章")
                
        except Exception as e:
            print(f"✗ 搜索过程中出现错误: {e}")
            
    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}")

if __name__ == "__main__":
    test_search_urls()