import json
import os

print('=== 分析results_0.json.backup文件结构 ===')

data_dir = 'c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\data'
results_file = os.path.join(data_dir, 'results_0.json.backup')

# 读取原始文件
with open(results_file, 'r', encoding='utf-8') as f:
    content = f.read()

print('文件总大小:', len(content), '字符')

# 手动统计文章数量
print('手动统计文章数量:')
article_count = content.count('{"title":')
print('通过标题字段统计的文章数量:', article_count)

# 检查URL数量
url_count = content.count('"url":')
print('通过URL字段统计的数量:', url_count)

# 检查文件是否包含多个JSON对象
print('多JSON对象检查:')

# 查找所有可能的JSON对象开始位置
json_starts = []
pos = 0
while pos < len(content):
    next_pos = content.find('{', pos)
    if next_pos == -1:
        break
    json_starts.append(next_pos)
    pos = next_pos + 1

print('找到', len(json_starts), '个可能的JSON对象开始位置')

# 检查前3个开始位置
for i, start_pos in enumerate(json_starts[:3]):
    print('检查第' + str(i+1) + '个开始位置 ' + str(start_pos) + ':')
    
    # 尝试解析从这个位置开始的内容
    try:
        test_content = content[start_pos:]
        data = json.loads(test_content)
        print('  解析成功，包含有效JSON数据')
        if 'articles' in data:
            print('  包含articles字段，文章数量:', len(data['articles']))
    except Exception as e:
        print('  解析失败:', str(e)[:100])