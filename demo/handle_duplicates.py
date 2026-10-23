import pandas as pd
import numpy as np

# 文件路径
merged_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/merged_data_with_cooperation_depth.csv'

print("=== 处理重复匹配 ===")

# 读取融合后的数据
print("\n1. 读取融合后的数据...")
merged_df = pd.read_csv(merged_file, low_memory=False)
print(f"   融合后记录数: {len(merged_df)}")

# 检查原始固定文件记录数对应的merged_df记录数
print("\n2. 检查原始固定文件记录数对应的merged_df记录数...")
# 通过original_index分组，计算每个original_index对应的记录数
grouped = merged_df.groupby('original_index').size().reset_index(name='count')
print(f"   - 唯一original_index数: {len(grouped)}")
print(f"   - 平均每个original_index对应的记录数: {grouped['count'].mean():.2f}")
print(f"   - 最多记录数: {grouped['count'].max()}")
print(f"   - 最少记录数: {grouped['count'].min()}")

# 处理重复匹配：为每个original_index保留一条记录
print("\n3. 处理重复匹配...")
# 去重策略：对于每个original_index，保留第一条记录
unique_merged_df = merged_df.drop_duplicates(subset=['original_index'], keep='first')
print(f"   - 去重后记录数: {len(unique_merged_df)}")
print(f"   - 去重前记录数: {len(merged_df)}")
print(f"   - 去重比例: {(1 - len(unique_merged_df)/len(merged_df))*100:.2f}%")

# 检查去重后的匹配情况
print("\n4. 检查去重后的匹配情况...")
matched_count = unique_merged_df['cooperation_depth_index'].notnull().sum()
unmatched_count = len(unique_merged_df) - matched_count
print(f"   - 匹配到的记录数: {matched_count}")
print(f"   - 未匹配到的记录数: {unmatched_count}")
print(f"   - 匹配率: {matched_count/len(unique_merged_df)*100:.2f}%")

# 检查合作纵深性字段的完整性
print("\n5. 合作纵深性字段完整性检查:")
coop_fields = ['long_term_word_count', 'has_multi_agent_interaction', 
               'long_term_word_count_log', 'long_term_percentile', 
               'multi_agent_percentile', 'cooperation_depth_index']
for field in coop_fields:
    non_null_count = unique_merged_df[field].notnull().sum()
    print(f"   - {field}: 非空值数 = {non_null_count}")

# 保存去重后的结果
print("\n6. 保存去重后的结果...")
unique_merged_df.to_csv('c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/unique_merged_data.csv', index=False, encoding='utf-8-sig')
print(f"   - 保存路径: unique_merged_data.csv")

print(f"\n=== 处理完成 ===")
print(f"✅ 去重后记录数: {len(unique_merged_df)}")
print(f"✅ 匹配到 {matched_count} 条记录")
print(f"✅ 未匹配到 {unmatched_count} 条记录，需要进行预测")
