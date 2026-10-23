import csv
import sys

# 增加CSV字段限制
csv.field_size_limit(100000000)

# 定义文件路径
sentiment_csv_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\optimized_sentiment_analyzed_data.csv'
year_csv_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_cleaned_data_with_year.csv'
output_csv_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_cleaned_data_with_year_and_sentiment.csv'

# 读取情感分析数据，存储在字典中
def read_sentiment_data(csv_path):
    print("正在读取情感分析数据...")
    sentiment_dict = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            original_index = row.get('original_index')
            if original_index:
                sentiment_dict[original_index] = {
                    'sentiment_label': row.get('sentiment_label'),
                    'sentiment_intensity': row.get('sentiment_intensity'),
                    'positive_words_count': row.get('positive_words_count'),
                    'negative_words_count': row.get('negative_words_count'),
                    'total_words_count': row.get('total_words_count')
                }
            
            # 显示进度
            if (i + 1) % 1000 == 0:
                print(f'已读取 {i + 1} 条情感分析数据')
    
    print(f"共读取 {len(sentiment_dict)} 条情感分析数据")
    return sentiment_dict

# 合并情感分析数据到带有年份的CSV文件
def merge_data(year_csv_path, sentiment_dict, output_path):
    print("正在合并数据...")
    
    # 读取带有年份的CSV文件
    with open(year_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames.copy()
        
        # 添加情感分析字段
        sentiment_fields = ['sentiment_label', 'sentiment_intensity', 
                           'positive_words_count', 'negative_words_count', 
                           'total_words_count']
        fieldnames.extend(sentiment_fields)
        
        rows = list(reader)
    
    # 合并数据
    for i, row in enumerate(rows):
        original_index = row.get('original_index')
        if original_index in sentiment_dict:
            sentiment_data = sentiment_dict[original_index]
            for field in sentiment_fields:
                row[field] = sentiment_data[field]
        else:
            # 如果没有对应的情感分析数据，填充空值
            for field in sentiment_fields:
                row[field] = ''
        
        # 显示进度
        if (i + 1) % 1000 == 0:
            print(f'已合并 {i + 1} 条数据')
    
    # 写入合并后的文件
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"数据合并完成！")
    print(f"- 总处理条数: {len(rows)}条")

# 执行主函数
if __name__ == "__main__":
    sentiment_dict = read_sentiment_data(sentiment_csv_path)
    merge_data(year_csv_path, sentiment_dict, output_csv_path)
