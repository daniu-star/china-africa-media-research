import pandas as pd

# 主函数
def main():
    # 文件路径
    input_file = '清洗数据/sentiment_analyzed_data.csv'
    output_file = '清洗数据/fixed_sentiment_analyzed_data.csv'
    
    print("正在读取情感分析结果...")
    # 读取数据，跳过重复列
    df = pd.read_csv(input_file)
    
    print(f"原始数据形状: {df.shape}")
    print(f"原始列名: {df.columns.tolist()}")
    
    # 移除重复的情感分析列
    # 保留最后两个列（正确的情感分析结果）
    cols = df.columns.tolist()
    
    # 找到重复的列
    seen = {}
    duplicates = []
    for i, col in enumerate(cols):
        if col in seen:
            duplicates.append(i)
        else:
            seen[col] = i
    
    print(f"重复列索引: {duplicates}")
    
    # 删除重复的列
    df = df.drop(df.columns[duplicates], axis=1)
    
    # 重命名情感分析列
    df = df.rename(columns={
        'sentiment_score': 'sentiment_score',
        'sentiment_label': 'sentiment_label'
    })
    
    print(f"修复后的数据形状: {df.shape}")
    print(f"修复后列名: {df.columns.tolist()}")
    
    # 保存修复后的数据
    print("\n正在保存修复后的数据...")
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    # 显示情感分布
    print("\n情感分布:")
    print(df['sentiment_label'].value_counts())
    print("\n情感分布占比:")
    print(df['sentiment_label'].value_counts(normalize=True))
    
    # 显示前5行数据
    print("\n修复后的数据示例（前5行）:")
    print(df[['title', 'sentiment_score', 'sentiment_label']].head())
    
    print("\n✓ 数据修复完成！")
    print(f"✓ 修复后的数据已保存到 {output_file}")

if __name__ == "__main__":
    main()