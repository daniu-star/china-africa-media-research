#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能发布日期完善脚本
从URL和内容中提取真实发布日期，完善unknown状态的日期字段
"""

import json
import re
import requests
from datetime import datetime, timedelta
from urllib.parse import urlparse
import time
from collections import Counter

class DateExtractor:
    """智能日期提取器"""
    
    def __init__(self):
        # URL中的日期模式
        self.url_date_patterns = [
            # 标准日期格式
            r'(\d{4})/(\d{1,2})/(\d{1,2})',  # 2023/12/31
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2023-12-31
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 12/31/2023
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # 12-31-2023
            
            # 年月格式
            r'(\d{4})/(\d{1,2})',  # 2023/12
            r'(\d{4})-(\d{1,2})',  # 2023-12
            
            # 中文日期格式
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # 2023年12月31日
            r'(\d{4})年(\d{1,2})月',  # 2023年12月
            
            # 新闻网站特定格式
            r'(\d{4})(\d{2})(\d{2})',  # 20231231
            r'(\d{2})(\d{2})(\d{4})',  # 12312023
        ]
        
        # 内容中的日期模式
        self.content_date_patterns = [
            # 标准格式
            r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日]?',
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
            
            # 文本格式
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})',
            
            # 中文文本格式
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{1,2})月(\d{1,2})日(\d{4})年',
            
            # 相对时间
            r'(\d+)\s+(days?|weeks?|months?|years?)\s+ago',
            r'(\d+)\s+(天|周|月|年)前',
        ]
        
        # 月份映射
        self.month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
            'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
    
    def extract_from_url(self, url):
        """从URL中提取日期"""
        for pattern in self.url_date_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                try:
                    return self._parse_date_match(match.groups(), pattern)
                except:
                    continue
        return None
    
    def extract_from_content(self, content):
        """从内容中提取日期"""
        # 首先尝试标准日期格式
        for pattern in self.content_date_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    date = self._parse_date_match(match.groups(), pattern)
                    if date and self._is_valid_date(date):
                        return date
                except:
                    continue
        
        # 尝试相对时间
        relative_date = self._extract_relative_date(content)
        if relative_date:
            return relative_date
            
        return None
    
    def _parse_date_match(self, groups, pattern):
        """解析日期匹配结果"""
        if len(groups) == 3:
            # 标准日期格式
            if '/' in pattern or '-' in pattern:
                if len(groups[0]) == 4:  # YYYY-MM-DD
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                else:  # MM-DD-YYYY
                    month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
            elif '年' in pattern:  # 中文格式
                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
            else:
                return None
                
            return f"{year:04d}-{month:02d}-{day:02d}"
        
        elif len(groups) == 2:
            # 年月格式
            if len(groups[0]) == 4:  # YYYY-MM
                year, month = int(groups[0]), int(groups[1])
                return f"{year:04d}-{month:02d}-01"  # 默认到月初
            
        return None
    
    def _extract_relative_date(self, content):
        """提取相对时间"""
        # 英文相对时间
        relative_patterns = [
            (r'(\d+)\s+days?\s+ago', 'days'),
            (r'(\d+)\s+weeks?\s+ago', 'weeks'),
            (r'(\d+)\s+months?\s+ago', 'months'),
            (r'(\d+)\s+years?\s+ago', 'years'),
        ]
        
        for pattern, unit in relative_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    num = int(match.group(1))
                    today = datetime.now()
                    
                    if unit == 'days':
                        delta = timedelta(days=num)
                    elif unit == 'weeks':
                        delta = timedelta(weeks=num)
                    elif unit == 'months':
                        delta = timedelta(days=num*30)  # 近似值
                    elif unit == 'years':
                        delta = timedelta(days=num*365)  # 近似值
                    
                    result_date = today - delta
                    return result_date.strftime('%Y-%m-%d')
                except:
                    continue
        
        return None
    
    def _is_valid_date(self, date_str):
        """验证日期是否有效"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            
            # 检查日期是否合理（不能太早或太晚）
            year = int(date_str[:4])
            return 2000 <= year <= 2025  # 合理的时间范围
        except:
            return False

