import os
import pandas as pd

# 文件路径
file_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception.csv'

print("=== 文件信息检查 ===")

# 检查文件大小
file_size = os.path.getsize(file_path)
print(f"1. 文件大小: {file_size / (1024*1024):.2f} MB")
print(f"   换算为GB: {file_size / (1024*1024*1024):.2f} GB")

# 读取文件前几行，检查字段
print("\n2. 读取文件...")
df = pd.read_csv(file_path, low_memory=False)
print(f"   记录数: {len(df)}")
print(f"   字段数: {len(df.columns)}")

# 检查重要字段
print("\n3. 重要字段检查:")
important_fields = [
    '认同度',
    '发展需求感知', 
    '议题集中度',
    'development_demand_perception',
    'issue_concentration',
    'cooperation_depth_index'
]

for field in important_fields:
    if field in df.columns:
        non_null_count = df[field].notnull().sum()
        null_count = len(df) - non_null_count
        print(f"   - {field}: 存在, 非空值数 = {non_null_count}, 空值数 = {null_count}")
    else:
        print(f"   - {field}: 不存在")

# 列出所有字段
print("\n4. 所有字段列表 (共{}个):".format(len(df.columns)))
for i, col in enumerate(df.columns):
    print(f"   {i+1}: {col}")

print("\n=== 检查完成 ===")