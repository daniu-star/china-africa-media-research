"""
HTML解析和内容提取优化模块
优化现有的BeautifulSoup解析逻辑，提高内容提取的准确性和效率
"""

import re
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class HTMLParsingOptimizer:
    """HTML解析优化器"""
    
    def __init__(self):
        # 优化的CSS选择器优先级
        self.optimized_selectors = {
            'content': [
                # 高优先级：语义化内容区域
                'article[class*="content"]',
                'div[class*="article-body"]',
                'section[class*="content"]',
                'main article',
                'div[class*="story-content"]',
                '.article-content',  # 添加测试HTML中的类名
                '.article-body',      # 添加测试HTML中的类名
                # 中优先级：通用内容区域
                'article',
                '.content-wrapper',
                '.entry-content',
                '.post-content',
                # 低优先级：备用选择器
                'div[class*="text"]',
                'div[class*="body"]'
            ],
            'title': [
                'h1[class*="title"]',
                'h1',
                '.article-title',
                '.news-title',
                '.entry-title',
                'title'
            ],
            'date': [
                'time[datetime]',
                'meta[property="article:published_time"]',
                'meta[name="publish_date"]',
                '.publish-date',
                '.article-date',
                '.date'
            ],
            'author': [
                '.author',
                '.byline',
                'meta[name="author"]',
                '.article-author',
                '.post-author'
            ]
        }
        
        # 文本清理和规范化规则
        self.cleaning_rules = {
            'noise_patterns': [
                r'^\s*[\d一二三四五六七八九十]+\s*[、.]\s*',  # 编号前缀
                r'\s*[\[【].*?[\]】]\s*',  # 括号内容
                r'\s*（.*?）\s*',  # 圆括号内容
                r'\s*广告\s*',  # 广告标识
                r'\s*赞助\s*',  # 赞助标识
                r'\s*推荐\s*',  # 推荐标识
            ],
            'whitespace_patterns': [
                r'\s+',  # 多个空白字符
                r'\n\s*\n',  # 多个换行
            ]
        }
    
    def extract_content_optimized(self, html_content: str, url: str = "") -> Dict[str, str]:
        """
        优化的内容提取方法
        返回包含标题、内容、日期、作者的结构化数据
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题
            title = self._extract_title_optimized(soup)
            
            # 提取内容
            content = self._extract_content_optimized(soup)
            
            # 提取日期
            date = self._extract_date_optimized(soup, url)
            
            # 提取作者
            author = self._extract_author_optimized(soup)
            
            # 内容质量评估
            quality_score = self._assess_content_quality(title, content)
            
            return {
                'title': title,
                'content': content,
                'date': date,
                'author': author,
                'quality_score': quality_score,
                'extraction_method': 'optimized_parser'
            }
            
        except Exception as e:
            logger.error(f"优化内容提取失败: {e}")
            return {
                'title': '',
                'content': '',
                'date': '',
                'author': '',
                'quality_score': 0,
                'extraction_method': 'failed'
            }
    
    def _extract_title_optimized(self, soup: BeautifulSoup) -> str:
        """优化标题提取"""
        # 按优先级尝试不同的选择器
        for selector in self.optimized_selectors['title']:
            element = soup.select_one(selector)
            if element:
                title = self._clean_text(element.get_text())
                if self._is_valid_title(title):
                    return title
        
        # 备用策略：从meta标签提取
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            title = self._clean_text(meta_title['content'])
            if self._is_valid_title(title):
                return title
        
        # 最后尝试页面标题
        page_title = soup.title
        if page_title:
            title = self._clean_text(page_title.get_text())
            if self._is_valid_title(title):
                return title
        
        return ""
    
    def _extract_content_optimized(self, soup: BeautifulSoup) -> str:
        """优化内容提取"""
        content_parts = []
        
        # 策略1: 语义化内容区域提取
        for selector in self.optimized_selectors['content']:
            elements = soup.select(selector)
            for element in elements:
                text = self._extract_text_from_element(element)
                if text and len(text.strip()) > 50:
                    content_parts.append(text)
        
        # 策略2: 段落级提取
        if not content_parts:
            paragraphs = soup.find_all('p')
            paragraph_texts = []
            for p in paragraphs:
                text = self._clean_text(p.get_text())
                if len(text.strip()) > 30:  # 降低有效段落长度要求
                    paragraph_texts.append(text)
            
            if paragraph_texts:
                # 选择最长的连续段落组
                content_parts.append(' '.join(paragraph_texts))
        
        # 策略3: 基于文本密度的提取
        if not content_parts:
            text_density_content = self._extract_by_text_density_optimized(soup)
            if text_density_content:
                content_parts.append(text_density_content)
        
        # 合并和清理内容
        if content_parts:
            combined_content = '\n\n'.join(content_parts)
            cleaned_content = self._clean_content(combined_content)
            return cleaned_content if len(cleaned_content.strip()) > 30 else ""
        
        return ""
    
    def _extract_date_optimized(self, soup: BeautifulSoup, url: str) -> str:
        """优化日期提取"""
        date_candidates = []
        
        # 策略1: meta标签（最高优先级）
        meta_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publish_date"]',
            'meta[property="og:published_time"]',
            'meta[name="date"]'
        ]
        
        for selector in meta_selectors:
            element = soup.select_one(selector)
            if element and element.get('content'):
                date = element['content'].strip()
                if self._validate_date(date):
                    date_candidates.append((date, 'meta', 10))
        
        # 策略2: time标签
        time_element = soup.find('time', {'datetime': True})
        if time_element:
            date = time_element['datetime'].strip()
            if self._validate_date(date):
                date_candidates.append((date, 'time', 9))
        
        # 策略3: 可见日期元素
        for selector in self.optimized_selectors['date']:
            element = soup.select_one(selector)
            if element:
                date = self._clean_text(element.get_text())
                if self._validate_date(date):
                    date_candidates.append((date, 'visible', 8))
        
        # 策略4: 从URL提取
        url_date = self._extract_date_from_url(url)
        if url_date:
            date_candidates.append((url_date, 'url', 6))
        
        # 选择最可靠的日期
        if date_candidates:
            date_candidates.sort(key=lambda x: x[2], reverse=True)
            return date_candidates[0][0]
        
        return ""
    
    def _extract_author_optimized(self, soup: BeautifulSoup) -> str:
        """优化作者提取"""
        author_candidates = []
        
        # 策略1: meta标签
        meta_selectors = [
            'meta[name="author"]',
            'meta[property="article:author"]',
            'meta[property="og:author"]'
        ]
        
        for selector in meta_selectors:
            element = soup.select_one(selector)
            if element and element.get('content'):
                author = element['content'].strip()
                if self._is_valid_author(author):
                    author_candidates.append((author, 'meta', 10))
        
        # 策略2: 可见作者元素
        for selector in self.optimized_selectors['author']:
            element = soup.select_one(selector)
            if element:
                author = self._clean_text(element.get_text())
                if self._is_valid_author(author):
                    author_candidates.append((author, 'visible', 8))
        
        # 选择最可靠的作者
        if author_candidates:
            author_candidates.sort(key=lambda x: x[2], reverse=True)
            return author_candidates[0][0]
        
        return ""
    
    def _extract_text_from_element(self, element) -> str:
        """从元素中提取文本，智能清理干扰内容"""
        try:
            # 创建元素的副本以避免修改原始元素
            element_copy = BeautifulSoup(str(element), 'html.parser')
            
            # 移除脚本、样式等干扰元素
            for tag in element_copy.find_all(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            
            # 提取文本并清理
            text = element_copy.get_text(separator='\n')
            cleaned_text = self._clean_content(text)
            
            return cleaned_text if len(cleaned_text.strip()) > 30 else ""
        except Exception as e:
            return ""
    
    def _extract_by_text_density_optimized(self, soup: BeautifulSoup) -> str:
        """优化的基于文本密度的内容提取"""
        elements = soup.find_all(['div', 'section', 'article'])
        
        best_element = None
        best_score = 0
        
        for element in elements:
            # 计算文本密度
            text = element.get_text(strip=True)
            html = str(element)
            
            if len(text) > 200:  # 提高最小文本长度要求
                # 文本密度
                density = len(text) / len(html) if len(html) > 0 else 0
                
                # 链接密度惩罚
                link_count = len(element.find_all('a'))
                link_density = link_count / len(text.split()) if text else 0
                
                # 段落结构奖励
                paragraphs = element.find_all('p')
                paragraph_bonus = min(len(paragraphs) * 0.1, 0.5)
                
                # 综合评分
                score = density * (1 - min(link_density, 0.3)) + paragraph_bonus
                
                if score > best_score:
                    best_score = score
                    best_element = element
        
        if best_element and best_score > 0.15:  # 提高密度阈值
            return self._extract_text_from_element(best_element)
        
        return ""
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除干扰模式
        for pattern in self.cleaning_rules['noise_patterns']:
            text = re.sub(pattern, ' ', text)
        
        return text.strip()
    
    def _clean_content(self, content: str) -> str:
        """清理内容文本"""
        if not content:
            return ""
        
        # 首先清理整个文本
        cleaned = self._clean_text(content)
        
        # 分割段落
        paragraphs = cleaned.split('\n')
        cleaned_paragraphs = []
        
        for para in paragraphs:
            para_cleaned = para.strip()
            if len(para_cleaned) > 10:  # 降低有效段落长度要求
                cleaned_paragraphs.append(para_cleaned)
        
        return '\n'.join(cleaned_paragraphs)
    
    def _is_valid_title(self, title: str) -> bool:
        """验证标题有效性"""
        if not title:
            return False
        
        # 标题长度检查
        if len(title) < 5 or len(title) > 200:
            return False
        
        # 排除常见无效标题
        invalid_patterns = [
            r'^首页$',
            r'^主页$',
            r'^网站地图$',
            r'^联系我们$',
            r'^关于我们$'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, title.strip()):
                return False
        
        return True
    
    def _is_valid_author(self, author: str) -> bool:
        """验证作者有效性"""
        if not author:
            return False
        
        # 作者名长度检查
        if len(author) < 2 or len(author) > 50:
            return False
        
        # 排除常见无效作者名
        invalid_patterns = [
            r'^作者$',
            r'^编辑$',
            r'^记者$',
            r'^通讯员$'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, author.strip()):
                return False
        
        return True
    
    def _validate_date(self, date_str: str) -> bool:
        """验证日期格式"""
        if not date_str:
            return False
        
        # 常见日期格式模式
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{4}/\d{2}/\d{2}',
            r'\d{4}\.\d{2}\.\d{2}',
            r'\d{4}年\d{1,2}月\d{1,2}日',
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO格式
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, date_str):
                return True
        
        return False
    
    def _extract_date_from_url(self, url: str) -> str:
        """从URL中提取日期"""
        if not url:
            return ""
        
        date_patterns = [
            r'/(\d{4})/(\d{2})/(\d{2})/',
            r'/(\d{4})-(\d{2})-(\d{2})/',
            r'/(\d{4})\.(\d{2})\.(\d{2})/',
            r'_(\d{4})(\d{2})(\d{2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, url)
            if match and len(match.groups()) == 3:
                return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        
        return ""
    
    def _assess_content_quality(self, title: str, content: str) -> int:
        """评估内容质量"""
        score = 100
        
        # 标题质量
        if not title:
            score -= 30
        elif len(title) < 10:
            score -= 10
        
        # 内容质量
        if not content:
            score -= 50
        else:
            content_length = len(content)
            if content_length < 100:
                score -= 40
            elif content_length < 300:
                score -= 20
            elif content_length > 1000:
                score += 10
            
            # 段落结构
            paragraphs = content.split('\n')
            valid_paragraphs = [p for p in paragraphs if len(p.strip()) > 30]
            if len(valid_paragraphs) >= 3:
                score += 15
        
        return max(0, min(100, score))


def test_optimized_parsing():
    """测试优化解析功能"""
    optimizer = HTMLParsingOptimizer()
    
    # 测试HTML内容
    test_html = """
    <html>
    <head>
        <title>测试文章 - 中非合作新篇章</title>
        <meta property="og:title" content="中非合作新篇章">
        <meta property="article:published_time" content="2023-10-15T10:30:00Z">
        <meta name="author" content="李明">
    </head>
    <body>
        <article class="article-content">
            <h1 class="article-title">中非合作进入新时代</h1>
            <div class="article-meta">
                <span class="author">作者：李明</span>
                <span class="date">2023-10-15</span>
            </div>
            <div class="article-body">
                <p>这是第一段内容，详细介绍了中非合作的最新进展。</p>
                <p>第二段内容继续深入分析合作的具体领域和成果。</p>
                <p>第三段内容展望了未来合作的发展方向。</p>
            </div>
        </article>
    </body>
    </html>
    """
    
    result = optimizer.extract_content_optimized(test_html, "https://example.com/news/2023/10/15/test-article")
    
    print("=== 优化解析测试结果 ===")
    print(f"标题: {result['title']}")
    print(f"内容长度: {len(result['content'])} 字符")
    print(f"日期: {result['date']}")
    print(f"作者: {result['author']}")
    print(f"质量评分: {result['quality_score']}")
    print(f"提取方法: {result['extraction_method']}")
    
    return result


if __name__ == "__main__":
    test_optimized_parsing()