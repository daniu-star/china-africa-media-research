import pandas as pd
import numpy as np

# 读取最终文件
file_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_complete_cooperation_depth.csv'
df = pd.read_csv(file_path, low_memory=False)

print("=== 最终文件信息 ===")
print(f"\n1. 数据量:")
print(f"   - 总记录数: {len(df)}")
print(f"   - 总字段数: {len(df.columns)}")

print(f"\n2. 字段列表:")
all_columns = df.columns.tolist()
for i, col in enumerate(all_columns):
    print(f"   {i+1:3d}: {col}")

print(f"\n3. 合作纵深性相关字段:")
coop_fields = ['long_term_word_count', 'has_multi_agent_interaction', 
               'long_term_word_count_log', 'long_term_percentile', 
               'multi_agent_percentile', 'cooperation_depth_index',
               'long_term_word_count_scaled', 'has_multi_agent_interaction_scaled']
for field in coop_fields:
    if field in df.columns:
        print(f"   - {field}: 非空值数 = {df[field].notnull().sum()}")

print(f"\n4. 部分关键字段说明:")
key_field_descriptions = {
    'title': '新闻标题',
    'summary': '新闻摘要',
    'date': '发布日期',
    'category': '新闻类别',
    'source': '新闻来源',
    'url': '新闻URL',
    'content': '新闻内容',
    'word_count': '词数',
    'long_term_word_count': '长期战略词频',
    'has_multi_agent_interaction': '多元主体互动数量',
    'long_term_word_count_log': '长期战略词频对数变换',
    'long_term_percentile': '长期战略词频百分位数',
    'multi_agent_percentile': '多元主体互动百分位数',
    'cooperation_depth_index': '合作纵深性指数',
    'year': '年份',
    'country': '国家'
}
for field, desc in key_field_descriptions.items():
    if field in df.columns:
        print(f"   - {field}: {desc}")