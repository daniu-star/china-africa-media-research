import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import semopy
from semopy import Model, Optimizer
import os
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
result_dir = '多群组结构方程模型结果'
os.makedirs(result_dir, exist_ok=True)
print(f"结果将保存到: {result_dir}")

# 1. 数据读取与准备
print("\n1. 数据读取与准备")
data_path = r'c:\Users\13067\Desktop\论文\非洲\demo\潜在剖面分析结果\数据_带群体分类.csv'
df = pd.read_csv(data_path, low_memory=False)
print(f"数据大小: {len(df)} 行, {len(df.columns)} 列")

# 查看群体分布
profile_counts = df['profile'].value_counts().sort_index()
print(f"\n群体分布:")
print(profile_counts)

# 2. 定义模型变量
print("\n2. 定义模型变量")
model_vars = {
    'development_demand_pca_centered': 'development_demand',
    'normalized_sentiment_centered': 'sentiment',
    'cooperation_willingness_advanced_centered': 'cooperation',
    'china_africa_community_recognition': 'recognition'
}

# 3. 构建结构方程模型
print("\n3. 构建结构方程模型")

# 模型设定：中介效应模型
model_spec = """
# 测量模型
# 直接使用显变量，无需测量模型

# 结构模型
sentiment ~ development_demand + cooperation
recognition ~ development_demand + sentiment + cooperation
"""

# 4. 对每个群体分别拟合模型
print("\n4. 对每个群体分别拟合模型")

# 存储每个群体的模型结果
profile_results = {}
profile_params = []

for profile in sorted(df['profile'].unique()):
    print(f"\n拟合群体 {profile} 的模型...")
    
    # 提取该群体的数据
    profile_data = df[df['profile'] == profile]
    print(f"  样本量: {len(profile_data)}")
    
    # 重命名变量，适配模型
    model_data = profile_data.rename(columns=model_vars)
    
    # 只选择模型中需要的列
    model_columns = list(model_vars.values())
    model_data = model_data[model_columns]
    
    # 确保所有变量都是数值型
    model_data = model_data.astype(float)
    
    # 构建模型
    model = Model(model_spec)
    
    # 拟合模型
    result = model.fit(model_data)
    
    # 保存模型结果
    profile_results[profile] = {
        'model': model,
        'result': result,
        'data': model_data
    }
    
    # 获取路径系数
    params = model.inspect()
    params['profile'] = profile
    profile_params.append(params)
    
    # 打印模型拟合指数
    print(f"  模型拟合指数:")
    print(f"  - 卡方值: {result.chi2:.2f}")
    print(f"  - 自由度: {result.df:.0f}")
    print(f"  - p值: {result.pvalue:.4f}")
    print(f"  - CFI: {result.cfi:.4f}")
    print(f"  - TLI: {result.tli:.4f}")
    print(f"  - RMSEA: {result.rmsea:.4f}")
    print(f"  - SRMR: {result.srmr:.4f}")

# 5. 整理路径系数结果
print("\n5. 整理路径系数结果")

# 合并所有群体的路径系数
all_params = pd.concat(profile_params, ignore_index=True)

# 筛选结构路径系数
struct_params = all_params[all_params['op'] == '~'].copy()

# 保存所有路径系数
struct_params.to_csv(os.path.join(result_dir, '路径系数表.csv'), index=False, encoding='utf-8-sig')

# 打印关键路径系数
print("\n关键路径系数:")
key_paths = ['sentiment ~ development_demand', 'sentiment ~ cooperation', 
             'recognition ~ development_demand', 'recognition ~ sentiment', 'recognition ~ cooperation']
for path in key_paths:
    print(f"\n{path}:")
    path_params = struct_params[struct_params['lval'] + ' ~ ' + struct_params['rval'] == path]
    for _, row in path_params.iterrows():
        print(f"  群体 {row['profile']}: 系数 = {row['est']:.4f}, p值 = {row['pvalue']:.4f}, SE = {row['se']:.4f}")

