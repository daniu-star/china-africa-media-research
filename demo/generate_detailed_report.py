import pandas as pd
from datetime import datetime
import numpy as np

# 主函数
def main():
    # 文件路径
    input_file = '清洗数据/sentiment_analyzed_data.csv'
    output_file = '清洗数据/detailed_sample_report.md'
    
    print("正在读取情感分析数据...")
    # 读取数据
    df = pd.read_csv(input_file)
    
    print(f"数据总量: {len(df)} 条")
    
    # 数据预处理
    print("\n正在进行数据预处理...")
    
    # 1. 处理发布时间
    df['parsed_date'] = pd.to_datetime(df['date'], errors='coerce')
    df['publish_year'] = df['parsed_date'].dt.year
    df['publish_month'] = df['parsed_date'].dt.month
    
    # 2. 计算新闻字数
    df['title_length'] = df['title'].str.len()
    df['summary_length'] = df['summary'].str.len()
    df['total_length'] = df['title_length'] + df['summary_length']
    
    # 3. 处理体裁（category）
    df['clean_category'] = df['category'].astype(str).str.split('\n').str[0].str.strip()
    
    # 4. 处理信源（source）
    source_counts = df['source'].value_counts()
    
    # 5. 处理情感得分
    sentiment_cols = [col for col in df.columns if 'sentiment_score' in col]
    if len(sentiment_cols) > 1:
        df['final_sentiment_score'] = df[sentiment_cols[-1]]
    else:
        df['final_sentiment_score'] = df[sentiment_cols[0]]
    
    label_cols = [col for col in df.columns if 'sentiment_label' in col]
    if len(label_cols) > 1:
        df['final_sentiment_label'] = df[label_cols[-1]]
    else:
        df['final_sentiment_label'] = df[label_cols[0]]
    
    print("\n数据预处理完成！")
    print(f"有效数据量: {len(df)} 条")
    
    # 生成详细报告
    print("\n正在生成详细报告...")
    
    report = "# 样本数据详细报告\n\n"
    
    # 1. 样本基本信息
    report += "## 1. 样本基本信息\n\n"
    total_articles = len(df)
    avg_title_length = df['title_length'].mean()
    avg_summary_length = df['summary_length'].mean()
    avg_total_length = df['total_length'].mean()
    unique_sources = df['source'].nunique()
    unique_categories = df['clean_category'].nunique()
    sentiment_counts = df['final_sentiment_label'].value_counts()
    
    report += f"- 总样本量: {total_articles:,} 条\n"
    report += f"- 平均标题长度: {avg_title_length:.1f} 字符\n"
    report += f"- 平均摘要长度: {avg_summary_length:.1f} 字符\n"
    report += f"- 平均总长度: {avg_total_length:.1f} 字符\n"
    report += f"- 信源数量: {unique_sources} 个\n"
    report += f"- 体裁数量: {unique_categories} 个\n"
    report += f"- 积极情感报道: {sentiment_counts.get('positive', 0):,} 条 ({sentiment_counts.get('positive', 0)/total_articles*100:.1f}%)\n"
    report += f"- 中性情感报道: {sentiment_counts.get('neutral', 0):,} 条 ({sentiment_counts.get('neutral', 0)/total_articles*100:.1f}%)\n"
    report += f"- 消极情感报道: {sentiment_counts.get('negative', 0):,} 条 ({sentiment_counts.get('negative', 0)/total_articles*100:.1f}%)\n\n"
    
    # 2. 信源分布分析
    report += "## 2. 信源分布分析\n\n"
    report += "### 2.1 主要信源（发文量前20）\n\n"
    top_sources = source_counts.head(20)
    for source, count in top_sources.items():
        report += f"- {source}: {count:,} 条 ({count/total_articles*100:.1f}%)\n"
    
    report += f"\n### 2.2 信源发文量分布\n\n"
    report += f"- 发文量≥100的信源: {len(source_counts[source_counts>=100])} 个\n"
    report += f"- 发文量10-99的信源: {len(source_counts[(source_counts>=10) & (source_counts<100)])} 个\n"
    report += f"- 发文量1-9的信源: {len(source_counts[source_counts<10])} 个\n\n"
    
    # 3. 发布时间分析
    report += "## 3. 发布时间分析\n\n"
    
    # 年份分布
    report += "### 3.1 发布年份分布\n\n"
    year_counts = df['publish_year'].value_counts().sort_index()
    for year, count in year_counts.items():
        if pd.notna(year):
            report += f"- {int(year)}: {count:,} 条 ({count/total_articles*100:.1f}%)\n"
    
    # 月份分布
    report += "\n### 3.2 发布月份分布\n\n"
    month_counts = df['publish_month'].value_counts().sort_index()
    for month, count in month_counts.items():
        if pd.notna(month):
            report += f"- 月份 {int(month)}: {count:,} 条 ({count/total_articles*100:.1f}%)\n"
    
    # 4. 情感分析
    report += "## 4. 情感分析\n\n"
    
    # 情感得分统计
    report += "### 4.1 情感得分统计\n\n"
    sentiment_stats = df['final_sentiment_score'].describe()
    report += f"- 平均情感得分: {sentiment_stats['mean']:.3f}\n"
    report += f"- 情感得分标准差: {sentiment_stats['std']:.3f}\n"
    report += f"- 情感得分最小值: {sentiment_stats['min']:.3f}\n"
    report += f"- 情感得分25%分位数: {sentiment_stats['25%']:.3f}\n"
    report += f"- 情感得分中位数: {sentiment_stats['50%']:.3f}\n"
    report += f"- 情感得分75%分位数: {sentiment_stats['75%']:.3f}\n"
    report += f"- 情感得分最大值: {sentiment_stats['max']:.3f}\n"
    
    # 不同信源的情感分析
    report += "\n### 4.2 主要信源情感倾向\n\n"
    # 只分析发文量≥50的信源
    major_sources = source_counts[source_counts>=50].index.tolist()
    for source in major_sources:
        source_df = df[df['source'] == source]
        avg_sentiment = source_df['final_sentiment_score'].mean()
        report += f"- {source}: 平均情感得分 {avg_sentiment:.3f}\n"
    
    # 5. 文本特征分析
    report += "## 5. 文本特征分析\n\n"
    
    # 标题字数分布
    report += "### 5.1 标题字数分布\n\n"
    title_stats = df['title_length'].describe()
    report += f"- 平均标题字数: {title_stats['mean']:.1f}\n"
    report += f"- 标题字数标准差: {title_stats['std']:.1f}\n"
    report += f"- 最短标题: {title_stats['min']:.0f} 字符\n"
    report += f"- 标题字数25%分位数: {title_stats['25%']:.0f} 字符\n"
    report += f"- 标题字数中位数: {title_stats['50%']:.0f} 字符\n"
    report += f"- 标题字数75%分位数: {title_stats['75%']:.0f} 字符\n"
    report += f"- 最长标题: {title_stats['max']:.0f} 字符\n"
    
    # 摘要字数分布
    report += "\n### 5.2 摘要字数分布\n\n"
    summary_stats = df['summary_length'].describe()
    report += f"- 平均摘要字数: {summary_stats['mean']:.1f}\n"
    report += f"- 摘要字数标准差: {summary_stats['std']:.1f}\n"
    report += f"- 最短摘要: {summary_stats['min']:.0f} 字符\n"
    report += f"- 摘要字数25%分位数: {summary_stats['25%']:.0f} 字符\n"
    report += f"- 摘要字数中位数: {summary_stats['50%']:.0f} 字符\n"
    report += f"- 摘要字数75%分位数: {summary_stats['75%']:.0f} 字符\n"
    report += f"- 最长摘要: {summary_stats['max']:.0f} 字符\n"
    
    # 总字数分布
    report += "\n### 5.3 总字数分布\n\n"
    total_stats = df['total_length'].describe()
    report += f"- 平均总字数: {total_stats['mean']:.1f}\n"
    report += f"- 总字数标准差: {total_stats['std']:.1f}\n"
    report += f"- 最短总字数: {total_stats['min']:.0f} 字符\n"
    report += f"- 总字数25%分位数: {total_stats['25%']:.0f} 字符\n"
    report += f"- 总字数中位数: {total_stats['50%']:.0f} 字符\n"
    report += f"- 总字数75%分位数: {total_stats['75%']:.0f} 字符\n"
    report += f"- 最长总字数: {total_stats['max']:.0f} 字符\n"
    
    # 6. 体裁分布分析
    report += "## 6. 体裁分布分析\n\n"
    report += "### 6.1 主要体裁（发文量前20）\n\n"
    category_counts = df['clean_category'].value_counts()
    top_categories = category_counts.head(20)
    for category, count in top_categories.items():
        report += f"- {category}: {count:,} 条 ({count/total_articles*100:.1f}%)\n"
    
    # 不同体裁的情感倾向
    report += "\n### 6.2 主要体裁情感倾向\n\n"
    # 只分析发文量≥50的体裁
    major_categories = category_counts[category_counts>=50].index.tolist()
    for category in major_categories:
        category_df = df[df['clean_category'] == category]
        avg_sentiment = category_df['final_sentiment_score'].mean()
        report += f"- {category}: 平均情感得分 {avg_sentiment:.3f}\n"
    
    # 7. 数据质量分析
    report += "## 7. 数据质量分析\n\n"
    report += f"- 日期解析成功: {df['parsed_date'].notna().sum():,} 条 ({df['parsed_date'].notna().sum()/total_articles*100:.1f}%)\n"
    report += f"- 日期解析失败: {df['parsed_date'].isna().sum():,} 条 ({df['parsed_date'].isna().sum()/total_articles*100:.1f}%)\n"
    report += f"- 空标题: {df['title'].isna().sum() + (df['title'] == '').sum():,} 条\n"
    report += f"- 空摘要: {df['summary'].isna().sum() + (df['summary'] == '').sum():,} 条\n\n"
    
    # 8. 总结与结论
    report += "## 8. 总结与结论\n\n"
    report += "1. **样本规模与多样性**: 本样本包含 {total_articles:,} 条新闻报道，来自 {unique_sources} 个不同信源，覆盖 {unique_categories} 种体裁，样本具有较好的多样性和代表性。\n\n"
    
    report += "2. **时间分布**: 报道主要分布在 {year_counts.index.min():.0f} 年至 {year_counts.index.max():.0f} 年期间，{year_counts.idxmax():.0f} 年的报道数量最多，达到 {year_counts.max():,} 条。\n\n"
    
    report += "3. **情感倾向**: 样本整体情感倾向以 {sentiment_counts.idxmax()} 为主，占比 {sentiment_counts.max()/total_articles*100:.1f}%，积极情感报道占 {sentiment_counts.get('positive', 0)/total_articles*100:.1f}%，消极情感报道占 {sentiment_counts.get('negative', 0)/total_articles*100:.1f}%，反映了报道的整体客观中立性。\n\n"
    
    report += "4. **文本特征**: 平均标题长度为 {avg_title_length:.1f} 字符，平均摘要长度为 {avg_summary_length:.1f} 字符，平均总长度为 {avg_total_length:.1f} 字符，文本长度分布较为合理，符合新闻报道的一般特征。\n\n"
    
    report += "5. **信源特征**: 前20个主要信源贡献了大部分报道，其中 {top_sources.index[0]} 是最主要的信源，发文量达到 {top_sources.iloc[0]:,} 条，占总样本的 {top_sources.iloc[0]/total_articles*100:.1f}%。\n\n"
    
    report += "6. **数据质量**: 样本数据质量整体良好，日期解析成功率为 {df['parsed_date'].notna().sum()/total_articles*100:.1f}%，空标题和空摘要的比例较低，适合进行后续的深入分析。\n\n"
    
    report += "## 9. 数据文件信息\n\n"
    report += f"- 原始数据文件: {input_file}\n"
    report += f"- 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"- 报告版本: 1.0\n"
    report += f"- 分析工具: Python 3.11, pandas, numpy\n"
    
    # 保存报告
    print(f"\n正在保存详细报告到 {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n✓ 详细报告生成完成！")
    print(f"✓ 报告已保存到: {output_file}")
    
    # 打印报告摘要
    print("\n=== 报告摘要 ===")
    print(f"总样本量: {total_articles:,} 条")
    print(f"信源数量: {unique_sources} 个")
    print(f"体裁数量: {unique_categories} 个")
    print(f"情感分布: 积极 {sentiment_counts.get('positive', 0):,} 条, 中性 {sentiment_counts.get('neutral', 0):,} 条, 消极 {sentiment_counts.get('negative', 0):,} 条")
    print(f"平均标题长度: {avg_title_length:.1f} 字符")
    print(f"平均摘要长度: {avg_summary_length:.1f} 字符")
    print(f"日期解析成功率: {df['parsed_date'].notna().sum()/total_articles*100:.1f}%")

if __name__ == "__main__":
    main()
