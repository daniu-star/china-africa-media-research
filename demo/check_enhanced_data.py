import json

def check_enhanced_data():
    """检查增强后的数据质量"""
    try:
        with open('data/results_content_enhanced.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = data.get('articles', [])
        print(f'增强后文章总数: {len(articles)}')
        
        if not articles:
            print('没有找到文章数据')
            return
        
        # 内容长度统计
        content_lengths = []
        for article in articles:
            content = article.get('content', '')
            if content:
                content_lengths.append(len(content))
        
        if content_lengths:
            print(f'内容长度统计:')
            print(f'  平均长度: {sum(content_lengths)/len(content_lengths):.1f} 字符')
            print(f'  最大长度: {max(content_lengths)} 字符')
            print(f'  最小长度: {min(content_lengths)} 字符')
            
            # 内容分布
            short = len([l for l in content_lengths if l < 100])
            medium = len([l for l in content_lengths if 100 <= l < 500])
            long = len([l for l in content_lengths if l >= 500])
            
            print(f'内容分布:')
            print(f'  短内容(<100字符): {short} 篇 ({short/len(content_lengths)*100:.1f}%)')
            print(f'  中等内容(100-500字符): {medium} 篇 ({medium/len(content_lengths)*100:.1f}%)')
            print(f'  长内容(≥500字符): {long} 篇 ({long/len(content_lengths)*100:.1f}%)')
            
            # 检查前几篇文章
            print('\n前3篇文章预览:')
            for i in range(min(3, len(articles))):
                article = articles[i]
                title = article.get('title', '无标题')
                content = article.get('content', '')
                content_preview = content[:200] + '...' if len(content) > 200 else content
                
                print(f'{i+1}. 标题: {title}')
                print(f'   内容长度: {len(content)} 字符')
                print(f'   内容预览: {content_preview}')
                print()
        
        # 检查需要重新爬取的文章
        try:
            with open('data/recrawl_urls.json', 'r', encoding='utf-8') as f:
                recrawl_data = json.load(f)
            recrawl_urls = recrawl_data.get('urls', [])
            print(f'需要重新爬取的URL数量: {len(recrawl_urls)}')
        except FileNotFoundError:
            print('未找到需要重新爬取的URL列表')
            
    except Exception as e:
        print(f'检查数据时出错: {e}')

if __name__ == '__main__':
    check_enhanced_data()