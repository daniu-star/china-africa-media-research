#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容增强脚本
智能过滤登录页面内容，解决内容截断问题，完善新闻正文
"""

import json
import re
import os
from urllib.parse import urlparse
import requests
from datetime import datetime

class ContentEnhancer:
    """内容增强器，负责智能内容过滤和完善"""
    
    def __init__(self):
        # 登录页面关键词模式
        self.login_patterns = [
            r'sign\s*in', r'log\s*in', r'login', r'username', r'password',
            r'forgot\s*password', r'get\s*help', r'welcome', r'account',
            r'my\s*account', r'personal\s*details', r'change\s*password',
            r'purchases', r'sign\s*out', r'logging\s*you\s*out', r'subscribe'
        ]
        
        # 新闻正文关键词模式
        self.news_patterns = [
            r'news', r'article', r'report', r'story', r'update',
            r'breaking', r'latest', r'developments', r'analysis',
            r'feature', r'coverage', r'headline', r'journalism'
        ]
        
        # 无意义内容模式
        self.nonsense_patterns = [
            r'^\s*$',  # 空内容
            r'^[\s\W]*$',  # 只有标点符号
            r'loading', r'please\s*wait', r'redirecting'
        ]
    
    def is_login_page_content(self, content):
        """检测是否为登录页面内容"""
        content_lower = content.lower()
        login_matches = sum(1 for pattern in self.login_patterns 
                           if re.search(pattern, content_lower))
        
        # 如果包含多个登录关键词，认为是登录页面
        return login_matches >= 2
    
    def is_meaningful_content(self, content):
        """检测是否为有意义的新闻内容"""
        if not content or len(content.strip()) < 50:
            return False
        
        content_lower = content.lower()
        
        # 检查无意义内容
        for pattern in self.nonsense_patterns:
            if re.search(pattern, content_lower):
                return False
        
        # 检查新闻关键词
        news_matches = sum(1 for pattern in self.news_patterns 
                          if re.search(pattern, content_lower))
        
        # 包含新闻关键词或内容长度足够
        return news_matches > 0 or len(content) > 200
    
    def extract_main_content(self, content):
        """从内容中提取主要新闻正文"""
        if not content:
            return ""
        
        # 移除HTML标签和多余空格
        content = re.sub(r'<[^>]+>', ' ', content)
        content = re.sub(r'\s+', ' ', content).strip()
        
        # 分割段落
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        
        # 过滤掉短段落（可能是导航、广告等）
        meaningful_paragraphs = []
        for para in paragraphs:
            if len(para) > 50 and not self.is_login_page_content(para):
                meaningful_paragraphs.append(para)
        
        # 合并有意义的段落
        main_content = ' '.join(meaningful_paragraphs)
        
        # 如果内容仍然过短，尝试重新爬取
        if len(main_content) < 100:
            return ""  # 标记为需要重新爬取
        
        return main_content
    
    def enhance_article_content(self, article):
        """增强单篇文章的内容"""
        original_content = article.get('content', '')
        
        # 检查是否为登录页面内容
        if self.is_login_page_content(original_content):
            article['content_quality'] = 'login_page'
            article['needs_recrawl'] = True
            return article
        
        # 提取主要内容
        enhanced_content = self.extract_main_content(original_content)
        
        if enhanced_content:
            article['content'] = enhanced_content
            article['content_quality'] = 'enhanced'
            article['original_content_length'] = len(original_content)
            article['enhanced_content_length'] = len(enhanced_content)
        else:
            # 内容质量差，需要重新爬取
            article['content_quality'] = 'poor_quality'
            article['needs_recrawl'] = True
        
        return article

def enhance_existing_data():
    """增强现有数据的内容质量"""
    
    # 加载数据文件
    data_file = 'data/results_enhanced_with_dates.json'
    if not os.path.exists(data_file):
        print(f'错误: 数据文件 {data_file} 不存在')
        return
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data_dict = json.load(f)
    except Exception as e:
        print(f'加载数据文件失败: {e}')
        return
    
    # 获取文章列表
    if 'articles' not in data_dict:
        print('错误: 数据文件中没有articles键')
        return
    
    articles = data_dict['articles']
    print(f'开始处理 {len(articles)} 篇文章...')
    
    # 初始化内容增强器
    enhancer = ContentEnhancer()
    
    # 处理每篇文章
    enhanced_articles = []
    recrawl_articles = []
    
    for i, article in enumerate(articles):
        if i % 100 == 0:
            print(f'处理进度: {i}/{len(articles)}')
        
        enhanced_article = enhancer.enhance_article_content(article.copy())
        
        if enhanced_article.get('needs_recrawl', False):
            recrawl_articles.append(enhanced_article)
        else:
            enhanced_articles.append(enhanced_article)
    
    print(f'处理完成!')
    print(f'成功增强: {len(enhanced_articles)} 篇文章')
    print(f'需要重新爬取: {len(recrawl_articles)} 篇文章')
    
    # 保存增强后的数据
    enhanced_data = {
        'articles': enhanced_articles,
        'recrawl_articles': recrawl_articles,
        'enhancement_date': datetime.now().isoformat(),
        'total_processed': len(articles),
        'enhancement_stats': {
            'successful_enhancements': len(enhanced_articles),
            'needs_recrawl': len(recrawl_articles),
            'enhancement_rate': len(enhanced_articles) / len(articles) * 100
        }
    }
    
    # 保存文件
    output_file = 'data/results_content_enhanced.json'
    os.makedirs('data', exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
    
    print(f'增强后的数据已保存到: {output_file}')
    
    # 保存需要重新爬取的URL列表
    if recrawl_articles:
        recrawl_urls = [article['url'] for article in recrawl_articles]
        recrawl_file = 'data/recrawl_urls.json'
        
        with open(recrawl_file, 'w', encoding='utf-8') as f:
            json.dump(recrawl_urls, f, ensure_ascii=False, indent=2)
        
        print(f'需要重新爬取的URL列表已保存到: {recrawl_file}')

def update_crawler_for_content_enhancement():
    """更新爬虫代码以集成内容增强功能"""
    
    # 读取distributed_worker.py
    worker_file = 'distributed_worker.py'
    if not os.path.exists(worker_file):
        print(f'错误: {worker_file} 不存在')
        return
    
    try:
        with open(worker_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f'读取文件失败: {e}')
        return
    
    # 检查是否已经包含内容增强功能
    if 'ContentEnhancer' in content:
        print('爬虫代码已经包含内容增强功能')
        return
    
    # 在文件开头添加导入
    import_statement = """
