#!/usr/bin/env python3
"""
数据迁移脚本 - 将分布式爬虫爬取的数据迁移到 real_african_news.json 文件
"""

import json
import os
import glob
import logging
from datetime import datetime
from typing import List, Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataMigrator:
    """数据迁移器"""
    
    def __init__(self):
        self.data_dir = 'data'
        self.results_dir = os.path.join(self.data_dir, 'results')
        self.target_file = os.path.join(self.results_dir, 'real_african_news.json')
        self.backup_dir = os.path.join(self.data_dir, 'backup')
        
        # 确保目录存在
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def find_crawled_data_files(self) -> List[str]:
        """查找所有爬取的数据文件"""
        data_files = []
        
        # 查找分布式爬虫结果文件
        distributed_patterns = [
            os.path.join(self.results_dir, 'distributed_*.json'),
            os.path.join(self.results_dir, 'worker_*.json'),
            os.path.join(self.results_dir, 'results_*.json'),
            os.path.join(self.results_dir, '*.json.backup'),
        ]
        
        for pattern in distributed_patterns:
            data_files.extend(glob.glob(pattern))
        
        # 查找备份目录中的文件
        backup_patterns = [
            os.path.join(self.backup_dir, '*.json'),
            os.path.join(self.backup_dir, '*.json.backup'),
        ]
        
        for pattern in backup_patterns:
            data_files.extend(glob.glob(pattern))
        
        # 移除目标文件本身
        if self.target_file in data_files:
            data_files.remove(self.target_file)
        
        logger.info(f"找到 {len(data_files)} 个数据文件")
        return data_files
    
    def load_json_data(self, file_path: str) -> List[Dict[str, Any]]:
        """加载JSON数据文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 处理不同的数据格式
            if isinstance(data, dict):
                # 如果是字典格式，检查是否有results字段
                if 'results' in data:
                    return data['results']
                elif 'data' in data:
                    return data['data']
                else:
                    # 将字典转换为列表
                    return [data]
            elif isinstance(data, list):
                return data
            else:
                logger.warning(f"文件 {file_path} 包含未知格式的数据")
                return []
                
        except Exception as e:
            logger.error(f"加载文件 {file_path} 失败: {e}")
            return []
    
    def extract_articles_from_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从数据中提取文章信息"""
        articles = []
        
        for item in data:
            # 检查是否是文章数据
            if isinstance(item, dict):
                # 检查是否有文章的关键字段
                has_title = 'title' in item and item['title']
                has_content = 'content' in item and item['content']
                has_url = 'url' in item and item['url']
                
                if has_title and has_content and has_url:
                    # 标准化文章格式
                    article = {
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'content': item.get('content', ''),
                        'source': item.get('source', ''),
                        'publish_date': item.get('publish_date', ''),
                        'keyword': item.get('keyword', ''),
                        'year': item.get('year', 2024),
                        'crawl_time': item.get('crawl_time', datetime.now().isoformat()),
                        'crawl_method': item.get('crawl_method', 'distributed'),
                        'anti_crawler_detected': item.get('anti_crawler_detected', False),
                        'anti_crawler_type': item.get('anti_crawler_type', None),
                        'quality_score': item.get('quality_score', 0.0),
                        'quality_issues': item.get('quality_issues', []),
                        'worker_id': item.get('worker_id', ''),
                        'task_id': item.get('task_id', '')
                    }
                    articles.append(article)
                
                # 检查是否有嵌套的results字段
                if 'results' in item and isinstance(item['results'], list):
                    nested_articles = self.extract_articles_from_data(item['results'])
                    articles.extend(nested_articles)
        
        return articles
    
    def load_existing_data(self) -> List[Dict[str, Any]]:
        """加载现有的目标文件数据"""
        if not os.path.exists(self.target_file):
            return []
        
        try:
            with open(self.target_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                
            if isinstance(existing_data, list):
                return existing_data
            else:
                logger.warning(f"目标文件 {self.target_file} 格式不正确")
                return []
                
        except Exception as e:
            logger.error(f"加载现有数据失败: {e}")
            return []
    
    def merge_and_deduplicate(self, existing_articles: List[Dict[str, Any]], 
                             new_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并并去重文章数据"""
        # 使用URL作为唯一标识符进行去重
        seen_urls = set()
        merged_articles = []
        
        # 添加现有文章
        for article in existing_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged_articles.append(article)
        
        # 添加新文章
        for article in new_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged_articles.append(article)
        
        logger.info(f"合并后文章总数: {len(merged_articles)} (现有: {len(existing_articles)}, 新增: {len(new_articles)})")
        return merged_articles
    
    def save_merged_data(self, articles: List[Dict[str, Any]]) -> bool:
        """保存合并后的数据"""
        try:
            # 创建备份
            if os.path.exists(self.target_file):
                backup_file = os.path.join(
                    self.backup_dir, 
                    f'real_african_news_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                )
                os.rename(self.target_file, backup_file)
                logger.info(f"已创建备份: {backup_file}")
            
            # 保存新数据
            with open(self.target_file, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            
            logger.info(f"数据已保存到: {self.target_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            return False
    
    def migrate_data(self) -> bool:
        """执行数据迁移"""
        logger.info("开始数据迁移...")
        
        # 1. 查找所有数据文件
        data_files = self.find_crawled_data_files()
        if not data_files:
            logger.warning("未找到任何数据文件")
            return False
        
        # 2. 加载所有数据
        all_articles = []
        for file_path in data_files:
            logger.info(f"处理文件: {file_path}")
            data = self.load_json_data(file_path)
            articles = self.extract_articles_from_data(data)
            all_articles.extend(articles)
            logger.info(f"从 {file_path} 提取到 {len(articles)} 篇文章")
        
        # 3. 加载现有数据
        existing_articles = self.load_existing_data()
        logger.info(f"现有文件包含 {len(existing_articles)} 篇文章")
        
        # 4. 合并并去重
        merged_articles = self.merge_and_deduplicate(existing_articles, all_articles)
        
        # 5. 保存合并后的数据
        if self.save_merged_data(merged_articles):
            logger.info(f"数据迁移完成! 总文章数: {len(merged_articles)}")
            
            # 显示迁移统计
            new_articles_count = len(merged_articles) - len(existing_articles)
            logger.info(f"新增文章: {new_articles_count}")
            logger.info(f"处理文件数: {len(data_files)}")
            
            return True
        else:
            logger.error("数据迁移失败")
            return False

def main():
    """主函数"""
    migrator = DataMigrator()
    
    try:
        success = migrator.migrate_data()
        if success:
            print("数据迁移成功完成!")
        else:
            print("数据迁移失败，请检查日志")
            
    except Exception as e:
        logger.error(f"数据迁移过程中发生错误: {e}")
        print(f"错误: {e}")

if __name__ == "__main__":
    main()