import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
import numpy as np
import re
import sys

# 增加CSV字段限制
import csv
csv.field_size_limit(100000000)

# 定义文件路径
seed_file_path = r'c:\Users\13067\Desktop\论文\非洲\demo\china_africa_community_ultimate_seed_terms.json'
csv_file_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_cleaned_data_with_year_and_sentiment.csv'
output_csv_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_similarity_ultimate.csv'

# 文本预处理函数
def preprocess_text(text):
    if not isinstance(text, str):
        return ""
    
    # 转换为小写
    text = text.lower()
    
    # 移除特殊字符和数字，保留中英文
    text = re.sub(r'[^a-zA-Z\u4e00-\u9fa5\s]', ' ', text)
    
    # 移除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

# 加载种子词库
def load_seed_terms(file_path):
    print("正在加载终极版中非命运共同体种子词库...")
    with open(file_path, 'r', encoding='utf-8') as f:
        seed_data = json.load(f)
    
    # 为不同类别分配不同权重
    category_weights = {
        'core_concepts': 3.0,           # 核心概念权重最高
        'leadership_statements': 2.5,    # 领导人讲话权重较高
        'official_documents': 2.0,       # 官方文件权重较高
        'specific_initiatives': 1.8,     # 具体倡议权重中等
        'key_cooperation_areas': 1.5,    # 合作领域权重中等
        'policy_terms': 1.5,             # 政策术语权重中等
        'specific_projects': 1.2,        # 具体项目权重较低
        'country_relations': 1.0,        # 国家关系权重较低
        'values_and_principles': 1.0,    # 价值原则权重较低
        'historical_context': 1.0         # 历史背景权重较低
    }
    
    # 合并所有种子词和句子，并添加权重
    seed_terms_with_weights = []
    all_seed_terms = []
    
    for category, terms in seed_data.items():
        weight = category_weights.get(category, 1.0)
        for term in terms:
            seed_terms_with_weights.append((term, weight))
            all_seed_terms.append(term)
    
    print(f"共加载 {len(all_seed_terms)} 个种子词/句子")
    print(f"种子词库类别: {list(seed_data.keys())}")
    print(f"类别权重: {category_weights}")
    
    return seed_terms_with_weights, all_seed_terms

# 加载并处理CSV数据
def load_csv_data(file_path):
    print("正在加载新闻报道数据...")
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"共加载 {len(df)} 条新闻报道")
    
    # 选择用于相似度计算的文本字段
    # 合并标题和摘要，增加文本信息量
    df['text_for_similarity'] = df['title'].fillna('') + ' ' + df['summary'].fillna('') + ' ' + df['cleaned_title'].fillna('') + ' ' + df['cleaned_summary'].fillna('')
    
    # 文本预处理
    print("正在预处理文本...")
    df['text_for_similarity'] = df['text_for_similarity'].apply(preprocess_text)
    
    return df

# 计算相似度 - 使用优化的TF-IDF和加权余弦相似度
def calculate_similarity(df, seed_terms_with_weights, all_seed_terms):
    print("正在初始化优化的TF-IDF向量器...")
    
    # 1. 准备所有文本数据
    all_texts = df['text_for_similarity'].tolist()
    
    # 2. 初始化TF-IDF向量器，使用更优化的参数
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),         # 1-gram、2-gram和3-gram
        min_df=1,                   # 最少出现在1个文档中
        max_df=0.9,                 # 最多出现在90%的文档中
        use_idf=True,               # 使用IDF加权
        smooth_idf=True,            # 平滑IDF值
        sublinear_tf=True,          # 使用亚线性TF缩放
        stop_words='english'        # 移除英文停用词
    )
    
    print("正在计算TF-IDF矩阵...")
    # 3. 计算所有文本的TF-IDF向量
    # 将种子文本与所有新闻文本一起向量化
    # 为种子文本创建一个综合文档，重复出现的次数与权重相关
    weighted_seed_text = []
    for term, weight in seed_terms_with_weights:
        # 根据权重重复种子词，权重越高出现次数越多
        # 将权重转换为整数次数（如权重2.5转换为2次）
        repeat_count = max(1, int(weight))
        weighted_seed_text.extend([term] * repeat_count)
    
    # 创建种子文本的综合表示
    seed_text_combined = " ".join(weighted_seed_text)
    
    # 将所有新闻文本和种子文本组合
    all_texts_with_seed = all_texts + [seed_text_combined]
    
    # 计算TF-IDF矩阵
    tfidf_matrix = vectorizer.fit_transform(all_texts_with_seed)
    
    print("正在计算余弦相似度...")
    # 4. 分离新闻文本和种子文本的向量
    news_tfidf = tfidf_matrix[:-1]  # 所有新闻文本
    seed_tfidf = tfidf_matrix[-1]   # 种子词库文本
    
    # 5. 计算每条新闻与种子词库的余弦相似度
    # 将种子向量转换为2D数组以便计算
    seed_tfidf_2d = seed_tfidf.reshape(1, -1)
    
    # 批量计算余弦相似度
    similarities = cosine_similarity(news_tfidf, seed_tfidf_2d).flatten()
    
    # 6. 相似度后处理
    # 确保相似度在0-1范围内
    similarities = np.clip(similarities, 0.0, 1.0)
    
    # 使用幂变换增强区分度
    # 对相似度进行幂变换，增强高相似度文本的区分度
    similarities = np.power(similarities, 0.7)
    
    # 再次归一化到0-1范围
    similarities = (similarities - similarities.min()) / (similarities.max() - similarities.min()) if similarities.max() > similarities.min() else similarities
    
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
    print(f"平均值: {df['community_similarity'].mean():.6f}")
    print(f"中位数: {df['community_similarity'].median():.6f}")
    print(f"最小值: {df['community_similarity'].min():.6f}")
    print(f"最大值: {df['community_similarity'].max():.6f}")
    print(f"标准差: {df['community_similarity'].std():.6f}")
    
    # 按年份统计相似度
    print("\n按年份统计相似度:")
    year_stats = df.groupby('year')['community_similarity'].agg(['mean', 'count'])
    print(year_stats)
    
    # 按情感类型统计相似度
    print("\n按情感类型统计相似度:")
    sentiment_stats = df.groupby('sentiment_label')['community_similarity'].agg(['mean', 'count'])
    print(sentiment_stats)
    
    # 显示相似度分布（更细粒度）
    print("\n相似度分布:")
    bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    df['similarity_bin'] = pd.cut(df['community_similarity'], bins=bins, right=False)
    bin_stats = df['similarity_bin'].value_counts().sort_index()
    print(bin_stats)
    
    # 计算相关系数
    print("\n相关系数分析:")
    # 相似度与情感强度的相关系数
    sentiment_corr = df['community_similarity'].corr(df['sentiment_intensity'])
    print(f"相似度与情感强度的相关系数: {sentiment_corr:.4f}")
    
    # 相似度与年份的相关系数
    year_corr = df['community_similarity'].corr(df['year'].astype(float))
    print(f"相似度与年份的相关系数: {year_corr:.4f}")

# 主函数
def main():
    try:
        # 1. 加载种子词库
        seed_terms_with_weights, all_seed_terms = load_seed_terms(seed_file_path)
        
        # 2. 加载CSV数据
        df = load_csv_data(csv_file_path)
        
        # 3. 计算相似度
        similarities = calculate_similarity(df, seed_terms_with_weights, all_seed_terms)
        
        # 4. 保存结果
        save_results(df, similarities, output_csv_path)
        
        print("\n相似度计算完成！")
        
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
