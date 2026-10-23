import pandas as pd
import numpy as np
import re

# 文件路径
fixed_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception_fixed.csv'
original_coop_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_complete_cooperation_depth.csv'

print("=== 数据匹配和融合 ===")

# 读取固定文件
print("\n1. 读取固定文件...")
fixed_df = pd.read_csv(fixed_file, low_memory=False)
print(f"   固定文件记录数: {len(fixed_df)}")

# 读取原始合作纵深性文件
print("\n2. 读取原始合作纵深性文件...")
original_coop_df = pd.read_csv(original_coop_file, low_memory=False)
print(f"   原始合作纵深性文件记录数: {len(original_coop_df)}")

# 提取合作纵深性相关字段
coop_fields = ['long_term_word_count', 'has_multi_agent_interaction', 
               'long_term_word_count_log', 'long_term_percentile', 
               'multi_agent_percentile', 'cooperation_depth_index',
               'long_term_word_count_scaled', 'has_multi_agent_interaction_scaled']

# 预处理title字段用于匹配
print("\n3. 预处理title字段用于匹配...")
def preprocess_title(title):
    if pd.isnull(title):
        return ''
    # 转换为小写
    title = title.lower()
    # 去除特殊字符，只保留字母、数字和空格
    title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
    # 标准化空格
    title = re.sub(r'\s+', ' ', title).strip()
    return title

# 应用预处理
fixed_df['processed_title'] = fixed_df['title'].apply(preprocess_title)
original_coop_df['processed_title'] = original_coop_df['title'].apply(preprocess_title)

# 检查预处理后的title重叠情况
fixed_processed_titles = set(fixed_df['processed_title'])
original_processed_titles = set(original_coop_df['processed_title'])
overlap_titles = fixed_processed_titles & original_processed_titles
print(f"   - 固定文件处理后title数: {len(fixed_processed_titles)}")
print(f"   - 原始文件处理后title数: {len(original_processed_titles)}")
print(f"   - 重叠title数: {len(overlap_titles)}")
print(f"   - 重叠比例: {len(overlap_titles)/len(original_processed_titles)*100:.2f}%")

# 执行数据匹配和融合
print("\n4. 执行数据匹配和融合...")

# 首先，创建一个包含所有合作纵深性字段的原始数据子集
coop_df = original_coop_df[['processed_title'] + coop_fields].copy()

# 使用processed_title进行左连接
merged_df = pd.merge(fixed_df, coop_df, on='processed_title', how='left')

# 检查融合结果
print(f"\n5. 融合结果检查:")
print(f"   - 融合后记录数: {len(merged_df)}")

# 统计匹配到的记录数
matched_count = merged_df['cooperation_depth_index'].notnull().sum()
unmatched_count = len(merged_df) - matched_count
print(f"   - 匹配到的记录数: {matched_count}")
print(f"   - 未匹配到的记录数: {unmatched_count}")
print(f"   - 匹配率: {matched_count/len(merged_df)*100:.2f}%")

# 检查合作纵深性字段的融合情况
print("\n6. 合作纵深性字段融合情况:")
for field in coop_fields:
    non_null_count = merged_df[field].notnull().sum()
    print(f"   - {field}: 融合后非空值数 = {non_null_count}")

# 保存中间结果
merged_df.to_csv('c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/merged_data_with_cooperation_depth.csv', index=False, encoding='utf-8-sig')
print(f"\n7. 中间结果已保存到 merged_data_with_cooperation_depth.csv")

print(f"\n=== 数据匹配和融合完成 ===")
print(f"✅ 匹配到 {matched_count} 条记录")
print(f"✅ 未匹配到 {unmatched_count} 条记录，需要进行预测")
