import pandas as pd
import numpy as np

# 读取数据
df = pd.read_csv(r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv', low_memory=False)

print("1. 数据概览")
print(f"数据集行数: {len(df)}")
print(f"数据集列数: {len(df.columns)}")

# 2. 检查现有变量
print("\n2. 现有变量检查")

# 检查关键变量
key_vars = {
    '因变量': 'china_africa_community_recognition',
    '自变量1': 'source_region_5',
    '自变量2': 'cooperation_willingness_advanced',
    '自变量3': 'development_demand_pca',
    '控制变量1': 'time_index',
    '控制变量2': 'total_words_count',  # 文章字数
    '中介变量': 'normalized_sentiment'
}

for desc, var in key_vars.items():
    if var in df.columns:
        print(f"✅ {desc}: {var} 存在")
        print(f"   缺失值: {df[var].isnull().sum()} ({(df[var].isnull().sum()/len(df)*100):.2f}%)")
        if df[var].dtype != 'object':
            print(f"   均值: {df[var].mean():.4f}")
            print(f"   标准差: {df[var].std():.4f}")
    else:
        print(f"❌ {desc}: {var} 不存在")

# 3. 检查是否需要计算文章字数
print("\n3. 文章字数变量分析")

# 检查total_words_count的描述统计
if 'total_words_count' in df.columns:
    print("total_words_count 描述统计:")
    print(df['total_words_count'].describe())
    
    # 检查是否有其他可能的文本字段
    text_fields = ['title', 'summary', 'cleaned_title', 'cleaned_summary', 'combined_text', 'processed_text']
    for field in text_fields:
        if field in df.columns:
            sample_text = df[field].dropna().iloc[0]
            print(f"\n{field} 样本长度: {len(sample_text)} 字符, {len(sample_text.split())} 单词")

# 4. 计算缺失的变量
print("\n4. 计算缺失变量")

# 检查是否需要计算文章字数
if 'total_words_count' not in df.columns:
    print("正在计算文章字数...")
    df['total_words_count'] = df['combined_text'].str.split().str.len()
    print(f"文章字数计算完成，缺失值: {df['total_words_count'].isnull().sum()}")
else:
    print("total_words_count 已存在，无需计算")

# 检查是否需要计算其他缺失变量
print("\n5. 最终变量确认")
for desc, var in key_vars.items():
    print(f"{desc}: {var} {'存在' if var in df.columns else '不存在'}")

# 6. 保存数据
print("\n6. 保存数据")
df.to_csv(r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv', index=False, encoding='utf-8-sig')
print("数据保存完成")
