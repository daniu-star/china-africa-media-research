#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级中非投资数据爬虫
使用更有效的网络请求和解析方法
"""

import json
import time
import requests
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AdvancedInvestmentCrawler:
    """高级中非投资数据爬虫"""
    
    def __init__(self):
        """初始化爬虫"""
        self.session = self.create_session()
        self.collected_data = []
        
        # 可靠的数据源配置
        self.data_sources = [
            {
                'name': '新华网国际',
                'url': 'http://www.news.cn/english/',
                'search_url': 'http://www.news.cn/english/search.htm',
                'search_params': {'q': 'China Africa investment'},
                'type': 'news',
                'reliability': 'high'
            },
            {
                'name': '人民网英文版',
                'url': 'http://en.people.cn/',
                'search_url': 'http://en.people.cn/search/',
                'search_params': {'q': 'China Africa'},
                'type': 'news',
                'reliability': 'high'
            },
            {
                'name': '中国日报',
                'url': 'https://www.chinadaily.com.cn',
                'search_url': 'https://www.chinadaily.com.cn/search',
                'search_params': {'query': 'China Africa investment'},
                'type': 'media',
                'reliability': 'medium'
            }
        ]
        
        # 投资相关关键词
        self.investment_keywords = [
            '投资', 'investment', '合作', 'cooperation', '项目', 'project',
            '经济', 'economic', '贸易', 'trade', '发展', 'development',
            '中非', 'China-Africa', '一带一路', 'Belt and Road',
            'FOCAC', '中非合作论坛', 'infrastructure', '基础设施'
        ]
    
    def create_session(self) -> requests.Session:
        """创建HTTP会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/'
        })
        return session
    
    def safe_request(self, url: str, params: Dict = None, max_retries: int = 3) -> Optional[str]:
        """安全的HTTP请求"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    return response.text
                else:
                    logger.warning(f"请求失败: {url}, 状态码: {response.status_code}")
            except Exception as e:
                logger.warning(f"请求异常 (尝试 {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
        
        return None
    
    def parse_html_with_bs4(self, html_content: str, source_name: str) -> List[Dict]:
        """使用BeautifulSoup解析HTML内容"""
        articles = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 根据不同的网站结构进行解析
            if 'xinhua' in source_name.lower():
                articles = self.parse_xinhua(soup)
            elif 'people' in source_name.lower():
                articles = self.parse_people(soup)
            elif 'chinadaily' in source_name.lower():
                articles = self.parse_chinadaily(soup)
            else:
                # 通用解析方法
                articles = self.parse_generic(soup)
                
        except Exception as e:
            logger.error(f"解析 {source_name} 内容失败: {e}")
        
        return articles
    
    def parse_xinhua(self, soup: BeautifulSoup) -> List[Dict]:
        """解析新华网内容"""
        articles = []
        
        # 尝试多种选择器
        selectors = [
            'a[href*="china-africa"]',
            'a[href*="investment"]',
            '.news-item a',
            '.article-list a',
            'h3 a',
            'h2 a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links[:10]:  # 限制数量
                title = link.get_text(strip=True)
                href = link.get('href', '')
                
                if self.is_investment_related(title) and len(title) > 10:
                    full_url = urljoin('http://www.news.cn', href)
                    article = {
                        'title': title,
                        'url': full_url,
                        'source': '新华网',
                        'extraction_date': datetime.now().isoformat(),
                        'relevance_score': self.calculate_relevance_score(title),
                        'content_type': 'news'
                    }
                    articles.append(article)
        
        return articles[:5]  # 返回前5条
    
    def parse_people(self, soup: BeautifulSoup) -> List[Dict]:
        """解析人民网内容"""
        articles = []
        
        # 人民网的选择器
        selectors = [
            '.p1_title a',
            '.ej_list_box a',
            '.news_list a',
            'h2 a',
            'h3 a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links[:10]:
                title = link.get_text(strip=True)
                href = link.get('href', '')
                
                if self.is_investment_related(title) and len(title) > 10:
                    full_url = urljoin('http://en.people.cn', href)
                    article = {
                        'title': title,
                        'url': full_url,
                        'source': '人民网',
                        'extraction_date': datetime.now().isoformat(),
                        'relevance_score': self.calculate_relevance_score(title),
                        'content_type': 'news'
                    }
                    articles.append(article)
        
        return articles[:5]
    
    def parse_chinadaily(self, soup: BeautifulSoup) -> List[Dict]:
        """解析中国日报内容"""
        articles = []
        
        # 中国日报的选择器
        selectors = [
            '.mb10 a',
            '.topNews a',
            '.news_list a',
            'h3 a',
            'h4 a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links[:10]:
                title = link.get_text(strip=True)
                href = link.get('href', '')
                
                if self.is_investment_related(title) and len(title) > 10:
                    full_url = urljoin('https://www.chinadaily.com.cn', href)
                    article = {
                        'title': title,
                        'url': full_url,
                        'source': '中国日报',
                        'extraction_date': datetime.now().isoformat(),
                        'relevance_score': self.calculate_relevance_score(title),
                        'content_type': 'media'
                    }
                    articles.append(article)
        
        return articles[:5]
    
    def parse_generic(self, soup: BeautifulSoup) -> List[Dict]:
        """通用解析方法"""
        articles = []
        
        # 查找所有链接
        links = soup.find_all('a', href=True)
        
        for link in links[:20]:  # 限制数量
            title = link.get_text(strip=True)
            href = link.get('href', '')
            
            # 过滤条件
            if (self.is_investment_related(title) and 
                len(title) > 10 and 
                not href.startswith('#') and
                not href.startswith('javascript:')):
                
                article = {
                    'title': title,
                    'url': href if href.startswith('http') else f'https://{href}',
                    'source': '通用网站',
                    'extraction_date': datetime.now().isoformat(),
                    'relevance_score': self.calculate_relevance_score(title),
                    'content_type': 'unknown'
                }
                articles.append(article)
        
        return articles[:5]
    
    def is_investment_related(self, text: str) -> bool:
        """判断文本是否与投资相关"""
        if not text or len(text) < 5:
            return False
            
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.investment_keywords)
    
    def calculate_relevance_score(self, text: str) -> int:
        """计算相关性分数"""
        score = 0
        text_lower = text.lower()
        
        # 关键词权重
        keyword_weights = {
            '中非': 3, 'China-Africa': 3,
            '投资': 2, 'investment': 2,
            '合作': 2, 'cooperation': 2,
            '一带一路': 3, 'Belt and Road': 3,
            'FOCAC': 3, '中非合作论坛': 3,
            '基础设施': 2, 'infrastructure': 2
        }
        
        for keyword, weight in keyword_weights.items():
            if keyword.lower() in text_lower:
                score += weight
        
        return min(score, 10)  # 最大10分
    
    def crawl_with_search(self, source: Dict) -> List[Dict]:
        """使用搜索功能爬取数据"""
        articles = []
        
        try:
            # 尝试搜索功能
            if 'search_url' in source:
                logger.info(f"使用搜索功能爬取: {source['name']}")
                
                html_content = self.safe_request(
                    source['search_url'], 
                    source.get('search_params', {})
                )
                
                if html_content:
                    articles = self.parse_html_with_bs4(html_content, source['name'])
                
                if articles:
                    return articles
            
            # 如果搜索失败，尝试直接访问主页
            logger.info(f"直接访问主页: {source['name']}")
            html_content = self.safe_request(source['url'])
            
            if html_content:
                articles = self.parse_html_with_bs4(html_content, source['name'])
                
        except Exception as e:
            logger.error(f"爬取 {source['name']} 失败: {e}")
        
        return articles
    
    def generate_high_quality_sample_data(self) -> List[Dict]:
        """生成高质量样本数据"""
        sample_articles = [
            {
                'title': '中非合作论坛第八届部长级会议推动投资合作新机遇',
                'url': 'https://www.focac.org/sample1',
                'source': '中非合作论坛官网',
                'extraction_date': datetime.now().isoformat(),
                'relevance_score': 10,
                'content_type': 'official',
                'summary': '第八届中非合作论坛部长级会议为双边投资合作提供了新的政策支持和市场机遇。',
                'keywords': ['中非合作论坛', '投资合作', '政策支持']
            },
            {
                'title': '中国对非洲基础设施投资2024年同比增长15%',
                'url': 'https://www.xinhuanet.com/investment2024',
                'source': '新华网',
                'extraction_date': datetime.now().isoformat(),
                'relevance_score': 9,
                'content_type': 'news',
                'summary': '2024年中国企业在非洲基础设施建设领域的投资实现显著增长，涉及交通、能源等多个领域。',
                'keywords': ['基础设施', '投资增长', '中国企业']
            },
            {
                'title': '一带一路倡议下中非经贸合作深度分析',
                'url': 'https://africa.cgtn.com/belt-road-analysis',
                'source': 'CGTN非洲',
                'extraction_date': datetime.now().isoformat(),
                'relevance_score': 9,
                'content_type': 'media',
                'summary': '一带一路倡议为中非经贸合作提供了新的发展动力，涵盖贸易、投资、基础设施等多个维度。',
                'keywords': ['一带一路', '经贸合作', '深度分析']
            },
            {
                'title': '中非产能合作重点项目进展报告',
                'url': 'https://www.yidaiyilu.gov.cn/capacity-cooperation',
                'source': '中国一带一路网',
                'extraction_date': datetime.now().isoformat(),
                'relevance_score': 8,
                'content_type': 'official',
                'summary': '中非产能合作重点项目在多个非洲国家取得实质性进展，推动当地工业化进程。',
                'keywords': ['产能合作', '重点项目', '工业化']
            },
            {
                'title': '中国金融机构加大对非洲投资支持力度',
                'url': 'https://en.people.cn/finance-africa',
                'source': '人民网',
                'extraction_date': datetime.now().isoformat(),
                'relevance_score': 8,
                'content_type': 'news',
                'summary': '中国主要金融机构加大对非洲投资项目的金融支持，为双边经贸合作提供资金保障。',
                'keywords': ['金融机构', '投资支持', '资金保障']
            }
        ]
        
        return sample_articles
    
    def save_data(self, data: List[Dict], filename: str):
        """保存数据到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已保存到 {filename}, 共 {len(data)} 条记录")
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
    
    def run(self) -> Dict:
        """运行爬虫"""
        logger.info("开始运行高级中非投资数据爬虫")
        
        all_articles = []
        successful_sources = []
        
        # 爬取每个数据源
        for source in self.data_sources:
            logger.info(f"开始处理: {source['name']}")
            
            try:
                articles = self.crawl_with_search(source)
                
                if articles:
                    all_articles.extend(articles)
                    successful_sources.append(source['name'])
                    logger.info(f"从 {source['name']} 获取到 {len(articles)} 篇文章")
                else:
                    logger.warning(f"从 {source['name']} 未获取到文章")
                
                # 请求间隔
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"处理 {source['name']} 时发生错误: {e}")
        
        # 结果处理
        if len(all_articles) >= 3:
            logger.info(f"成功获取 {len(all_articles)} 篇真实文章")
            self.save_data(all_articles, 'advanced_real_investment_data.json')
            
            result = {
                'status': 'success',
                'total_articles': len(all_articles),
                'sources': successful_sources,
                'data_type': 'real',
                'articles': all_articles
            }
        else:
            logger.warning(f"真实数据不足 ({len(all_articles)} 篇), 使用高质量样本数据")
            sample_articles = self.generate_high_quality_sample_data()
            self.save_data(sample_articles, 'advanced_sample_investment_data.json')
            
            result = {
                'status': 'sample_data_used',
                'total_articles': len(sample_articles),
                'sources': ['高质量样本数据'],
                'data_type': 'sample',
                'articles': sample_articles
            }
        
        return result

def main():
    """主函数"""
    crawler = AdvancedInvestmentCrawler()
    
    try:
        result = crawler.run()
        
        # 输出统计信息
        print(f"\n=== 爬虫执行结果 ===")
        print(f"状态: {result['status']}")
        print(f"数据来源: {', '.join(result['sources'])}")
        print(f"文章总数: {result['total_articles']}")
        print(f"数据类型: {result['data_type']}")
        
        # 显示文章列表
        print(f"\n=== 获取的文章 ===")
        for i, article in enumerate(result['articles'], 1):
            print(f"{i}. {article['title']} (相关性: {article['relevance_score']}/10)")
            print(f"   来源: {article['source']}")
            if 'summary' in article:
                print(f"   摘要: {article['summary']}")
            print()
        
        print(f"详细数据已保存到文件")
        
    except KeyboardInterrupt:
        print("\n用户中断爬虫执行")
    except Exception as e:
        print(f"爬虫执行异常: {e}")

if __name__ == "__main__":
    main()