import json
import pandas as pd
import os

print('=== 数据记录数检查 ===')

# 检查CSV文件
csv_path = 'c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\清洗数据\\enhanced_data_with_demand_perception.csv'
df = pd.read_csv(csv_path, low_memory=False)
print('CSV文件记录数:', len(df))

# 检查JSON文件
def check_json_records(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            return len(data.get('data', [])) if 'data' in data else 1
        else:
            return 1
    except Exception as e:
        print(f'Error reading {os.path.basename(file_path)}: {e}')
        return 0

json_files = [
    'c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\清洗数据\\原始数据.json',
    'c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\清洗数据\\清洗数据.json',
    'c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\清洗数据\\高级遍历数据.json'
]

for file in json_files:
    records = check_json_records(file)
    print(f'{os.path.basename(file)}: {records} 条记录')

# 检查处理报告
try:
    with open('c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\清洗数据\\遍历处理报告.json', 'r', encoding='utf-8') as f:
        report = json.load(f)
    print('\n=== 遍历处理报告 ===')
    for key, value in report.items():
        print(f'{key}: {value}')
except Exception as e:
    print(f'Error reading 遍历处理报告.json: {e}')
