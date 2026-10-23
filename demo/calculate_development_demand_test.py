import json
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize
import re
from sklearn.preprocessing import MinMaxScaler

# 下载必要的NLTK数据
nltk.download('punkt')
nltk.download('vader_lexicon')

# 初始化情感分析器
sia = SentimentIntensityAnalyzer()

# 读取发展词典
def load_development_dictionary(dict_path):
    with open(dict_path, 'r', encoding='utf-8') as f:
        development_dict = json.load(f)
    
    # 提取所有发展关键词（英文）
    development_keywords = []
    for category in development_dict.values():
        for keyword in category.keys():
            development_keywords.append(keyword)
    
    return development_keywords

# 句子分割
def split_into_sentences(text):
    if not isinstance(text, str):
        return []
    return sent_tokenize(text)

# 检查句子是否包含发展关键词
def contains_development_keyword(sentence, keywords):
    sentence_lower = sentence.lower()
    for keyword in keywords:
        if keyword in sentence_lower:
            return True
    return False

# 计算局部情感值（包含发展关键词的句子的平均情感）
def calculate_local_sentiment(text, keywords):
    sentences = split_into_sentences(text)
    development_sentences = [sent for sent in sentences if contains_development_keyword(sent, keywords)]
    
    if not development_sentences:
        return 0.0
    
    sentiment_scores = []
    for sent in development_sentences:
        score = sia.polarity_scores(sent)['compound']
        sentiment_scores.append(score)
    
    return sum(sentiment_scores) / len(sentiment_scores)

# 主函数
def main():
    # 配置文件路径
    dict_path = 'c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\african_development_dictionary.json'
    data_path = 'c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\清洗数据\\enhanced_data_with_development_weight.csv'
    output_path = 'c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\enhanced_data_with_demand_perception_test.csv'
    
    # 加载发展词典
    development_keywords = load_development_dictionary(dict_path)
    print(f"Loaded {len(development_keywords)} development keywords")
    
    # 读取数据（只读取前1000行）
    df = pd.read_csv(data_path, encoding='utf-8', nrows=1000)
    print(f"Loaded {len(df)} records for testing")
    
    # 计算局部情感值
    print("Calculating local sentiment values...")
    df['local_sentiment'] = df['processed_text'].apply(lambda x: calculate_local_sentiment(x, development_keywords))
    
    # 提取TF-IDF权重和
    df['development_terms_weight'] = pd.to_numeric(df['development_terms_weight'], errors='coerce').fillna(0)
    
    # 标准化处理
    print("Performing normalization...")
    scaler = MinMaxScaler()
    
    # 标准化TF-IDF权重和
    df['standardized_tfidf_weight'] = scaler.fit_transform(df[['development_terms_weight']])
    
    # 标准化局部情感值
    df['standardized_local_sentiment'] = scaler.fit_transform(df[['local_sentiment']])
    
    # 计算发展需求感知强度
    print("Calculating development demand perception intensity...")
    df['development_demand_perception'] = df['standardized_tfidf_weight'] * df['standardized_local_sentiment']
    
    # 保存结果
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Test results saved to {output_path}")
    print("Test calculation completed successfully!")

if __name__ == "__main__":
    main()