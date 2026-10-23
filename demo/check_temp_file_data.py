import pandas as pd
import numpy as np

# 读取临时文件的不同部分进行检查
print("=== 临时文件数据质量检查 ===")

# 1. 检查前10行
print("\n1. 前10行数据:")
temp_df_head = pd.read_csv('c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/temp_enhanced_data.csv', nrows=10, low_memory=False)
for i in range(min(10, len(temp_df_head))):
    print(f"\n  行 {i+1}:")
    for field in ['title', 'summary', 'date', 'url', 'content', 'combined_text']:
        value = temp_df_head.loc[i, field]
        if pd.isnull(value):
            print(f"    {field}: NULL")
        else:
            print(f"    {field}: '{value}' (长度: {len(str(value))})")

# 2. 检查中间10000-10010行
print("\n2. 中间10000-10010行数据:")
temp_df_mid = pd.read_csv('c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/temp_enhanced_data.csv', 
                           skiprows=10000, nrows=10, low_memory=False)
for i in range(min(10, len(temp_df_mid))):
    print(f"\n  行 {10000+i+1}:")
    for field in ['title', 'summary', 'date', 'url', 'content', 'combined_text']:
        value = temp_df_mid.loc[i, field]
        if pd.isnull(value):
            print(f"    {field}: NULL")
        else:
            print(f"    {field}: '{value}' (长度: {len(str(value))})")

# 3. 检查最后10行
print("\n3. 最后10行数据:")
temp_df_tail = pd.read_csv('c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/temp_enhanced_data.csv', 
                           skiprows=24072, nrows=10, low_memory=False)
for i in range(min(10, len(temp_df_tail))):
    print(f"\n  行 {24072+i+1}:")
    for field in ['title', 'summary', 'date', 'url', 'content', 'combined_text']:
        value = temp_df_tail.loc[i, field]
        if pd.isnull(value):
            print(f"    {field}: NULL")
        else:
            print(f"    {field}: '{value}' (长度: {len(str(value))})")

# 4. 统计整个文件中关键字段的非空值比例
print("\n4. 整个文件关键字段非空值统计:")
# 使用 chunksize 来处理大文件
chunk_size = 10000
total_records = 0
non_null_counts = {}

# 初始化计数器
for field in ['title', 'summary', 'date', 'url', 'content', 'combined_text', 'processed_text']:
    non_null_counts[field] = 0

# 逐块读取并统计
for chunk in pd.read_csv('c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/temp_enhanced_data.csv', 
                         chunksize=chunk_size, low_memory=False):
    total_records += len(chunk)
    for field in non_null_counts.keys():
        if field in chunk.columns:
            non_null_counts[field] += chunk[field].notnull().sum()

# 输出统计结果
print(f"总记录数: {total_records}")
for field, count in non_null_counts.items():
    percent = (count / total_records) * 100 if total_records > 0 else 0
    print(f"  - {field}: {count} 非空值 ({percent:.1f}%)")