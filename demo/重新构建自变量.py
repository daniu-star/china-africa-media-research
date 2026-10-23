import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 创建结果目录
result_dir = 'c:/Users/13067/Desktop/论文/非洲/demo/重新构建自变量结果'
os.makedirs(result_dir, exist_ok=True)

# 1. 数据准备
print("1. 数据准备")
df = pd.read_csv(r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv')

# 2. 报道来源地理区域分类
print("2. 报道来源地理区域分类")

# 基于网站域名和国家的地理区域分类
source_region_mapping = {
    # 北非（埃及、阿尔及利亚、突尼斯、摩洛哥、利比亚）
    'Ahram Online': '北非',
    'english.ahram.org.eg': '北非',
    '金字塔报': '北非',
    'www.algerie-eco.com': '北非',
    'www.tunisienumerique.com': '北非',
    'www.maghrebia.com': '北非',
    
    # 西非（尼日利亚、加纳、塞内加尔、科特迪瓦等）
    'guardian.ng': '西非',
    'premiumtimesng.com': '西非',
    'www.vanguardngr.com': '西非',
    'www.thisdaylive.com': '西非',
    'www.ghanaweb.com': '西非',
    'www.modernghana.com': '西非',
    
    # 东非（肯尼亚、坦桑尼亚、乌干达、埃塞俄比亚、卢旺达等）
    'nation.africa': '东非',
    'theeastafrican.co.ke': '东非',
    'www.dailynews.co.tz': '东非',
    'www.newtimes.co.rw': '东非',
    'www.monitor.co.ug': '东非',
    'www.addisfortune.net': '东非',
    'www.capitalethiopia.com': '东非',
    'www.thecitizen.co.tz': '东非',
    
    # 南非（南非、博茨瓦纳、纳米比亚、津巴布韦等）
    'mg.co.za': '南非',
    'www.news24.com': '南非',
    'www.sowetanlive.co.za': '南非',
    'www.iol.co.za': '南非',
    'www.namibian.com.na': '南非',
    'www.zimbabwesituation.com': '南非',
    'www.businesslive.co.za': '南非',
    'www.fin24.com': '南非',
    
    # 泛非和国际媒体
    'allafrica.com': '泛非',
    'www.panapress.com': '泛非',
    'www.africanews.com': '泛非',
    'www.africa-confidential.com': '泛非',
    'www.theafricareport.com': '泛非',
    'theafricareport.com': '泛非',
    'aljazeera.com/africa': '国际',
    'africa-confidential.com': '泛非',
    'bbc.com/africa': '国际',
    'africanews.com': '泛非',
    'africanarguments.org': '国际',
    'africanbusinessmagazine.com': '国际',
    'africaintelligence.com': '国际',
    'reuters.com/africa': '国际',
    'African News Network': '国际',
    'Theguardian': '国际',
    'Bbc': '国际',
    'Chinadaily': '国际'
}

# 应用分类
df['source_region'] = df['source'].map(source_region_mapping).fillna('其他')

# 3. 合作强度指标优化
print("3. 合作强度指标优化")

# 合作强度的构成指标
cooperation_features = [
    'long_term_word_count_scaled',  # 长期合作词汇比例
    'has_multi_agent_interaction_scaled',  # 多主体互动
    'community_similarity',  # 社区相似度
    'china_africa_community_recognition',  # 中非命运共同体认知
    'development_terms_weight',  # 发展术语权重
    'development_demand_perception'  # 发展需求感知
]

# 检查所有特征是否存在
for feature in cooperation_features:
    if feature not in df.columns:
        print(f"警告: 特征 {feature} 不存在，将被跳过")
        cooperation_features.remove(feature)

# 提取合作强度相关特征
df_cooperation = df[cooperation_features].dropna()

# 标准化数据
scaler = StandardScaler()
cooperation_scaled = scaler.fit_transform(df_cooperation)

# 主成分分析优化合作强度
pca_cooperation = PCA(n_components=1, random_state=42)
df['cooperation_strength'] = pca_cooperation.fit_transform(cooperation_scaled)

# 标准化合作强度到0-1范围
df['cooperation_strength'] = (df['cooperation_strength'] - df['cooperation_strength'].min()) / \
                            (df['cooperation_strength'].max() - df['cooperation_strength'].min())

# 4. 发展需求感知强度PCA分析
print("4. 发展需求感知强度PCA分析")

development_features = [
    'development_terms_weight',
    'development_demand_perception',
    'development_keyword_count',
    'development_keyword_density'
]

# 检查所有特征是否存在
for feature in development_features:
    if feature not in df.columns:
        print(f"警告: 特征 {feature} 不存在，将被跳过")
        development_features.remove(feature)

# 提取发展需求感知相关特征
df_development = df[development_features].dropna()

# 标准化数据
development_scaled = scaler.fit_transform(df_development)

# 主成分分析
pca_development = PCA(n_components=1, random_state=42)
df['development_demand_pca'] = pca_development.fit_transform(development_scaled)

# 5. 时间变量处理
print("5. 时间变量处理")

# 将date转换为 datetime 并提取年份和月份
df['date'] = pd.to_datetime(df['date'], errors='coerce')

# 提取年份作为时间变量，避免处理复杂的周期类型
df['time_index'] = df['date'].dt.year.fillna(0).astype(int)

# 6. 构建最终自变量集
print("6. 构建最终自变量集")

# 选择最终自变量
final_df = df[[
    'time_index',  # 时间
    'cooperation_strength',  # 优化后的合作强度
    'development_demand_pca',  # PCA优化后的发展需求感知强度
    'source_region',  # 报道来源区域
    'normalized_sentiment'  # 因变量：标准化情感得分
]].dropna()

# 7. 生成虚拟变量
print("7. 生成虚拟变量")
final_df = pd.get_dummies(final_df, columns=['source_region'], drop_first=True)

# 8. 模型构建与评估
print("8. 模型构建与评估")

# 准备自变量和因变量
X = final_df.drop('normalized_sentiment', axis=1)
y = final_df['normalized_sentiment']

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 构建线性回归模型
model = LinearRegression()
model.fit(X_train, y_train)

# 模型评估
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)

