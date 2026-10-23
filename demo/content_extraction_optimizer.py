from datetime import datetime
import re
import html
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ContentExtractionOptimizer:
    """内容提取优化器 - 专门用于从HTML和文本中提取新闻内容"""
    
    def __init__(self):
        self.date_parser = DateParser()
    
    def extract_news_content_advanced(self, html_content: str) -> str:
        """智能新闻内容提取 - 增强版（支持多语言和复杂结构）"""
        # 移除脚本和样式标签
        cleaned_html = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        cleaned_html = re.sub(r'<style[^>]*>.*?</style>', '', cleaned_html, flags=re.DOTALL)
        cleaned_html = re.sub(r'<!--.*?-->', '', cleaned_html, flags=re.DOTALL)
        
        # 提取所有段落、标题和列表项
        paragraphs = []
        
        # 查找段落标签
        p_matches = re.findall(r'<p[^>]*>(.*?)</p>', cleaned_html, flags=re.DOTALL)
        paragraphs.extend(p_matches)
        
        # 查找标题标签
        h_matches = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', cleaned_html, flags=re.DOTALL)
        paragraphs.extend(h_matches)
        
        # 查找列表项
        li_matches = re.findall(r'<li[^>]*>(.*?)</li>', cleaned_html, flags=re.DOTALL)
        paragraphs.extend(li_matches)
        
        # 增强版div内容提取 - 针对非洲新闻网站优化
        div_patterns = [
            # 通用内容div模式
            r'<div[^>]*class="[^"]*(?:article|content|main|post|story|news|entry)[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*id="[^"]*(?:article|content|main|post|story|news|entry)[^"]*"[^>]*>(.*?)</div>',
            # 非洲新闻网站特定div模式
            r'<div[^>]*class="[^"]*(?:ahram|allafrica|news24|nation|premiumtimes|guardian)[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*(?:punch|vanguard|tribune|thisday|sun|dailytrust)[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*(?:leadership|businessday|independent|jeuneafrique|lemonde)[^"]*"[^>]*>(.*?)</div>',
            # 法语非洲新闻网站模式
            r'<div[^>]*class="[^"]*(?:article|contenu|principal|post|histoire|nouvelle|entrée)[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*(?:rfi|lemonde|jeuneafrique|afrique|africatime)[^"]*"[^>]*>(.*?)</div>',
            # 阿拉伯语非洲新闻网站模式
            r'<div[^>]*class="[^"]*(?:مقال|محتوى|رئيسي|خبر|قصة|مدونة)[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*(?:الأهرام|اليوم|الوطن|الشرق|الجزيرة)[^"]*"[^>]*>(.*?)</div>'
        ]
        
        for pattern in div_patterns:
            div_matches = re.findall(pattern, cleaned_html, flags=re.DOTALL | re.IGNORECASE)
            for div_content in div_matches:
                # 从div中提取文本内容
                div_text = re.sub(r'<[^>]+>', ' ', div_content)
                div_text = re.sub(r'\s+', ' ', div_text).strip()
                if len(div_text) >= 50:  # 只保留有实质内容的div
                    paragraphs.append(div_text)
        
        # 多语言内容提取增强
        multilingual_paragraphs = self._extract_multilingual_paragraphs(cleaned_html)
        paragraphs.extend(multilingual_paragraphs)
        
        # 复杂结构内容提取
        complex_paragraphs = self._extract_complex_structure_paragraphs(cleaned_html)
        paragraphs.extend(complex_paragraphs)
        
        # 清理和过滤段落
        filtered_paragraphs = []
        for para in paragraphs:
            # 移除HTML标签
            clean_text = re.sub(r'<[^>]+>', '', para)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            # 过滤短文本和导航文本
            if len(clean_text) >= 20 and not self._contains_navigation_keywords(clean_text):
                # 特别针对非洲新闻内容的质量检测
                if self._is_african_news_content(clean_text):
                    filtered_paragraphs.append(clean_text)
        
        # 智能段落排序和选择
        if filtered_paragraphs:
            # 按段落长度和质量评分排序
            scored_paragraphs = []
            for para in filtered_paragraphs:
                score = self._score_paragraph_quality_enhanced(para)
                scored_paragraphs.append((para, score))
            
            # 按质量评分排序
            scored_paragraphs.sort(key=lambda x: x[1], reverse=True)
            
            # 选择高质量的段落（前10个或所有高质量段落）
            high_quality_paragraphs = []
            for para, score in scored_paragraphs:
                if score >= 0.6:  # 质量阈值
                    high_quality_paragraphs.append(para)
                if len(high_quality_paragraphs) >= 10:  # 最多10个段落
                    break
            
            return high_quality_paragraphs
        
        return []
    
    def _extract_multilingual_paragraphs(self, html_content: str) -> List[str]:
        """提取多语言段落内容"""
        paragraphs = []
        
        # 法语内容提取模式
        french_patterns = [
            r'<div[^>]*class="[^"]*(?:article|contenu|principal|post|histoire|nouvelle|entrée|actualité)[^"]*"[^>]*>(.*?)</div>',
            r'<p[^>]*class="[^"]*(?:article|contenu|principal|post|histoire|nouvelle|entrée|actualité)[^"]*"[^>]*>(.*?)</p>',
            r'<section[^>]*class="[^"]*(?:article|contenu|principal|post|histoire|nouvelle|entrée|actualité)[^"]*"[^>]*>(.*?)</section>'
        ]
        
        # 阿拉伯语内容提取模式
        arabic_patterns = [
            r'<div[^>]*class="[^"]*(?:مقال|محتوى|رئيسي|خبر|قصة|مدونة|أخبار)[^"]*"[^>]*>(.*?)</div>',
            r'<p[^>]*class="[^"]*(?:مقال|محتوى|رئيسي|خبر|قصة|مدونة|أخبار)[^"]*"[^>]*>(.*?)</p>',
            r'<section[^>]*class="[^"]*(?:مقال|محتوى|رئيسي|خبر|قصة|مدونة|أخبار)[^"]*"[^>]*>(.*?)</section>'
        ]
        
        # 非洲本地语言内容提取模式
        african_language_patterns = [
            r'<div[^>]*class="[^"]*(?:habari|matukio|ripoti|makala|taarifa|uchambuzi)[^"]*"[^>]*>(.*?)</div>',
            r'<p[^>]*class="[^"]*(?:habari|matukio|ripoti|makala|taarifa|uchambuzi)[^"]*"[^>]*>(.*?)</p>',
            r'<section[^>]*class="[^"]*(?:habari|matukio|ripoti|makala|taarifa|uchambuzi)[^"]*"[^>]*>(.*?)</section>'
        ]
        
        # 提取法语内容
        for pattern in french_patterns:
            matches = re.findall(pattern, html_content, flags=re.DOTALL | re.IGNORECASE)
            for match in matches:
                text = re.sub(r'<[^>]+>', ' ', match)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) >= 30 and self._contains_french_keywords(text):
                    paragraphs.append(text)
        
        # 提取阿拉伯语内容
        for pattern in arabic_patterns:
            matches = re.findall(pattern, html_content, flags=re.DOTALL | re.IGNORECASE)
            for match in matches:
                text = re.sub(r'<[^>]+>', ' ', match)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) >= 30 and self._contains_arabic_keywords(text):
                    paragraphs.append(text)
        
        # 提取非洲本地语言内容
        for pattern in african_language_patterns:
            matches = re.findall(pattern, html_content, flags=re.DOTALL | re.IGNORECASE)
            for match in matches:
                text = re.sub(r'<[^>]+>', ' ', match)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) >= 30 and self._contains_african_language_keywords(text):
                    paragraphs.append(text)
        
        return paragraphs
    
    def _extract_complex_structure_paragraphs(self, html_content: str) -> List[str]:
        """提取复杂结构段落内容"""
        paragraphs = []
        
        # 表格内容提取
        table_patterns = [
            r'<table[^>]*>(.*?)</table>',
            r'<div[^>]*class="[^"]*(?:table|grid|data|stats)[^"]*"[^>]*>(.*?)</div>'
        ]
        
        for pattern in table_patterns:
            matches = re.findall(pattern, html_content, flags=re.DOTALL | re.IGNORECASE)
            for match in matches:
                # 提取表格中的文本内容
                table_text = re.sub(r'<[^>]+>', ' | ', match)
                table_text = re.sub(r'\s+', ' ', table_text).strip()
                if len(table_text) >= 50:
                    paragraphs.append(f"表格内容: {table_text}")
        
        # 列表内容提取
        list_patterns = [
            r'<ul[^>]*>(.*?)</ul>',
            r'<ol[^>]*>(.*?)</ol>',
            r'<div[^>]*class="[^"]*(?:list|items|points)[^"]*"[^>]*>(.*?)</div>'
        ]
        
        for pattern in list_patterns:
            matches = re.findall(pattern, html_content, flags=re.DOTALL | re.IGNORECASE)
            for match in matches:
                # 提取列表项
                list_items = re.findall(r'<li[^>]*>(.*?)</li>', match, flags=re.DOTALL)
                if list_items:
                    list_text = ' | '.join([re.sub(r'<[^>]+>', '', item).strip() for item in list_items])
                    if len(list_text) >= 30:
                        paragraphs.append(f"列表内容: {list_text}")
        
        # 层级结构内容提取
        hierarchical_patterns = [
            r'<div[^>]*class="[^"]*(?:hierarchy|nested|tree|structure)[^"]*"[^>]*>(.*?)</div>',
            r'<section[^>]*class="[^"]*(?:hierarchy|nested|tree|structure)[^"]*"[^>]*>(.*?)</section>'
        ]
        
        for pattern in hierarchical_patterns:
            matches = re.findall(pattern, html_content, flags=re.DOTALL | re.IGNORECASE)
            for match in matches:
                # 提取层级结构中的文本
                hierarchical_text = re.sub(r'<[^>]+>', ' > ', match)
                hierarchical_text = re.sub(r'\s+', ' ', hierarchical_text).strip()
                if len(hierarchical_text) >= 40:
                    paragraphs.append(f"层级内容: {hierarchical_text}")
        
        return paragraphs
    
    def _score_paragraph_quality_enhanced(self, paragraph: str) -> float:
        """增强版段落质量评分（支持多语言和复杂结构）"""
        score = 0.0
        
        # 基础长度评分（15-300字符为最佳）- 降低要求
        length = len(paragraph)
        if 15 <= length <= 300:  # 降低最佳范围
            score += 0.3
        elif length > 300:
            score += 0.25
        elif length >= 10:  # 增加更短内容的分数
            score += 0.2
        
        # 多语言句子结构评分 - 更宽松
        sentences = re.split(r'[.!?。！؟؟]+', paragraph)
        valid_sentences = [s.strip() for s in sentences if len(s.strip()) >= 8]  # 降低句子长度要求
        if len(valid_sentences) >= 1:  # 降低句子数量要求
            score += 0.3
        
        # 内容密度评分（避免过多标点符号）- 更宽松
        text_chars = len(re.sub(r'\s', '', paragraph))
        if text_chars > 0:
            density = text_chars / length
            if density > 0.6:  # 降低密度要求
                score += 0.2
            elif density > 0.4:  # 增加中等密度的分数
                score += 0.1
        
        # 非洲新闻内容加分 - 增加权重
        if self._is_african_news_content(paragraph):
            score += 0.25
        
        # 多语言内容加分 - 增加权重
        if self._contains_multilingual_features(paragraph):
            score += 0.15
        
        # 复杂结构内容加分
        if paragraph.startswith(('表格内容:', '列表内容:', '层级内容:')):
            score += 0.15
        
        return min(score, 1.0)
    
    def _contains_french_keywords(self, text: str) -> bool:
        """检测是否包含法语关键词"""
        french_keywords = ['le', 'la', 'les', 'un', 'une', 'des', 'est', 'et', 'dans', 'pour', 'avec', 'sur', 'par', 'au', 'aux', 'du', 'de', 'à', 'en']
        text_lower = text.lower()
        french_count = sum(1 for keyword in french_keywords if keyword in text_lower)
        return french_count >= 3
    
    def _contains_arabic_keywords(self, text: str) -> bool:
        """检测是否包含阿拉伯语关键词"""
        arabic_keywords = ['ال', 'وال', 'في', 'من', 'إلى', 'على', 'عن', 'أن', 'إن', 'هذا', 'هذه', 'هؤلاء']
        text_lower = text.lower()
        arabic_count = sum(1 for keyword in arabic_keywords if keyword in text_lower)
        return arabic_count >= 2
    
    def _contains_african_language_keywords(self, text: str) -> bool:
        """检测是否包含非洲本地语言关键词"""
        african_keywords = ['habari', 'matukio', 'ripoti', 'makala', 'taarifa', 'uchambuzi', 'news', 'report', 'analysis', 'event']
        text_lower = text.lower()
        african_count = sum(1 for keyword in african_keywords if keyword in text_lower)
        return african_count >= 2
    
    def _contains_multilingual_features(self, text: str) -> bool:
        """检测是否包含多语言特征"""
        return (self._contains_french_keywords(text) or 
                self._contains_arabic_keywords(text) or 
                self._contains_african_language_keywords(text))
    
    def _score_paragraph_quality(self, paragraph: str) -> float:
        """评估段落质量评分（0-1）- 针对非洲新闻优化"""
        score = 0.0
        
        # 长度评分（0-0.3）- 降低要求
        if len(paragraph) >= 200:  # 降低满分长度要求
            score += 0.3
        elif len(paragraph) >= 100:
            score += 0.25
        elif len(paragraph) >= 50:
            score += 0.2
        elif len(paragraph) >= 30:
            score += 0.15
        elif len(paragraph) >= 20:
            score += 0.1
        else:
            score += 0.05
        
        # 句子结构评分（0-0.3）- 更宽松
        sentences = re.split(r'[.!?]+', paragraph)
        valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]  # 降低句子长度要求
        
        if len(valid_sentences) >= 2:  # 降低句子数量要求
            score += 0.3
        elif len(valid_sentences) >= 1:
            score += 0.2
        else:
            score += 0.1  # 即使没有有效句子也给予基础分数
        
        # 内容密度评分（0-0.2）- 更宽松
        if valid_sentences:
            avg_sentence_length = sum(len(s) for s in valid_sentences) / len(valid_sentences)
            if avg_sentence_length >= 30:  # 降低平均长度要求
                score += 0.2
            elif avg_sentence_length >= 20:
                score += 0.15
            elif avg_sentence_length >= 15:
                score += 0.1
            else:
                score += 0.05
        
        # 非洲内容加分（0-0.2）- 增加权重
        if self._is_african_news_content(paragraph):
            score += 0.2
        
        return min(1.0, score)
    
    def _is_african_news_content(self, text: str) -> bool:
        """检测是否为非洲新闻相关内容"""
        # 非洲国家关键词
        african_countries = [
            'nigeria', 'kenya', 'south africa', 'ghana', 'egypt', 'ethiopia',
            'tanzania', 'uganda', 'morocco', 'algeria', 'sudan', 'angola',
            'mozambique', 'zambia', 'zimbabwe', 'senegal', 'cameroon', 'cote d\'ivoire',
            'ivory coast', 'tunisia', 'libya', 'rwanda', 'burundi', 'somalia',
            'madagascar', 'mauritius', 'seychelles', 'comoros', 'djibouti', 'eritrea',
            'namibia', 'botswana', 'lesotho', 'swaziland', 'malawi', 'liberia',
            'sierra leone', 'benin', 'togo', 'niger', 'mali', 'burkina faso',
            'chad', 'central african republic', 'congo', 'democratic republic of congo',
            'gabon', 'equatorial guinea', 'sao tome and principe', 'cape verde',
            'gambia', 'guinea-bissau', 'guinea'
        ]
        
        # 非洲新闻相关关键词
        african_news_keywords = [
            'africa', 'african', 'continent', 'sub-saharan', 'west africa', 'east africa',
            'southern africa', 'north africa', 'central africa', 'horn of africa',
            'sahel', 'maghreb', 'ecowas', 'african union', 'pan-african'
        ]
        
        text_lower = text.lower()
        
        # 检查是否包含非洲国家或地区关键词
        for country in african_countries:
            if country in text_lower:
                return True
        
        # 检查是否包含非洲新闻相关关键词
        for keyword in african_news_keywords:
            if keyword in text_lower:
                return True
        
        # 检查是否包含非洲语言特征（法语、阿拉伯语等）
        french_indicators = ['le ', 'la ', 'les ', 'un ', 'une ', 'des ', 'est ', 'et ', 'dans ']
        arabic_indicators = ['ال', 'وال', 'في ', 'من ', 'إلى ', 'على ', 'عن ']
        
        for indicator in french_indicators:
            if indicator in text_lower:
                return True
        
        for indicator in arabic_indicators:
            if indicator in text_lower:
                return True
        
        return len(text) >= 50  # 如果文本较长且没有明显排除特征，也认为是相关内容
    
    def _is_likely_content_div_enhanced(self, div_content: str) -> bool:
        """增强版内容div判断"""
        div_lower = div_content.lower()
        
        # 排除包含导航、广告等关键词的div
        exclude_keywords = ['nav', 'menu', 'sidebar', 'advertisement', 'ad', 'banner', 'footer', 'header', 'widget', 'promo']
        for keyword in exclude_keywords:
            if keyword in div_lower:
                return False
        
        # 检查是否包含段落或较长的文本
        text_content = self._extract_text_from_html(div_content)
        if text_content and len(text_content.strip()) > 100:
            # 进一步检查文本质量
            sentences = re.split(r'[.!?]+', text_content)
            valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
            
            # 如果有足够多的有效句子，认为是主要内容
            if len(valid_sentences) >= 2:
                return True
        
        return False
    
    def _is_likely_content_div(self, div_content: str) -> bool:
        """判断div是否可能包含主要内容"""
        div_lower = div_content.lower()
        
        # 排除包含导航、广告等关键词的div
        exclude_keywords = ['nav', 'menu', 'sidebar', 'advertisement', 'ad', 'banner', 'footer', 'header']
        for keyword in exclude_keywords:
            if keyword in div_lower:
                return False
        
        # 检查是否包含段落或较长的文本
        text_content = self._extract_text_from_html(div_content)
        if text_content and len(text_content.strip()) > 100:
            return True
        
        return False
    
    def _extract_fallback_content(self, html_content: str) -> str:
        """备用内容提取方法"""
        # 提取body标签内的所有文本
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
        if body_match:
            body_text = self._extract_text_from_html(body_match.group(1))
            return body_text
        
        return ""
    
    def _extract_text_from_html(self, html: str) -> str:
        """从HTML片段中提取纯文本"""
        import html as html_module
        # 移除所有HTML标签
        text = re.sub(r'<[^>]+>', '', html)
        # 解码HTML实体
        text = html_module.unescape(text)
        # 清理多余的空格和换行
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _clean_and_limit_content(self, content: str, max_length: int = 5000) -> str:
        """内容清理和智能截断（特别优化非洲多语言内容）"""
        # 解码HTML实体
        content = html.unescape(content)
        # 清理多余的空格
        content = re.sub(r'\s+', ' ', content).strip()
        
        # 智能截断：避免在句子中间截断（支持多语言）
        if len(content) > max_length:
            # 查找最后一个完整的句子结束位置（支持多种语言）
            sentence_endings = [
                '.', '!', '?', '。', '!', '?',  # 中英文
                '»', '«', '؛', '؟', '۔',        # 阿拉伯语
                '።', '፧', '፨', '፡', '።',        # 阿姆哈拉语
                '፤', '፥', '፦', '፡', '።',        # 埃塞俄比亚语言
                '।', '॥', 'ॽ', '।', '॥',         # 印地语
                '⸮', '؟', '⸮', '؟', '⸮'          # 法语/阿拉伯语
            ]
            
            last_sentence_end = -1
            for ending in sentence_endings:
                end_pos = content.rfind(ending, 0, max_length)
                if end_pos > last_sentence_end:
                    last_sentence_end = end_pos
            
            if last_sentence_end > max_length * 0.7:  # 确保截断位置合理
                content = content[:last_sentence_end + 1]
            else:
                # 如果没有找到合适的句子结束位置，在单词边界处截断
                # 支持多种语言的分词边界
                word_boundaries = [' ', '\t', '\n', '\r', '\f', '\v']
                last_boundary = -1
                for boundary in word_boundaries:
                    boundary_pos = content.rfind(boundary, 0, max_length)
                    if boundary_pos > last_boundary:
                        last_boundary = boundary_pos
                
                if last_boundary > max_length * 0.8:
                    content = content[:last_boundary]
                else:
                    content = content[:max_length] + '...'
        
        return content
    
    def enhance_existing_content(self, original_content: str, url: str = "") -> str:
        """增强现有内容 - 重新爬取或智能处理"""
        # 如果内容过短或包含登录页面特征，标记为需要重新爬取
        if len(original_content.strip()) < 100 or self.is_login_page(original_content):
            return ""  # 空字符串表示需要重新爬取
        
        # 如果内容质量尚可，进行智能清理
        return self._clean_and_limit_content(original_content)
    
    def extract_content_with_metadata(self, html_content: str, url: str = "") -> Dict[str, Any]:
        """提取内容并包含元数据（发布日期等）"""
        result = {
            'content': '',
            'metadata': {},
            'quality_score': 0.0,
            'extraction_method': '',
            'date_info': {}
        }
        
        # 提取主要内容
        content = self.extract_news_content_advanced(html_content)
        result['content'] = content
        
        # 提取发布日期
        date_result = self.date_parser.extract_publish_date(html_content, url)
        result['date_info'] = date_result
        
        # 评估内容质量
        quality_result = self.validate_content_quality(content)
        result['quality_score'] = quality_result.get('quality_score', 0.0)
        
        # 确定提取方法
        if len(content) > 0:
            result['extraction_method'] = 'advanced_extraction'
        else:
            # 如果高级提取失败，尝试备用方法
            fallback_content = self._extract_fallback_content(html_content)
            if len(fallback_content) > 100:
                result['content'] = fallback_content
                result['extraction_method'] = 'fallback_extraction'
                result['quality_score'] = 0.5  # 备用方法质量分数较低
        
        # 收集元数据
        result['metadata'] = {
            'content_length': len(content),
            'has_date': date_result['date_found'],
            'publish_date': date_result.get('publish_date', ''),
            'date_confidence': date_result.get('confidence', 0.0),
            'quality_issues': quality_result.get('issues', []),
            'quality_suggestions': quality_result.get('suggestions', [])
        }
        
        return result


