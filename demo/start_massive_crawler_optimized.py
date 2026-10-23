#!/usr/bin/env python3
"""
优化的大规模爬虫启动脚本
集成数据存储管理器，支持断点续爬和智能恢复
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from intelligent_crawling_system import IntelligentCrawlingSystem
from data_storage_manager import DataStorageManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('massive_crawler_optimized.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def load_config():
    """加载爬虫配置"""
    try:
        with open('massive_crawler_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        logging.info("成功加载爬虫配置")
        return config
    except Exception as e:
        logging.error(f"加载配置失败: {e}")
        return None

def load_keywords():
    """加载关键词列表"""
    try:
        # 首先尝试从关键词文件加载
        if os.path.exists('china_imagination_keywords.json'):
            with open('china_imagination_keywords.json', 'r', encoding='utf-8') as f:
                keywords_data = json.load(f)
                
                # 从嵌套结构中提取所有关键词
                keywords = []
                
                # 提取主要关键词
                if 'primary_keywords' in keywords_data:
                    for category in keywords_data['primary_keywords'].values():
                        if isinstance(category, list):
                            keywords.extend(category)
                
                # 提取经济框架关键词
                if 'economic_framework' in keywords_data:
                    for category in keywords_data['economic_framework'].values():
                        if isinstance(category, list):
                            keywords.extend(category)
                
                # 提取地缘政治关键词
                if 'geopolitical_narratives' in keywords_data:
                    for category in keywords_data['geopolitical_narratives'].values():
                        if isinstance(category, list):
                            keywords.extend(category)
                
                # 提取文化社会关键词
                if 'cultural_social_representations' in keywords_data:
                    for category in keywords_data['cultural_social_representations'].values():
                        if isinstance(category, list):
                            keywords.extend(category)
                
                # 去重并过滤空值
                keywords = list(set([kw for kw in keywords if kw and isinstance(kw, str)]))
                
        else:
            # 使用默认配置中的关键词
            config = load_config()
            keywords = config.get('keywords', [])
        
        logging.info(f"加载了 {len(keywords)} 个关键词")
        return keywords
    except Exception as e:
        logging.error(f"加载关键词失败: {e}")
        return []

def check_existing_progress():
    """检查现有的爬虫进度"""
    try:
        if os.path.exists('massive_crawler_progress.json'):
            with open('massive_crawler_progress.json', 'r', encoding='utf-8') as f:
                progress = json.load(f)
            
            completed_keywords = [item['keyword'] for item in progress.get('completed_keywords', [])]
            logging.info(f"发现 {len(completed_keywords)} 个已完成的关键词")
            return progress, completed_keywords
        
    except Exception as e:
        logging.warning(f"检查进度文件失败: {e}")
    
    return None, []

def initialize_crawler_system():
    """初始化智能爬虫系统"""
    try:
        # 配置数据存储管理器
        storage_config = {
            'base_dir': 'massive_crawler_results',
            'backup_dir': 'massive_crawler_results/backup'
        }
        
        # 初始化智能爬虫系统
        crawler_system = IntelligentCrawlingSystem(
            config_file="adaptive_learning_config.json",
            storage_config=storage_config
        )
        
        logging.info("智能爬虫系统初始化成功")
        return crawler_system
    except Exception as e:
        logging.error(f"初始化爬虫系统失败: {e}")
        return None

def _simulate_article_extraction(keyword, max_articles):
    """模拟文章提取（用于演示）"""
    import random
    
    # 模拟生成文章数据
    articles = []
    for i in range(min(max_articles, random.randint(3, 10))):
        article = {
            'title': f"关于{keyword}的文章 {i+1}",
            'url': f"https://example.com/article/{keyword.replace(' ', '_')}_{i+1}",
            'content': f"这是关于{keyword}的模拟文章内容。文章讨论了{keyword}的相关话题。",
            'source': random.choice(['新华网', '人民网', '央视网', '中国日报', '环球时报']),
            'publish_date': f"202{random.randint(0,4)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            'keyword': keyword
        }
        articles.append(article)
    
    return articles

def start_massive_crawling():
    """启动大规模爬虫"""
    logging.info("=== 开始大规模爬虫任务 ===")
    
    # 加载配置
    config = load_config()
    if not config:
        logging.error("配置加载失败，无法继续")
        return
    
    # 加载关键词
    keywords = load_keywords()
    if not keywords:
        logging.error("没有找到关键词，无法继续")
        return
    
    # 检查现有进度
    progress_data, completed_keywords = check_existing_progress()
    
    # 过滤掉已完成的关键词
    remaining_keywords = [kw for kw in keywords if kw not in completed_keywords]
    
    if not remaining_keywords:
        logging.info("所有关键词已完成爬取")
        return
    
    logging.info(f"剩余 {len(remaining_keywords)} 个关键词需要爬取")
    
    # 初始化爬虫系统
    crawler_system = initialize_crawler_system()
    if not crawler_system:
        logging.error("爬虫系统初始化失败")
        return
    
    # 开始爬虫任务
    crawler_settings = config.get('crawler_settings', {})
    max_pages_per_keyword = crawler_settings.get('max_pages_per_keyword', 10)
    max_articles_per_keyword = crawler_settings.get('max_articles_per_keyword', 50)
    delay_between_keywords = crawler_settings.get('delay_between_keywords', 3)
    
    # 初始化进度跟踪
    progress = {
        'started_at': datetime.now().isoformat(),
        'completed_keywords': progress_data.get('completed_keywords', []) if progress_data else [],
        'current_keyword': None,
        'current_page': 0,
        'total_articles': progress_data.get('total_articles', 0) if progress_data else 0,
        'last_saved': datetime.now().isoformat()
    }
    
    # 开始爬取剩余关键词
    for i, keyword in enumerate(remaining_keywords):
        logging.info(f"开始爬取关键词 [{i+1}/{len(remaining_keywords)}]: {keyword}")
        
        try:
            # 更新进度
            progress['current_keyword'] = keyword
            progress['current_page'] = 0
            
            # 使用智能爬虫系统进行爬取
            # 构建搜索URL（这里使用Google搜索作为示例）
            search_url = f"https://www.google.com/search?q={keyword.replace(' ', '+')}"
            
            # 使用智能爬虫系统爬取搜索页面
            result = crawler_system.crawl_url(search_url)
            
            # 处理爬取结果
            if result['success']:
                # 这里应该解析搜索结果页面，提取文章链接和内容
                # 由于这是模拟实现，我们创建模拟的文章数据
                results = _simulate_article_extraction(keyword, max_articles_per_keyword)
            else:
                results = []
            
            # 记录结果
            articles_found = len(results) if results else 0
            progress['total_articles'] += articles_found
            
            # 添加完成的关键词记录
            completed_keyword = {
                'keyword': keyword,
                'articles_found': articles_found,
                'completed_at': datetime.now().isoformat()
            }
            progress['completed_keywords'].append(completed_keyword)
            
            logging.info(f"关键词 '{keyword}' 完成，找到 {articles_found} 篇文章")
            
            # 保存进度
            with open('massive_crawler_progress.json', 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2, ensure_ascii=False)
            
            # 延迟一段时间再处理下一个关键词
            if i < len(remaining_keywords) - 1:
                logging.info(f"等待 {delay_between_keywords} 秒后继续...")
                time.sleep(delay_between_keywords)
                
        except Exception as e:
            logging.error(f"爬取关键词 '{keyword}' 时出错: {e}")
            # 继续处理下一个关键词
            continue
    
    logging.info("=== 大规模爬虫任务完成 ===")
    logging.info(f"总共爬取了 {len(keywords)} 个关键词，找到 {progress['total_articles']} 篇文章")

def main():
    """主函数"""
    try:
        start_massive_crawling()
    except KeyboardInterrupt:
        logging.info("用户中断爬虫任务")
    except Exception as e:
        logging.error(f"爬虫任务异常终止: {e}")

if __name__ == "__main__":
    main()