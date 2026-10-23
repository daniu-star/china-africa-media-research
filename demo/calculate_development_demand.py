import json
import pandas as pd
import re
from sklearn.preprocessing import MinMaxScaler

# 简化的情感分析器（避免依赖NLTK的vader_lexicon）
class SimpleSentimentAnalyzer:
    def polarity_scores(self, text):
        # 使用简单的关键词匹配来计算情感得分
        positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'improve', 'increase', 'grow', 'enhance', 'boost']
        negative_words = ['bad', 'poor', 'negative', 'failure', 'decrease', 'reduce', 'decline', 'harm', 'damage', 'worsen']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        # 计算简单的情感得分
        if pos_count + neg_count == 0:
            return {'compound': 0.0}
        
        score = (pos_count - neg_count) / (pos_count + neg_count)
        return {'compound': score}

# 初始化简化的情感分析器
sia = SimpleSentimentAnalyzer()
print("Simple sentiment analyzer initialized")

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

# 快速句子分割（使用简单的标点符号分割）
def quick_split_sentences(text):
    if not isinstance(text, str) or not text:
        return []
    # 使用简单的标点符号分割句子
    sentences = re.split(r'[.!?]+', text)
    # 过滤空句子
    return [sent.strip() for sent in sentences if sent.strip()]

# 快速检查文本是否包含发展关键词
def contains_development_keyword(text, keywords):
    if not isinstance(text, str) or not text:
        return False
    text_lower = text.lower()
    for keyword in keywords:
        if keyword in text_lower:
            return True
    return False

# 计算局部情感值（包含发展关键词的句子的平均情感）
def calculate_local_sentiment(text, keywords):
    if not isinstance(text, str) or not text:
        return 0.0
    
    # 快速检查是否包含发展关键词
    if not contains_development_keyword(text, keywords):
        return 0.0
    
    # 快速分割句子
    sentences = quick_split_sentences(text)
    development_sentences = [sent for sent in sentences if contains_development_keyword(sent, keywords)]
    
    if not development_sentences:
        return 0.0
    
    # 计算情感得分
    total_score = 0.0
    for sent in development_sentences:
        total_score += sia.polarity_scores(sent)['compound']
    
    return total_score / len(development_sentences)

# 主函数
def main():
    # 配置文件路径
    dict_path = 'c:/Users/13067/Desktop/论文/非洲/demo/african_development_dictionary.json'
    data_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_development_weight.csv'
    output_path = 'c:/Users/13067/Desktop/论文/非洲/demo/enhanced_data_with_demand_perception.csv'
    
    # 加载发展词典
    development_keywords = load_development_dictionary(dict_path)
    print(f"Loaded {len(development_keywords)} development keywords")
    
    # 读取数据
    print("Loading data...")
    df = pd.read_csv(data_path, encoding='utf-8')
    print(f"Loaded {len(df)} records")
    
    # 计算局部情感值（使用简化的快速计算方法）
    print("Calculating local sentiment values...")
    df['local_sentiment'] = df['processed_text'].apply(lambda x: calculate_local_sentiment(x, development_keywords))
    
    # 提取TF-IDF权重和
    print("Processing TF-IDF weights...")
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
    print("Saving results...")
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Results saved to {output_path}")
    print("Calculation completed successfully!")

if __name__ == "__main__":
    main()