"""
登录页面过滤器 - 专门处理登录页面和导航页面问题
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any

class LoginPageFilter:
    """登录页面过滤器"""
    
    def __init__(self):
        # 登录页面关键词模式
        self.login_patterns = [
            r'login', r'sign in', r'signin', r'log in', r'logon',
            r'username', r'password', r'email', r'account',
            r'forgot password', r'remember me', r'stay signed in',
            r'authentication', r'authorization', r'credentials',
            r'access denied', r'please log in', r'enter your',
            r'welcome back', r'returning user', r'member login'
        ]
        
        # 导航页面关键词模式
        self.navigation_patterns = [
            r'home', r'about', r'contact', r'services', r'products',
            r'portfolio', r'blog', r'news', r'careers', r'career',
            r'team', r'company', r'organization', r'institution',
            r'department', r'faculty', r'staff', r'students',
            r'alumni', r'partners', r'sponsors', r'donors',
            r'events', r'calendar', r'schedule', r'programs',
            r'courses', r'research', r'publications', r'resources',
            r'library', r'archives', r'museum', r'gallery',
            r'admissions', r'apply', r'enrollment', r'tuition',
            r'financial aid', r'scholarships', r'campus', r'facilities',
            r'location', r'directions', r'map', r'hours', r'visit'
        ]
        
        # 文章内容关键词模式
        self.article_patterns = [
            r'according to', r'reported that', r'said that', r'announced that',
            r'study shows', r'research indicates', r'findings suggest',
            r'in a statement', r'in an interview', r'during the meeting',
            r'according to sources', r'officials said', r'experts believe',
            r'the results show', r'data reveals', r'analysis suggests',
            r'in recent years', r'over the past', r'during the period',
            r'according to the report', r'based on data', r'statistics show'
        ]
        
        # 编译正则表达式
        self.login_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.login_patterns]
        self.nav_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.navigation_patterns]
        self.article_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.article_patterns]
    
    def analyze_page(self, content: str, url: str = "") -> Dict[str, Any]:
        """分析页面类型"""
        
        # 计算登录页面特征分数
        login_score = self._calculate_pattern_score(content, self.login_regex)
        
        # 计算导航页面特征分数
        nav_score = self._calculate_pattern_score(content, self.nav_regex)
        
        # 计算文章内容特征分数
        article_score = self._calculate_pattern_score(content, self.article_regex)
        
        # URL分析
        url_score = self._analyze_url(url)
        
        # 综合判断页面类型
        page_type, confidence = self._determine_page_type(login_score, nav_score, article_score, url_score)
        
        return {
            'page_type': page_type,
            'confidence': confidence,
            'scores': {
                'login_score': login_score,
                'nav_score': nav_score,
                'article_score': article_score,
                'url_score': url_score
            },
            'suggestion': self._get_suggestion(page_type)
        }
    
    def _calculate_pattern_score(self, text: str, patterns: List[re.Pattern]) -> float:
        """计算模式匹配分数"""
        if not text:
            return 0.0
        
        # 计算匹配密度（匹配数/文本词数）
        words = text.split()
        if not words:
            return 0.0
        
        match_count = 0
        for pattern in patterns:
            matches = pattern.findall(text)
            match_count += len(matches)
        
        # 基于匹配密度计算分数，密度越高分数越高
        density = match_count / len(words)
        score = min(density * 10, 1.0)  # 限制最大分数为1.0
        
        return round(score, 2)
    
    def _analyze_url(self, url: str) -> float:
        """分析URL特征"""
        if not url:
            return 0.0
        
        # URL中的登录相关关键词
        login_url_patterns = [
            r'/login', r'/signin', r'/sign-in', r'/auth', r'/account',
            r'/register', r'/signup', r'/password', r'/forgot', r'/reset'
        ]
        
        # URL中的导航相关关键词
        nav_url_patterns = [
            r'/about', r'/contact', r'/services', r'/team', r'/careers',
            r'/events', r'/programs', r'/courses', r'/admissions', r'/visit'
        ]
        
        # URL中的文章相关关键词
        article_url_patterns = [
            r'/article', r'/news', r'/blog', r'/story', r'/report',
            r'/analysis', r'/feature', r'/opinion', r'/editorial', r'/coverage'
        ]
        
        url_lower = url.lower()
        
        # 检查登录URL模式
        for pattern in login_url_patterns:
            if re.search(pattern, url_lower):
                return 0.9  # 高置信度登录页面
        
        # 检查导航URL模式
        for pattern in nav_url_patterns:
            if re.search(pattern, url_lower):
                return 0.7  # 中等置信度导航页面
        
        # 检查文章URL模式
        for pattern in article_url_patterns:
            if re.search(pattern, url_lower):
                return 0.8  # 高置信度文章页面
        
        return 0.5  # 中性分数
    
    def _determine_page_type(self, login_score: float, nav_score: float, article_score: float, url_score: float) -> tuple:
        """确定页面类型"""
        
        # 基于URL分数调整判断
        if url_score > 0.8:
            if any(pattern in ['login', 'signin', 'auth', 'account'] for pattern in self.login_patterns):
                return 'login_page', 0.9
            elif url_score > 0.7:
                return 'navigation_page', 0.8
            elif url_score > 0.6:
                return 'likely_article_page', 0.7
        
        # 基于内容分数判断
        if login_score > 0.3:  # 降低阈值
            return 'login_page', min(login_score + 0.3, 0.9)
        
        if nav_score > 0.4:  # 降低阈值
            return 'navigation_page', min(nav_score + 0.2, 0.8)
        
        if article_score > 0.3:  # 降低阈值
            return 'likely_article_page', min(article_score + 0.2, 0.8)
        
        # 如果URL质量较高，倾向于文章页面
        if url_score > 0.6:
            return 'likely_article_page', 0.6
        
        return 'unknown_page', 0.5
    
    def _get_suggestion(self, page_type: str) -> str:
        """获取处理建议"""
        suggestions = {
            'login_page': '建议过滤：检测到登录页面特征',
            'navigation_page': '建议过滤：检测到导航页面特征',
            'likely_article_page': '建议保留：可能为文章内容',
            'unknown_page': '建议人工审核：无法确定页面类型'
        }
        return suggestions.get(page_type, '建议进一步分析')
    
    def filter_articles(self, articles: List[Dict[str, Any]], min_confidence: float = 0.6) -> Dict[str, Any]:
        """过滤文章列表"""
        filtered_articles = []
        removed_articles = []
        
        stats = {
            'total': len(articles),
            'kept': 0,
            'removed': 0,
            'login_pages': 0,
            'navigation_pages': 0,
            'unknown_pages': 0
        }
        
        for article in articles:
            content = article.get('content', '')
            url = article.get('url', '')
            
            analysis = self.analyze_page(content, url)
            
            if analysis['page_type'] in ['login_page', 'navigation_page']:
                if analysis['confidence'] >= min_confidence:
                    stats['removed'] += 1
                    if analysis['page_type'] == 'login_page':
                        stats['login_pages'] += 1
                    else:
                        stats['navigation_pages'] += 1
                    
                    removed_articles.append({
                        'original_article': article,
                        'analysis': analysis,
                        'reason': f"检测到{analysis['page_type']}"
                    })
                    continue
            
            # 保留文章
            filtered_articles.append(article)
            stats['kept'] += 1
        
        return {
            'filtered_articles': filtered_articles,
            'removed_articles': removed_articles,
            'stats': stats,
            'filter_summary': {
                'improvement_rate': round((stats['kept'] / stats['total']) * 100, 2) if stats['total'] > 0 else 0,
                'quality_improvement': f"移除{stats['removed']}篇低质量文章"
            }
        }

def test_filter():
    """测试过滤器"""
    filter = LoginPageFilter()
    
    # 测试用例
    test_cases = [
        {
            'content': 'Please login to access this content. Enter your username and password.',
            'url': 'https://example.com/login'
        },
        {
            'content': 'About our company, contact information, and team members.',
            'url': 'https://example.com/about'
        },
        {
            'content': 'According to recent reports, the economic situation has improved significantly.',
            'url': 'https://example.com/news/2024/economic-report'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        result = filter.analyze_page(test_case['content'], test_case['url'])
        print(f"测试用例 {i}:")
        print(f"  页面类型: {result['page_type']}")
        print(f"  置信度: {result['confidence']}")
        print(f"  建议: {result['suggestion']}")
        print()

if __name__ == "__main__":
    test_filter()