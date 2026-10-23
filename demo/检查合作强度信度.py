import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import os

# 设置结果目录
result_dir = 'c:/Users/13067/Desktop/论文/非洲/demo/重新构建自变量结果'

# 读取原始数据
df = pd.read_csv(r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv')

# 合作强度的构成指标
cooperation_features = [
    'long_term_word_count_scaled',  # 长期合作词汇比例
    'has_multi_agent_interaction_scaled',  # 多主体互动
    'community_similarity',  # 社区相似度
    'china_africa_community_recognition',  # 中非命运共同体认知
    'development_terms_weight',  # 发展术语权重
    'development_demand_perception'  # 发展需求感知
]

# 检查所有特征是否存在
for feature in cooperation_features:
    if feature not in df.columns:
        print(f"警告: 特征 {feature} 不存在，将被跳过")
        cooperation_features.remove(feature)

# 提取合作强度相关特征
df_cooperation = df[cooperation_features].dropna()

# 计算Cronbach's α信度
print("合作强度构成指标的Cronbach's α信度分析")

def cronbach_alpha(df):
    """计算Cronbach's α信度系数"""
    # 计算项目间的协方差矩阵
    cov_matrix = df.cov()
    # 计算项目间的协方差之和
    sum_cov = cov_matrix.sum().sum()
    # 计算项目内的方差之和
    sum_var = df.var().sum()
    # 计算项目数
    k = len(df.columns)
    # 计算Cronbach's α
    alpha = (k / (k - 1)) * (1 - sum_var / sum_cov)
    return alpha

# 计算信度
alpha = cronbach_alpha(df_cooperation)
print(f"Cronbach's α信度系数: {alpha:.4f}")

# 分析各指标的相关性
print("\n各构成指标的相关系数矩阵:")
corr_matrix = df_cooperation.corr()
print(corr_matrix)

# 主成分分析结果
print("\n主成分分析结果:")
scaler = StandardScaler()
cooperation_scaled = scaler.fit_transform(df_cooperation)

pca = PCA()
pca_result = pca.fit(cooperation_scaled)

# 输出主成分解释方差比
print(f"各主成分解释方差比: {pca.explained_variance_ratio_}")
print(f"累计解释方差比: {np.cumsum(pca.explained_variance_ratio_)} ")

# 输出主成分载荷
print("\n主成分载荷矩阵:")
loadings = pd.DataFrame(pca.components_.T, columns=[f'PC{i+1}' for i in range(len(pca.components_))], index=cooperation_features)
print(loadings)

# 保存信度分析结果
with open(os.path.join(result_dir, '合作强度信度分析.txt'), 'w', encoding='utf-8') as f:
    f.write("# 合作强度指标信度分析\n\n")
    f.write(f"Cronbach's α信度系数: {alpha:.4f}\n\n")
    f.write("各构成指标的相关系数矩阵:\n")
    f.write(corr_matrix.to_string())
    f.write("\n\n主成分分析结果:\n")
    f.write(f"各主成分解释方差比: {pca.explained_variance_ratio_}\n")
    f.write(f"累计解释方差比: {np.cumsum(pca.explained_variance_ratio_)}\n\n")
    f.write("主成分载荷矩阵:\n")
    f.write(loadings.to_string())

print("\n信度分析结果已保存到: ", os.path.join(result_dir, '合作强度信度分析.txt'))

# 评估合作强度指标质量
if alpha >= 0.7:
    print("\n合作强度指标信度良好 (α ≥ 0.7)")
elif alpha >= 0.6:
    print("\n合作强度指标信度可接受 (0.6 ≤ α < 0.7)")
else:
    print("\n合作强度指标信度较低 (α < 0.6)，建议进一步优化")
