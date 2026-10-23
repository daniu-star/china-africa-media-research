#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证和清洗功能测试脚本
测试非洲报纸爬虫的数据质量验证和清洗功能
"""

import sys
import os
import json
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from african_newspaper_crawler import AfricanNewspaperCrawler

def test_data_validation():
    """测试数据验证和清洗功能"""
    print("=== 非洲报纸爬虫数据验证和清洗功能测试 ===\n")
    
    # 初始化爬虫
    crawler = AfricanNewspaperCrawler()
    
    # 测试关键词
    test_keyword = "China"
    
    # 测试所有报纸
    newspapers = ['ahram', 'citizen', 'vanguard', 'nation', 'mg']
    
    for newspaper_key in newspapers:
        print(f"\n--- 测试 {crawler.newspapers[newspaper_key]['name']} ---")
        
        try:
            # 搜索文章
            print(f"搜索关键词: {test_keyword}")
            article_links = crawler.search_articles(newspaper_key, test_keyword, max_articles=3)
            
            if not article_links:
                print("❌ 搜索失败，未找到文章链接")
                continue
            
            print(f"✅ 搜索成功，找到 {len(article_links)} 篇文章")
            
            # 爬取前2篇文章进行测试
            for i, article_url in enumerate(article_links[:2]):
                print(f"\n爬取第 {i+1} 篇文章: {article_url}")
                
                try:
                    # 爬取文章内容
                    article_data = crawler.crawl_article(newspaper_key, article_url)
                    
                    if article_data:
                        print("✅ 文章爬取成功")
                        
                        # 显示数据验证结果
                        quality_score = article_data.get('quality_score', 0)
                        issues = article_data.get('quality_issues', [])
                        suggestions = article_data.get('quality_suggestions', [])
                        
                        print(f"📊 质量评分: {quality_score:.2f}")
                        
                        if issues:
                            print(f"⚠️  发现 {len(issues)} 个问题:")
                            for issue in issues[:3]:  # 只显示前3个问题
                                print(f"   - {issue}")
                        else:
                            print("✅ 未发现质量问题")
                        
                        if suggestions:
                            print(f"💡 改进建议 ({len(suggestions)} 条):")
                            for suggestion in suggestions[:2]:  # 只显示前2条建议
                                print(f"   - {suggestion}")
                        
                        # 显示清洗后的数据摘要
                        title = article_data.get('title', 'N/A')
                        content_preview = article_data.get('content', '')[:100] + '...' if article_data.get('content') else 'N/A'
                        author = article_data.get('author', 'N/A')
                        publish_time = article_data.get('publish_time', 'N/A')
                        
                        print(f"📰 标题: {title}")
                        print(f"📝 内容预览: {content_preview}")
                        print(f"👤 作者: {author}")
                        print(f"⏰ 发布时间: {publish_time}")
                        
                        # 验证数据完整性
                        is_complete = crawler._validate_article_completeness(article_data)
                        print(f"🔍 数据完整性: {'✅ 完整' if is_complete else '❌ 不完整'}")
                        
                        # 保存测试数据
                        test_data_dir = "test_data"
                        os.makedirs(test_data_dir, exist_ok=True)
                        
                        filename = f"{newspaper_key}_article_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        filepath = os.path.join(test_data_dir, filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(article_data, f, ensure_ascii=False, indent=2)
                        
                        print(f"💾 测试数据已保存: {filepath}")
                        
                    else:
                        print("❌ 文章爬取失败")
                        
                except Exception as e:
                    print(f"❌ 爬取文章时发生错误: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ 测试 {crawler.newspapers[newspaper_key]['name']} 时发生错误: {e}")
            continue
    
    print("\n=== 测试完成 ===")

def test_data_cleaning_functions():
    """测试数据清洗功能"""
    print("\n=== 测试数据清洗功能 ===\n")
    
    crawler = AfricanNewspaperCrawler()
    
    # 测试数据
    test_articles = [
        {
            'title': '   Test Article  |  With Extra Spaces   ',
            'content': 'This is a test content with    multiple    spaces and special characters &amp; entities.',
            'author': 'By John Smith',
            'publish_time': '2024-01-15 14:30:00',
            'url': 'http://example.com/test'
        },
        {
            'title': 'Another Test',
            'content': 'Short content',  # 短内容，应该被标记为不完整
            'author': '',
            'publish_time': '15/01/2024',
            'url': 'http://example.com/test2'
        }
    ]
    
    for i, article in enumerate(test_articles):
        print(f"测试文章 {i+1}:")
        print(f"原始标题: '{article['title']}'")
        print(f"原始内容长度: {len(article['content'])}")
        print(f"原始作者: '{article['author']}'")
        print(f"原始时间: '{article['publish_time']}'")
        
        # 应用数据清洗
        cleaned_article = crawler._clean_article_fields(article.copy())
        
        print(f"清洗后标题: '{cleaned_article['title']}'")
        print(f"清洗后内容长度: {len(cleaned_article['content'])}")
        print(f"清洗后作者: '{cleaned_article['author']}'")
        print(f"清洗后时间: '{cleaned_article['publish_time']}'")
        
        # 验证完整性
        is_complete = crawler._validate_article_completeness(cleaned_article)
        print(f"数据完整性: {'✅ 完整' if is_complete else '❌ 不完整'}")
        print("-" * 50)

def main():
    """主函数"""
    print("非洲报纸爬虫数据验证和清洗功能测试")
    print("=" * 60)
    
    # 测试数据清洗功能
    test_data_cleaning_functions()
    
    # 测试完整的数据验证流程
    test_data_validation()

if __name__ == "__main__":
    main()