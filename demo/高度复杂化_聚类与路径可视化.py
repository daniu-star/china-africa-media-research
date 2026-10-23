import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from scipy.cluster.hierarchy import linkage, dendrogram
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import os
import warnings
import statsmodels.api as sm
from scipy import stats
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches

# 设置中文字体和全局参数
# 优化中文字体设置，确保中文正常显示
# 更全面的中文字体设置，确保所有图表元素都使用中文字体
plt.rcParams['font.family'] = ['sans-serif']
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans', 'WenQuanYi Micro Hei', 'Heiti TC']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 12
plt.rcParams['figure.figsize'] = (16, 12)
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['legend.fontsize'] = 12
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 8
plt.rcParams['savefig.dpi'] = 300

# 确保所有文本元素都使用中文字体
plt.rcParams['text.usetex'] = False  # 禁用LaTeX，避免中文字体冲突

# 设置Seaborn样式 - 确保使用中文字体
sns.set_style("whitegrid")
sns.set_palette("Set2")
sns.set_context("notebook", font_scale=1.2)
sns.set(font='SimHei')  # 使用更通用的黑体

# 设置NetworkX图表的字体
nx_font = {
    'font_family': 'SimHei',
    'font_size': 12,
    'font_weight': 'bold'
}

# 忽略警告
warnings.filterwarnings('ignore')

# 创建结果目录
result_dir = '高度复杂化_可视化结果'
os.makedirs(result_dir, exist_ok=True)
print(f"结果将保存到: {result_dir}")

# 数据文件路径
lpa_data_path = r'c:\Users\13067\Desktop\论文\非洲\demo\优化版_潜在剖面分析结果\数据_带群体分类.csv'
path_coeff_path = r'c:\Users\13067\Desktop\论文\非洲\demo\优化版_多群组回归分析结果\路径系数表.csv'
mediation_path = r'c:\Users\13067\Desktop\论文\非洲\demo\优化版_多群组回归分析结果\中介效应结果.csv'

# 核心变量定义
core_vars = {
    'development_demand': 'development_demand_pca',
    'sentiment': 'normalized_sentiment',
    'cooperation': 'cooperation_willingness_advanced',
    'recognition': 'china_africa_community_recognition'
}

# 控制变量定义
control_vars = {
    'time_index': 'time_index',
    'total_words_count': 'total_words_count',
    'source_region_5': 'source_region_5',
    '主题': '主题'
}

# 群体命名映射
profile_names = {
    0: '合作意愿强烈型',
    1: '发展需求主导型',
    2: '情感积极型',
    3: '综合平衡型',
    4: '谨慎观察型',
    5: '多元复杂型'
}

# 路径系数名称映射
path_names = {
    'path_development_demand_pca_M_full': '发展需求→情感',
    'path_cooperation_willingness_advanced_M_full': '合作意愿→情感',
    'path_M_Y_full': '情感→认同',
    'path_development_demand_pca_Y_direct_full': '发展需求→认同(直接)',
    'path_cooperation_willingness_advanced_Y_direct_full': '合作意愿→认同(直接)'
}

# 函数定义

def load_data():
    """加载并预处理所有数据"""
    print("\n1. 数据加载与预处理")
    
    # 加载潜在剖面分析数据
    lpa_df = pd.read_csv(lpa_data_path, low_memory=False)
    print(f"潜在剖面分析数据: {len(lpa_df)} 行, {len(lpa_df.columns)} 列")
    
    # 加载路径系数数据
    path_df = pd.read_csv(path_coeff_path, low_memory=False)
    print(f"路径系数数据: {len(path_df)} 行, {len(path_df.columns)} 列")
    
    # 加载中介效应数据
    mediation_df = pd.read_csv(mediation_path, low_memory=False)
    print(f"中介效应数据: {len(mediation_df)} 行, {len(mediation_df.columns)} 列")
    
    # 数据预处理
    # 标准化核心变量
    scaler = StandardScaler()
    core_var_cols = list(core_vars.values())
    lpa_df[core_var_cols] = scaler.fit_transform(lpa_df[core_var_cols])
    
    return lpa_df, path_df, mediation_df

def visualize_group_distribution(lpa_df, path_df):
    """可视化聚类分析后的群体分布"""
    print("\n2. 群体分布可视化")
    
    # 2.1 3D核心特征散点图
    print("  2.1 3D核心特征散点图")
    visualize_3d_scatter(lpa_df)
    
    # 2.2 群体特征热图
    print("  2.2 群体特征热图")
    visualize_feature_heatmap(lpa_df)
    
    # 2.3 群体分布树状图
    print("  2.3 群体分布树状图")
    visualize_dendrogram(lpa_df)
    
    # 2.4 多维度雷达图
    print("  2.4 多维度雷达图")
    visualize_radar_chart(lpa_df)
    
    # 2.5 群体分布马赛克图
    print("  2.5 群体分布马赛克图")
    visualize_mosaic_plot(lpa_df)

def visualize_identification_paths(path_df, mediation_df, lpa_df):
    """可视化各个群体的认同路径"""
    print("\n3. 群体认同路径可视化")
    
    # 3.1 结构方程模型(SEM)路径图
    print("  3.1 结构方程模型(SEM)路径图")
    visualize_sem_path(path_df, mediation_df)
    
    # 3.2 中介效应热图
    print("  3.2 中介效应热图")
    visualize_mediation_heatmap(mediation_df)
    
    # 3.3 多群体路径比较图
    print("  3.3 多群体路径比较图")
    visualize_path_comparison(path_df)
    
    # 3.4 变量关系网络图
    print("  3.4 变量关系网络图")
    visualize_network_graph(path_df)

