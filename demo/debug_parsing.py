"""
调试HTML解析问题
"""

from bs4 import BeautifulSoup

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

def debug_content_extraction():
    soup = BeautifulSoup(test_html, 'html.parser')
    
    print("=== 调试内容提取 ===")
    
    # 测试选择器
    selectors = [
        'article[class*="content"]',
        'div[class*="article-body"]',
        '.article-content',
        '.article-body',
        'article',
        'p'
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        print(f"选择器 '{selector}' 找到 {len(elements)} 个元素")
        
        for i, element in enumerate(elements):
            text = element.get_text(separator='\n')
            print(f"  元素 {i+1}: 文本长度 = {len(text)}")
            if len(text) > 0:
                print(f"  前50字符: {text[:50]}")
    
    # 测试段落提取
    paragraphs = soup.find_all('p')
    print(f"\n找到 {len(paragraphs)} 个段落")
    
    for i, p in enumerate(paragraphs):
        text = p.get_text()
        print(f"段落 {i+1}: {text}")
    
    # 测试文本清理
    print("\n=== 测试文本清理 ===")
    for i, p in enumerate(paragraphs):
        text = p.get_text()
        cleaned = text.strip()
        print(f"段落 {i+1} 清理后: 长度={len(cleaned)}, 内容='{cleaned}'")

if __name__ == "__main__":
    debug_content_extraction()