import pandas as pd
import numpy as np

# 读取数据
data_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception.csv'
df = pd.read_csv(data_path, encoding='utf-8')

print("=== 发展需求感知深度分析报告 ===")
print(f"数据总量: {len(df)} 条记录")
print()

# 1. 发展需求感知强度的基本统计特征
print("1. 发展需求感知强度基本统计特征")
print(df['development_demand_perception'].describe())
print()

# 2. 关键词检测情况
print("2. 关键词检测情况")
has_keywords = df['development_keyword_count'] > 0
print(f"检测到关键词的记录数: {has_keywords.sum()} ({has_keywords.sum()/len(df)*100:.2f}%)")
print(f"未检测到关键词的记录数: {len(df) - has_keywords.sum()} ({(len(df)-has_keywords.sum())/len(df)*100:.2f}%)")
print()

# 3. 关键词数量分布
print("3. 关键词数量分布")
print(df['development_keyword_count'].value_counts().sort_index())
print()

# 4. 局部情感值分布
print("4. 局部情感值分布")
print(df['local_sentiment'].describe())
print()

# 5. 关键词密度分布
print("5. 关键词密度分布")
print(df['development_keyword_density'].describe())
print()

# 6. 发展需求感知强度的分位数
print("6. 发展需求感知强度分位数")
print(df['development_demand_perception'].quantile([0.1, 0.25, 0.5, 0.75, 0.9]))
print()

# 7. 相关性分析
print("7. 相关性分析")
corr_matrix = df[['development_keyword_count', 'development_keyword_density', 'local_sentiment', 'development_demand_perception']].corr()
print(corr_matrix)
print()

# 8. 发展需求感知强度的分布区间
print("8. 发展需求感知强度分布区间")
bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
labels = ['0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0']
df['demand_interval'] = pd.cut(df['development_demand_perception'], bins=bins, labels=labels, include_lowest=True)
interval_counts = df['demand_interval'].value_counts().sort_index()
print(interval_counts)
print(f"各区间占比:")
print(interval_counts / len(df) * 100)
