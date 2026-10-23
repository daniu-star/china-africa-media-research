import pandas as pd
import re
from tqdm import tqdm

# 简单的情感词典
POSITIVE_WORDS = set([
    'good', 'great', 'excellent', 'positive', 'best', 'better', 'success',
    'win', 'victory', 'progress', 'improve', 'growth', 'happy', 'joy',
    'love', 'peace', 'hope', 'bright', 'promise', 'strong', 'stable',
    'secure', 'safe', 'benefit', 'advantage', 'opportunity', 'prosperity',
    'wealth', 'health', 'well', 'fine', 'perfect', 'wonderful', 'amazing',
    'fantastic', 'superb', 'outstanding', 'remarkable', 'impressive',
    'constructive', 'helpful', 'supportive', 'favorable', 'positive',
    'encouraging', 'optimistic', 'confident', 'trust', 'trustworthy'
])

NEGATIVE_WORDS = set([
    'bad', 'worse', 'worst', 'negative', 'poor', 'failure', 'lose', 'loss',
    'defeat', 'problem', 'issue', 'challenge', 'crisis', 'danger', 'risk',
    'threat', 'danger', 'harm', 'damage', 'destruction', 'war', 'conflict',
    'violence', 'attack', 'kill', 'death', 'disease', 'illness', 'sick',
    'weak', 'unstable', 'insecure', 'unsafe', 'bad', 'terrible', 'awful',
    'horrible', 'disaster', 'catastrophe', 'tragedy', 'sad', 'sorrow',
    'pain', 'suffering', 'fear', 'anxiety', 'worry', 'concern', 'doubt',
    'mistrust', 'untrustworthy', 'corrupt', 'corruption', 'crime', 'criminal',
    'evil', 'hate', 'hateful', 'angry', 'anger', 'frustration', 'disappointment',
    'disaster', 'failure', 'collapse', 'decline', 'decrease', 'downturn',
    'recession', 'depression', 'poverty', 'hunger', 'starvation', 'unemployment'
])

# 定义情感分析函数
def fast_analyze_sentiment(text):
    if not text or pd.isna(text):
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral'
        }
    
    # 简单的文本处理
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    words = text.split()
    
    # 计算情感得分
    positive_count = 0
    negative_count = 0
    
    for word in words:
        if word in POSITIVE_WORDS:
            positive_count += 1
        elif word in NEGATIVE_WORDS:
            negative_count += 1
    
    # 计算情感得分
    total = positive_count + negative_count
    if total == 0:
        sentiment_score = 0.0
    else:
        sentiment_score = (positive_count - negative_count) / total
    
    # 根据得分确定情感标签
    if sentiment_score > 0.1:
        sentiment_label = 'positive'
    elif sentiment_score < -0.1:
        sentiment_label = 'negative'
    else:
        sentiment_label = 'neutral'
    
    return {
        'sentiment_score': sentiment_score,
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
    print("\n正在进行快速情感分析...")
    
    # 初始化结果列
    df['sentiment_score'] = 0.0
    df['sentiment_label'] = 'neutral'
    
    # 使用高效的列表推导式进行处理
    results = []
    for text in tqdm(df['combined_text'], desc="情感分析进度"):
        result = fast_analyze_sentiment(text)
        results.append(result)
    
    # 将结果转换为DataFrame并合并
    results_df = pd.DataFrame(results)
    df = pd.concat([df, results_df], axis=1)
    
    # 保存结果
    print("\n正在保存情感分析结果...")
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print("✓ 快速情感分析完成！")
    print(f"✓ 结果已保存到 {output_file}")
    print(f"✓ 数据形状: {df.shape}")
    
    # 显示前5行结果
    print("\n情感分析结果示例（前5行）:")
    print(df[['title', 'sentiment_score', 'sentiment_label']].head())
    
    # 显示情感分布
    print("\n情感分布:")
    print(df['sentiment_label'].value_counts())
    print("\n情感分布占比:")
    print(df['sentiment_label'].value_counts(normalize=True))

if __name__ == "__main__":
    main()