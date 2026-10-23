import os
import pandas as pd

# 文件路径
file_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception_fixed.csv'

print("=== 固定文件信息检查 ===")

# 检查文件是否存在
if not os.path.exists(file_path):
    print("❌ 文件不存在")
    exit(1)

# 检查文件大小
file_size = os.path.getsize(file_path)
print(f"1. 文件大小: {file_size / (1024*1024):.2f} MB")
print(f"   换算为GB: {file_size / (1024*1024*1024):.2f} GB")

# 读取文件
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

# 列出所有字段（前20个）
print("\n4. 字段列表 (前20个):")
for i, col in enumerate(df.columns[:20]):
    print(f"   {i+1}: {col}")

if len(df.columns) > 20:
    print(f"   ... 还有 {len(df.columns) - 20} 个字段")

# 查看前3行数据概览
print("\n5. 数据概览 (前3行):")
print(df.head(3))

print("\n=== 检查完成 ===")