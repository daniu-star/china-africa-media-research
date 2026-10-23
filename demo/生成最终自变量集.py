import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 设置结果目录
result_dir = 'c:/Users/13067/Desktop/论文/非洲/demo/最终自变量集结果'
os.makedirs(result_dir, exist_ok=True)

# 读取包含5个区域分类的数据
df = pd.read_csv(r'c:\Users\13067\Desktop\论文\非洲\demo\最终优化结果\data_with_advanced_willingness.csv')

print("生成最终自变量集")
print("="*50)

# 1. 报道来源地理区域分类
print("1. 报道来源地理区域分类")

# 直接使用已有的五个非洲区域分类（source_region_5列）
df['source_region'] = df['source_region_5']

# 2. 时间变量处理
print("2. 时间变量处理")

df['date'] = pd.to_datetime(df['date'], errors='coerce')
df['time_index'] = df['date'].dt.year.fillna(0).astype(int)

# 3. 合作意愿指标处理（使用高级TF-IDF优化的结果）
print("3. 合作意愿指标处理")

# 直接使用优化后的合作意愿指标
df['cooperation_willingness'] = df['cooperation_willingness_advanced'].fillna(0)

# 4. 发展需求感知强度PCA分析
print("4. 发展需求感知强度PCA分析")

development_features = [
    'development_terms_weight',
    'development_demand_perception',
    'development_keyword_count',
    'development_keyword_density'
]

# 提取发展需求感知相关特征
df_development = df[development_features].dropna()

# 标准化数据
scaler = StandardScaler()
development_scaled = scaler.fit_transform(df_development)

# 主成分分析
pca_development = PCA(n_components=1, random_state=42)
df['development_demand_pca'] = pca_development.fit_transform(development_scaled)

# 5. 生成最终自变量集
print("5. 生成最终自变量集")

# 构建最终自变量集
final_df = df[[
    'time_index',  # 时间
    'cooperation_willingness',  # 优化后的合作意愿
    'development_demand_pca',  # PCA优化后的发展需求感知强度
    'source_region',  # 报道来源区域
    'normalized_sentiment'  # 因变量：标准化情感得分
]].dropna()

# 生成虚拟变量
final_df = pd.get_dummies(final_df, columns=['source_region'], drop_first=True)

# 6. 统计描述
print("\n6. 最终自变量集统计描述")
print(final_df.describe())

# 7. 保存最终自变量集
print("\n7. 保存最终自变量集")

# 保存处理后的数据
final_df.to_csv(os.path.join(result_dir, '最终自变量数据.csv'), index=False, encoding='utf-8-sig')
df.to_csv(os.path.join(result_dir, '包含优化指标的完整数据集.csv'), index=False, encoding='utf-8-sig')

# 8. 生成最终报告
print("\n8. 生成最终报告")

report = f"""# 最终自变量集构建报告

## 1. 数据概览
- 原始数据行数: {len(df)}
- 最终有效数据行数: {len(final_df)}
- 数据缺失率: {((len(df) - len(final_df)) / len(df)) * 100:.2f}%

## 2. 自变量构成

### 2.1 时间变量
- 变量名: `time_index`
- 含义: 文章发布年份
- 处理方法: 从日期字段中提取年份

### 2.2 合作意愿指标
- 变量名: `cooperation_willingness`
- 构建方法: 高级TF-IDF + 余弦相似度
- 种子词库: 60个合作相关的中英文种子词
- 处理方式: 平滑处理 + 非线性转换 + 0-1标准化
- 分布范围: 0-1
- 均值: {df['cooperation_willingness'].mean():.4f}
- 标准差: {df['cooperation_willingness'].std():.4f}

### 2.3 发展需求感知强度
- 变量名: `development_demand_pca`
- 构成指标: `development_terms_weight`, `development_demand_perception`, `development_keyword_count`, `development_keyword_density`
- 构建方法: 主成分分析(PCA)
- 主成分解释方差比: {pca_development.explained_variance_ratio_[0]:.4f}
- 均值: {df['development_demand_pca'].mean():.4f}
- 标准差: {df['development_demand_pca'].std():.4f}

### 2.4 报道来源区域
- 变量名: `source_region`
- 分类方法: 基于网站域名和所属国家的地理位置，分为五个非洲区域
- 分类结果:
{df['source_region'].value_counts().to_string()}

## 3. 最终自变量集

### 3.1 数值型自变量
1. `time_index`: 时间变量（年份）
2. `cooperation_willingness`: 优化后的合作意愿（0-1标准化）
3. `development_demand_pca`: PCA优化后的发展需求感知强度

### 3.2 虚拟变量（报道来源区域）
{', '.join([col for col in final_df.columns if col.startswith('source_region_')])}

### 3.3 因变量
- `normalized_sentiment`: 标准化情感得分

## 4. 自变量集统计描述
{final_df.describe().to_string()}

## 5. 结论与建议

1. **自变量构建完成**: 成功构建了包含时间、合作意愿、发展需求感知强度和报道来源区域的自变量集
2. **合作意愿指标优化**: 使用高级TF-IDF方法优化了合作意愿指标，具有较好的区分度
3. **发展需求感知强度**: 通过主成分分析将多维度指标降维为单一指标，解释方差比为{pca_development.explained_variance_ratio_[0]:.4f}
4. **报道来源分类**: 成功将报道来源分类为北非、西非、东非、南非和中非五个非洲区域

### 5.1 使用建议
- 该自变量集可直接用于后续的线性回归分析
- 建议在回归分析中考虑自变量之间的交互效应
- 可进一步探索其他可能的自变量，如文章长度、主题分类等

### 5.2 局限性
- 合作意愿指标基于文本内容分析，可能受到文本质量的影响
- 报道来源分类可能存在一定的主观性
- 时间变量仅使用了年份，可考虑更细粒度的时间划分
"""

# 保存最终报告
with open(os.path.join(result_dir, '最终自变量集构建报告.md'), 'w', encoding='utf-8') as f:
    f.write(report)

print("\n" + "="*50)
print("最终自变量集生成完成！")
print(f"结果已保存到: {result_dir}")
print(f"最终报告: {os.path.join(result_dir, '最终自变量集构建报告.md')}")
print(f"最终自变量数据: {os.path.join(result_dir, '最终自变量数据.csv')}")
print(f"包含优化指标的完整数据集: {os.path.join(result_dir, '包含优化指标的完整数据集.csv')}")

# 评估最终结果
print(f"\n最终评估结果:")
print(f"- 合作意愿指标均值: {df['cooperation_willingness'].mean():.4f}")
print(f"- 合作意愿指标标准差: {df['cooperation_willingness'].std():.4f}")
print(f"- 发展需求感知主成分解释方差比: {pca_development.explained_variance_ratio_[0]:.4f}")
print(f"- 最终自变量集行数: {len(final_df)}")
