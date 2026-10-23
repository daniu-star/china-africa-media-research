import pandas as pd
from textblob import TextBlob
from tqdm import tqdm

# 定义情感分析函数
def analyze_sentiment(text):
    if not text or pd.isna(text):
        return {
            'polarity': 0.0,
            'subjectivity': 0.0,
            'sentiment_label': 'neutral'
        }
    
    # 使用TextBlob进行情感分析
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    
    # 根据polarity值添加情感标签
    if polarity > 0.05:
        sentiment_label = 'positive'
    elif polarity < -0.05:
        sentiment_label = 'negative'
    else:
        sentiment_label = 'neutral'
    
    return {
        'polarity': polarity,
        'subjectivity': subjectivity,
        'sentiment_label': sentiment_label
    }

# 主函数
def main():
    # 文件路径
    input_file = '清洗数据/enhanced_cleaned_data.csv'
    output_file = '清洗数据/sentiment_analyzed_data.csv'
    
    print("正在读取增强后的数据...")
    # 读取增强后的数据
    df = pd.read_csv(input_file, usecols=['original_index', 'data_type', 'title', 'summary', 'cleaned_title', 'cleaned_summary', 'combined_text', 'date', 'category', 'source', 'scraped_time'])
    
    print(f"数据总量: {len(df)} 条")
    
    # 对每条新闻进行情感分析
    print("\n正在进行情感分析...")
    
    # 初始化情感分析结果列
    df['polarity'] = 0.0
    df['subjectivity'] = 0.0
    df['sentiment_label'] = 'neutral'
    
    # 使用apply和tqdm进行情感分析
    tqdm.pandas(desc="情感分析进度")
    
    def apply_sentiment(row):
        scores = analyze_sentiment(row['combined_text'])
        return pd.Series(scores)
    
    # 批量处理
    sentiment_scores = df.progress_apply(apply_sentiment, axis=1)
    df[['polarity', 'subjectivity', 'sentiment_label']] = sentiment_scores
    
    # 保存结果
    print("\n正在保存情感分析结果...")
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print("✓ 情感分析完成！")
    print(f"✓ 结果已保存到 {output_file}")
    print(f"✓ 数据形状: {df.shape}")
    
    # 显示前5行结果
    print("\n情感分析结果示例（前5行）:")
    print(df[['title', 'polarity', 'subjectivity', 'sentiment_label']].head())
    
    # 显示情感分布
    print("\n情感分布:")
    print(df['sentiment_label'].value_counts())
    print("\n情感分布占比:")
    print(df['sentiment_label'].value_counts(normalize=True))

if __name__ == "__main__":
    main()