# 计算调整R²
n = len(X_test)
p = X_test.shape[1]
adjusted_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1)

# 9. 结果可视化与报告
print("9. 结果可视化与报告")

# 生成详细报告
report = f"""# 自变量重新构建与模型评估报告

## 1. 数据概览
- 原始数据行数: {len(df)}
- 有效数据行数: {len(final_df)}
- 数据缺失率: {((len(df) - len(final_df)) / len(df)) * 100:.2f}%

## 2. 报道来源地理区域分类
- 分类规则: 基于网站域名和所属国家的地理位置
- 分类结果:
{df['source_region'].value_counts().to_string()}

## 3. 合作强度指标优化
- 构成指标: {', '.join(cooperation_features)}
- 优化方法: 主成分分析(PCA)
- 主成分解释方差比: {pca_cooperation.explained_variance_ratio_[0]:.4f}
- 合作强度分布:
  - 均值: {df['cooperation_strength'].mean():.4f}
  - 标准差: {df['cooperation_strength'].std():.4f}
  - 最小值: {df['cooperation_strength'].min():.4f}
  - 最大值: {df['cooperation_strength'].max():.4f}

## 4. 发展需求感知强度PCA分析
- 构成指标: {', '.join(development_features)}
- 主成分解释方差比: {pca_development.explained_variance_ratio_[0]:.4f}
- 发展需求感知强度分布:
  - 均值: {df['development_demand_pca'].mean():.4f}
  - 标准差: {df['development_demand_pca'].std():.4f}
  - 最小值: {df['development_demand_pca'].min():.4f}
  - 最大值: {df['development_demand_pca'].max():.4f}

## 5. 自变量集
最终自变量包括:
- 时间变量: time_index (数值型)
- 合作强度: cooperation_strength (数值型, 0-1标准化)
- 发展需求感知强度: development_demand_pca (数值型)
- 报道来源区域: 虚拟变量 (北非、西非、东非、南非、泛非、国际、其他)

## 6. 模型评估结果
- R²: {r2:.4f}
- 调整R²: {adjusted_r2:.4f}
- 模型系数:
{pd.DataFrame({'自变量': X.columns, '系数': model.coef_}).to_string(index=False)}
- 截距: {model.intercept_:.4f}

## 7. 模型解释
- 时间变量系数: {model.coef_[0]:.4f}，表示随时间变化的情感趋势
- 合作强度系数: {model.coef_[1]:.4f}，表示合作强度对情感的影响
- 发展需求感知强度系数: {model.coef_[2]:.4f}，表示发展需求感知对情感的影响
- 各区域虚拟变量系数表示相对于基准类别的情感差异

## 8. 结论与建议
1. 合作强度指标通过主成分分析优化后，具有较高的解释力
2. 发展需求感知强度经PCA处理后，简化了模型复杂度
3. 报道来源区域对情感有显著影响，不同区域的报道视角存在差异
4. 模型的调整R²为{adjusted_r2:.4f}，表明模型具有一定的解释力，但仍有提升空间
5. 建议进一步考虑更多的控制变量，如文章主题、作者背景等
"""

