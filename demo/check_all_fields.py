import pandas as pd

# 文件路径
fixed_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception_fixed.csv'
original_coop_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_complete_cooperation_depth.csv'

print("=== 固定文件所有字段检查 ===")

# 读取固定文件
fixed_df = pd.read_csv(fixed_file, low_memory=False)
print(f"固定文件记录数: {len(fixed_df)}")
print(f"固定文件字段数: {len(fixed_df.columns)}")

# 列出所有字段
print("\n1. 固定文件所有字段:")
for i, col in enumerate(fixed_df.columns):
    print(f"   {i+1:2d}: {col}")

# 查看所有字段的详细信息
print("\n2. 字段详细信息:")
for col in fixed_df.columns:
    dtype = fixed_df[col].dtype
    non_null_count = fixed_df[col].notnull().sum()
    null_count = len(fixed_df) - non_null_count
    unique_count = fixed_df[col].nunique()
    
    # 查看数值字段的统计信息
    if pd.api.types.is_numeric_dtype(dtype):
        min_val = fixed_df[col].min()
        max_val = fixed_df[col].max()
        mean_val = fixed_df[col].mean()
        std_val = fixed_df[col].std()
        print(f"   - {col} (数值): 非空={non_null_count}, 唯一={unique_count}, 最小值={min_val:.4f}, 最大值={max_val:.4f}, 平均值={mean_val:.4f}, 标准差={std_val:.4f}")
    else:
        # 查看文本字段的统计信息
        sample = fixed_df[col].dropna().head(1).values[0] if non_null_count > 0 else ""
        print(f"   - {col} (文本): 非空={non_null_count}, 唯一={unique_count}, 示例='{sample[:30]}...'"
    )

# 检查原始合作纵深性文件的字段
print("\n3. 原始合作纵深性文件关键字段:")
original_coop_df = pd.read_csv(original_coop_file, low_memory=False)
coop_fields = ['long_term_word_count', 'has_multi_agent_interaction', 
               'long_term_word_count_log', 'long_term_percentile', 
               'multi_agent_percentile', 'cooperation_depth_index']
for field in coop_fields:
    if field in original_coop_df.columns:
        print(f"   - {field}: 存在")

# 分析可能对应的字段
print("\n4. 可能对应的概念字段:")
print("   中非命运共同体认同度相关字段可能:")
for col in fixed_df.columns:
    if any(keyword in col.lower() for keyword in ['sentiment', 'community', '认同', 'perception', 'attitude', 'opinion']):
        print(f"     - {col}")

print("   发展需求感知相关字段可能:")
for col in fixed_df.columns:
    if any(keyword in col.lower() for keyword in ['development', 'demand', 'perception', '需求', '发展', '需求感知', 'development_demand']):
        print(f"     - {col}")

print("   议题集中度相关字段可能:")
for col in fixed_df.columns:
    if any(keyword in col.lower() for keyword in ['concentration', 'issue', 'topic', '议题', '集中度', 'community', 'community_similarity']):
        print(f"     - {col}")

# 查看原始合作纵深性文件的URL字段，用于匹配
print("\n5. 检查URL字段用于匹配:")
if 'url' in original_coop_df.columns and 'url' in fixed_df.columns:
    print(f"   原始合作纵深性文件URL数: {original_coop_df['url'].nunique()}")
    print(f"   固定文件URL数: {fixed_df['url'].nunique()}")
else:
    print(f"   检查其他可能的匹配字段:")
    possible_match_fields = ['title', 'date', 'title_date', 'combined_text', 'original_index']
    for field in possible_match_fields:
        if field in original_coop_df.columns and field in fixed_df.columns:
            print(f"     - {field}: 原始文件唯一值={original_coop_df[field].nunique()}, 固定文件唯一值={fixed_df[field].nunique()}")
