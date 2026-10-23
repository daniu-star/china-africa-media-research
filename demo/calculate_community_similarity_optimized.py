import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import sys

# 增加CSV字段限制
import csv
csv.field_size_limit(100000000)

# 定义文件路径
seed_file_path = r'c:\Users\13067\Desktop\论文\非洲\demo\china_africa_community_expanded_seed_terms.json'
csv_file_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_cleaned_data_with_year_and_sentiment.csv'
output_csv_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_similarity_optimized.csv'

# 加载种子词库
def load_seed_terms(file_path):
    print("正在加载扩展版中非命运共同体种子词库...")
    with open(file_path, 'r', encoding='utf-8') as f:
        seed_data = json.load(f)
    
    # 合并所有种子词和句子
    seed_terms = []
    for category, terms in seed_data.items():
        seed_terms.extend(terms)
    
    print(f"共加载 {len(seed_terms)} 个种子词/句子")
    print(f"种子词库类别: {list(seed_data.keys())}")
    
    # 生成种子词库的综合文本
    seed_text = " ".join(seed_terms)
    
    return seed_terms, seed_text

# 加载并处理CSV数据
def load_csv_data(file_path):
    print("正在加载新闻报道数据...")
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"共加载 {len(df)} 条新闻报道")
    
    # 选择用于相似度计算的文本字段
    # 合并标题和摘要，增加文本信息量
    df['text_for_similarity'] = df['title'].fillna('') + ' ' + df['summary'].fillna('') + ' ' + df['cleaned_title'].fillna('') + ' ' + df['cleaned_summary'].fillna('')
    
    return df

# 计算相似度 - 使用TF-IDF和余弦相似度
def calculate_similarity(df, seed_terms, seed_text):
    print("正在初始化TF-IDF向量器...")
    
    # 1. 准备所有文本数据
    # 将种子词库作为一个特殊文档添加到文本列表中
    all_texts = df['text_for_similarity'].tolist()
    
    # 添加种子词库的综合文本作为参考文档
    reference_text = " ".join(seed_terms)
    
    # 2. 初始化TF-IDF向量器
    # 使用unigram和bigram特征，支持中英文
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),  # 1-gram和2-gram
        min_df=2,            # 最少出现在2个文档中
        max_df=0.8,          # 最多出现在80%的文档中
        stop_words='english' # 英文停用词
    )
    
    print("正在计算TF-IDF矩阵...")
    # 3. 计算所有文本的TF-IDF向量
    # 将种子文本与所有新闻文本一起向量化
    all_texts_with_seed = all_texts + [reference_text]
    tfidf_matrix = vectorizer.fit_transform(all_texts_with_seed)
    
    print("正在计算余弦相似度...")
    # 4. 分离新闻文本和种子文本的向量
    news_tfidf = tfidf_matrix[:-1]  # 所有新闻文本
    seed_tfidf = tfidf_matrix[-1]   # 种子词库文本
    
    # 5. 计算每条新闻与种子词库的余弦相似度
    # 将种子向量转换为2D数组以便计算
    seed_tfidf_2d = seed_tfidf.reshape(1, -1)
    
    # 批量计算余弦相似度，返回一个数组
    similarities = cosine_similarity(news_tfidf, seed_tfidf_2d).flatten()
    
    # 确保相似度在0-1范围内
    similarities = np.clip(similarities, 0.0, 1.0)
    
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
    
    # 按情感类型统计相似度
    print("\n按情感类型统计相似度:")
    sentiment_stats = df.groupby('sentiment_label')['community_similarity'].agg(['mean', 'count'])
    print(sentiment_stats)
    
    # 显示相似度分布
    print("\n相似度分布:")
    bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    df['similarity_bin'] = pd.cut(df['community_similarity'], bins=bins, right=False)
    bin_stats = df['similarity_bin'].value_counts().sort_index()
    print(bin_stats)

# 主函数
def main():
    try:
        # 1. 加载种子词库
        seed_terms, seed_text = load_seed_terms(seed_file_path)
        
        # 2. 加载CSV数据
        df = load_csv_data(csv_file_path)
        
        # 3. 计算相似度
        similarities = calculate_similarity(df, seed_terms, seed_text)
        
        # 4. 保存结果
        save_results(df, similarities, output_csv_path)
        
        print("\n相似度计算完成！")
        
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