# 内容增强功能
from content_enhancement import ContentEnhancer
"""
    
    # 找到第一个import语句的位置
    import_match = re.search(r'^import\s+', content, re.MULTILINE)
    if import_match:
        insert_pos = import_match.start()
        content = content[:insert_pos] + import_statement + content[insert_pos:]
    else:
        # 如果没有import语句，添加到文件开头
        content = import_statement + content
    
    # 在extract_content_from_html函数中添加内容增强逻辑
    extract_function_pattern = r'def extract_content_from_html\([^)]*\):'
    extract_match = re.search(extract_function_pattern, content)
    
    if extract_match:
        # 在函数末尾添加内容增强逻辑
        function_end_pattern = r'(?=\n\n|\nclass|\ndef|\nif\s+__name__)'
        function_end_match = re.search(function_end_pattern, content[extract_match.end():])
        
        if function_end_match:
            insert_pos = extract_match.end() + function_end_match.start()
            
            enhancement_code = """
    
    # 内容增强处理
    enhancer = ContentEnhancer()
    
    # 检查是否为登录页面内容
    if enhancer.is_login_page_content(content):
        return ""  # 返回空内容，标记为需要重新爬取
    
    # 提取主要新闻内容
    enhanced_content = enhancer.extract_main_content(content)
    
    return enhanced_content
"""
            
            content = content[:insert_pos] + enhancement_code + content[insert_pos:]
    
    # 保存更新后的文件
    backup_file = 'distributed_worker.py.backup'
    os.rename(worker_file, backup_file)
    
    with open(worker_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'爬虫代码已更新，原文件备份为: {backup_file}')

if __name__ == '__main__':
    print('=== 内容增强系统 ===')
    print('1. 增强现有数据内容质量')
    print('2. 更新爬虫代码集成内容增强功能')
    
    choice = input('请选择操作 (1或2): ').strip()
    
    if choice == '1':
        enhance_existing_data()
    elif choice == '2':
        update_crawler_for_content_enhancement()
    else:
        print('无效选择')