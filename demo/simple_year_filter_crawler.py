#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版时间范围过滤爬虫
专注于展示2010-2025年时间范围过滤功能
"""

import json
import time
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('year_filter_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class YearFilterCrawler:
    """时间范围过滤爬虫"""
    
    def __init__(self, start_year: int = 2010, end_year: int = 2025):
        self.start_year = start_year
        self.end_year = end_year
        self.collected_data = []
        self.year_stats = {year: 0 for year in range(start_year, end_year + 1)}
        
        # 基础搜索查询模板
        self.base_queries = [
            "中国非洲经济合作",
            "中国在非洲投资",
            "中非合作论坛",
            "一带一路非洲",
            "中国援助非洲",
            "中非贸易关系",
            "中国非洲基础设施",
            "中非文化交流",
            "中国非洲医疗合作",
            "中非教育合作"
        ]
        
        # 生成年份特定的搜索查询
        self.year_specific_queries = self._build_year_specific_queries()
        
        logger.info(f"初始化时间范围过滤爬虫，时间范围: {start_year}-{end_year}")
        logger.info(f"生成 {len(self.year_specific_queries)} 个年份特定搜索查询")
    
    def _build_year_specific_queries(self) -> List[str]:
        """构建年份特定的搜索查询"""
        queries = []
        for base_query in self.base_queries:
            for year in range(self.start_year, self.end_year + 1):
                # 添加年份限定符
                queries.append(f"{base_query} {year}")
                # 添加历史限定符
                queries.append(f"{base_query} {year} 历史")
                queries.append(f"{base_query} {year} 档案")
        
        return queries
    
    def _extract_year_from_content(self, content: str) -> int:
        """从内容中提取年份"""
        import re
        
        # 尝试从内容中提取年份
        year_patterns = [
            r'\b(20[1-3][0-9])\b',  # 2010-2039年
            r'\b(19[7-9][0-9])\b',  # 1970-1999年
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, content)
            if matches:
                for match in matches:
                    year = int(match)
                    if self.start_year <= year <= self.end_year:
                        return year
        
        # 如果没有找到有效年份，随机生成一个在时间范围内的年份
        return random.randint(self.start_year, self.end_year)
    
    def _filter_by_year_range(self, year: int) -> bool:
        """根据时间范围过滤年份"""
        return self.start_year <= year <= self.end_year
    
    def generate_mock_article(self, query: str) -> Dict[str, Any]:
        """生成模拟文章数据"""
        # 从查询中提取年份信息
        year = self._extract_year_from_content(query)
        
        # 生成文章标题和内容
        title = f"{query} - 新闻报道"
        content = f"""
        这是一篇关于{query}的模拟新闻报道。
        
        文章发表于{year}年，详细介绍了中国与非洲在相关领域的合作情况。
        文章内容涵盖了政策背景、具体合作项目、影响评估等方面。
        
        该报道反映了{year}年中非关系的发展状况，具有重要的历史参考价值。
        """
        
        # 计算相关性分数
        relevance_score = self._calculate_relevance_score(query, content)
        
        article = {
            'title': title,
            'url': f'https://mock-news.com/article/{year}/{hash(query) % 10000}',
            'content': content,
            'year': year,
            'query': query,
            'relevance_score': relevance_score,
            'content_length': len(content),
            'collection_date': datetime.now().isoformat()
        }
        
        return article
    
    def _calculate_relevance_score(self, query: str, content: str) -> float:
        """计算文章相关性分数"""
        score = 6.0  # 基础分数
        
        # 关键词匹配加分
        keywords = ['中国', '非洲', '合作', '投资', '经济', '发展']
        for keyword in keywords:
            if keyword in query or keyword in content:
                score += 0.5
        
        # 内容长度加分
        if len(content) > 500:
            score += 1.0
        
        # 随机波动
        score += random.uniform(-0.5, 0.5)
        
        return min(10.0, max(1.0, score))
    
    def collect_data(self, target_count: int = 100) -> None:
        """收集数据"""
        logger.info(f"开始收集数据，目标数量: {target_count}")
        logger.info(f"时间范围: {self.start_year}-{self.end_year}")
        
        iteration = 0
        
        while len(self.collected_data) < target_count:
            iteration += 1
            
            # 按顺序选择查询
            query_index = (iteration - 1) % len(self.year_specific_queries)
            query = self.year_specific_queries[query_index]
            
            logger.info(f"第 {iteration} 轮 - 查询: {query}")
            
            # 生成模拟文章
            article = self.generate_mock_article(query)
            
            # 应用时间范围过滤
            if self._filter_by_year_range(article['year']):
                # 检查是否重复
                if not any(a['title'] == article['title'] for a in self.collected_data):
                    self.collected_data.append(article)
                    self.year_stats[article['year']] += 1
                    
                    logger.info(f"✓ 新增 {article['year']}年文章: {article['title'][:30]}...")
                    logger.info(f"  相关性: {article['relevance_score']:.1f}, 长度: {article['content_length']} 字符")
            else:
                logger.warning(f"✗ 文章年份 {article['year']} 超出时间范围，已过滤")
            
            # 显示进度
            if iteration % 10 == 0:
                self._log_progress()
            
            # 避免过于频繁
            time.sleep(0.1)
            
            # 每20条保存一次
            if iteration % 20 == 0:
                self.save_data()
        
        logger.info("数据收集完成")
        self._log_final_statistics()
        self.save_data()
    
    def _log_progress(self) -> None:
        """记录进度"""
        total = len(self.collected_data)
        logger.info(f"=== 当前进度 ===")
        logger.info(f"总收集文章数: {total}")
        
        # 显示年份分布
        for year in sorted(self.year_stats.keys()):
            count = self.year_stats[year]
            if count > 0:
                percentage = (count / total * 100) if total > 0 else 0
                logger.info(f"{year}年: {count} 篇 ({percentage:.1f}%)")
        
        logger.info("================")
    
    def _log_final_statistics(self) -> None:
        """记录最终统计信息"""
        total = len(self.collected_data)
        avg_content_length = sum(a['content_length'] for a in self.collected_data) / total if total > 0 else 0
        avg_relevance = sum(a['relevance_score'] for a in self.collected_data) / total if total > 0 else 0
        
        logger.info("=== 最终统计 ===")
        logger.info(f"总文章数: {total}")
        logger.info(f"平均内容长度: {avg_content_length:.0f} 字符")
        logger.info(f"平均相关性: {avg_relevance:.1f}")
        logger.info(f"时间范围: {self.start_year}-{self.end_year}")
        
        # 年份分布
        logger.info("年份分布:")
        for year in sorted(self.year_stats.keys()):
            count = self.year_stats[year]
            if count > 0:
                percentage = (count / total * 100) if total > 0 else 0
                logger.info(f"  {year}年: {count} 篇 ({percentage:.1f}%)")
        
        logger.info("================")
    
    def save_data(self, filename: str = 'year_filter_data.json') -> None:
        """保存数据"""
        try:
            data_to_save = {
                'metadata': {
                    'total_articles': len(self.collected_data),
                    'collection_date': datetime.now().isoformat(),
                    'time_range': f'{self.start_year}-{self.end_year}',
                    'year_statistics': self.year_stats,
                    'description': f'{self.start_year}-{self.end_year}年时间范围过滤测试数据'
                },
                'articles': self.collected_data
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            
            # 保存为Excel
            self._save_to_excel(filename.replace('.json', '.xlsx'))
            
            logger.info(f"数据已保存到 {filename}")
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
    
    def _save_to_excel(self, filename: str) -> None:
        """保存为Excel格式"""
        try:
            if not self.collected_data:
                return
            
            # 创建DataFrame
            df_data = []
            for article in self.collected_data:
                df_data.append({
                    '标题': article['title'],
                    '年份': article['year'],
                    '相关性分数': article['relevance_score'],
                    '内容长度': article['content_length'],
                    '查询关键词': article['query'],
                    'URL': article['url'],
                    '收集时间': article['collection_date']
                })
            
            df = pd.DataFrame(df_data)
            df.to_excel(filename, index=False, engine='openpyxl')
            
            logger.info(f"Excel数据已保存到 {filename}")
            
        except Exception as e:
            logger.error(f"保存Excel数据失败: {e}")
    
    def generate_report(self) -> str:
        """生成详细报告"""
        if not self.collected_data:
            return "暂无数据"
        
        total = len(self.collected_data)
        avg_content_length = sum(a['content_length'] for a in self.collected_data) / total
        avg_relevance = sum(a['relevance_score'] for a in self.collected_data) / total
        
        report = f"""
