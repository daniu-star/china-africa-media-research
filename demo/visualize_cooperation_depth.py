import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

print("=== 合作纵深性变量可视化分析 ===")

# 读取数据
file_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_complete_features.csv'
print(f"\n1. 读取数据文件: {file_path}")

# 只选择需要的列，提高读取速度
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

# 创建综合图表
print("\n3. 创建综合可视化图表...")
fig = plt.figure(figsize=(16, 12))

# 使用GridSpec创建复杂布局
gs = GridSpec(3, 3, figure=fig, hspace=0.4, wspace=0.3)

# 1. 合作纵深性指数分布（中心大图）
ax_center = fig.add_subplot(gs[0:2, 0:2])
sns.kdeplot(data=df, x='cooperation_depth_index', fill=True, color='skyblue', alpha=0.7, ax=ax_center)
ax_center.set_title('合作纵深性指数分布', fontsize=16, fontweight='bold')
ax_center.set_xlabel('合作纵深性指数', fontsize=14)
ax_center.set_ylabel('密度', fontsize=14)
ax_center.grid(True, alpha=0.3)

# 添加统计信息
stats = df['cooperation_depth_index'].describe()
stats_text = f"样本数: {len(df):,}\n"
stats_text += f"平均值: {stats['mean']:.4f}\n"
stats_text += f"中位数: {stats['50%']:.4f}\n"
stats_text += f"标准差: {stats['std']:.4f}\n"
stats_text += f"最小值: {stats['min']:.4f}\n"
stats_text += f"最大值: {stats['max']:.4f}\n"
stats_text += f"25%分位数: {stats['25%']:.4f}\n"
stats_text += f"75%分位数: {stats['75%']:.4f}"
ax_center.text(0.85, 0.95, stats_text, transform=ax_center.transAxes, fontsize=12, 
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# 2. 合作纵深性指数与中非命运共同体认同度关系
ax1 = fig.add_subplot(gs[0, 2])
scatter = ax1.scatter(df['china_africa_community_recognition'], df['cooperation_depth_index'], 
                      alpha=0.5, s=10, color='purple')
ax1.set_title('合作纵深性指数与\n中非命运共同体认同度关系', fontsize=12, fontweight='bold')
ax1.set_xlabel('中非命运共同体认同度', fontsize=11)
ax1.set_ylabel('合作纵深性指数', fontsize=11)
ax1.grid(True, alpha=0.3)

# 3. 合作纵深性指数与发展需求感知关系
ax2 = fig.add_subplot(gs[1, 2])
scatter = ax2.scatter(df['development_demand_perception'], df['cooperation_depth_index'], 
                      alpha=0.5, s=10, color='green')
ax2.set_title('合作纵深性指数与\n发展需求感知关系', fontsize=12, fontweight='bold')
ax2.set_xlabel('发展需求感知', fontsize=11)
ax2.set_ylabel('合作纵深性指数', fontsize=11)
ax2.grid(True, alpha=0.3)

# 4. 合作纵深性指数与社区相似度关系
ax3 = fig.add_subplot(gs[2, 0])
scatter = ax3.scatter(df['community_similarity'], df['cooperation_depth_index'], 
                      alpha=0.5, s=10, color='orange')
ax3.set_title('合作纵深性指数与\n社区相似度关系', fontsize=12, fontweight='bold')
ax3.set_xlabel('社区相似度', fontsize=11)
ax3.set_ylabel('合作纵深性指数', fontsize=11)
ax3.grid(True, alpha=0.3)

# 5. 长期战略词频与多元主体互动关系
ax4 = fig.add_subplot(gs[2, 1])
scatter = ax4.scatter(df['long_term_word_count_log'], df['has_multi_agent_interaction'], 
                      alpha=0.5, s=10, color='red')
ax4.set_title('长期战略词频与\n多元主体互动关系', fontsize=12, fontweight='bold')
ax4.set_xlabel('长期战略词频（对数）', fontsize=11)
ax4.set_ylabel('多元主体互动', fontsize=11)
ax4.grid(True, alpha=0.3)

# 6. 年度合作纵深性指数趋势
ax5 = fig.add_subplot(gs[2, 2])
year_avg = df.groupby('year')['cooperation_depth_index'].mean().reset_index()
ax5.plot(year_avg['year'], year_avg['cooperation_depth_index'], marker='o', linewidth=2, color='blue')
ax5.set_title('年度合作纵深性指数趋势', fontsize=12, fontweight='bold')
ax5.set_xlabel('年份', fontsize=11)
ax5.set_ylabel('平均合作纵深性指数', fontsize=11)
ax5.grid(True, alpha=0.3)
ax5.set_xticks(year_avg['year'])
ax5.tick_params(axis='x', rotation=45)

# 调整布局
plt.tight_layout()

# 保存图表
output_path = 'c:/Users/13067/Desktop/论文/非洲/demo/合作纵深性变量综合分析图.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\n4. 图表保存到: {output_path}")

plt.close()

print("\n=== 可视化完成 ===")
print(f"✅ 生成了一张综合可视化图表")
print(f"✅ 涵盖了合作纵深性指数的分布、相关关系和年度趋势")
print(f"✅ 中文显示正常")
