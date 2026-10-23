import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
import os

# 设置中文字体，确保中文正常显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = ['Microsoft YaHei']

# 创建输出目录
output_dir = 'c:/Users/13067/Desktop/论文/非洲/demo/发展需求分析报告'
os.makedirs(output_dir, exist_ok=True)

# 读取数据
def load_data(file_path):
    print(f"Reading data from {file_path}...")
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"Loaded {len(df)} records")
    return df

# 可视化发展需求感知分布（修复中文显示）
def visualize_distribution_fixed(df, output_dir):
    print("\n=== Creating Visualizations with Fixed Chinese Fonts ===")
    
    # 设置风格
    sns.set_style("whitegrid")
    
    # 1. 直方图
    plt.figure(figsize=(12, 6))
    sns.histplot(df['development_demand_perception'], bins=30, kde=True, color='skyblue')
    # 显式设置所有文本的字体
    plt.title('发展需求感知强度分布直方图', fontsize=16, fontname='Microsoft YaHei')
    plt.xlabel('发展需求感知强度', fontsize=14, fontname='Microsoft YaHei')
    plt.ylabel('频率', fontsize=14, fontname='Microsoft YaHei')
    plt.xticks(fontsize=12, fontname='Microsoft YaHei')
    plt.yticks(fontsize=12, fontname='Microsoft YaHei')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    hist_path = os.path.join(output_dir, '发展需求感知强度分布直方图.png')
    plt.savefig(hist_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Created histogram: {hist_path}")
    
    # 2. 箱线图
    plt.figure(figsize=(10, 6))
    sns.boxplot(y=df['development_demand_perception'], color='lightgreen')
    plt.title('发展需求感知强度箱线图', fontsize=16, fontname='Microsoft YaHei')
    plt.ylabel('发展需求感知强度', fontsize=14, fontname='Microsoft YaHei')
    plt.yticks(fontsize=12, fontname='Microsoft YaHei')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    box_path = os.path.join(output_dir, '发展需求感知强度箱线图.png')
    plt.savefig(box_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Created boxplot: {box_path}")
    
    # 3. 密度图
    plt.figure(figsize=(12, 6))
    sns.kdeplot(df['development_demand_perception'], fill=True, color='purple', alpha=0.6)
    plt.title('发展需求感知强度密度图', fontsize=16, fontname='Microsoft YaHei')
    plt.xlabel('发展需求感知强度', fontsize=14, fontname='Microsoft YaHei')
    plt.ylabel('密度', fontsize=14, fontname='Microsoft YaHei')
    plt.xticks(fontsize=12, fontname='Microsoft YaHei')
    plt.yticks(fontsize=12, fontname='Microsoft YaHei')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    density_path = os.path.join(output_dir, '发展需求感知强度密度图.png')
    plt.savefig(density_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Created density plot: {density_path}")
    
    # 4. 小提琴图
    plt.figure(figsize=(10, 6))
    sns.violinplot(y=df['development_demand_perception'], color='orange', inner='quartile')
    plt.title('发展需求感知强度小提琴图', fontsize=16, fontname='Microsoft YaHei')
    plt.ylabel('发展需求感知强度', fontsize=14, fontname='Microsoft YaHei')
    plt.yticks(fontsize=12, fontname='Microsoft YaHei')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    violin_path = os.path.join(output_dir, '发展需求感知强度小提琴图.png')
    plt.savefig(violin_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Created violin plot: {violin_path}")
    
    # 5. 散点图：关键词密度 vs 局部情感值
    plt.figure(figsize=(12, 6))
    sc = plt.scatter(x=df['development_keyword_density'], y=df['local_sentiment'], 
                   c=df['development_demand_perception'], cmap='viridis', alpha=0.6, s=50)
    plt.title('发展关键词密度 vs 局部情感值', fontsize=16, fontname='Microsoft YaHei')
    plt.xlabel('发展关键词密度', fontsize=14, fontname='Microsoft YaHei')
    plt.ylabel('局部情感值', fontsize=14, fontname='Microsoft YaHei')
    # 设置颜色条
    cbar = plt.colorbar(sc)
    cbar.set_label('发展需求感知强度', fontsize=12, fontname='Microsoft YaHei')
    cbar.ax.tick_params(labelsize=10)
    # 设置颜色条刻度标签字体
    for label in cbar.ax.get_yticklabels():
        label.set_fontname('Microsoft YaHei')
    # 设置坐标轴刻度标签字体
    for label in plt.gca().get_xticklabels():
        label.set_fontname('Microsoft YaHei')
    for label in plt.gca().get_yticklabels():
        label.set_fontname('Microsoft YaHei')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    scatter_path = os.path.join(output_dir, '关键词密度vs局部情感值散点图.png')
    plt.savefig(scatter_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Created scatter plot: {scatter_path}")
    
    return {
        'histogram': hist_path,
        'boxplot': box_path,
        'density_plot': density_path,
        'violin_plot': violin_path,
        'scatter_plot': scatter_path
    }

# 主函数
def main():
    # 文件路径
    file_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception.csv'
    
    # 1. 加载数据
    df = load_data(file_path)
    
    # 2. 创建修复中文显示的可视化
    visualize_distribution_fixed(df, output_dir)
    
    print("\n=== Analysis Completed with Fixed Chinese Fonts ===")
    print(f"All visualizations with fixed Chinese fonts saved to: {output_dir}")

if __name__ == "__main__":
    main()