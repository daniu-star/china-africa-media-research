import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
import matplotlib.ticker as ticker

# 设置中文字体，确保中文正常显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 设置结果保存目录
output_dir = 'c:/Users/13067/Desktop/论文/非洲/demo/议题集中度分析结果'
os.makedirs(output_dir, exist_ok=True)

# 读取HHI指数数据
hhi_data = pd.read_csv(os.path.join(output_dir, 'yearly_hhi.csv'))
hhi_data['year'] = pd.to_datetime(hhi_data['year'], format='%Y')
hhi_data.set_index('year', inplace=True)

# 生成年份序列
hhi_data['year_num'] = hhi_data.index.year

# 创建一个复杂、学术、专业的可视化图表
plt.figure(figsize=(12, 8), dpi=300)  # 高分辨率

# 设置背景风格为学术风格
sns.set_style("whitegrid")
sns.set_context("paper", font_scale=1.2)  # 学术论文风格

# 1. 绘制原始数据点（散点图）
plt.scatter(hhi_data['year_num'], hhi_data['hhi_index'], 
            s=100, c='darkblue', alpha=0.8, 
            edgecolor='black', linewidth=1.5, 
            label='Annual HHI Index')

# 2. 绘制折线图，连接各个数据点
plt.plot(hhi_data['year_num'], hhi_data['hhi_index'], 
         color='blue', linestyle='-', linewidth=2, 
         alpha=0.6, label='HHI Trend Line')

# 3. 绘制平滑趋势线（使用低ess方法）
sns.regplot(x='year_num', y='hhi_index', data=hhi_data, 
            scatter=False, lowess=True, 
            color='red', 
            line_kws={'linewidth': 2.5}, 
            label='Lowess Smoothing Trend', 
            ax=plt.gca())

# 4. 计算并绘制95%置信区间
# 使用多项式拟合
z = np.polyfit(hhi_data['year_num'], hhi_data['hhi_index'], 3)
f = np.poly1d(z)

# 生成预测值和置信区间
x_pred = np.linspace(hhi_data['year_num'].min(), hhi_data['year_num'].max(), 100)
y_pred = f(x_pred)

# 计算置信区间
n = hhi_data.shape[0]
p = z.shape[0]
df = n - p

# 计算预测值的标准误差
x_mean = hhi_data['year_num'].mean()
sse = np.sum((hhi_data['hhi_index'] - f(hhi_data['year_num'])) ** 2)
std_err = np.sqrt(sse / df)

# 计算置信区间
confidence = 0.95
t_value = stats.t.ppf((1 + confidence) / 2, df)

# 计算每个预测点的标准误差
sigma_hat = std_err * np.sqrt(1/n + (x_pred - x_mean)**2 / np.sum((hhi_data['year_num'] - x_mean)**2))

# 绘制置信区间
plt.fill_between(x_pred, y_pred - t_value * sigma_hat, 
                y_pred + t_value * sigma_hat, 
                color='gray', alpha=0.2, 
                label=f'{confidence*100}% Confidence Interval')

