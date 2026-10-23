import pandas as pd
import numpy as np

# 读取原始文件（完整）
original_df = pd.read_csv('c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception.csv', low_memory=False)
print("=== 原始文件分析 ===")
print(f"记录数: {len(original_df)}")
print(f"字段数: {len(original_df.columns)}")
print(f"\n原始文件字段列表:")
for col in original_df.columns:
    print(f"  - {col}")

# 查看原始文件的合作纵深性指数相关字段
print(f"\n合作纵深性指数相关字段:")
coop_fields = ['long_term_word_count', 'has_multi_agent_interaction', 
               'long_term_word_count_log', 'long_term_percentile', 
               'multi_agent_percentile', 'cooperation_depth_index']
for field in coop_fields:
    if field in original_df.columns:
        print(f"  - {field}: 非空值数 = {original_df[field].notnull().sum()}")

# 读取临时文件（前100行）
temp_df = pd.read_csv('c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/temp_enhanced_data.csv', nrows=100, low_memory=False)
print("\n=== 临时文件分析（前100行） ===")
print(f"记录数（样本）: {len(temp_df)}")
print(f"字段数: {len(temp_df.columns)}")
print(f"\n临时文件字段列表:")
for col in temp_df.columns:
    print(f"  - {col}")

# 查看临时文件的关键字段
print(f"\n临时文件关键字段示例:")
key_fields = ['title', 'summary', 'date', 'url', 'content', 'combined_text', 'processed_text']
for field in key_fields:
    if field in temp_df.columns:
        print(f"  - {field}: 非空值数 = {temp_df[field].notnull().sum()}")
        if temp_df[field].notnull().sum() > 0:
            print(f"    示例: {temp_df[field].iloc[0][:50]}...")

# 检查两个文件的共同字段
common_fields = list(set(original_df.columns) & set(temp_df.columns))
print(f"\n=== 共同字段 ===")
print(f"共有 {len(common_fields)} 个共同字段:")
for field in common_fields:
    print(f"  - {field}")

# 保存分析结果到文件
with open('data_analysis_results.txt', 'w', encoding='utf-8') as f:
    f.write("=== 原始文件分析 ===\n")
    f.write(f"记录数: {len(original_df)}\n")
    f.write(f"字段数: {len(original_df.columns)}\n")
    f.write(f"\n原始文件字段列表:\n")
    for col in original_df.columns:
        f.write(f"  - {col}\n")
    
    f.write(f"\n=== 临时文件分析 ===\n")
    f.write(f"字段数: {len(temp_df.columns)}\n")
    f.write(f"\n临时文件字段列表:\n")
    for col in temp_df.columns:
        f.write(f"  - {col}\n")
    
    f.write(f"\n=== 共同字段 ===\n")
    f.write(f"共有 {len(common_fields)} 个共同字段:\n")
    for field in common_fields:
        f.write(f"  - {field}\n")

print("\n分析结果已保存到 data_analysis_results.txt")