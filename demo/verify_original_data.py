import pandas as pd
import numpy as np

# 读取原始文件
original_df = pd.read_csv('c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception.csv', low_memory=False)
print("=== 原始文件合作纵深性指数验证 ===")
print(f"总记录数: {len(original_df)}")

# 1. 检查合作纵深性相关字段的完整性
print(f"\n1. 合作纵深性相关字段完整性:")
coop_fields = ['long_term_word_count', 'has_multi_agent_interaction', 
               'long_term_word_count_log', 'long_term_percentile', 
               'multi_agent_percentile', 'cooperation_depth_index']
all_complete = True
for field in coop_fields:
    non_null_count = original_df[field].notnull().sum()
    complete = non_null_count == len(original_df)
    print(f"   - {field}: {non_null_count}/{len(original_df)} ({'完整' if complete else '不完整'})")
    if not complete:
        all_complete = False

if all_complete:
    print(f"\n   ✅ 所有合作纵深性相关字段都完整")
else:
    print(f"\n   ❌ 部分合作纵深性相关字段不完整")

# 2. 检查合作纵深性指数的分布情况
print(f"\n2. 合作纵深性指数分布:")
coop_depth = original_df['cooperation_depth_index']
print(f"   - 平均值: {coop_depth.mean():.4f}")
print(f"   - 中位数: {coop_depth.median():.4f}")
print(f"   - 标准差: {coop_depth.std():.4f}")
print(f"   - 最小值: {coop_depth.min():.4f}")
print(f"   - 最大值: {coop_depth.max():.4f}")

# 3. 检查指数值是否在合理范围内（0-1之间）
print(f"\n3. 合作纵深性指数范围验证:")
valid_range_count = ((coop_depth >= 0) & (coop_depth <= 1)).sum()
print(f"   - 有效范围值(0-1): {valid_range_count}/{len(original_df)} ({(valid_range_count/len(original_df)*100):.1f}%)")
if valid_range_count == len(original_df):
    print(f"   ✅ 所有合作纵深性指数都在合理范围内(0-1)")
else:
    print(f"   ❌ 部分合作纵深性指数超出合理范围(0-1)")

# 4. 验证指数计算的正确性
print(f"\n4. 合作纵深性指数计算验证:")
# 计算预期的合作纵深性指数
calculated_coop = (original_df['long_term_percentile'] + original_df['multi_agent_percentile']) / 200
# 检查计算结果与实际结果的一致性
consistent_count = np.isclose(original_df['cooperation_depth_index'], calculated_coop).sum()
print(f"   - 计算一致性: {consistent_count}/{len(original_df)} ({(consistent_count/len(original_df)*100):.1f}%)")
if consistent_count == len(original_df):
    print(f"   ✅ 所有合作纵深性指数计算正确")
else:
    print(f"   ❌ 部分合作纵深性指数计算可能存在问题")

# 5. 检查long_term_word_count_log的计算正确性
print(f"\n5. long_term_word_count_log计算验证:")
calculated_log = np.log1p(original_df['long_term_word_count'])
consistent_count = np.isclose(original_df['long_term_word_count_log'], calculated_log).sum()
print(f"   - 计算一致性: {consistent_count}/{len(original_df)} ({(consistent_count/len(original_df)*100):.1f}%)")
if consistent_count == len(original_df):
    print(f"   ✅ 所有long_term_word_count_log计算正确")
else:
    print(f"   ❌ 部分long_term_word_count_log计算可能存在问题")

# 6. 检查是否存在重复记录
print(f"\n6. 重复记录检查:")
# 使用URL或title+date作为唯一标识符
if 'url' in original_df.columns:
    duplicate_urls = original_df[original_df.duplicated('url')]['url'].unique()
    print(f"   - 基于URL的重复记录数: {len(duplicate_urls)}")
else:
    print(f"   - URL字段不存在，跳过基于URL的重复检查")

# 7. 输出验证总结
print(f"\n=== 验证总结 ===")
if all_complete and valid_range_count == len(original_df) and consistent_count == len(original_df):
    print("✅ 原始文件合作纵深性指数验证通过，所有记录都有完整、正确的合作纵深性指数")
    print("   总记录数: 19,435")
    print("   所有记录都包含完整的合作纵深性指数")
    print("   所有指数值都在合理范围内(0-1)")
    print("   所有指数计算正确")
else:
    print("❌ 原始文件合作纵深性指数验证未完全通过")
    print(f"   总记录数: 19,435")
    print(f"   字段完整性: {'通过' if all_complete else '未通过'}")
    print(f"   指数范围: {'通过' if valid_range_count == len(original_df) else '未通过'}")
    print(f"   计算正确性: {'通过' if consistent_count == len(original_df) else '未通过'}")

# 保存验证结果到文件
with open('original_data_verification_results.txt', 'w', encoding='utf-8') as f:
    f.write("=== 原始文件合作纵深性指数验证结果 ===\n")
    f.write(f"总记录数: {len(original_df)}\n\n")
    
    f.write("1. 合作纵深性相关字段完整性:\n")
    for field in coop_fields:
        non_null_count = original_df[field].notnull().sum()
        complete = non_null_count == len(original_df)
        f.write(f"   - {field}: {non_null_count}/{len(original_df)} ({'完整' if complete else '不完整'})\n")
    
    f.write(f"\n2. 合作纵深性指数分布:\n")
    f.write(f"   - 平均值: {coop_depth.mean():.4f}\n")
    f.write(f"   - 中位数: {coop_depth.median():.4f}\n")
    f.write(f"   - 标准差: {coop_depth.std():.4f}\n")
    f.write(f"   - 最小值: {coop_depth.min():.4f}\n")
    f.write(f"   - 最大值: {coop_depth.max():.4f}\n")
    
    f.write(f"\n3. 合作纵深性指数范围验证:\n")
    f.write(f"   - 有效范围值(0-1): {valid_range_count}/{len(original_df)} ({(valid_range_count/len(original_df)*100):.1f}%)\n")
    
    f.write(f"\n4. 合作纵深性指数计算验证:\n")
    f.write(f"   - 计算一致性: {consistent_count}/{len(original_df)} ({(consistent_count/len(original_df)*100):.1f}%)\n")
    
    f.write(f"\n=== 验证总结 ===\n")
    if all_complete and valid_range_count == len(original_df) and consistent_count == len(original_df):
        f.write("✅ 原始文件合作纵深性指数验证通过，所有记录都有完整、正确的合作纵深性指数\n")
    else:
        f.write("❌ 原始文件合作纵深性指数验证未完全通过\n")

print(f"\n验证结果已保存到 original_data_verification_results.txt")