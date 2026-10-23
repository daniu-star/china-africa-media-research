import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 1. 数据读取与预处理
print("=== 内部信效度检验开始 ===")

# 读取主数据
main_file_path = 'c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\清洗数据\\enhanced_data_with_complete_features.csv'
cols_to_read = [
    'year', 'china_africa_community_recognition', 'normalized_sentiment', 'community_similarity',
    'development_demand_perception', 'cooperation_depth_index', 'long_term_percentile',
    'multi_agent_percentile', 'long_term_word_count', 'has_multi_agent_interaction'
]
df = pd.read_csv(main_file_path, usecols=cols_to_read, low_memory=False)

# 读取HHI数据
hhi_file_path = 'c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\议题集中度分析结果\\yearly_hhi.csv'
hhi_df = pd.read_csv(hhi_file_path)
df = pd.merge(df, hhi_df, on='year', how='left')
df.rename(columns={'hhi_index': 'issue_concentration'}, inplace=True)

# 定义变量
independent_vars = ['development_demand_perception', 'issue_concentration', 'cooperation_depth_index']
dependent_var = 'china_africa_community_recognition'

print(f"数据记录数: {len(df)}")
print(f"自变量: {independent_vars}")
print(f"因变量: {dependent_var}")

# 2. 合成指标的内部一致性检验
print("\n=== 合成指标内部一致性检验 ===")

# 2.1 中非命运共同体认同强度的内部一致性
print("\n1. 中非命运共同体认同强度 (china_africa_community_recognition)")
print("   构成分量: normalized_sentiment + community_similarity")

# 计算分量间相关性
recognition_corr = df[['normalized_sentiment', 'community_similarity']].corr()
print(f"   分量间相关系数: {recognition_corr.iloc[0, 1]:.4f}")

# 计算Cronbach's α
# Cronbach's α公式: α = (k * r_avg) / (1 + (k - 1) * r_avg)，其中k是分量数，r_avg是平均相关系数
k_recognition = 2
r_avg_recognition = recognition_corr.iloc[0, 1]
alpha_recognition = (k_recognition * r_avg_recognition) / (1 + (k_recognition - 1) * r_avg_recognition)
print(f"   Cronbach's α: {alpha_recognition:.4f}")
print(f"   内部一致性: {'良好' if alpha_recognition >= 0.7 else '一般' if alpha_recognition >= 0.6 else '较差'}")

# 2.2 合作纵深性指数的内部一致性
print("\n2. 合作纵深性指数 (cooperation_depth_index)")
print("   构成分量: long_term_percentile + multi_agent_percentile")

# 计算分量间相关性
cooperation_corr = df[['long_term_percentile', 'multi_agent_percentile']].corr()
print(f"   分量间相关系数: {cooperation_corr.iloc[0, 1]:.4f}")

# 计算Cronbach's α
k_cooperation = 2
r_avg_cooperation = cooperation_corr.iloc[0, 1]
alpha_cooperation = (k_cooperation * r_avg_cooperation) / (1 + (k_cooperation - 1) * r_avg_cooperation)
print(f"   Cronbach's α: {alpha_cooperation:.4f}")
print(f"   内部一致性: {'良好' if alpha_cooperation >= 0.7 else '一般' if alpha_cooperation >= 0.6 else '较差'}")

# 2.3 合作纵深性指数原始分量的内部一致性
print("\n3. 合作纵深性指数原始分量")
print("   构成分量: long_term_word_count + has_multi_agent_interaction")

# 计算分量间相关性
cooperation_raw_corr = df[['long_term_word_count', 'has_multi_agent_interaction']].corr()
print(f"   原始分量间相关系数: {cooperation_raw_corr.iloc[0, 1]:.4f}")

# 3. 分量间关系可视化
print("\n=== 分量间关系可视化 ===")

# 3.1 中非命运共同体认同强度分量散点图
plt.figure(figsize=(12, 10))

plt.subplot(2, 2, 1)
sns.scatterplot(x='normalized_sentiment', y='community_similarity', data=df, alpha=0.5)
plt.title('认同强度分量关系: 归一化情感强度 vs 社区相似度')
plt.xlabel('normalized_sentiment')
plt.ylabel('community_similarity')
plt.grid(True, alpha=0.3)

