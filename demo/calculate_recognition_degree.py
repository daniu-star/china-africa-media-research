import pandas as pd
import numpy as np
import sys

# 增加CSV字段限制
import csv
csv.field_size_limit(100000000)

# 定义文件路径
input_csv_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_similarity_ultimate.csv'
output_csv_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_recognition_degree.csv'

def calculate_recognition_degree(input_path, output_path):
    print("正在加载数据...")
    # 读取CSV文件
    df = pd.read_csv(input_path, encoding='utf-8')
    print(f"共加载 {len(df)} 条数据")
    
    # 1. 重命名字段：将"sentiment_intensity"改为"全部情感强度"
    print("正在重命名字段...")
    df = df.rename(columns={'sentiment_intensity': '全部情感强度'})
    
    # 2. 标准化情感强度
    print("正在标准化情感强度...")
    # 原始情感强度范围
    min_sentiment = df['全部情感强度'].min()
    max_sentiment = df['全部情感强度'].max()
    print(f"原始情感强度范围: {min_sentiment:.4f} 到 {max_sentiment:.4f}")
    
    # 归一化到0-1范围
    # 使用Min-Max归一化
    df['normalized_sentiment'] = (df['全部情感强度'] - min_sentiment) / (max_sentiment - min_sentiment) if max_sentiment > min_sentiment else 0.5
    
    # 确保归一化后的值在0-1范围内
    df['normalized_sentiment'] = df['normalized_sentiment'].clip(0.0, 1.0)
    
    print(f"归一化后情感强度范围: {df['normalized_sentiment'].min():.4f} 到 {df['normalized_sentiment'].max():.4f}")
    
    # 3. 计算认同程度
    print("正在计算中非命运共同体认同程度...")
    # 语义关联度已在0-1范围内
    df['china_africa_community_recognition'] = (df['normalized_sentiment'] + df['community_similarity']) / 2
    
    # 4. 保存结果
    print("正在保存结果...")
    df.to_csv(output_path, encoding='utf-8', index=False)
    
    print(f"结果已保存到: {output_path}")
    
    # 打印统计信息
    print("\n统计信息:")
    print("全部情感强度统计:")
    print(df['全部情感强度'].describe())
    print("\n归一化情感强度统计:")
    print(df['normalized_sentiment'].describe())
    print("\n语义关联度统计:")
    print(df['community_similarity'].describe())
    print("\n中非命运共同体认同程度统计:")
    print(df['china_africa_community_recognition'].describe())

if __name__ == "__main__":
    calculate_recognition_degree(input_csv_path, output_csv_path)