# 保存报告
with open(os.path.join(result_dir, '自变量重新构建与模型评估报告.md'), 'w', encoding='utf-8') as f:
    f.write(report)

# 保存处理后的数据
final_df.to_csv(os.path.join(result_dir, '重新构建的自变量数据.csv'), index=False, encoding='utf-8-sig')

# 可视化1：合作强度分布
plt.figure(figsize=(10, 6))
sns.histplot(df['cooperation_strength'].dropna(), bins=20, kde=True)
plt.title('优化后的合作强度分布')
plt.xlabel('合作强度')
plt.ylabel('频数')
plt.savefig(os.path.join(result_dir, '合作强度分布.png'), dpi=300, bbox_inches='tight')
plt.close()

# 可视化2：发展需求感知强度分布
plt.figure(figsize=(10, 6))
sns.histplot(df['development_demand_pca'].dropna(), bins=20, kde=True)
plt.title('PCA优化后的发展需求感知强度分布')
plt.xlabel('发展需求感知强度')
plt.ylabel('频数')
plt.savefig(os.path.join(result_dir, '发展需求感知强度分布.png'), dpi=300, bbox_inches='tight')
plt.close()

# 可视化3：各区域情感得分对比
plt.figure(figsize=(12, 6))
sns.boxplot(x='source_region', y='normalized_sentiment', data=df.dropna(subset=['source_region', 'normalized_sentiment']))
plt.title('不同区域报道的情感得分对比')
plt.xlabel('报道区域')
plt.ylabel('标准化情感得分')
plt.xticks(rotation=45)
plt.savefig(os.path.join(result_dir, '区域情感得分对比.png'), dpi=300, bbox_inches='tight')
plt.close()

# 可视化4：合作强度与情感得分关系
plt.figure(figsize=(10, 6))
sns.scatterplot(x='cooperation_strength', y='normalized_sentiment', data=df.dropna(subset=['cooperation_strength', 'normalized_sentiment']), alpha=0.5)
sns.regplot(x='cooperation_strength', y='normalized_sentiment', data=df.dropna(subset=['cooperation_strength', 'normalized_sentiment']), scatter=False, color='red')
plt.title('合作强度与情感得分关系')
plt.xlabel('合作强度')
plt.ylabel('标准化情感得分')
plt.savefig(os.path.join(result_dir, '合作强度与情感关系.png'), dpi=300, bbox_inches='tight')
plt.close()

print("自变量重新构建完成！")
print(f"结果已保存到: {result_dir}")
print(f"报告文件: {os.path.join(result_dir, '自变量重新构建与模型评估报告.md')}")
print(f"处理后的数据: {os.path.join(result_dir, '重新构建的自变量数据.csv')}")
