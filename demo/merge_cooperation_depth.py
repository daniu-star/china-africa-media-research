import pandas as pd
import numpy as np

# 文件路径
original_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception.csv'
complete_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_complete_cooperation_depth.csv'

print("=== 合作纵深性指数融合处理 ===")

# 读取原始文件
print("\n1. 读取原始文件...")
original_df = pd.read_csv(original_file, low_memory=False)
print(f"   原始文件记录数: {len(original_df)}")
print(f"   原始文件字段数: {len(original_df.columns)}")

# 读取完整指数文件
print("\n2. 读取完整指数文件...")
complete_df = pd.read_csv(complete_file, low_memory=False)
print(f"   完整指数文件记录数: {len(complete_df)}")
print(f"   完整指数文件字段数: {len(complete_df.columns)}")

# 检查原始文件中合作纵深性指数的完整性
print("\n3. 检查原始文件合作纵深性指数完整性...")
coop_fields = ['long_term_word_count', 'has_multi_agent_interaction', 
               'long_term_word_count_log', 'long_term_percentile', 
               'multi_agent_percentile', 'cooperation_depth_index']
for field in coop_fields:
    if field in original_df.columns:
        non_null_count = original_df[field].notnull().sum()
        null_count = len(original_df) - non_null_count
        print(f"   - {field}: 非空值数 = {non_null_count}, 空值数 = {null_count}")

# 确定唯一标识符字段
print("\n4. 确定唯一标识符...")
# 检查URL字段的唯一性
print(f"   - URL唯一性检查: 原始文件 = {original_df['url'].nunique()}/{len(original_df)}, 完整指数文件 = {complete_df['url'].nunique()}/{len(complete_df)}")

# 检查title+date的唯一性
original_df['title_date'] = original_df['title'].fillna('') + '_' + original_df['date'].fillna('')
complete_df['title_date'] = complete_df['title'].fillna('') + '_' + complete_df['date'].fillna('')
print(f"   - title+date唯一性检查: 原始文件 = {original_df['title_date'].nunique()}/{len(original_df)}, 完整指数文件 = {complete_df['title_date'].nunique()}/{len(complete_df)}")

# 使用URL作为唯一标识符，因为title+date可能存在重复
unique_id = 'url'
print(f"   - 选择 {unique_id} 作为唯一标识符")

# 找出原始文件中没有合作纵深性指数的记录
print("\n5. 找出缺少合作纵深性指数的记录...")
# 首先检查原始文件中合作纵深性指数为空的记录
missing_coop = original_df[original_df['cooperation_depth_index'].isnull()]
print(f"   - 原始文件中合作纵深性指数为空的记录数: {len(missing_coop)}")

# 如果所有记录都有指数，检查两个文件的URL差异
if len(missing_coop) == 0:
    print(f"   - 原始文件中所有记录都有合作纵深性指数，检查两个文件的URL差异...")
    # 获取两个文件的URL集合
    original_urls = set(original_df[unique_id])
    complete_urls = set(complete_df[unique_id])
    
    # 找出原始文件中有但完整指数文件中没有的URL
    urls_only_in_original = original_urls - complete_urls
    print(f"   - 仅存在于原始文件中的URL数: {len(urls_only_in_original)}")
    
    # 找出完整指数文件中有但原始文件中没有的URL
    urls_only_in_complete = complete_urls - original_urls
    print(f"   - 仅存在于完整指数文件中的URL数: {len(urls_only_in_complete)}")

# 输出详细信息
print(f"\n6. 详细信息:")
print(f"   - 原始文件总记录数: {len(original_df)}")
print(f"   - 完整指数文件总记录数: {len(complete_df)}")
print(f"   - 两个文件共有的URL数: {len(original_urls & complete_urls)}")

# 保存差异信息
with open('cooperation_depth_merge_info.txt', 'w', encoding='utf-8') as f:
    f.write("=== 合作纵深性指数融合信息 ===\n\n")
    f.write(f"1. 原始文件信息:\n")
    f.write(f"   - 记录数: {len(original_df)}\n")
    f.write(f"   - 字段数: {len(original_df.columns)}\n\n")
    
    f.write(f"2. 完整指数文件信息:\n")
    f.write(f"   - 记录数: {len(complete_df)}\n")
    f.write(f"   - 字段数: {len(complete_df.columns)}\n\n")
    
    f.write(f"3. URL差异:\n")
    f.write(f"   - 仅存在于原始文件中的URL数: {len(urls_only_in_original)}\n")
    f.write(f"   - 仅存在于完整指数文件中的URL数: {len(urls_only_in_complete)}\n")
    f.write(f"   - 两个文件共有的URL数: {len(original_urls & complete_urls)}\n\n")
    
    f.write(f"4. 原始文件合作纵深性指数完整性:\n")
    for field in coop_fields:
        if field in original_df.columns:
            non_null_count = original_df[field].notnull().sum()
            f.write(f"   - {field}: {non_null_count}/{len(original_df)}\n")

print(f"\n7. 处理结果已保存到 cooperation_depth_merge_info.txt")