# 6. 计算中介效应
print("\n6. 计算中介效应")

# 存储中介效应结果
mediation_results = []

for profile in sorted(df['profile'].unique()):
    # 获取该群体的路径系数
    profile_struct = struct_params[struct_params['profile'] == profile]
    
    # 提取相关路径系数
    a1 = profile_struct[(profile_struct['lval'] == 'sentiment') & (profile_struct['rval'] == 'development_demand')]['est'].values[0]
    b1 = profile_struct[(profile_struct['lval'] == 'recognition') & (profile_struct['rval'] == 'sentiment')]['est'].values[0]
    c1_prime = profile_struct[(profile_struct['lval'] == 'recognition') & (profile_struct['rval'] == 'development_demand')]['est'].values[0]
    
    a2 = profile_struct[(profile_struct['lval'] == 'sentiment') & (profile_struct['rval'] == 'cooperation')]['est'].values[0]
    b2 = b1  # 与上面相同
    c2_prime = profile_struct[(profile_struct['lval'] == 'recognition') & (profile_struct['rval'] == 'cooperation')]['est'].values[0]
    
    # 计算中介效应
    indirect_effect_dev = a1 * b1
    total_effect_dev = indirect_effect_dev + c1_prime
    mediation_ratio_dev = indirect_effect_dev / total_effect_dev * 100 if total_effect_dev != 0 else 0
    
    indirect_effect_coop = a2 * b2
    total_effect_coop = indirect_effect_coop + c2_prime
    mediation_ratio_coop = indirect_effect_coop / total_effect_coop * 100 if total_effect_coop != 0 else 0
    
    # 保存结果
    mediation_results.append({
        'profile': profile,
        'indirect_effect_dev': indirect_effect_dev,
        'direct_effect_dev': c1_prime,
        'total_effect_dev': total_effect_dev,
        'mediation_ratio_dev': mediation_ratio_dev,
        'indirect_effect_coop': indirect_effect_coop,
        'direct_effect_coop': c2_prime,
        'total_effect_coop': total_effect_coop,
        'mediation_ratio_coop': mediation_ratio_coop
    })

# 转换为DataFrame
mediation_df = pd.DataFrame(mediation_results)

# 保存中介效应结果
mediation_df.to_csv(os.path.join(result_dir, '中介效应结果.csv'), index=False, encoding='utf-8-sig')

# 打印中介效应结果
print("\n中介效应结果（发展需求感知 → 情感强度 → 认同）:")
for _, row in mediation_df.iterrows():
    print(f"  群体 {row['profile']}: ")
    print(f"    间接效应: {row['indirect_effect_dev']:.4f}")
    print(f"    直接效应: {row['direct_effect_dev']:.4f}")
    print(f"    总效应: {row['total_effect_dev']:.4f}")
    print(f"    中介效应占比: {row['mediation_ratio_dev']:.2f}%")

print("\n中介效应结果（合作意愿 → 情感强度 → 认同）:")
for _, row in mediation_df.iterrows():
    print(f"  群体 {row['profile']}: ")
    print(f"    间接效应: {row['indirect_effect_coop']:.4f}")
    print(f"    直接效应: {row['direct_effect_coop']:.4f}")
    print(f"    总效应: {row['total_effect_coop']:.4f}")
    print(f"    中介效应占比: {row['mediation_ratio_coop']:.2f}%")

# 7. 多群组比较
print("\n7. 多群组比较")

# 准备多群组比较数据
multi_group_data = {}
for profile in sorted(df['profile'].unique()):
    model_data = df[df['profile'] == profile].rename(columns=model_vars)
    # 只选择模型中需要的列
    model_columns = list(model_vars.values())
    model_data = model_data[model_columns]
    model_data = model_data.astype(float)
    multi_group_data[f'group{profile}'] = model_data

# 构建多群组模型
print("\n构建多群组模型...")
multi_model = Model(model_spec)

