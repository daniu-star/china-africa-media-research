import json
import pandas as pd
import re
from sklearn.preprocessing import MinMaxScaler
import os

# 简化的情感分析器
class SimpleSentimentAnalyzer:
    def polarity_scores(self, text):
        positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'improve', 'increase', 'grow', 'enhance', 'boost']
        negative_words = ['bad', 'poor', 'negative', 'failure', 'decrease', 'reduce', 'decline', 'harm', 'damage', 'worsen']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count + neg_count == 0:
            return {'compound': 0.0}
        
        score = (pos_count - neg_count) / (pos_count + neg_count)
        return {'compound': score}

def main():
    print("=== 重新处理所有数据 ===")
    
    # 文件路径
    raw_data_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/原始数据.json'
    output_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception.csv'
    
    # 读取原始数据
    print(f"读取原始数据: {raw_data_path}")
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    print(f"原始数据记录数: {len(raw_data)}")
    
    # 转换为DataFrame
    print("转换为DataFrame...")
    df = pd.DataFrame(raw_data)
    print(f"转换后记录数: {len(df)}")
    
    # 确保必要的列存在
    required_columns = ['title', 'summary', 'date', 'category', 'source', 'url', 'content']
    for col in required_columns:
        if col not in df.columns:
            df[col] = ''
    
    # 创建combined_text列
    df['combined_text'] = df['title'].fillna('') + ' ' + df['summary'].fillna('') + ' ' + df['content'].fillna('')
    
    # 创建processed_text列（简化处理）
    def simple_preprocess(text):
        if not isinstance(text, str):
            return ''
        # 转换为小写
        text = text.lower()
        # 移除特殊字符，只保留字母、数字和空格
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        # 多个空格替换为一个
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    print("处理文本...")
    df['processed_text'] = df['combined_text'].apply(simple_preprocess)
    
    # 计算发展需求感知相关指标（简化版本，确保所有记录都被处理）
    print("计算发展需求感知指标...")
    
    # 简化的发展关键词列表
    development_keywords = ['development', 'economy', 'growth', 'investment', 'infrastructure', 
                           'education', 'health', 'agriculture', 'technology', 'trade', 'cooperation']
    
    # 计算发展关键词出现次数
    def count_development_keywords(text):
        if not isinstance(text, str):
            return 0
        count = 0
        for keyword in development_keywords:
            count += text.count(keyword)
        return count
    
    df['development_keyword_count'] = df['processed_text'].apply(count_development_keywords)
    
    # 计算文本长度
    df['text_length'] = df['processed_text'].apply(len)
    
    # 计算关键词密度
    def calculate_keyword_density(count, length):
        if length == 0:
            return 0.0
        return count / length
    
    df['development_keyword_density'] = df.apply(lambda row: calculate_keyword_density(row['development_keyword_count'], row['text_length']), axis=1)
    
    # 简化的情感分析
    sia = SimpleSentimentAnalyzer()
    df['sentiment'] = df['processed_text'].apply(lambda x: sia.polarity_scores(x)['compound'])
    
    # 标准化处理
    scaler = MinMaxScaler()
    
    # 创建基本的发展需求感知指标
    df['development_terms_weight'] = df['development_keyword_count']
    df['local_sentiment'] = df['sentiment']
    
    # 标准化
    df['standardized_tfidf_weight'] = scaler.fit_transform(df[['development_terms_weight']])
    df['standardized_local_sentiment'] = scaler.fit_transform(df[['local_sentiment']])
    
    # 计算发展需求感知强度
    df['development_demand_perception'] = df['standardized_tfidf_weight'] * df['standardized_local_sentiment']
    
    # 添加年份列（简化处理）
    def extract_year(date_str):
        if not isinstance(date_str, str):
            return 2023
        # 尝试从日期字符串中提取年份
        year_match = re.search(r'\d{4}', date_str)
        if year_match:
            return int(year_match.group())
        return 2023
    
    df['year'] = df['date'].apply(extract_year)
    
    # 保存初步结果
    intermediate_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/temp_enhanced_data.csv'
    df.to_csv(intermediate_path, index=False, encoding='utf-8-sig')
    print(f"初步结果保存到: {intermediate_path}")
    print(f"初步处理记录数: {len(df)}")
    
    # 继续计算合作纵深性指数
    print("\n=== 计算合作纵深性指数 ===")
    
    # 构建关键词库
    def build_keyword_libraries():
        # 长期战略词库
        long_term_strategic = {
            'long-term': '长期', 'long term': '长期', 'longterm': '长期',
            'strategic': '战略', 'strategy': '战略', 'strategies': '战略', 'strategically': '战略',
            'sustainable': '可持续', 'sustainability': '可持续', 'sustainably': '可持续',
            'enduring': '持久', 'endurance': '持久', 'persistent': '持久', 'persistence': '持久',
            'lasting': '持久', 'permanent': '永久', 'permanence': '永久',
            'future-oriented': '面向未来', 'future oriented': '面向未来', 'futureoriented': '面向未来',
            'forward-looking': '前瞻性', 'forward looking': '前瞻性', 'forwardlooking': '前瞻性',
            'vision': '愿景', 'visionary': '愿景', 'visioning': '愿景',
            'perspective': '视角', 'perspectives': '视角',
            'holistic': '整体', 'comprehensive': '全面',
            'integrated': '整合', 'integration': '整合',
            'systematic': '系统', 'system': '系统', 'systems': '系统',
            'framework': '框架', 'frameworks': '框架',
            'blueprint': '蓝图',
            'roadmap': '路线图', 'road map': '路线图', 'roadmap': '路线图',
            'action plan': '行动计划', 'action_plan': '行动计划', 'actionplan': '行动计划',
            'partnership': '伙伴关系', 'partnerships': '伙伴关系',
            'alliance': '联盟', 'alliances': '联盟',
            'cooperation': '合作', 'cooperative': '合作',
            'collaboration': '协作', 'collaborative': '协作',
            'joint': '联合',
            'mutual': 'mutual',
            'reciprocal': '互惠',
            'win-win': '双赢', 'win win': '双赢', 'winwin': '双赢'
        }
        
        # 多元主体词库（简化版）
        multi_agents = {
            'government': '政府', 'governments': '政府', 'state': '国家', 'states': '国家',
            'enterprise': '企业', 'enterprises': '企业', 'company': '公司', 'companies': '公司',
            'university': '大学', 'universities': '大学', 'research': '研究',
            'ngo': '非政府组织', 'ngos': '非政府组织',
            'education': '教育', 'cultural': '文化', 'technology': '技术',
            'agriculture': '农业', 'health': '卫生', 'medical': '医疗'
        }
        
        return list(long_term_strategic.keys()), list(multi_agents.keys())
    
    long_term_words, multi_agent_words = build_keyword_libraries()
    
    # 计算长期战略词频
    def count_long_term_words(text):
        if not isinstance(text, str) or not text:
            return 0
        count = 0
        for word in long_term_words:
            count += text.count(word)
        return count
    
    # 计算多元主体提及数量
    def count_multi_agents(text):
        if not isinstance(text, str) or not text:
            return 0
        count = 0
        for word in multi_agent_words:
            if word in text:
                count += 1
        return count
    
    print("计算长期战略词频...")
    df['long_term_word_count'] = df['processed_text'].apply(count_long_term_words)
    
    print("计算多元主体互动...")
    df['has_multi_agent_interaction'] = df['processed_text'].apply(count_multi_agents)
    
    print("标准化指标...")
    # 对数变换
    df['long_term_word_count_log'] = df['long_term_word_count'].apply(lambda x: 0 if x == 0 else np.log(x))
    
    # 百分位数赋值
    df['long_term_percentile'] = df['long_term_word_count_log'].rank(pct=True) * 100
    df['multi_agent_percentile'] = df['has_multi_agent_interaction'].rank(pct=True) * 100
    
    # 计算合作纵深性指数
    df['cooperation_depth_index'] = (df['long_term_percentile'] + df['multi_agent_percentile']) / 200
    
    # 确保所有记录都有值
    df['cooperation_depth_index'] = df['cooperation_depth_index'].fillna(0.0)
    
    # 保存最终结果
    print("保存最终结果...")
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"最终结果保存到: {output_path}")
    print(f"最终记录数: {len(df)}")
    
    print("\n=== 处理完成 ===")
    print(f"从 {len(raw_data)} 条原始数据生成了 {len(df)} 条最终记录")
    print("数据处理完成，未丢失大量记录！")

if __name__ == "__main__":
    import numpy as np
    main()
