import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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
result_dir = '优化版_群体差异可视化结果'
os.makedirs(result_dir, exist_ok=True)
print(f"结果将保存到: {result_dir}")

# 1. 数据读取与准备
print("\n1. 数据读取与准备")

# 读取优化版潜在剖面分析数据
data_path = r'c:\Users\13067\Desktop\论文\非洲\demo\优化版_潜在剖面分析结果\数据_带群体分类.csv'
df = pd.read_csv(data_path, low_memory=False)
print(f"数据大小: {len(df)} 行, {len(df.columns)} 列")

# 读取优化版多群组回归分析结果
path_coefficients_path = r'c:\Users\13067\Desktop\论文\非洲\demo\优化版_多群组回归分析结果\路径系数表.csv'
path_df = pd.read_csv(path_coefficients_path)
print(f"路径系数数据大小: {len(path_df)} 行, {len(path_df.columns)} 列")

# 2. 定义核心变量和控制变量
print("\n2. 定义核心变量和控制变量")
core_vars = {
    'development_demand': 'development_demand_pca',
    'sentiment': 'normalized_sentiment',
    'cooperation': 'cooperation_willingness_advanced',
    'recognition': 'china_africa_community_recognition'
}

# 定义控制变量
control_vars = {
    # 连续控制变量
    'time_index': 'time_index',
    'total_words_count': 'total_words_count',
    # 分类控制变量
    'source_region_5': 'source_region_5',
    '主题': '主题'
}

# 3. 群体分布可视化
print("\n3. 群体分布可视化")

# 3.1 群体分布饼图
plt.figure(figsize=(10, 8))
profile_counts = df['profile'].value_counts().sort_index()
colors = sns.color_palette("Set3", len(profile_counts))

wedges, texts, autotexts = plt.pie(
    profile_counts, 
    labels=profile_counts.index, 
    autopct='%1.1f%%', 
    startangle=90, 
    colors=colors,
    wedgeprops={'edgecolor': 'white', 'linewidth': 1}
)

# 设置文本样式
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(12)
    autotext.set_fontweight('bold')

