import json
import pandas as pd
import re

# 读取JSON文件
def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 统计数据数量
def count_data_entries(data):
    return len(data)

# 简单的文本清洗函数
def simple_clean_text(text):
    if not text:
        return ''
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 移除特殊字符
    text = re.sub(r'[^a-zA-Z\sÀ-ÿ]', '', text)
    # 转换为小写
    text = text.lower()
    # 移除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 主函数
def main():
    # 文件路径
    file_path = '清洗数据.json'
    
    # 读取数据
    print("正在读取JSON文件...")
    data = read_json_file(file_path)
    
    # 统计数据数量
    count = count_data_entries(data)
    print(f"✓ JSON文件中共有 {count} 条数据")
    
    # 转换为DataFrame
    df = pd.DataFrame(data)
    
    # 查看数据列
    print("\n数据列:", df.columns.tolist())
    
    # 简单预处理：只处理title和summary列
    print("\n正在进行简单数据预处理...")
    
    # 处理title列
    if 'title' in df.columns:
        print("1. 清洗title列...")
        df['cleaned_title'] = df['title'].apply(simple_clean_text)
    
    # 处理summary列
    if 'summary' in df.columns:
        print("2. 清洗summary列...")
        df['cleaned_summary'] = df['summary'].apply(simple_clean_text)
    
    # 处理content列（如果存在）
    if 'content' in df.columns:
        print("3. 清洗content列...")
        df['cleaned_content'] = df['content'].apply(simple_clean_text)
    
    # 保存处理后的数据
    print("\n保存预处理后的数据...")
    df.to_csv('simple_preprocessed.csv', index=False, encoding='utf-8')
    print("✓ 预处理后的数据已保存到 simple_preprocessed.csv")
    
    # 显示前3行预处理结果
    print("\n预处理结果示例（前3行）:")
    columns_to_show = ['title', 'cleaned_title', 'summary', 'cleaned_summary'] if 'summary' in df.columns else ['title', 'cleaned_title', 'content', 'cleaned_content']
    columns_to_show = [col for col in columns_to_show if col in df.columns]
    print(df[columns_to_show].head(3))

if __name__ == "__main__":
    main()