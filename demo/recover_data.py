import json
import re
import os

def recover_data():
    print("=== 数据恢复程序 ===")
    
    # 读取原始文件
    with open("c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\data\\results_0.json.backup", "r", encoding="utf-8") as f:
        content = f.read()
    
    print(f"原始文件大小: {len(content):,} 字符")
    
    # 方法1：尝试提取所有完整的JSON对象
    print("\n方法1：提取完整JSON对象...")
    
    # 查找所有可能的文章对象模式
    article_patterns = []
    
    # 更精确的模式匹配
    pattern = r'\{\s*"title"\s*:\s*"[^"]*"[^}]*\}'
    matches = re.finditer(pattern, content)
    
    valid_articles = []
    for match in matches:
        try:
            article_json = match.group()
            # 尝试解析
            article = json.loads(article_json)
            if article.get('title') and article.get('url'):
                valid_articles.append(article)
        except:
            continue
    
    print(f"找到有效文章: {len(valid_articles)} 篇")
    
    if valid_articles:
        # 创建恢复的数据结构
        recovered_data = {
            "articles": valid_articles,
            "articles_found": len(valid_articles),
            "recovery_method": "regex_extraction",
            "original_file_size": len(content)
        }
        
        # 保存恢复的数据
        output_file = "data/results_recovered.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(recovered_data, f, ensure_ascii=False, indent=2)
        
        print(f"恢复的数据已保存到: {output_file}")
        
        # 显示一些样本数据
        print("\n样本文章:")
        for i, article in enumerate(valid_articles[:3]):
            print(f"{i+1}. 标题: {article.get('title', 'N/A')}")
            print(f"   URL: {article.get('url', 'N/A')}")
            print(f"   来源: {article.get('source', 'N/A')}")
            print()
    
    # 方法2：如果方法1失败，尝试手动解析
    if len(valid_articles) < 1000:  # 如果恢复的文章太少
        print("\n方法2：尝试手动解析...")
        
        # 查找articles数组的开始位置
        articles_start = content.find('"articles"')
        if articles_start != -1:
            bracket_start = content.find('[', articles_start)
            if bracket_start != -1:
                # 提取articles数组内容
                bracket_count = 1
                pos = bracket_start + 1
                
                while pos < len(content) and bracket_count > 0:
                    if content[pos] == '[':
                        bracket_count += 1
                    elif content[pos] == ']':
                        bracket_count -= 1
                    pos += 1
                
                if bracket_count == 0:
                    articles_content = content[bracket_start:pos]
                    print(f"找到articles数组，长度: {len(articles_content):,} 字符")
                    
                    # 尝试修复数组内容
                    # 移除可能的多余字符
                    fixed_content = articles_content.replace('"articles":', '').strip()
                    
                    try:
                        # 尝试解析为JSON
                        articles_list = json.loads(fixed_content)
                        if isinstance(articles_list, list):
                            print(f"成功解析文章列表，数量: {len(articles_list)}")
                            
                            # 保存修复的数据
                            recovered_data = {
                                "articles": articles_list,
                                "articles_found": len(articles_list),
                                "recovery_method": "direct_parsing",
                                "original_file_size": len(content)
                            }
                            
                            output_file = "data/results_recovered_method2.json"
                            with open(output_file, "w", encoding="utf-8") as f:
                                json.dump(recovered_data, f, ensure_ascii=False, indent=2)
                            
                            print(f"方法2恢复的数据已保存到: {output_file}")
                    except Exception as e:
                        print(f"方法2解析失败: {e}")
    
    print("\n=== 数据恢复完成 ===")

if __name__ == "__main__":
    recover_data()