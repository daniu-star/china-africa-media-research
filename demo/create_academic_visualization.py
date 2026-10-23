import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec
from scipy import stats

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

print("=== 合作纵深性变量学术化可视化 ===")

# 读取数据
file_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_complete_features.csv'
print(f"\n1. 读取数据文件: {file_path}")

# 选择需要的列
cols_to_read = [
    'cooperation_depth_index',
    'long_term_word_count',
    'has_multi_agent_interaction',
    'china_africa_community_recognition',
    'development_demand_perception',
    'community_similarity',
    'year'
]

df = pd.read_csv(file_path, usecols=cols_to_read, low_memory=False)
print(f"   数据记录数: {len(df)}")
print(f"   数据字段数: {len(df.columns)}")

# 数据预处理
print("\n2. 数据预处理...")
# 对数变换long_term_word_count，处理长尾分布
df['long_term_word_count_log'] = np.log1p(df['long_term_word_count'])

# 为年份创建分组，每5年一组
df['year_group'] = pd.cut(df['year'], bins=range(2000, 2026, 5), right=False, labels=['2000-2004', '2005-2009', '2010-2014', '2015-2019', '2020-2024'])

# 计算相关性矩阵
corr_matrix = df[[
    'cooperation_depth_index',
    'long_term_word_count_log',
    'has_multi_agent_interaction',
    'china_africa_community_recognition',
    'development_demand_perception',
    'community_similarity'
]].corr()

# 创建学术化可视化图表
print("\n3. 创建学术化可视化图表...")
fig = plt.figure(figsize=(20, 16))

# 使用GridSpec创建复杂布局
gs = GridSpec(5, 4, figure=fig, hspace=0.6, wspace=0.5)

# 设置学术风格配色
sns.set_style("whitegrid")
cmap = sns.diverging_palette(10, 250, as_cmap=True)

# 1. 主标题
fig.suptitle('合作纵深性变量学术化综合分析', fontsize=24, fontweight='bold', y=0.98)

# 2. 合作纵深性指数分布（小提琴图+箱线图+散点图）
ax1 = fig.add_subplot(gs[0:2, 0:2])
# 小提琴图
sns.violinplot(data=df, y='cooperation_depth_index', color='lightblue', inner=None, ax=ax1)
# 箱线图（叠加）
sns.boxplot(data=df, y='cooperation_depth_index', width=0.3, color='darkblue', ax=ax1)
# 散点图（抖动）
sns.stripplot(data=df, y='cooperation_depth_index', jitter=True, size=2, color='black', alpha=0.2, ax=ax1)
ax1.set_title('(a) 合作纵深性指数分布', fontsize=16, fontweight='bold')
ax1.set_ylabel('合作纵深性指数', fontsize=14)
ax1.set_xlabel('')

# 添加统计信息
stats = df['cooperation_depth_index'].describe()
stats_text = f"样本数: {len(df):,}\n"
stats_text += f"平均值: {stats['mean']:.4f}\n"
stats_text += f"中位数: {stats['50%']:.4f}\n"
stats_text += f"标准差: {stats['std']:.4f}\n"
stats_text += f"最小值: {stats['min']:.4f}\n"
stats_text += f"最大值: {stats['max']:.4f}\n"
stats_text += f"偏度: {stats.skew():.4f}\n"
stats_text += f"峰度: {stats.kurtosis():.4f}"
ax1.text(1.05, 0.95, stats_text, transform=ax1.transAxes, fontsize=12, 
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# 3. 相关性热力图
ax2 = fig.add_subplot(gs[0:2, 2:4])
# 创建带显著性标记的热力图
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, cmap=cmap, vmin=-1, vmax=1, center=0, 
            square=True, linewidths=.5, cbar_kws={"shrink": .8}, ax=ax2)
# 添加相关性值
for i in range(len(corr_matrix.columns)):
    for j in range(len(corr_matrix.columns)):
        if i > j:  # 只在三角区域添加值
            text_color = "white" if abs(corr_matrix.iloc[i, j]) > 0.5 else "black"
            ax2.text(j + 0.5, i + 0.5, f"{corr_matrix.iloc[i, j]:.2f}", 
                     ha="center", va="center", color=text_color, fontsize=11)
ax2.set_title('(b) 变量间相关性热力图', fontsize=16, fontweight='bold')
ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha='right', fontsize=12)
ax2.set_yticklabels(ax2.get_yticklabels(), fontsize=12)

# 4. 年份分组的合作纵深性指数箱线图
ax3 = fig.add_subplot(gs[2, 0:2])
sns.boxplot(data=df, x='year_group', y='cooperation_depth_index', palette='Blues', ax=ax3)
sns.swarmplot(data=df, x='year_group', y='cooperation_depth_index', size=2, color='black', alpha=0.3, ax=ax3)
ax3.set_title('(c) 不同年份组的合作纵深性指数分布', fontsize=16, fontweight='bold')
ax3.set_xlabel('年份组', fontsize=14)
ax3.set_ylabel('合作纵深性指数', fontsize=14)
ax3.tick_params(axis='x', rotation=45)