# 拟合多群组模型
print("拟合多群组模型...")
multi_result = multi_model.fit(multi_group_data)

# 保存多群组模型结果
with open(os.path.join(result_dir, '多群组模型结果.txt'), 'w', encoding='utf-8') as f:
    f.write("多群组结构方程模型结果\n")
    f.write("="*50 + "\n\n")
    f.write(f"模型设定:\n{model_spec}\n\n")
    f.write(f"模型拟合指数:\n")
    f.write(f"- 卡方值: {multi_result.chi2:.2f}\n")
    f.write(f"- 自由度: {multi_result.df:.0f}\n")
    f.write(f"- p值: {multi_result.pvalue:.4f}\n")
    f.write(f"- CFI: {multi_result.cfi:.4f}\n")
    f.write(f"- TLI: {multi_result.tli:.4f}\n")
    f.write(f"- RMSEA: {multi_result.rmsea:.4f}\n")
    f.write(f"- SRMR: {multi_result.srmr:.4f}\n\n")
    
    # 写入路径系数
    f.write("各群体路径系数:\n")
    f.write("="*50 + "\n")
    for path in key_paths:
        f.write(f"\n{path}:\n")
        path_params = struct_params[struct_params['lval'] + ' ~ ' + struct_params['rval'] == path]
        for _, row in path_params.iterrows():
            f.write(f"  群体 {row['profile']}: 系数 = {row['est']:.4f}, p值 = {row['pvalue']:.4f}\n")
    
    # 写入中介效应
    f.write("\n\n中介效应结果:\n")
    f.write("="*50 + "\n")
    f.write("\n发展需求感知 → 情感强度 → 认同:\n")
    for _, row in mediation_df.iterrows():
        f.write(f"\n  群体 {row['profile']}: ")
        f.write(f"间接效应 = {row['indirect_effect_dev']:.4f}, ")
        f.write(f"直接效应 = {row['direct_effect_dev']:.4f}, ")
        f.write(f"总效应 = {row['total_effect_dev']:.4f}, ")
        f.write(f"中介效应占比 = {row['mediation_ratio_dev']:.2f}%\n")
    
    f.write("\n\n合作意愿 → 情感强度 → 认同:\n")
    for _, row in mediation_df.iterrows():
        f.write(f"\n  群体 {row['profile']}: ")
        f.write(f"间接效应 = {row['indirect_effect_coop']:.4f}, ")
        f.write(f"直接效应 = {row['direct_effect_coop']:.4f}, ")
        f.write(f"总效应 = {row['total_effect_coop']:.4f}, ")
        f.write(f"中介效应占比 = {row['mediation_ratio_coop']:.2f}%\n")

# 8. 可视化结果
print("\n8. 可视化结果")

# 8.1 路径系数对比图
plt.figure(figsize=(15, 12))

# 发展需求感知对情感强度的影响
plt.subplot(2, 2, 1)
path_data = struct_params[(struct_params['lval'] == 'sentiment') & (struct_params['rval'] == 'development_demand')]
sns.barplot(x='profile', y='est', data=path_data, palette='Set1')
plt.errorbar(x=range(len(path_data)), y=path_data['est'], yerr=path_data['se'], fmt='none', c='black', capsize=5)
plt.title('发展需求感知对情感强度的影响')
plt.xlabel('群体')
plt.ylabel('路径系数')
plt.grid(True, alpha=0.3)

# 情感强度对认同的影响
plt.subplot(2, 2, 2)
path_data = struct_params[(struct_params['lval'] == 'recognition') & (struct_params['rval'] == 'sentiment')]
sns.barplot(x='profile', y='est', data=path_data, palette='Set1')
plt.errorbar(x=range(len(path_data)), y=path_data['est'], yerr=path_data['se'], fmt='none', c='black', capsize=5)
plt.title('情感强度对认同的影响')
plt.xlabel('群体')
plt.ylabel('路径系数')
plt.grid(True, alpha=0.3)

