import pandas as pd
import numpy as np
import re
import os
from gensim import corpora, models
import gensim

# 设置结果保存目录
output_dir = 'c:/Users/13067/Desktop/论文/非洲/demo/议题集中度分析结果'
os.makedirs(output_dir, exist_ok=True)

# 构建大型、合理的停用词库
expanded_stopwords = set([
    # 基础代词、动词、冠词等
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
    "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
    'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them',
    'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll",
    'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
    'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or',
    'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
    'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from',
    'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
    'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now',
    'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn',
    "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn',
    "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't",
    'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
])

# 简化的词形还原函数，直接返回原词
def simple_lemmatize(word):
    return word

# 数据预处理函数
def preprocess_text(text):
    """对文本进行预处理：清洗、分词、去停用词、词形还原"""
    if not isinstance(text, str) or not text:
        return []
    
    # 1. 转换为小写
    text = text.lower()
    
    # 2. 移除特殊字符和数字
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # 3. 简化的分词方法：直接按空格分词，避免依赖punkt和punkt_tab资源
    tokens = text.split()
    
    # 4. 去停用词
    tokens = [token for token in tokens if token not in expanded_stopwords]
    
    # 5. 词形还原（简化版本）
    tokens = [simple_lemmatize(token) for token in tokens]
    
    # 6. 移除短词（长度小于3）
    tokens = [token for token in tokens if len(token) > 2]
    
    return tokens