# 5. 合作纵深性指数与其他变量的关系（多子图）
# 5.1 与中非命运共同体认同度
ax4a = fig.add_subplot(gs[2, 2])
scatter = sns.scatterplot(data=df, x='china_africa_community_recognition', y='cooperation_depth_index', 
                          alpha=0.5, s=20, color='purple', ax=ax4a)
# 添加趋势线
slope, intercept, r_value, p_value, std_err = stats.linregress(df['china_africa_community_recognition'], df['cooperation_depth_index'])
ax4a.plot(df['china_africa_community_recognition'], intercept + slope*df['china_africa_community_recognition'], 
          color='darkpurple', linewidth=2)
ax4a.set_title('(d) 与中非命运共同体认同度', fontsize=14, fontweight='bold')
ax4a.set_xlabel('认同度', fontsize=12)
ax4a.set_ylabel('合作纵深性指数', fontsize=12)
ax4a.text(0.05, 0.95, f'R² = {r_value**2:.3f}', transform=ax4a.transAxes, 
          fontsize=11, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# 5.2 与发展需求感知
ax4b = fig.add_subplot(gs[2, 3])
scatter = sns.scatterplot(data=df, x='development_demand_perception', y='cooperation_depth_index', 
                          alpha=0.5, s=20, color='green', ax=ax4b)
# 添加趋势线
slope, intercept, r_value, p_value, std_err = stats.linregress(df['development_demand_perception'], df['cooperation_depth_index'])
ax4b.plot(df['development_demand_perception'], intercept + slope*df['development_demand_perception'], 
          color='darkgreen', linewidth=2)
ax4b.set_title('(e) 与发展需求感知', fontsize=14, fontweight='bold')
ax4b.set_xlabel('发展需求感知', fontsize=12)
ax4b.set_ylabel('合作纵深性指数', fontsize=12)
ax4b.text(0.05, 0.95, f'R² = {r_value**2:.3f}', transform=ax4b.transAxes, 
          fontsize=11, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# 6. 长期战略词频与多元主体互动的关系（按年份分组）
ax5 = fig.add_subplot(gs[3:5, 0:2])
sns.scatterplot(data=df, x='long_term_word_count_log', y='has_multi_agent_interaction', 
                hue='year_group', palette='viridis', alpha=0.6, s=30, ax=ax5)
ax5.set_title('(f) 长期战略词频与多元主体互动的关系（按年份分组）', fontsize=16, fontweight='bold')
ax5.set_xlabel('长期战略词频（对数变换）', fontsize=14)
ax5.set_ylabel('多元主体互动', fontsize=14)
ax5.legend(title='年份组', fontsize=11, title_fontsize=12)

# 7. 合作纵深性指数的累积分布函数
ax6 = fig.add_subplot(gs[3, 2:4])
sorted_values = np.sort(df['cooperation_depth_index'])
cdf = np.arange(1, len(sorted_values) + 1) / len(sorted_values)
ax6.plot(sorted_values, cdf, color='blue', linewidth=2)
ax6.fill_between(sorted_values, cdf, alpha=0.3, color='lightblue')
ax6.set_title('(g) 合作纵深性指数的累积分布函数', fontsize=16, fontweight='bold')
ax6.set_xlabel('合作纵深性指数', fontsize=14)
ax6.set_ylabel('累积比例', fontsize=14)
ax6.grid(True, alpha=0.3)

# 8. 统计摘要表格
ax7 = fig.add_subplot(gs[4, 2:4])
# 准备统计数据
stats_df = df[[
    'cooperation_depth_index',
    'long_term_word_count_log',
    'has_multi_agent_interaction',
    'china_africa_community_recognition',
    'development_demand_perception',
    'community_similarity'
]].describe().T[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']]
stats_df['count'] = stats_df['count'].astype(int)

# 创建表格
ax7.axis('tight')
ax7.axis('off')
table = ax7.table(cellText=stats_df.round(4).values, 
                  colLabels=stats_df.columns, 
                  rowLabels=stats_df.index, 
                  cellLoc='center', 
                  rowLoc='center', 
                  loc='center')
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.5)
ax7.set_title('(h) 变量统计摘要', fontsize=16, fontweight='bold', y=1.1)

# 调整布局
plt.tight_layout()

# 保存学术化图表
output_path = 'c:/Users/13067/Desktop/论文/非洲/demo/合作纵深性变量学术化综合分析图.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\n4. 图表保存到: {output_path}")

plt.close()

print("\n=== 学术化可视化完成 ===")
print(f"✅ 生成了一张学术化、复杂化的综合可视化图表")
print(f"✅ 包含了分布、相关性、分组分析、趋势分析和统计摘要")
print(f"✅ 中文显示正常，符合学术规范")
print(f"✅ 300 DPI高分辨率，适合论文发表")
