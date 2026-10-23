import json
import pandas as pd
import re
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk

# 下载必要的NLTK资源
nltk.download('punkt')
nltk.download('stopwords')

# 读取JSON文件
def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 统计数据数量
def count_data_entries(data):
    return len(data)

# 数据清洗函数
def clean_text(text):
    if not text:
        return ''
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 移除特殊字符和数字
    text = re.sub(r'[^a-zA-Z\sÀ-ÿ]', '', text)
    # 转换为小写
    text = text.lower()
    # 移除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 分词和停用词移除函数
def tokenize_and_remove_stopwords(text, language='english'):
    if not text:
        return []
    
    # 分词
    tokens = word_tokenize(text, language=language)
    
    # 获取对应语言的停用词
    try:
        stop_words = set(stopwords.words(language))
    except OSError:
        stop_words = set(stopwords.words('english'))
    
    # 移除停用词和短词
    filtered_tokens = [token for token in tokens if token not in stop_words and len(token) > 2]
    
    return filtered_tokens

# 检测文本语言（简单检测）
def detect_language(text):
    if not text:
        return 'english'
    
    # 简单的语言检测，基于常见词汇
    english_words = set(['the', 'and', 'of', 'to', 'in', 'is', 'it'])
    french_words = set(['le', 'la', 'les', 'et', 'de', 'du', 'des'])
    portuguese_words = set(['o', 'a', 'os', 'as', 'e', 'de', 'do'])
    
    text_lower = text.lower()
    words = text_lower.split()
    
    english_count = sum(1 for word in words if word in english_words)
    french_count = sum(1 for word in words if word in french_words)
    portuguese_count = sum(1 for word in words if word in portuguese_words)
    
    max_count = max(english_count, french_count, portuguese_count)
    
    if max_count == english_count:
        return 'english'
    elif max_count == french_count:
        return 'french'
    elif max_count == portuguese_count:
        return 'portuguese'
    else:
        return 'english'

# 主函数
def main():
    # 文件路径
    file_path = '清洗数据.json'
    
    # 读取数据
    print("正在读取JSON文件...")
    data = read_json_file(file_path)
    
    # 统计数据数量
    count = count_data_entries(data)
    print(f"JSON文件中共有 {count} 条数据")
    
    # 转换为DataFrame
    df = pd.DataFrame(data)
    
    # 查看数据结构
    print("\n数据结构:")
    print(df.columns.tolist())
    print(f"数据形状: {df.shape}")
    
    # 数据预处理
    print("\n正在进行数据预处理...")
    
    # 只处理title和summary列（因为数据中主要是这两列）
    processed_columns = []
    
    # 处理title列
    if 'title' in df.columns:
        print("\n1. 处理title列...")
        # 清洗title
        print("   - 清洗title文本...")
        df['cleaned_title'] = df['title'].apply(clean_text)
        
        # 检测title语言
        print("   - 检测title语言...")
        df['title_language'] = df['cleaned_title'].apply(detect_language)
        
        # 分词和移除停用词
        print("   - 对title进行分词和停用词移除...")
        df['tokenized_title'] = df.apply(lambda x: tokenize_and_remove_stopwords(x['cleaned_title'], x['title_language']), axis=1)
        
        # 将分词结果转换为字符串，用于向量化
        df['processed_title'] = df['tokenized_title'].apply(lambda x: ' '.join(x))
        processed_columns.append('processed_title')
    
    # 处理summary或content列
    content_col = 'summary' if 'summary' in df.columns else 'content' if 'content' in df.columns else None
    if content_col:
        print(f"\n2. 处理{content_col}列...")
        # 清洗内容
        print(f"   - 清洗{content_col}文本...")
        df['cleaned_content'] = df[content_col].apply(clean_text)
        
        # 检测内容语言
        print(f"   - 检测{content_col}语言...")
        df['content_language'] = df['cleaned_content'].apply(detect_language)
        
        # 分词和移除停用词
        print(f"   - 对{content_col}进行分词和停用词移除...")
        df['tokenized_content'] = df.apply(lambda x: tokenize_and_remove_stopwords(x['cleaned_content'], x['content_language']), axis=1)
        
        # 将分词结果转换为字符串，用于向量化
        df['processed_content'] = df['tokenized_content'].apply(lambda x: ' '.join(x))
        processed_columns.append('processed_content')
    
    # 合并处理后的文本列
    if len(processed_columns) > 0:
        print("\n3. 合并处理后的文本列...")
        df['combined_text'] = df[processed_columns].apply(lambda x: ' '.join(x.dropna()), axis=1)
        
        # 使用TF-IDF进行向量化
        print("\n4. 进行TF-IDF向量化...")
        vectorizer = TfidfVectorizer(max_features=1000, min_df=2, max_df=0.95)
        tfidf_matrix = vectorizer.fit_transform(df['combined_text'])
        
        # 将向量化结果转换为DataFrame
        print("   - 转换向量化结果为DataFrame...")
        tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=vectorizer.get_feature_names_out())
        
        # 保存向量化结果
        print("   - 保存向量化结果...")
        tfidf_df.to_csv('tfidf_vectorized.csv', index=False, encoding='utf-8')
        print("   ✓ TF-IDF向量化结果已保存到 tfidf_vectorized.csv")
    
    # 保存处理后的数据
    print("\n5. 保存预处理后的数据...")
    df.to_csv('preprocessed_data.csv', index=False, encoding='utf-8')
    print("   ✓ 预处理后的数据已保存到 preprocessed_data.csv")
    
    # 显示预处理结果示例
    print("\n6. 预处理结果示例:")
    if 'title' in df.columns and 'processed_title' in df.columns:
        sample = df[['title', 'cleaned_title', 'tokenized_title', 'title_language']].head(2)
        print(sample)
    
    if 'processed_content' in df.columns:
        sample_content = df[['cleaned_content', 'tokenized_content', 'content_language']].head(1)
        print("\n内容预处理示例:")
        print(sample_content)
    
    print("\n✓ 数据预处理完成！")

if __name__ == "__main__":
    main()