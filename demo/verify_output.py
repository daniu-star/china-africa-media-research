import json

# 验证输出文件
def verify_output():
    output_file = "清洗数据/原始数据.json"
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"文件包含 {len(data)} 篇文章")
        print("\n第一篇文章示例：")
        first_article = data[0]
        # 打印文章的关键信息
        print(f"标题: {first_article.get('title', '无标题')}")
        print(f"URL: {first_article.get('url', '无URL')}")
        print(f"发布日期: {first_article.get('publish_date', '无发布日期')}")
        print(f"来源: {first_article.get('source', '无来源')}")
        print(f"关键词: {first_article.get('keyword', '无关键词')}")
        print(f"内容预览: {first_article.get('content', '')[:200]}...")
        
        print("\n文件验证成功！")
        return True
    
    except Exception as e:
        print(f"文件验证失败: {e}")
        return False

if __name__ == "__main__":
    verify_output()