=== 时间范围过滤爬虫报告 ===

数据收集统计:
- 总文章数: {total} 篇
- 时间范围: {self.start_year}-{self.end_year} 年
- 平均内容长度: {avg_content_length:.0f} 字符
- 平均相关性分数: {avg_relevance:.1f}/10.0

年份分布统计:
"""
        
        # 添加年份分布
        for year in sorted(self.year_stats.keys()):
            count = self.year_stats[year]
            if count > 0:
                percentage = (count / total * 100)
                report += f"- {year}年: {count} 篇 ({percentage:.1f}%)\n"
        
        # 添加高质量文章列表
        high_quality = [a for a in self.collected_data if a['relevance_score'] >= 8.0]
        if high_quality:
            report += f"\n高质量文章 (相关性≥8.0): {len(high_quality)} 篇\n"
            for i, article in enumerate(high_quality[:5], 1):
                report += f"{i}. {article['title'][:40]}... (相关性: {article['relevance_score']:.1f}, {article['year']}年)\n"
        
        report += "\n=== 报告结束 ==="
        
        return report

def main():
    """主函数"""
    # 创建爬虫实例
    crawler = YearFilterCrawler(start_year=2010, end_year=2025)
    
    # 收集数据
    crawler.collect_data(target_count=50)  # 收集50篇文章进行演示
    
    # 生成报告
    report = crawler.generate_report()
    print(report)
    
    # 保存报告到文件
    with open('year_filter_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info("程序执行完成")

if __name__ == "__main__":
    main()