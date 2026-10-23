import json
from urllib.parse import urlparse

# 读取去重后的新闻数据文件
file_path = r'c:\Users\13067\Desktop\论文\非洲\demo\all_unique_news_data.json'

with open(file_path, 'r', encoding='utf-8') as f:
    all_news = json.load(f)

# 定义域名到消息来源的映射
domain_to_source = {
    'cgtn.com': 'CGTN',
    'africa.cgtn.com': 'CGTN',
    'yidaiyilu.gov.cn': '中国一带一路网',
    'xinhuanet.com': '新华网',
    'news.cn': '新华网',
    'xinhua.org': '新华网',
    'ahram.org.eg': 'Ahram Online',
    'news24.com': 'News24',
    'fin24.com': 'Fin24',
    'iol.co.za': 'IOL',
    'thisdaylive.com': 'THISDAYLIVE',
    'example.com': '示例网站'
    # 可以根据需要添加更多域名映射
}

# 提取并分析每条新闻的URL
print("新闻报道来源分析（按URL）：")
print("=" * 80)

for i, news in enumerate(all_news, 1):
    if isinstance(news, dict):
        title = news.get('title', '无标题')
        url = news.get('url', '')
        
        if url:
            # 解析URL，提取域名
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            # 去除www前缀
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # 判断消息来源
            source = domain_to_source.get(domain, f'未知来源 ({domain})')
            
            print(f"新闻 {i:3d}: {title}")
            print(f"  URL: {url}")
            print(f"  域名: {domain}")
            print(f"  消息来源: {source}")
        else:
            print(f"新闻 {i:3d}: {title}")
            print(f"  URL: 无")
            print(f"  域名: 无")
            print(f"  消息来源: 无")
        print()

print("=" * 80)
print("分析完成！")
