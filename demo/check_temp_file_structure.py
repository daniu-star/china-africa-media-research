import pandas as pd
import numpy as np

# 读取临时文件的列名和前几行
print("=== 临时文件结构检查 ===")

# 读取列名
with open('c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/temp_enhanced_data.csv', 'r', encoding='utf-8') as f:
    header = f.readline().strip()
    print(f"\n1. 临时文件列名:")
    print(f"   {header}")
    
    columns = header.split(',')
    print(f"\n2. 列名列表:")
    for i, col in enumerate(columns):
        print(f"   {i+1}: {col}")

# 读取前5行（包括列名）
print(f"\n3. 前5行数据:")
with open('c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/temp_enhanced_data.csv', 'r', encoding='utf-8') as f:
    for i in range(5):
        line = f.readline().strip()
        print(f"   行 {i+1}: {line}")

# 检查文件大小
import os
file_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/temp_enhanced_data.csv'
file_size = os.path.getsize(file_path)
print(f"\n4. 文件信息:")
print(f"   - 文件大小: {file_size / (1024*1024*1024):.2f} GB")

# 使用pandas读取前10行，不自动推断列类型
try:
    temp_df = pd.read_csv(file_path, nrows=10, dtype=str, keep_default_na=False)
    print(f"\n5. pandas读取结果（前10行）:")
    print(f"   - 行数: {len(temp_df)}")
    print(f"   - 列数: {len(temp_df.columns)}")
    
    # 显示列名和数据类型
    print(f"\n   - 列名和非空值计数:")
    for col in temp_df.columns:
        non_null_count = (temp_df[col] != '').sum()
        print(f"     {col}: {non_null_count} 个非空值")
    
    # 显示前3行数据
    print(f"\n   - 前3行数据:")
    for i in range(min(3, len(temp_df))):
        print(f"     行 {i+1}: {temp_df.iloc[i].to_dict()}")
        
except Exception as e:
    print(f"\n5. pandas读取失败: {e}")
    print(f"   错误类型: {type(e).__name__}")

# 检查是否存在BOM或其他编码问题
print(f"\n6. 编码检查:")
try:
    with open(file_path, 'rb') as f:
        first_bytes = f.read(10)
        print(f"   - 文件前10字节: {first_bytes.hex()}")
        
        # 检查BOM
        if first_bytes.startswith(b'\xef\xbb\xbf'):
            print(f"   - 包含UTF-8 BOM")
        elif first_bytes.startswith(b'\xff\xfe'):
            print(f"   - 包含UTF-16 LE BOM")
        elif first_bytes.startswith(b'\xfe\xff'):
            print(f"   - 包含UTF-16 BE BOM")
        else:
            print(f"   - 无明显BOM")
            
        # 尝试读取第一行文本
        f.seek(0)
        first_line = f.readline().decode('utf-8')
        print(f"   - 第一行文本: {repr(first_line)}")
        
except Exception as e:
    print(f"   - 编码检查失败: {e}")