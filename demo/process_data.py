import os
import json
import glob

# 设置数据目录和输出目录
data_dir = "c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\非洲数据\\非洲数据\\data"
output_dir = "c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\清洗数据"
output_file = os.path.join(output_dir, "原始数据.json")

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)

# 用于存储唯一文章的集合（使用URL作为键）
unique_articles = {}
# 统计信息
total_files = 0
total_articles = 0
duplicate_articles = 0

# 遍历所有results_*.json文件
json_files = glob.glob(os.path.join(data_dir, "**", "results_*.json"), recursive=True)

print(f"找到 {len(json_files)} 个JSON文件")

for file_path in json_files:
    total_files += 1
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # 处理数据格式
        if isinstance(content, list):
            # 格式1：直接是文章数组
            articles = content
        elif isinstance(content, dict) and 'results' in content:
            # 格式2：包含task信息和results数组
            articles = content['results']
        else:
            # 未知格式，跳过
            continue
        
        # 处理每篇文章
        for article in articles:
            total_articles += 1
            # 使用URL作为唯一标识
            url = article.get('url', '')
            if url:
                if url not in unique_articles:
                    unique_articles[url] = article
                else:
                    duplicate_articles += 1
    
    except json.JSONDecodeError as e:
        print(f"解析文件 {file_path} 时出错: {e}")
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
    
    # 每处理1000个文件打印一次进度
    if total_files % 1000 == 0:
        print(f"已处理 {total_files} 个文件，累计文章 {total_articles} 篇，重复文章 {duplicate_articles} 篇")

# 保存去重后的文章
unique_articles_list = list(unique_articles.values())
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(unique_articles_list, f, ensure_ascii=False, indent=2)

print(f"\n处理完成！")
print(f"总文件数: {total_files}")
print(f"总文章数: {total_articles}")
print(f"重复文章数: {duplicate_articles}")
print(f"唯一文章数: {len(unique_articles_list)}")
print(f"输出文件: {output_file}")