class DateEnhancer:
    """日期完善器"""
    
    def __init__(self):
        self.extractor = DateExtractor()
        self.stats = {
            'total_processed': 0,
            'dates_extracted': 0,
            'sources_enhanced': {},
            'extraction_methods': Counter()
        }
    
    def enhance_article_dates(self, article):
        """完善单篇文章的日期"""
        current_date = article.get('publish_date', 'unknown')
        
        # 如果已经是有效日期，跳过
        if current_date != 'unknown' and current_date != '2025-11-12':
            return article
        
        self.stats['total_processed'] += 1
        
        # 方法1：从URL中提取
        url_date = self.extractor.extract_from_url(article.get('url', ''))
        if url_date:
            article['publish_date'] = url_date
            article['date_extraction_method'] = 'url_pattern'
            self.stats['dates_extracted'] += 1
            self.stats['extraction_methods']['url_pattern'] += 1
            return article
        
        # 方法2：从内容中提取
        content_date = self.extractor.extract_from_content(article.get('content', ''))
        if content_date:
            article['publish_date'] = content_date
            article['date_extraction_method'] = 'content_pattern'
            self.stats['dates_extracted'] += 1
            self.stats['extraction_methods']['content_pattern'] += 1
            return article
        
        # 方法3：基于关键词和年份推断
        inferred_date = self._infer_date_from_context(article)
        if inferred_date:
            article['publish_date'] = inferred_date
            article['date_extraction_method'] = 'context_inference'
            self.stats['dates_extracted'] += 1
            self.stats['extraction_methods']['context_inference'] += 1
            return article
        
        # 无法提取，保持unknown
        article['date_extraction_method'] = 'failed'
        return article
    
    def _infer_date_from_context(self, article):
        """基于上下文推断日期"""
        # 如果有年份信息，使用年份
        year = article.get('year')
        if year and 2000 <= year <= 2025:
            return f"{year}-01-01"  # 默认到年初
        
        # 基于关键词推断（简单逻辑）
        content = article.get('content', '').lower()
        keyword = article.get('keyword', '').lower()
        
        # 基于关键词的年份推断（简化版）
        keyword_year_map = {
            'covid': 2020,
            'pandemic': 2020,
            'coronavirus': 2020,
            'brexit': 2016,
            'trump': 2016,
            'obama': 2008,
        }
        
        for kw, yr in keyword_year_map.items():
            if kw in content or kw in keyword:
                return f"{yr}-01-01"
        
        return None
    
    def print_stats(self):
        """打印统计信息"""
        print("\n=== 日期完善统计 ===")
        print(f"处理文章总数: {self.stats['total_processed']}")
        print(f"成功提取日期: {self.stats['dates_extracted']}")
        print(f"提取成功率: {self.stats['dates_extracted']/self.stats['total_processed']*100:.1f}%")
        
        print("\n提取方法分布:")
        for method, count in self.stats['extraction_methods'].items():
            print(f"  {method}: {count} 篇")

def enhance_publish_dates():
    """主函数：完善发布日期"""
    input_file = "data/results_enhanced.json"
    output_file = "data/results_enhanced_with_dates.json"
    
    print("开始完善发布日期信息...")
    
    try:
        # 读取数据
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = data.get('articles', [])
        print(f"原始数据包含 {len(articles)} 篇文章")
        
        # 初始化完善器
        enhancer = DateEnhancer()
        
        # 处理每篇文章
        enhanced_articles = []
        for i, article in enumerate(articles):
            if i % 1000 == 0:
                print(f"处理进度: {i}/{len(articles)} ({i/len(articles)*100:.1f}%)")
            
            enhanced_article = enhancer.enhance_article_dates(article)
            enhanced_articles.append(enhanced_article)
        
        # 保存增强后的数据
        enhanced_data = {
            'articles': enhanced_articles,
            'enhancement_date': datetime.now().isoformat(),
            'total_articles': len(enhanced_articles),
            'date_enhancement_stats': enhancer.stats,
            'original_file': input_file
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n日期完善完成！增强后的数据已保存到 {output_file}")
        
        # 打印统计信息
        enhancer.print_stats()
        
        # 验证结果
        print("\n=== 验证结果 ===")
        date_stats = {}
        for article in enhanced_articles:
            date = article.get('publish_date', 'unknown')
            date_stats[date] = date_stats.get(date, 0) + 1
        
        print("发布日期分布:")
        unknown_count = date_stats.get('unknown', 0)
        valid_dates = sum(count for date, count in date_stats.items() 
                         if date != 'unknown')
        
        print(f"有效日期: {valid_dates} 篇 ({valid_dates/len(enhanced_articles)*100:.1f}%)")
        print(f"unknown状态: {unknown_count} 篇 ({unknown_count/len(enhanced_articles)*100:.1f}%)")
        
        # 显示前几个有效日期
        valid_date_items = [(date, count) for date, count in date_stats.items() 
                           if date != 'unknown']
        valid_date_items.sort(key=lambda x: x[1], reverse=True)
        
        print("\n最常见的有效日期:")
        for date, count in valid_date_items[:10]:
            print(f"  {date}: {count} 篇")
        
    except Exception as e:
        print(f"处理出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    enhance_publish_dates()