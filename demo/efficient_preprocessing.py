import json
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm

# 读取JSON文件并返回生成器，逐行处理
def read_json_generator(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for item in data:
        yield item

# 文本清洗函数
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

# 主函数
def main():
    file_path = '清洗数据.json'
    
    # 统计数据数量
    print("正在统计数据数量...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    total_count = len(data)
    print(f"✓ 总数据量: {total_count} 条")
    
    # 准备数据列表
    titles = []
    summaries = []
    
    # 逐行读取和处理数据
    print("\n正在进行数据清洗...")
    for item in tqdm(read_json_generator(file_path), total=total_count, desc="处理进度"):
        if isinstance(item, dict):
            # 处理title
            title = item.get('title', '')
            cleaned_title = clean_text(title)
            titles.append(cleaned_title)
            
            # 处理summary
            summary = item.get('summary', '')
            cleaned_summary = clean_text(summary)
            summaries.append(cleaned_summary)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'title': titles,
        'summary': summaries
    })
    
    # 合并title和summary用于向量化
    df['combined_text'] = df['title'] + ' ' + df['summary']
    
    # 使用TF-IDF进行向量化
    print("\n正在进行TF-IDF向量化...")
    vectorizer = TfidfVectorizer(max_features=1000, min_df=2, max_df=0.95)
    tfidf_matrix = vectorizer.fit_transform(df['combined_text'])
    
    # 将向量化结果转换为DataFrame
    tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=vectorizer.get_feature_names_out())
    
    # 保存结果
    print("\n正在保存结果...")
    df.to_csv('cleaned_data.csv', index=False, encoding='utf-8')
    tfidf_df.to_csv('tfidf_vectorized.csv', index=False, encoding='utf-8')
    
    print("✓ 数据预处理完成！")
    print(f"✓ 清洗后的数据已保存到 cleaned_data.csv")
    print(f"✓ TF-IDF向量化结果已保存到 tfidf_vectorized.csv")
    print(f"✓ 数据形状: {df.shape}")
    print(f"✓ 向量化结果形状: {tfidf_df.shape}")

if __name__ == "__main__":
    main()