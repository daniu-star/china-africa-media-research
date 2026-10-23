import pandas as pd
import numpy as np

# 读取临时文件的中间部分（行1000-1010）
print("=== 临时文件中间部分检查 ===")

file_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/temp_enhanced_data.csv'

# 读取行1000-1010
print(f"\n1. 行1000-1010数据:")
with open(file_path, 'r', encoding='utf-8') as f:
    # 跳过前999行
    for _ in range(999):
        f.readline()
    
    # 读取接下来的11行（包括行1000）
    for i in range(11):
        line = f.readline().strip()
        if line:
            print(f"   行 {1000+i}: {line}")
        else:
            print(f"   行 {1000+i}: 空行")

# 使用pandas读取行1000-1010，不自动推断列类型
try:
    temp_df_mid = pd.read_csv(file_path, skiprows=999, nrows=10, dtype=str, keep_default_na=False)
    print(f"\n2. pandas读取结果（行1000-1009）:")
    print(f"   - 行数: {len(temp_df_mid)}")
    print(f"   - 列数: {len(temp_df_mid.columns)}")
    
    # 显示每行的关键字段值
    print(f"\n   - 关键字段值:")
    key_fields = ['title', 'summary', 'date', 'url', 'content', 'combined_text']
    for i in range(len(temp_df_mid)):
        print(f"     行 {1000+i}:")
        for field in key_fields:
            if field in temp_df_mid.columns:
                value = temp_df_mid.loc[i, field]
                print(f"       {field}: '{value}' (长度: {len(value)})")
    
except Exception as e:
    print(f"\n2. pandas读取失败: {e}")
    print(f"   错误类型: {type(e).__name__}")

# 统计临时文件中关键字段的非空值比例
print(f"\n3. 关键字段非空值统计（样本1000-2000行）:")
temp_df_sample = pd.read_csv(file_path, skiprows=999, nrows=1000, dtype=str, keep_default_na=False)
key_fields = ['title', 'summary', 'date', 'url', 'content', 'combined_text']
for field in key_fields:
    if field in temp_df_sample.columns:
        non_null_count = (temp_df_sample[field] != '').sum()
        percent = (non_null_count / len(temp_df_sample)) * 100
        print(f"   - {field}: {non_null_count}/1000 ({percent:.1f}%)")

# 检查是否有记录包含有意义的文本
print(f"\n4. 检查是否有记录包含有意义的文本:")
# 过滤出combined_text长度大于10的记录
significant_text = temp_df_sample[temp_df_sample['combined_text'].str.len() > 10]
print(f"   - 包含大于10字符文本的记录数: {len(significant_text)}")

if len(significant_text) > 0:
    print(f"\n   - 示例记录:")
    for i in range(min(3, len(significant_text))):
        text = significant_text['combined_text'].iloc[i]
        print(f"     示例 {i+1}: {text[:100]}...")
else:
    print(f"   - 没有找到包含有意义文本的记录")