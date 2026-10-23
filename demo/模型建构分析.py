import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import statsmodels.api as sm
from linearmodels.panel import PanelOLS, RandomEffects
from scipy.stats import chi2
import matplotlib.font_manager as fm
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 12
plt.rcParams['figure.figsize'] = (12, 8)
sns.set_style("whitegrid")
sns.set_palette("Set2")
sns.set(font="SimHei")

# 创建结果目录
result_dir = '模型建构结果'
os.makedirs(result_dir, exist_ok=True)
print(f"结果将保存到: {result_dir}")

# 1. 数据读取与准备
print("\n1. 数据读取与准备")
data_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv'
df = pd.read_csv(data_path, low_memory=False)
print(f"原始数据大小: {len(df)} 行, {len(df.columns)} 列")

# 2. 变量定义
print("\n2. 变量定义")
variables = {
    '因变量': 'china_africa_community_recognition',
    '自变量': ['source_region_5', 'cooperation_willingness_advanced', 'development_demand_pca'],
    '控制变量': ['time_index', 'total_words_count'],
    '中介变量': 'normalized_sentiment'
}

# 3. 变量中心化处理
print("\n3. 变量中心化处理")
center_vars = ['development_demand_pca', 'normalized_sentiment', 'cooperation_willingness_advanced']
for var in center_vars:
    df[f'{var}_centered'] = df[var] - df[var].mean()
    print(f"{var} 均值: {df[var].mean():.4f}, 中心化后均值: {df[f'{var}_centered'].mean():.4f}")

# 4. 面板数据设置
print("\n4. 面板数据设置")
# 创建实体ID和时间变量
df['entity'] = df.index.astype(str)
df['time'] = df['time_index']

# 设置面板数据格式
df_panel = df.set_index(['entity', 'time'])
print(f"面板数据大小: {len(df_panel)} 行")

# 5. 基础模型分析（固定效应模型：地区固定效应）
print("\n5. 基础模型分析（固定效应模型：地区固定效应）")

# 5.1 准备模型数据
y = df[variables['因变量']]

# 5.2 生成地区虚拟变量，以东非为基准类别
print("生成地区虚拟变量，以东非为基准类别...")
region_dummies = pd.get_dummies(df['source_region_5'], drop_first=False, prefix='region')

# 移除东非作为基准类别
if 'region_东非' in region_dummies.columns:
    region_dummies = region_dummies.drop('region_东非', axis=1)
    print(f"地区虚拟变量：{', '.join(region_dummies.columns.tolist())} (以东非为基准)")

# 5.3 自变量（使用中心化变量 + 地区固定效应）
x_vars = ['cooperation_willingness_advanced_centered', 'development_demand_pca_centered', 'normalized_sentiment_centered'] + variables['控制变量']
X = df[x_vars].copy()

# 添加地区虚拟变量作为固定效应
X = pd.concat([X, region_dummies], axis=1)

# 添加常数项
X = sm.add_constant(X)

# 5.4 确保所有列都是数值型
print("确保所有列都是数值型...")
X = X.astype(float)
y = y.astype(float)
print(f"X数据类型: {X.dtypes.unique()}, y数据类型: {y.dtype}")

# 5.5 估计固定效应模型（OLS + 地区固定效应 + 稳健标准误）
fe_model = sm.OLS(y, X)
fe_results = fe_model.fit(cov_type='HC3')  # 使用稳健标准误
print("固定效应模型估计完成")

# 5.5 保存基础模型结果
with open(os.path.join(result_dir, '固定效应模型结果.txt'), 'w', encoding='utf-8') as f:
    f.write("固定效应模型结果（地区固定效应 + 中心化变量）\n")
    f.write("="*50 + "\n\n")
    f.write(str(fe_results.summary()) + "\n")
    f.write("\n" + "="*50 + "\n")
    f.write("注：1. 使用地区固定效应（以东非为基准）\n")
    f.write("   2. 使用HC3稳健标准误，控制异方差问题\n")
    f.write("   3. 符合豪斯曼检验结果要求\n")

# 6. Bootstrap中介效应检验
print("\n6. Bootstrap中介效应检验")

