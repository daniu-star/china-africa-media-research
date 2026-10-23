import json
import pandas as pd

# 主函数
def main():
    # 文件路径
    json_file_path = '清洗数据/清洗数据.json'
    cleaned_csv_path = '清洗数据/comprehensive_cleaned_data.csv'
    output_csv_path = '清洗数据/enhanced_cleaned_data.csv'
    
    print("正在读取原始JSON数据...")
    # 读取原始JSON数据
    with open(json_file_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    print("正在读取清洗后的数据...")
    # 读取清洗后的数据
    cleaned_df = pd.read_csv(cleaned_csv_path)
    
    # 准备要添加的字段
    dates = []
    categories = []
    sources = []
    scraped_times = []
    
    print("正在匹配和添加字段...")
    # 遍历清洗后的数据，根据original_index匹配原始数据
    for idx, row in cleaned_df.iterrows():
        original_idx = row['original_index']
        
        # 检查原始索引是否在有效范围内
        if 0 <= original_idx < len(original_data):
            original_item = original_data[original_idx]
            
            if isinstance(original_item, dict):
                # 字典类型数据，提取相关字段
                dates.append(original_item.get('date', ''))
                categories.append(original_item.get('category', ''))
                sources.append(original_item.get('source', ''))
                scraped_times.append(original_item.get('scraped_time', ''))
            else:
                # 非字典类型数据，添加空值
                dates.append('')
                categories.append('')
                sources.append('')
                scraped_times.append('')
        else:
            # 索引无效，添加空值
            dates.append('')
            categories.append('')
            sources.append('')
            scraped_times.append('')
    
    # 将新字段添加到DataFrame
    cleaned_df['date'] = dates
    cleaned_df['category'] = categories
    cleaned_df['source'] = sources
    cleaned_df['scraped_time'] = scraped_times
    
    # 保存增强后的数据
    print("正在保存增强后的数据...")
    cleaned_df.to_csv(output_csv_path, index=False, encoding='utf-8')
    
    print("✓ 数据增强完成！")
    print(f"✓ 增强后的数据已保存到 {output_csv_path}")
    print(f"✓ 数据形状: {cleaned_df.shape}")
    print(f"✓ 新增字段: date, category, source, scraped_time")
    
    # 显示前5行数据，验证结果
    print("\n增强后的数据示例（前5行）:")
    print(cleaned_df[['original_index', 'title', 'date', 'source', 'category']].head())

if __name__ == "__main__":
    main()