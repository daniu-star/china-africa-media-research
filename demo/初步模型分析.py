import pandas as pd
import numpy as np
import statsmodels.api as sm
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv(r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv', low_memory=False)

# 1. 确定因变量
# 从数据中寻找与中非命运共同体认同强度相关的变量
print("1. 因变量分析")
suspected_dependent_vars = [
    'china_africa_community_recognition',
    'community_similarity',
    'normalized_sentiment'
]

for var in suspected_dependent_vars:
    print(f"\n{var} 描述统计:")
    print(df[var].describe())
    print(f"缺失值比例: {(df[var].isnull().sum() / len(df)) * 100:.2f}%")

# 2. 自变量分析
print("\n2. 自变量分析")
independent_vars = [
    'cooperation_willingness_advanced',
    'development_demand_pca',
    'source_region_5',
    'time_index'
]

for var in independent_vars:
    if var == 'source_region_5':
        print(f"\n{var} 分布:")
        print(df[var].value_counts())
    else:
        print(f"\n{var} 描述统计:")
        print(df[var].describe())
        print(f"缺失值比例: {(df[var].isnull().sum() / len(df)) * 100:.2f}%")

# 3. 相关分析
print("\n3. 相关分析")
numeric_vars = suspected_dependent_vars + [var for var in independent_vars if var != 'source_region_5']
corr_matrix = df[numeric_vars].corr()
print(corr_matrix)

# 4. 初步回归模型
print("\n4. 初步回归模型")

# 4.1 数据准备
# 使用 china_africa_community_recognition 作为因变量
y = df['china_africa_community_recognition'].dropna()

# 筛选自变量数据，保持与因变量的行数一致
X = df.loc[y.index, independent_vars].copy()

# 将分类变量转换为虚拟变量
X = pd.get_dummies(X, columns=['source_region_5'], drop_first=True)

# 确保所有自变量都是数值类型
X = X.apply(pd.to_numeric, errors='coerce')

# 添加常数项
X = sm.add_constant(X)

# 移除包含缺失值的行
valid_rows = X.notnull().all(axis=1) & y.notnull()
X = X[valid_rows]
y = y[valid_rows]

# 4.2 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# 4.3 拟合模型
model = sm.OLS(y_train, X_train).fit()

# 4.4 模型结果
print("\n模型拟合结果:")
print(model.summary())

# 4.5 模型评估
print("\n模型评估:")
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)
adjusted_r2 = 1 - (1 - r2) * (len(y_test) - 1) / (len(y_test) - X_test.shape[1] - 1)
mse = mean_squared_error(y_test, y_pred)
print(f"R²: {r2:.4f}")
print(f"调整后R²: {adjusted_r2:.4f}")
print(f"均方误差: {mse:.4f}")

# 5. 模型假设检验
print("\n5. 模型假设检验")

# 5.1 残差分析
residuals = y_test - y_pred

plt.figure(figsize=(12, 8))

# 残差直方图
plt.subplot(2, 2, 1)
plt.hist(residuals, bins=30, edgecolor='black')
plt.title('残差分布直方图')
plt.xlabel('残差')
plt.ylabel('频率')

# 残差散点图
plt.subplot(2, 2, 2)
plt.scatter(y_pred, residuals, alpha=0.5)
plt.axhline(y=0, color='red', linestyle='--')
plt.title('残差 vs 预测值')
plt.xlabel('预测值')
plt.ylabel('残差')

# Q-Q图
plt.subplot(2, 2, 3)
from statsmodels.graphics.gofplots import qqplot
qqplot(residuals, line='s', ax=plt.gca())
plt.title('残差Q-Q图')

# 因变量分布
plt.subplot(2, 2, 4)
plt.hist(y, bins=30, edgecolor='black')
plt.title('因变量分布直方图')
plt.xlabel('china_africa_community_recognition')
plt.ylabel('频率')

plt.tight_layout()
plt.savefig('初步模型分析.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n6. 模型效力结论")
print("-" * 50)
print(f"模型R²: {r2:.4f}")
print(f"调整后R²: {adjusted_r2:.4f}")
print(f"F统计量: {model.fvalue:.4f}")
print(f"F统计量p值: {model.f_pvalue:.4f}")

if model.f_pvalue < 0.05:
    print("\n结论: 模型整体具有统计显著性")
else:
    print("\n结论: 模型整体不具有统计显著性")

print("\n7. 系数显著性")
for var, pval in zip(model.params.index[1:], model.pvalues[1:]):
    if pval < 0.05:
        print(f"{var}: p值={pval:.4f} (显著)")
    else:
        print(f"{var}: p值={pval:.4f} (不显著)")

print("\n8. 完善模型建议")
print("-" * 50)
print("1. 考虑添加交互项，如合作意愿与时间的交互，探索时间变化对合作意愿影响的调节效应")
print("2. 检查并处理可能的非线性关系，如对部分变量进行对数转换")
print("3. 考虑添加其他控制变量，如文章长度、情感倾向等")
print("4. 考虑使用固定效应模型，控制时间或来源的固定效应")
print("5. 检查并处理异常值，提高模型稳健性")
print("6. 考虑使用其他回归方法，如稳健回归或分位数回归")
print("7. 评估模型的预测能力，使用交叉验证等方法")
print("8. 考虑将因变量进行转换，如标准化或对数转换，改善模型拟合")
