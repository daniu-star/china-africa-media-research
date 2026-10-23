#!/usr/bin/env python3
"""
数据完善脚本 - 修复现有数据质量问题
"""

import json
import re
from datetime import datetime
import html
from urllib.parse import urlparse

def decode_html_entities(text):
    """解码HTML实体"""
    if not text:
        return text
    return html.unescape(text)

def clean_content(text):
    """清理内容，移除多余空白和HTML标签"""
    if not text:
        return text
    
    # 解码HTML实体
    text = decode_html_entities(text)
    
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 限制长度
    if len(text) > 1000:
        text = text[:1000] + "..."
    
    return text

def extract_real_publish_date(url, content):
    """从URL和内容中提取真实的发布日期"""
    # 从URL中提取日期模式
    date_patterns = [
        r'(\d{4})/(\d{1,2})/(\d{1,2})',  # 2023/12/31
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2023-12-31
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 12/31/2023
        r'(\d{1,2})-(\d{1,2})-(\d{4})',  # 12-31-2023
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # 2023年12月31日
    ]
    
    # 从URL中查找日期
    for pattern in date_patterns:
        match = re.search(pattern, url)
        if match:
            try:
                if '/' in pattern or '-' in pattern:
                    if len(match.group(1)) == 4:  # YYYY-MM-DD
                        date_str = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                    else:  # MM-DD-YYYY
                        date_str = f"{match.group(3)}-{match.group(1).zfill(2)}-{match.group(2).zfill(2)}"
                    return date_str
            except:
                continue
    
    # 从内容中查找日期
    content_date_patterns = [
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        r'(\d{1,2})/(\d{1,2})/(\d{4})',
    ]
    
    for pattern in content_date_patterns:
        match = re.search(pattern, content)
        if match:
            try:
                if '年' in pattern:
                    date_str = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                elif len(match.group(1)) == 4:  # YYYY-MM-DD
                    date_str = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                else:  # MM-DD-YYYY
                    date_str = f"{match.group(3)}-{match.group(1).zfill(2)}-{match.group(2).zfill(2)}"
                return date_str
            except:
                continue
    
    return "unknown"

def enhance_data():
    """完善现有数据"""
    input_file = "data/results_recovered.json"
    output_file = "data/results_enhanced.json"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"原始数据包含 {len(data.get('articles', []))} 篇文章")
        
        enhanced_articles = []
        
        for article in data.get('articles', []):
            # 清理标题
            article['title'] = clean_content(article.get('title', ''))
            
            # 清理内容
            article['content'] = clean_content(article.get('content', ''))
            
            # 提取真实发布日期
            current_date = article.get('publish_date', '')
            if current_date == '2025-11-12' or current_date == 'unknown':
                real_date = extract_real_publish_date(
                    article.get('url', ''), 
                    article.get('content', '')
                )
                article['publish_date'] = real_date
            
            # 添加数据质量标记
            article['data_quality'] = 'good'
            if len(article.get('content', '')) < 50:
                article['data_quality'] = 'poor'
            elif article.get('publish_date') == 'unknown':
                article['data_quality'] = 'medium'
            
            enhanced_articles.append(article)
        
        # 保存增强后的数据
        enhanced_data = {
            'articles': enhanced_articles,
            'enhancement_date': datetime.now().isoformat(),
            'total_articles': len(enhanced_articles),
            'original_file': input_file
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
        
        print(f"数据完善完成！增强后的数据已保存到 {output_file}")
        print(f"处理了 {len(enhanced_articles)} 篇文章")
        
        # 统计质量分布
        quality_stats = {}
        for article in enhanced_articles:
            quality = article.get('data_quality', 'unknown')
            quality_stats[quality] = quality_stats.get(quality, 0) + 1
        
        print("数据质量分布:")
        for quality, count in quality_stats.items():
            print(f"  {quality}: {count} 篇")
        
    except Exception as e:
        print(f"数据处理出错: {e}")

if __name__ == "__main__":
    enhance_data()