import pandas as pd
from tqdm import tqdm
import re

# 最终版情感词典，进一步优化词汇和规则
sentiment_dict = {
    'positive': {
        'words': [
            # 通用积极词汇
            'good', 'great', 'excellent', 'positive', 'success', 'benefit', 'progress', 
            'agreement', 'cooperation', 'growth', 'support', 'boost', 'strong', 'stable', 
            'improve', 'enhance', 'increase', 'rise', 'win', 'achievement', 'opportunity', 
            'potential', 'promising', 'advantage', 'better', 'best', 'effective', 'efficient', 
            'favorable', 'helpful', 'important', 'key', 'major', 'significant', 'valuable', 'well',
            
            # 经济相关积极词汇
            'invest', 'investment', 'finance', 'fund', 'capital', 'profit', 'gain', 'earn', 
            'rich', 'wealth', 'prosper', 'prosperity', 'boom', 'expand', 'develop', 'development',
            'trade', 'export', 'import', 'market', 'business', 'enterprise', 'industry', 'factory',
            'job', 'employment', 'hire', 'salary', 'wage', 'income', 'economy', 'economic',
            
            # 政治相关积极词汇
            'peace', 'security', 'stability', 'agreement', 'treaty', 'alliance', 'cooperation',
            'diplomacy', 'negotiate', 'talk', 'meet', 'summit', 'leader', 'president', 'prime',
            'government', 'state', 'nation', 'country', 'people', 'citizen', 'society',
            
            # 关系相关积极词汇
            'friend', 'friendly', 'partner', 'partnership', 'ally', 'alliance', 'cooperate',
            'collaborate', 'support', 'back', 'backing', 'aid', 'assist', 'help', 'assistance',
            
            # 其他积极词汇
            'welcome', 'greet', 'hail', 'praise', 'commend', 'applaud', 'approve', 'support',
            'accept', 'agree', 'unite', 'unification', 'join', 'connect', 'link', 'bridge'
        ],
        'prefixes': ['pro-', 'multi-', 'inter-', 'co-', 'sym-'],
        'suffixes': ['-able', '-ible', '-ful', '-ous', '-ive', '-ing', '-ed', '-ment', '-tion', '-sion']
    },
    'negative': {
        'words': [
            # 通用消极词汇
            'bad', 'poor', 'negative', 'failure', 'problem', 'issue', 'challenge', 'risk', 
            'threat', 'danger', 'crisis', 'conflict', 'war', 'dispute', 'tension', 'hostile', 
            'aggressive', 'violate', 'sanction', 'block', 'ban', 'restrict', 'limit', 'decline', 
            'decrease', 'fall', 'lose', 'damage', 'harm', 'hurt', 'pain', 'suffer', 'difficult', 
            'hard', 'trouble', 'worry', 'concern', 'fear', 'anxiety', 'uncertain', 'unstable', 
            'weak', 'fragile', 'slow', 'worse', 'worst', 'ineffective', 'inefficient', 'unfavorable', 
            'unhelpful', 'minor', 'insignificant', 'valueless', 'ill',
            
            # 经济相关消极词汇
            'loss', 'lose', 'cost', 'expense', 'debt', 'deficit', 'bankrupt', 'bankruptcy',
            'recession', 'depression', 'crisis', 'inflation', 'deflation', 'unemployment',
            'jobless', 'poverty', 'poor', 'low', 'down', 'drop', 'fall', 'decline',
            'tariff', 'tax', 'duty', 'levy', 'fine', 'penalty', 'sanction',
            
            # 政治相关消极词汇
            'war', 'conflict', 'dispute', 'fight', 'battle', 'attack', 'invade', 'invasion',
            'sanction', 'block', 'ban', 'restrict', 'limit', 'forbid', 'prohibit', 'prevent',
            'oppose', 'opposition', 'protest', 'demonstrate', 'riot', 'rebel', 'revolution',
            'coup', 'overthrow', 'dictator', 'authoritarian', 'totalitarian',
            
            # 关系相关消极词汇
            'enemy', 'hostile', 'oppose', 'opposition', 'compete', 'competition', 'rival', 'rivalry',
            'conflict', 'dispute', 'tension', 'strained', 'broken', 'split', 'divide', 'separate',
            
            # 其他消极词汇
            'reject', 'refuse', 'deny', 'disagree', 'disapprove', 'criticize', 'criticism',
            'blame', 'accuse', 'charge', 'condemn', 'oppose', 'resist', 'block', 'hinder',
            'obstruct', 'delay', 'slow', 'stop', 'end', 'terminate', 'cancel', 'abandon'
        ],
        'prefixes': ['anti-', 'dis-', 'in-', 'un-', 'non-', 'mal-', 'mis-', 'de-'],
        'suffixes': ['-less', '-ful', '-ous', '-ive', '-ing', '-ed', '-ment', '-tion', '-sion']
    },
    'negators': [
        # 否定词，用于反转情感
        'not', 'no', 'never', 'none', 'nobody', 'nothing', 'nowhere', 'neither', 'nor',
        'hardly', 'scarcely', 'barely', 'seldom', 'rarely', 'little', 'few'
    ],
    'intensifiers': [
        # 程度副词，用于增强情感
        'very', 'extremely', 'exceedingly', 'exceptionally', 'especially', 'particularly',
        'highly', 'greatly', 'strongly', 'severely', 'seriously', 'badly', 'well',
        'much', 'many', 'more', 'most', 'too', 'so', 'such', 'quite', 'rather',
        'fairly', 'somewhat', 'slightly', 'a little', 'a bit', 'enough', 'adequately'
    ]
}