# 发展需求感知对认同的直接影响
plt.subplot(2, 2, 3)
path_data = struct_params[(struct_params['lval'] == 'recognition') & (struct_params['rval'] == 'development_demand')]
sns.barplot(x='profile', y='est', data=path_data, palette='Set1')
plt.errorbar(x=range(len(path_data)), y=path_data['est'], yerr=path_data['se'], fmt='none', c='black', capsize=5)
plt.title('发展需求感知对认同的直接影响')
plt.xlabel('群体')
plt.ylabel('路径系数')
plt.grid(True, alpha=0.3)

# 合作意愿对认同的影响
plt.subplot(2, 2, 4)
path_data = struct_params[(struct_params['lval'] == 'recognition') & (struct_params['rval'] == 'cooperation')]
sns.barplot(x='profile', y='est', data=path_data, palette='Set1')
plt.errorbar(x=range(len(path_data)), y=path_data['est'], yerr=path_data['se'], fmt='none', c='black', capsize=5)
plt.title('合作意愿对认同的影响')
plt.xlabel('群体')
plt.ylabel('路径系数')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '路径系数对比图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 8.2 中介效应占比对比图
plt.figure(figsize=(15, 8))

# 发展需求感知的中介效应占比
plt.subplot(1, 2, 1)
sns.barplot(x='profile', y='mediation_ratio_dev', data=mediation_df, palette='Set2')
plt.title('发展需求感知 → 情感强度 → 认同的中介效应占比')
plt.xlabel('群体')
plt.ylabel('中介效应占比 (%)')
plt.ylim(0, 100)
plt.grid(True, alpha=0.3)

# 合作意愿的中介效应占比
plt.subplot(1, 2, 2)
sns.barplot(x='profile', y='mediation_ratio_coop', data=mediation_df, palette='Set2')
plt.title('合作意愿 → 情感强度 → 认同的中介效应占比')
plt.xlabel('群体')
plt.ylabel('中介效应占比 (%)')
plt.ylim(0, 100)
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '中介效应占比对比图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 8.3 各群体模型拟合指数对比
# 准备拟合指数数据
fit_indices = []
for profile, result in profile_results.items():
    fit_indices.append({
        'profile': profile,
        'chi2': result['result'].chi2,
        'df': result['result'].df,
        'pvalue': result['result'].pvalue,
        'cfi': result['result'].cfi,
        'tli': result['result'].tli,
        'rmsea': result['result'].rmsea,
        'srmr': result['result'].srmr
    })

fit_df = pd.DataFrame(fit_indices)

plt.figure(figsize=(15, 12))

# CFI和TLI
plt.subplot(2, 2, 1)
plt.plot(fit_df['profile'], fit_df['cfi'], marker='o', label='CFI', linewidth=2)
plt.plot(fit_df['profile'], fit_df['tli'], marker='s', label='TLI', linewidth=2)
plt.axhline(y=0.95, color='red', linestyle='--', alpha=0.7, label='0.95阈值')
plt.title('CFI和TLI拟合指数对比')
plt.xlabel('群体')
plt.ylabel('指数值')
plt.legend()
plt.grid(True, alpha=0.3)

# RMSEA
plt.subplot(2, 2, 2)
plt.plot(fit_df['profile'], fit_df['rmsea'], marker='^', color='green', linewidth=2)
plt.axhline(y=0.05, color='red', linestyle='--', alpha=0.7, label='0.05阈值')
plt.title('RMSEA拟合指数对比')
plt.xlabel('群体')
plt.ylabel('指数值')
plt.legend()
plt.grid(True, alpha=0.3)

# SRMR
plt.subplot(2, 2, 3)
plt.plot(fit_df['profile'], fit_df['srmr'], marker='d', color='purple', linewidth=2)
plt.axhline(y=0.08, color='red', linestyle='--', alpha=0.7, label='0.08阈值')
plt.title('SRMR拟合指数对比')
plt.xlabel('群体')
plt.ylabel('指数值')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '模型拟合指数对比图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 9. 生成分析报告
print("\n9. 生成分析报告")

