#!/usr/bin/env python3
"""检查清理后数据的质量"""

import json
import os

def analyze_cleaned_data():
    """分析清理后的数据质量"""
    
    cleaned_files = [
        'data/results_content_enhanced_cleaned.json',
        'data/results_enhanced_with_dates_cleaned.json'
    ]
    
    for file_path in cleaned_files:
        if os.path.exists(file_path):
            print(f"\n=== 分析文件: {file_path} ===")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            articles = data.get('articles', [])
            cleanup_stats = data.get('cleanup_stats', {})
            
            print(f"总文章数: {len(articles)}")
            print(f"清理统计: {cleanup_stats}")
            
            # 分析内容长度分布
            content_lengths = [len(article.get('content', '')) for article in articles]
            
            if content_lengths:
                avg_length = sum(content_lengths) / len(content_lengths)
                max_length = max(content_lengths)
                min_length = min(content_lengths)
                
                print(f"内容长度统计:")
                print(f"  平均长度: {avg_length:.1f} 字符")
                print(f"  最大长度: {max_length} 字符")
                print(f"  最小长度: {min_length} 字符")
                
                # 长度分布
                length_ranges = [0, 100, 500, 1000, 2000, float('inf')]
                range_labels = ['极短(0-100)', '短(100-500)', '中(500-1000)', '长(1000-2000)', '超长(2000+)']
                
                for i in range(len(length_ranges) - 1):
                    count = sum(1 for length in content_lengths 
                              if length_ranges[i] <= length < length_ranges[i+1])
                    percentage = (count / len(content_lengths)) * 100
                    print(f"  {range_labels[i]}: {count} 篇 ({percentage:.1f}%)")
            
            # 检查增强标记
            enhanced_count = sum(1 for article in articles if article.get('content_enhanced', False))
            need_recrawl_count = sum(1 for article in articles if article.get('need_recrawl', False))
            
            print(f"内容增强标记: {enhanced_count} 篇")
            print(f"需要重新爬取: {need_recrawl_count} 篇")
            
            # 检查前3篇文章的内容质量
            print(f"\n前3篇文章预览:")
            for i, article in enumerate(articles[:3]):
                content = article.get('content', '')
                print(f"\n文章 {i+1}:")
                print(f"  标题: {article.get('title', 'N/A')[:50]}...")
                print(f"  URL: {article.get('url', 'N/A')}")
                print(f"  内容长度: {len(content)} 字符")
                print(f"  增强标记: {article.get('content_enhanced', False)}")
                print(f"  需要重新爬取: {article.get('need_recrawl', False)}")
                if content:
                    print(f"  内容预览: {content[:100]}...")
    
    # 检查重新爬取URL列表
    recrawl_files = [
        'data/results_content_enhanced_cleaned_recrawl_urls.json',
        'data/results_enhanced_with_dates_cleaned_recrawl_urls.json'
    ]
    
    for file_path in recrawl_files:
        if os.path.exists(file_path):
            print(f"\n=== 重新爬取URL列表: {file_path} ===")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                recrawl_urls = json.load(f)
            
            print(f"需要重新爬取的URL数量: {len(recrawl_urls)}")
            
            if recrawl_urls:
                print("前5个需要重新爬取的URL:")
                for i, url_info in enumerate(recrawl_urls[:5]):
                    print(f"  {i+1}. {url_info.get('url', 'N/A')}")
                    print(f"     关键词: {url_info.get('keyword', 'N/A')}")
                    print(f"     年份: {url_info.get('year', 'N/A')}")
                    print(f"     原因: {url_info.get('reason', 'N/A')}")

def main():
    """主函数"""
    print("开始检查清理后的数据质量...\n")
    
    analyze_cleaned_data()
    
    print("\n=== 检查完成 ===")

if __name__ == "__main__":
    main()