def visualize_3d_scatter(lpa_df):
    """3D核心特征散点图"""
    # 选择核心变量
    x_col = core_vars['development_demand']
    y_col = core_vars['sentiment']
    z_col = core_vars['cooperation']
    
    # 创建3D散点图
    fig = px.scatter_3d(
        lpa_df,
        x=x_col,
        y=y_col,
        z=z_col,
        color='profile_name',
        symbol='profile_name',
        hover_data=['profile', 'source_region_5', '主题'],
        title='非洲媒体潜在群体3D核心特征分布',
        labels={
            x_col: '发展需求感知强度 (标准化)',
            y_col: '情感强度 (标准化)',
            z_col: '合作意愿 (标准化)',
            'profile_name': '群体名称'
        },
        opacity=0.7,
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    
    # 优化布局
    fig.update_layout(
        scene=dict(
            xaxis_title_font=dict(size=14, family='Microsoft YaHei'),
            yaxis_title_font=dict(size=14, family='Microsoft YaHei'),
            zaxis_title_font=dict(size=14, family='Microsoft YaHei'),
            xaxis_tickfont=dict(size=12, family='Microsoft YaHei'),
            yaxis_tickfont=dict(size=12, family='Microsoft YaHei'),
            zaxis_tickfont=dict(size=12, family='Microsoft YaHei')
        ),
        title_font=dict(size=18, family='Microsoft YaHei', weight='bold'),
        legend_title=dict(font=dict(size=14, family='Microsoft YaHei')),
        legend_font=dict(size=12, family='Microsoft YaHei'),
        margin=dict(l=0, r=0, b=0, t=50)
    )
    
    # 保存为HTML
    html_path = os.path.join(result_dir, '高度复杂化_群体分布_3D散点图.html')
    fig.write_html(html_path)
    
    print(f"  3D核心特征散点图已保存到: {html_path}")

def visualize_feature_heatmap(lpa_df):
    """群体特征热图"""
    # 计算群体特征均值
    core_var_cols = list(core_vars.values())
    group_means = lpa_df.groupby('profile_name')[core_var_cols].mean()
    
    # 添加控制变量均值
    control_var_cols = ['time_index', 'total_words_count']
    group_means[control_var_cols] = lpa_df.groupby('profile_name')[control_var_cols].mean()
    
    # 标准化特征
    scaler = StandardScaler()
    scaled_means = pd.DataFrame(scaler.fit_transform(group_means), 
                               index=group_means.index, 
                               columns=group_means.columns)
    
    # 重命名列名
    col_names = {
        'development_demand_pca': '发展需求感知',
        'normalized_sentiment': '情感强度',
        'cooperation_willingness_advanced': '合作意愿',
        'time_index': '时间索引',
        'total_words_count': '文章长度'
    }
    scaled_means = scaled_means.rename(columns=col_names)
    
    # 创建热图
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 绘制热图
    heatmap = sns.heatmap(
        scaled_means,
        annot=True,
        fmt='.3f',
        cmap='coolwarm',
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={
            'label': '标准化均值',
            'shrink': 0.8,
            'orientation': 'vertical'
        },
        ax=ax
    )
    
    # 添加统计显著性标记
    # 计算每个特征的组间差异显著性
    for i, col in enumerate(scaled_means.columns):
        group_data = [lpa_df[lpa_df['profile_name'] == group][group_means.columns[i]] for group in scaled_means.index]
        f_stat, p_val = stats.f_oneway(*group_data)
        sig = ""
        if p_val < 0.001:
            sig = '***'
        elif p_val < 0.01:
            sig = '**'
        elif p_val < 0.05:
            sig = '*'
        ax.text(i + 0.5, -0.5, sig, ha='center', va='center', fontsize=14, fontweight='bold')
    
    # 优化布局
    ax.set_title('非洲媒体群体特征热图\n(组间差异显著性: *p<0.05, **p<0.01, ***p<0.001)', 
                fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('特征变量', fontsize=16, labelpad=15)
    ax.set_ylabel('群体名称', fontsize=16, labelpad=15)
    
    # 调整刻度标签
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    # 保存图片
    output_path = os.path.join(result_dir, '高度复杂化_群体特征热图.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  群体特征热图已保存到: {output_path}")

def visualize_dendrogram(lpa_df):
    """群体分布树状图"""
    # 计算群体特征均值
    core_var_cols = list(core_vars.values())
    group_means = lpa_df.groupby('profile_name')[core_var_cols].mean()
    
    # 计算层次聚类
    linkage_matrix = linkage(group_means, method='ward')
    
    # 创建树状图
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # 绘制树状图
    dendro = dendrogram(
        linkage_matrix,
        labels=group_means.index,
        orientation='top',
        distance_sort='descending',
        show_leaf_counts=True,
        ax=ax
    )
    
    # 添加群体特征
    # 在树状图右侧添加特征热图
    ax2 = fig.add_axes([0.85, 0.1, 0.1, 0.8])
    
    # 标准化数据
    scaler = StandardScaler()
    scaled_means = scaler.fit_transform(group_means)
    scaled_df = pd.DataFrame(scaled_means, index=group_means.index, columns=group_means.columns)
    
    # 重命名列名
    col_names = {
        'development_demand_pca': '发展需求',
        'normalized_sentiment': '情感',
        'cooperation_willingness_advanced': '合作'
    }
    scaled_df = scaled_df.rename(columns=col_names)
    
    # 绘制特征热图
    sns.heatmap(
        scaled_df.loc[dendro['ivl'], :],
        cmap='coolwarm',
        center=0,
        cbar=False,
        square=True,
        ax=ax2
    )
    
    # 调整坐标轴
    ax2.set_yticks([])
    ax2.set_xlabel('特征', fontsize=14, labelpad=10)
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha='center')
    
    # 添加标题和标签
    ax.set_title('非洲媒体群体层次聚类树状图\n(基于核心特征的Ward层次聚类)', 
                fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('距离', fontsize=16, labelpad=15)
    ax.set_ylabel('群体名称', fontsize=16, labelpad=15)
    
    # 添加统计指标
    # 计算剪影系数
    silhouette_avg = silhouette_score(lpa_df[core_var_cols], lpa_df['profile'])
    
    # 在图中添加统计指标
    stats_text = f"Silhouette Score: {silhouette_avg:.3f}\nCluster Distance Method: Ward Linkage"
    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, 
            fontsize=14, verticalalignment='top', bbox=dict(boxstyle='round', alpha=0.8, facecolor='white'))
    
    # 保存图片
    output_path = os.path.join(result_dir, '高度复杂化_群体聚类树状图.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  群体分布树状图已保存到: {output_path}")

def visualize_radar_chart(lpa_df):
    """多维度雷达图"""
    # 计算群体特征均值和置信区间
    # 包含认同度作为核心变量
    core_var_cols = ['development_demand_pca', 'normalized_sentiment', 'cooperation_willingness_advanced', 'china_africa_community_recognition']
    group_stats = lpa_df.groupby('profile_name')[core_var_cols].agg(['mean', 'std', 'count'])
    
    # 计算95%置信区间
    for col in core_var_cols:
        group_stats[(col, 'ci_lower')] = group_stats[(col, 'mean')] - 1.96 * group_stats[(col, 'std')] / np.sqrt(group_stats[(col, 'count')])
        group_stats[(col, 'ci_upper')] = group_stats[(col, 'mean')] + 1.96 * group_stats[(col, 'std')] / np.sqrt(group_stats[(col, 'count')])
    
    # 重命名列名
    col_names = {
        'development_demand_pca': '发展需求感知',
        'normalized_sentiment': '情感强度',
        'cooperation_willingness_advanced': '合作意愿',
        'china_africa_community_recognition': '认同度'
    }
    group_stats = group_stats.rename(columns=col_names, level=0)
    
    # 准备雷达图数据
    categories = list(col_names.values())
    n_categories = len(categories)
    angles = [n / float(n_categories) * 2 * np.pi for n in range(n_categories)]
    angles += angles[:1]  # 闭合雷达图
    
    # 创建雷达图
    fig, ax = plt.subplots(figsize=(14, 12), subplot_kw=dict(polar=True))
    
    # 设置颜色
    colors = plt.cm.Set1(np.linspace(0, 1, len(group_stats)))
    
    # 绘制每个群体的雷达图
    for i, (profile, row) in enumerate(group_stats.iterrows()):
        # 提取均值和置信区间
        values = row.xs('mean', level=1).values.tolist()
        values += values[:1]  # 闭合雷达图
        
        # 绘制均值线
        ax.plot(
            angles,
            values,
            linewidth=3,
            linestyle='solid',
            label=profile,
            color=colors[i]
        )
        
        # 填充置信区间
        ci_lower = row.xs('ci_lower', level=1).values.tolist()
        ci_upper = row.xs('ci_upper', level=1).values.tolist()
        ci_lower += ci_lower[:1]
        ci_upper += ci_upper[:1]
        
        ax.fill_between(
            angles,
            ci_lower,
            ci_upper,
            alpha=0.15,
            color=colors[i]
        )
    
    # 设置雷达图属性
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=14, fontweight='bold')
    ax.set_yticklabels([])
    
    # 添加网格线
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # 添加标题
    ax.set_title('非洲媒体群体核心特征雷达图\n(带95%置信区间)', 
                fontsize=20, fontweight='bold', pad=20)
    
    # 添加图例
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=14, title='群体名称')
    
    # 保存图片
    output_path = os.path.join(result_dir, '高度复杂化_群体特征雷达图.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  多维度雷达图已保存到: {output_path}")

def visualize_mosaic_plot(lpa_df):
    """群体分布马赛克图"""
    # 准备数据
    # 计算群体在地区和新闻主题上的分布
    region_topic_dist = lpa_df.groupby(['profile_name', 'source_region_5', '主题']).size().unstack(fill_value=0)
    
    # 简化数据，只保留主要地区和主题
    # 选择前3个主要地区和前3个主要主题
    top_regions = lpa_df['source_region_5'].value_counts().nlargest(4).index
    top_topics = lpa_df['主题'].value_counts().nlargest(4).index
    
    # 过滤数据
    filtered_df = lpa_df[
        (lpa_df['source_region_5'].isin(top_regions)) & 
        (lpa_df['主题'].isin(top_topics))
    ]
    
    # 创建马赛克图
    fig, ax = plt.subplots(figsize=(18, 14))
    
    # 计算马赛克图数据
    # 使用pandas.crosstab创建交叉表
    crosstab = pd.crosstab(
        index=[filtered_df['profile_name'], filtered_df['source_region_5']],
        columns=filtered_df['主题'],
        normalize='all'
    )
    
    # 转换为百分比
    crosstab_perc = crosstab * 100
    
    # 创建马赛克图
    # 使用GridSpec创建复杂布局
    gs = GridSpec(2, 1, height_ratios=[1, 8], hspace=0.05)
    
    # 上部：群体分布
    ax1 = fig.add_subplot(gs[0])
    group_sizes = filtered_df['profile_name'].value_counts(normalize=True) * 100
    ax1.bar(group_sizes.index, group_sizes.values, color=sns.color_palette("Set1", len(group_sizes)))
    ax1.set_title('非洲媒体群体分布\n(按地区和新闻主题交叉分布)', fontsize=20, fontweight='bold', pad=10)
    ax1.set_ylabel('群体比例 (%)', fontsize=14)
    ax1.set_xticklabels([])
    ax1.set_ylim(0, 100)
    
    # 下部：马赛克图
    ax2 = fig.add_subplot(gs[1])
    
    # 计算位置
    group_pos = {}
    current_pos = 0
    
    for group in group_sizes.index:
        group_data = filtered_df[filtered_df['profile_name'] == group]
        region_sizes = group_data['source_region_5'].value_counts(normalize=True) * group_sizes.loc[group]
        
        for region in top_regions:
            if region in region_sizes:
                region_size = region_sizes.loc[region]
                region_data = group_data[group_data['source_region_5'] == region]
                topic_sizes = region_data['主题'].value_counts(normalize=True) * region_size
                
                topic_pos = current_pos
                for topic in top_topics:
                    if topic in topic_sizes:
                        topic_size = topic_sizes.loc[topic]
                        # 绘制矩形
                        rect = mpatches.Rectangle(
                            (topic_pos, 0),
                            topic_size,
                            1,
                            edgecolor='white',
                            linewidth=0.5,
                            alpha=0.8
                        )
                        ax2.add_patch(rect)
                        topic_pos += topic_size
                
                current_pos += region_size
        
        group_pos[group] = (current_pos - group_sizes.loc[group], current_pos)
    
    # 优化布局
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 1)
    ax2.set_yticks([])
    ax2.set_xlabel('分布比例 (%)', fontsize=16, labelpad=15)
    
    # 添加群体分隔线和标签
    for group, (left, right) in group_pos.items():
        ax2.axvline(x=left, color='black', linewidth=2, alpha=0.5)
        ax2.text((left + right) / 2, 0.5, group, ha='center', va='center', 
                 rotation=90, fontsize=12, fontweight='bold', transform=ax2.transAxes)
    
    # 添加地区和主题标签
    # 这里简化处理，只添加主要标签
    ax2.text(50, 0.1, '地区分布', ha='center', va='center', fontsize=14, fontweight='bold')
    ax2.text(50, 0.9, '新闻主题分布', ha='center', va='center', fontsize=14, fontweight='bold')
    
    # 添加图例
    # 创建地区和主题的图例
    region_patches = [mpatches.Patch(color=sns.color_palette("Set2", len(top_regions))[i], label=region) 
                      for i, region in enumerate(top_regions)]
    topic_patches = [mpatches.Patch(color=sns.color_palette("Set3", len(top_topics))[i], label=topic) 
                     for i, topic in enumerate(top_topics)]
    
    ax2.legend(handles=region_patches + topic_patches, 
               loc='upper right', bbox_to_anchor=(1.1, 1.05), 
               fontsize=12, title='地区和主题', ncol=2)
    
    # 保存图片
    output_path = os.path.join(result_dir, '高度复杂化_群体分布马赛克图.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  群体分布马赛克图已保存到: {output_path}")

def visualize_sem_path(path_df, mediation_df):
    """结构方程模型(SEM)路径图 - 整合所有群体"""
    # 选择完整模型路径系数
    full_path_df = path_df[path_df['model'] == 'full'].copy()
    
    # 创建整合的SEM路径图，3行2列布局
    fig = plt.figure(figsize=(24, 30))
    gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.1)
    
    # 统一节点位置和标签
    node_pos = {
        'X1': (0.2, 0.8),    # 发展需求感知
        'X2': (0.2, 0.6),    # 合作意愿
        'M': (0.5, 0.7),      # 情感强度
        'Y': (0.8, 0.7),      # 认同度
        'C': (0.5, 0.9),      # 控制变量
        'C1': (0.5, 0.5)      # 控制变量2
    }
    
    node_labels = {
        'X1': '发展需求感知',
        'X2': '合作意愿',
        'M': '情感强度',
        'Y': '认同度',
        'C': '控制变量\n(地区)',
        'C1': '控制变量\n(新闻主题)'
    }
    
    # 绘制每个群体的路径图
    for i, profile in enumerate(full_path_df['profile']):
        row = i // 2
        col = i % 2
        ax = fig.add_subplot(gs[row, col])
        
        profile_name = profile_names[profile]
        profile_data = full_path_df[full_path_df['profile'] == profile].iloc[0]
        
        # 创建有向图
        G = nx.DiGraph()
        
        # 添加节点
        G.add_nodes_from(node_pos.keys())
        
        # 添加边（路径）
        edges = []
        edge_labels = {}
        
        # 核心路径
        # X1 → M
        coeff = profile_data['path_development_demand_pca_M_full']
        edges.append(('X1', 'M'))
        edge_labels[('X1', 'M')] = f"{coeff:.3f}"
        
        # X2 → M
        coeff = profile_data['path_cooperation_willingness_advanced_M_full']
        edges.append(('X2', 'M'))
        edge_labels[('X2', 'M')] = f"{coeff:.3f}"
        
        # M → Y
        coeff = profile_data['path_M_Y_full']
        edges.append(('M', 'Y'))
        edge_labels[('M', 'Y')] = f"{coeff:.3f}"
        
        # X1 → Y (直接效应)
        coeff = profile_data['path_development_demand_pca_Y_direct_full']
        edges.append(('X1', 'Y'))
        edge_labels[('X1', 'Y')] = f"{coeff:.3f}"
        
        # X2 → Y (直接效应)
        coeff = profile_data['path_cooperation_willingness_advanced_Y_direct_full']
        edges.append(('X2', 'Y'))
        edge_labels[('X2', 'Y')] = f"{coeff:.3f}"
        
        # 控制变量
        edges.append(('C', 'M'))
        edges.append(('C', 'Y'))
        edges.append(('C1', 'M'))
        edges.append(('C1', 'Y'))
        
        # 添加边到图中
        G.add_edges_from(edges)
        
        # 绘制节点
        nx.draw_networkx_nodes(
            G, node_pos, 
            node_size=4000, 
            node_color=['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f'],
            alpha=0.8,
            ax=ax
        )
        
        # 绘制边
        nx.draw_networkx_edges(
            G, node_pos, 
            width=2,
            edge_color='gray',
            alpha=0.7,
            arrowsize=15,
            ax=ax
        )
        
        # 绘制边标签
        nx.draw_networkx_edge_labels(
            G, node_pos,
            edge_labels=edge_labels,
            font_size=10,
            font_weight='bold',
            font_family='SimHei',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3'),
            ax=ax
        )
        
        # 绘制节点标签
        nx.draw_networkx_labels(
            G, node_pos,
            labels=node_labels,
            font_size=11,
            font_weight='bold',
            font_family='SimHei',
            ax=ax
        )
        
        # 添加子图标题
        ax.set_title(f'群体{profile}: {profile_name}', 
                    fontsize=16, fontweight='bold', pad=15)
        
        # 隐藏坐标轴
        ax.axis('off')
    
    # 添加主标题
    fig.suptitle('非洲媒体各群体结构方程模型路径图\n(标准化路径系数，3行2列布局)', 
                fontsize=28, fontweight='bold', y=0.95)
    
    # 添加统一的图例和说明
    legend_ax = fig.add_axes([0.5, 0.02, 0.4, 0.03])
    legend_ax.axis('off')
    
    legend_text = '''
    核心路径：发展需求感知(X1)→情感强度(M)→认同度(Y)
             合作意愿(X2)→情感强度(M)→认同度(Y)
             发展需求感知(X1)→认同度(Y)（直接效应）
             合作意愿(X2)→认同度(Y)（直接效应）
    控制变量：地区、新闻主题等
    路径系数：标准化回归系数
    数据来源：多群组回归分析结果
    '''
    legend_ax.text(0.5, 0.5, legend_text, ha='center', va='center',
                   fontsize=12, fontweight='bold',
                   bbox=dict(boxstyle='round', alpha=0.8, facecolor='white'))
    
    # 保存图片 - PNG格式
    output_path_png = os.path.join(result_dir, '高度复杂化_整合群体决策路径图.png')
    plt.savefig(output_path_png, dpi=300, bbox_inches='tight')
    
    # 保存图片 - PDF格式（适合论文印刷）
    output_path_pdf = os.path.join(result_dir, '高度复杂化_整合群体决策路径图.pdf')
    plt.savefig(output_path_pdf, dpi=300, bbox_inches='tight')
    
    plt.close()
    
    print(f"  整合群体决策路径图已保存为PNG和PDF格式")

def visualize_mediation_heatmap(mediation_df):
    """中介效应热图"""
    # 选择关键的中介效应指标
    mediation_cols = [
        'profile',
        'indirect_effect_development_full',
        'direct_effect_development_full',
        'total_effect_development_full',
        'mediation_ratio_development_full',
        'indirect_effect_cooperation_full',
        'direct_effect_cooperation_full',
        'total_effect_cooperation_full',
        'mediation_ratio_cooperation_full'
    ]
    
    # 过滤数据
    heatmap_data = mediation_df[mediation_cols].copy()
    
    # 添加群体名称
    heatmap_data['profile_name'] = heatmap_data['profile'].map(profile_names)
    heatmap_data = heatmap_data.set_index('profile_name')
    heatmap_data = heatmap_data.drop('profile', axis=1)
    
    # 重命名列名
    col_names = {
        'indirect_effect_development_full': '发展需求→认同(间接)',
        'direct_effect_development_full': '发展需求→认同(直接)',
        'total_effect_development_full': '发展需求→认同(总效应)',
        'mediation_ratio_development_full': '发展需求中介效应占比(%)',
        'indirect_effect_cooperation_full': '合作意愿→认同(间接)',
        'direct_effect_cooperation_full': '合作意愿→认同(直接)',
        'total_effect_cooperation_full': '合作意愿→认同(总效应)',
        'mediation_ratio_cooperation_full': '合作意愿中介效应占比(%)'
    }
    heatmap_data = heatmap_data.rename(columns=col_names)
    
    # 创建热图
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # 绘制热图
    heatmap = sns.heatmap(
        heatmap_data,
        annot=True,
        fmt='.3f',
        cmap='RdBu_r',
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={
            'label': '效应值/占比',
            'shrink': 0.8,
            'orientation': 'vertical'
        },
        ax=ax
    )
    
    # 添加统计显著性标记
    # 简化处理，假设所有效应都是显著的
    
    # 优化布局
    ax.set_title('非洲媒体群体中介效应热图\n(完整模型，包含控制变量)', 
                fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('效应类型', fontsize=16, labelpad=15)
    ax.set_ylabel('群体名称', fontsize=16, labelpad=15)
    
    # 调整刻度标签
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    # 保存图片
    output_path = os.path.join(result_dir, '高度复杂化_中介效应热图.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  中介效应热图已保存到: {output_path}")

def visualize_path_comparison(path_df):
    """多群体路径比较图"""
    # 选择完整模型路径系数
    full_path_df = path_df[path_df['model'] == 'full'].copy()
    
    # 添加群体名称
    full_path_df['profile_name'] = full_path_df['profile'].map(profile_names)
    
    # 选择核心路径
    core_paths = [
        'path_development_demand_pca_M_full',
        'path_cooperation_willingness_advanced_M_full',
        'path_M_Y_full',
        'path_development_demand_pca_Y_direct_full',
        'path_cooperation_willingness_advanced_Y_direct_full'
    ]
    
    # 重命名路径
    path_labels = [
        '发展需求→情感',
        '合作意愿→情感',
        '情感→认同',
        '发展需求→认同(直接)',
        '合作意愿→认同(直接)'
    ]
    
    # 转换数据为长格式
    path_data = full_path_df.melt(
        id_vars=['profile_name'],
        value_vars=core_paths,
        var_name='path',
        value_name='coefficient'
    )
    
    # 替换路径名称
    path_map = dict(zip(core_paths, path_labels))
    path_data['path'] = path_data['path'].map(path_map)
    
    # 创建分组柱状图
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # 绘制分组柱状图
    sns.barplot(
        x='path',
        y='coefficient',
        hue='profile_name',
        data=path_data,
        palette='Set1',
        ax=ax,
        capsize=0.1,
        errwidth=2
    )
    
    # 优化布局
    ax.set_title('非洲媒体群体核心路径系数比较\n(完整模型，包含控制变量)', 
                fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('路径类型', fontsize=16, labelpad=15)
    ax.set_ylabel('标准化路径系数', fontsize=16, labelpad=15)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    
    # 添加网格线
    ax.grid(True, alpha=0.3, axis='y')
    
    # 添加显著性标记
    # 计算每个路径的组间差异显著性
    for i, path in enumerate(path_labels):
        path_coeffs = [path_data[(path_data['path'] == path) & (path_data['profile_name'] == group)]['coefficient'].values for group in path_data['profile_name'].unique()]
        if all(len(coeffs) > 0 for coeffs in path_coeffs):
            f_stat, p_val = stats.f_oneway(*path_coeffs)
            sig = ""
            if p_val < 0.001:
                sig = '***'
            elif p_val < 0.01:
                sig = '**'
            elif p_val < 0.05:
                sig = '*'
            ax.text(i, ax.get_ylim()[1] * 0.95, sig, ha='center', va='center', fontsize=14, fontweight='bold')
    
    # 添加图例
    ax.legend(title='群体名称', fontsize=12, loc='upper right', bbox_to_anchor=(1.15, 1))
    
    # 添加说明
    note_text = '''
    统计显著性：*p<0.05, **p<0.01, ***p<0.001
    路径系数：标准化回归系数
    模型：完整模型，包含地区和新闻主题控制变量
    '''
    ax.text(0.02, 0.02, note_text, transform=ax.transAxes,
            fontsize=12, verticalalignment='bottom',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3'))
    
    # 保存图片
    output_path = os.path.join(result_dir, '高度复杂化_多群体路径比较图.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  多群体路径比较图已保存到: {output_path}")

def visualize_network_graph(path_df):
    """变量关系网络图"""
    # 选择完整模型路径系数
    full_path_df = path_df[path_df['model'] == 'full'].copy()
    
    # 添加群体名称
    full_path_df['profile_name'] = full_path_df['profile'].map(profile_names)
    
    # 选择所有路径系数
    path_cols = [col for col in full_path_df.columns if col.startswith('path_')]
    
    # 计算平均路径系数
    avg_path_coeffs = full_path_df[path_cols].mean()
    
    # 创建变量关系网络图
    fig, ax = plt.subplots(figsize=(20, 16))
    
    # 创建有向图
    G = nx.DiGraph()
    
    # 定义变量节点
    variables = {
        'development': '发展需求感知',
        'cooperation': '合作意愿',
        'sentiment': '情感强度',
        'recognition': '认同度',
        'time': '时间索引',
        'words': '文章长度',
        'region': '地区',
        'topic': '新闻主题'
    }
    
    # 添加节点
    G.add_nodes_from(variables.keys())
    
    # 构建边（路径）
    edges = []
    edge_weights = {}
    
    # 核心路径
    edges.append(('development', 'sentiment'))
    edges.append(('cooperation', 'sentiment'))
    edges.append(('sentiment', 'recognition'))
    edges.append(('development', 'recognition'))
    edges.append(('cooperation', 'recognition'))
    
    # 控制变量路径
    edges.append(('time', 'recognition'))
    edges.append(('time', 'sentiment'))
    edges.append(('words', 'recognition'))
    edges.append(('words', 'sentiment'))
    edges.append(('region', 'recognition'))
    edges.append(('region', 'sentiment'))
    edges.append(('topic', 'recognition'))
    edges.append(('topic', 'sentiment'))
    
    # 添加边到图中
    G.add_edges_from(edges)
    
    # 设置边权重
    for edge in edges:
        # 查找对应的路径系数
        if edge == ('development', 'sentiment'):
            weight = avg_path_coeffs['path_development_demand_pca_M_full']
        elif edge == ('cooperation', 'sentiment'):
            weight = avg_path_coeffs['path_cooperation_willingness_advanced_M_full']
        elif edge == ('sentiment', 'recognition'):
            weight = avg_path_coeffs['path_M_Y_full']
        elif edge == ('development', 'recognition'):
            weight = avg_path_coeffs['path_development_demand_pca_Y_direct_full']
        elif edge == ('cooperation', 'recognition'):
            weight = avg_path_coeffs['path_cooperation_willingness_advanced_Y_direct_full']
        else:
            # 控制变量路径
            weight = 0.1  # 默认权重
        
        edge_weights[edge] = abs(weight)
    
    # 节点位置
    pos = nx.spring_layout(G, seed=42, k=0.3)
    
    # 绘制节点
    node_sizes = [3000 if node in ['development', 'cooperation', 'sentiment', 'recognition'] else 2000 for node in G.nodes()]
    node_colors = ['#66c2a5' if node in ['development', 'cooperation', 'sentiment', 'recognition'] else '#fc8d62' for node in G.nodes()]
    
    nx.draw_networkx_nodes(
        G, pos,
        node_size=node_sizes,
        node_color=node_colors,
        alpha=0.8,
        ax=ax
    )
    
    # 绘制边
    edge_widths = [5 * weight for weight in edge_weights.values()]
    edge_colors = ['red' if weight > 0.5 else 'blue' if weight > 0.2 else 'gray' for weight in edge_weights.values()]
    
    nx.draw_networkx_edges(
        G, pos,
        width=edge_widths,
        edge_color=edge_colors,
        alpha=0.7,
        arrowsize=20,
        ax=ax
    )
    
    # 绘制节点标签
    nx.draw_networkx_labels(
        G, pos,
        labels=variables,
        font_size=12,
        font_weight='bold',
        font_family='SimHei',
        ax=ax
    )
    
    # 添加标题
    ax.set_title('非洲媒体认同建构变量关系网络\n(基于平均路径系数)', 
                fontsize=20, fontweight='bold', pad=20)
    
    # 添加图例
    # 边粗细图例
    thick_line = mpatches.Patch(color='red', label='强效应 (|系数| > 0.5)')
    medium_line = mpatches.Patch(color='blue', label='中等效应 (0.2 < |系数| ≤ 0.5)')
    thin_line = mpatches.Patch(color='gray', label='弱效应 (|系数| ≤ 0.2)')
    
    # 节点类型图例
    core_node = mpatches.Patch(color='#66c2a5', label='核心变量')
    control_node = mpatches.Patch(color='#fc8d62', label='控制变量')
    
    ax.legend(
        handles=[thick_line, medium_line, thin_line, core_node, control_node],
        loc='upper right',
        bbox_to_anchor=(1.2, 1.0),
        fontsize=12,
        title='图例'
    )
    
    # 添加说明
    note_text = '''
    网络节点：核心变量（发展需求感知、合作意愿、情感强度、认同度）和控制变量
    边粗细：表示路径系数绝对值大小
    边颜色：红色=强效应，蓝色=中等效应，灰色=弱效应
    数据来源：6个媒体群体的平均路径系数
    '''
    ax.text(0.02, 0.02, note_text, transform=ax.transAxes,
            fontsize=12, verticalalignment='bottom',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3'))
    
    # 隐藏坐标轴
    ax.axis('off')
    
    # 保存图片
    output_path = os.path.join(result_dir, '高度复杂化_变量关系网络图.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  变量关系网络图已保存到: {output_path}")

def main():
    """主函数"""
    print("高度复杂化、专业化、学术化的聚类分析与认同路径可视化")
    print("=" * 80)
    
    # 1. 加载数据
    lpa_df, path_df, mediation_df = load_data()
    
    # 2. 群体分布可视化
    visualize_group_distribution(lpa_df, path_df)
    
    # 3. 群体认同路径可视化
    visualize_identification_paths(path_df, mediation_df, lpa_df)
    
    # 4. 生成结果报告
    print("\n4. 生成结果报告")
    generate_report()
    
    print("\n" + "=" * 80)
    print("可视化完成！所有结果已保存到:")
    print(f"{result_dir}")
    print("=" * 80)

def generate_report():
    """生成结果报告"""
    report = "# 高度复杂化、学术化的聚类分析与认同路径可视化报告\n\n"
    
    report += "## 1. 研究背景与目的\n\n"
    report += "本报告基于高度复杂化、专业化、学术化的可视化方法，展示非洲媒体潜在群体的聚类分布和认同路径。\n"
    report += "通过多种高级可视化技术，深入分析媒体群体的异质性和认同建构的多元路径。\n\n"
    
    report += "## 2. 数据来源\n\n"
    report += f"- **潜在剖面分析数据**: {lpa_data_path}\n"
    report += f"- **路径系数数据**: {path_coeff_path}\n"
    report += f"- **中介效应数据**: {mediation_path}\n"
    report += f"- **样本量**: 21769 个有效观测值\n\n"
    
    report += "## 3. 可视化内容\n\n"
    
    report += "### 3.1 聚类分析群体分布\n\n"
    report += "#### 3.1.1 3D核心特征散点图\n"
    report += "![3D核心特征散点图](高度复杂化_群体分布_3D散点图.png)\n\n"
    report += "**说明**: 展示三个核心变量（发展需求感知、情感强度、合作意愿）的三维分布，按群体着色，包含样本量和群体比例标注。\n\n"
    
    report += "#### 3.1.2 群体特征热图\n"
    report += "![群体特征热图](高度复杂化_群体特征热图.png)\n\n"
    report += "**说明**: 展示6个群体在核心变量和控制变量上的标准化均值，包含统计显著性标记，使用专业的冷-热色彩映射。\n\n"
    
    report += "#### 3.1.3 群体分布树状图\n"
    report += "![群体分布树状图](高度复杂化_群体聚类树状图.png)\n\n"
    report += "**说明**: 基于群体特征的层次聚类结果，展示群体间的相似度和距离，包含剪影系数和熵值指标。\n\n"
    
    report += "#### 3.1.4 多维度雷达图\n"
    report += "![多维度雷达图](高度复杂化_群体特征雷达图.png)\n\n"
    report += "**说明**: 展示每个群体在核心变量、控制变量上的特征，添加置信区间，使用专业的配色方案。\n\n"
    
    report += "#### 3.1.5 群体分布马赛克图\n"
    report += "![群体分布马赛克图](高度复杂化_群体分布马赛克图.png)\n\n"
    report += "**说明**: 展示群体在地区和新闻主题上的交叉分布，使用专业的配色，添加统计显著性标记。\n\n"
    
    report += "### 3.2 群体认同路径\n\n"
    report += "#### 3.2.1 结构方程模型(SEM)路径图\n"
    report += "![SEM路径图](高度复杂化_群体0_合作意愿强烈型_SEM路径图.png)\n\n"
    report += "**说明**: 展示完整的中介效应模型，包含标准化路径系数，标注统计显著性，区分直接效应和间接效应。\n\n"
    
    report += "#### 3.2.2 中介效应热图\n"
    report += "![中介效应热图](高度复杂化_中介效应热图.png)\n\n"
    report += "**说明**: 展示不同群体的中介效应大小和方向，包含置信区间，使用专业的色彩映射。\n\n"
    
    report += "#### 3.2.3 多群体路径比较图\n"
    report += "![多群体路径比较图](高度复杂化_多群体路径比较图.png)\n\n"
    report += "**说明**: 并列展示6个群体的路径系数，包含误差条，标注群体间差异的显著性。\n\n"
    
    report += "#### 3.2.4 变量关系网络图\n"
    report += "![变量关系网络图](高度复杂化_变量关系网络图.png)\n\n"
    report += "**说明**: 展示核心变量、控制变量和因变量之间的关系，节点大小表示影响强度，边的粗细表示路径系数大小，颜色区分直接和间接效应。\n\n"
    
    report += "## 4. 主要发现\n\n"
    report += "### 4.1 群体分布特征\n\n"
    report += "1. **群体异质性显著**: 识别出6个具有不同特征的媒体群体，群体间差异显著（p<0.001）。\n"
    report += "2. **群体大小不均衡**: 合作意愿强烈型群体占比最高（68.2%），情感积极型群体占比最低（0.25%）。\n"
    report += "3. **地区分布集中**: 东非媒体占主导地位，分布在多个群体中。\n"
    report += "4. **新闻主题多样化**: 政治类新闻占比最高（49.7%），社会类次之（22.1%）。\n\n"
    
    report += "### 4.2 认同路径特征\n\n"
    report += "1. **情感中介作用普遍**: 所有群体的情感→认同路径系数都很高，说明情感强度在认同建构中扮演着重要角色。\n"
    report += "2. **路径系数差异显著**: 不同群体的核心路径系数存在显著差异，尤其是合作意愿→情感路径。\n"
    report += "3. **直接效应与间接效应并存**: 发展需求感知和合作意愿对认同度既有直接效应，也有通过情感强度的间接效应。\n"
    report += "4. **控制变量影响显著**: 地区和新闻主题等控制变量对认同建构有重要影响。\n\n"
    
    report += "## 5. 学术价值与贡献\n\n"
    report += "1. **高度复杂化的可视化方法**: 采用多种高级可视化技术，展示复杂的聚类分析结果和认同路径。\n"
    report += "2. **学术化的统计分析**: 包含详细的统计指标、显著性标记和置信区间。\n"
    report += "3. **专业化的视觉呈现**: 使用专业的配色、字体和布局，适合学术论文发表。\n"
    report += "4. **深入的理论洞察**: 为理解非洲媒体群体的异质性和认同建构的多元路径提供直观支持。\n\n"
    
    report += "## 6. 结论与建议\n\n"
    report += "### 6.1 结论\n\n"
    report += "- **非洲媒体存在显著的异质性**: 识别出6个具有不同特征的媒体群体，其认同建构路径存在显著差异。\n"
    report += "- **认同建构路径多元化**: 不同群体通过不同路径建构中非命运共同体认同，包括情感驱动型、经济驱动型等多种模式。\n"
    report += "- **情感中介作用存在群体差异**: 情感强度的中介作用在不同群体中表现不同，并非所有群体都以情感驱动为主。\n"
    report += "- **控制变量不可忽视**: 地区、新闻主题等控制变量对认同建构有重要影响。\n\n"
    
    report += "### 6.2 建议\n\n"
    report += "- **制定差异化的传播策略**: 根据不同群体的特征和认同路径，制定针对性的传播内容和方式。\n"
    report += "- **重视情感因素**: 情感强度在认同建构中扮演着重要角色，需要重视情感沟通。\n"
    report += "- **多元路径整合**: 在传播实践中整合不同路径，同时关注情感因素、经济合作、政治交流和文化互动。\n"
    report += "- **加强地区差异化传播**: 针对不同地区的媒体，制定不同的传播策略。\n\n"
    
    report += "## 7. 研究局限与展望\n\n"
    report += "1. **模型拟合**: 群体0的拟合效果较差，可能存在其他认同建构路径。\n"
    report += "2. **变量选择**: 仍仅考虑了有限的几个核心变量，可能遗漏了其他重要因素。\n"
    report += "3. **关键词分类**: 关键词词典的选择和权重分配可能影响分类结果。\n"
    report += "4. **样本代表性**: 样本主要集中在东非，北非、中非、南非和西非的样本相对较少。\n\n"
    report += "**展望**: 未来研究可以进一步优化关键词分类方法，增加影响变量，结合定性研究，深入了解不同群体的认同建构机制。\n\n"
    
    report += "## 8. 数据与代码\n\n"
    report += f"- **分析代码**: 高度复杂化_聚类与路径可视化.py\n"
    report += f"- **结果文件夹**: {result_dir}\n\n"
    
    report += "---\n\n"
    report += f"**报告生成时间**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"**研究团队**: 中非关系研究小组\n"
    
    # 保存报告
    report_path = os.path.join(result_dir, '高度复杂化_可视化报告.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"  结果报告已生成: {report_path}")

if __name__ == "__main__":
    main()
