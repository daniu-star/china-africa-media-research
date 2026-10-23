import json

# 定义与中国相关的关键词
china_keywords = [
    "China", "Chinese", "Xi Jinping", "Beijing", "Gansu", "Hong Kong",
    "Sungrow", "Sailun", "TEDA", "Shanghai Cooperation Organization", "SCO",
    "Belt and Road", "一带一路", "中国", "中国人", "中国领导人"
]

# 统计计数器
china_articles_count = 0
china_articles = []

# 读取并解析JSON文件
with open(r"c:\Users\13067\Desktop\论文\非洲\demo\清洗数据.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    
    # 遍历每条报道
    for article in data:
        # 检查是否包含中国相关关键词
        contains_china = False
        
        # 检查标题
        if "title" in article and article["title"]:
            for keyword in china_keywords:
                if keyword.lower() in article["title"].lower():
                    contains_china = True
                    break
        
        # 检查摘要
        if not contains_china and "summary" in article and article["summary"]:
            for keyword in china_keywords:
                if keyword.lower() in article["summary"].lower():
                    contains_china = True
                    break
        
        # 检查关键词
        if not contains_china and "keywords" in article and article["keywords"]:
            # 处理keywords字段，无论是字符串还是列表
            keywords = article["keywords"]
            if isinstance(keywords, list):
                keywords_str = " ".join(keywords)
            else:
                keywords_str = keywords
            
            for keyword in china_keywords:
                if keyword.lower() in keywords_str.lower():
                    contains_china = True
                    break
        
        # 检查正文内容
        if not contains_china and "content" in article and article["content"]:
            for keyword in china_keywords:
                if keyword.lower() in article["content"].lower():
                    contains_china = True
                    break
        
        # 如果包含中国相关内容，增加计数并保存
        if contains_china:
            china_articles_count += 1
            china_articles.append(article)

# 输出结果
print(f"与中国相关的报道总数: {china_articles_count}")

# 将结果保存到文件
with open("china_articles.json", "w", encoding="utf-8") as f:
    json.dump(china_articles, f, ensure_ascii=False, indent=2)

print("与中国相关的报道已保存到 china_articles.json 文件中")
