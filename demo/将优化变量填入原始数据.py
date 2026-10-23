import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 创建结果目录
result_dir = 'c:/Users/13067/Desktop/论文/非洲/demo/自变量分析结果'
os.makedirs(result_dir, exist_ok=True)

print("将优化后的自变量和因变量填入原始数据集")
print("="*50)

# 1. 读取数据
print("1. 读取数据")

# 读取原始数据集
df_original = pd.read_csv(r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv')

# 读取包含优化后变量的数据
df_optimized = pd.read_csv(r'c:\Users\13067\Desktop\论文\非洲\demo\自变量\data_with_advanced_willingness.csv')

# 2. 合并数据
print("2. 合并数据")

# 基于original_index进行合并
merged_df = pd.merge(df_original, df_optimized[[
    'original_index', 
    'cooperation_willingness_advanced', 
    'source_region_5'
]], on='original_index', how='left')

# 3. 计算缺失的自变量
print("3. 计算缺失的自变量")

# 3.1 时间变量处理
merged_df['date'] = pd.to_datetime(merged_df['date'], errors='coerce')
merged_df['time_index'] = merged_df['date'].dt.year.fillna(0).astype(int)

# 3.2 发展需求感知PCA分析
development_features = [
    'development_terms_weight',
    'development_demand_perception',
    'development_keyword_count',
    'development_keyword_density'
]

# 提取发展需求感知相关特征
df_development = merged_df[development_features].dropna()

# 标准化数据
scaler = StandardScaler()
development_scaled = scaler.fit_transform(df_development)

# 主成分分析
pca_development = PCA(n_components=1, random_state=42)
merged_df['development_demand_pca'] = pca_development.fit_transform(development_scaled)

# 4. 保存合并后的数据集
print("4. 保存合并后的数据集")
merged_df.to_csv(r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv', index=False, encoding='utf-8-sig')

print("\n数据合并完成！")
print(f"合并后的数据集包含 {len(merged_df)} 条记录")
print(f"已保存到: r'c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\清洗数据\\enhanced_data_with_complete_features.csv'")

# 5. 自变量分析
print("\n5. 自变量分析")

# 定义自变量列表
independent_variables = {
    'time_index': '时间变量',
    'cooperation_willingness_advanced': '合作意愿',
    'development_demand_pca': '发展需求感知',
    'source_region_5': '报道来源区域'
}

# 6. 为每个自变量生成分析结果
for var_name, var_label in independent_variables.items():
    print(f"\n6. 分析自变量: {var_label} ({var_name})")
    
    # 创建变量分析目录
    var_dir = os.path.join(result_dir, var_label)
    os.makedirs(var_dir, exist_ok=True)
    
    # 6.1 分布情况
    print(f"   6.1 生成分布图表")
    
    plt.figure(figsize=(12, 6))
    
    if var_name == 'source_region_5':
        # 分类变量，使用条形图
        merged_df[var_name].value_counts().plot(kind='bar')
        plt.title(f'{var_label}分布情况')
        plt.xlabel(var_label)
        plt.ylabel('数量')
        plt.xticks(rotation=45)
    else:
        # 数值变量，使用直方图和箱线图
        plt.subplot(1, 2, 1)
        sns.histplot(merged_df[var_name].dropna(), kde=True)
        plt.title(f'{var_label}分布直方图')
        plt.xlabel(var_label)
        plt.ylabel('频率')
        
        plt.subplot(1, 2, 2)
        sns.boxplot(y=merged_df[var_name].dropna())
        plt.title(f'{var_label}箱线图')
        plt.ylabel(var_label)
    
    plt.tight_layout()
    plt.savefig(os.path.join(var_dir, f'{var_label}分布.png'), dpi=300, bbox_inches='tight')
    plt.close()

print("\n" + "="*50)
print("所有自变量分析完成！")
print(f"结果已保存到: {result_dir}")