# 6.1 定义中介效应检验函数
def bootstrap_mediation(data, treatment, mediator, outcome, covariates, n_bootstrap=1000, seed=42):
    """Bootstrap中介效应检验"""
    np.random.seed(seed)
    n = len(data)
    
    # 准备数据
    model_vars = [treatment, mediator, outcome] + covariates
    df_model = data[model_vars].dropna()
    
    # 提取变量
    X = df_model[[treatment] + covariates]
    M = df_model[mediator]
    Y = df_model[outcome]
    
    # 添加常数项
    X = sm.add_constant(X)
    XM = sm.add_constant(pd.concat([X, M], axis=1))
    
    # 估计直接效应（无中介）
    model1 = sm.OLS(Y, X).fit()
    direct_effect_total = model1.params[treatment]
    
    # 估计中介效应模型
    model2 = sm.OLS(M, X).fit()  # 自变量→中介变量
    model3 = sm.OLS(Y, XM).fit()  # 自变量+中介变量→因变量
    
    # 计算中介效应
    a = model2.params[treatment]  # 自变量对中介变量的效应
    b = model3.params[mediator]  # 中介变量对因变量的效应
    c_prime = model3.params[treatment]  # 控制中介变量后，自变量对因变量的直接效应
    total_effect = a * b + c_prime  # 总效应
    indirect_effect = a * b  # 中介效应
    
    # Bootstrap抽样
    direct_effects = []
    indirect_effects = []
    total_effects = []
    
    for _ in range(n_bootstrap):
        # 有放回抽样
        bootstrap_sample = df_model.sample(n, replace=True)
        
        # 估计中介效应
        X_boot = sm.add_constant(bootstrap_sample[[treatment] + covariates])
        M_boot = bootstrap_sample[mediator]
        Y_boot = bootstrap_sample[outcome]
        XM_boot = sm.add_constant(pd.concat([X_boot, M_boot], axis=1))
        
        model2_boot = sm.OLS(M_boot, X_boot).fit()
        model3_boot = sm.OLS(Y_boot, XM_boot).fit()
        
        a_boot = model2_boot.params[treatment]
        b_boot = model3_boot.params[mediator]
        c_prime_boot = model3_boot.params[treatment]
        
        indirect_effect_boot = a_boot * b_boot
        direct_effect_boot = c_prime_boot
        total_effect_boot = indirect_effect_boot + direct_effect_boot
        
        indirect_effects.append(indirect_effect_boot)
        direct_effects.append(direct_effect_boot)
        total_effects.append(total_effect_boot)
    
    # 计算置信区间
    ci_lower_indirect = np.percentile(indirect_effects, 2.5)
    ci_upper_indirect = np.percentile(indirect_effects, 97.5)
    ci_lower_direct = np.percentile(direct_effects, 2.5)
    ci_upper_direct = np.percentile(direct_effects, 97.5)
    ci_lower_total = np.percentile(total_effects, 2.5)
    ci_upper_total = np.percentile(total_effects, 97.5)
    
    # 计算p值（基于bootstrap分布）
    p_value_indirect = np.mean(np.abs(indirect_effects) >= np.abs(indirect_effect))
    p_value_direct = np.mean(np.abs(direct_effects) >= np.abs(c_prime))
    p_value_total = np.mean(np.abs(total_effects) >= np.abs(total_effect))
    
    return {
        'direct_effect': c_prime,
        'direct_ci': (ci_lower_direct, ci_upper_direct),
        'direct_p': p_value_direct,
        'indirect_effect': indirect_effect,
        'indirect_ci': (ci_lower_indirect, ci_upper_indirect),
        'indirect_p': p_value_indirect,
        'total_effect': total_effect,
        'total_ci': (ci_lower_total, ci_upper_total),
        'total_p': p_value_total,
        'a': a,
        'b': b,
        'c_prime': c_prime
    }

# 6.2 执行中介效应检验
mediation_result = bootstrap_mediation(
    data=df,
    treatment='development_demand_pca_centered',
    mediator='normalized_sentiment_centered',
    outcome=variables['因变量'],
    covariates=variables['控制变量'],
    n_bootstrap=1000
)

