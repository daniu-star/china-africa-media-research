#!/usr/bin/env python3
"""智能页面过滤器 - 识别和过滤登录页面、导航页面等非文章内容"""

import re
from typing import Dict, List, Tuple
import json

class SmartPageFilter:
    """智能页面过滤器"""
    
    def __init__(self):
        # 登录页面关键词模式
        self.login_patterns = [
            r'login', r'sign in', r'log in', r'password', r'username',
            r'账户', r'登录', r'密码', r'注册', r'register', r'sign up',
            r'forgot password', r'reset password', r'忘记密码',
            r'email address', r'电子邮件', r'邮箱'
        ]
        
        # 导航页面关键词模式
        self.navigation_patterns = [
            r'home', r'首页', r'main page', r'主页',
            r'navigation', r'导航', r'menu', r'菜单',
            r'header', r'footer', r'侧边栏', r'sidebar'
        ]
        
        # 非文章内容模式
        self.non_article_patterns = [
            r'404', r'not found', r'页面未找到',
            r'error', r'错误', r'无法访问',
            r'under construction', r'建设中',
            r'coming soon', r'即将推出'
        ]
        
        # 高质量文章内容特征
        self.article_features = [
            r'\b(article|news|report|story|analysis)\b',
            r'\b(作者|记者|编辑|来源)\b',
            r'\b(published|posted|updated)\b',
            r'\b(发布时间|发布日期|来源)\b',
            r'\d{4}-\d{2}-\d{2}',  # 日期格式
            r'\b(paragraph|section|chapter)\b'
        ]
    
    def analyze_page_type(self, content: str, url: str = "") -> Dict:
        """分析页面类型"""
        content_lower = content.lower()
        url_lower = url.lower()
        
        # 计算各种模式的匹配分数
        login_score = self._calculate_pattern_score(content_lower, self.login_patterns)
        navigation_score = self._calculate_pattern_score(content_lower, self.navigation_patterns)
        non_article_score = self._calculate_pattern_score(content_lower, self.non_article_patterns)
        article_score = self._calculate_pattern_score(content_lower, self.article_features)
        
        # URL分析
        url_score = self._analyze_url(url_lower)
        
        # 内容结构分析
        structure_score = self._analyze_content_structure(content)
        
        # 综合判断
        total_score = {
            'login_likelihood': login_score,
            'navigation_likelihood': navigation_score,
            'non_article_likelihood': non_article_score,
            'article_likelihood': article_score,
            'url_quality': url_score,
            'structure_quality': structure_score
        }
        
        # 确定页面类型
        page_type = self._determine_page_type(total_score)
        
        return {
            'page_type': page_type,
            'confidence': self._calculate_confidence(total_score),
            'scores': total_score,
            'recommendation': self._get_recommendation(page_type, total_score)
        }
    
    def _calculate_pattern_score(self, text: str, patterns: List[str]) -> float:
        """计算模式匹配分数"""
        score = 0.0
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 根据匹配密度计算分数
                match_density = len(matches) / max(1, len(text.split()))
                score += min(match_density * 10, 0.5)  # 密度越高分数越高
        return min(score, 1.0)  # 最大1.0分
    
    def _analyze_url(self, url: str) -> float:
        """分析URL质量"""
        if not url:
            return 0.5
        
        score = 0.5  # 基础分
        
        # 检查URL中是否包含文章相关关键词
        article_keywords = ['article', 'news', 'story', 'report', 'blog']
        for keyword in article_keywords:
            if keyword in url:
                score += 0.2
        
        # 检查URL中是否包含日期格式
        if re.search(r'\d{4}/\d{2}/\d{2}', url) or re.search(r'\d{4}-\d{2}-\d{2}', url):
            score += 0.3
        
        return min(score, 1.0)
    
    def _analyze_content_structure(self, content: str) -> float:
        """分析内容结构质量"""
        if len(content.strip()) < 50:
            return 0.0
        
        score = 0.0
        
        # 段落数量
        paragraphs = content.split('\n\n')
        if len(paragraphs) >= 3:
            score += 0.3
        
        # 句子数量
        sentences = re.split(r'[.!?]+', content)
        if len(sentences) >= 5:
            score += 0.3
        
        # 标题存在性
        if re.search(r'^#+\s+.+', content, re.MULTILINE):
            score += 0.2
        
        # 链接数量（适度）
        links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        if 1 <= len(links) <= 10:
            score += 0.2
        
        return min(score, 1.0)
    
    def _determine_page_type(self, scores: Dict) -> str:
        """确定页面类型"""
        login_score = scores['login_likelihood']
        navigation_score = scores['navigation_likelihood']
        non_article_score = scores['non_article_likelihood']
        article_score = scores['article_likelihood']
        structure_score = scores['structure_quality']
        
        # 优先处理明确的非文章页面
        if login_score > 0.3:
            return 'login_page'
        elif navigation_score > 0.4:
            return 'navigation_page'
        elif non_article_score > 0.4:
            return 'non_article_page'
        
        # 文章页面判断
        if article_score > 0.3 and structure_score > 0.4:
            return 'article_page'
        elif article_score > 0.2:
            return 'likely_article_page'
        
        # 基于URL质量判断
        if scores['url_quality'] > 0.6:
            return 'likely_article_page'
        
        return 'unknown_page'
    
    def _calculate_confidence(self, scores: Dict) -> float:
        """计算判断置信度"""
        # 基于各分数之间的差异计算置信度
        max_score = max(scores.values())
        min_score = min(scores.values())
        
        if max_score - min_score > 0.3:
            return 0.8  # 高置信度
        elif max_score - min_score > 0.1:
            return 0.6  # 中等置信度
        else:
            return 0.4  # 低置信度
    
    def _get_recommendation(self, page_type: str, scores: Dict) -> str:
        """获取处理建议"""
        recommendations = {
            'login_page': '建议过滤：检测到登录页面特征',
            'navigation_page': '建议过滤：检测到导航页面特征',
            'non_article_page': '建议过滤：检测到非文章页面特征',
            'article_page': '建议保留：高质量文章内容',
            'likely_article_page': '建议保留：可能为文章内容',
            'unknown_page': '建议人工审核：无法确定页面类型'
        }
        return recommendations.get(page_type, '未知页面类型')
    
    def should_filter_page(self, content: str, url: str = "") -> Tuple[bool, str]:
        """判断是否应该过滤页面"""
        analysis = self.analyze_page_type(content, url)
        
        filter_types = ['login_page', 'navigation_page', 'non_article_page']
        
        if analysis['page_type'] in filter_types:
            return True, f"过滤原因：{analysis['page_type']} - {analysis['recommendation']}"
        
        return False, "页面类型正常，建议保留"
    
    def filter_content(self, article: Dict) -> Dict:
        """过滤文章内容 - 兼容性方法"""
        content = article.get('content', '')
        url = article.get('url', '')
        
        # 使用现有的should_filter_page方法进行判断
        should_filter, reason = self.should_filter_page(content, url)
        
        # 返回兼容的格式
        return {
            'is_valid': not should_filter,
            'reasons': [reason] if should_filter else [],
            'analysis': self.analyze_page_type(content, url)
        }

