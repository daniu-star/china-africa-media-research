#!/usr/bin/env python3
"""
中国与非洲关系爬虫 - 专门处理中国相关关键词的多语言搜索
"""

import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChinaAfricaCrawler:
    """中国与非洲关系爬虫类"""
    
    def __init__(self, keywords_file: str = 'china_africa_keywords.json'):
        """初始化爬虫"""
        self.keywords_file = keywords_file
        self.keywords_data = self.load_keywords()
        
        # 创建输出目录
        os.makedirs('china_africa_results', exist_ok=True)
        
        logger.info(f"中国与非洲关系爬虫初始化完成")
        logger.info(f"关键词总数: {self.keywords_data['metadata']['total_keywords']}")
        logger.info(f"支持语言: {', '.join(self.keywords_data['metadata']['languages'])}")
    
    def load_keywords(self) -> Dict[str, Any]:
        """加载关键词配置"""
        try:
            with open(self.keywords_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载关键词文件失败: {e}")
            # 返回默认关键词
            return self.get_default_keywords()
    
    def get_default_keywords(self) -> Dict[str, Any]:
        """获取默认关键词"""
        return {
            "chinese_keywords": {
                "china_related": {
                    "english": ["China", "South China Sea", "Belt and Road Initiative"],
                    "swahili": ["Uchina", "Bahari ya Kusini ya Uchina", "Mradi wa Ukanda na Barabara"]
                }
            },
            "metadata": {
                "total_keywords": 5,
                "languages": ["english", "swahili"],
                "categories": ["china_related"],
                "created_at": datetime.now().isoformat(),
                "description": "默认中国关键词库"
            }
        }
    
    def generate_search_tasks(self) -> List[Dict[str, Any]]:
        """生成搜索任务"""
        tasks = []
        task_id_counter = 1
        
        # 处理中国相关关键词
        china_related = self.keywords_data['chinese_keywords']['china_related']
        for language, keywords in china_related.items():
            for keyword in keywords:
                task = {
                    "task_id": f"china_related_{language}_{task_id_counter}",
                    "keyword": keyword,
                    "language": language,
                    "category": "china_related",
                    "priority": "high",
                    "created_at": datetime.now().isoformat(),
                    "status": "pending"
                }
                tasks.append(task)
                task_id_counter += 1
        
        # 处理中国省份关键词
        if 'chinese_provinces' in self.keywords_data['chinese_keywords']:
            provinces = self.keywords_data['chinese_keywords']['chinese_provinces']['english']
            for province in provinces:
                task = {
                    "task_id": f"province_{task_id_counter}",
                    "keyword": province,
                    "language": "english",
                    "category": "chinese_provinces",
                    "priority": "medium",
                    "created_at": datetime.now().isoformat(),
                    "status": "pending"
                }
                tasks.append(task)
                task_id_counter += 1
        
        # 处理搜索分类
        if 'search_categories' in self.keywords_data['chinese_keywords']:
            categories = self.keywords_data['chinese_keywords']['search_categories']
            for category_name, keywords in categories.items():
                for keyword in keywords:
                    task = {
                        "task_id": f"{category_name}_{task_id_counter}",
                        "keyword": keyword,
                        "language": "english",
                        "category": category_name,
                        "priority": "medium",
                        "created_at": datetime.now().isoformat(),
                        "status": "pending"
                    }
                    tasks.append(task)
                    task_id_counter += 1
        
        logger.info(f"生成了 {len(tasks)} 个中国与非洲关系搜索任务")
        return tasks
    
    def save_tasks_to_file(self, tasks: List[Dict[str, Any]], filename: str = None):
        """保存任务到文件"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"china_africa_results/china_africa_tasks_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "tasks": tasks,
                    "metadata": {
                        "total_tasks": len(tasks),
                        "generated_at": datetime.now().isoformat(),
                        "description": "中国与非洲关系爬虫任务列表"
                    }
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"任务列表已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存任务列表失败: {e}")
    
    def integrate_with_distributed_system(self):
        """集成到分布式爬虫系统"""
        try:
            # 生成任务
            tasks = self.generate_search_tasks()
            
            # 保存任务文件
            self.save_tasks_to_file(tasks)
            
            # 创建与分布式系统兼容的任务格式
            distributed_tasks = []
            for task in tasks:
                distributed_task = {
                    "task_id": task["task_id"],
                    "keyword": task["keyword"],
                    "priority": task["priority"],
                    "created_at": task["created_at"],
                    "status": "pending",
                    "metadata": {
                        "language": task["language"],
                        "category": task["category"],
                        "source": "china_africa_crawler"
                    }
                }
                distributed_tasks.append(distributed_task)
            
            # 保存分布式兼容格式
            distributed_filename = "china_africa_results/distributed_tasks.json"
            with open(distributed_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "tasks": distributed_tasks,
                    "metadata": {
                        "total_tasks": len(distributed_tasks),
                        "generated_at": datetime.now().isoformat(),
                        "system": "distributed_crawler"
                    }
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"分布式系统兼容任务已保存到: {distributed_filename}")
            logger.info(f"可以导入到分布式爬虫系统进行大规模数据采集")
            
            return distributed_tasks
            
        except Exception as e:
            logger.error(f"集成到分布式系统失败: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        tasks = self.generate_search_tasks()
        
        # 按语言统计
        language_stats = {}
        category_stats = {}
        
        for task in tasks:
            lang = task['language']
            cat = task['category']
            
            if lang not in language_stats:
                language_stats[lang] = 0
            language_stats[lang] += 1
            
            if cat not in category_stats:
                category_stats[cat] = 0
            category_stats[cat] += 1
        
        return {
            "total_tasks": len(tasks),
            "languages": language_stats,
            "categories": category_stats,
            "keywords_file": self.keywords_file,
            "generated_at": datetime.now().isoformat()
        }

def main():
    """主函数"""
    try:
        # 创建爬虫实例
        crawler = ChinaAfricaCrawler()
        
        # 显示统计信息
        stats = crawler.get_statistics()
        print("=== 中国与非洲关系爬虫统计信息 ===")
        print(f"总任务数: {stats['total_tasks']}")
        print("语言分布:")
        for lang, count in stats['languages'].items():
            print(f"  {lang}: {count}")
        print("分类分布:")
        for cat, count in stats['categories'].items():
            print(f"  {cat}: {count}")
        
        # 集成到分布式系统
        print("\n正在集成到分布式爬虫系统...")
        distributed_tasks = crawler.integrate_with_distributed_system()
        
        print(f"\n✅ 中国与非洲关系爬虫初始化完成!")
        print(f"📊 生成了 {len(distributed_tasks)} 个搜索任务")
        print(f"🌍 支持 {len(stats['languages'])} 种语言")
        print(f"📁 任务文件已保存到 china_africa_results/ 目录")
        print(f"🔗 可以导入到分布式爬虫系统进行大规模数据采集")
        
    except Exception as e:
        logger.error(f"中国与非洲关系爬虫运行失败: {e}")
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()