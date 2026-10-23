import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import nltk

# 下载VADER词典
nltk.download('vader_lexicon')

# 初始化情感分析器
sia = SentimentIntensityAnalyzer()

# 定义情感分析函数
def analyze_sentiment(text):
    if not text or pd.isna(text):
        return {
            'vader_neg': 0.0,
            'vader_neu': 0.0,
            'vader_pos': 0.0,
            'vader_compound': 0.0,
            'textblob_polarity': 0.0,
            'textblob_subjectivity': 0.0
        }
    
    # 使用VADER进行情感分析
    vader_scores = sia.polarity_scores(text)
    
    # 使用TextBlob进行情感分析
    blob = TextBlob(text)
    textblob_scores = {
        'polarity': blob.sentiment.polarity,
        'subjectivity': blob.sentiment.subjectivity
    }
    
    # 合并结果
    return {
        'vader_neg': vader_scores['neg'],
        'vader_neu': vader_scores['neu'],
        'vader_pos': vader_scores['pos'],
        'vader_compound': vader_scores['compound'],
        'textblob_polarity': textblob_scores['polarity'],
        'textblob_subjectivity': textblob_scores['subjectivity']
    }

# 主函数
def main():
    # 文件路径
    input_file = '清洗数据/enhanced_cleaned_data.csv'
    output_file = '清洗数据/sentiment_analyzed_data.csv'
    
    print("正在读取增强后的数据...")
    # 读取增强后的数据
    df = pd.read_csv(input_file)
    
    print(f"数据总量: {len(df)} 条")
    
    # 对每条新闻进行情感分析
    print("\n正在进行情感分析...")
    sentiments = []
    for idx, row in df.iterrows():
        # 使用合并后的文本进行情感分析
        text = row['combined_text']
        sentiment_scores = analyze_sentiment(text)
        sentiments.append(sentiment_scores)
        
        # 打印进度
        if (idx + 1) % 1000 == 0:
            print(f"已完成 {idx + 1} 条数据的情感分析")
    
    # 将情感分析结果转换为DataFrame
    sentiment_df = pd.DataFrame(sentiments)
    
    # 将情感分析结果合并到原数据中
    df_with_sentiment = pd.concat([df, sentiment_df], axis=1)
    
    # 保存结果
    print("\n正在保存情感分析结果...")
    df_with_sentiment.to_csv(output_file, index=False, encoding='utf-8')
    
    print("✓ 情感分析完成！")
    print(f"✓ 结果已保存到 {output_file}")
    print(f"✓ 数据形状: {df_with_sentiment.shape}")
    
    # 显示前5行结果
    print("\n情感分析结果示例（前5行）:")
    sentiment_cols = ['vader_neg', 'vader_neu', 'vader_pos', 'vader_compound', 'textblob_polarity', 'textblob_subjectivity']
    print(df_with_sentiment[['title', 'vader_compound', 'textblob_polarity']].head())
    
    # 显示情感分析统计信息
    print("\n情感分析统计信息:")
    print(df_with_sentiment[sentiment_cols].describe())

if __name__ == "__main__":
    main()