"""
数据质量增强器 - 专门处理登录页面和内容过短问题
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any
from login_page_filter import LoginPageFilter

class DataQualityEnhancer:
    """数据质量增强器"""
    
    def __init__(self, min_content_length: int = 200):
        """
        初始化数据质量增强器
        
        Args:
            min_content_length: 最小内容长度阈值
        """
        self.min_content_length = min_content_length
        self.page_filter = LoginPageFilter()
        
        # 统计信息
        self.stats = {
            'total_articles': 0,
            'filtered_articles': 0,
            'login_pages_removed': 0,
            'navigation_pages_removed': 0,
            'short_content_removed': 0,
            'duplicates_removed': 0,
            'quality_improved': 0
        }
    
    def load_data_files(self, data_dir: str = "data/results") -> List[Dict[str, Any]]:
        """加载所有数据文件"""
        all_articles = []
        
        if not os.path.exists(data_dir):
            print(f"数据目录不存在: {data_dir}")
            return all_articles
        
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            all_articles.extend(data)
                        elif isinstance(data, dict) and 'articles' in data:
                            all_articles.extend(data['articles'])
                except Exception as e:
                    print(f"加载文件失败 {filename}: {e}")
        
        self.stats['total_articles'] = len(all_articles)
        print(f"加载到 {len(all_articles)} 篇文章")
        return all_articles
    
    def filter_login_and_navigation_pages(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤登录页面和导航页面"""
        filtered_articles = []
        
        for article in articles:
            content = article.get('content', '')
            url = article.get('url', '')
            
            # 使用页面过滤器分析
            result = self.page_filter.analyze_page(content, url)
            
            if result['page_type'] == 'login_page':
                self.stats['login_pages_removed'] += 1
                continue
            elif result['page_type'] == 'navigation_page':
                self.stats['navigation_pages_removed'] += 1
                continue
            
            filtered_articles.append(article)
        
        print(f"过滤登录/导航页面后剩余: {len(filtered_articles)} 篇文章")
        return filtered_articles
    
    def filter_short_content(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤内容过短的文章"""
        filtered_articles = []
        
        for article in articles:
            content = article.get('content', '')
            
            # 计算有效内容长度
            clean_content = self.clean_text(content)
            
            if len(clean_content) < self.min_content_length:
                self.stats['short_content_removed'] += 1
                continue
            
            filtered_articles.append(article)
        
        print(f"过滤短内容后剩余: {len(filtered_articles)} 篇文章")
        return filtered_articles
    
    def remove_duplicates(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去除重复文章"""
        seen_urls = set()
        unique_articles = []
        
        for article in articles:
            url = article.get('url', '')
            
            if url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
            else:
                self.stats['duplicates_removed'] += 1
        
        print(f"去重后剩余: {len(unique_articles)} 篇文章")
        return unique_articles
    
    def improve_content_quality(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """改进内容质量"""
        improved_articles = []
        
        for article in articles:
            improved_article = self._enhance_article(article)
            if improved_article:
                improved_articles.append(improved_article)
                self.stats['quality_improved'] += 1
        
        print(f"质量改进后: {len(improved_articles)} 篇文章")
        return improved_articles
    
    def _enhance_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """增强单篇文章质量"""
        enhanced_article = article.copy()
        
        # 清理标题
        title = article.get('title', '')
        if title:
            enhanced_article['title'] = self.clean_text(title)
        
        # 清理内容
        content = article.get('content', '')
        if content:
            enhanced_article['content'] = self.clean_text(content)
        
        # 标准化日期格式
        date = article.get('date', '')
        if date:
            enhanced_article['date'] = self._standardize_date(date)
        
        # 添加质量评分
        enhanced_article['quality_score'] = self._calculate_quality_score(enhanced_article)
        
        return enhanced_article
    
    def clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""
        
        # 去除HTML标签
        text = re.sub(r'<[^>]+>', ' ', text)
        # 去除多余空格
        text = re.sub(r'\s+', ' ', text)
        # 去除首尾空格
        text = text.strip()
        
        return text
    
    def _standardize_date(self, date_str: str) -> str:
        """标准化日期格式"""
        if not date_str:
            return ""
        
        # 尝试解析常见日期格式
        date_patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # DD.MM.YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                if pattern == r'(\d{4})-(\d{1,2})-(\d{1,2})':
                    year, month, day = match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                elif pattern == r'(\d{1,2})/(\d{1,2})/(\d{4})':
                    month, day, year = match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                elif pattern == r'(\d{1,2})\.(\d{1,2})\.(\d{4})':
                    day, month, year = match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return date_str
    
    def _calculate_quality_score(self, article: Dict[str, Any]) -> float:
        """计算文章质量评分"""
        score = 0.0
        
        # 标题质量 (30%)
        title = article.get('title', '')
        if len(title) >= 10:
            score += 0.3
        
        # 内容质量 (50%)
        content = article.get('content', '')
        if len(content) >= self.min_content_length:
            score += 0.5
        
        # 日期质量 (10%)
        date = article.get('date', '')
        if date and re.match(r'\d{4}-\d{2}-\d{2}', date):
            score += 0.1
        
        # URL质量 (10%)
        url = article.get('url', '')
        if url and url.startswith('http'):
            score += 0.1
        
        return round(score, 2)
    
    def enhance_data(self, data_dir: str = "data/results") -> Dict[str, Any]:
        """执行完整的数据质量增强流程"""
        print("开始数据质量增强...")
        
        # 加载原始数据
        articles = self.load_data_files(data_dir)
        
        # 执行增强步骤
        articles = self.filter_login_and_navigation_pages(articles)
        articles = self.filter_short_content(articles)
        articles = self.remove_duplicates(articles)
        articles = self.improve_content_quality(articles)
        
        # 更新统计信息
        self.stats['filtered_articles'] = len(articles)
        
        # 生成增强报告
        report = self.generate_enhancement_report()
        
        # 保存增强后的数据
        self.save_enhanced_data(articles)
        
        return {
            'enhanced_articles': articles,
            'report': report
        }
    
    def generate_enhancement_report(self) -> Dict[str, Any]:
        """生成增强报告"""
        total_removed = (self.stats['login_pages_removed'] + 
                        self.stats['navigation_pages_removed'] + 
                        self.stats['short_content_removed'] + 
                        self.stats['duplicates_removed'])
        
        improvement_rate = ((self.stats['filtered_articles'] / 
                           self.stats['total_articles']) * 100) if self.stats['total_articles'] > 0 else 0
        
        return {
            'timestamp': datetime.now().isoformat(),
            'original_count': self.stats['total_articles'],
            'enhanced_count': self.stats['filtered_articles'],
            'removed_count': total_removed,
            'improvement_rate': round(improvement_rate, 2),
            'quality_improvement': self.stats['quality_improved'],
            'details': {
                'login_pages_removed': self.stats['login_pages_removed'],
                'navigation_pages_removed': self.stats['navigation_pages_removed'],
                'short_content_removed': self.stats['short_content_removed'],
                'duplicates_removed': self.stats['duplicates_removed']
            }
        }
    
    def save_enhanced_data(self, articles: List[Dict[str, Any]]):
        """保存增强后的数据"""
        # 创建增强数据目录
        enhanced_dir = "data/enhanced"
        os.makedirs(enhanced_dir, exist_ok=True)
        
        # 保存增强后的数据
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_data_{timestamp}.json"
        filepath = os.path.join(enhanced_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        print(f"增强后的数据已保存到: {filepath}")
        
        # 保存增强报告
        report_file = f"enhancement_report_{timestamp}.json"
        report_path = os.path.join(enhanced_dir, report_file)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.generate_enhancement_report(), f, ensure_ascii=False, indent=2)
        
        print(f"增强报告已保存到: {report_path}")

def main():
    """主函数"""
    enhancer = DataQualityEnhancer(min_content_length=200)
    
    # 执行数据增强
    result = enhancer.enhance_data("data/results")
    
    # 打印增强结果
    report = result['report']
    print("\n=== 数据质量增强完成 ===")
    print(f"原始文章数量: {report['original_count']}")
    print(f"增强后文章数量: {report['enhanced_count']}")
    print(f"移除文章数量: {report['removed_count']}")
    print(f"质量提升率: {report['improvement_rate']}%")
    print(f"质量改进文章数: {report['quality_improvement']}")
    print(f"详细统计:")
    print(f"  - 登录页面移除: {report['details']['login_pages_removed']}")
    print(f"  - 导航页面移除: {report['details']['navigation_pages_removed']}")
    print(f"  - 内容过短移除: {report['details']['short_content_removed']}")
    print(f"  - 重复文章移除: {report['details']['duplicates_removed']}")

if __name__ == "__main__":
    main()