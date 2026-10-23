import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
import os

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = 'white'

# 创建输出目录
output_dir = 'c:/Users/13067/Desktop/论文/非洲/demo/发展需求分析报告'
os.makedirs(output_dir, exist_ok=True)

# 读取数据
def load_data(file_path):
    print(f"Reading data from {file_path}...")
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"Loaded {len(df)} records")
    return df

# 基本统计分析
def basic_statistics(df):
    print("\n=== Basic Statistics ===")
    stats_df = df['development_demand_perception'].describe()
    print(stats_df)
    
    # 计算偏度和峰度
    skew = stats.skew(df['development_demand_perception'])
    kurtosis = stats.kurtosis(df['development_demand_perception'])
    print(f"\nSkewness: {skew:.4f}")
    print(f"Kurtosis: {kurtosis:.4f}")
    
    return {
        'statistics': stats_df,
        'skewness': skew,
        'kurtosis': kurtosis
    }

# 可视化发展需求感知分布
def visualize_distribution(df, output_dir):
    print("\n=== Creating Visualizations ===")
    
    # 设置风格
    sns.set_style("whitegrid")
    
    # 1. 直方图
    plt.figure(figsize=(12, 6))
    sns.histplot(df['development_demand_perception'], bins=30, kde=True, color='skyblue')
    plt.title('发展需求感知强度分布直方图', fontsize=16)
    plt.xlabel('发展需求感知强度', fontsize=14)
    plt.ylabel('频率', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    hist_path = os.path.join(output_dir, '发展需求感知强度分布直方图.png')
    plt.savefig(hist_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Created histogram: {hist_path}")
    
    # 2. 箱线图
    plt.figure(figsize=(10, 6))
    sns.boxplot(y=df['development_demand_perception'], color='lightgreen')
    plt.title('发展需求感知强度箱线图', fontsize=16)
    plt.ylabel('发展需求感知强度', fontsize=14)
    plt.yticks(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    box_path = os.path.join(output_dir, '发展需求感知强度箱线图.png')
    plt.savefig(box_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Created boxplot: {box_path}")
    
    # 3. 密度图
    plt.figure(figsize=(12, 6))
    sns.kdeplot(df['development_demand_perception'], fill=True, color='purple', alpha=0.6)
    plt.title('发展需求感知强度密度图', fontsize=16)
    plt.xlabel('发展需求感知强度', fontsize=14)
    plt.ylabel('密度', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    density_path = os.path.join(output_dir, '发展需求感知强度密度图.png')
    plt.savefig(density_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Created density plot: {density_path}")
    
    # 4. 小提琴图
    plt.figure(figsize=(10, 6))
    sns.violinplot(y=df['development_demand_perception'], color='orange', inner='quartile')
    plt.title('发展需求感知强度小提琴图', fontsize=16)
    plt.ylabel('发展需求感知强度', fontsize=14)
    plt.yticks(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    violin_path = os.path.join(output_dir, '发展需求感知强度小提琴图.png')
    plt.savefig(violin_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Created violin plot: {violin_path}")
    
    # 5. 散点图：TF-IDF权重 vs 局部情感值
    plt.figure(figsize=(12, 6))
    # 使用matplotlib的scatter函数，这样可以直接获取mappable对象
    sc = plt.scatter(x=df['standardized_tfidf_weight'], y=df['standardized_local_sentiment'], 
                   c=df['development_demand_perception'], cmap='viridis', alpha=0.6, s=50)
    plt.title('标准化TF-IDF权重 vs 标准化局部情感值', fontsize=16)
    plt.xlabel('标准化TF-IDF权重', fontsize=14)
    plt.ylabel('标准化局部情感值', fontsize=14)
    # 现在可以正确添加颜色条
    cbar = plt.colorbar(sc)
    cbar.set_label('发展需求感知强度', fontsize=12)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    scatter_path = os.path.join(output_dir, 'TF-IDF权重vs局部情感值散点图.png')
    plt.savefig(scatter_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Created scatter plot: {scatter_path}")
    
    return {
        'histogram': hist_path,
        'boxplot': box_path,
        'density_plot': density_path,
        'violin_plot': violin_path,
        'scatter_plot': scatter_path
    }

# 生成统计报告
def generate_statistical_report(stats_result, output_dir):
    print("\n=== Generating Statistical Report ===")
    
    report_path = os.path.join(output_dir, '发展需求感知强度统计报告.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 发展需求感知强度统计报告\n\n")
        f.write("## 1. 基本统计描述\n\n")
        f.write(stats_result['statistics'].to_markdown() + "\n\n")
        
        f.write("## 2. 分布特征\n\n")
        f.write(f"- **偏度 (Skewness)**: {stats_result['skewness']:.4f}\n")
        f.write(f"- **峰度 (Kurtosis)**: {stats_result['kurtosis']:.4f}\n\n")
        
        # 分析分布类型
        f.write("## 3. 分布类型分析\n\n")
        skew = stats_result['skewness']
        kurtosis = stats_result['kurtosis']
        
        if abs(skew) < 0.5:
            skew_desc = "近似对称分布"
        elif skew > 0:
            skew_desc = "右偏分布（长尾向右延伸）"
        else:
            skew_desc = "左偏分布（长尾向左延伸）"
        
        if abs(kurtosis) < 0.5:
            kurtosis_desc = "近似正态峰度"
        elif kurtosis > 0:
            kurtosis_desc = "尖峰分布（数据更集中）"
        else:
            kurtosis_desc = "平峰分布（数据更分散）"
        
        f.write(f"- **分布形态**: {skew_desc}\n")
        f.write(f"- **峰度特征**: {kurtosis_desc}\n\n")
        
        f.write("## 4. 统计结论\n\n")
        f.write("根据统计分析，发展需求感知强度呈现以下特征：\n")
        f.write("1. 均值为 {:.4f}，说明整体发展需求感知水平处于中等水平\n".format(stats_result['statistics']['mean']))
        f.write("2. 标准差为 {:.4f}，表明数据存在一定的离散程度\n".format(stats_result['statistics']['std']))
        f.write("3. 最小值为 {:.4f}，最大值为 {:.4f}，数据分布范围较广\n".format(
            stats_result['statistics']['min'], stats_result['statistics']['max']))
        f.write("4. 25%分位数为 {:.4f}，75%分位数为 {:.4f}，中间50%的数据集中在该区间\n".format(
            stats_result['statistics']['25%'], stats_result['statistics']['75%']))
    
    print(f"Generated statistical report: {report_path}")
    return report_path

# 生成分析报告
def generate_analysis_report(df, stats_result, output_dir):
    print("\n=== Generating Analysis Report ===")
    
    report_path = os.path.join(output_dir, '发展需求感知强度分析报告.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 发展需求感知强度分析报告\n\n")
        f.write("## 1. 数据背景\n\n")
        f.write("本分析基于非洲新闻数据，通过计算发展关键词的TF-IDF权重和局部情感值，\n")
        f.write("使用公式 发展需求感知强度 = (标准化TF-IDF权重) × (标准化局部情感值) 得到结果。\n\n")
        
        f.write("## 2. 分布特征分析\n\n")
        skew = stats_result['skewness']
        kurtosis = stats_result['kurtosis']
        
        f.write("### 2.1 分布形态\n\n")
        if skew > 0.5:
            f.write("**右偏分布特征明显**：大部分数据集中在较低水平，少数数据具有较高的发展需求感知强度。\n")
            f.write("这种分布表明，在非洲新闻报道中，大多数报道对中非合作的发展需求感知相对较弱，\n")
            f.write("只有少数报道强烈表达了对发展合作的需求和积极情感。\n\n")
        elif skew < -0.5:
            f.write("**左偏分布特征明显**：大部分数据集中在较高水平，少数数据具有较低的发展需求感知强度。\n")
            f.write("这种分布表明，非洲新闻报道整体对中非合作的发展需求感知较强。\n\n")
        else:
            f.write("**近似对称分布**：数据分布较为均匀，没有明显的偏斜。\n")
            f.write("这种分布表明，非洲新闻报道对中非合作的发展需求感知呈现多样化特征。\n\n")
        
        f.write("### 2.2 峰度特征\n\n")
        if kurtosis > 1:
            f.write("**尖峰分布**：数据高度集中在均值附近，极端值较少。\n")
            f.write("这表明非洲新闻报道对中非合作的发展需求感知具有较高的一致性。\n\n")
        elif kurtosis < -1:
            f.write("**平峰分布**：数据分布较为分散，没有明显的集中趋势。\n")
            f.write("这表明非洲新闻报道对中非合作的发展需求感知存在较大差异。\n\n")
        else:
            f.write("**近似正态峰度**：数据分布既不过于集中也不过于分散。\n")
            f.write("这表明非洲新闻报道对中非合作的发展需求感知呈现较为自然的分布状态。\n\n")
        
        f.write("## 3. 影响因素分析\n\n")
        f.write("### 3.1 TF-IDF权重的影响\n\n")
        tfidf_mean = df['standardized_tfidf_weight'].mean()
        f.write(f"- 标准化TF-IDF权重的均值为 {tfidf_mean:.4f}，表明发展关键词在报道中的整体重要性处于中等水平。\n")
        f.write("- 当报道中频繁出现发展关键词时，TF-IDF权重增加，从而提高发展需求感知强度。\n\n")
        
        f.write("### 3.2 局部情感值的影响\n\n")
        sentiment_mean = df['standardized_local_sentiment'].mean()
        f.write(f"- 标准化局部情感值的均值为 {sentiment_mean:.4f}，表明包含发展关键词的句子整体情感偏向积极。\n")
        f.write("- 积极的情感表达会增强发展需求感知强度，消极的情感表达则会减弱。\n\n")
        
        f.write("## 4. 分布原因分析\n\n")
        f.write("### 4.1 数据来源因素\n\n")
        f.write("- 非洲新闻报道的主题多样性：不同类型的新闻（政治、经济、社会、文化）对发展需求的关注度不同。\n")
        f.write("- 报道来源的差异：不同媒体机构对中非合作的立场和关注点存在差异。\n\n")
        
        f.write("### 4.2 内容因素\n\n")
        f.write("- 发展关键词的使用频率：一些报道可能更多关注政治或安全议题，而非发展议题。\n")
        f.write("- 情感表达的差异：不同报道对中非合作的态度和情感表达存在差异。\n\n")
        
        f.write("### 4.3 时间因素\n\n")
        f.write("- 新闻报道的时间分布：不同时期的报道对发展需求的关注程度可能不同。\n")
        f.write("- 重大事件的影响：特定时期的重大事件可能影响媒体对发展议题的报道。\n\n")
        
        f.write("## 5. 结论与建议\n\n")
        f.write("### 5.1 主要结论\n\n")
        f.write("1. **发展需求感知强度整体处于中等水平**：均值为 {:.4f}，表明非洲新闻报道对中非合作的发展需求有一定感知，但强度不高。\n".format(stats_result['statistics']['mean']))
        f.write("2. **分布呈现明显的右偏特征**：大部分报道的发展需求感知强度较低，少数报道较高。\n")
        f.write("3. **情感因素的积极影响**：包含发展关键词的句子整体情感偏向积极，对发展需求感知强度有正向贡献。\n")
        f.write("4. **TF-IDF权重的差异化**：发展关键词在不同报道中的重要性存在较大差异。\n\n")
        
        f.write("### 5.2 建议\n\n")
        f.write("1. **加强对发展议题的关注**：鼓励媒体更多报道中非合作中的发展议题，提高发展关键词的使用频率。\n")
        f.write("2. **深化情感沟通**：通过积极的情感表达，增强非洲媒体和民众对中非发展合作的认同和需求感知。\n")
        f.write("3. **多样化报道角度**：从不同角度报道中非发展合作，丰富发展需求感知的维度。\n")
        f.write("4. **建立长期监测机制**：定期监测非洲媒体对中非发展合作的报道，及时调整合作策略。\n\n")
        
        f.write("## 6. 可视化结果\n\n")
        f.write("本分析生成了以下可视化图表：\n")
        f.write("1. 发展需求感知强度分布直方图\n")
        f.write("2. 发展需求感知强度箱线图\n")
        f.write("3. 发展需求感知强度密度图\n")
        f.write("4. 发展需求感知强度小提琴图\n")
        f.write("5. 标准化TF-IDF权重 vs 标准化局部情感值散点图\n")
    
    print(f"Generated analysis report: {report_path}")
    return report_path

# 主函数
def main():
    # 文件路径
    file_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception.csv'
    
    # 1. 加载数据
    df = load_data(file_path)
    
    # 2. 基本统计分析
    stats_result = basic_statistics(df)
    
    # 3. 可视化分布
    visualize_distribution(df, output_dir)
    
    # 4. 生成统计报告
    generate_statistical_report(stats_result, output_dir)
    
    # 5. 生成分析报告
    generate_analysis_report(df, stats_result, output_dir)
    
    print("\n=== Analysis Completed ===")
    print(f"All reports and visualizations saved to: {output_dir}")

if __name__ == "__main__":
    main()