def filter_articles_batch(articles: List[Dict]) -> Dict:
    """批量过滤文章"""
    filter = SmartPageFilter()
    
    filtered_articles = []
    filtered_out = []
    
    for article in articles:
        content = article.get('content', '')
        url = article.get('url', '')
        
        should_filter, reason = filter.should_filter_page(content, url)
        
        if should_filter:
            filtered_out.append({
                'original_article': article,
                'filter_reason': reason,
                'analysis': filter.analyze_page_type(content, url)
            })
        else:
            filtered_articles.append(article)
    
    return {
        'filtered_articles': filtered_articles,
        'filtered_out_count': len(filtered_out),
        'filtered_out_details': filtered_out,
        'original_count': len(articles),
        'filtered_count': len(filtered_articles),
        'filter_rate': len(filtered_out) / len(articles) if articles else 0
    }

def test_smart_filter():
    """测试智能过滤器"""
    filter = SmartPageFilter()
    
    # 测试用例
    test_cases = [
        {
            'content': 'Please login to access this content. Username: Password:',
            'url': 'https://example.com/login',
            'expected_type': 'login_page'
        },
        {
            'content': 'Home About Contact Services',
            'url': 'https://example.com/navigation',
            'expected_type': 'navigation_page'
        },
        {
            'content': 'This is a news article about China-Africa investment. Published on 2023-10-15.',
            'url': 'https://news.com/article/123',
            'expected_type': 'article_page'
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        result = filter.analyze_page_type(test_case['content'], test_case['url'])
        print(f"测试用例 {i+1}:")
        print(f"  页面类型: {result['page_type']}")
        print(f"  置信度: {result['confidence']:.2f}")
        print(f"  建议: {result['recommendation']}")
        print()

if __name__ == "__main__":
    test_smart_filter()