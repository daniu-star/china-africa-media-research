import json
import pandas as pd
import re
from sklearn.preprocessing import MinMaxScaler
import os

# 创建输出目录
output_dir = 'c:/Users/13067/Desktop/论文/非洲/demo/优化后的发展需求分析'
os.makedirs(output_dir, exist_ok=True)

# 读取发展词典
def load_development_dictionary(dict_path):
    with open(dict_path, 'r', encoding='utf-8') as f:
        development_dict = json.load(f)
    
    # 提取所有发展关键词（英文和中文）
    all_keywords = []
    for category in development_dict.values():
        for en_keyword, zh_keyword in category.items():
            all_keywords.append(en_keyword)
            all_keywords.append(zh_keyword)
    
    return all_keywords

# 优化的发展关键词匹配函数
def count_development_keywords(text, keywords):
    """计算文本中包含的发展关键词数量"""
    if not isinstance(text, str) or not text:
        return 0
    
    text_lower = text.lower()
    count = 0
    
    # 优先匹配中文关键词，因为新闻中可能包含中文
    for keyword in keywords:
        if keyword in text or keyword in text_lower:
            count += 1
    
    return count

# 优化的局部情感分析函数
def calculate_optimized_local_sentiment(text, keywords):
    """优化的局部情感分析，考虑发展关键词的上下文"""
    if not isinstance(text, str) or not text:
        return 0.0
    
    # 简单的积极和消极词列表
    positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'improve', 'increase', 'grow', 'enhance', 'boost', '发展', '增长', '合作', '机遇', '成功', '促进', '提升', '支持', '友好', '共赢']
    negative_words = ['bad', 'poor', 'negative', 'failure', 'decrease', 'reduce', 'decline', 'harm', 'damage', 'worsen', '问题', '挑战', '困难', '冲突', '危机', '风险', '障碍', '反对', '批评']
    
    # 检查是否包含发展关键词
    has_development_keyword = any(keyword in text or keyword in text.lower() for keyword in keywords)
    if not has_development_keyword:
        return 0.0
    
    text_lower = text.lower()
    
    # 计算积极和消极词的数量
    pos_count = sum(1 for word in positive_words if word in text or word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text or word in text_lower)
    
    # 计算情感得分
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    
    # 更合理的情感得分计算
    sentiment_score = (pos_count - neg_count) / total
    
    return sentiment_score

# 重新计算TF-IDF权重（简化版）
def calculate_tfidf_weight(text, keywords):
    """简化的TF-IDF权重计算，基于关键词出现频率"""
    if not isinstance(text, str) or not text:
        return 0.0
    
    # 计算文本中的单词总数
    words = re.findall(r'\w+', text.lower())
    total_words = len(words)
    if total_words == 0:
        return 0.0
    
    # 计算发展关键词在文本中出现的次数
    keyword_count = 0
    for keyword in keywords:
        keyword_count += text.lower().count(keyword.lower())
    
    # 简化的TF-IDF权重：关键词频率 * 1（假设IDF为1）
    if total_words > 0:
        tfidf_weight = keyword_count / total_words
    else:
        tfidf_weight = 0.0
    
    return tfidf_weight

# 优化的发展需求感知强度计算
def calculate_optimized_demand_perception(df, keywords):
    """优化的发展需求感知强度计算"""
    print("Calculating optimized development demand perception...")
    
    # 1. 重新计算发展关键词出现次数
    print("Step 1: Counting development keywords...")
    df['development_keyword_count'] = df['processed_text'].apply(lambda x: count_development_keywords(x, keywords))
    
    # 2. 重新计算局部情感值
    print("Step 2: Recalculating local sentiment...")
    df['local_sentiment'] = df['processed_text'].apply(lambda x: calculate_optimized_local_sentiment(x, keywords))
    
    # 3. 计算发展相关指标
    print("Step 3: Calculating development-related metrics...")
    # 发展关键词密度 = 关键词数量 / 文本长度
    df['development_keyword_density'] = df.apply(lambda row: row['development_keyword_count'] / len(row['processed_text']) if len(row['processed_text']) > 0 else 0, axis=1)
    
    # 4. 计算发展需求感知强度（不使用标准化，直接使用原始值计算）
    print("Step 4: Calculating optimized development demand perception...")
    # 使用更合理的公式：发展需求感知强度 = (关键词密度 * 10 + 局部情感值 + 1) / 2
    # 将结果缩放到0-1范围
    df['development_demand_perception'] = (df['development_keyword_density'] * 10 + df['local_sentiment'] + 1) / 2
    
    # 确保值在0-1范围内
    df['development_demand_perception'] = df['development_demand_perception'].clip(0, 1)
    
    # 5. 更新TF-IDF权重字段，使用关键词数量作为替代
    df['development_terms_weight'] = df['development_keyword_count']
    
    # 6. 计算标准化值，但确保有合理分布
    scaler = MinMaxScaler()
    df['standardized_tfidf_weight'] = scaler.fit_transform(df[['development_terms_weight']])
    df['standardized_local_sentiment'] = scaler.fit_transform(df[['local_sentiment']])
    
    return df

# 主函数
def main():
    # 文件路径
    dict_path = 'c:/Users/13067/Desktop/论文/非洲/demo/african_development_dictionary.json'
    input_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception.csv'
    output_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception_optimized.csv'
    
    # 加载发展词典
    keywords = load_development_dictionary(dict_path)
    print(f"Loaded {len(keywords)} development keywords")
    
    # 读取数据
    print(f"Reading data from {input_path}...")
    df = pd.read_csv(input_path, encoding='utf-8')
    print(f"Loaded {len(df)} records")
    
    # 重新计算发展需求感知强度
    df_optimized = calculate_optimized_demand_perception(df, keywords)
    
    # 保存优化后的数据
    print(f"Saving optimized data to {output_path}...")
    df_optimized.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    # 显示一些统计信息
    print("\nOptimization Results:")
    print(f"Average development_terms_weight: {df_optimized['development_terms_weight'].mean():.6f}")
    print(f"Average local_sentiment: {df_optimized['local_sentiment'].mean():.6f}")
    print(f"Average development_demand_perception: {df_optimized['development_demand_perception'].mean():.6f}")
    print(f"\nMin development_demand_perception: {df_optimized['development_demand_perception'].min():.6f}")
    print(f"Max development_demand_perception: {df_optimized['development_demand_perception'].max():.6f}")
    print(f"Std development_demand_perception: {df_optimized['development_demand_perception'].std():.6f}")
    
    print("\nOptimization completed successfully!")

if __name__ == "__main__":
    main()