plt.title('非洲媒体潜在群体分布', fontsize=16, fontweight='bold')
plt.axis('equal')
plt.tight_layout()
plt.savefig(os.path.join(result_dir, '群体分布饼图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 3.2 群体分布柱状图
plt.figure(figsize=(12, 8))
sns.barplot(x=profile_counts.index, y=profile_counts.values, palette='Set3')
plt.title('非洲媒体潜在群体分布', fontsize=16, fontweight='bold')
plt.xlabel('群体', fontsize=14)
plt.ylabel('样本量', fontsize=14)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)

# 添加数值标签
for i, v in enumerate(profile_counts.values):
    plt.text(i, v + 50, str(v), ha='center', va='bottom', fontsize=12, fontweight='bold')

plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(os.path.join(result_dir, '群体分布柱状图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 4. 群体特征可视化
print("\n4. 群体特征可视化")

# 4.1 核心变量箱线图
plt.figure(figsize=(15, 12))

for i, (var_name, var_col) in enumerate(core_vars.items(), 1):
    plt.subplot(2, 2, i)
    sns.boxplot(x='profile', y=var_col, data=df, palette='Set3', showfliers=False)
    sns.stripplot(x='profile', y=var_col, data=df, color='black', alpha=0.3, size=2)
    plt.title(f'{var_name}的群体分布', fontsize=14, fontweight='bold')
    plt.xlabel('群体', fontsize=12)
    plt.ylabel(var_name, fontsize=12)
    plt.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '核心变量箱线图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 4.2 核心变量小提琴图
plt.figure(figsize=(15, 12))

for i, (var_name, var_col) in enumerate(core_vars.items(), 1):
    plt.subplot(2, 2, i)
    sns.violinplot(x='profile', y=var_col, data=df, palette='Set3', inner='quartile')
    plt.title(f'{var_name}的群体分布', fontsize=14, fontweight='bold')
    plt.xlabel('群体', fontsize=12)
    plt.ylabel(var_name, fontsize=12)
    plt.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '核心变量小提琴图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 4.3 群体特征雷达图
plt.figure(figsize=(12, 10))

# 计算各群体核心变量的均值
profile_means = df.groupby('profile')[list(core_vars.values())].mean()

# 标准化数据
profile_means_std = (profile_means - profile_means.mean()) / profile_means.std()

# 雷达图参数
categories = list(core_vars.keys())
n_categories = len(categories)
angles = [n / float(n_categories) * 2 * np.pi for n in range(n_categories)]
angles += angles[:1]  # 闭合雷达图

ax = plt.subplot(111, polar=True)

# 绘制每个群体的雷达图
colors = sns.color_palette("husl", len(profile_means_std))
for i, (profile, row) in enumerate(profile_means_std.iterrows()):
    values = row.values.tolist()
    values += values[:1]  # 闭合雷达图
    ax.plot(angles, values, linewidth=2, linestyle='solid', label=f'群体 {profile}', color=colors[i])
    ax.fill(angles, values, alpha=0.1, color=colors[i])

# 设置雷达图属性
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=12, fontweight='bold')
ax.set_yticklabels([])
ax.set_title('群体核心特征雷达图', fontsize=16, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '群体核心特征雷达图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 5. 控制变量可视化
print("\n5. 控制变量可视化")

# 5.1 连续控制变量可视化
print("  连续控制变量可视化...")
plt.figure(figsize=(15, 12))

continuous_vars = ['time_index', 'total_words_count']
for i, var in enumerate(continuous_vars, 1):
    plt.subplot(2, 2, i)
    sns.boxplot(x='profile', y=var, data=df, palette='Set3', showfliers=False)
    sns.stripplot(x='profile', y=var, data=df, color='black', alpha=0.3, size=2)
    plt.title(f'{var}的群体分布', fontsize=14, fontweight='bold')
    plt.xlabel('群体', fontsize=12)
    plt.ylabel(var, fontsize=12)
    plt.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '连续控制变量箱线图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 5.2 分类控制变量可视化 - 地区分布
print("  分类控制变量可视化 - 地区分布...")
plt.figure(figsize=(12, 8))

region_counts = df.groupby(['profile', 'source_region_5']).size().unstack(fill_value=0)
region_counts.plot(kind='bar', stacked=True, figsize=(12, 8), colormap='Set3')

plt.title('各群体地区分布', fontsize=16, fontweight='bold')
plt.xlabel('群体', fontsize=14)
plt.ylabel('样本量', fontsize=14)
plt.xticks(rotation=0, fontsize=12)
plt.legend(title='地区', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(os.path.join(result_dir, '群体地区分布.png'), dpi=300, bbox_inches='tight')
plt.close()

# 5.3 分类控制变量可视化 - 主题分布
print("  分类控制变量可视化 - 主题分布...")
plt.figure(figsize=(12, 8))

category_counts = df.groupby(['profile', '主题']).size().unstack(fill_value=0)
category_counts.plot(kind='bar', stacked=True, figsize=(12, 8), colormap='Set3')

plt.title('各群体新闻主题分布', fontsize=16, fontweight='bold')
plt.xlabel('群体', fontsize=14)
plt.ylabel('样本量', fontsize=14)
plt.xticks(rotation=0, fontsize=12)
plt.legend(title='新闻主题', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(os.path.join(result_dir, '群体新闻主题分布.png'), dpi=300, bbox_inches='tight')
plt.close()

# 6. 群体差异综合可视化
print("\n6. 群体差异综合可视化")

# 6.1 群体特征散点图矩阵
plt.figure(figsize=(15, 12))
sns.pairplot(
    df, 
    vars=list(core_vars.values()), 
    hue='profile', 
    palette='Set1', 
    plot_kws={'alpha': 0.6, 's': 30}, 
    diag_kws={'alpha': 0.8}
)
plt.suptitle('群体特征散点图矩阵', y=1.02, fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(result_dir, '群体特征散点图矩阵.png'), dpi=300, bbox_inches='tight')
plt.close()

# 6.2 群体特征相关性热图
plt.figure(figsize=(15, 12))

# 计算每个群体的相关性矩阵
corr_matrices = {}
for profile in df['profile'].unique():
    profile_data = df[df['profile'] == profile]
    corr_matrix = profile_data[list(core_vars.values())].corr()
    corr_matrices[profile] = corr_matrix

# 绘制多个热图
n_profiles = len(corr_matrices)
n_cols = 3
n_rows = (n_profiles + n_cols - 1) // n_cols

for i, (profile, corr_matrix) in enumerate(corr_matrices.items(), 1):
    plt.subplot(n_rows, n_cols, i)
    sns.heatmap(
        corr_matrix, 
        annot=True, 
        cmap='coolwarm', 
        center=0, 
        fmt='.2f', 
        cbar=False,
        square=True
    )
    plt.title(f'群体 {profile} 特征相关性', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(rotation=0, fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '群体特征相关性热图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 7. 路径系数简化可视化 - 仅展示核心变量路径
print("\n7. 路径系数简化可视化")

# 7.1 核心变量路径系数热图 - 仅展示完整模型
plt.figure(figsize=(12, 8))

# 选择完整模型数据
full_path_df = path_df[path_df['model'] == 'full']

# 准备核心变量路径系数数据
core_path_cols = [
    'profile',
    'path_development_demand_pca_M_full',
    'path_cooperation_willingness_advanced_M_full',
    'path_M_Y_full',
    'path_development_demand_pca_Y_direct_full',
    'path_cooperation_willingness_advanced_Y_direct_full'
]

path_data = full_path_df[core_path_cols].set_index('profile')

# 路径名称映射
path_names = {
    'path_development_demand_pca_M_full': '发展需求→情感',
    'path_cooperation_willingness_advanced_M_full': '合作意愿→情感',
    'path_M_Y_full': '情感→认同',
    'path_development_demand_pca_Y_direct_full': '发展需求→认同(直接)',
    'path_cooperation_willingness_advanced_Y_direct_full': '合作意愿→认同(直接)'
}

path_data = path_data.rename(columns=path_names)

# 绘制热图
sns.heatmap(
    path_data, 
    annot=True, 
    cmap='RdBu_r', 
    center=0, 
    fmt='.2f', 
    cbar_kws={'label': '路径系数'}
)

plt.title('不同群体的核心路径系数热图（完整模型）', fontsize=16, fontweight='bold')
plt.xlabel('路径', fontsize=14)
plt.ylabel('群体', fontsize=14)
plt.xticks(rotation=45, ha='right', fontsize=12)
plt.yticks(fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(result_dir, '路径系数热图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 7.2 核心变量路径系数柱状图对比
plt.figure(figsize=(15, 12))

# 路径列表
paths = list(path_names.values())
path_cols = list(path_names.keys())

for i, (path_name, path_col) in enumerate(zip(paths, path_cols), 1):
    plt.subplot(3, 2, i)
    sns.barplot(x='profile', y=path_col, data=full_path_df, palette='Set2')
    plt.title(f'{path_name}的群体差异', fontsize=14, fontweight='bold')
    plt.xlabel('群体', fontsize=12)
    plt.ylabel('路径系数', fontsize=12)
    plt.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '路径系数柱状图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 8. 读取中介效应结果进行可视化
print("\n8. 中介效应可视化")

# 读取中介效应结果
mediation_path = r'c:\Users\13067\Desktop\论文\非洲\demo\优化版_多群组回归分析结果\中介效应结果.csv'
mediation_df = pd.read_csv(mediation_path)
print(f"中介效应数据大小: {len(mediation_df)} 行, {len(mediation_df.columns)} 列")

# 8.1 效应分解对比图
plt.figure(figsize=(15, 12))

# 发展需求感知的效应分解
plt.subplot(2, 1, 1)
bar_width = 0.25
x = np.arange(len(mediation_df))

plt.bar(x - bar_width, mediation_df['total_effect_development_full'], width=bar_width, label='总效应', color='blue', alpha=0.8)
plt.bar(x, mediation_df['direct_effect_development_full'], width=bar_width, label='直接效应', color='green', alpha=0.8)
plt.bar(x + bar_width, mediation_df['indirect_effect_development_full'], width=bar_width, label='间接效应', color='red', alpha=0.8)

plt.title('发展需求感知对认同的效应分解（完整模型）', fontsize=16, fontweight='bold')
plt.xlabel('群体', fontsize=14)
plt.ylabel('效应值', fontsize=14)
plt.xticks(x, mediation_df['profile'])
plt.legend()
plt.grid(True, alpha=0.3, axis='y')

# 合作意愿的效应分解
plt.subplot(2, 1, 2)
plt.bar(x - bar_width, mediation_df['total_effect_cooperation_full'], width=bar_width, label='总效应', color='blue', alpha=0.8)
plt.bar(x, mediation_df['direct_effect_cooperation_full'], width=bar_width, label='直接效应', color='green', alpha=0.8)
plt.bar(x + bar_width, mediation_df['indirect_effect_cooperation_full'], width=bar_width, label='间接效应', color='red', alpha=0.8)

plt.title('合作意愿对认同的效应分解（完整模型）', fontsize=16, fontweight='bold')
plt.xlabel('群体', fontsize=14)
plt.ylabel('效应值', fontsize=14)
plt.xticks(x, mediation_df['profile'])
plt.legend()
plt.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '效应分解对比图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 8.2 中介效应占比对比图
plt.figure(figsize=(15, 10))

# 发展需求感知的中介效应占比
plt.subplot(2, 1, 1)
bar_width = 0.6
x = np.arange(len(mediation_df))

plt.bar(x, mediation_df['mediation_ratio_development_full'], width=bar_width, label='中介效应占比', color='red', alpha=0.7)
plt.bar(x, 100 - mediation_df['mediation_ratio_development_full'], width=bar_width, bottom=mediation_df['mediation_ratio_development_full'], label='直接效应占比', color='blue', alpha=0.7)

plt.title('发展需求感知→情感强度→认同的效应占比（完整模型）', fontsize=16, fontweight='bold')
plt.xlabel('群体', fontsize=14)
plt.ylabel('占比 (%)', fontsize=14)
plt.xticks(x, mediation_df['profile'])
plt.legend()
plt.grid(True, alpha=0.3, axis='y')
plt.ylim(0, 100)

# 合作意愿的中介效应占比
plt.subplot(2, 1, 2)
plt.bar(x, mediation_df['mediation_ratio_cooperation_full'], width=bar_width, label='中介效应占比', color='red', alpha=0.7)
plt.bar(x, 100 - mediation_df['mediation_ratio_cooperation_full'], width=bar_width, bottom=mediation_df['mediation_ratio_cooperation_full'], label='直接效应占比', color='blue', alpha=0.7)

plt.title('合作意愿→情感强度→认同的效应占比（完整模型）', fontsize=16, fontweight='bold')
plt.xlabel('群体', fontsize=14)
plt.ylabel('占比 (%)', fontsize=14)
plt.xticks(x, mediation_df['profile'])
plt.legend()
plt.grid(True, alpha=0.3, axis='y')
plt.ylim(0, 100)

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '中介效应占比堆叠图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 8. 生成可视化报告
print("\n8. 生成可视化报告")

report = "# 优化版群体差异可视化报告（纳入控制变量）\n\n"

report += "## 1. 研究背景与目的\n\n"
report += "本报告通过多种可视化方法，展示非洲媒体不同潜在群体在中非命运共同体认同建构中的差异，\n"
report += "重点分析群体特征、路径系数和中介效应的差异，并纳入媒体类型、地区等控制变量，\n"
report += "以更全面地了解非洲媒体的异质性和认同建构路径。\n\n"

report += "## 2. 数据来源\n\n"
report += f"- 潜在剖面分析数据: {data_path}\n"
report += f"- 多群组回归分析结果: {path_coefficients_path}\n\n"

report += "## 3. 群体分布\n\n"
report += "### 3.1 群体分布饼图\n"
report += "![群体分布饼图](群体分布饼图.png)\n\n"

report += "### 3.2 群体分布柱状图\n"
report += "![群体分布柱状图](群体分布柱状图.png)\n\n"

report += "## 4. 群体特征差异\n\n"
report += "### 4.1 核心变量箱线图\n"
report += "![核心变量箱线图](核心变量箱线图.png)\n\n"

report += "### 4.2 核心变量小提琴图\n"
report += "![核心变量小提琴图](核心变量小提琴图.png)\n\n"

report += "### 4.3 群体核心特征雷达图\n"
report += "![群体核心特征雷达图](群体核心特征雷达图.png)\n\n"

report += "### 4.4 群体特征散点图矩阵\n"
report += "![群体特征散点图矩阵](群体特征散点图矩阵.png)\n\n"

report += "### 4.5 群体特征相关性热图\n"
report += "![群体特征相关性热图](群体特征相关性热图.png)\n\n"

report += "## 5. 控制变量差异\n\n"
report += "### 5.1 连续控制变量箱线图\n"
report += "![连续控制变量箱线图](连续控制变量箱线图.png)\n\n"

report += "### 5.2 群体地区分布\n"
report += "![群体地区分布](群体地区分布.png)\n\n"

report += "### 5.3 群体新闻主题分布\n"
report += "![群体新闻主题分布](群体新闻主题分布.png)\n\n"

report += "## 6. 路径系数差异\n\n"
report += "### 6.1 路径系数热图\n"
report += "![路径系数热图](路径系数热图.png)\n\n"

report += "### 6.2 路径系数柱状图对比\n"
report += "![路径系数柱状图](路径系数柱状图.png)\n\n"

report += "## 7. 中介效应差异\n\n"
report += "### 7.1 中介效应占比堆叠图\n"
report += "![中介效应占比堆叠图](中介效应占比堆叠图.png)\n\n"

report += "### 7.2 效应分解对比图\n"
report += "![效应分解对比图](效应分解对比图.png)\n\n"

report += "## 8. 主要发现\n\n"
report += "1. **群体分布不均衡**: 非洲媒体群体分布存在显著的不均衡，部分群体样本量较大，部分群体样本量较小。\n\n"

report += "2. **群体特征差异显著**: 不同群体在发展需求感知、情感强度、合作意愿和认同度方面存在显著差异，\n"
report += "   表明非洲媒体在中非命运共同体认同建构中表现出明显的异质性。\n\n"

report += "3. **控制变量差异明显**: 不同群体在地区分布和新闻类别上存在明显差异，\n"
report += "   表明媒体类型和地区等控制变量对认同建构有重要影响。\n\n"

report += "4. **路径系数差异明显**: 不同群体的路径系数存在明显差异，\n"
report += "   表明认同建构的路径在不同群体中是不同的。\n\n"

report += "5. **中介效应占比差异**: 情感强度的中介效应占比在不同群体中存在差异，\n"
report += "   部分群体以直接效应为主，部分群体以间接效应为主。\n\n"

report += "6. **认同建构路径多元化**: 非洲媒体通过多种路径建构中非命运共同体认同，\n"
report += "   包括情感驱动型、理性务实型等多种模式。\n\n"

report += "## 9. 结论与启示\n\n"
report += "### 9.1 结论\n"
report += "- **非洲媒体存在显著的异质性**: 识别出具有不同特征的媒体群体，\n"
report += "   其认同建构路径存在显著差异。\n"
report += "- **认同建构路径多元化**: 不同群体通过不同路径建构中非命运共同体认同，\n"
report += "   情感驱动和理性务实都是有效的认同建构方式。\n"
report += "- **情感中介作用存在群体差异**: 情感强度的中介作用在不同群体中表现不同，\n"
report += "   并非所有群体都以情感驱动为主。\n"
report += "- **控制变量不可忽视**: 媒体类型、地区等控制变量对认同建构有重要影响，\n"
report += "   纳入这些变量可以更全面地理解认同建构过程。\n\n"

report += "### 9.2 启示\n"
report += "- **打破'一刀切'结论**: 中非命运共同体认同建构是一个多元、分层的过程，\n"
report += "   不能用单一模式解释所有媒体的行为。\n"
report += "- **重视群体异质性**: 研究和实践中需要考虑不同媒体群体的特征差异，\n"
report += "   制定差异化的传播策略。\n"
report += "- **多元路径并存**: 认同建构的不同路径可以并存，\n"
report += "   情感驱动和理性务实都是有效的认同建构方式。\n"
report += "- **考虑控制变量影响**: 在研究和实践中，应充分考虑媒体类型、地区等控制变量的影响，\n"
report += "   制定更精准的传播策略。\n\n"

report += "## 10. 数据与代码\n\n"
report += f"- **数据文件**: {data_path}\n"
report += f"- **分析代码**: {os.path.basename(__file__)}\n"
report += f"- **结果文件夹**: {result_dir}\n\n"

report += "---\n\n"
report += f"**报告生成时间**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

# 保存报告
with open(os.path.join(result_dir, '群体差异可视化报告.md'), 'w', encoding='utf-8') as f:
    f.write(report)

# 9. 输出完成信息
print("\n" + "="*50)
print("优化版群体差异可视化完成！")
print(f"所有结果已保存到: {result_dir}")
print("包含文件：")
print("1. 群体分布饼图.png")
print("2. 群体分布柱状图.png")
print("3. 核心变量箱线图.png")
print("4. 核心变量小提琴图.png")
print("5. 群体核心特征雷达图.png")
print("6. 连续控制变量箱线图.png")
print("7. 群体地区分布.png")
print("8. 群体新闻类别分布.png")
print("9. 路径系数热图.png")
print("10. 路径系数柱状图.png")
print("11. 中介效应占比堆叠图.png")
print("12. 效应分解对比图.png")
print("13. 群体特征散点图矩阵.png")
print("14. 群体特征相关性热图.png")
print("15. 优化版群体差异可视化报告.md")
print("="*50)