# 3.2 合作纵深性指数分量散点图
plt.subplot(2, 2, 2)
sns.scatterplot(x='long_term_percentile', y='multi_agent_percentile', data=df, alpha=0.5)
plt.title('合作纵深性分量关系: 长期战略词频百分位 vs 多元主体互动百分位')
plt.xlabel('long_term_percentile')
plt.ylabel('multi_agent_percentile')
plt.grid(True, alpha=0.3)

# 3.3 合作纵深性原始分量散点图
plt.subplot(2, 2, 3)
sns.scatterplot(x='long_term_word_count', y='has_multi_agent_interaction', data=df, alpha=0.5)
plt.title('合作纵深性原始分量关系: 长期战略词频 vs 多元主体互动')
plt.xlabel('long_term_word_count')
plt.ylabel('has_multi_agent_interaction')
plt.grid(True, alpha=0.3)

# 3.4 认同强度与合作纵深性关系
plt.subplot(2, 2, 4)
sns.scatterplot(x='cooperation_depth_index', y='china_africa_community_recognition', data=df, alpha=0.5)
plt.title('核心变量关系: 合作纵深性指数 vs 认同强度')
plt.xlabel('cooperation_depth_index')
plt.ylabel('china_africa_community_recognition')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('内部信度检验可视化.png', dpi=300)
plt.close()

# 4. 合成指标的结构效度检验
print("\n=== 合成指标结构效度检验 ===")

# 4.1 因子分析模拟
print("\n1. 因子分析模拟结果")

# 对认同强度分量进行因子分析（简化版，计算因子载荷）
from sklearn.decomposition import PCA

# 认同强度分量
recognition_components = df[['normalized_sentiment', 'community_similarity']].dropna()
pca_recognition = PCA(n_components=1)
pca_recognition.fit(recognition_components)
recognition_loadings = pca_recognition.components_[0]
print(f"   认同强度因子载荷: {recognition_loadings}")
print(f"   因子解释方差比例: {pca_recognition.explained_variance_ratio_[0]:.4f}")

# 合作纵深性分量
cooperation_components = df[['long_term_percentile', 'multi_agent_percentile']].dropna()
pca_cooperation = PCA(n_components=1)
pca_cooperation.fit(cooperation_components)
cooperation_loadings = pca_cooperation.components_[0]
print(f"   合作纵深性因子载荷: {cooperation_loadings}")
print(f"   因子解释方差比例: {pca_cooperation.explained_variance_ratio_[0]:.4f}")

# 4.2 结构效度评估
print("\n2. 结构效度评估")
print("   认同强度因子解释方差比例: {pca_recognition.explained_variance_ratio_[0]:.4f} ({'良好' if pca_recognition.explained_variance_ratio_[0] >= 0.7 else '一般'})")
print("   合作纵深性因子解释方差比例: {pca_cooperation.explained_variance_ratio_[0]:.4f} ({'良好' if pca_cooperation.explained_variance_ratio_[0] >= 0.7 else '一般'})")

# 5. 回归分析（在内部信效度检验后）
print("\n=== 回归分析（内部信效度检验后） ===")

# 准备数据
X = df[independent_vars].dropna()
y = df.loc[X.index, dependent_var]

print(f"\n回归分析样本量: {len(X)}")

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# 标准化数据
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 建立回归模型
model = LinearRegression()
model.fit(X_train_scaled, y_train)

# 模型评估
y_pred = model.predict(X_test_scaled)
r2 = r2_score(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)

print(f"\n回归模型结果:")
print(f"R²值: {r2:.4f}")
print(f"均方误差(MSE): {mse:.4f}")
print(f"根均方误差(RMSE): {rmse:.4f}")

# 回归系数（标准化）
print(f"\n标准化回归系数:")
for i, var in enumerate(independent_vars):
    print(f"{var}: {model.coef_[i]:.4f}")
print(f"截距: {model.intercept_:.4f}")

# 6. 生成内部信效度检验报告
# 生成报告内容
# 计算评估结果
recognition_alpha_eval = '良好' if alpha_recognition >= 0.7 else '一般' if alpha_recognition >= 0.6 else '较差'
cooperation_alpha_eval = '良好' if alpha_cooperation >= 0.7 else '一般' if alpha_cooperation >= 0.6 else '较差'
recognition_structure_eval = '良好' if pca_recognition.explained_variance_ratio_[0] >= 0.7 else '一般'
cooperation_structure_eval = '良好' if pca_cooperation.explained_variance_ratio_[0] >= 0.7 else '一般'
r2_eval = '较强' if r2 >= 0.5 else '中等' if r2 >= 0.3 else '较弱'
recognition_suggestion = '考虑增加认同强度的构成分量，或调整现有分量的权重' if alpha_recognition < 0.7 else '认同强度指标结构合理，可继续使用'
cooperation_suggestion = '考虑优化合作纵深性指数的构成分量，或调整分量间的权重分配' if alpha_cooperation < 0.7 else '合作纵深性指数结构合理，可继续使用'

