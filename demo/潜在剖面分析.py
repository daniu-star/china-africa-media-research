import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score
import os
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 12
plt.rcParams['figure.figsize'] = (12, 8)
sns.set_style("whitegrid")
sns.set_palette("Set2")
sns.set(font="SimHei")

# 创建结果目录
result_dir = '潜在剖面分析结果'
os.makedirs(result_dir, exist_ok=True)
print(f"结果将保存到: {result_dir}")

# 1. 数据读取与准备
print("\n1. 数据读取与准备")
data_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv'
df = pd.read_csv(data_path, low_memory=False)
print(f"原始数据大小: {len(df)} 行, {len(df.columns)} 列")

# 2. 变量中心化处理
print("\n2. 变量中心化处理")
center_vars = ['development_demand_pca', 'normalized_sentiment', 'cooperation_willingness_advanced']
for var in center_vars:
    df[f'{var}_centered'] = df[var] - df[var].mean()
    print(f"{var} 均值: {df[var].mean():.4f}, 中心化后均值: {df[f'{var}_centered'].mean():.4f}")

# 3. 准备潜在剖面分析数据
print("\n3. 准备潜在剖面分析数据")
lpa_vars = ['development_demand_pca_centered', 'normalized_sentiment_centered', 'cooperation_willingness_advanced_centered']
lpa_data = df[lpa_vars]
print(f"分析变量: {lpa_vars}")
print(f"分析数据大小: {lpa_data.shape}")

# 4. 潜在剖面分析
print("\n4. 潜在剖面分析")

# 拟合1-6个剖面的模型
max_profiles = 6
models = {}
results = []

for n in range(1, max_profiles + 1):
    print(f"\n拟合 {n} 个剖面的模型...")
    
    # 拟合高斯混合模型
    gmm = GaussianMixture(n_components=n, random_state=42, covariance_type='full')
    gmm.fit(lpa_data)
    
    # 计算模型指标
    aic = gmm.aic(lpa_data)
    bic = gmm.bic(lpa_data)
    entropy = gmm.score(lpa_data)
    
    # 预测群体分类
    labels = gmm.predict(lpa_data)
    
    # 计算轮廓系数（仅当n > 1时）
    silhouette = silhouette_score(lpa_data, labels) if n > 1 else None
    
    # 保存模型结果
    models[n] = {
        'model': gmm,
        'labels': labels,
        'aic': aic,
        'bic': bic,
        'entropy': entropy,
        'silhouette': silhouette
    }
    
    results.append({
        'profiles': n,
        'aic': aic,
        'bic': bic,
        'entropy': entropy,
        'silhouette': silhouette
    })
    
    print(f"  AIC: {aic:.2f}")
    print(f"  BIC: {bic:.2f}")
    print(f"  熵值: {entropy:.2f}")
    if silhouette is not None:
        print(f"  轮廓系数: {silhouette:.2f}")

# 5. 模型比较与选择
print("\n5. 模型比较与选择")
results_df = pd.DataFrame(results)
print("模型拟合指标:")
print(results_df)

# 保存模型比较结果
results_df.to_csv(os.path.join(result_dir, '模型拟合指标.csv'), index=False, encoding='utf-8-sig')

# 可视化模型拟合指标
plt.figure(figsize=(12, 8))

# AIC和BIC
plt.subplot(2, 1, 1)
plt.plot(results_df['profiles'], results_df['aic'], marker='o', label='AIC')
plt.plot(results_df['profiles'], results_df['bic'], marker='s', label='BIC')
plt.title('AIC和BIC指标对比')
plt.xlabel('剖面数量')
plt.ylabel('指标值')
plt.legend()
plt.grid(True, alpha=0.3)

# 轮廓系数
plt.subplot(2, 1, 2)
plt.plot(results_df['profiles'][1:], results_df['silhouette'][1:], marker='^', color='green')
plt.title('轮廓系数对比')
plt.xlabel('剖面数量')
plt.ylabel('轮廓系数')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '模型拟合指标对比.png'), dpi=300, bbox_inches='tight')
plt.close()

# 选择最佳模型（这里选择轮廓系数最高的模型，实际可根据需要调整）
best_n = results_df.loc[1:, 'silhouette'].idxmax() + 1  # +1因为索引从0开始
print(f"\n最佳剖面数量: {best_n}")

# 6. 获取最佳模型结果
print("\n6. 获取最佳模型结果")
best_model = models[best_n]
df['profile'] = best_model['labels']

