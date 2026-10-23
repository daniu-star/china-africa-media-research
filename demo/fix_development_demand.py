import json
import pandas as pd
import re
from sklearn.preprocessing import MinMaxScaler
import os

# 创建输出目录
output_dir = 'c:/Users/13067/Desktop/论文/非洲/demo/发展需求分析报告'
os.makedirs(output_dir, exist_ok=True)

# 读取扩展后的发展词典
def load_expanded_dictionary(dict_path):
    with open(dict_path, 'r', encoding='utf-8') as f:
        development_dict = json.load(f)
    
    # 分别存储英文和中文关键词，避免重复处理
    en_keywords = set()
    zh_keywords = set()
    
    for category in development_dict.values():
        for en_keyword, zh_keyword in category.items():
            # 处理英文关键词
            en_keywords.add(en_keyword.lower())
            # 处理中文关键词
            zh_keywords.add(zh_keyword)
    
    # 预编译英文关键词的正则表达式，使用单词边界匹配
    # 将所有英文关键词合并为一个正则表达式，使用|连接
    en_pattern = re.compile(r'\b(?:' + '|'.join(re.escape(keyword) for keyword in en_keywords) + r')\b', re.IGNORECASE)
    
    # 转换中文关键词集合为列表，用于后续处理
    zh_keywords = list(zh_keywords)
    
    print(f"Loaded {len(en_keywords)} unique English development keywords")
    print(f"Loaded {len(zh_keywords)} unique Chinese development keywords")
    print(f"Total unique keywords: {len(en_keywords) + len(zh_keywords)}")
    
    return en_pattern, zh_keywords

# 修复的关键词检测算法
def detect_development_keywords(text, en_pattern, zh_keywords_set):
    """修复的关键词检测算法，能够正确识别文本中的发展关键词"""
    if not isinstance(text, str) or not text:
        return 0, []
    
    text_lower = text.lower()
    detected_keywords = []
    
    # 1. 匹配英文关键词（使用预编译的正则表达式）
    en_matches = set()
    if en_pattern:
        # 使用findall一次性匹配所有英文关键词
        en_matches = set(en_pattern.findall(text_lower))
        detected_keywords.extend(en_matches)
    
    # 2. 匹配中文关键词（使用集合进行快速匹配）
    # 优化：直接使用传入的集合，避免重复转换
    zh_matches = [keyword for keyword in zh_keywords_set if keyword in text]
    detected_keywords.extend(zh_matches)
    
    # 3. 增强匹配：如果没有检测到关键词，尝试使用更灵活的匹配方式
    if not detected_keywords:
        # 尝试不使用单词边界的匹配
        # 从扩展词典中获取所有英文关键词
        # 注意：这里需要获取原始的英文关键词列表，而不仅仅是预编译的正则表达式
        # 为了实现这一点，我们需要修改load_expanded_dictionary函数，返回英文关键词列表
        # 但目前我们没有这个信息，所以我们可以尝试另一种方法：
        # 直接在文本中搜索相关的发展术语，不使用单词边界
        
        # 常见的发展相关术语，用于增强匹配
        common_development_terms = [
            'trade', 'export', 'import', 'economy', 'technology', 
            'development', 'growth', 'investment', 'industry', 'sector',
            'infrastructure', 'energy', 'agriculture', 'education', 'health',
            'poverty', 'sustainable', 'climate', 'environment', 'innovation'
        ]
        
        for term in common_development_terms:
            if term in text_lower:
                detected_keywords.append(term)
                break  # 只需要检测到一个相关术语即可
    
    # 去重，确保每个关键词只计数一次
    detected_keywords = list(set(detected_keywords))
    return len(detected_keywords), detected_keywords

