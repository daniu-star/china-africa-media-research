import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from tqdm import tqdm
import nltk

# 确保VADER词典已下载
nltk.download('vader_lexicon', quiet=True)

# 初始化情感分析器
sia = SentimentIntensityAnalyzer()

# 定义增强版情感分析函数
def analyze_enhanced_sentiment(text):
    if not text or pd.isna(text):
        return {
            # VADER情感分析结果
            'vader_neg': 0.0,
            'vader_neu': 0.0,
            'vader_pos': 0.0,
            'vader_compound': 0.0,
            
            # TextBlob情感分析结果
            'textblob_polarity': 0.0,
            'textblob_subjectivity': 0.0,
            
            # 综合情感分析结果
            'sentiment_label': 'neutral',
            'sentiment_intensity': 0.0,
            'sentiment_confidence': 0.0
        }
    
    # 使用VADER进行情感分析
    vader_scores = sia.polarity_scores(text)
    
    # 使用TextBlob进行情感分析
    blob = TextBlob(text)
    textblob_scores = {
        'polarity': blob.sentiment.polarity,
        'subjectivity': blob.sentiment.subjectivity
    }
    
    # 计算综合情感强度
    # VADER compound范围: [-1, 1]
    # TextBlob polarity范围: [-1, 1]
    # 综合情感强度: 取两者的加权平均，VADER权重0.6，TextBlob权重0.4
    combined_intensity = (vader_scores['compound'] * 0.6) + (textblob_scores['polarity'] * 0.4)
    
    # 确定情感标签
    if combined_intensity > 0.1:
        sentiment_label = "positive"
    elif combined_intensity < -0.1:
        sentiment_label = "negative"
    else:
        sentiment_label = "neutral"
    
    # 计算情感置信度（基于情感强度的绝对值）
    sentiment_confidence = abs(combined_intensity)
    
    # 合并结果
    return {
        # VADER情感分析结果
        'vader_neg': vader_scores['neg'],
        'vader_neu': vader_scores['neu'],
        'vader_pos': vader_scores['pos'],
        'vader_compound': vader_scores['compound'],
        
        # TextBlob情感分析结果
        'textblob_polarity': textblob_scores['polarity'],
        'textblob_subjectivity': textblob_scores['subjectivity'],
        
        # 综合情感分析结果
        'sentiment_label': sentiment_label,
        'sentiment_intensity': round(combined_intensity, 4),
        'sentiment_confidence': round(sentiment_confidence, 4)
    }

# 主函数
def main():
    # 文件路径
    input_file = '清洗数据/enhanced_cleaned_data.csv'
    output_file = '清洗数据/enhanced_sentiment_analyzed_data.csv'
    
    print("正在读取增强后的数据...")
    # 读取增强后的数据
    df = pd.read_csv(input_file, usecols=['original_index', 'data_type', 'title', 'summary', 'cleaned_title', 'cleaned_summary', 'combined_text', 'date', 'category', 'source', 'scraped_time'])
    
    print(f"数据总量: {len(df)} 条")
    
    # 对每条新闻进行情感分析
    print("\n正在进行增强版情感分析...")
    
    # 使用apply和tqdm提高效率
    tqdm.pandas(desc="情感分析进度")
    
    # 批量处理
    sentiment_results = df.progress_apply(lambda row: pd.Series(analyze_enhanced_sentiment(row['combined_text'])), axis=1)
    
    # 将情感分析结果合并到原数据中
    df_with_sentiment = pd.concat([df, sentiment_results], axis=1)
    
    # 保存结果
    print("\n正在保存情感分析结果...")
    df_with_sentiment.to_csv(output_file, index=False, encoding='utf-8')
    
    print("✓ 增强版情感分析完成！")
    print(f"✓ 结果已保存到 {output_file}")
    print(f"✓ 数据形状: {df_with_sentiment.shape}")
    
    # 显示前5行结果
    print("\n情感分析结果示例（前5行）:")
    print(df_with_sentiment[['title', 'sentiment_label', 'sentiment_intensity', 'sentiment_confidence', 'vader_compound', 'textblob_polarity']].head())
    
    # 显示情感分布
    print("\n情感分布:")
    sentiment_distribution = df_with_sentiment['sentiment_label'].value_counts()
    print(sentiment_distribution)
    print("\n情感分布占比:")
    print(df_with_sentiment['sentiment_label'].value_counts(normalize=True))
    
    # 显示情感强度统计
    print("\n情感强度统计:")
    print(df_with_sentiment['sentiment_intensity'].describe())

if __name__ == "__main__":
    main()