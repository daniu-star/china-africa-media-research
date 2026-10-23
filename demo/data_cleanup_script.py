#!/usr/bin/env python3
"""数据清理脚本 - 遍历现有数据并完善内容"""

import json
import logging
import os
from datetime import datetime
from content_extraction_optimizer import ContentExtractionOptimizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_cleanup.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataCleanupProcessor:
    """数据清理处理器"""
    
    def __init__(self):
        self.optimizer = ContentExtractionOptimizer()
        self.stats = {
            'total_articles': 0,
            'enhanced_articles': 0,
            'need_recrawl': 0,
            'login_pages': 0,
            'short_content': 0,
            'truncated_content': 0
        }
    
    def analyze_content_quality(self, content: str) -> dict:
        """分析内容质量"""
        quality = {
            'length': len(content),
            'is_short': len(content) < 100,
            'is_truncated': '...' in content or '点击阅读全文' in content or '订阅' in content,
            'has_login_keywords': any(keyword in content.lower() for keyword in 
                                   ['登录', '注册', 'sign in', 'subscribe', 'members only'])
        }
        return quality
    
    def process_article(self, article: dict) -> dict:
        """处理单篇文章"""
        original_content = article.get('content', '')
        url = article.get('url', '')
        
        # 分析内容质量
        quality = self.analyze_content_quality(original_content)
        
        # 更新统计信息
        if quality['is_short']:
            self.stats['short_content'] += 1
        if quality['is_truncated']:
            self.stats['truncated_content'] += 1
        if quality['has_login_keywords']:
            self.stats['login_pages'] += 1
        
        # 如果内容质量较差，尝试增强
        if quality['is_short'] or quality['is_truncated'] or quality['has_login_keywords']:
            enhanced_content = self.optimizer.enhance_existing_content(original_content, url)
            
            if enhanced_content and enhanced_content != original_content:
                article['content'] = enhanced_content
                article['content_enhanced'] = True
                article['enhancement_date'] = datetime.now().isoformat()
                self.stats['enhanced_articles'] += 1
                logger.info(f"成功增强文章内容: {url}")
            else:
                article['need_recrawl'] = True
                self.stats['need_recrawl'] += 1
                logger.warning(f"需要重新爬取文章: {url}")
        
        return article
    
    def process_data_file(self, input_file: str, output_file: str) -> dict:
        """处理数据文件"""
        logger.info(f"开始处理数据文件: {input_file}")
        
        try:
            # 读取数据
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            articles = data.get('articles', [])
            self.stats['total_articles'] = len(articles)
            
            logger.info(f"找到 {len(articles)} 篇文章")
            
            # 处理每篇文章
            processed_articles = []
            recrawl_urls = []
            
            for i, article in enumerate(articles):
                if i % 100 == 0:
                    logger.info(f"处理进度: {i}/{len(articles)}")
                
                processed_article = self.process_article(article)
                processed_articles.append(processed_article)
                
                if processed_article.get('need_recrawl', False):
                    recrawl_urls.append({
                        'url': processed_article['url'],
                        'keyword': processed_article.get('keyword', ''),
                        'year': processed_article.get('year', ''),
                        'reason': 'content_quality_issue'
                    })
            
            # 更新数据
            data['articles'] = processed_articles
            data['cleanup_date'] = datetime.now().isoformat()
            data['cleanup_stats'] = self.stats
            
            # 保存处理后的数据
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存需要重新爬取的URL列表
            if recrawl_urls:
                recrawl_file = output_file.replace('.json', '_recrawl_urls.json')
                with open(recrawl_file, 'w', encoding='utf-8') as f:
                    json.dump(recrawl_urls, f, ensure_ascii=False, indent=2)
                logger.info(f"保存了 {len(recrawl_urls)} 个需要重新爬取的URL到 {recrawl_file}")
            
            logger.info(f"数据清理完成，结果保存到: {output_file}")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"处理数据文件时出错: {e}")
            raise

def main():
    """主函数"""
    processor = DataCleanupProcessor()
    
    # 定义输入输出文件
    input_files = [
        'data/results_content_enhanced.json',
        'data/results_enhanced_with_dates.json'
    ]
    
    for input_file in input_files:
        if os.path.exists(input_file):
            output_file = input_file.replace('.json', '_cleaned.json')
            
            try:
                stats = processor.process_data_file(input_file, output_file)
                
                # 打印统计信息
                print(f"\n=== {input_file} 清理统计 ===")
                print(f"总文章数: {stats['total_articles']}")
                print(f"增强文章数: {stats['enhanced_articles']}")
                print(f"需要重新爬取: {stats['need_recrawl']}")
                print(f"登录页面: {stats['login_pages']}")
                print(f"短内容: {stats['short_content']}")
                print(f"截断内容: {stats['truncated_content']}")
                
            except Exception as e:
                logger.error(f"处理文件 {input_file} 时出错: {e}")
        else:
            logger.warning(f"文件不存在: {input_file}")
    
    print("\n=== 数据清理完成 ===")

if __name__ == "__main__":
    main()