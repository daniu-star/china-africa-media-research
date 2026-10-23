import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 设置中文字体和样式
# 确保中文能正确显示
import matplotlib.font_manager as fm

# 强制使用SimHei字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 12
plt.rcParams['figure.figsize'] = (12, 8)

# 确保seaborn使用中文字体
sns.set_style("whitegrid")
sns.set_palette("Set2")
sns.set(font="SimHei")

# 检查字体是否可用
try:
    fm.findfont('SimHei')
    print("✅ SimHei字体可用")
except:
    print("⚠️ SimHei字体不可用，尝试其他字体")
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
    sns.set(font="Microsoft YaHei")

# 创建结果目录
result_dir = '变量关系可视化'
os.makedirs(result_dir, exist_ok=True)

print("开始生成变量关系可视化...")

# 1. 读取VIF数据
vif_file = r'c:\Users\13067\Desktop\论文\非洲\demo\变量关系检验\方差膨胀因子VIF.csv'
vif_data = pd.read_csv(vif_file)
print(f"VIF数据读取完成，共 {len(vif_data)} 个变量")

# 2. 读取豪斯曼检验数据
hausman_file = r'c:\Users\13067\Desktop\论文\非洲\demo\变量关系检验\豪斯曼检验结果.txt'
with open(hausman_file, 'r', encoding='utf-8') as f:
    hausman_content = f.read()

# 解析豪斯曼检验结果
hausman_stat = float(hausman_content.split('检验统计量: ')[1].split('\n')[0])
hausman_df = int(hausman_content.split('自由度: ')[1].split('\n')[0])
hausman_pval = float(hausman_content.split('p值: ')[1].split('\n')[0])

print(f"豪斯曼检验结果解析完成: 统计量={hausman_stat:.4f}, 自由度={hausman_df}, p值={hausman_pval:.4f}")

# 3. 生成VIF可视化
print("\n生成VIF可视化...")

# 3.1 水平条形图 - VIF值
plt.figure(figsize=(12, 8))

# 按VIF值排序
sorted_vif = vif_data.sort_values('VIF', ascending=True)

# 绘制条形图
bars = plt.barh(sorted_vif['变量'], sorted_vif['VIF'], color='skyblue')

# 添加VIF值标签
for bar in bars:
    width = bar.get_width()
    plt.text(width + 0.2, bar.get_y() + bar.get_height()/2, 
             f'{width:.2f}', ha='left', va='center', fontweight='bold')

# 添加阈值线
plt.axvline(x=10, color='red', linestyle='--', linewidth=2, label='VIF阈值 (10)')
plt.axvline(x=5, color='orange', linestyle='--', linewidth=1.5, label='VIF警告线 (5)')