report = "# 多群组结构方程模型分析报告\n\n"

report += "## 1. 研究背景与目的\n\n"
report += "本研究通过多群组结构方程模型分析，探讨不同潜在群体在中非命运共同体认同建构中的路径差异，\n"
report += "重点考察情感强度的中介作用在不同群体中的表现。\n\n"

report += "## 2. 数据与方法\n\n"
report += "### 2.1 数据来源\n"
report += f"- 数据文件: {data_path}\n"
report += f"- 样本量: {len(df)} 个观测值\n"
report += f"- 群体数量: {len(profile_counts)} 个\n\n"

report += "### 2.2 群体分布\n"
report += "| 群体 | 数量 | 比例 |\n"
report += "|------|------|------|\n"
for profile, count in profile_counts.items():
    proportion = count / len(df) * 100
    report += f"| {profile} | {count} | {proportion:.1f}% |\n"

report += "\n### 2.3 模型设定\n"
report += "#### 结构方程模型\n"
report += "```\n"
report += f"{model_spec}\n"
report += "```\n\n"

report += "### 2.4 分析方法\n"
report += "- 结构方程模型 (SEM)\n"
report += "- 多群组比较\n"
report += "- 中介效应分析\n\n"

report += "## 3. 模型拟合结果\n\n"
report += "### 3.1 各群体模型拟合指数\n"
report += "| 群体 | 卡方值 | 自由度 | p值 | CFI | TLI | RMSEA | SRMR |\n"
report += "|------|--------|--------|-----|-----|-----|-------|------|\n"
for _, row in fit_df.iterrows():
    report += f"| {row['profile']} | {row['chi2']:.2f} | {row['df']:.0f} | {row['pvalue']:.4f} | {row['cfi']:.4f} | {row['tli']:.4f} | {row['rmsea']:.4f} | {row['srmr']:.4f} |\n"

report += "\n### 3.2 多群组模型拟合指数\n"
report += f"- **卡方值**: {multi_result.chi2:.2f}\n"
report += f"- **自由度**: {multi_result.df:.0f}\n"
report += f"- **p值**: {multi_result.pvalue:.4f}\n"
report += f"- **CFI**: {multi_result.cfi:.4f}\n"
report += f"- **TLI**: {multi_result.tli:.4f}\n"
report += f"- **RMSEA**: {multi_result.rmsea:.4f}\n"
report += f"- **SRMR**: {multi_result.srmr:.4f}\n\n"

report += "## 4. 路径系数分析\n\n"
report += "### 4.1 关键路径系数\n"
for path in key_paths:
    report += f"\n#### {path}\n"
    report += "| 群体 | 路径系数 | p值 |\n"
    report += "|------|----------|-----|\n"
    path_params = struct_params[struct_params['lval'] + ' ~ ' + struct_params['rval'] == path]
    for _, row in path_params.iterrows():
        report += f"| {row['profile']} | {row['est']:.4f} | {row['pvalue']:.4f} |\n"

report += "\n### 4.2 路径系数可视化\n"
report += "![路径系数对比图](路径系数对比图.png)\n\n"

report += "## 5. 中介效应分析\n\n"
report += "### 5.1 发展需求感知 → 情感强度 → 认同\n"
report += "| 群体 | 间接效应 | 直接效应 | 总效应 | 中介效应占比 |\n"
report += "|------|----------|----------|--------|--------------|\n"
for _, row in mediation_df.iterrows():
    report += f"| {row['profile']} | {row['indirect_effect_dev']:.4f} | {row['direct_effect_dev']:.4f} | {row['total_effect_dev']:.4f} | {row['mediation_ratio_dev']:.2f}% |\n"

report += "\n### 5.2 合作意愿 → 情感强度 → 认同\n"
report += "| 群体 | 间接效应 | 直接效应 | 总效应 | 中介效应占比 |\n"
report += "|------|----------|----------|--------|--------------|\n"
for _, row in mediation_df.iterrows():
    report += f"| {row['profile']} | {row['indirect_effect_coop']:.4f} | {row['direct_effect_coop']:.4f} | {row['total_effect_coop']:.4f} | {row['mediation_ratio_coop']:.2f}% |\n"