# 定义最终版情感分析函数
def analyze_final_sentiment(text):
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
    
    # 移除标点符号和特殊字符
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
    
    # 初始化计数
    positive_count = 0
    negative_count = 0
    
    # 检查特定关键词，直接判定消极情感
    negative_keywords = ['war', 'conflict', 'sanction', 'ban', 'tariff', 'threat', 'attack', 'invasion', 'crisis', 'dispute', 'tension', 'hostile', 'aggressive', 'violate', 'block', 'restrict', 'limit', 'decline', 'decrease', 'fall', 'lose', 'damage', 'harm', 'hurt', 'pain', 'suffer']
    for keyword in negative_keywords:
        if keyword in text_clean:
            negative_count += 2  # 增加消极词权重
    
    # 检查特定关键词，直接判定积极情感
    positive_keywords = ['peace', 'agreement', 'cooperation', 'investment', 'trade', 'partnership', 'ally', 'alliance', 'support', 'aid', 'assistance', 'friend', 'friendly', 'boom', 'expand', 'develop', 'growth', 'profit', 'gain', 'success', 'victory', 'win']
    for keyword in positive_keywords:
        if keyword in text_clean:
            positive_count += 2  # 增加积极词权重
    
    for i, word in enumerate(words):
        # 跳过过短的词
        if len(word) < 3:
            continue
        
        # 检查是否为积极词
        is_positive = False
        is_negative = False
        
        # 检查完整单词
        if word in sentiment_dict['positive']['words']:
            is_positive = True
        elif word in sentiment_dict['negative']['words']:
            is_negative = True
        else:
            # 检查前缀
            for prefix in sentiment_dict['positive']['prefixes']:
                if word.startswith(prefix):
                    is_positive = True
                    break
            if not is_positive:
                for prefix in sentiment_dict['negative']['prefixes']:
                    if word.startswith(prefix):
                        is_negative = True
                        break
            
            # 检查后缀
            if not is_positive and not is_negative:
                for suffix in sentiment_dict['positive']['suffixes']:
                    if word.endswith(suffix):
                        is_positive = True
                        break
                if not is_positive:
                    for suffix in sentiment_dict['negative']['suffixes']:
                        if word.endswith(suffix):
                            is_negative = True
                            break
        
        # 检查周围是否有否定词，反转情感
        negated = False
        window_size = 2
        for j in range(max(0, i - window_size), i):
            if words[j] in sentiment_dict['negators']:
                negated = True
                break
        
        # 更新计数
        if is_positive:
            if negated:
                negative_count += 1
            else:
                positive_count += 1
        elif is_negative:
            if negated:
                positive_count += 1
            else:
                negative_count += 1
    
    # 计算情感强度
    sentiment_score = (positive_count - negative_count) / max(total_words, 1)
    
    # 调整情感阈值，使情感分布更合理
    if sentiment_score > 0.02:
        sentiment_label = "positive"
    elif sentiment_score < -0.01:  # 降低消极阈值
        sentiment_label = "negative"
    else:
        sentiment_label = "neutral"
    
    return {
        'sentiment_label': sentiment_label,
        'sentiment_intensity': round(sentiment_score, 4),
        'positive_words_count': positive_count,
        'negative_words_count': negative_count,
        'total_words_count': total_words
    }

# 主函数
def main():
    # 文件路径
    input_file = '清洗数据/enhanced_cleaned_data.csv'
    output_file = '清洗数据/final_sentiment_analyzed_data.csv'
    
    print("正在读取增强后的数据...")
    # 读取增强后的数据
    df = pd.read_csv(input_file, usecols=['original_index', 'data_type', 'title', 'summary', 'cleaned_title', 'cleaned_summary', 'combined_text', 'date', 'category', 'source', 'scraped_time'])
    
    print(f"数据总量: {len(df)} 条")
    
    # 对每条新闻进行情感分析
    print("\n正在进行最终版情感分析...")
    
    # 使用apply和tqdm提高效率
    tqdm.pandas(desc="情感分析进度")
    
    # 批量处理
    sentiment_results = df.progress_apply(lambda row: pd.Series(analyze_final_sentiment(row['combined_text'])), axis=1)
    
    # 将情感分析结果合并到原数据中
    df_with_sentiment = pd.concat([df, sentiment_results], axis=1)
    
    # 保存结果
    print("\n正在保存最终版情感分析结果...")
    df_with_sentiment.to_csv(output_file, index=False, encoding='utf-8')
    
    print("✓ 最终版情感分析完成！")
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