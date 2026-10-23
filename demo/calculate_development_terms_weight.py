import pandas as pd
import numpy as np
import json
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import os

# 设置文件路径
DICTIONARY_PATH = r'c:\Users\13067\Desktop\论文\非洲\demo\african_development_dictionary.json'
CSV_PATH = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_recognition_degree.csv'
OUTPUT_PATH = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_development_weight.csv'

# 读取发展词典
def load_dictionary(file_path):
    print("正在加载发展词典...")
    with open(file_path, 'r', encoding='utf-8') as f:
        dictionary = json.load(f)
    
    # 提取所有英文关键词
    all_terms = set()
    for category, terms in dictionary.items():
        all_terms.update(terms.keys())
    
    print(f"共加载 {len(all_terms)} 个发展词典关键词")
    return list(all_terms)

# 读取CSV数据
def load_csv_data(file_path):
    print("正在加载CSV数据...")
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"共加载 {len(df)} 条数据")
    return df

# 预处理文本
def preprocess_text(text):
    if pd.isna(text):
        return ""
    # 将文本转换为小写
    text = str(text).lower()
    # 移除特殊字符
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    # 移除多余的空格
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 计算发展词典词汇的TF-IDF权重和
def calculate_development_weight(df, terms):
    print("正在计算发展词典词汇的TF-IDF权重和...")
    
    # 预处理所有文本
    df['processed_text'] = df['combined_text'].apply(preprocess_text)
    
    # 初始化TF-IDF向量器
    vectorizer = TfidfVectorizer(
        vocabulary=terms,
        ngram_range=(1, 2),
        stop_words='english',
        min_df=1,
        max_df=0.8
    )
    
    # 计算TF-IDF矩阵
    tfidf_matrix = vectorizer.fit_transform(df['processed_text'])
    
    # 计算每篇文档中发展词典词汇的权重和
    development_weights = tfidf_matrix.sum(axis=1).A1
    
    # 将结果添加到DataFrame中
    df['development_terms_weight'] = development_weights
    
    print(f"发展词典词汇权重和计算完成，均值: {development_weights.mean():.4f}, 标准差: {development_weights.std():.4f}")
    return df

# 主函数
def main():
    try:
        # 1. 加载发展词典
        terms = load_dictionary(DICTIONARY_PATH)
        
        # 2. 加载CSV数据
        df = load_csv_data(CSV_PATH)
        
        # 3. 计算发展词典词汇权重和
        df = calculate_development_weight(df, terms)
        
        # 4. 保存结果
        print("正在保存结果...")
        df.to_csv(OUTPUT_PATH, encoding='utf-8', index=False)
        
        print(f"结果已保存到: {OUTPUT_PATH}")
        print("\n处理完成！")
        
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()