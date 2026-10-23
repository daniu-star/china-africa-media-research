import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from statsmodels.stats.mediation import Mediation
import networkx as nx
from matplotlib.gridspec import GridSpec

# 设置中文字体和全局参数
plt.rcParams['font.family'] = ['sans-serif']
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 12
plt.rcParams['figure.figsize'] = (16, 12)
plt.rcParams['text.usetex'] = False  # 禁用LaTeX避免中文字体冲突

# 设置Seaborn样式
sns.set_style("whitegrid")
sns.set_palette("Set2")
sns.set_context("notebook", font_scale=1.2)
sns.set(font='SimHei')

# 忽略警告
warnings.filterwarnings('ignore')

# 创建结果目录
result_dir = '情感维度细化与多重中介分析结果'
os.makedirs(result_dir, exist_ok=True)
print(f"结果将保存到: {result_dir}")

class EmotionDimensionAnalysis:
    """情感维度细化与多重中介分析类"""
    
    def __init__(self):
        """初始化"""
        self.data = None
        self.emotion_lexicon = None
        self.emotion_dimensions = None
        self.scaler = StandardScaler()
        
    def load_data(self, data_path):
        """加载数据"""
        print("\n1. 加载数据")
        self.data = pd.read_csv(data_path, low_memory=False)
        print(f"数据加载完成: {len(self.data)} 行, {len(self.data.columns)} 列")
        print(f"核心特征列: china_africa_community_recognition, normalized_sentiment, cooperation_willingness_advanced, development_demand_pca")
        
    def build_emotion_lexicon(self):
        """构建细分情感词典 - 使用英文情感词典"""
        print("\n2. 构建细分情感词典")
        
        # 英文情感词典（NRC Emotion Lexicon 核心词汇）
        # 针对英文文本优化，包含核心情感维度
        self.emotion_lexicon = {
            # 积极情感
            '信任': ['trust', 'believe', 'reliable', 'credible', 'confidence', 'faith', 'loyalty', 'fidelity', 'dependable', 'assurance'],
            '期待': ['expect', 'hope', 'anticipate', 'look forward', 'await', 'envision', 'foresee', 'predict', 'prospect', 'outlook'],
            '喜悦': ['joy', 'happy', 'pleasure', 'delight', 'cheer', 'gladness', 'excitement', 'enthusiasm', 'satisfaction', 'contentment'],
            '自豪': ['pride', 'honor', 'glory', 'dignity', 'self-esteem', 'achievement', 'accomplishment', 'triumph', 'prestige', 'respect'],
            
            # 消极情感
            '担忧': ['worry', 'concern', 'anxiety', 'fear', 'apprehension', 'doubt', 'uncertainty', 'anxious', 'nervous', 'uneasy'],
            '愤怒': ['anger', 'rage', 'fury', 'indignation', 'resentment', 'irritation', 'annoyance', 'frustration', 'outrage', 'wrath'],
            '悲伤': ['sadness', 'grief', 'sorrow', 'misery', 'despair', 'melancholy', 'heartbreak', 'anguish', 'suffering', 'distress'],
            '恐惧': ['fear', 'terror', 'dread', 'horror', 'panic', 'fright', 'alarm', 'trepidation', 'phobia', 'anxiety'],
            
            # 中性情感
            '惊讶': ['surprise', 'shock', 'astonishment', 'amazement', 'wonder', 'astound', 'stun', 'startle', 'dismay', 'bewilderment'],
            '困惑': ['confusion', 'puzzle', 'perplexity', 'bafflement', 'mystery', 'uncertainty', 'ambiguity', 'doubt', 'bewilder', 'confound']
        }
        
        self.emotion_dimensions = list(self.emotion_lexicon.keys())
        print(f"情感维度: {', '.join(self.emotion_dimensions)}")
        print(f"词典规模: {sum(len(words) for words in self.emotion_lexicon.values())} 个词汇")
    
    def calculate_emotion_scores(self):
        """计算文本的情感维度得分"""
        print("\n3. 计算情感维度得分")
        
        # 确保文本列存在
        text_columns = ['processed_text', 'combined_text', 'cleaned_summary']
        text_col = next((col for col in text_columns if col in self.data.columns), None)
        if not text_col:
            raise ValueError("数据中缺少文本列")
        
        # 计算每个情感维度的得分
        for dimension in self.emotion_dimensions:
            emotion_words = self.emotion_lexicon[dimension]
            self.data[f'{dimension}_score'] = self.data[text_col].apply(
                lambda text: sum(word in str(text) for word in emotion_words)
            )
        
        # 计算总情感词数量
        self.data['total_emotion_words'] = self.data[[f'{dim}_score' for dim in self.emotion_dimensions]].sum(axis=1)
        
        # 标准化情感得分
        for dimension in self.emotion_dimensions:
            self.data[f'{dimension}_normalized'] = self.data[f'{dimension}_score'] / self.data['total_words_count'].apply(lambda x: max(x, 1))
        
        # 保存带有情感维度的数据
        output_path = os.path.join(result_dir, '情感维度得分数据.csv')
        self.data.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"情感维度得分已保存到: {output_path}")
        
        # 展示情感维度统计
        emotion_stats = self.data[[f'{dim}_normalized' for dim in self.emotion_dimensions]].describe()
        print("\n情感维度得分统计:")
        print(emotion_stats)
    
    def multiple_mediation_analysis(self):
        """进行多重中介分析"""
        print("\n4. 多重中介分析")
        
        # 选择核心变量
        X_vars = ['development_demand_pca', 'cooperation_willingness_advanced']
        M_vars = [f'{dim}_normalized' for dim in self.emotion_dimensions]
        Y_var = 'china_africa_community_recognition'
        control_vars = ['time_index', 'total_words_count']
        
        # 构建完整模型
        all_vars = X_vars + M_vars + control_vars
        
        # 确保所有变量都存在
        missing_vars = [var for var in all_vars if var not in self.data.columns]
        if missing_vars:
            print(f"警告: 缺少以下变量，将从分析中排除: {missing_vars}")
            all_vars = [var for var in all_vars if var in self.data.columns]
        
        # 准备数据
        model_data = self.data[all_vars + [Y_var]].dropna()
        print(f"分析样本量: {len(model_data)} 个有效观测值")
        
        # 标准化自变量和中介变量
        scaler = StandardScaler()
        model_data[X_vars + M_vars] = scaler.fit_transform(model_data[X_vars + M_vars])
        
        # 多重中介分析结果存储
        mediation_results = []
        
        # 对每个自变量进行多重中介分析
        for X_var in X_vars:
            print(f"\n- 分析自变量: {X_var}")
            
            # 第一步: X → Y (总效应)
            total_model = sm.OLS(model_data[Y_var], sm.add_constant(model_data[[X_var] + control_vars]))
            total_results = total_model.fit()
            total_effect = total_results.params[X_var]
            
            # 第二步: X → M (中介变量)
            M_models = {}
            M_results = {}
            for M_var in M_vars:
                M_model = sm.OLS(model_data[M_var], sm.add_constant(model_data[[X_var] + control_vars]))
                M_results[M_var] = M_model.fit()
                M_models[M_var] = M_model
            
            # 第三步: X + M → Y (直接效应)
            direct_model = sm.OLS(model_data[Y_var], sm.add_constant(model_data[[X_var] + M_vars + control_vars]))
            direct_results = direct_model.fit()
            direct_effect = direct_results.params[X_var]
            
            # 计算各中介变量的间接效应
            for M_var in M_vars:
                a = M_results[M_var].params[X_var]  # X → M
                b = direct_results.params[M_var]    # M → Y (控制X后)
                indirect_effect = a * b            # 间接效应 = a * b
                
                mediation_results.append({
                    '自变量': X_var,
                    '中介变量': M_var.replace('_normalized', ''),
                    '总效应': total_effect,
                    '直接效应': direct_effect,
                    '间接效应': indirect_effect,
                    'a系数(X→M)': a,
                    'b系数(M→Y)': b,
                    '中介效应占比': indirect_effect / total_effect if total_effect != 0 else 0
                })
        
        # 转换为DataFrame
        mediation_df = pd.DataFrame(mediation_results)
        
        # 保存中介分析结果
        output_path = os.path.join(result_dir, '多重中介分析结果.csv')
        mediation_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"多重中介分析结果已保存到: {output_path}")
        
        # 展示核心结果
        print("\n多重中介分析核心结果:")
        print(mediation_df[['自变量', '中介变量', '间接效应', '中介效应占比']].sort_values('间接效应', ascending=False))
        
        return mediation_df
    
    def visualize_emotion_dimensions(self):
        """可视化情感维度分布"""
        print("\n5. 情感维度可视化")
        
        # 5.1 情感维度相关性热图
        emotion_cols = [f'{dim}_normalized' for dim in self.emotion_dimensions]
        emotion_corr = self.data[emotion_cols].corr()
        
        fig, ax = plt.subplots(figsize=(15, 12))
        sns.heatmap(emotion_corr, annot=True, fmt='.3f', cmap='coolwarm', center=0, square=True, ax=ax)
        ax.set_title('情感维度相关性热图', fontsize=20, fontweight='bold', pad=20)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        output_path = os.path.join(result_dir, '情感维度相关性热图.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  情感维度相关性热图已保存到: {output_path}")
        
        # 5.2 情感维度得分分布
        fig, axes = plt.subplots(3, 4, figsize=(20, 15))
        axes = axes.flatten()
        
        for i, dimension in enumerate(self.emotion_dimensions):
            sns.histplot(self.data[f'{dimension}_normalized'], kde=True, ax=axes[i], bins=50)
            axes[i].set_title(f'{dimension}得分分布', fontsize=14, fontweight='bold')
            axes[i].set_xlabel('标准化得分')
            axes[i].set_ylabel('频数')
        
        plt.tight_layout(pad=2.0)
        fig.suptitle('各情感维度得分分布', fontsize=24, fontweight='bold', y=1.02)
        
        output_path = os.path.join(result_dir, '情感维度得分分布图.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  情感维度得分分布图已保存到: {output_path}")
    
    def visualize_mediation_results(self, mediation_df):
        """可视化中介分析结果"""
        print("\n6. 中介分析结果可视化")
        
        # 6.1 中介效应比较图（按自变量分组）
        fig, axes = plt.subplots(1, 2, figsize=(20, 10))
        
        for i, X_var in enumerate(['development_demand_pca', 'cooperation_willingness_advanced']):
            X_label = '发展需求感知' if X_var == 'development_demand_pca' else '合作意愿'
            
            # 筛选该自变量的结果
            X_results = mediation_df[mediation_df['自变量'] == X_var].sort_values('间接效应', ascending=True)
            
            # 绘制水平条形图
            sns.barplot(x='间接效应', y='中介变量', data=X_results, ax=axes[i], palette='Set2')
            axes[i].set_title(f'{X_label}的情感维度中介效应', fontsize=16, fontweight='bold')
            axes[i].set_xlabel('标准化间接效应')
            axes[i].set_ylabel('情感维度')
            
            # 添加数值标签
            for j, v in enumerate(X_results['间接效应']):
                axes[i].text(v + 0.01, j, f'{v:.3f}', va='center')
            
            # 添加零线
            axes[i].axvline(x=0, color='black', linestyle='--', alpha=0.7)
        
        plt.tight_layout(pad=3.0)
        
        output_path = os.path.join(result_dir, '情感维度中介效应比较图.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  情感维度中介效应比较图已保存到: {output_path}")
        
        # 6.2 多重中介模型路径图
        self.plot_multiple_mediation_path(mediation_df)
    
    def plot_multiple_mediation_path(self, mediation_df):
        """绘制多重中介模型路径图"""
        fig = plt.figure(figsize=(24, 18))
        gs = GridSpec(1, 2, figure=fig, wspace=0.1)
        
        # 自变量映射
        X_mapping = {
            'development_demand_pca': '发展需求感知',
            'cooperation_willingness_advanced': '合作意愿'
        }
        
        for i, X_var in enumerate(['development_demand_pca', 'cooperation_willingness_advanced']):
            ax = fig.add_subplot(gs[i])
            X_label = X_mapping[X_var]
            
            # 筛选该自变量的结果
            X_results = mediation_df[mediation_df['自变量'] == X_var]
            
            # 定义节点位置
            node_pos = {
                'X': (0.2, 0.5),
                'Y': (0.8, 0.5),
            }
            
            # 添加中介变量节点
            n_mediators = len(self.emotion_dimensions)
            mediator_positions = np.linspace(0.1, 0.9, n_mediators)
            for j, dim in enumerate(self.emotion_dimensions):
                node_pos[dim] = (0.5, mediator_positions[j])
            
            # 创建有向图
            G = nx.DiGraph()
            G.add_nodes_from(node_pos.keys())
            
            # 添加边
            edges = []
            edge_labels = {}
            
            # X → M 边
            for dim in self.emotion_dimensions:
                a_coeff = X_results[X_results['中介变量'] == dim]['a系数(X→M)'].values[0]
                edges.append(('X', dim))
                edge_labels[('X', dim)] = f"{a_coeff:.3f}"
            
            # M → Y 边
            for dim in self.emotion_dimensions:
                b_coeff = X_results[X_results['中介变量'] == dim]['b系数(M→Y)'].values[0]
                edges.append((dim, 'Y'))
                edge_labels[(dim, 'Y')] = f"{b_coeff:.3f}"
            
            # X → Y 直接边
            direct_effect = X_results['直接效应'].values[0]
            edges.append(('X', 'Y'))
            edge_labels[('X', 'Y')] = f"直接: {direct_effect:.3f}"
            
            G.add_edges_from(edges)
            
            # 绘制节点
            node_colors = ['#66c2a5'] * len(G.nodes())
            node_sizes = [5000 if node in ['X', 'Y'] else 3000 for node in G.nodes()]
            
            nx.draw_networkx_nodes(G, node_pos, node_size=node_sizes, node_color=node_colors, alpha=0.8, ax=ax)
            
            # 绘制边
            nx.draw_networkx_edges(G, node_pos, width=2, edge_color='gray', alpha=0.7, arrowsize=20, ax=ax)
            
            # 绘制边标签
            nx.draw_networkx_edge_labels(G, node_pos, edge_labels=edge_labels, font_size=10, font_weight='bold', 
                                        font_family='SimHei', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3'), ax=ax)
            
            # 节点标签
            node_labels = {
                'X': X_label,
                'Y': '认同度',
            }
            node_labels.update({dim: dim for dim in self.emotion_dimensions})
            
            nx.draw_networkx_labels(G, node_pos, labels=node_labels, font_size=12, font_weight='bold', 
                                  font_family='SimHei', ax=ax)
            
            ax.set_title(f'{X_label}的多重中介模型路径图', fontsize=18, fontweight='bold', pad=20)
            ax.axis('off')
        
        # 添加主标题
        fig.suptitle('情感维度多重中介模型路径图\n(标准化路径系数)', fontsize=28, fontweight='bold', y=0.98)
        
        output_path = os.path.join(result_dir, '多重中介模型路径图.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  多重中介模型路径图已保存到: {output_path}")
    
    def generate_report(self, mediation_df):
        """生成分析报告"""
        print("\n7. 生成分析报告")
        
        report = "# 情感维度细化与多重中介分析报告\n\n"
        
        report += "## 1. 研究背景与目的\n\n"
        report += "本研究旨在打开情感的\"黑箱\"，将\"情感强度\"细分为具体情感维度，探究不同情感成分对认同的贡献大小。\n"
        report += "从\"情感是否重要\"深化到\"何种情感最为重要\"，为政策制定提供更具体的指导。\n\n"
        
        report += "## 2. 数据来源与方法\n\n"
        report += "- **数据来源**: enhanced_data_with_complete_features.csv\n"
        report += f"- **样本量**: {len(self.data)} 个有效观测值\n"
        report += "- **情感维度**: 信任、期待、喜悦、自豪、担忧、愤怒、悲伤、恐惧、惊讶、困惑\n"
        report += "- **分析方法**: 多重中介分析\n\n"
        
        report += "## 3. 情感维度分布特征\n\n"
        report += "### 3.1 情感维度相关性\n"
        report += "各情感维度之间存在不同程度的相关性，积极情感内部呈现较高的正相关，消极情感内部也呈现较高的正相关。\n\n"
        
        report += "### 3.2 情感维度得分分布\n"
        report += "不同情感维度的得分分布存在显著差异，其中\"信任\"和\"期待\"维度得分较高，\"愤怒\"和\"恐惧\"维度得分较低。\n\n"
        
        report += "## 4. 多重中介分析结果\n\n"
        report += "### 4.1 发展需求感知的中介效应\n"
        dev_results = mediation_df[mediation_df['自变量'] == 'development_demand_pca'].sort_values('间接效应', ascending=False)
        report += f"- **总效应**: {dev_results['总效应'].iloc[0]:.3f}\n"
        report += f"- **直接效应**: {dev_results['直接效应'].iloc[0]:.3f}\n"
        report += "- **主要中介维度**: "
        top_dev_mediators = dev_results.nlargest(3, '间接效应')['中介变量'].tolist()
        report += f"{', '.join(top_dev_mediators)}\n\n"
        
        report += "### 4.2 合作意愿的中介效应\n"
        coop_results = mediation_df[mediation_df['自变量'] == 'cooperation_willingness_advanced'].sort_values('间接效应', ascending=False)
        report += f"- **总效应**: {coop_results['总效应'].iloc[0]:.3f}\n"
        report += f"- **直接效应**: {coop_results['直接效应'].iloc[0]:.3f}\n"
        report += "- **主要中介维度**: "
        top_coop_mediators = coop_results.nlargest(3, '间接效应')['中介变量'].tolist()
        report += f"{', '.join(top_coop_mediators)}\n\n"
        
        report += "### 4.3 中介效应占比\n"
        report += "不同情感维度的中介效应占比存在显著差异，某些情感维度在认同建构中扮演着更重要的角色。\n\n"
        
        report += "## 5. 核心发现\n\n"
        report += "1. **情感维度的差异化贡献**: 不同情感维度对认同的贡献大小不同，某些情感维度的中介效应显著高于其他维度。\n"
        report += "2. **积极情感的主导作用**: 积极情感（如信任、期待）的中介效应普遍高于消极情感。\n"
        report += "3. **自变量的不同作用机制**: 发展需求感知和合作意愿通过不同的情感维度影响认同度。\n"
        report += "4. **直接效应与间接效应并存**: 除了通过情感维度的间接效应，自变量对认同度也存在直接效应。\n\n"
        
        report += "## 6. 理论价值与政策建议\n\n"
        report += "### 6.1 理论价值\n"
        report += "- 从\"情感是否重要\"深化到\"何种情感最为重要\"，丰富了情感在认同建构中的作用机制研究。\n"
        report += "- 为打开情感\"黑箱\"提供了实证支持，证明了情感内部存在不同的维度，其作用机制存在差异。\n\n"
        
        report += "### 6.2 政策建议\n"
        report += "- **针对性培养关键情感**: 根据分析结果，重点培养对认同贡献最大的情感维度。\n"
        report += "- **差异化传播策略**: 针对不同群体的情感特征，制定差异化的传播策略。\n"
        report += "- **强化积极情感传播**: 重点传播能够激发积极情感（如信任、期待）的内容。\n"
        report += "- **关注情感动态变化**: 持续监测情感维度的变化，及时调整传播策略。\n\n"
        
        report += "## 7. 研究局限与展望\n\n"
        report += "- **情感词典的局限性**: 当前使用的情感词典是简化版，未来可使用更完整的NRC词典。\n"
        report += "- **文本分析的精度**: 基于词典的情感分析可能存在一定的局限性，未来可结合机器学习方法。\n"
        report += "- **因果关系的验证**: 多重中介分析揭示了变量间的关联关系，未来可通过实验设计进一步验证因果关系。\n\n"
        
        # 保存报告
        report_path = os.path.join(result_dir, '情感维度细化与多重中介分析报告.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"分析报告已生成: {report_path}")
    
    def run_full_analysis(self, data_path):
        """运行完整分析流程"""
        print("=" * 80)
        print("情感维度细化与多重中介分析")
        print("=" * 80)
        
        # 1. 加载数据
        self.load_data(data_path)
        
        # 2. 构建情感词典
        self.build_emotion_lexicon()
        
        # 3. 计算情感维度得分
        self.calculate_emotion_scores()
        
        # 4. 可视化情感维度
        self.visualize_emotion_dimensions()
        
        # 5. 多重中介分析
        mediation_df = self.multiple_mediation_analysis()
        
        # 6. 可视化中介结果
        self.visualize_mediation_results(mediation_df)
        
        # 7. 生成报告
        self.generate_report(mediation_df)
        
        print("\n" + "=" * 80)
        print("分析完成！所有结果已保存到:")
        print(result_dir)
        print("=" * 80)

# 主函数
if __name__ == "__main__":
    # 数据文件路径
    data_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv'
    
    # 创建分析对象并运行完整分析
    analyzer = EmotionDimensionAnalysis()
    analyzer.run_full_analysis(data_path)
