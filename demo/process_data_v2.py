import os
import json
import glob
import hashlib

# 设置数据目录和输出目录
data_dir = "c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\非洲数据\\非洲数据\\data"
output_dir = "c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\清洗数据"
output_file = os.path.join(output_dir, "原始数据.json")

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)

# 用于存储唯一文章的字典，键为生成的唯一标识
unique_articles = {}
# 统计信息
total_files = 0
successful_files = 0
error_files = 0
total_articles = 0
duplicate_articles = 0

# 生成唯一标识的函数
def generate_unique_key(article):
    url = article.get('url', '')
    title = article.get('title', '')
    publish_date = article.get('publish_date', '')
    content = article.get('content', '')[:100]  # 使用前100个字符作为内容摘要
    
    # 优先使用URL+标题+发布日期
    if url and title and publish_date:
        key = f"{url}|{title}|{publish_date}"
    # 其次使用标题+发布日期+内容摘要
    elif title and publish_date:
        key = f"{title}|{publish_date}|{content}"
    # 最后使用标题+内容摘要
    elif title:
        key = f"{title}|{content}"
    # 最坏情况使用内容哈希
    else:
        # 使用内容的MD5哈希作为唯一标识
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        key = content_hash
    
    return key

# 处理单个JSON对象
def process_json_object(obj):
    global total_articles, duplicate_articles
    
    articles = []
    # 检查是否是包含results字段的对象
    if isinstance(obj, dict) and 'results' in obj:
        results = obj['results']
        if isinstance(results, list):
            articles = results
    # 检查是否直接是文章对象
    elif isinstance(obj, dict):
        articles = [obj]
    
    # 处理每篇文章
    for article in articles:
        total_articles += 1
        # 生成唯一标识
        unique_key = generate_unique_key(article)
        if unique_key not in unique_articles:
            unique_articles[unique_key] = article
        else:
            duplicate_articles += 1

# 处理单个文件
def process_file(file_path):
    global total_files, successful_files, error_files
    total_files += 1
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # 检查是否是空文件
        if not content:
            return
        
        # 尝试作为完整JSON解析
        try:
            data = json.loads(content)
            # 处理JSON数组
            if isinstance(data, list):
                for item in data:
                    process_json_object(item)
            # 处理单个JSON对象
            elif isinstance(data, dict):
                process_json_object(data)
            successful_files += 1
        
        # 作为NDJSON处理（每行一个JSON对象）
        except json.JSONDecodeError:
            # 按行处理
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        obj = json.loads(line)
                        process_json_object(obj)
                    except json.JSONDecodeError:
                        continue
            successful_files += 1
    
    except Exception as e:
        error_files += 1
        print(f"处理文件 {file_path} 时出错: {e}")

# 获取所有JSON文件
print("正在查找所有JSON文件...")
json_files = glob.glob(os.path.join(data_dir, "**", "*.json"), recursive=True)
print(f"找到 {len(json_files)} 个JSON文件")

# 处理所有文件
for i, file_path in enumerate(json_files):
    process_file(file_path)
    
    # 每处理100个文件打印一次进度
    if (i + 1) % 100 == 0:
        print(f"已处理 {i + 1}/{len(json_files)} 个文件，成功 {successful_files} 个，失败 {error_files} 个")
        print(f"累计文章 {total_articles} 篇，重复文章 {duplicate_articles} 篇")

# 保存去重后的文章
unique_articles_list = list(unique_articles.values())
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(unique_articles_list, f, ensure_ascii=False, indent=2)

print(f"\n处理完成！")
print(f"总文件数: {total_files}")
print(f"成功处理文件数: {successful_files}")
print(f"处理失败文件数: {error_files}")
print(f"总文章数: {total_articles}")
print(f"重复文章数: {duplicate_articles}")
print(f"唯一文章数: {len(unique_articles_list)}")
print(f"输出文件: {output_file}")