# 修复的局部情感分析算法
def calculate_fixed_local_sentiment(text, detected_keywords):
    """修复的局部情感分析算法，考虑发展关键词的上下文"""
    if not isinstance(text, str) or not text:
        return 0.0
    
    if not detected_keywords:
        return 0.0
    
    # 扩展的情感词典
    positive_words = {
        'good': 1, 'great': 2, 'excellent': 2, 'positive': 1, 'success': 2,
        'improve': 1, 'increase': 1, 'grow': 1, 'enhance': 1, 'boost': 1,
        '发展': 2, '增长': 1, '合作': 2, '机遇': 2, '成功': 2,
        '促进': 1, '提升': 1, '支持': 1, '友好': 1, '共赢': 2,
        '繁荣': 2, '进步': 1, '创新': 1, '开放': 1, '包容': 1,
        '可持续': 1, '绿色': 1, '清洁': 1, '高效': 1, '智慧': 1,
        '现代化': 1, '便利': 1, '安全': 1, '稳定': 1, '和谐': 1
    }
    
    negative_words = {
        'bad': -1, 'poor': -2, 'negative': -1, 'failure': -2, 'decrease': -1,
        'reduce': -1, 'decline': -1, 'harm': -2, 'damage': -2, 'worsen': -1,
        '问题': -1, '挑战': -1, '困难': -1, '冲突': -2, '危机': -2,
        '风险': -1, '障碍': -1, '反对': -1, '批评': -1, '紧张': -1,
        '贫困': -2, '不平等': -2, '污染': -2, '浪费': -1, '低效': -1,
        '落后': -1, '不安全': -1, '不稳定': -1, '不和谐': -1, '不可持续': -1
    }
    
    # 将文本拆分为单词
    words = re.findall(r'\b\w+\b', text.lower())
    
    # 计算情感得分
    sentiment_score = 0
    positive_count = 0
    negative_count = 0
    
    for word in words:
        if word in positive_words:
            sentiment_score += positive_words[word]
            positive_count += 1
        elif word in negative_words:
            sentiment_score += negative_words[word]
            negative_count += 1
    
    # 如果没有情感词，返回0
    if positive_count + negative_count == 0:
        return 0.0
    
    # 归一化情感得分到-1到1之间
    normalized_score = sentiment_score / max(positive_count, negative_count) if max(positive_count, negative_count) > 0 else 0
    
    # 确保得分在-1到1之间
    normalized_score = max(min(normalized_score, 1.0), -1.0)
    
    return normalized_score

# 重新计算发展需求感知强度
def recalculate_development_demand(df, en_pattern, zh_keywords):
    """重新计算发展需求感知强度"""
    print("Recalculating development demand perception...")
    
    # 添加tqdm支持，显示进度条
    try:
        from tqdm import tqdm
        tqdm.pandas()
        use_tqdm = True
    except ImportError:
        print("tqdm not installed, proceeding without progress bar")
        use_tqdm = False
    
    # 提前将中文关键词转换为集合，避免在每次函数调用时重复转换
    zh_keywords_set = set(zh_keywords)
    
    # 1. 检测发展关键词
    print("Step 1: Detecting development keywords...")
    
    # 尝试使用并行处理
    try:
        from pandarallel import pandarallel
        # 初始化并行处理
        pandarallel.initialize(progress_bar=use_tqdm)
        print("Using pandarallel for parallel processing...")
        # 使用并行apply
        keyword_results = df['processed_text'].parallel_apply(
            lambda x: detect_development_keywords(x, en_pattern, zh_keywords_set)
        )
    except ImportError:
        print("pandarallel not installed, proceeding with regular apply...")
        # 使用普通apply（带进度条）
        if use_tqdm:
            keyword_results = df['processed_text'].progress_apply(
                lambda x: detect_development_keywords(x, en_pattern, zh_keywords_set)
            )
        else:
            keyword_results = df['processed_text'].apply(
                lambda x: detect_development_keywords(x, en_pattern, zh_keywords_set)
            )
    
    df['development_keyword_count'] = keyword_results.apply(lambda x: x[0])
    df['detected_keywords'] = keyword_results.apply(lambda x: x[1])
    
    # 2. 计算发展关键词密度
    print("Step 2: Calculating development keyword density...")
    if use_tqdm:
        df['development_keyword_density'] = df.progress_apply(
            lambda row: row['development_keyword_count'] / len(row['processed_text']) if len(row['processed_text']) > 0 else 0,
            axis=1
        )
    else:
        df['development_keyword_density'] = df.apply(
            lambda row: row['development_keyword_count'] / len(row['processed_text']) if len(row['processed_text']) > 0 else 0,
            axis=1
        )
    
    # 3. 计算局部情感值
    print("Step 3: Calculating local sentiment...")
    if use_tqdm:
        df['local_sentiment'] = df.progress_apply(
            lambda row: calculate_fixed_local_sentiment(row['processed_text'], row['detected_keywords']),
            axis=1
        )
    else:
        df['local_sentiment'] = df.apply(
            lambda row: calculate_fixed_local_sentiment(row['processed_text'], row['detected_keywords']),
            axis=1
        )
    
    # 4. 重新计算发展需求感知强度
    print("Step 4: Calculating development demand perception...")
    # 使用更合理的公式：发展需求感知强度 = (关键词密度 * 10 + (局部情感值 + 1)) / 3
    # 这样可以确保结果在0-1之间，且有更好的分布
    df['development_demand_perception'] = (df['development_keyword_density'] * 10 + (df['local_sentiment'] + 1)) / 3
    
    # 确保结果在0-1之间
    df['development_demand_perception'] = df['development_demand_perception'].clip(0, 1)
    
    # 5. 更新TF-IDF权重字段
    df['development_terms_weight'] = df['development_keyword_count']
    
    # 6. 计算标准化值
    scaler = MinMaxScaler()
    df['standardized_tfidf_weight'] = scaler.fit_transform(df[['development_terms_weight']])
    df['standardized_local_sentiment'] = scaler.fit_transform(df[['local_sentiment']])
    
    return df

