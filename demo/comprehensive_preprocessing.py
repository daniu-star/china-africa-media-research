import json
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm

# 读取JSON文件
def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

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
    file_path = '清洗数据/清洗数据.json'
    
    # 读取数据
    print("正在读取JSON文件...")
    data = read_json_file(file_path)
    total_count = len(data)
    print(f"✓ 总数据量: {total_count} 条")
    
    # 准备数据列表
    all_data = []
    
    # 处理所有数据
    print("\n正在处理所有数据...")
    for i, item in tqdm(enumerate(data), total=total_count, desc="处理进度"):
        processed_item = {
            'original_index': i,
            'data_type': type(item).__name__,
            'title': '',
            'summary': '',
            'cleaned_title': '',
            'cleaned_summary': ''
        }
        
        if isinstance(item, dict):
            # 处理字典类型数据
            processed_item['title'] = item.get('title', '')
            processed_item['summary'] = item.get('summary', '')
            processed_item['cleaned_title'] = clean_text(processed_item['title'])
            processed_item['cleaned_summary'] = clean_text(processed_item['summary'])
        elif isinstance(item, str):
            # 处理字符串类型数据（可能是URL）
            processed_item['title'] = item
            processed_item['cleaned_title'] = clean_text(item)
        elif isinstance(item, list):
            # 处理列表类型数据
            # 尝试将列表转换为字符串
            list_str = ' '.join(map(str, item))
            processed_item['title'] = list_str
            processed_item['cleaned_title'] = clean_text(list_str)
        
        all_data.append(processed_item)
    
    # 创建DataFrame
    df = pd.DataFrame(all_data)
    
    # 合并cleaned_title和cleaned_summary用于向量化
    df['combined_text'] = df['cleaned_title'] + ' ' + df['cleaned_summary']
    
    # 过滤掉空的combined_text
    df = df[df['combined_text'].str.strip() != ''].reset_index(drop=True)
    
    # 使用TF-IDF进行向量化
    print("\n正在进行TF-IDF向量化...")
    vectorizer = TfidfVectorizer(max_features=1000, min_df=2, max_df=0.95)
    tfidf_matrix = vectorizer.fit_transform(df['combined_text'])
    
    # 将向量化结果转换为DataFrame
    tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=vectorizer.get_feature_names_out())
    
    # 保存结果
    print("\n正在保存结果...")
    df.to_csv('comprehensive_cleaned_data.csv', index=False, encoding='utf-8')
    tfidf_df.to_csv('comprehensive_tfidf_vectorized.csv', index=False, encoding='utf-8')
    
    print("✓ 数据预处理完成！")
    print(f"✓ 总数据量: {total_count} 条")
    print(f"✓ 处理后的数据量: {len(df)} 条")
    print(f"✓ 清洗后的数据已保存到 comprehensive_cleaned_data.csv")
    print(f"✓ TF-IDF向量化结果已保存到 comprehensive_tfidf_vectorized.csv")
    print(f"✓ 向量化结果形状: {tfidf_df.shape}")
    
    # 打印数据类型分布
    print("\n数据类型分布:")
    type_distribution = df['data_type'].value_counts()
    for data_type, count in type_distribution.items():
        print(f"  {data_type}: {count} 条")

if __name__ == "__main__":
    main()