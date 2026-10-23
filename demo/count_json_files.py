import os

# 源目录
source_dir = r"c:\Users\13067\Desktop\论文\非洲\demo\data\crawler_results"

# 统计JSON文件数量
json_count = 0
gzip_count = 0

for root, dirs, files in os.walk(source_dir):
    for file in files:
        if file.endswith('.json.gz'):
            gzip_count += 1
        elif file.endswith('.json'):
            json_count += 1

print(f"原 gzip 文件数量: {gzip_count}")
print(f"转换后的 JSON 文件数量: {json_count}")
print(f"转换率: {json_count/gzip_count*100:.1f}%" if gzip_count > 0 else "没有找到 gzip 文件")