# 生成报告内容
report_content = f"""# 内部信效度检验报告

## 1. 研究背景
- **数据来源**: 合并自增强特征数据与议题集中度HHI指数
- **样本量**: {len(df)} 条记录
- **研究变量**:
  - 自变量: 发展需求感知、议题集中程度（HHI指数）、合作纵深性指数
  - 因变量: 中非命运共同体认同强度

## 2. 合成指标内部一致性检验

### 2.1 中非命运共同体认同强度
- **构成分量**: 归一化情感强度 (normalized_sentiment) + 社区相似度 (community_similarity)
- **分量间相关系数**: {recognition_corr.iloc[0, 1]:.4f}
- **Cronbach's α**: {alpha_recognition:.4f}
- **内部一致性评价**: {recognition_alpha_eval}

### 2.2 合作纵深性指数
- **构成分量**: 长期战略词频百分位 (long_term_percentile) + 多元主体互动百分位 (multi_agent_percentile)
- **分量间相关系数**: {cooperation_corr.iloc[0, 1]:.4f}
- **Cronbach's α**: {alpha_cooperation:.4f}
- **内部一致性评价**: {cooperation_alpha_eval}

### 2.3 合作纵深性指数原始分量
- **构成分量**: 长期战略词频 (long_term_word_count) + 多元主体互动 (has_multi_agent_interaction)
- **分量间相关系数**: {cooperation_raw_corr.iloc[0, 1]:.4f}

## 3. 结构效度检验

### 3.1 因子分析结果
- **认同强度因子解释方差比例**: {pca_recognition.explained_variance_ratio_[0]:.4f}
- **合作纵深性因子解释方差比例**: {pca_cooperation.explained_variance_ratio_[0]:.4f}

### 3.2 结构效度评估
- 认同强度的结构效度: {recognition_structure_eval}
- 合作纵深性的结构效度: {cooperation_structure_eval}

## 4. 回归分析结果

### 4.1 模型拟合情况
- **样本量**: {len(X)}
- **R²值**: {r2:.4f}
- **均方误差(MSE)**: {mse:.4f}
- **根均方误差(RMSE)**: {rmse:.4f}

### 4.2 标准化回归系数
"""

# 添加回归系数到报告
for i, var in enumerate(independent_vars):
    report_content += f"- {var}: {model.coef_[i]:.4f}\n"
report_content += f"- 截距: {model.intercept_:.4f}\n"

report_content += f"""

## 5. 结论与建议

### 5.1 信效度检验结论
1. **内部一致性**: 
   - 中非命运共同体认同强度的内部一致性Cronbach's α: {alpha_recognition:.4f}，属于{recognition_alpha_eval}水平
   - 合作纵深性指数的内部一致性Cronbach's α: {alpha_cooperation:.4f}，属于{cooperation_alpha_eval}水平

2. **结构效度**: 
   - 认同强度的结构效度: {pca_recognition.explained_variance_ratio_[0]:.4f}，属于{recognition_structure_eval}水平
   - 合作纵深性的结构效度: {pca_cooperation.explained_variance_ratio_[0]:.4f}，属于{cooperation_structure_eval}水平

3. **回归分析**: 
   - 模型R²值为{r2:.4f}，具有{r2_eval}的解释力

### 5.2 研究建议
1. **指标优化建议**: 
   - {recognition_suggestion}
   - {cooperation_suggestion}

2. **后续研究方向**: 
   - 深入探讨各分量对合成指标的贡献机制
   - 考虑引入更多控制变量，提高模型解释力
   - 进行细分样本分析，验证指标在不同群体中的稳定性

## 6. 可视化图表
- 内部信度检验可视化.png：展示各分量间关系
"""

# 保存报告
with open('内部信效度检验报告.md', 'w', encoding='utf-8') as f:
    f.write(report_content)

print("\n=== 内部信效度检验完成 ===")
print("生成的文件：")
print("1. 内部信度检验可视化.png")
print("2. 内部信效度检验报告.md")
