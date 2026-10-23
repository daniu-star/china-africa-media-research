import pandas as pd

# 读取数据
df = pd.read_csv('清洗数据/enhanced_data_with_complete_features.csv', low_memory=False)
print('数据列名：')
print(df.columns.tolist())

# 检查是否包含china_africa_community_recognition列
if 'china_africa_community_recognition' in df.columns:
    print('\nchina_africa_community_recognition列存在')
    print('该列非空值数量：', df['china_africa_community_recognition'].notnull().sum())
else:
    print('\nchina_africa_community_recognition列不存在')
    # 查找包含recognition或community的列
    print('\n包含recognition或community的列：')
    for col in df.columns:
        if 'recognition' in col.lower() or 'community' in col.lower():
            print(col)