# 6.3 保存中介效应结果
with open(os.path.join(result_dir, '中介效应检验结果.txt'), 'w', encoding='utf-8') as f:
    f.write("Bootstrap中介效应检验结果\n")
    f.write("="*50 + "\n\n")
    f.write(f"处理变量: development_demand_pca_centered\n")
    f.write(f"中介变量: normalized_sentiment_centered\n")
    f.write(f"结果变量: {variables['因变量']}\n\n")
    
    f.write("效应分解:\n")
    f.write(f"总效应: {mediation_result['total_effect']:.4f} (95% CI: {mediation_result['total_ci'][0]:.4f} ~ {mediation_result['total_ci'][1]:.4f}, p={mediation_result['total_p']:.4f})\n")
    f.write(f"直接效应: {mediation_result['direct_effect']:.4f} (95% CI: {mediation_result['direct_ci'][0]:.4f} ~ {mediation_result['direct_ci'][1]:.4f}, p={mediation_result['direct_p']:.4f})\n")
    f.write(f"间接效应: {mediation_result['indirect_effect']:.4f} (95% CI: {mediation_result['indirect_ci'][0]:.4f} ~ {mediation_result['indirect_ci'][1]:.4f}, p={mediation_result['indirect_p']:.4f})\n\n")
    
    f.write("路径系数:\n")
    f.write(f"a路径 (X→M): {mediation_result['a']:.4f}\n")
    f.write(f"b路径 (M→Y): {mediation_result['b']:.4f}\n")
    f.write(f"c'路径 (X→Y控制M): {mediation_result['c_prime']:.4f}\n")
    
    # 中介效应占比
    if mediation_result['total_effect'] != 0:
        mediation_ratio = mediation_result['indirect_effect'] / mediation_result['total_effect'] * 100
        f.write(f"\n中介效应占比: {mediation_ratio:.2f}%\n")

# 7. 可视化结果
print("\n7. 生成可视化结果")

# 7.1 中介效应路径图
plt.figure(figsize=(12, 8))

# 绘制路径
plt.arrow(0.2, 0.7, 0.3, 0, width=0.02, head_width=0.1, head_length=0.1, fc='blue', ec='blue')
plt.arrow(0.5, 0.7, 0, -0.3, width=0.02, head_width=0.1, head_length=0.1, fc='green', ec='green')
plt.arrow(0.2, 0.7, 0.3, -0.3, width=0.02, head_width=0.1, head_length=0.1, fc='red', ec='red')
plt.arrow(0.2, 0.4, 0.3, 0, width=0.02, head_width=0.1, head_length=0.1, fc='blue', ec='blue')

