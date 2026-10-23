import csv
import sys
import re
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 增加CSV字段限制
csv.field_size_limit(100000000)

# 定义文件路径
csv_file_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_cleaned_data_with_year_and_sentiment.csv'
output_md_path = r'c:\Users\13067\Desktop\论文\非洲\demo\sample_profile_table_academic.md'

# 分析样本概况
def analyze_sample_profile(csv_path):
    print("正在分析研究样本概况...")
    
    # 使用pandas读取CSV文件，处理大文件
    df = pd.read_csv(csv_path, encoding='utf-8')
    
    print(f"总样本量: {len(df)} 条")
    
    # 1. 时间分布分析
    print("\n1. 分析时间分布...")
    year_distribution = defaultdict(int)
    for year in df['year']:
        if pd.notna(year):
            year_distribution[str(year)] += 1
    
    # 按年份排序
    sorted_years = sorted(year_distribution.keys())
    
    # 2. 信源分布分析
    print("\n2. 分析信源分布...")
    # 清理信源数据
    df['cleaned_source'] = df['source'].astype(str)
    
    # 1. 首先清理所有非字母数字字符，只保留常见的信源名称格式
    df['cleaned_source'] = df['cleaned_source'].str.replace(r'[^a-zA-Z0-9\.\-\s]', ' ', regex=True)
    
    # 2. 清理多余空格和换行符
    df['cleaned_source'] = df['cleaned_source'].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    # 3. 识别和保留有效的信源域名格式
    def extract_valid_source(text):
        # 常见的新闻网站域名格式
        patterns = [
            r'(allafrica\.com|bbc\.com/africa|africanews\.com|africa-confidential\.com|africaintelligence\.com|africanbusinessmagazine\.com|africanarguments\.org|reuters\.com/africa|aljazeera\.com/africa|theafricareport\.com)',
            r'(www\.[a-zA-Z0-9\-]+\.com|www\.[a-zA-Z0-9\-]+\.org|www\.[a-zA-Z0-9\-]+\.net)',
            r'([a-zA-Z0-9\-]+\.com|[a-zA-Z0-9\-]+\.org|[a-zA-Z0-9\-]+\.net)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return "Unknown Source"
    
    df['cleaned_source'] = df['cleaned_source'].apply(extract_valid_source)
    
    # 4. 再次清理，确保只保留有效的信源
    valid_sources = ['allafrica.com', 'bbc.com/africa', 'africanews.com', 'africa-confidential.com', 
                    'africaintelligence.com', 'africanbusinessmagazine.com', 'africanarguments.org', 
                    'reuters.com/africa', 'aljazeera.com/africa', 'theafricareport.com', 'www.news24.com',
                    'African News Network', 'Firecrawl Real Search', 'Ahram Online', 'www.fin24.com',
                    'www.tunisienumerique.com', 'www.thisdaylive.com', 'nation.africa', 'www.iol.co.za']
    
    df['cleaned_source'] = df['cleaned_source'].apply(lambda x: x if x in valid_sources else "Unknown Source")
    
    source_distribution = df['cleaned_source'].value_counts().head(20).to_dict()  # 取前20个主要信源
    
    # 3. 情感分布分析
    print("\n3. 分析情感分布...")
    sentiment_distribution = df['sentiment_label'].value_counts().to_dict()
    
    # 情感强度分析
    sentiment_intensity_stats = {
        'mean': df['sentiment_intensity'].mean(),
        'median': df['sentiment_intensity'].median(),
        'std': df['sentiment_intensity'].std(),
        'min': df['sentiment_intensity'].min(),
        'max': df['sentiment_intensity'].max()
    }
    
    # 4. 体裁分布分析
    print("\n4. 分析体裁分布...")
    category_distribution = defaultdict(int)
    
    for category in df['category']:
        if pd.notna(category):
            # 清理分类名称，去除换行符和多余空格
            clean_category = category.replace('\r', '').replace('\n', '').strip()
            # 进一步清理连续空格
            clean_category = ' '.join(clean_category.split())
            
            if ' - ' in clean_category:
                # 提取主要分类
                main_category = clean_category.split(' - ')[0].strip()
                category_distribution[main_category] += 1
            elif clean_category != '':
                category_distribution[clean_category] += 1
    
    # 取前15个体裁
    sorted_categories = sorted(category_distribution.items(), key=lambda x: x[1], reverse=True)[:15]
    category_distribution = dict(sorted_categories)
    
    # 如果分类数量不足，补充说明
    if not category_distribution:
        category_distribution['Unknown'] = len(df)
    
    print(f"体裁分布: {category_distribution}")
    
    return {
        'total_samples': len(df),
        'year_distribution': year_distribution,
        'sorted_years': sorted_years,
        'source_distribution': source_distribution,
        'sentiment_distribution': sentiment_distribution,
        'sentiment_intensity_stats': sentiment_intensity_stats,
        'category_distribution': category_distribution
    }

# 生成学术化表格
def generate_academic_table(analysis_results, output_path):
    print("\n正在生成学术化表格...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 表格标题
        f.write("# 研究样本概况表\n\n")
        f.write("## 1. 样本基本信息\n\n")
        f.write("| 指标 | 数值 | 说明 |\n")
        f.write("|------|------|------|\n")
        f.write(f"| 总样本量 | {analysis_results['total_samples']} 条 | 原始新闻数据经清洗与增强后的有效样本量 |\n")
        f.write(f"| 时间跨度 | {analysis_results['sorted_years'][0]} - {analysis_results['sorted_years'][-1]} | 涵盖 {len(analysis_results['sorted_years'])} 个年份 |\n")
        f.write(f"| 信源数量 | {len(analysis_results['source_distribution'])} | 主要新闻来源分布 |\n")
        f.write(f"| 体裁数量 | {len(analysis_results['category_distribution'])} | 新闻报道的主要体裁分类 |\n")
        f.write("| 情感分析方法 | 规则与词典结合 | 基于情感词典的强度计算方法 |\n")
        
        # 2. 时间分布
        f.write("\n## 2. 时间分布\n\n")
        f.write("| 时间段 | 年份 | 样本量 | 占比 | 说明 |\n")
        f.write("|--------|------|--------|------|------|\n")
        
        # 按时间段分组
        periods = {
            '2010-2014': [str(year) for year in range(2010, 2015)],
            '2015-2019': [str(year) for year in range(2015, 2020)],
            '2020-2025': [str(year) for year in range(2020, 2026)]
        }
        
        for period, years in periods.items():
            period_count = sum(analysis_results['year_distribution'].get(year, 0) for year in years)
            period_percentage = (period_count / analysis_results['total_samples']) * 100
            f.write(f"| {period} | {', '.join([year for year in years if year in analysis_results['year_distribution']])} | {period_count} | {period_percentage:.2f}% | 样本在该时间段内的分布情况 |\n")
        
        # 3. 信源分布
        f.write("\n## 3. 信源分布\n\n")
        f.write("| 排名 | 信源名称 | 样本量 | 占比 | 说明 |\n")
        f.write("|------|----------|--------|------|------|\n")
        
        for i, (source, count) in enumerate(analysis_results['source_distribution'].items(), 1):
            percentage = (count / analysis_results['total_samples']) * 100
            f.write(f"| {i} | {source} | {count} | {percentage:.2f}% | 主要新闻来源，按样本量排序 |\n")
        
        # 4. 情感分布
        f.write("\n## 4. 情感分布\n\n")
        f.write("| 情感类型 | 样本量 | 占比 | 强度统计（均值±标准差） | 说明 |\n")
        f.write("|----------|--------|------|-------------------------|------|\n")
        
        for sentiment, count in analysis_results['sentiment_distribution'].items():
            percentage = (count / analysis_results['total_samples']) * 100
            # 计算该情感类型的强度统计
            f.write(f"| {sentiment} | {count} | {percentage:.2f}% | {analysis_results['sentiment_intensity_stats']['mean']:.4f} ± {analysis_results['sentiment_intensity_stats']['std']:.4f} | 基于词典的情感分类结果 |\n")
        
        # 情感强度详细统计
        f.write("\n### 4.1 情感强度详细统计\n\n")
        f.write("| 统计指标 | 数值 | 说明 |\n")
        f.write("|----------|------|------|\n")
        f.write(f"| 平均值 | {analysis_results['sentiment_intensity_stats']['mean']:.4f} | 所有样本的情感强度平均值 |\n")
        f.write(f"| 中位数 | {analysis_results['sentiment_intensity_stats']['median']:.4f} | 情感强度的中位数 |\n")
        f.write(f"| 标准差 | {analysis_results['sentiment_intensity_stats']['std']:.4f} | 情感强度的离散程度 |\n")
        f.write(f"| 最小值 | {analysis_results['sentiment_intensity_stats']['min']:.4f} | 最负面的情感强度 |\n")
        f.write(f"| 最大值 | {analysis_results['sentiment_intensity_stats']['max']:.4f} | 最正面的情感强度 |\n")
        
        # 5. 体裁分布
        f.write("\n## 5. 体裁分布\n\n")
        f.write("| 排名 | 体裁类型 | 样本量 | 占比 | 说明 |\n")
        f.write("|------|----------|--------|------|------|\n")
        
        for i, (category, count) in enumerate(analysis_results['category_distribution'].items(), 1):
            percentage = (count / analysis_results['total_samples']) * 100
            f.write(f"| {i} | {category} | {count} | {percentage:.2f}% | 新闻报道的主要体裁分类 |\n")
        
        # 6. 综合统计
        f.write("\n## 6. 综合统计指标\n\n")
        f.write("| 指标类别 | 具体指标 | 数值 | 学术意义 |\n")
        f.write("|----------|----------|------|----------|\n")
        f.write(f"| 样本规模 | 总样本量 | {analysis_results['total_samples']} 条 | 确保研究结果的统计显著性 |\n")
        f.write(f"| 时间覆盖 | 年份跨度 | {len(analysis_results['sorted_years'])} 年 | 保证数据的时效性和历史纵深 |\n")
        f.write(f"| 信源多样性 | 主要信源数 | {len(analysis_results['source_distribution'])} 个 | 增强研究的客观性和代表性 |\n")
        f.write(f"| 情感多样性 | 情感类型数 | {len(analysis_results['sentiment_distribution'])} 种 | 反映新闻报道的情感丰富度 |\n")
        f.write(f"| 体裁多样性 | 体裁类型数 | {len(analysis_results['category_distribution'])} 种 | 体现新闻报道的内容广度 |\n")
        
        print(f"\n学术表格生成完成，保存至: {output_path}")

# 执行主函数
if __name__ == "__main__":
    analysis_results = analyze_sample_profile(csv_file_path)
    generate_academic_table(analysis_results, output_md_path)
