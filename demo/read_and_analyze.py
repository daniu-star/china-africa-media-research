import pandas as pd
import numpy as np

# 文件路径
fixed_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception_fixed.csv'
original_coop_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_complete_cooperation_depth.csv'

print("=== 数据结构和字段匹配关系分析 ===")

# 读取固定文件
print("\n1. 读取固定文件...")
fixed_df = pd.read_csv(fixed_file, low_memory=False)
print(f"   固定文件记录数: {len(fixed_df)}")
print(f"   固定文件字段数: {len(fixed_df.columns)}")

# 读取原始合作纵深性文件
print("\n2. 读取原始合作纵深性文件...")
original_coop_df = pd.read_csv(original_coop_file, low_memory=False)
print(f"   原始合作纵深性文件记录数: {len(original_coop_df)}")
print(f"   原始合作纵深性文件字段数: {len(original_coop_df.columns)}")

# 提取合作纵深性相关字段
coop_fields = ['long_term_word_count', 'has_multi_agent_interaction', 
               'long_term_word_count_log', 'long_term_percentile', 
               'multi_agent_percentile', 'cooperation_depth_index',
               'long_term_word_count_scaled', 'has_multi_agent_interaction_scaled']

print("\n3. 合作纵深性相关字段:")
for field in coop_fields:
    if field in original_coop_df.columns:
        print(f"   - {field}: 存在于原始合作纵深性文件中")

# 检查可能的匹配字段
print("\n4. 可能的匹配字段分析:")
possible_match_fields = ['title', 'date', 'combined_text', 'url', 'processed_text']
for field in possible_match_fields:
    if field in fixed_df.columns and field in original_coop_df.columns:
        fixed_unique = fixed_df[field].nunique()
        original_unique = original_coop_df[field].nunique()
        print(f"   - {field}: 固定文件唯一值={fixed_unique}, 原始文件唯一值={original_unique}")
    elif field in fixed_df.columns:
        print(f"   - {field}: 仅存在于固定文件中")
    elif field in original_coop_df.columns:
        print(f"   - {field}: 仅存在于原始文件中")

# 检查固定文件中的关键研究字段
print("\n5. 固定文件关键研究字段:")
key_research_fields = [
    'china_africa_community_recognition',
    'development_demand_perception',
    'community_similarity',
    'sentiment_label',
    'normalized_sentiment'
]
for field in key_research_fields:
    if field in fixed_df.columns:
        print(f"   - {field}: 存在, 非空值数={fixed_df[field].notnull().sum()}")

# 创建匹配键
print("\n6. 创建匹配键...")
# 为两个文件创建匹配键：title + date + combined_text前50字符
for df in [fixed_df, original_coop_df]:
    df['title'] = df['title'].fillna('')
    df['date'] = df['date'].fillna('')
    df['combined_text'] = df['combined_text'].fillna('')
    df['match_key'] = df['title'].str[:100] + '_' + df['date'] + '_' + df['combined_text'].str[:100]

print(f"\n7. 匹配键唯一性检查:")
print(f"   - 固定文件匹配键唯一值: {fixed_df['match_key'].nunique()}")
print(f"   - 原始文件匹配键唯一值: {original_coop_df['match_key'].nunique()}")

# 检查匹配键的重叠情况
print(f"\n8. 匹配键重叠情况:")
fixed_match_keys = set(fixed_df['match_key'])
original_match_keys = set(original_coop_df['match_key'])
overlap_keys = fixed_match_keys & original_match_keys
print(f"   - 固定文件匹配键数: {len(fixed_match_keys)}")
print(f"   - 原始文件匹配键数: {len(original_match_keys)}")
print(f"   - 重叠匹配键数: {len(overlap_keys)}")
print(f"   - 重叠比例: {len(overlap_keys)/len(original_match_keys)*100:.2f}%")

# 保存分析结果
with open('data_analysis_results.txt', 'w', encoding='utf-8') as f:
    f.write("=== 数据结构和字段匹配关系分析结果 ===\n\n")
    f.write("1. 文件基本信息:\n")
    f.write(f"   - 固定文件: 记录数={len(fixed_df)}, 字段数={len(fixed_df.columns)}\n")
    f.write(f"   - 原始合作纵深性文件: 记录数={len(original_coop_df)}, 字段数={len(original_coop_df.columns)}\n\n")
    
    f.write("2. 合作纵深性相关字段:\n")
    for field in coop_fields:
        if field in original_coop_df.columns:
            f.write(f"   - {field}: 存在\n")
    
    f.write("\n3. 匹配键分析:\n")
    f.write(f"   - 固定文件匹配键唯一值: {fixed_df['match_key'].nunique()}\n")
    f.write(f"   - 原始文件匹配键唯一值: {original_coop_df['match_key'].nunique()}\n")
    f.write(f"   - 重叠匹配键数: {len(overlap_keys)}\n")
    f.write(f"   - 重叠比例: {len(overlap_keys)/len(original_match_keys)*100:.2f}%\n")

print(f"\n9. 分析结果已保存到 data_analysis_results.txt")
print("\n=== 分析完成 ===")