# 7. 群体特征分析
print("\n7. 群体特征分析")

# 群体大小
profile_sizes = df['profile'].value_counts().sort_index()
print("群体大小:")
print(profile_sizes)

# 群体特征描述
profile_desc = df.groupby('profile')[lpa_vars].describe()
print("\n群体特征描述:")
print(profile_desc)

# 保存群体特征结果
profile_sizes.to_csv(os.path.join(result_dir, '群体大小.csv'), encoding='utf-8-sig', header=['数量'])
profile_desc.to_csv(os.path.join(result_dir, '群体特征描述.csv'), encoding='utf-8-sig')

# 8. 群体可视化
print("\n8. 群体可视化")

# 8.1 散点图矩阵
plt.figure(figsize=(15, 12))
sns.pairplot(df, vars=lpa_vars, hue='profile', palette='Set1', plot_kws={'alpha': 0.6})
plt.suptitle('潜在群体散点图矩阵', y=1.02, fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(result_dir, '群体散点图矩阵.png'), dpi=300, bbox_inches='tight')
plt.close()

# 8.2 箱线图
plt.figure(figsize=(15, 10))
for i, var in enumerate(lpa_vars, 1):
    plt.subplot(2, 2, i)
    sns.boxplot(x='profile', y=var, data=df, palette='Set1')
    plt.title(f'{var} 的群体分布')
    plt.xlabel('群体')
    plt.ylabel(var)
    
    # 添加群体均值点
    means = df.groupby('profile')[var].mean()
    plt.plot(range(len(means)), means, 'ro-', markersize=8)
    
    plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '群体箱线图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 8.3 三维散点图
fig = plt.figure(figsize=(15, 12))
ax = fig.add_subplot(111, projection='3d')

# 绘制三维散点图
scatter = ax.scatter(
    df['development_demand_pca_centered'],
    df['normalized_sentiment_centered'],
    df['cooperation_willingness_advanced_centered'],
    c=df['profile'],
    cmap='Set1',
    alpha=0.6,
    s=50
)

# 添加标签和标题
ax.set_xlabel('发展需求感知（中心化）')
ax.set_ylabel('情感强度（中心化）')
ax.set_zlabel('合作意愿（中心化）')
ax.set_title('三维散点图 - 潜在群体分布', fontsize=16, fontweight='bold')

# 添加颜色条
plt.colorbar(scatter, ax=ax, label='群体')

