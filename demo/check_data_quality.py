import pandas as pd

# 读取原始数据
data_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv'
df = pd.read_csv(data_path, low_memory=False)

print(f"原始数据大小: {len(df)} 行, {len(df.columns)} 列")
print()

# 查看关键变量的缺失情况
key_vars = [
    'development_demand_pca',
    'normalized_sentiment',
    'cooperation_willingness_advanced',
    'time_index',
    'total_words_count',
    'source_region_5',
    'category',
    'china_africa_community_recognition'
]

print("关键变量缺失情况:")
missing_counts = df[key_vars].isnull().sum()
missing_percentages = (missing_counts / len(df)) * 100
missing_df = pd.DataFrame({
    '缺失数量': missing_counts,
    '缺失比例(%)': missing_percentages.round(2)
})
print(missing_df)
print()

# 查看文本内容相关列
text_cols = [col for col in df.columns if 'text' in col.lower() or 'title' in col.lower() or 'summary' in col.lower()]
print("文本相关列:")
print(text_cols)
print()

# 查看前几行文本内容
if len(text_cols) > 0:
    print("前5行文本内容预览:")
    print(df[text_cols[:3]].head())
