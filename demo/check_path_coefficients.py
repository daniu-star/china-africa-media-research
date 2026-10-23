import pandas as pd

# 读取优化版路径系数数据
path_coefficients_path = r'c:\Users\13067\Desktop\论文\非洲\demo\优化版_多群组回归分析结果\路径系数表.csv'
path_df = pd.read_csv(path_coefficients_path)
print('优化版路径系数表列名：')
print(path_df.columns.tolist())

# 打印前几行数据，查看数据结构
print('\n优化版路径系数表前几行数据：')
print(path_df.head())