# 设置图表属性
plt.title('变量方差膨胀因子 (VIF) 分析', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('VIF值', fontsize=14, labelpad=15)
plt.ylabel('变量名称', fontsize=14, labelpad=15)
plt.xlim(0, max(sorted_vif['VIF']) + 2)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.legend(fontsize=12, loc='lower right')
plt.grid(axis='x', linestyle='--', alpha=0.7)

# 添加统计信息
max_vif = sorted_vif['VIF'].max()
high_vif_vars = sorted_vif[sorted_vif['VIF'] >= 10]['变量'].tolist()
plt.text(0.95, 0.95, f'最大VIF值: {max_vif:.2f}\n高VIF变量: {"、".join(high_vif_vars)}', 
         transform=plt.gca().transAxes, ha='right', va='top', 
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray'),
         fontsize=12)

plt.tight_layout()
vif_bar_path = os.path.join(result_dir, 'VIF水平条形图.png')
plt.savefig(vif_bar_path, dpi=300, bbox_inches='tight')
plt.close()

# 3.2 VIF分布直方图
plt.figure(figsize=(10, 6))
sns.histplot(vif_data['VIF'], bins=15, kde=True, color='purple', alpha=0.7)
plt.axvline(x=10, color='red', linestyle='--', linewidth=2, label='VIF阈值 (10)')
plt.title('VIF值分布直方图', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('VIF值', fontsize=14, labelpad=15)
plt.ylabel('频率', fontsize=14, labelpad=15)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()
vif_hist_path = os.path.join(result_dir, 'VIF分布直方图.png')
plt.savefig(vif_hist_path, dpi=300, bbox_inches='tight')
plt.close()

# 4. 生成豪斯曼检验可视化
print("\n生成豪斯曼检验可视化...")

# 4.1 豪斯曼检验结果展示
plt.figure(figsize=(12, 8))

# 创建子图布局
grid = plt.GridSpec(3, 2, wspace=0.4, hspace=0.3)

# 主标题
plt.suptitle('豪斯曼检验结果分析', fontsize=18, fontweight='bold', y=0.95)

# 子图1: 豪斯曼统计量和p值
ax1 = plt.subplot(grid[0:2, 0])

# 创建数据
stats_data = [hausman_stat, hausman_pval]
labels = ['豪斯曼统计量', 'p值']
colors = ['skyblue', 'salmon']

# 绘制条形图
bars = ax1.bar(labels, stats_data, color=colors, width=0.5)

# 添加数值标签
for bar, value in zip(bars, stats_data):
    height = bar.get_height()
    label = f'{value:.4f}'
    ax1.text(bar.get_x() + bar.get_width()/2, height + 0.05 * max(stats_data), 
             label, ha='center', va='bottom', fontweight='bold', fontsize=12)

# 设置y轴范围
ax1.set_ylim(0, max(stats_data) * 1.2)

# 添加阈值线
if hausman_pval < 0.05:
    ax1.axhline(y=0.05, color='red', linestyle='--', linewidth=1.5, label='显著性水平 (0.05)')

ax1.set_title('豪斯曼检验核心统计量', fontsize=14, fontweight='bold', pad=15)
ax1.tick_params(axis='x', rotation=0, labelsize=12)
ax1.tick_params(axis='y', labelsize=12)
ax1.grid(True, alpha=0.3, axis='y')
ax1.legend(fontsize=11)

# 子图2: 模型选择结论
ax2 = plt.subplot(grid[0:2, 1])

# 创建结论文本
if hausman_pval < 0.05:
    conclusion = "拒绝原假设\n建议使用固定效应模型"
    color = 'green'
    model = '固定效应模型'
else:
    conclusion = "不拒绝原假设\n建议使用随机效应模型"
    color = 'orange'
    model = '随机效应模型'

# 绘制结论卡片
ax2.text(0.5, 0.5, conclusion, ha='center', va='center', fontsize=18, 
         fontweight='bold', color=color, transform=ax2.transAxes)

ax2.set_title('模型选择结论', fontsize=14, fontweight='bold', pad=15)
ax2.axis('off')

# 子图3: 自由度和临界值
ax3 = plt.subplot(grid[2, :])

# 计算卡方分布的临界值
from scipy.stats import chi2
critical_value = chi2.ppf(0.95, hausman_df)

# 创建数据点
x = np.linspace(0, hausman_stat * 1.5, 1000)
y = chi2.pdf(x, hausman_df)

# 绘制卡方分布
ax3.plot(x, y, color='blue', linewidth=2, label=f'卡方分布 (df={hausman_df})')

# 填充拒绝域
ax3.fill_between(x, y, where=(x >= critical_value), color='red', alpha=0.3, label='拒绝域')

# 添加统计量和临界值标记
ax3.axvline(x=hausman_stat, color='green', linestyle='--', linewidth=2, label=f'豪斯曼统计量 ({hausman_stat:.2f})')
ax3.axvline(x=critical_value, color='purple', linestyle='--', linewidth=2, label=f'临界值 ({critical_value:.2f})')

ax3.set_title('卡方分布与拒绝域', fontsize=14, fontweight='bold', pad=15)
ax3.set_xlabel('卡方值', fontsize=12, labelpad=10)
ax3.set_ylabel('概率密度', fontsize=12, labelpad=10)
ax3.tick_params(labelsize=11)
ax3.grid(True, alpha=0.3)
ax3.legend(fontsize=11, loc='upper right')

plt.tight_layout()
hausman_path = os.path.join(result_dir, '豪斯曼检验结果可视化.png')
plt.savefig(hausman_path, dpi=300, bbox_inches='tight')
plt.close()

# 5. 生成组合可视化 - VIF与模型选择的关系
print("\n生成组合可视化...")

plt.figure(figsize=(15, 10))

# 5.1 VIF和模型选择组合图
grid = plt.GridSpec(2, 2, wspace=0.3, hspace=0.4)

# 子图1: VIF条形图 (垂直)
ax1 = plt.subplot(grid[0, :])
sorted_vif_desc = vif_data.sort_values('VIF', ascending=False)
bars = ax1.bar(sorted_vif_desc['变量'], sorted_vif_desc['VIF'], color='lightgreen')
ax1.axhline(y=10, color='red', linestyle='--', linewidth=2, label='VIF阈值 (10)')
ax1.set_title('变量多重共线性分析 (VIF)', fontsize=16, fontweight='bold', pad=20)
ax1.set_xlabel('变量', fontsize=14, labelpad=15)
ax1.set_ylabel('VIF值', fontsize=14, labelpad=15)
ax1.set_xticklabels(sorted_vif_desc['变量'], rotation=45, ha='right', fontsize=11)
ax1.tick_params(axis='y', labelsize=12)
ax1.legend(fontsize=12)
ax1.grid(True, alpha=0.3, axis='y')

# 子图2: 豪斯曼检验结果摘要
ax2 = plt.subplot(grid[1, 0])

# 创建摘要文本
summary_text = f"""
豪斯曼检验结果
=================
检验统计量: {hausman_stat:.4f}
自由度: {hausman_df}
p值: {hausman_pval:.4f}
显著性水平: 0.05

结论: {'拒绝' if hausman_pval < 0.05 else '不拒绝'}原假设
建议模型: {model}

模型选择依据:
- 固定效应模型: 控制个体异质性
- 随机效应模型: 假设个体效应与自变量无关

共线性影响:
- 高VIF变量: {', '.join(high_vif_vars)}
- 建议: 考虑变量筛选或降维
"""

ax2.text(0.05, 0.95, summary_text, ha='left', va='top', fontsize=12, 
         family='Times New Roman', linespacing=1.5)
ax2.set_title('模型选择分析摘要', fontsize=14, fontweight='bold', pad=15)
ax2.axis('off')

# 子图3: 系数比较 (固定效应 vs 随机效应)
ax3 = plt.subplot(grid[1, 1])

# 解析系数数据
coef_data = {
    '变量': ['const', 'cooperation_willingness_advanced', 'development_demand_pca', 
            'time_index', 'total_words_count', 'normalized_sentiment'],
    '固定效应': [-0.071381, 0.240197, 0.054956, -0.024684, 0.000003, 0.748784],
    '随机效应': [-0.068100, 0.243688, 0.056248, -0.026250, 0.000001, 0.747159]
}

coef_df = pd.DataFrame(coef_data)

# 绘制系数比较图
x = np.arange(len(coef_df['变量']))
width = 0.35

bars1 = ax3.bar(x - width/2, coef_df['固定效应'], width, label='固定效应模型', color='skyblue')
bars2 = ax3.bar(x + width/2, coef_df['随机效应'], width, label='随机效应模型', color='salmon')

# 添加系数标签
for i, (fe, re) in enumerate(zip(coef_df['固定效应'], coef_df['随机效应'])):
    ax3.text(i - width/2, fe + 0.01, f'{fe:.4f}', ha='center', va='bottom', fontsize=9, rotation=45)
    ax3.text(i + width/2, re + 0.01, f'{re:.4f}', ha='center', va='bottom', fontsize=9, rotation=45)

ax3.set_title('固定效应与随机效应系数比较', fontsize=14, fontweight='bold', pad=15)
ax3.set_xlabel('变量', fontsize=12, labelpad=10)
ax3.set_ylabel('系数值', fontsize=12, labelpad=10)
ax3.set_xticks(x)
ax3.set_xticklabels(coef_df['变量'], rotation=45, ha='right', fontsize=10)
ax3.legend(fontsize=11)
ax3.grid(True, alpha=0.3, axis='y')

plt.suptitle('变量关系检验综合分析', fontsize=18, fontweight='bold', y=0.98)
plt.tight_layout()
combined_path = os.path.join(result_dir, '变量关系检验综合分析.png')
plt.savefig(combined_path, dpi=300, bbox_inches='tight')
plt.close()

print("\n所有可视化生成完成！")
print(f"生成的文件:")
print(f"1. {vif_bar_path}")
print(f"2. {vif_hist_path}")
print(f"3. {hausman_path}")
print(f"4. {combined_path}")
print(f"\n可视化结果已保存到 {result_dir} 目录")
