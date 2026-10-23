import json
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch
import sys

# 增加CSV字段限制
import csv
csv.field_size_limit(100000000)

# 定义文件路径
seed_file_path = r'c:\Users\13067\Desktop\论文\非洲\demo\china_africa_community_seed_terms.json'
csv_file_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_cleaned_data_with_year_and_sentiment.csv'
output_csv_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_similarity.csv'

# 加载种子词库
def load_seed_terms(file_path):
    print("正在加载中非命运共同体种子词库...")
    with open(file_path, 'r', encoding='utf-8') as f:
        seed_data = json.load(f)
    
    # 合并所有种子词和句子
    seed_terms = []
    for category, terms in seed_data.items():
        seed_terms.extend(terms)
    
    print(f"共加载 {len(seed_terms)} 个种子词/句子")
    print(f"种子词库类别: {list(seed_data.keys())}")
    
    return seed_terms

# 加载并处理CSV数据
def load_csv_data(file_path):
    print("正在加载新闻报道数据...")
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"共加载 {len(df)} 条新闻报道")
    
    # 选择用于相似度计算的文本字段
    # 合并标题和摘要，增加文本信息量
    df['text_for_similarity'] = df['title'].fillna('') + ' ' + df['summary'].fillna('') + ' ' + df['cleaned_title'].fillna('') + ' ' + df['cleaned_summary'].fillna('')
    
    return df

# 基于关键词匹配的相似度计算
def calculate_similarity(df, seed_terms):
    print("正在初始化关键词匹配相似度计算...")
    
    # 1. 构建关键词集合
    # 将种子词分为不同级别，核心词权重更高
    core_terms = [term for term in seed_terms if any(keyword in term for keyword in ['中非命运共同体', 'China-Africa Community', '中非合作论坛', 'FOCAC', '一带一路', '真实亲诚', '正确义利观'])]
    important_terms = [term for term in seed_terms if term not in core_terms]
    
    print(f"核心关键词数量: {len(core_terms)}")
    print(f"重要关键词数量: {len(important_terms)}")
    
    # 2. 定义相似度计算函数
    def keyword_similarity(text):
        if not text:
            return 0.0
        
        # 将文本转换为小写，便于匹配
        text_lower = text.lower()
        
        # 初始化匹配计数
        core_matches = 0
        important_matches = 0
        
        # 匹配核心关键词（权重更高）
        for term in core_terms:
            if term.lower() in text_lower:
                core_matches += 1
        
        # 匹配重要关键词
        for term in important_terms:
            if term.lower() in text_lower:
                important_matches += 1
        
        # 计算加权相似度
        # 核心关键词权重为2，重要关键词权重为1
        total_weighted_matches = core_matches * 2 + important_matches
        
        # 计算最大可能匹配值（用于归一化）
        max_possible = len(core_terms) * 2 + len(important_terms)
        
        # 计算相似度（0-1范围）
        if max_possible == 0:
            return 0.0
        
        similarity = total_weighted_matches / max_possible
        
        return similarity
    
    print("正在计算新闻报道相似度...")
    # 3. 批量计算相似度
    similarities = []
    
    for i, text in enumerate(df['text_for_similarity']):
        sim = keyword_similarity(text)
        similarities.append(sim)
        
        # 显示进度
        if (i + 1) % 1000 == 0:
            print(f"已计算 {i + 1} 条文本的相似度")
    
    return similarities

# 保存结果
def save_results(df, similarities, output_path):
    print("正在保存结果...")
    # 添加相似度列
    df['community_similarity'] = similarities
    
    # 保存到新的CSV文件
    df.to_csv(output_path, encoding='utf-8', index=False)
    
    print(f"结果已保存到: {output_path}")
    
    # 打印相似度统计
    print("\n相似度统计:")
    print(f"平均值: {df['community_similarity'].mean():.4f}")
    print(f"中位数: {df['community_similarity'].median():.4f}")
    print(f"最小值: {df['community_similarity'].min():.4f}")
    print(f"最大值: {df['community_similarity'].max():.4f}")
    print(f"标准差: {df['community_similarity'].std():.4f}")
    
    # 按年份统计相似度
    print("\n按年份统计相似度:")
    year_stats = df.groupby('year')['community_similarity'].agg(['mean', 'count'])
    print(year_stats)

# 主函数
def main():
    try:
        # 1. 加载种子词库
        seed_terms = load_seed_terms(seed_file_path)
        
        # 2. 加载CSV数据
        df = load_csv_data(csv_file_path)
        
        # 3. 计算相似度
        similarities = calculate_similarity(df, seed_terms)
        
        # 4. 保存结果
        save_results(df, similarities, output_csv_path)
        
        print("\n相似度计算完成！")
        
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
