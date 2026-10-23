import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

# 设置中文字体和风格
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.style.use('seaborn-v0_8-paper')

# 主函数
def main():
    # 文件路径
    input_file = '清洗数据/sentiment_analyzed_data.csv'
    
    print("正在读取情感分析数据...")
    # 读取数据
    df = pd.read_csv(input_file)
    
    print(f"数据总量: {len(df)} 条")
    
    # 数据预处理
    print("\n正在进行数据预处理...")
    
    # 1. 处理发布时间 - 简化处理，不删除无效数据
    df['parsed_date'] = pd.to_datetime(df['date'], errors='coerce')
    # 保留所有数据，即使日期解析失败
    
    # 2. 计算新闻字数
    df['title_length'] = df['title'].str.len()
    df['summary_length'] = df['summary'].str.len()
    df['total_length'] = df['title_length'] + df['summary_length']
    
    # 3. 处理体裁（category）
    # 清理category字段，提取主要类别
    df['clean_category'] = df['category'].astype(str).str.split('\n').str[0].str.strip()
    
    # 4. 处理信源（source）
    # 只保留出现次数较多的信源，其他归为"其他"
    source_counts = df['source'].value_counts()
    top_sources = source_counts[source_counts >= 10].index.tolist()  # 降低阈值
    df['clean_source'] = df['source'].apply(lambda x: x if x in top_sources else '其他')
    
    # 5. 处理情感得分
    # 使用正确的情感得分列（最后一个sentiment_score列）
    sentiment_cols = [col for col in df.columns if 'sentiment_score' in col]
    if len(sentiment_cols) > 1:
        df['final_sentiment_score'] = df[sentiment_cols[-1]]
    else:
        df['final_sentiment_score'] = df[sentiment_cols[0]]
    
    # 情感标签也使用最后一个
    label_cols = [col for col in df.columns if 'sentiment_label' in col]
    if len(label_cols) > 1:
        df['final_sentiment_label'] = df[label_cols[-1]]
    else:
        df['final_sentiment_label'] = df[label_cols[0]]
    
    print("\n数据预处理完成！")
    print(f"有效数据量: {len(df)} 条")
    
    # 生成可视化图表
    print("\n正在生成可视化图表...")
    
    # 创建一个大图，包含多个子图
    fig = plt.figure(figsize=(20, 24))
    
    # 使用GridSpec创建网格布局
    gs = fig.add_gridspec(6, 2, hspace=0.4, wspace=0.3)
    
    # 1. 样本基本信息
    ax1 = fig.add_subplot(gs[0, :])
    ax1.axis('off')
    
    # 计算基本统计信息
    total_articles = len(df)
    avg_title_length = df['title_length'].mean()
    avg_summary_length = df['summary_length'].mean()
    avg_total_length = df['total_length'].mean()
    unique_sources = df['clean_source'].nunique()
    unique_categories = df['clean_category'].nunique()
    sentiment_counts = df['final_sentiment_label'].value_counts()
    
    # 添加文本信息
    info_text = f"""样本基本信息
    总样本量: {total_articles:,} 条
    平均标题长度: {avg_title_length:.1f} 字符
    平均摘要长度: {avg_summary_length:.1f} 字符
    平均总长度: {avg_total_length:.1f} 字符
    信源数量: {unique_sources} 个
    体裁数量: {unique_categories} 个
    情感分布: 积极 {sentiment_counts.get('positive', 0):,} 条, 中性 {sentiment_counts.get('neutral', 0):,} 条, 消极 {sentiment_counts.get('negative', 0):,} 条
    """
    
    ax1.text(0.5, 0.5, info_text, ha='center', va='center', fontsize=12, fontfamily='SimHei')
    ax1.set_title('样本基本统计信息', fontsize=14, fontweight='bold', fontfamily='SimHei')
    
    # 2. 信源分布（前20个）
    ax2 = fig.add_subplot(gs[1, 0])
    source_dist = df['clean_source'].value_counts().sort_values(ascending=False)
    source_dist.plot(kind='bar', ax=ax2, color='skyblue', edgecolor='black')
    ax2.set_title('信源分布', fontsize=12, fontweight='bold')
    ax2.set_xlabel('信源')
    ax2.set_ylabel('文章数量')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 3. 体裁分布
    ax3 = fig.add_subplot(gs[1, 1])
    category_dist = df['clean_category'].value_counts().sort_values(ascending=False).head(15)  # 只显示前15个
    category_dist.plot(kind='bar', ax=ax3, color='lightgreen', edgecolor='black')
    ax3.set_title('体裁分布', fontsize=12, fontweight='bold')
    ax3.set_xlabel('体裁')
    ax3.set_ylabel('文章数量')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 4. 发布年份分布（如果日期解析成功）
    ax4 = fig.add_subplot(gs[2, :])
    if 'parsed_date' in df.columns:
        df['publish_year'] = df['parsed_date'].dt.year
        year_counts = df['publish_year'].value_counts().sort_index()
        year_counts.plot(kind='bar', ax=ax4, color='blue', edgecolor='black')
        ax4.set_title('发布年份分布', fontsize=12, fontweight='bold')
        ax4.set_xlabel('发布年份')
        ax4.set_ylabel('文章数量')
        ax4.tick_params(axis='x', rotation=0)
        ax4.grid(axis='y', linestyle='--', alpha=0.7)
    else:
        ax4.text(0.5, 0.5, '日期解析失败', ha='center', va='center', fontsize=12)
        ax4.set_title('发布年份分布', fontsize=12, fontweight='bold')
    
    # 5. 情感强度分布
    ax5 = fig.add_subplot(gs[3, 0])
    sns.histplot(df['final_sentiment_score'], bins=30, kde=True, ax=ax5, color='purple', edgecolor='black')
    ax5.set_title('情感强度分布', fontsize=12, fontweight='bold')
    ax5.set_xlabel('情感得分')
    ax5.set_ylabel('文章数量')
    ax5.grid(axis='y', linestyle='--', alpha=0.7)
    ax5.axvline(x=0, color='red', linestyle='--', label='中性')
    ax5.legend()
    
    # 6. 情感标签分布
    ax6 = fig.add_subplot(gs[3, 1])
    sentiment_dist = df['final_sentiment_label'].value_counts()
    sentiment_dist.plot(kind='pie', ax=ax6, autopct='%1.1f%%', startangle=90, 
                        colors=['green', 'gray', 'red'])
    ax6.set_title('情感标签分布', fontsize=12, fontweight='bold')
    ax6.set_ylabel('')
    
    # 7. 标题与摘要字数分布
    ax7 = fig.add_subplot(gs[4, 0])
    sns.boxplot(data=df[['title_length', 'summary_length']].dropna(), ax=ax7, palette='Set2')
    ax7.set_title('标题与摘要字数分布', fontsize=12, fontweight='bold')
    ax7.set_xlabel('文本类型')
    ax7.set_ylabel('字数')
    ax7.grid(axis='y', linestyle='--', alpha=0.7)
    ax7.set_xticklabels(['标题', '摘要'])
    
    # 8. 总字数分布
    ax8 = fig.add_subplot(gs[4, 1])
    sns.histplot(df['total_length'].dropna(), bins=50, kde=True, ax=ax8, color='orange', edgecolor='black')
    ax8.set_title('总字数分布', fontsize=12, fontweight='bold')
    ax8.set_xlabel('总字数')
    ax8.set_ylabel('文章数量')
    ax8.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 9. 不同信源的情感分布
    ax9 = fig.add_subplot(gs[5, 0])
    sns.boxplot(x='clean_source', y='final_sentiment_score', data=df, ax=ax9, palette='Set3')
    ax9.set_title('不同信源的情感分布', fontsize=12, fontweight='bold')
    ax9.set_xlabel('信源')
    ax9.set_ylabel('情感得分')
    ax9.tick_params(axis='x', rotation=45)
    ax9.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 10. 不同体裁的情感分布
    ax10 = fig.add_subplot(gs[5, 1])
    # 只选择主要体裁
    top_categories = df['clean_category'].value_counts()[:10].index.tolist()
    category_sentiment = df[df['clean_category'].isin(top_categories)]
    sns.boxplot(x='clean_category', y='final_sentiment_score', data=category_sentiment, ax=ax10, palette='Set1')
    ax10.set_title('不同体裁的情感分布', fontsize=12, fontweight='bold')
    ax10.set_xlabel('体裁')
    ax10.set_ylabel('情感得分')
    ax10.tick_params(axis='x', rotation=45)
    ax10.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表为PDF文件
    output_path = '清洗数据/sample_visualization.pdf'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n可视化图表已保存到: {output_path}")
    
    # 保存图表为PNG文件（备用）
    output_path_png = '清洗数据/sample_visualization.png'
    plt.savefig(output_path_png, dpi=300, bbox_inches='tight')
    print(f"可视化图表已保存到: {output_path_png}")
    
    # 显示图表
    # plt.show()
    
    print("\n可视化生成完成！")
    print("图表包含以下内容:")
    print("1. 样本基本统计信息")
    print("2. 信源分布")
    print("3. 体裁分布")
    print("4. 发布年份分布")
    print("5. 情感强度分布")
    print("6. 情感标签分布")
    print("7. 标题与摘要字数分布")
    print("8. 总字数分布")
    print("9. 不同信源的情感分布")
    print("10. 不同体裁的情感分布")

if __name__ == "__main__":
    main()
