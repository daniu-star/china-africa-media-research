import pandas as pd
from tqdm import tqdm
import re

# 改进的情感词典，扩大词汇量并添加更多领域相关词汇
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
            'war', 'conflict', 'dispute', 'fight', 'battle', 'attack', 'invade', 'invation',
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
    'neutral': {
        'words': [
            # 时间相关词汇
            'time', 'date', 'day', 'week', 'month', 'year', 'hour', 'minute', 'second',
            'today', 'tomorrow', 'yesterday', 'now', 'then', 'before', 'after', 'during',
            
            # 数字和数量相关词汇
            'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
            'hundred', 'thousand', 'million', 'billion', 'trillion', 'many', 'much', 'few', 'little',
            'some', 'any', 'all', 'every', 'each', 'none', 'no',
            
            # 地点相关词汇
            'place', 'location', 'area', 'region', 'country', 'nation', 'state', 'city', 'town',
            'village', 'continent', 'ocean', 'sea', 'river', 'lake', 'mountain', 'hill', 'valley',
            
            # 人物相关词汇
            'person', 'people', 'man', 'woman', 'child', 'boy', 'girl', 'man', 'woman',
            'leader', 'president', 'prime', 'minister', 'king', 'queen', 'prince', 'princess',
            'official', 'officer', 'worker', 'employee', 'employer', 'boss', 'manager', 'director',
            
            # 其他中性词汇
            'say', 'speak', 'talk', 'tell', 'ask', 'answer', 'reply', 'respond',
            'think', 'believe', 'know', 'understand', 'learn', 'study', 'research',
            'see', 'look', 'watch', 'hear', 'listen', 'feel', 'touch', 'smell', 'taste',
            'do', 'make', 'create', 'build', 'construct', 'produce', 'manufacture', 'work'
        ]
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

# 定义改进的规则基情感分析函数
def analyze_improved_sentiment(text):
    if not text or pd.isna(text):
        return {
            'sentiment_label': 'neutral',
            'sentiment_intensity': 0.0,
            'positive_words_count': 0,
            'negative_words_count': 0,
            'neutral_words_count': 0,
            'total_words_count': 0,
            'negators_count': 0,
            'intensifiers_count': 0
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
            'neutral_words_count': 0,
            'total_words_count': 0,
            'negators_count': 0,
            'intensifiers_count': 0
        }
    
    # 初始化计数
    positive_count = 0.0
    negative_count = 0.0
    neutral_count = 0.0
    negators_count = 0.0
    intensifiers_count = 0.0
    
    # 窗口大小，用于处理否定词和程度副词
    window_size = 3
    
    for i, word in enumerate(words):
        # 检查是否为否定词
        if word in sentiment_dict['negators']:
            negators_count += 1
            continue
        
        # 检查是否为程度副词
        if word in sentiment_dict['intensifiers']:
            intensifiers_count += 1
            continue
        
        # 检查是否为中性词
        if word in sentiment_dict['neutral']['words']:
            neutral_count += 1
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
        for j in range(max(0, i - window_size), i):
            if words[j] in sentiment_dict['negators']:
                negated = True
                break
        
        # 检查周围是否有程度副词，增强情感
        intensified = 1.0
        for j in range(max(0, i - window_size), i):
            if words[j] in sentiment_dict['intensifiers']:
                intensified = 1.5
                break
        
        # 更新计数
        if is_positive:
            if negated:
                negative_count += 1.0 * intensified
            else:
                positive_count += 1.0 * intensified
        elif is_negative:
            if negated:
                positive_count += 1.0 * intensified
            else:
                negative_count += 1.0 * intensified
        else:
            neutral_count += 1
    
    # 计算情感强度
    # 考虑中性词的影响，中性词越多，情感强度越弱
    neutral_ratio = neutral_count / total_words
    sentiment_score = (positive_count - negative_count) / max(total_words, 1)
    
    # 根据中性词比例调整情感强度
    adjusted_score = sentiment_score * (1 - neutral_ratio)
    
    # 确定情感标签，调整阈值以获得更合理的分布
    if adjusted_score > 0.05:
        sentiment_label = "positive"
    elif adjusted_score < -0.05:
        sentiment_label = "negative"
    else:
        sentiment_label = "neutral"
    
    return {
        'sentiment_label': sentiment_label,
        'sentiment_intensity': round(adjusted_score, 4),
        'positive_words_count': round(positive_count, 1),
        'negative_words_count': round(negative_count, 1),
        'neutral_words_count': round(neutral_count, 1),
        'total_words_count': total_words,
        'negators_count': int(negators_count),
        'intensifiers_count': int(intensifiers_count)
    }

# 主函数
def main():
    # 文件路径
    input_file = '清洗数据/enhanced_cleaned_data.csv'
    output_file = '清洗数据/improved_sentiment_analyzed_data.csv'
    
    print("正在读取增强后的数据...")
    # 读取增强后的数据
    df = pd.read_csv(input_file, usecols=['original_index', 'data_type', 'title', 'summary', 'cleaned_title', 'cleaned_summary', 'combined_text', 'date', 'category', 'source', 'scraped_time'])
    
    print(f"数据总量: {len(df)} 条")
    
    # 对每条新闻进行情感分析
    print("\n正在进行改进版情感分析...")
    
    # 使用apply和tqdm提高效率
    tqdm.pandas(desc="情感分析进度")
    
    # 批量处理
    sentiment_results = df.progress_apply(lambda row: pd.Series(analyze_improved_sentiment(row['combined_text'])), axis=1)
    
    # 将情感分析结果合并到原数据中
    df_with_sentiment = pd.concat([df, sentiment_results], axis=1)
    
    # 保存结果
    print("\n正在保存改进版情感分析结果...")
    df_with_sentiment.to_csv(output_file, index=False, encoding='utf-8')
    
    print("✓ 改进版情感分析完成！")
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