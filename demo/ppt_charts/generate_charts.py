import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 学术配色定义
BG_COLOR = '#F5F5F0'
DEEP_BLUE = '#1E3A5F'
MEDIUM_BLUE = '#4A6FA5'
TECH_GREEN = '#2E8B57'
AMBER_GOLD = '#D4A574'
CORAL_RED = '#C75B5B'

OUTPUT_DIR = r'c:\Users\13067\Desktop\论文\非洲\demo\ppt_charts'

# ============================================
# 图表1: 区域异质性柱状图 (水平)
# ============================================
fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
fig.patch.set_facecolor(BG_COLOR)
ax.set_facecolor(BG_COLOR)

regions = ['北非', '南非', '中非', '东非']
coefficients = [-0.060, -0.046, 0.0007, 0.00]
colors = [CORAL_RED, AMBER_GOLD, MEDIUM_BLUE, TECH_GREEN]

bars = ax.barh(regions, coefficients, color=colors, height=0.55, edgecolor='white', linewidth=0.8)

# 添加数值标签
for bar, coef in zip(bars, coefficients):
    width = bar.get_width()
    label_x = width + 0.003 if width >= 0 else width - 0.003
    ha = 'left' if width >= 0 else 'right'
    label_text = f'{coef:.3f}' if coef != 0 else '0.00 (基准)'
    ax.text(label_x, bar.get_y() + bar.get_height()/2, label_text,
            va='center', ha=ha, fontsize=11, fontweight='bold', color=DEEP_BLUE)

# 添加零线
ax.axvline(x=0, color=DEEP_BLUE, linewidth=0.8, linestyle='-')

# 设置标题和标签
ax.set_title('固定效应回归系数：区域异质性', fontsize=14, fontweight='bold', color=DEEP_BLUE, pad=15)
ax.set_xlabel('回归系数', fontsize=11, color=DEEP_BLUE)
ax.tick_params(axis='both', labelsize=11, colors=DEEP_BLUE)

# 移除顶部和右侧边框
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color(DEEP_BLUE)
ax.spines['bottom'].set_color(DEEP_BLUE)

# 添加注释
ax.text(0.02, 0.02, '注：东非为基准组', transform=ax.transAxes, fontsize=9,
        color=DEEP_BLUE, style='italic', alpha=0.8)

# 设置x轴范围
ax.set_xlim(-0.08, 0.02)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'regional_heterogeneity.png'), dpi=300, bbox_inches='tight',
            facecolor=BG_COLOR, edgecolor='none')
plt.close()

# ============================================
# 图表2: 六大簇群环形图
# ============================================
fig, ax = plt.subplots(figsize=(8, 7), dpi=300)
fig.patch.set_facecolor(BG_COLOR)
ax.set_facecolor(BG_COLOR)

labels = ['情感积极型', '合作意愿强烈型', '发展需求主导型', '综合平衡型', '谨慎观察型', '多元复杂型']
sizes = [25, 20, 15, 15, 15, 10]
colors_donut = [TECH_GREEN, MEDIUM_BLUE, AMBER_GOLD, '#7BA3C8', '#8FB996', '#B8A9C9']
explode = (0.03, 0.03, 0.03, 0.03, 0.03, 0.03)

wedges, texts, autotexts = ax.pie(
    sizes, labels=None, colors=colors_donut, autopct='%1.0f%%',
    startangle=90, pctdistance=0.78, explode=explode,
    wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2),
    textprops=dict(fontsize=10, color=DEEP_BLUE, fontweight='bold')
)

# 美化百分比标签
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(9)
    autotext.set_fontweight('bold')

# 添加中心圆（甜甜圈效果）
centre_circle = plt.Circle((0, 0), 0.45, fc=BG_COLOR, ec='none')
ax.add_artist(centre_circle)

# 中心文字
ax.text(0, 0.06, '非洲媒体', ha='center', va='center', fontsize=13, fontweight='bold', color=DEEP_BLUE)
ax.text(0, -0.08, '簇群分布', ha='center', va='center', fontsize=13, fontweight='bold', color=DEEP_BLUE)

# 图例
legend = ax.legend(wedges, [f'{l} ({s}%)' for l, s in zip(labels, sizes)],
                   loc='center left', bbox_to_anchor=(1.02, 0.5),
                   fontsize=10, frameon=False, labelcolor=DEEP_BLUE)

ax.set_title('非洲媒体六大簇群分布', fontsize=14, fontweight='bold', color=DEEP_BLUE, pad=20)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'cluster_doughnut.png'), dpi=300, bbox_inches='tight',
            facecolor=BG_COLOR, edgecolor='none')
plt.close()

# ============================================
# 图表3: 中介效应分解柱状图 (垂直)
# ============================================
fig, ax = plt.subplots(figsize=(7, 5.5), dpi=300)
fig.patch.set_facecolor(BG_COLOR)
ax.set_facecolor(BG_COLOR)

categories = ['直接效应', '间接效应', '总效应']
values = [0.044, 0.589, 0.633]
colors_bar = [AMBER_GOLD, TECH_GREEN, DEEP_BLUE]

bars = ax.bar(categories, values, color=colors_bar, width=0.55, edgecolor='white', linewidth=1.2)

# 添加数值标签
for bar, val in zip(bars, values):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.015,
            f'{val:.3f}', ha='center', va='bottom', fontsize=12, fontweight='bold', color=DEEP_BLUE)

# 设置标题和标签
ax.set_title('Bootstrap中介效应分解', fontsize=14, fontweight='bold', color=DEEP_BLUE, pad=15)
ax.set_ylabel('效应值', fontsize=11, color=DEEP_BLUE)
ax.tick_params(axis='both', labelsize=11, colors=DEEP_BLUE)

# 移除顶部和右侧边框
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color(DEEP_BLUE)
ax.spines['bottom'].set_color(DEEP_BLUE)

# 添加注释
ax.text(0.98, 0.95, '中介效应占比：93.04%', transform=ax.transAxes, fontsize=10,
        color=DEEP_BLUE, ha='right', va='top', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=DEEP_BLUE, alpha=0.7))

# 设置y轴范围
ax.set_ylim(0, 0.75)

# 添加网格线
ax.yaxis.grid(True, linestyle='--', alpha=0.4, color=DEEP_BLUE)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'mediation_decomposition.png'), dpi=300, bbox_inches='tight',
            facecolor=BG_COLOR, edgecolor='none')
plt.close()

print("所有图表已成功生成！")
print(f"输出目录: {OUTPUT_DIR}")
