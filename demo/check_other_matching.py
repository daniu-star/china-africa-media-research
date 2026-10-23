import pandas as pd
import numpy as np

# 文件路径
fixed_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception_fixed.csv'
original_coop_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_complete_cooperation_depth.csv'

print("=== 其他匹配方法分析 ===")

# 读取固定文件
print("\n1. 读取固定文件...")
fixed_df = pd.read_csv(fixed_file, low_memory=False)

# 读取原始合作纵深性文件
print("\n2. 读取原始合作纵深性文件...")
original_coop_df = pd.read_csv(original_coop_file, low_memory=False)

# 检查固定文件是否有URL字段
print("\n3. 检查URL字段...")
if 'url' in fixed_df.columns:
    print(f"   - 固定文件URL唯一值: {fixed_df['url'].nunique()}")
    print(f"   - 固定文件URL非空值数: {fixed_df['url'].notnull().sum()}")
else:
    print(f"   - 固定文件没有URL字段")

if 'url' in original_coop_df.columns:
    print(f"   - 原始合作纵深性文件URL唯一值: {original_coop_df['url'].nunique()}")
    print(f"   - 原始合作纵深性文件URL非空值数: {original_coop_df['url'].notnull().sum()}")
else:
    print(f"   - 原始合作纵深性文件没有URL字段")

# 检查original_index字段
print("\n4. 检查original_index字段...")
if 'original_index' in fixed_df.columns:
    print(f"   - 固定文件original_index: 存在")
    print(f"     - 最小值: {fixed_df['original_index'].min()}")
    print(f"     - 最大值: {fixed_df['original_index'].max()}")
    print(f"     - 平均值: {fixed_df['original_index'].mean()}")
else:
    print(f"   - 固定文件没有original_index字段")

# 检查原始合作纵深性文件是否有类似的索引字段
print("\n5. 检查原始合作纵深性文件的索引字段...")
possible_index_fields = ['id', 'original_index', 'index', 'article_index', 'crawl_timestamp']
for field in possible_index_fields:
    if field in original_coop_df.columns:
        print(f"   - {field}: 存在")
        print(f"     - 唯一值: {original_coop_df[field].nunique()}")
        print(f"     - 非空值数: {original_coop_df[field].notnull().sum()}")

# 尝试使用title作为匹配键
print("\n6. 尝试使用title作为匹配键...")
fixed_titles = set(fixed_df['title'].str.lower())
original_titles = set(original_coop_df['title'].str.lower())
overlap_titles = fixed_titles & original_titles
print(f"   - 固定文件title数: {len(fixed_titles)}")
print(f"   - 原始文件title数: {len(original_titles)}")
print(f"   - 重叠title数: {len(overlap_titles)}")
print(f"   - 重叠比例: {len(overlap_titles)/len(original_titles)*100:.2f}%")

# 尝试使用processed_text作为匹配键
print("\n7. 尝试使用processed_text作为匹配键...")
fixed_processed = set(fixed_df['processed_text'].str.lower())
original_processed = set(original_coop_df['processed_text'].str.lower())
overlap_processed = fixed_processed & original_processed
print(f"   - 固定文件processed_text数: {len(fixed_processed)}")
print(f"   - 原始文件processed_text数: {len(original_processed)}")
print(f"   - 重叠processed_text数: {len(overlap_processed)}")
print(f"   - 重叠比例: {len(overlap_processed)/len(original_processed)*100:.2f}%")

# 查看固定文件的前几条记录
print("\n8. 固定文件前3条记录:")
print(fixed_df[['original_index', 'title', 'date', 'combined_text']].head(3))

# 查看原始合作纵深性文件的前几条记录
print("\n9. 原始合作纵深性文件前3条记录:")
print(original_coop_df[['title', 'date', 'combined_text', 'url']].head(3))