# 5. 添加学术化的标题和标签
plt.title('Annual Concentration of China-Africa Community of Shared Future Issues (2000-2025)', 
          fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Year', fontsize=14, fontweight='bold', labelpad=15)
plt.ylabel('Herfindahl-Hirschman Index (HHI)', 
           fontsize=14, fontweight='bold', labelpad=15)

# 6. 优化坐标轴
plt.xticks(hhi_data['year_num'], rotation=45, ha='right', fontsize=12)
plt.yticks(fontsize=12)
plt.ylim(0, 0.4)  # 设置y轴范围，突出变化

# 7. 添加网格线，增强可读性
plt.grid(True, linestyle='--', alpha=0.7)

# 8. 添加图例，放置在合适位置
plt.legend(loc='upper right', fontsize=12, 
           frameon=True, framealpha=0.9, 
           borderpad=1, handletextpad=0.5)

# 9. 添加水平参考线，显示平均HHI值
hhi_mean = hhi_data['hhi_index'].mean()
plt.axhline(y=hhi_mean, color='green', linestyle='--', 
            linewidth=2, alpha=0.7, 
            label=f'Mean HHI: {hhi_mean:.4f}')

# 10. 添加数据标签，显示关键年份的HHI值
key_years = [2000, 2010, 2013, 2016, 2020, 2025]
for year in key_years:
    year_data = hhi_data[hhi_data['year_num'] == year]
    if not year_data.empty:
        hhi_value = year_data['hhi_index'].values[0]
        plt.annotate(f'{hhi_value:.4f}', 
                     xy=(year, hhi_value), 
                     xytext=(0, 15),  # 偏移量
                     textcoords='offset points', 
                     ha='center', va='bottom', 
                     fontsize=10, fontweight='bold', 
                     bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.8),
                     arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.2', lw=1.5))

# 11. 添加HHI指数的解释性文本框
plt.text(0.02, 0.02, 
         'HHI Index Interpretation:\n' +
         '• 0-0.15: Low concentration (diverse issues)\n' +
         '• 0.15-0.25: Medium concentration\n' +
         '• 0.25-0.40: High concentration (focused issues)',
         transform=plt.gca().transAxes, 
         fontsize=11, 
         verticalalignment='bottom', 
         bbox=dict(boxstyle='round,pad=0.5', fc='lightgray', alpha=0.9, ec='gray', lw=1))

# 12. 添加趋势解释
plt.text(0.98, 0.98, 
         'Trend Analysis:\n' +
         '• 2000-2009: High concentration\n' +
         '• 2010-2019: Low concentration\n' +
         '• 2020-2025: Moderate concentration',
         transform=plt.gca().transAxes, 
         fontsize=11, 
         verticalalignment='top', 
         horizontalalignment='right',
         bbox=dict(boxstyle='round,pad=0.5', fc='lightyellow', alpha=0.9, ec='gray', lw=1))

# 13. 添加学术论文常用的元素
plt.tight_layout()  # 自动调整布局

# 添加图表编号（学术论文常用）
plt.text(0.01, 0.99, 'Figure 1', 
         transform=plt.gcf().transFigure, 
         fontsize=14, fontweight='bold', 
         verticalalignment='top',
         bbox=dict(boxstyle='square,pad=0.3', fc='white', ec='black', lw=1))

# 14. 保存为高质量图片
output_path = os.path.join(output_dir, '议题集中度_HHI指数趋势分析图_学术版.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight', format='png')

# 创建第二个图表：HHI指数分布直方图与密度图
plt.figure(figsize=(12, 8), dpi=300)

# 1. 绘制直方图
bins = 15
plt.hist(hhi_data['hhi_index'], bins=bins, 
         density=True, alpha=0.6, color='skyblue', 
         edgecolor='black', linewidth=1.2, 
         label=f'HHI Distribution (bins={bins})')

# 2. 绘制核密度估计曲线
sns.kdeplot(hhi_data['hhi_index'], 
            bw_adjust=0.8, 
            color='red', linewidth=2.5, 
            label='Kernel Density Estimation', 
            fill=True, alpha=0.3)

# 3. 添加垂直参考线，显示关键统计量
plt.axvline(hhi_data['hhi_index'].mean(), color='green', linestyle='--', 
            linewidth=2, alpha=0.8, label=f'Mean: {hhi_data["hhi_index"].mean():.4f}')
plt.axvline(hhi_data['hhi_index'].median(), color='orange', linestyle='--', 
            linewidth=2, alpha=0.8, label=f'Median: {hhi_data["hhi_index"].median():.4f}')
plt.axvline(hhi_data['hhi_index'].mode()[0], color='purple', linestyle='--', 
            linewidth=2, alpha=0.8, label=f'Mode: {hhi_data["hhi_index"].mode()[0]:.4f}')

# 4. 添加学术化的标题和标签
plt.title('Distribution of Herfindahl-Hirschman Index (2000-2025)', 
          fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Herfindahl-Hirschman Index (HHI)', 
           fontsize=14, fontweight='bold', labelpad=15)
plt.ylabel('Density', 
           fontsize=14, fontweight='bold', labelpad=15)

# 5. 优化坐标轴
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)

# 6. 添加图例
plt.legend(loc='upper right', fontsize=12, 
           frameon=True, framealpha=0.9, 
           borderpad=1, handletextpad=0.5)

# 7. 添加统计描述
# 使用三重引号构建多行字符串，避免语法错误
stats_text = '''Descriptive Statistics:
• Sample Size: {}
• Mean: {:.4f}
• Median: {:.4f}
• Standard Deviation: {:.4f}
• Minimum: {:.4f}
• Maximum: {:.4f}'''.format(
    len(hhi_data),
    hhi_data["hhi_index"].mean(),
    hhi_data["hhi_index"].median(),
    hhi_data["hhi_index"].std(),
    hhi_data["hhi_index"].min(),
    hhi_data["hhi_index"].max()
)

plt.text(0.02, 0.98, stats_text, 
         transform=plt.gca().transAxes, 
         fontsize=11, 
         verticalalignment='top', 
         bbox=dict(boxstyle='round,pad=0.5', fc='lightgray', alpha=0.9, ec='gray', lw=1))

# 8. 添加图表编号
plt.text(0.01, 0.99, 'Figure 2', 
         transform=plt.gcf().transFigure, 
         fontsize=14, fontweight='bold', 
         verticalalignment='top',
         bbox=dict(boxstyle='square,pad=0.3', fc='white', ec='black', lw=1))

# 9. 保存为高质量图片
output_path2 = os.path.join(output_dir, '议题集中度_HHI指数分布分析图_学术版.png')
plt.savefig(output_path2, dpi=300, bbox_inches='tight', format='png')

print(f"可视化图表已生成并保存到: {output_dir}")
print(f"1. 趋势分析图: {output_path}")
print(f"2. 分布分析图: {output_path2}")

plt.close('all')  # 关闭所有图表窗口