class DateParser:
    """日期解析器 - 专门用于从HTML和文本中提取发布日期"""
    
    def __init__(self):
        # 日期模式正则表达式 - 支持多种格式
        self.date_patterns = [
            # 标准格式
            r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b',  # 2024-01-15, 2024/01/15
            r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b',  # 15-01-2024, 15/01/2024
            
            # 带时间的格式
            r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})[T\s](\d{1,2}):(\d{2})',  # 2024-01-15T14:30
            r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})[\s](\d{1,2}):(\d{2})',  # 15/01/2024 14:30
            
            # 文本格式
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})\b',  # Jan 15, 2024
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b',  # January 15, 2024
            
            # 法语日期格式
            r'\b(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})\b',
            r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',  # 15/01/2024 (法语格式)
            
            # 阿拉伯语日期格式
            r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b',  # 15-01-2024 (阿拉伯语)
            
            # 非洲本地化格式
            r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b',  # 15 Jan 2024
            r'\b(\d{1,2})\s+(\d{1,2})\s+(\d{4})\b',  # 15 01 2024
        ]
        
        # 发布日期关键词
        self.publish_keywords = [
            'published', 'publié', 'veröffentlicht', 'publicado', 'نشر',
            'posted', 'posté', 'gepostet', 'publicado', 'نشر',
            'date', 'datum', 'fecha', 'تاريخ',
            'time', 'zeit', 'hora', 'وقت',
            'created', 'créé', 'erstellt', 'creado', 'تم إنشاؤه',
            'updated', 'mis à jour', 'aktualisiert', 'actualizado', 'تم التحديث',
            'news date', 'date de publication', 'veröffentlichungsdatum',
            'fecha de publicación', 'تاريخ النشر'
        ]
        
        # 月份映射
        self.month_mapping = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
            'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        }
    
    def extract_publish_date(self, html_content: str, url: str = "") -> Dict[str, Any]:
        """从HTML内容中提取发布日期"""
        result = {
            'date_found': False,
            'publish_date': None,
            'date_string': '',
            'confidence': 0.0,
            'source': '',
            'method': '',
            'year': None,
            'month': None,
            'day': None,
            'month_name': None,
            'quarter': None
        }
        
        # 方法1: 从meta标签提取
        meta_date = self._extract_from_meta_tags(html_content)
        if meta_date['date_found']:
            result.update(meta_date)
            result['confidence'] = max(result['confidence'], 0.9)
            # 提取月份细化信息
            month_details = self._extract_month_details(result.get('publish_date'), result.get('date_string'))
            result.update(month_details)
            return result
        
        # 方法2: 从HTML属性提取
        attr_date = self._extract_from_html_attributes(html_content)
        if attr_date['date_found']:
            result.update(attr_date)
            result['confidence'] = max(result['confidence'], 0.8)
            # 提取月份细化信息
            month_details = self._extract_month_details(result.get('publish_date'), result.get('date_string'))
            result.update(month_details)
            return result
        
        # 方法3: 从文本内容提取
        text_date = self._extract_from_text_content(html_content)
        if text_date['date_found']:
            result.update(text_date)
            result['confidence'] = max(result['confidence'], 0.7)
            # 提取月份细化信息
            month_details = self._extract_month_details(result.get('publish_date'), result.get('date_string'))
            result.update(month_details)
            return result
        
        return result
    
    def _extract_month_details(self, publish_date: str, date_string: str) -> Dict[str, Any]:
        """提取月份细化信息"""
        month_details = {
            'year': None,
            'month': None,
            'day': None,
            'month_name': None,
            'quarter': None
        }
        
        if publish_date:
            # 从标准化日期中提取
            try:
                from datetime import datetime
                dt = datetime.strptime(publish_date, '%Y-%m-%d')
                month_details['year'] = dt.year
                month_details['month'] = dt.month
                month_details['day'] = dt.day
                month_details['month_name'] = self._get_month_name(dt.month)
                month_details['quarter'] = (dt.month - 1) // 3 + 1
            except:
                pass
        
        if date_string and (month_details['month'] is None):
            # 从原始日期字符串中尝试提取月份
            month_from_string = self._extract_month_from_string(date_string)
            if month_from_string:
                month_details['month'] = month_from_string
                month_details['month_name'] = self._get_month_name(month_from_string)
                month_details['quarter'] = (month_from_string - 1) // 3 + 1
        
        return month_details
    
    def _extract_month_from_string(self, date_string: str) -> int:
        """从日期字符串中提取月份"""
        # 尝试匹配月份名称或缩写
        month_patterns = [
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
            r'\b(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\b'
        ]
        
        for pattern in month_patterns:
            matches = re.findall(pattern, date_string, re.IGNORECASE)
            if matches:
                month_str = matches[0].lower()
                for key, value in self.month_mapping.items():
                    if month_str.startswith(key):
                        return value
        
        # 尝试从数字格式中提取
        month_num_patterns = [
            r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b',
            r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b'
        ]
        
        for pattern in month_num_patterns:
            matches = re.findall(pattern, date_string)
            if matches:
                if len(matches[0]) >= 2:
                    try:
                        month = int(matches[0][1])
                        if 1 <= month <= 12:
                            return month
                    except:
                        pass
        
        return None
    
    def _get_month_name(self, month: int) -> str:
        """获取月份名称"""
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        return month_names.get(month, '')
    
    def _extract_from_meta_tags(self, html_content: str) -> Dict[str, Any]:
        """从meta标签提取发布日期"""
        meta_patterns = [
            r'<meta[^>]*property="(?:article:published_time|publish_date)"[^>]*content="([^"]+)"[^>]*>',
            r'<meta[^>]*name="(?:publish_date|date|DC\.date)"[^>]*content="([^"]+)"[^>]*>',
            r'<meta[^>]*content="([^"]+)"[^>]*property="(?:article:published_time|publish_date)"[^>]*>',
            r'<meta[^>]*content="([^"]+)"[^>]*name="(?:publish_date|date)"[^>]*>',
        ]
        
        for pattern in meta_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                date_str = match if isinstance(match, str) else match[0]
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    return {
                        'date_found': True,
                        'publish_date': parsed_date,
                        'date_string': date_str,
                        'source': 'meta_tag',
                        'method': 'property_attribute'
                    }
        
        return {'date_found': False}
    
    def _extract_from_html_attributes(self, html_content: str) -> Dict[str, Any]:
        """从HTML属性提取发布日期"""
        # 查找包含日期关键词的标签
        patterns = [
            r'<(?:time|span|div)[^>]*\b(?:published|date|time)\b[^>]*>([^<]+)</(?:time|span|div)>',
            r'<(?:time|span|div)[^>]*datetime="([^"]+)"[^>]*>',
            r'<(?:time|span|div)[^>]*data-date="([^"]+)"[^>]*>',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                date_str = match
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    return {
                        'date_found': True,
                        'publish_date': parsed_date,
                        'date_string': date_str,
                        'source': 'html_attribute',
                        'method': 'tag_attribute'
                    }
        
        return {'date_found': False}
    
    def _extract_from_text_content(self, html_content: str) -> Dict[str, Any]:
        """从文本内容提取发布日期 - 增强版"""
        # 提取纯文本
        text_content = re.sub(r'<[^>]+>', ' ', html_content)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # 增强版关键词匹配 - 支持多语言和上下文
        enhanced_keywords = self.publish_keywords + [
            # 非洲本地化关键词
            'il y a', 'ago', 'قبل', 'há', 'vor',  # 时间相关
            'actualité', 'actualidad', 'Aktualität', 'أخبار',  # 新闻相关
            'report', 'rapport', 'Bericht', 'تقرير',  # 报告相关
            'analysis', 'analyse', 'Analyse', 'تحليل',  # 分析相关
            'study', 'étude', 'Studie', 'دراسة',  # 研究相关
            'survey', 'enquête', 'Umfrage', 'استطلاع'  # 调查相关
        ]
        
        # 方法1: 上下文关键词匹配
        for keyword in enhanced_keywords:
            # 更灵活的上下文匹配模式
            keyword_patterns = [
                r'\b' + re.escape(keyword) + r'[^.!?]*?\b(\d{1,4}[-/\s]\d{1,2}[-/\s]\d{1,4})\b',
                r'\b(\d{1,4}[-/\s]\d{1,2}[-/\s]\d{1,4})[^.!?]*?\b' + re.escape(keyword) + r'\b',
                r'\b' + re.escape(keyword) + r'\s*[:：]\s*(\d{1,4}[-/\s]\d{1,2}[-/\s]\d{1,4})\b'
            ]
            
            for pattern in keyword_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for date_str in matches:
                    parsed_date = self._parse_date_string(date_str)
                    if parsed_date:
                        return {
                            'date_found': True,
                            'publish_date': parsed_date,
                            'date_string': date_str,
                            'source': 'text_content',
                            'method': 'enhanced_keyword_context',
                            'confidence': 0.85
                        }
        
        # 方法2: 智能日期模式匹配
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    date_str = ' '.join(match)
                else:
                    date_str = match
                
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    # 计算置信度：基于日期格式的标准化程度
                    confidence = self._calculate_date_confidence(date_str, parsed_date)
                    return {
                        'date_found': True,
                        'publish_date': parsed_date,
                        'date_string': date_str,
                        'source': 'text_content',
                        'method': 'pattern_matching',
                        'confidence': confidence
                    }
        
        # 方法3: 非洲新闻网站特定日期格式
        african_date_patterns = [
            # 法语非洲格式
            r'\b(\d{1,2})\s+(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)\.?\s+(\d{4})\b',
            # 阿拉伯语格式
            r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b',
            # 本地化格式
            r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b'
        ]
        
        for pattern in african_date_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    date_str = ' '.join(match)
                else:
                    date_str = match
                
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    return {
                        'date_found': True,
                        'publish_date': parsed_date,
                        'date_string': date_str,
                        'source': 'text_content',
                        'method': 'african_pattern',
                        'confidence': 0.75
                    }
        
        return {'date_found': False}
    
    def _calculate_date_confidence(self, original_date: str, parsed_date: str) -> float:
        """计算日期识别的置信度"""
        confidence = 0.5  # 基础置信度
        
        # 基于格式标准化程度
        if parsed_date == original_date:
            confidence += 0.3  # 完全匹配
        elif re.match(r'^\d{4}-\d{2}-\d{2}$', parsed_date):
            confidence += 0.2  # 标准格式
        
        # 基于日期合理性
        try:
            from datetime import datetime
            dt = datetime.strptime(parsed_date, '%Y-%m-%d')
            current_year = datetime.now().year
            
            # 检查年份合理性
            if 2000 <= dt.year <= current_year + 1:
                confidence += 0.2
            elif 1900 <= dt.year < 2000:
                confidence += 0.1
            
            # 检查月份和日期合理性
            if 1 <= dt.month <= 12 and 1 <= dt.day <= 31:
                confidence += 0.1
                
        except:
            pass
        
        return min(confidence, 1.0)
    
    def _parse_date_string(self, date_str: str) -> str:
        """解析日期字符串为标准化格式 - 增强版"""
        try:
            # 清理日期字符串
            date_str = date_str.strip()
            
            # 处理常见日期格式
            if 'T' in date_str:
                # ISO格式: 2024-01-15T14:30:00Z
                date_str = date_str.split('T')[0]
            
            # 尝试多种解析方式
            from datetime import datetime
            
            # 标准格式尝试
            formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%d-%m-%Y',
                '%d/%m/%Y',
                '%m-%d-%Y',
                '%m/%d/%Y',
                '%Y.%m.%d',
                '%d.%m.%Y',
                # 非洲本地化格式
                '%d %b %Y',  # 15 Jan 2024
                '%d %B %Y',  # 15 January 2024
                '%b %d, %Y',  # Jan 15, 2024
                '%B %d, %Y',  # January 15, 2024
                # 法语格式
                '%d %B %Y',  # 15 janvier 2024
                '%d %b %Y',  # 15 janv. 2024
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # 文本月份格式 - 增强版
            for month_name, month_num in self.month_mapping.items():
                if month_name in date_str.lower():
                    # 尝试解析类似 "15 Jan 2024" 的格式
                    patterns = [
                        r'(\d{1,2})\s+' + re.escape(month_name) + r'\s+(\d{4})',
                        r'(\d{1,2})\s+' + re.escape(month_name) + r'\.?\s+(\d{4})',
                        r'' + re.escape(month_name) + r'\s+(\d{1,2}),?\s+(\d{4})'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, date_str, re.IGNORECASE)
                        if match:
                            groups = match.groups()
                            if len(groups) == 2:
                                day, year = groups
                                return f"{year}-{month_num:02d}-{int(day):02d}"
                            elif len(groups) == 3:
                                month, day, year = groups
                                return f"{year}-{month_num:02d}-{int(day):02d}"
            
            # 非洲本地化日期格式处理
            # 处理类似 "15/01/2024" 的格式（日/月/年）
            if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
                parts = date_str.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    try:
                        dt = datetime(int(year), int(month), int(day))
                        return dt.strftime('%Y-%m-%d')
                    except:
                        pass
            
            # 处理类似 "2024-01-15" 但顺序可能不同的格式
            date_parts = re.findall(r'\d+', date_str)
            if len(date_parts) == 3:
                # 尝试不同的组合
                combinations = [
                    (date_parts[0], date_parts[1], date_parts[2]),  # YYYY-MM-DD
                    (date_parts[2], date_parts[1], date_parts[0]),  # DD-MM-YYYY
                    (date_parts[2], date_parts[0], date_parts[1]),  # DD-YYYY-MM
                ]
                
                for year, month, day in combinations:
                    try:
                        if len(year) == 4 and len(month) <= 2 and len(day) <= 2:
                            dt = datetime(int(year), int(month), int(day))
                            if 2000 <= dt.year <= datetime.now().year + 1:
                                return dt.strftime('%Y-%m-%d')
                    except:
                        continue
            
            return None
            
        except Exception as e:
            logger.debug(f"日期解析失败: {date_str}, 错误: {e}")
            return None


def test_content_extraction():
    """测试内容提取功能"""
    optimizer = ContentExtractionOptimizer()
    
    # 测试HTML内容
    test_html = """
    <html>
    <head><title>测试文章</title></head>
    <body>
        <div class="article-content">
            <h1>这是文章标题</h1>
            <p>这是第一段内容，包含重要的新闻信息。</p>
            <p>这是第二段内容，继续详细描述新闻事件。</p>
            <p>这是第三段内容，提供更多的背景信息和细节。</p>
        </div>
        <div class="sidebar">广告内容</div>
    </body>
    </html>
    """
    
    result = optimizer.extract_news_content_advanced(test_html)
    print("提取结果:")
    print(result)
    print(f"内容长度: {len(result)} 字符")


def test_date_parsing():
    """测试日期解析功能"""
    date_parser = DateParser()
    
    # 测试HTML内容
    test_html = """
    <html>
    <head>
        <meta property="article:published_time" content="2024-01-15T14:30:00Z">
        <title>测试文章 - 发布日期测试</title>
    </head>
    <body>
        <div class="article-header">
            <h1>文章标题</h1>
            <time datetime="2024-01-15">发布于 2024年1月15日</time>
        </div>
        <div class="article-content">
            <p>这是文章内容，发布于 2024-01-15。</p>
        </div>
    </body>
    </html>
    """
    
    result = date_parser.extract_publish_date(test_html)
    print("日期解析结果:")
    print(f"找到日期: {result['date_found']}")
    if result['date_found']:
        print(f"发布日期: {result['publish_date']}")
        print(f"原始字符串: {result['date_string']}")
        print(f"置信度: {result['confidence']}")
        print(f"来源: {result['source']}")
        print(f"方法: {result['method']}")


def test_integrated_extraction():
    """测试集成的内容提取和日期解析功能"""
    optimizer = ContentExtractionOptimizer()
    
    # 测试HTML内容（包含日期信息）
    test_html = """
    <html>
    <head>
        <title>非洲新闻：尼日利亚经济发展报告</title>
        <meta name="publish_date" content="2023-12-25">
    </head>
    <body>
        <div class="header">
            <span class="date">发布日期: 2023年12月25日</span>
        </div>
        <div class="navigation">首页 | 新闻 | 关于我们</div>
        <div class="main-content">
            <h1>尼日利亚2023年经济发展报告</h1>
            <p>尼日利亚作为非洲最大的经济体之一，在2023年取得了显著的经济增长。</p>
            <p>根据最新数据显示，尼日利亚GDP增长率达到3.5%，主要得益于石油出口和农业部门的复苏。</p>
            <p>政府实施的各项经济改革措施也起到了积极的推动作用。</p>
        </div>
        <div class="footer">© 2023 非洲新闻网</div>
    </body>
    </html>
    """
    
    print("=== 测试集成的内容提取和日期解析 ===")
    result = optimizer.extract_content_with_metadata(test_html, "https://africanews.com/nigeria-economy")
    
    print(f"提取方法: {result['extraction_method']}")
    print(f"质量分数: {result['quality_score']:.2f}")
    print(f"内容长度: {result['metadata']['content_length']} 字符")
    print(f"是否找到日期: {result['metadata']['has_date']}")
    print(f"发布日期: {result['metadata']['publish_date']}")
    print(f"日期置信度: {result['metadata']['date_confidence']:.2f}")
    
    print("\n=== 内容预览 ===")
    content = result['content']
    if len(content) > 200:
        print(f"内容: {content[:200]}...")
    else:
        print(f"内容: {content}")
    
    print("\n=== 质量评估 ===")
    if result['metadata']['quality_issues']:
        print("质量问题:")
        for issue in result['metadata']['quality_issues']:
            print(f"  - {issue}")
    else:
        print("无质量问题")
    
    if result['metadata']['quality_suggestions']:
        print("改进建议:")
        for suggestion in result['metadata']['quality_suggestions']:
            print(f"  - {suggestion}")


if __name__ == "__main__":
    test_content_extraction()
    print("\n" + "="*50 + "\n")
    test_date_parsing()
    print("\n" + "="*50 + "\n")
    test_integrated_extraction()