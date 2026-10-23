import pandas as pd
import numpy as np

# 读取临时文件的更多记录（前1000行）
temp_df = pd.read_csv('c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/temp_enhanced_data.csv', nrows=1000, low_memory=False)
print("=== 临时文件详细分析（前1000行） ===")
print(f"记录数: {len(temp_df)}")

# 检查关键字段的非空值分布
print(f"\n关键字段非空值分布:")
key_fields = ['title', 'summary', 'date', 'url', 'content', 'combined_text', 'processed_text']
for field in key_fields:
    non_null_count = temp_df[field].notnull().sum()
    non_null_percent = (non_null_count / len(temp_df)) * 100
    print(f"  - {field}: {non_null_count} 条非空值 ({non_null_percent:.1f}%)")

# 查看combined_text字段的内容
print(f"\ncombined_text字段分析:")
combined_text_non_null = temp_df[temp_df['combined_text'].notnull()]
if len(combined_text_non_null) > 0:
    # 查看combined_text的长度分布
    temp_df['combined_text_length'] = temp_df['combined_text'].str.len()
    print(f"  - 平均长度: {temp_df['combined_text_length'].mean():.0f} 字符")
    print(f"  - 最大长度: {temp_df['combined_text_length'].max()} 字符")
    print(f"  - 最小长度: {temp_df['combined_text_length'].min()} 字符")
    
    # 查看几个示例
    print(f"\n  示例内容:")
    for i, text in enumerate(combined_text_non_null['combined_text'].head(3)):
        print(f"    示例 {i+1}: {text[:100]}...")

# 检查临时文件是否有合作纵深性相关字段
print(f"\n合作纵深性相关字段检查:")
coop_fields = ['long_term_word_count', 'has_multi_agent_interaction', 'cooperation_depth_index']
for field in coop_fields:
    if field in temp_df.columns:
        print(f"  - {field}: 存在")
    else:
        print(f"  - {field}: 不存在")

# 保存详细分析结果
detailed_analysis = {
    'total_records': len(temp_df),
    'non_null_distribution': {field: temp_df[field].notnull().sum() for field in key_fields},
    'combined_text_stats': {
        'mean_length': temp_df['combined_text_length'].mean(),
        'max_length': temp_df['combined_text_length'].max(),
        'min_length': temp_df['combined_text_length'].min()
    }
}

with open('temp_file_detailed_analysis.txt', 'w', encoding='utf-8') as f:
    f.write("=== 临时文件详细分析结果 ===\n")
    f.write(f"分析记录数: {detailed_analysis['total_records']}\n\n")
    
    f.write("关键字段非空值分布:\n")
    for field, count in detailed_analysis['non_null_distribution'].items():
        percent = (count / detailed_analysis['total_records']) * 100
        f.write(f"  - {field}: {count} ({percent:.1f}%)\n")
    
    f.write("\ncombined_text字段统计:\n")
    f.write(f"  - 平均长度: {detailed_analysis['combined_text_stats']['mean_length']:.0f} 字符\n")
    f.write(f"  - 最大长度: {detailed_analysis['combined_text_stats']['max_length']} 字符\n")
    f.write(f"  - 最小长度: {detailed_analysis['combined_text_stats']['min_length']} 字符\n")

print("\n详细分析结果已保存到 temp_file_detailed_analysis.txt")