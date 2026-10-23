"""
数据存储和检索性能优化系统
实现高效的数据存储、索引和检索优化
"""

import json
import os
import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import hashlib
from collections import defaultdict

class DataStorageOptimizer:
    """数据存储和检索性能优化系统"""
    
    def __init__(self, data_dir: str = "data", db_path: str = "data/articles.db"):
        self.data_dir = data_dir
        self.db_path = db_path
        self.optimization_config = {
            "batch_size": 1000,
            "index_fields": ["title", "keywords", "year", "country", "category"],
            "cache_size": 10000,
            "compression": True,
            "partition_by_year": True,
            "enable_fulltext_search": True
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库和索引"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建主表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT UNIQUE,
                title TEXT NOT NULL,
                content TEXT,
                summary TEXT,
                url TEXT,
                year INTEGER,
                month INTEGER,
                country TEXT,
                category TEXT,
                keywords TEXT,
                source TEXT,
                quality_score REAL,
                content_length INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_year ON articles(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_country ON articles(country)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON articles(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality ON articles(quality_score)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON articles(created_at)")
        
        # 启用全文搜索（如果支持）
        try:
            cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(title, content, keywords)")
        except sqlite3.OperationalError:
            print("警告: 不支持FTS5，使用普通索引")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_title ON articles(title)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_keywords ON articles(keywords)")
        
        conn.commit()
        conn.close()
    
    def import_json_data(self, json_file: str) -> Dict[str, Any]:
        """导入JSON数据到数据库"""
        
        start_time = time.time()
        
        if not os.path.exists(json_file):
            return {"success": False, "error": f"文件不存在: {json_file}"}
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            return {"success": False, "error": f"读取JSON文件失败: {e}"}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        imported_count = 0
        skipped_count = 0
        
        # 批量插入
        batch_size = self.optimization_config["batch_size"]
        batch_data = []
        
        for item in data:
            # 生成唯一ID
            article_id = self._generate_article_id(item)
            
            # 检查是否已存在
            cursor.execute("SELECT id FROM articles WHERE article_id = ?", (article_id,))
            if cursor.fetchone():
                skipped_count += 1
                continue
            
            # 解析发布日期
            publish_date = item.get('publish_date', '')
            year = item.get('year', 0)
            month = 0
            
            # 增强日期解析逻辑，支持多种日期格式
            if publish_date and publish_date != 'unknown':
                year, month = self._parse_date_to_year_month(publish_date)
            
            # 如果从日期解析失败，尝试从年份字段获取
            if year == 0 and item.get('year', 0) > 0:
                year = item.get('year', 0)
            
            # 提取国家信息
            country = self._extract_country_from_source(item.get('source', ''))
            
            # 提取类别信息
            category = self._extract_category_from_keyword(item.get('keyword', ''))
            
            # 计算质量分数
            content = item.get('content', '')
            quality_score = self._calculate_quality_score(content, len(content))
            
            # 准备插入数据
            batch_data.append((
                article_id,
                item.get('title', ''),
                content,
                item.get('summary', ''),
                item.get('url', ''),
                year,
                month,
                country,
                category,
                json.dumps([item.get('keyword', '')], ensure_ascii=False),
                item.get('source', ''),
                quality_score,
                len(content)
            ))
            
            # 批量插入
            if len(batch_data) >= batch_size:
                try:
                    cursor.executemany("""
                        INSERT OR IGNORE INTO articles (
                            article_id, title, content, summary, url, year, month, 
                            country, category, keywords, source, quality_score, content_length
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch_data)
                    imported_count += len(batch_data)
                    batch_data = []
                except sqlite3.IntegrityError:
                    # 如果批量插入失败，尝试逐条插入
                    for single_item in batch_data:
                        try:
                            cursor.execute("""
                                INSERT OR IGNORE INTO articles (
                                    article_id, title, content, summary, url, year, month, 
                                    country, category, keywords, source, quality_score, content_length
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, single_item)
                            imported_count += 1
                        except sqlite3.IntegrityError:
                            skipped_count += 1
                    batch_data = []
        
        # 插入剩余数据
        if batch_data:
            try:
                cursor.executemany("""
                    INSERT OR IGNORE INTO articles (
                        article_id, title, content, summary, url, year, month, 
                        country, category, keywords, source, quality_score, content_length
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch_data)
                imported_count += len(batch_data)
            except sqlite3.IntegrityError:
                for single_item in batch_data:
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO articles (
                                article_id, title, content, summary, url, year, month, 
                                country, category, keywords, source, quality_score, content_length
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, single_item)
                        imported_count += 1
                    except sqlite3.IntegrityError:
                        skipped_count += 1
        
        conn.commit()
        
        # 更新全文搜索索引
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO articles_fts (rowid, title, content, keywords)
                SELECT id, title, content, keywords FROM articles 
                WHERE id > (SELECT COALESCE(MAX(rowid), 0) FROM articles_fts)
            """)
            conn.commit()
        except sqlite3.OperationalError:
            pass  # 如果不支持FTS
        
        conn.close()
        
        elapsed_time = time.time() - start_time
        
        return {
            "success": True,
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "elapsed_time": elapsed_time,
            "performance": f"{imported_count / elapsed_time:.2f} 条/秒" if elapsed_time > 0 else "N/A"
        }
    
    def search_articles(self, query: str, filters: Dict[str, Any] = None, 
                       limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """搜索文章"""
        
        start_time = time.time()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if query:
            try:
                # 使用全文搜索
                conditions.append("""
                    id IN (
                        SELECT rowid FROM articles_fts 
                        WHERE articles_fts MATCH ?
                    )
                """)
                params.append(query)
            except sqlite3.OperationalError:
                # 回退到普通搜索
                conditions.append("(title LIKE ? OR keywords LIKE ?)")
                params.extend([f"%{query}%"] * 2)
        
        if filters:
            for field, value in filters.items():
                if field == "year_range":
                    conditions.append("year BETWEEN ? AND ?")
                    params.extend(value)
                elif field == "quality_min":
                    conditions.append("quality_score >= ?")
                    params.append(value)
                elif field == "country":
                    conditions.append("country = ?")
                    params.append(value)
                elif field == "category":
                    conditions.append("category = ?")
                    params.append(value)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 执行查询
        sql = f"""
            SELECT * FROM articles 
            WHERE {where_clause}
            ORDER BY quality_score DESC, created_at DESC
            LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        # 获取总数
        count_sql = f"SELECT COUNT(*) FROM articles WHERE {where_clause}"
        cursor.execute(count_sql, params[:-2])  # 排除LIMIT和OFFSET参数
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        elapsed_time = time.time() - start_time
        
        # 避免除零错误
        performance_rate = len(results) / elapsed_time if elapsed_time > 0 else len(results)
        
        return {
            "query": query,
            "filters": filters,
            "results": [self._row_to_dict(row, cursor.description) for row in results],
            "total_count": total_count,
            "returned_count": len(results),
            "elapsed_time": elapsed_time,
            "performance": f"{performance_rate:.2f} 条/秒"
        }
    
    def analyze_performance(self) -> Dict[str, Any]:
        """分析数据库性能"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取表统计信息
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT country) FROM articles")
        unique_countries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT category) FROM articles")
        unique_categories = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(year), MAX(year) FROM articles WHERE year > 0")
        year_range = cursor.fetchone()
        
        # 索引使用情况
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type = 'index' AND name LIKE 'idx_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        # 表大小
        cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_articles": total_articles,
            "unique_countries": unique_countries,
            "unique_categories": unique_categories,
            "year_range": {"min": year_range[0], "max": year_range[1]} if year_range[0] else None,
            "indexes": indexes,
            "database_size": f"{db_size / 1024 / 1024:.2f} MB",
            "optimization_recommendations": self._generate_optimization_recommendations(total_articles)
        }
    
    def optimize_database(self) -> Dict[str, Any]:
        """优化数据库性能"""
        
        start_time = time.time()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 执行优化操作
        cursor.execute("VACUUM")  # 清理碎片
        cursor.execute("ANALYZE")  # 更新统计信息
        
        # 重新构建索引
        cursor.execute("REINDEX")
        
        conn.commit()
        conn.close()
        
        elapsed_time = time.time() - start_time
        
        return {
            "success": True,
            "optimization_operations": ["VACUUM", "ANALYZE", "REINDEX"],
            "elapsed_time": elapsed_time
        }
    
    def _generate_article_id(self, item: Dict[str, Any]) -> str:
        """生成文章唯一ID"""
        
        content = f"{item.get('title', '')}{item.get('url', '')}{item.get('year', 0)}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _row_to_dict(self, row: tuple, description) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        
        return {desc[0]: value for desc, value in zip(description, row)}
    
    def _extract_country_from_source(self, source: str) -> str:
        """从来源信息中提取国家"""
        
        country_mapping = {
            'egypt': '埃及', 'eg': '埃及', 'ahram': '埃及',
            'algeria': '阿尔及利亚', 'dz': '阿尔及利亚', 'algerie': '阿尔及利亚',
            'tunisia': '突尼斯', 'tn': '突尼斯', 'tunisie': '突尼斯',
            'nigeria': '尼日利亚', 'ng': '尼日利亚', 'vanguard': '尼日利亚',
            'ghana': '加纳', 'gh': '加纳', 'ghanaweb': '加纳',
            'kenya': '肯尼亚', 'ke': '肯尼亚', 'nation': '肯尼亚',
            'tanzania': '坦桑尼亚', 'tz': '坦桑尼亚', 'dailynews': '坦桑尼亚',
            'rwanda': '卢旺达', 'rw': '卢旺达', 'newtimes': '卢旺达',
            'uganda': '乌干达', 'ug': '乌干达', 'monitor': '乌干达',
            'south africa': '南非', 'za': '南非', 'news24': '南非',
            'china': '中国', 'cn': '中国', 'xinhua': '中国', 'people': '中国'
        }
        
        source_lower = source.lower()
        for key, country in country_mapping.items():
            if key in source_lower:
                return country
        
        return '未知'
    
    def _extract_category_from_keyword(self, keyword: str) -> str:
        """从关键词中提取类别"""
        
        category_mapping = {
            'description': '综合', 'news': '新闻', 'economy': '经济',
            'business': '商业', 'technology': '技术', 'investment': '投资',
            'infrastructure': '基础设施', 'development': '发展', 'trade': '贸易',
            'finance': '金融', 'agriculture': '农业', 'energy': '能源',
            'education': '教育', 'health': '健康', 'culture': '文化'
        }
        
        keyword_lower = keyword.lower()
        for key, category in category_mapping.items():
            if key in keyword_lower:
                return category
        
        return '其他'
    
    def _calculate_quality_score(self, content: str, content_length: int) -> float:
        """计算内容质量分数"""
        
        score = 0.5  # 基础分数
        
        # 根据内容长度评分
        if content_length > 1000:
            score += 0.3
        elif content_length > 500:
            score += 0.2
        elif content_length > 100:
            score += 0.1
        
        # 根据内容质量评分
        if '内容提取失败' not in content and 'error' not in content.lower():
            score += 0.2
        
        # 限制在0-1之间
        return min(max(score, 0), 1)
    
    def _parse_date_to_year_month(self, date_string: str) -> tuple:
        """解析日期字符串为年份和月份，支持多种日期格式"""
        
        year = 0
        month = 0
        
        if not date_string or date_string == 'unknown':
            return year, month
        
        try:
            # 尝试解析标准日期格式
            date_formats = [
                '%Y-%m-%d',
                '%Y-%m',
                '%Y/%m/%d',
                '%Y/%m',
                '%d-%m-%Y',
                '%d/%m/%Y',
                '%B %d, %Y',  # March 15, 2024
                '%b %d, %Y',  # Mar 15, 2024
                '%d %B %Y',   # 15 March 2024
                '%d %b %Y',   # 15 Mar 2024
            ]
            
            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_string, fmt)
                    break
                except ValueError:
                    continue
            
            if parsed_date:
                year = parsed_date.year
                month = parsed_date.month
                return year, month
            
            # 尝试从字符串中提取年份和月份
            import re
            
            # 匹配年份（4位数字）
            year_match = re.search(r'\b(19|20)\d{2}\b', date_string)
            if year_match:
                year = int(year_match.group())
            
            # 匹配月份（1-2位数字或月份名称）
            month_mapping = {
                'january': 1, 'jan': 1, '1': 1, '01': 1,
                'february': 2, 'feb': 2, '2': 2, '02': 2,
                'march': 3, 'mar': 3, '3': 3, '03': 3,
                'april': 4, 'apr': 4, '4': 4, '04': 4,
                'may': 5, '5': 5, '05': 5,
                'june': 6, 'jun': 6, '6': 6, '06': 6,
                'july': 7, 'jul': 7, '7': 7, '07': 7,
                'august': 8, 'aug': 8, '8': 8, '08': 8,
                'september': 9, 'sep': 9, '9': 9, '09': 9,
                'october': 10, 'oct': 10, '10': 10,
                'november': 11, 'nov': 11, '11': 11,
                'december': 12, 'dec': 12, '12': 12
            }
            
            # 查找月份数字
            month_match = re.search(r'\b(0?[1-9]|1[0-2])\b', date_string)
            if month_match:
                month = int(month_match.group())
            else:
                # 查找月份名称
                for month_name, month_num in month_mapping.items():
                    if month_name in date_string.lower():
                        month = month_num
                        break
            
        except Exception as e:
            # 如果解析失败，返回默认值
            pass
        
        return year, month
    
    def _generate_optimization_recommendations(self, total_articles: int) -> List[str]:
        """生成优化建议"""
        
        recommendations = []
        
        if total_articles > 100000:
            recommendations.append("考虑使用分区表按年份分割数据")
            recommendations.append("实现数据归档策略，将旧数据移至归档表")
        
        if total_articles > 50000:
            recommendations.append("增加缓存大小以提高查询性能")
            recommendations.append("考虑使用更强大的数据库引擎如PostgreSQL")
        
        if total_articles > 10000:
            recommendations.append("定期执行数据库优化操作（VACUUM, ANALYZE）")
            recommendations.append("监控查询性能，优化慢查询")
        
        recommendations.append("确保所有常用查询字段都有索引")
        recommendations.append("定期备份数据库文件")
        recommendations.append("监控数据库文件大小，避免过大影响性能")
        
        return recommendations

def main():
    """主函数"""
    
    print("=" * 60)
    print("数据存储和检索性能优化系统")
    print("=" * 60)
    
    optimizer = DataStorageOptimizer()
    
    # 分析当前性能
    print("\n1. 分析当前数据库性能...")
    performance = optimizer.analyze_performance()
    
    print(f"  总文章数: {performance['total_articles']}")
    print(f"  唯一国家数: {performance['unique_countries']}")
    print(f"  唯一类别数: {performance['unique_categories']}")
    if performance['year_range']:
        print(f"  年份范围: {performance['year_range']['min']} - {performance['year_range']['max']}")
    print(f"  数据库大小: {performance['database_size']}")
    print(f"  索引数量: {len(performance['indexes'])}")
    
    # 导入示例数据（如果数据库为空）
    if performance['total_articles'] == 0:
        print("\n2. 导入示例数据...")
        json_files = [f for f in os.listdir("data") if f.endswith('.json') and 'results' in f]
        
        if json_files:
            sample_file = os.path.join("data", json_files[0])
            import_result = optimizer.import_json_data(sample_file)
            
            if import_result["success"]:
                print(f"  导入成功: {import_result['imported_count']} 条记录")
                print(f"  跳过重复: {import_result['skipped_count']} 条记录")
                print(f"  导入性能: {import_result['performance']}")
            else:
                print(f"  导入失败: {import_result['error']}")
    
    # 测试搜索性能
    print("\n3. 测试搜索性能...")
    search_results = optimizer.search_articles(
        query="非洲 投资",
        filters={"quality_min": 0.7, "year_range": [2010, 2025]},
        limit=10
    )
    
    print(f"  搜索查询: {search_results['query']}")
    print(f"  返回结果: {search_results['returned_count']} 条")
    print(f"  总匹配数: {search_results['total_count']} 条")
    print(f"  搜索性能: {search_results['performance']}")
    
    # 优化数据库
    print("\n4. 优化数据库性能...")
    optimization_result = optimizer.optimize_database()
    
    if optimization_result["success"]:
        print(f"  优化操作: {', '.join(optimization_result['optimization_operations'])}")
        print(f"  优化耗时: {optimization_result['elapsed_time']:.2f} 秒")
    
    # 生成优化报告
    print("\n5. 优化建议:")
    for i, recommendation in enumerate(performance['optimization_recommendations'], 1):
        print(f"  {i}. {recommendation}")
    
    # 保存性能报告
    report = {
        "generated_at": datetime.now().isoformat(),
        "performance_analysis": performance,
        "search_test": search_results,
        "optimization_result": optimization_result
    }
    
    report_file = os.path.join("data", "storage_optimization_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n性能报告已保存到: {report_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()