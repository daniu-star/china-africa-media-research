import pandas as pd

# 读取CSV文件
df = pd.read_csv(r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv')

# 提取source列的唯一值
unique_sources = df['source'].unique()

# 打印唯一的来源
print("Unique sources:")
for source in unique_sources:
    print(source)

# 保存到文件
with open('unique_sources.txt', 'w', encoding='utf-8') as f:
    for source in unique_sources:
        f.write(f"{source}\n")

print("\nSources saved to unique_sources.txt")