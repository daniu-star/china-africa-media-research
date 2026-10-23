import pandas as pd
from tqdm import tqdm
import re

# 简单的情感词典
sentiment_dict = {
    'positive': {
        'words': ['good', 'great', 'excellent', 'positive', 'success', 'benefit', 'progress', 'agreement', 'cooperation', 'growth', 'support', 'boost', 'strong', 'stable', 'improve', 'enhance', 'increase', 'rise', 'win', 'achievement', 'opportunity', 'potential', 'promising', 'advantage', 'better', 'best', 'effective', 'efficient', 'favorable', 'helpful', 'important', 'key', 'major', 'significant', 'valuable', 'well'],
        'prefixes': ['pro-', 'multi-', 'inter-']
    },
    'negative': {
        'words': ['bad', 'poor', 'negative', 'failure', 'problem', 'issue', 'challenge', 'risk', 'threat', 'danger', 'crisis', 'conflict', 'war', 'dispute', 'tension', 'hostile', 'aggressive', 'violate', 'sanction', 'block', 'ban', 'restrict', 'limit', 'decline', 'decrease', 'fall', 'lose', 'damage', 'harm', 'hurt', 'pain', 'suffer', 'difficult', 'hard', 'trouble', 'worry', 'concern', 'fear', 'anxiety', 'uncertain', 'unstable', 'weak', 'fragile', 'slow', 'worse', 'worst', 'ineffective', 'inefficient', 'unfavorable', 'unhelpful', 'minor', 'insignificant', 'valueless', 'ill'],
        'prefixes': ['anti-', 'dis-', 'in-', 'un-', 'non-', 'mal-']
    }
}

# 定义简单的规则基情感分析函数
def analyze_rule_based_sentiment(text):
    if not text or pd.isna(text):
        return {
            'sentiment_label': 'neutral',
            'sentiment_intensity': 0.0,
            'positive_words_count': 0,
            'negative_words_count': 0,
            'total_words_count': 0
        }
    
    # 将文本转换为小写
    text_lower = text.lower()
    
    # 移除标点符号
    text_clean = re.sub(r'[^a-zA-Z\s]', '', text_lower)
    
    # 分词
    words = text_clean.split()
    total_words = len(words)
    
    if total_words == 0:
        return {
            'sentiment_label': 'neutral',
            'sentiment_intensity': 0.0,
            'positive_words_count': 0,
            'negative_words_count': 0,
            'total_words_count': 0
        }
    
    # 计算情感词数量
    positive_count = 0
    negative_count = 0
    
    for word in words:
        # 检查完整单词
        if word in sentiment_dict['positive']['words']:
            positive_count += 1
        elif word in sentiment_dict['negative']['words']:
            negative_count += 1
        else:
            # 检查前缀
            for prefix in sentiment_dict['positive']['prefixes']:
                if word.startswith(prefix):
                    positive_count += 0.5
                    break
            for prefix in sentiment_dict['negative']['prefixes']:
                if word.startswith(prefix):
                    negative_count += 0.5
                    break
    
    # 计算情感强度
    sentiment_score = (positive_count - negative_count) / max(total_words, 1)  # 范围: [-1, 1]
    
    # 确定情感标签
    if sentiment_score > 0.1:
        sentiment_label = "positive"
    elif sentiment_score < -0.1:
        sentiment_label = "negative"
    else:
        sentiment_label = "neutral"
    
    # 计算情感强度（归一化到 [-1, 1]）
    sentiment_intensity = sentiment_score
    
    return {
        'sentiment_label': sentiment_label,
        'sentiment_intensity': round(sentiment_intensity, 4),
        'positive_words_count': positive_count,
        'negative_words_count': negative_count,
        'total_words_count': total_words
    }

# 主函数
def main():
    # 文件路径
    input_file = '清洗数据/enhanced_cleaned_data.csv'
    output_file = '清洗数据/rule_based_sentiment_analyzed_data.csv'
    
    print("正在读取增强后的数据...")
    # 读取增强后的数据
    df = pd.read_csv(input_file, usecols=['original_index', 'data_type', 'title', 'summary', 'cleaned_title', 'cleaned_summary', 'combined_text', 'date', 'category', 'source', 'scraped_time'])
    
    print(f"数据总量: {len(df)} 条")
    
    # 对每条新闻进行情感分析
    print("\n正在进行规则基情感分析...")
    
    # 使用apply和tqdm提高效率
    tqdm.pandas(desc="情感分析进度")
    
    # 批量处理
    sentiment_results = df.progress_apply(lambda row: pd.Series(analyze_rule_based_sentiment(row['combined_text'])), axis=1)
    
    # 将情感分析结果合并到原数据中
    df_with_sentiment = pd.concat([df, sentiment_results], axis=1)
    
    # 保存结果
    print("\n正在保存情感分析结果...")
    df_with_sentiment.to_csv(output_file, index=False, encoding='utf-8')
    
    print("✓ 规则基情感分析完成！")
    print(f"✓ 结果已保存到 {output_file}")
    print(f"✓ 数据形状: {df_with_sentiment.shape}")
    
    # 显示前5行结果
    print("\n情感分析结果示例（前5行）:")
    print(df_with_sentiment[['title', 'sentiment_label', 'sentiment_intensity', 'positive_words_count', 'negative_words_count']].head())
    
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