# 主函数
def main():
    print("=== 议题集中度计算开始 ===")
    
    # 1. 读取数据
    print("Step 1: 读取数据...")
    data_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception.csv'
    df = pd.read_csv(data_path, encoding='utf-8')
    print(f"数据总量: {len(df)} 条记录")
    
    # 2. 数据预处理
    print("Step 2: 数据预处理...")
    
    # 对processed_text字段进行预处理
    df['processed_tokens'] = df['processed_text'].apply(preprocess_text)
    
    # 过滤掉空列表
    df = df[df['processed_tokens'].apply(len) > 0]
    print(f"预处理后的数据量: {len(df)} 条记录")
    
    # 3. 构建词典和语料库
    print("Step 3: 构建词典和语料库...")
    
    # 构建词典
    dictionary = corpora.Dictionary(df['processed_tokens'])
    
    # 过滤低频词和高频词
    # 只保留在10个文档以上出现且在总文档数50%以下出现的词
    dictionary.filter_extremes(no_below=10, no_above=0.5)
    
    # 构建语料库
    corpus = [dictionary.doc2bow(tokens) for tokens in df['processed_tokens']]
    
    print(f"词典大小: {len(dictionary)} 个词")
    print(f"语料库大小: {len(corpus)} 个文档")
    
    # 保存词典和语料库
    dictionary.save(os.path.join(output_dir, 'dictionary.gensim'))
    corpora.MmCorpus.serialize(os.path.join(output_dir, 'corpus.mm'), corpus)
    print("词典和语料库保存完成")
    
    # 4. 训练LDA模型
    print("Step 4: 训练LDA模型...")
    
    # 设置LDA模型参数
    num_topics = 15
    passes = 20  # 减少迭代次数，加快训练速度
    alpha = 'auto'
    eta = 'auto'
    
    # 使用LdaModel代替LdaMulticore，因为LdaMulticore不支持auto alpha
    lda_model = gensim.models.LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=num_topics,
        passes=passes,
        alpha=alpha,
        eta=eta,
        random_state=42
    )
    
    # 保存LDA模型
    lda_model.save(os.path.join(output_dir, 'lda_model.gensim'))
    print("LDA模型训练完成并保存")
    
    # 5. 提取主题和主题词
    print("Step 5: 提取主题和主题词...")
    
    # 提取每个主题的前20个关键词
    topics = lda_model.print_topics(num_words=20)
    
    # 保存主题词到文件
    topic_file_path = os.path.join(output_dir, 'topic_terms.txt')
    with open(topic_file_path, 'w', encoding='utf-8') as f:
        for topic in topics:
            f.write(f"Topic {topic[0]}: {topic[1]}\n\n")
    
    # 保存主题词为CSV格式，便于人工标注
    topic_terms = []
    for topic_id in range(num_topics):
        terms = lda_model.show_topic(topic_id, topn=20)
        topic_terms.append([topic_id] + [term[0] for term in terms])
    
    topic_df = pd.DataFrame(topic_terms, columns=['topic_id'] + [f'term_{i+1}' for i in range(20)])
    topic_df['core_issue'] = ''  # 预留人工标注列
    topic_df.to_csv(os.path.join(output_dir, 'topic_annotation.csv'), index=False, encoding='utf-8-sig')
    
    # 6. 计算每个文档的主题概率分布
    print("Step 6: 计算文档主题概率分布...")
    
    # 计算每个文档的主题概率分布
    doc_topics = []
    for idx, bow in enumerate(corpus):
        topics = lda_model.get_document_topics(bow, minimum_probability=0.0)
        # 将主题概率转换为字典格式
        topic_probs = {topic[0]: topic[1] for topic in topics}
        doc_topics.append(topic_probs)
    
    # 将主题概率添加到DataFrame
    for topic_id in range(num_topics):
        df[f'topic_{topic_id}_prob'] = df.index.map(lambda idx: doc_topics[idx].get(topic_id, 0.0))
    
    # 7. 人工标注核心议题（这里先使用预设的标注，实际应人工完成）
    print("Step 7: 人工标注核心议题...")
    
    # 这里使用预设的核心议题标注，实际应用中应人工完成
    # 核心议题类别：合作发展、全球治理、基础设施、经贸合作、人文交流、安全合作、科技合作、农业合作
    core_issue_mapping = {
        0: '合作发展',
        1: '全球治理',
        2: '基础设施',
        3: '经贸合作',
        4: '人文交流',
        5: '安全合作',
        6: '科技合作',
        7: '农业合作',
        8: '合作发展',
        9: '全球治理',
        10: '基础设施',
        11: '经贸合作',
        12: '人文交流',
        13: '安全合作',
        14: '科技合作'
    }
    
    # 保存核心议题映射
    core_issue_df = pd.DataFrame(list(core_issue_mapping.items()), columns=['topic_id', 'core_issue'])
    core_issue_df.to_csv(os.path.join(output_dir, 'core_issue_mapping.csv'), index=False, encoding='utf-8-sig')
    
    # 8. 计算每个文档的核心议题概率
    print("Step 8: 计算核心议题概率...")
    
    # 核心议题列表
    core_issues = list(set(core_issue_mapping.values()))
    
    # 计算每个文档的核心议题概率
    for issue in core_issues:
        # 获取该核心议题对应的所有主题
        related_topics = [topic_id for topic_id, core_issue in core_issue_mapping.items() if core_issue == issue]
        # 计算该核心议题的总概率
        df[issue] = df[[f'topic_{topic_id}_prob' for topic_id in related_topics]].sum(axis=1)
    
    # 9. 计算年度HHI指数
    print("Step 9: 计算年度HHI指数...")
    
    # 按年份分组
    yearly_groups = df.groupby('year')
    
    # 计算每个年份的HHI指数
    yearly_hhi = {}
    
    for year, group in yearly_groups:
        # 计算该年份所有报道在核心议题上的平均概率
        issue_probs = group[core_issues].mean()
        
        # 计算HHI指数
        hhi = sum(prob ** 2 for prob in issue_probs)
        yearly_hhi[year] = hhi
    
    # 保存年度HHI指数
    yearly_hhi_df = pd.DataFrame(list(yearly_hhi.items()), columns=['year', 'hhi_index'])
    yearly_hhi_df.to_csv(os.path.join(output_dir, 'yearly_hhi.csv'), index=False, encoding='utf-8-sig')
    print(f"年度HHI指数计算完成，共{len(yearly_hhi)}个年份")
    
    # 10. 将HHI指数赋给每个年份的报道
    print("Step 10: 整合结果...")
    
    # 添加issue_concentration字段
    df['issue_concentration'] = df['year'].map(yearly_hhi)
    
    # 11. 保存更新后的数据
    print("Step 11: 保存更新后的数据...")
    
    # 移除临时列
    temp_cols = ['processed_tokens'] + [f'topic_{i}_prob' for i in range(num_topics)]
    df = df.drop(columns=temp_cols)
    
    # 保存更新后的数据
    updated_data_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception.csv'
    df.to_csv(updated_data_path, index=False, encoding='utf-8-sig')
    print(f"数据更新完成，添加了issue_concentration字段")
    
    # 12. 生成结果报告
    print("Step 12: 生成结果报告...")
    
    report_path = os.path.join(output_dir, '议题集中度分析报告.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=== 议题集中度分析报告 ===\n\n")
        f.write(f"数据总量: {len(df)} 条记录\n")
        f.write(f"核心议题数量: {len(core_issues)} 个\n")
        f.write(f"核心议题列表: {', '.join(core_issues)}\n\n")
        f.write("年度HHI指数:\n")
        for year, hhi in sorted(yearly_hhi.items()):
            f.write(f"{year}: {hhi:.6f}\n")
        f.write(f"\nHHI指数范围: {min(yearly_hhi.values()):.6f} - {max(yearly_hhi.values()):.6f}\n")
        f.write(f"HHI指数平均值: {sum(yearly_hhi.values())/len(yearly_hhi):.6f}\n")
    
    print("议题集中度计算完成！")
    print(f"结果保存在: {output_dir}")

if __name__ == "__main__":
    main()
