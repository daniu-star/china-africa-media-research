#!/usr/bin/env python3
"""
测试增强版数据质量处理功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_quality_optimizer import data_quality_optimizer

def test_enhanced_data_quality():
    """测试增强版数据质量处理功能"""
    print("=== 测试增强版数据质量处理功能 ===\n")
    
    # 测试用例1：标准新闻文章
    print("1. 测试标准新闻文章：")
    article1 = {
        'title': '非洲经济发展迎来新机遇，多国合作推动区域一体化',
        'content': '''
        近日，非洲多个国家在经济发展方面取得了显著进展。根据最新数据显示，
        非洲大陆的经济增长率达到了5.2%，创下近年新高。
        
        专家分析认为，这一增长主要得益于基础设施建设的加速推进和数字经济的快速发展。
        多个非洲国家正在加强合作，共同推动区域经济一体化进程。
        
        在数字经济领域，非洲的移动支付和电子商务发展迅速，为经济增长注入了新动力。
        同时，可再生能源项目的建设也为非洲的可持续发展提供了重要支撑。
        ''',
        'metadata': {
            'date': {
                'value': '2024-01-15',
                'confidence': 0.95,
                'source': 'meta_tag'
            },
            'author': {
                'value': 'John Smith',
                'confidence': 0.90,
                'source': 'meta_tag'
            }
        }
    }
    
    result1 = data_quality_optimizer.validate_article_quality(article1)
    print(f"质量状态: {result1['quality_status']}")
    print(f"质量分数: {result1['quality_score']}")
    print(f"元数据完整性: {result1['metadata_completeness']}")
    print(f"发现的问题数: {result1['issues_found']}")
    print("建议:")
    for suggestion in result1['suggestions']:
        print(f"  - {suggestion}")
    print()
    
    # 测试用例2：法语新闻文章
    print("2. 测试法语新闻文章：")
    article2 = {
        'title': 'Le développement économique en Afrique connaît de nouvelles opportunités',
        'content': '''
        Récemment, de nombreux pays africains ont réalisé des progrès significatifs dans le développement économique. 
        Selon les dernières données, le taux de croissance économique du continent africain a atteint 5,2%, 
        atteignant un nouveau sommet ces dernières années.
        
        Les experts estiment que cette croissance est principalement due à l'accélération de la construction 
        d'infrastructures et au développement rapide de l'économie numérique.
        
        Dans le domaine de l'économie numérique, les paiements mobiles et le commerce électronique 
        se développent rapidement en Afrique, injectant une nouvelle dynamique dans la croissance économique.
        ''',
        'metadata': {
            'date': {
                'value': '15 janvier 2024',
                'confidence': 0.85,
                'source': 'text_pattern'
            },
            'author': {
                'value': 'Rédaction Afrique',
                'confidence': 0.70,
                'source': 'first_paragraph'
            }
        }
    }
    
    result2 = data_quality_optimizer.validate_article_quality(article2)
    print(f"质量状态: {result2['quality_status']}")
    print(f"质量分数: {result2['quality_score']}")
    print(f"元数据完整性: {result2['metadata_completeness']}")
    print(f"发现的问题数: {result2['issues_found']}")
    print("建议:")
    for suggestion in result2['suggestions']:
        print(f"  - {suggestion}")
    print()
    
    # 测试用例3：质量较差的文章
    print("3. 测试质量较差的文章：")
    article3 = {
        'title': 'Breaking News',
        'content': 'This is a short article with limited content.',
        'metadata': {
            'date': {
                'value': 'yesterday',
                'confidence': 0.30,
                'source': 'relative_time'
            },
            'author': {
                'value': '',
                'confidence': 0.0,
                'source': 'unknown'
            }
        }
    }
    
    result3 = data_quality_optimizer.validate_article_quality(article3)
    print(f"质量状态: {result3['quality_status']}")
    print(f"质量分数: {result3['quality_score']}")
    print(f"元数据完整性: {result3['metadata_completeness']}")
    print(f"发现的问题数: {result3['issues_found']}")
    print("建议:")
    for suggestion in result3['suggestions']:
        print(f"  - {suggestion}")
    print()
    
    # 测试用例4：测试语言检测功能
    print("4. 测试语言检测功能：")
    test_texts = [
        "This is an English article about African development.",
        "Cet article est en français et parle du développement en Afrique.",
        "Este artigo está em português e fala sobre o desenvolvimento em África.",
        "هذا المقال باللغة العربية ويتحدث عن التنمية في أفريقيا.",
        "这是一篇关于非洲发展的中文文章。"
    ]
    
    for i, text in enumerate(test_texts, 1):
        language_result = data_quality_optimizer._detect_language(text)
        print(f"文本{i}: {text[:50]}...")
        print(f"  检测语言: {language_result}")
    print()
    
    # 测试用例5：测试内容提取功能
    print("5. 测试内容提取功能：")
    html_content = '''
    <html>
    <head><title>Test Article</title></head>
    <body>
        <div class="header">Header content</div>
        <div class="content">
            <h1>Main Article Title</h1>
            <p>This is the first paragraph of the article content.</p>
            <p>This is the second paragraph with more detailed information.</p>
            <div class="advertisement">Ad content here</div>
            <p>This is the third paragraph continuing the article.</p>
        </div>
        <div class="footer">Footer content</div>
    </body>
    </html>
    '''
    
    # 创建BeautifulSoup对象
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 调试：检查选择器是否匹配到元素
    print("调试选择器匹配：")
    test_selectors = [
        'article .article-body',
        '.article .content',
        '.news-article .text',
        '.story .body',
        '.post .entry',
        '.news-detail .detail-content',
        '.main-article .article-content',
        '.article-content',
        'article div.article-content',
        'div.article-content',  # 更通用的选择器
        'article',  # 直接选择article元素
        'div.content',  # 通用内容选择器
        'div.text',  # 通用文本选择器
        'div.body',  # 通用正文选择器
        'div.main',  # 通用主内容选择器
        'div.entry-content',  # 通用入口内容选择器
        'div.post-content'  # 通用文章内容选择器
    ]
    
    for selector in test_selectors:
        element = soup.select_one(selector)
        if element:
            print(f"选择器 '{selector}' 匹配到元素")
            print(f"元素内容预览: {element.get_text()[:100]}...")
            break
    else:
        print("所有选择器都没有匹配到元素")
        # 打印HTML结构进行调试
        print("HTML结构预览：")
        print(soup.prettify()[:500])
    
    # 测试内部方法调用
    element = soup.select_one('div.content')
    if element:
        cleaned_text = data_quality_optimizer._clean_and_extract_text(element)
        is_valid = data_quality_optimizer._is_valid_content(cleaned_text)
        
        print(f"清理后的文本长度: {len(cleaned_text)} 字符")
        print(f"内容是否有效: {is_valid}")
        print(f"最小内容长度要求: {data_quality_optimizer.quality_config['min_content_length']} 字符")
    
    extracted_content = data_quality_optimizer._extract_content(soup)
    print(f"\n最终提取的内容长度: {len(extracted_content)} 字符")
    print(f"最终提取的内容预览: {extracted_content[:200]}...")
    print()
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    test_enhanced_data_quality()