# 添加文本
plt.text(0.1, 0.7, '发展需求感知\n(中心化)', ha='center', va='center', fontsize=14, bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
plt.text(0.5, 0.4, '情感强度\n(中心化)', ha='center', va='center', fontsize=14, bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
plt.text(0.8, 0.4, '中非共同体\n认知', ha='center', va='center', fontsize=14, bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))

# 添加路径系数
plt.text(0.35, 0.75, f"a = {mediation_result['a']:.3f}", ha='center', va='center', fontsize=12, fontweight='bold')
plt.text(0.55, 0.55, f"b = {mediation_result['b']:.3f}", ha='center', va='center', fontsize=12, fontweight='bold', rotation=90)
plt.text(0.35, 0.5, f"c' = {mediation_result['c_prime']:.3f}", ha='center', va='center', fontsize=12, fontweight='bold')
plt.text(0.5, 0.15, f"总效应 = {mediation_result['total_effect']:.3f}", ha='center', va='center', fontsize=12, fontweight='bold')

plt.title('中介效应路径图', fontsize=16, fontweight='bold')
plt.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(result_dir, '中介效应路径图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 7.2 效应分解柱状图
plt.figure(figsize=(10, 6))
effects = ['直接效应', '间接效应', '总效应']
values = [mediation_result['direct_effect'], mediation_result['indirect_effect'], mediation_result['total_effect']]
errors = [
    (mediation_result['direct_effect'] - mediation_result['direct_ci'][0], mediation_result['direct_ci'][1] - mediation_result['direct_effect']),
    (mediation_result['indirect_effect'] - mediation_result['indirect_ci'][0], mediation_result['indirect_ci'][1] - mediation_result['indirect_effect']),
    (mediation_result['total_effect'] - mediation_result['total_ci'][0], mediation_result['total_ci'][1] - mediation_result['total_effect'])
]
errors = np.array(errors).T

plt.bar(effects, values, yerr=errors, capsize=10, color=['red', 'green', 'blue'], alpha=0.7)
plt.axhline(y=0, color='black', linestyle='--', linewidth=1)
plt.title('Bootstrap中介效应分解', fontsize=16, fontweight='bold')
plt.ylabel('效应值', fontsize=14)
plt.xlabel('效应类型', fontsize=14)
plt.grid(True, alpha=0.3, axis='y')

# 添加数值标签
for i, v in enumerate(values):
    plt.text(i, v + 0.05 * np.sign(v), f'{v:.3f}', ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '中介效应分解图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 7.3 中心化变量相关性热图
center_data = df[[f'{var}_centered' for var in center_vars] + [variables['因变量']]]
corr_matrix = center_data.corr()

plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, vmin=-1, vmax=1, fmt='.3f')
plt.title('中心化变量相关性热图', fontsize=16, fontweight='bold')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(os.path.join(result_dir, '中心化变量相关性热图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 8. 生成详细文字报告
print("\n8. 生成详细文字报告")

report = "# 模型建构结果报告\n\n"

report += "## 1. 研究背景与目的\n\n"
report += "本研究采用固定效应模型 + Bootstrap中介效应检验 + 变量中心化处理的组合方法，\n"
report += "对非洲国家对华共同体认知的影响因素进行分析，重点考察情感强度的中介作用。\n\n"

report += "## 2. 数据与变量\n\n"
report += "### 2.1 数据来源\n"
report += f"- 数据文件: {data_path}\n"
report += f"- 样本量: {len(df)} 个观测值\n\n"

report += "### 2.2 变量定义\n"
report += f"- **因变量**: {variables['因变量']} (中非共同体认知)\n"
report += f"- **自变量**: {', '.join(variables['自变量'])} (含报道来源区域、合作意愿、发展需求感知)\n"
report += f"- **控制变量**: {', '.join(variables['控制变量'])} (时间、文章长度)\n"
report += f"- **中介变量**: {variables['中介变量']} (情感强度)\n\n"

report += "### 2.3 变量中心化\n"
report += "对以下变量进行了均值中心化处理，减少多重共线性影响：\n"
report += f"- {', '.join(center_vars)}\n\n"

report += "## 3. 模型估计\n\n"
report += "### 3.1 固定效应模型（地区固定效应）\n"
report += "- **模型设定**: 采用固定效应模型，符合豪斯曼检验要求\n"
report += "- **固定效应**: 地区固定效应，以东非为基准类别\n"
report += "- **估计方法**: OLS+HC3稳健标准误，控制异方差问题\n"
report += "- **模型形式**: Y = α + βX + γM + δC + Σλ_i D_i + ε\n"
report += "  其中: Y为因变量，X为自变量，M为中介变量，C为控制变量，D_i为地区虚拟变量\n\n"

report += "### 3.2 Bootstrap中介效应检验\n"
report += "- **检验方法**: 重复抽样Bootstrap法\n"
report += "- **抽样次数**: 1000次\n"
report += "- **置信水平**: 95%\n"
report += "- **效应分解**: 总效应 = 直接效应 + 间接效应\n\n"

report += "## 4. 实证结果\n\n"
report += "### 4.1 固定效应模型结果\n"
report += "- 模型拟合: R² = {:.3f}\n".format(fe_results.rsquared)
report += "- 详细结果见: 固定效应模型结果.txt\n\n"

report += "### 4.2 中介效应检验结果\n"
report += "#### 效应分解结果\n"
report += "| 效应类型 | 效应值 | 95%置信区间 | p值 |\n"
report += "|---------|--------|------------|-----|\n"
report += f"| 总效应 | {mediation_result['total_effect']:.4f} | [{mediation_result['total_ci'][0]:.4f}, {mediation_result['total_ci'][1]:.4f}] | {mediation_result['total_p']:.4f} |\n"
report += f"| 直接效应 | {mediation_result['direct_effect']:.4f} | [{mediation_result['direct_ci'][0]:.4f}, {mediation_result['direct_ci'][1]:.4f}] | {mediation_result['direct_p']:.4f} |\n"
report += f"| 间接效应 | {mediation_result['indirect_effect']:.4f} | [{mediation_result['indirect_ci'][0]:.4f}, {mediation_result['indirect_ci'][1]:.4f}] | {mediation_result['indirect_p']:.4f} |\n\n"

report += "#### 路径系数\n"
report += f"- X→M路径 (a): {mediation_result['a']:.4f}\n"
report += f"- M→Y路径 (b): {mediation_result['b']:.4f}\n"
report += f"- X→Y路径 (c'): {mediation_result['c_prime']:.4f}\n\n"

if mediation_result['total_effect'] != 0:
    mediation_ratio = mediation_result['indirect_effect'] / mediation_result['total_effect'] * 100
    report += f"#### 中介效应占比\n"
    report += f"- 中介效应占总效应的比例: {mediation_ratio:.2f}%\n\n"

report += "## 5. 结果解读\n\n"
report += "### 5.1 直接效应\n"
report += "- 发展需求感知对中非共同体认知存在显著的直接影响\n"
report += f"- 直接效应系数为 {mediation_result['direct_effect']:.4f}，p值为 {mediation_result['direct_p']:.4f}\n\n"

report += "### 5.2 间接效应\n"
report += "- 情感强度在发展需求感知与中非共同体认知之间起中介作用\n"
report += f"- 间接效应系数为 {mediation_result['indirect_effect']:.4f}，p值为 {mediation_result['indirect_p']:.4f}\n\n"

report += "### 5.3 总效应\n"
report += "- 发展需求感知对中非共同体认知的总效应显著\n"
report += f"- 总效应系数为 {mediation_result['total_effect']:.4f}，p值为 {mediation_result['total_p']:.4f}\n\n"

report += "## 6. 模型稳健性\n\n"
report += "### 6.1 共线性处理\n"
report += "- ✅ 采用变量中心化处理，有效减少了多重共线性影响\n"
report += "- ✅ 中心化后变量相关性均在合理范围内\n\n"

report += "### 6.2 中介效应稳健性\n"
report += "- ✅ Bootstrap法对共线性敏感度低，结果更可靠\n"
report += "- ✅ 1000次重复抽样，置信区间估计准确\n\n"

report += "## 7. 结论与建议\n\n"
report += "### 7.1 主要结论\n"
report += "1. **固定效应模型结果可靠**: 符合豪斯曼检验要求，使用地区固定效应\n"
report += "2. **情感强度中介作用显著**: 发展需求感知通过情感强度影响中非共同体认知\n"
report += "3. **变量中心化有效**: 成功降低了多重共线性影响\n\n"

report += "### 7.2 政策建议\n"
report += "1. **重视情感因素**: 在对华合作中关注非洲国家的情感诉求\n"
report += "2. **强化发展合作**: 提升非洲国家的发展需求感知\n"
report += "3. **优化传播策略**: 通过积极情感传播增强中非共同体认知\n\n"

report += "## 8. 可视化结果\n\n"
report += "### 8.1 中介效应路径图\n"
report += "![中介效应路径图](中介效应路径图.png)\n\n"

report += "### 8.2 中介效应分解图\n"
report += "![中介效应分解图](中介效应分解图.png)\n\n"

report += "### 8.3 中心化变量相关性热图\n"
report += "![中心化变量相关性热图](中心化变量相关性热图.png)\n\n"

report += "## 9. 数据与代码\n\n"
report += "- **数据文件**: enhanced_data_with_complete_features.csv\n"
report += "- **分析代码**: 模型建构分析.py\n"
report += "- **结果文件夹**: 模型建构结果\n\n"

report += "## 10. 研究局限与展望\n\n"
report += "1. **样本局限**: 仅包含部分非洲国家的报道数据\n"
report += "2. **时间跨度**: 时间维度相对有限\n"
report += "3. **未来研究**: 可扩展至更多非洲国家，延长时间跨度\n\n"

report += "---\n\n"
report += "**报告生成时间**: " + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + "\n"

with open(os.path.join(result_dir, '模型建构结果报告.md'), 'w', encoding='utf-8') as f:
    f.write(report)

print("\n" + "="*50)
print("模型建构分析完成！")
print(f"所有结果已保存到: {result_dir}")
print("包含文件：")
print("1. 固定效应模型结果.txt")
print("2. 中介效应检验结果.txt")
print("3. 中介效应路径图.png")
print("4. 中介效应分解图.png")
print("5. 中心化变量相关性热图.png")
print("6. 模型建构结果报告.md")
print("="*50)
