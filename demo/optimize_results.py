#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据整合和优化脚本
将多个数据源整合并转换为新闻报道格式
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any

# 文件路径配置
DATA_DIR = "data"
RESULTS_SUBDIR = os.path.join(DATA_DIR, "results")
TARGET_FILE = os.path.join(RESULTS_SUBDIR, "results_1.json")

# 数据源文件
MAIN_SOURCE = os.path.join(RESULTS_SUBDIR, "results_1.json")  # 主要数据源
BACKUP_SOURCE = os.path.join(DATA_DIR, "results_0.json.backup")  # 工作节点备份
OLD_SOURCE = os.path.join(DATA_DIR, "results_1.json")  # 旧数据源（质量差）

def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """加载JSON文件"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载文件失败 {file_path}: {e}")
        return []

def extract_articles_from_task(task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从任务数据中提取新闻报道"""
    articles = []
    
    # 检查是否有result字段
    if 'result' in task_data and task_data['result']:
        result = task_data['result']
        
        # 检查是否有articles字段
        if 'articles' in result and result['articles']:
            for article in result['articles']:
                # 转换为新闻报道格式
                news_article = {
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'content': article.get('content', ''),
                    'source': article.get('source', ''),
                    'publish_date': article.get('publish_date', ''),
                    'keyword': result.get('keyword', ''),
                    'year': result.get('year', ''),
                    'crawl_time': article.get('crawl_time', ''),
                    'crawl_method': article.get('crawl_method', 'traditional')
                }
                
                # 过滤无效内容
                if (news_article['content'] and 
                    len(news_article['content'].strip()) > 50 and
                    news_article['title'] and
                    news_article['url']):
                    articles.append(news_article)
    
    return articles

def extract_articles_from_backup(backup_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从备份数据中提取新闻报道"""
    articles = []
    
    for article in backup_data:
        # 备份数据已经是文章格式，直接转换
        news_article = {
            'title': article.get('title', ''),
            'url': article.get('url', ''),
            'content': article.get('content', ''),
            'source': article.get('source', ''),
            'publish_date': article.get('publish_date', ''),
            'keyword': article.get('keyword', ''),
            'year': article.get('year', ''),
            'crawl_time': article.get('crawl_time', ''),
            'crawl_method': article.get('crawl_method', 'traditional')
        }
        
        # 过滤无效内容
        if (news_article['content'] and 
            len(news_article['content'].strip()) > 50 and
            news_article['title'] and
            news_article['url']):
            articles.append(news_article)
    
    return articles

def deduplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """去重文章（基于URL和内容）"""
    seen_urls = set()
    unique_articles = []
    
    for article in articles:
        url = article['url']
        if url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)
    
    return unique_articles

def save_optimized_data(articles: List[Dict[str, Any]], target_file: str):
    """保存优化后的数据"""
    # 确保目录存在
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    
    # 保存数据
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    
    print(f"优化后的数据已保存到: {target_file}")
    print(f"共保存 {len(articles)} 条新闻报道")

def main():
    """主函数"""
    print("开始数据整合和优化...")
    
    # 1. 加载主要数据源
    print("加载主要数据源...")
    main_data = load_json_file(MAIN_SOURCE)
    print(f"主要数据源加载完成，共 {len(main_data)} 条任务记录")
    
    # 2. 从主要数据源提取文章
    main_articles = []
    for task in main_data:
        articles = extract_articles_from_task(task)
        main_articles.extend(articles)
    print(f"从主要数据源提取到 {len(main_articles)} 篇文章")
    
    # 3. 加载备份数据源
    print("加载备份数据源...")
    backup_data = load_json_file(BACKUP_SOURCE)
    print(f"备份数据源加载完成，共 {len(backup_data)} 条记录")
    
    # 4. 从备份数据源提取文章
    backup_articles = extract_articles_from_backup(backup_data)
    print(f"从备份数据源提取到 {len(backup_articles)} 篇文章")
    
    # 5. 合并所有文章
    all_articles = main_articles + backup_articles
    print(f"合并后共 {len(all_articles)} 篇文章")
    
    # 6. 去重
    unique_articles = deduplicate_articles(all_articles)
    print(f"去重后剩余 {len(unique_articles)} 篇唯一文章")
    
    # 7. 按爬取时间排序（最新的在前）
    unique_articles.sort(key=lambda x: x.get('crawl_time', ''), reverse=True)
    
    # 8. 保存优化后的数据
    save_optimized_data(unique_articles, TARGET_FILE)
    
    # 9. 统计信息
    print("\n数据统计信息:")
    print(f"- 总文章数: {len(unique_articles)}")
    
    # 按关键词统计
    keyword_stats = {}
    for article in unique_articles:
        keyword = article.get('keyword', '未知')
        keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1
    
    print("\n按关键词统计:")
    for keyword, count in sorted(keyword_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {keyword}: {count} 篇")
    
    print("\n数据整合和优化完成!")

if __name__ == "__main__":
    main()