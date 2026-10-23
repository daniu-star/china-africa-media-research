import pandas as pd
import numpy as np
import os
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# 设置输出目录
output_dir = 'c:/Users/13067/Desktop/论文/非洲/demo/信效度分析结果'
os.makedirs(output_dir, exist_ok=True)

print("=== 合成变量信度分析修正 ===")

# 读取数据
file_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_complete_features.csv'
print(f"\n1. 读取数据文件: {file_path}")

# 读取所有需要的列
cols_to_read = [
    'development_terms_weight', 'local_sentiment', 'development_demand_perception',
    'long_term_word_count', 'has_multi_agent_interaction', 'cooperation_depth_index',
    'china_africa_community_recognition', 'normalized_sentiment', 'community_similarity'
]

df = pd.read_csv(file_path, usecols=cols_to_read, low_memory=False)
print(f"   数据记录数: {len(df)}")
print(f"   数据字段数: {len(df.columns)}")

# 计算Cronbach's α的函数
def calculate_cronbach_alpha(components):
    """计算Cronbach's α"""
    cov_matrix = components.cov()
    total_variance = cov_matrix.sum().sum()
    avg_item_variance = np.mean(np.diag(cov_matrix))
    k = len(components.columns)
    if k < 2:
        return None
    alpha = (k / (k - 1)) * (1 - (avg_item_variance / (total_variance / k)))
    return alpha

# 分析合作纵深性指数分布偏左的原因
print("\n2. 合作纵深性指数分布分析")
coop_depth_stats = df['cooperation_depth_index'].describe()
print(f"   平均值: {coop_depth_stats['mean']:.4f}")
print(f"   中位数: {coop_depth_stats['50%']:.4f}")
print(f"   标准差: {coop_depth_stats['std']:.4f}")
print(f"   最小值: {coop_depth_stats['min']:.4f}")
print(f"   最大值: {coop_depth_stats['max']:.4f}")
print(f"   偏度: {stats.skew(df['cooperation_depth_index']):.4f}")
print(f"   峰度: {stats.kurtosis(df['cooperation_depth_index']):.4f}")

# 分析各合成变量的构成
print("\n3. 合成变量构成分析")

# 1. 发展需求感知强度
development_components = df[['development_terms_weight', 'local_sentiment']]
development_alpha = calculate_cronbach_alpha(development_components)
print(f"\n   1. 发展需求感知强度:")
print(f"      构成分量: development_terms_weight, local_sentiment")
print(f"      Cronbach's α: {development_alpha:.4f}")
print(f"      相关系数: {development_components.corr().iloc[0, 1]:.4f}")

# 2. 命运共同体认同度（已正确处理）
community_components = df[['normalized_sentiment', 'community_similarity']]
community_alpha = calculate_cronbach_alpha(community_components)
print(f"\n   2. 命运共同体认同度:")
print(f"      构成分量: normalized_sentiment, community_similarity")
print(f"      Cronbach's α: {community_alpha:.4f}")
print(f"      相关系数: {community_components.corr().iloc[0, 1]:.4f}")

# 3. 合作纵深性指数（使用提供的权重计算）
print(f"\n   3. 合作纵深性指数:")
print(f"      构成指标: long_term_word_count, has_multi_agent_interaction, 合作领域多样性")
print(f"      PCA权重: [0.3350, 0.3183, 0.3467]")
print(f"      注: 合作领域多样性在当前数据中未直接体现")

# 修改信效度分析脚本，正确处理合成变量
print("\n4. 信效度分析脚本修改建议")
print("   需要修改变量信效度分析与SPSS可视化.py中的calculate_reliability方法，")
print("   让它正确识别以下合成变量的构成:")
print("   - development_demand_perception: [development_terms_weight, local_sentiment]")
print("   - cooperation_depth_index: [long_term_word_count, has_multi_agent_interaction]")
print("   - china_africa_community_recognition: [normalized_sentiment, community_similarity]")

# 生成修正后的信度分析报告
print("\n5. 生成修正后的信度分析结果")

# 定义合成变量
composite_vars = {
    'development_demand_perception': ['development_terms_weight', 'local_sentiment'],
    'china_africa_community_recognition': ['normalized_sentiment', 'community_similarity'],
    'cooperation_depth_index': ['long_term_word_count', 'has_multi_agent_interaction']
}

# 计算各合成变量的信度
reliability_results = []
for var_name, components in composite_vars.items():
    if all(comp in df.columns for comp in components):
        comp_data = df[components]
        alpha = calculate_cronbach_alpha(comp_data)
        # Shapiro-Wilk正态性检验
        _, p_value = stats.shapiro(df[var_name].sample(min(5000, len(df))))
        is_normal = p_value > 0.05
        
        # 评估信度
        if alpha is not None:
            if alpha >= 0.8:
                evaluation = '优秀'
            elif alpha >= 0.7:
                evaluation = '良好'
            elif alpha >= 0.6:
                evaluation = '可接受'
            else:
                evaluation = '较差'
        else:
            evaluation = '单一指标'
        
        reliability_results.append({
            'variable': var_name,
            'components': components,
            'is_normal': is_normal,
            'shapiro_p': p_value,
            'cronbach_alpha': alpha,
            'reliability_evaluation': evaluation
        })

# 转换为DataFrame
reliability_df = pd.DataFrame(reliability_results)

# 保存结果
reliability_df.to_csv(os.path.join(output_dir, '合成变量信度分析结果.csv'), index=False, encoding='utf-8-sig')

print(f"\n6. 保存修正后的信度分析结果到: {os.path.join(output_dir, '合成变量信度分析结果.csv')}")

# 输出结果
print("\n=== 修正后的合成变量信度分析结果 ===")
print(reliability_df.to_string(index=False))

print("\n=== 合作纵深性指数分布偏左原因分析 ===")
print("1. 数据分布特征:")
print(f"   - 平均值: {coop_depth_stats['mean']:.4f}")
print(f"   - 中位数: {coop_depth_stats['50%']:.4f}")
print(f"   - 偏度: {stats.skew(df['cooperation_depth_index']):.4f} (右偏分布)")
print("\n2. 可能的原因:")
print("   - 数据本身的分布特性: 大部分合作项目的纵深性处于中等水平")
print("   - 计算方式影响: 三个构成指标的加权平均可能导致数值集中")
print("   - 样本特性: 可能存在大量浅层次合作样本")
print("   - 取值范围: 数值分布在0-1之间，0.17的平均值是合理的")

print("\n=== 分析完成 ===")