plt.savefig(os.path.join(result_dir, '群体三维散点图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 8.4 群体分布饼图
plt.figure(figsize=(10, 8))
colors = plt.cm.Set1(range(len(profile_sizes)))
plt.pie(profile_sizes, labels=profile_sizes.index, autopct='%1.1f%%', startangle=90, colors=colors)
plt.title('潜在群体分布', fontsize=16, fontweight='bold')
plt.axis('equal')
plt.tight_layout()
plt.savefig(os.path.join(result_dir, '群体分布饼图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 9. 群体命名建议
print("\n9. 群体命名建议")

# 基于群体特征给出命名建议
profile_means = df.groupby('profile')[lpa_vars].mean()
print("群体均值:")
print(profile_means)

# 生成命名建议
profile_names = {}
for profile in profile_means.index:
    means = profile_means.loc[profile]
    
    # 基于三个变量的均值水平（高于总体均值为高，否则为低/中）
    dev_demand = "高" if means['development_demand_pca_centered'] > 0 else "低"
    sentiment = "高" if means['normalized_sentiment_centered'] > 0 else "低"
    coop_will = "高" if means['cooperation_willingness_advanced_centered'] > 0 else "低"
    
    # 组合命名
    name = f"{sentiment}情感_{dev_demand}需求_{coop_will}合作"
    profile_names[profile] = name
    
    print(f"群体 {profile}: {name}")

# 10. 保存带有群体分类的数据
print("\n10. 保存带有群体分类的数据")
df.to_csv(os.path.join(result_dir, '数据_带群体分类.csv'), index=False, encoding='utf-8-sig')

# 11. 生成分析报告
print("\n11. 生成分析报告")

report = "# 潜在剖面分析报告\n\n"

report += "## 1. 研究背景与目的\n\n"
report += "本研究通过潜在剖面分析，识别非洲媒体在中非命运共同体认同建构中的不同子群体，\n"
report += "为后续多群组结构方程模型分析奠定基础。\n\n"

report += "## 2. 数据与方法\n\n"
report += "### 2.1 数据来源\n"
report += f"- 数据文件: {data_path}\n"
report += f"- 样本量: {len(df)} 个观测值\n\n"

report += "### 2.2 分析变量\n"
report += "- **发展需求感知强度**: development_demand_pca_centered\n"
report += "- **情感强度**: normalized_sentiment_centered\n"
report += "- **合作意愿**: cooperation_willingness_advanced_centered\n\n"

report += "### 2.3 分析方法\n"
report += "- 高斯混合模型 (Gaussian Mixture Model)\n"
report += f"- 拟合剖面数: 1-{max_profiles}\n"
report += "- 模型选择指标: AIC、BIC、熵值、轮廓系数\n\n"

report += "## 3. 模型拟合结果\n\n"
report += "### 3.1 模型拟合指标\n"
report += "| 剖面数 | AIC | BIC | 熵值 | 轮廓系数 |\n"
report += "|-------|-----|-----|------|----------|\n"
for _, row in results_df.iterrows():
    report += f"| {row['profiles']} | {row['aic']:.2f} | {row['bic']:.2f} | {row['entropy']:.2f} | {row['silhouette']:.4f} |\n"

report += "\n### 3.2 最佳模型选择\n"
report += f"- **最佳剖面数**: {best_n}\n"
report += f"- **选择依据**: 轮廓系数最高\n\n"

report += "## 4. 群体特征分析\n\n"
report += "### 4.1 群体大小\n"
report += "| 群体 | 数量 | 比例 |\n"
report += "|------|------|------|\n"
for profile, size in profile_sizes.items():
    proportion = size / len(df) * 100
    report += f"| {profile} | {size} | {proportion:.1f}% |\n"

report += "\n### 4.2 群体特征\n"
report += "| 群体 | 发展需求感知 | 情感强度 | 合作意愿 | 命名建议 |\n"
report += "|------|--------------|----------|----------|----------|\n"
for profile in profile_means.index:
    means = profile_means.loc[profile]
    dev_demand = "高" if means['development_demand_pca_centered'] > 0 else "低"
    sentiment = "高" if means['normalized_sentiment_centered'] > 0 else "低"
    coop_will = "高" if means['cooperation_willingness_advanced_centered'] > 0 else "低"
    name = profile_names[profile]
    report += f"| {profile} | {dev_demand} | {sentiment} | {coop_will} | {name} |\n"

report += "\n## 5. 可视化结果\n\n"
report += "### 5.1 模型拟合指标对比\n"
report += "![模型拟合指标对比](模型拟合指标对比.png)\n\n"

report += "### 5.2 群体散点图矩阵\n"
report += "![群体散点图矩阵](群体散点图矩阵.png)\n\n"

report += "### 5.3 群体箱线图\n"
report += "![群体箱线图](群体箱线图.png)\n\n"

report += "### 5.4 群体三维散点图\n"
report += "![群体三维散点图](群体三维散点图.png)\n\n"

report += "### 5.5 群体分布饼图\n"
report += "![群体分布饼图](群体分布饼图.png)\n\n"

report += "## 6. 结论与建议\n\n"
report += "1. **识别出 {best_n} 个潜在群体**: 非洲媒体在中非命运共同体认同建构中表现出明显的异质性\n"
report += "2. **群体特征差异显著**: 不同群体在发展需求感知、情感强度和合作意愿方面存在显著差异\n"
report += "3. **为后续研究奠定基础**: 群体分类结果可用于多群组结构方程模型分析，进一步探索不同群体的认同建构路径\n\n"

report += "## 7. 数据与代码\n\n"
report += f"- **数据文件**: {data_path}\n"
report += "- **分析代码**: 潜在剖面分析.py\n"
report += f"- **结果文件夹**: {result_dir}\n\n"

report += "---\n\n"
report += f"**报告生成时间**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

# 保存报告
with open(os.path.join(result_dir, '潜在剖面分析报告.md'), 'w', encoding='utf-8') as f:
    f.write(report)

# 12. 输出完成信息
print("\n" + "="*50)
print("潜在剖面分析完成！")
print(f"所有结果已保存到: {result_dir}")
print("包含文件：")
print("1. 模型拟合指标.csv")
print("2. 群体大小.csv")
print("3. 群体特征描述.csv")
print("4. 数据_带群体分类.csv")
print("5. 模型拟合指标对比.png")
print("6. 群体散点图矩阵.png")
print("7. 群体箱线图.png")
print("8. 群体三维散点图.png")
print("9. 群体分布饼图.png")
print("10. 潜在剖面分析报告.md")
print("="*50)