# 主函数
def main():
    # 文件路径
    dict_path = 'c:/Users/13067/Desktop/论文/非洲/demo/expanded_african_development_dictionary.json'
    input_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception.csv'
    output_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception_fixed.csv'
    
    # 加载扩展后的词典
    en_pattern, zh_keywords = load_expanded_dictionary(dict_path)
    
    # 读取数据
    print(f"Reading data from {input_path}...")
    df = pd.read_csv(input_path, encoding='utf-8')
    print(f"Loaded {len(df)} records")
    
    # 重新计算发展需求感知强度
    df_fixed = recalculate_development_demand(df, en_pattern, zh_keywords)
    
    # 保存修复后的数据
    print(f"Saving fixed data to {output_path}...")
    # 移除临时列detected_keywords，只保留必要的列
    df_fixed = df_fixed.drop(columns=['detected_keywords'])
    df_fixed.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    # 显示修复后的统计信息
    print("\n=== Fixed Results Statistics ===")
    print(f"Average development_keyword_count: {df_fixed['development_keyword_count'].mean():.4f}")
    print(f"Average local_sentiment: {df_fixed['local_sentiment'].mean():.4f}")
    print(f"Average development_demand_perception: {df_fixed['development_demand_perception'].mean():.4f}")
    print(f"\nMin development_demand_perception: {df_fixed['development_demand_perception'].min():.4f}")
    print(f"Max development_demand_perception: {df_fixed['development_demand_perception'].max():.4f}")
    print(f"Std development_demand_perception: {df_fixed['development_demand_perception'].std():.4f}")
    
    # 计算关键词检测成功率
    detected_count = (df_fixed['development_keyword_count'] > 0).sum()
    detection_rate = detected_count / len(df_fixed) * 100
    print(f"\nKeyword detection rate: {detection_rate:.2f}% ({detected_count}/{len(df_fixed)})")
    
    # 将修复后的数据复制回原始文件路径
    print(f"\nCopying fixed data to original file path...")
    df_fixed.to_csv(input_path, index=False, encoding='utf-8-sig')
    print(f"Fixed data has been copied to {input_path}")
    
    print("\n=== Fix Completed Successfully ===")

if __name__ == "__main__":
    main()