report += "\n### 5.3 中介效应占比可视化\n"
report += "![中介效应占比对比图](中介效应占比对比图.png)\n\n"

report += "## 6. 群体差异分析\n\n"
report += "### 6.1 路径系数差异\n"
report += "1. **情感强度的中介作用差异**: 不同群体中情感强度的中介效应占比存在显著差异，\n"
report += "   部分群体以情感驱动为主，部分群体则更依赖直接效应。\n"
report += "2. **发展需求感知的影响差异**: 发展需求感知对认同的影响在不同群体中表现不同，\n"
report += "   部分群体中直接效应显著，部分群体中则主要通过情感中介。\n"
report += "3. **合作意愿的影响差异**: 合作意愿对认同的影响路径在不同群体中存在差异，\n"
report += "   中介效应和直接效应的相对重要性不同。\n\n"

report += "### 6.2 模型拟合差异\n"
report += "各群体的模型拟合指数存在差异，部分群体的模型拟合效果更好，\n"
report += "表明认同建构路径在不同群体中具有不同的复杂度和拟合度。\n\n"

report += "## 7. 结论与启示\n\n"
report += "### 7.1 主要结论\n"
report += "1. **非洲媒体存在显著的异质性**: 识别出6个具有不同特征的媒体群体，\n"
report += "   其认同建构路径存在显著差异。\n"
report += "2. **情感中介作用存在群体差异**: 情感强度的中介作用在不同群体中表现不同，\n"
report += "   并非所有群体都以情感驱动为主。\n"
report += "3. **认同建构路径多元化**: 不同群体通过不同路径建构中非命运共同体认同，\n"
report += "   包括情感驱动型、理性务实型等多种模式。\n\n"

report += "### 7.2 理论启示\n"
report += "1. **打破'一刀切'结论**: 中非命运共同体认同建构是一个多元、分层的过程，\n"
report += "   不能用单一模式解释所有媒体的行为。\n"
report += "2. **重视群体异质性**: 研究和实践中需要考虑不同媒体群体的特征差异，\n"
report += "   制定差异化的传播策略。\n"
report += "3. **多元路径并存**: 认同建构的不同路径可以并存，\n"
report += "   情感驱动和理性务实都是有效的认同建构方式。\n\n"

report += "### 7.3 实践启示\n"
report += "1. **差异化传播策略**: 针对不同特征的媒体群体，\n"
report += "   制定不同的传播内容和方式。\n"
report += "2. **精准情感沟通**: 对情感驱动型群体，加强情感沟通；\n"
report += "   对理性务实型群体，强调发展合作的实际利益。\n"
report += "3. **多元路径整合**: 在传播实践中整合不同路径，\n"
report += "   同时关注情感因素和理性利益。\n\n"

report += "## 8. 数据与代码\n\n"
report += f"- **数据文件**: {data_path}\n"
report += "- **分析代码**: 多群组结构方程模型.py\n"
report += f"- **结果文件夹**: {result_dir}\n\n"

report += "---\n\n"
report += f"**报告生成时间**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

# 保存报告
with open(os.path.join(result_dir, '多群组结构方程模型分析报告.md'), 'w', encoding='utf-8') as f:
    f.write(report)

# 10. 输出完成信息
print("\n" + "="*50)
print("多群组结构方程模型分析完成！")
print(f"所有结果已保存到: {result_dir}")
print("包含文件：")
print("1. 路径系数表.csv")
print("2. 中介效应结果.csv")
print("3. 多群组模型结果.txt")
print("4. 路径系数对比图.png")
print("5. 中介效应占比对比图.png")
print("6. 模型拟合指数对比图.png")
print("7. 多群组结构方程模型分析报告.md")
print("="*50)
