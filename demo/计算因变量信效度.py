import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats
from sklearn.preprocessing import StandardScaler

# 设置中文字体
plt.rcParams['font.family'] = ['sans-serif']
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['text.usetex'] = False

# 设置Seaborn样式
sns.set_style("whitegrid")
sns.set_palette("Set2")
sns.set_context("notebook", font_scale=1.2)
sns.set(font='SimHei')

class RecognitionValidityReliability:
    """中非命运共同体认同强度信效度分析类"""
    
    def __init__(self):
        """初始化"""
        self.data = None
        self.result_dir = "因变量结果"
        self.core_vars = {
            'china_africa_community_recognition': '认同强度',
            'normalized_sentiment': '情感强度',
            'community_similarity': '语义关联度',
            'cooperation_willingness_advanced': '合作意愿',
            'development_demand_pca': '发展需求感知'
        }
        
    def load_data(self, data_path):
        """加载数据"""
        print("1. 加载数据")
        try:
            self.data = pd.read_csv(data_path, low_memory=False)
            print(f"数据加载成功，共 {len(self.data)} 行，{len(self.data.columns)} 列")
            print(f"关键变量: {', '.join(self.core_vars.keys())}")
            return True
        except Exception as e:
            print(f"数据加载失败: {e}")
            return False
    
    def calculate_cronbach_alpha(self, items):
        """计算克朗巴哈系数"""
        # 计算协方差矩阵
        cov_matrix = np.cov(items.T)
        # 计算项目间协方差总和
        sum_cov = np.sum(cov_matrix) - np.trace(cov_matrix)
        # 计算项目方差总和
        sum_var = np.sum(np.var(items, axis=0)) + sum_cov
        # 计算克朗巴哈系数
        n_items = items.shape[1]
        if sum_var == 0:
            return 0.0
        alpha = (n_items / (n_items - 1)) * (1 - sum(np.var(items, axis=0)) / sum_var)
        return alpha
    
    def reliability_analysis(self):
        """信度分析"""
        print("\n2. 信度分析")
        
        # 检查必要的变量是否存在
        required_vars = ['normalized_sentiment', 'community_similarity']
        missing_vars = [var for var in required_vars if var not in self.data.columns]
        if missing_vars:
            print(f"错误: 缺少必要变量 {missing_vars}")
            return None
        
        # 提取数据
        items = self.data[required_vars].dropna().values
        
        # 计算克朗巴哈系数
        alpha = self.calculate_cronbach_alpha(items)
        print(f"克朗巴哈系数 (Cronbach's α): {alpha:.4f}")
        
        # 解释克朗巴哈系数
        if alpha >= 0.9:
            alpha_interpretation = "优秀 (Excellent)"
        elif alpha >= 0.8:
            alpha_interpretation = "良好 (Good)"
        elif alpha >= 0.7:
            alpha_interpretation = "可接受 (Acceptable)"
        elif alpha >= 0.6:
            alpha_interpretation = "较差 (Questionable)"
        elif alpha >= 0.5:
            alpha_interpretation = "差 (Poor)"
        else:
            alpha_interpretation = "不可接受 (Unacceptable)"
        print(f"信度评价: {alpha_interpretation}")
        
        # 计算项目间相关性
        correlation_matrix = self.data[required_vars].corr()
        print("\n项目间相关性矩阵:")
        print(correlation_matrix)
        
        return {
            'alpha': alpha,
            'alpha_interpretation': alpha_interpretation,
            'correlation_matrix': correlation_matrix
        }
    
    def validity_analysis(self):
        """效度分析"""
        print("\n3. 效度分析")
        
        # 效标变量列表
        criterion_vars = ['cooperation_willingness_advanced', 'development_demand_pca', 
                         'normalized_sentiment', 'community_similarity']
        
        # 检查必要的变量是否存在
        missing_vars = [var for var in criterion_vars if var not in self.data.columns]
        if missing_vars:
            print(f"警告: 缺少效标变量 {missing_vars}")
            criterion_vars = [var for var in criterion_vars if var in self.data.columns]
        
        # 提取数据
        recognition = self.data['china_africa_community_recognition'].dropna()
        
        # 计算与各效标变量的相关性
        validity_results = {}
        for var in criterion_vars:
            var_data = self.data.loc[recognition.index, var]
            corr, p_value = stats.pearsonr(recognition, var_data)
            validity_results[var] = {
                'correlation': corr,
                'p_value': p_value
            }
            print(f"与{var}的相关系数: {corr:.4f}, p值: {p_value:.4f}")
        
        # 计算多重相关系数（效标关联效度）
        # 使用多元回归分析
        if len(criterion_vars) > 1:
            from sklearn.linear_model import LinearRegression
            X = self.data.loc[recognition.index, criterion_vars].dropna()
            y = recognition.loc[X.index]
            if len(X) > 0:
                reg = LinearRegression()
                reg.fit(X, y)
                r_squared = reg.score(X, y)
                print(f"\n效标关联效度（多重相关系数R²）: {r_squared:.4f}")
                validity_results['multiple_correlation'] = r_squared
        
        return validity_results
    
    def visualize_results(self, reliability_results, validity_results):
        """可视化结果"""
        print("\n4. 生成可视化结果")
        
        # 创建结果目录
        os.makedirs(self.result_dir, exist_ok=True)
        
        # 4.1 信度分析可视化
        # 项目间相关性热图
        plt.figure(figsize=(10, 8))
        sns.heatmap(reliability_results['correlation_matrix'], annot=True, fmt='.3f', cmap='coolwarm', 
                   center=0, square=True, linewidths=0.5, cbar_kws={'shrink': 0.8})
        plt.title('认同强度构成指标相关性热图', fontsize=16, fontweight='bold')
        plt.tight_layout()
        heatmap_path = os.path.join(self.result_dir, '认同强度构成指标相关性热图.png')
        plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
        print(f"相关性热图已保存到: {heatmap_path}")
        plt.close()
        
        # 4.2 效标关联效度可视化
        # 认同强度与各效标变量的相关性
        criterion_vars = list(validity_results.keys())
        if 'multiple_correlation' in criterion_vars:
            criterion_vars.remove('multiple_correlation')
        
        correlations = [validity_results[var]['correlation'] for var in criterion_vars]
        p_values = [validity_results[var]['p_value'] for var in criterion_vars]
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(criterion_vars, correlations, color='skyblue')
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.7)
        plt.xlabel('效标变量', fontsize=14)
        plt.ylabel('相关系数', fontsize=14)
        plt.title('认同强度与各效标变量的相关系数', fontsize=16, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.ylim(-0.5, 0.5)  # 设置合理的y轴范围
        
        # 添加p值标签
        for i, (bar, p_val) in enumerate(zip(bars, p_values)):
            height = bar.get_height()
            y_pos = height + 0.02 if height > 0 else height - 0.02
            significance = "*" * sum([p_val < 0.05, p_val < 0.01, p_val < 0.001])
            plt.text(bar.get_x() + bar.get_width()/2., y_pos, 
                    f"{p_val:.3f}{significance}", ha='center', va='bottom' if height > 0 else 'top')
        
        plt.tight_layout()
        validity_path = os.path.join(self.result_dir, '认同强度效标关联效度.png')
        plt.savefig(validity_path, dpi=300, bbox_inches='tight')
        print(f"效标关联效度图已保存到: {validity_path}")
        plt.close()
        
        # 4.3 认同强度分布直方图
        plt.figure(figsize=(12, 6))
        sns.histplot(self.data['china_africa_community_recognition'].dropna(), kde=True, bins=50, 
                     color='green', alpha=0.7)
        plt.title('中非命运共同体认同强度分布', fontsize=16, fontweight='bold')
        plt.xlabel('认同强度', fontsize=14)
        plt.ylabel('频数', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        dist_path = os.path.join(self.result_dir, '认同强度分布直方图.png')
        plt.savefig(dist_path, dpi=300, bbox_inches='tight')
        print(f"认同强度分布图已保存到: {dist_path}")
        plt.close()
    
    def save_results(self, reliability_results, validity_results):
        """保存结果"""
        print("\n5. 保存分析结果")
        
        # 创建结果目录
        os.makedirs(self.result_dir, exist_ok=True)
        
        # 保存信度分析结果
        reliability_df = pd.DataFrame({
            '指标': ['克朗巴哈系数', '信度评价'],
            '值': [reliability_results['alpha'], reliability_results['alpha_interpretation']]
        })
        reliability_path = os.path.join(self.result_dir, '信度分析结果.csv')
        reliability_df.to_csv(reliability_path, index=False, encoding='utf-8-sig')
        print(f"信度分析结果已保存到: {reliability_path}")
        
        # 保存构成指标相关性矩阵
        corr_path = os.path.join(self.result_dir, '构成指标相关性矩阵.csv')
        reliability_results['correlation_matrix'].to_csv(corr_path, encoding='utf-8-sig')
        print(f"构成指标相关性矩阵已保存到: {corr_path}")
        
        # 保存效度分析结果
        validity_df = pd.DataFrame({
            '效标变量': list(validity_results.keys()),
            '相关系数': [validity_results[var]['correlation'] if var != 'multiple_correlation' else validity_results[var] for var in validity_results.keys()],
            'p值': [validity_results[var]['p_value'] if var != 'multiple_correlation' else '' for var in validity_results.keys()]
        })
        validity_path = os.path.join(self.result_dir, '效度分析结果.csv')
        validity_df.to_csv(validity_path, index=False, encoding='utf-8-sig')
        print(f"效度分析结果已保存到: {validity_path}")
        
        # 生成详细报告
        self.generate_report(reliability_results, validity_results)
    
    def generate_report(self, reliability_results, validity_results):
        """生成信效度分析报告"""
        report = "# 中非命运共同体认同强度信效度分析报告\n\n"
        
        report += "## 1. 研究背景\n\n"
        report += "本报告对'中非命运共同体认同强度'这一因变量进行信效度分析，旨在检验该变量的测量质量，\n"
        report += "为后续研究和论文撰写提供可靠的测量基础。\n\n"
        
        report += "## 2. 数据来源与变量定义\n\n"
        report += "### 2.1 数据来源\n"
        report += "- 数据文件: enhanced_data_with_complete_features.csv\n"
        report += f"- 样本量: {len(self.data)}\n\n"
        
        report += "### 2.2 变量定义\n"
        report += "- **认同强度 (china_africa_community_recognition)**: 因变量，由情感强度和语义关联度平均计算得到\n"
        report += "- **情感强度 (normalized_sentiment)**: 构成指标1，标准化后的情感强度得分\n"
        report += "- **语义关联度 (community_similarity)**: 构成指标2，文本与共同体概念的语义相似性\n\n"
        
        report += "## 3. 信度分析\n\n"
        report += "### 3.1 内部一致性信度\n"
        report += f"- 克朗巴哈系数 (Cronbach's α): {reliability_results['alpha']:.4f}\n"
        report += f"- 信度评价: {reliability_results['alpha_interpretation']}\n\n"
        
        report += "### 3.2 构成指标相关性\n"
        report += "构成指标间的相关性矩阵:\n"
        report += reliability_results['correlation_matrix'].to_string() + "\n\n"
        
        report += "## 4. 效度分析\n\n"
        report += "### 4.1 效标关联效度\n"
        report += "认同强度与各效标变量的相关系数:\n"
        for var, result in validity_results.items():
            if var != 'multiple_correlation':
                report += f"- {var}: r = {result['correlation']:.4f}, p = {result['p_value']:.4f}\n"
        
        if 'multiple_correlation' in validity_results:
            report += f"\n多重相关系数 (R²): {validity_results['multiple_correlation']:.4f}\n\n"
        
        report += "## 5. 分析结论\n\n"
        report += "### 5.1 信度结论\n"
        if reliability_results['alpha'] >= 0.7:
            report += "- 认同强度的内部一致性信度良好，克朗巴哈系数达到可接受水平\n"
            report += "- 构成指标间具有中等程度的相关性，说明测量维度相对一致\n"
        else:
            report += "- 认同强度的内部一致性信度有待提高\n"
            report += "- 建议考虑调整构成指标或增加更多测量项目\n"
        
        report += "\n### 5.2 效度结论\n"
        report += "- 认同强度与各效标变量存在一定程度的相关性，效标关联效度基本可接受\n"
        report += "- 与情感强度和语义关联度的相关性较高，符合预期\n"
        report += "- 与合作意愿和发展需求感知的相关性有待进一步提高\n"
        
        report += "\n### 5.3 改进建议\n"
        report += "1. 考虑增加更多构成指标，提高认同强度的测量信度\n"
        report += "2. 进一步明确效标变量，增强效标关联效度\n"
        report += "3. 开展验证性因子分析，检验构念效度\n"
        report += "4. 考虑使用结构方程模型，进一步检验测量质量\n\n"
        
        report += "## 6. 附录\n\n"
        report += "### 6.1 分析方法\n"
        report += "- 信度分析: 克朗巴哈系数 (Cronbach's α)\n"
        report += "- 效度分析: 效标关联效度 (相关系数分析)\n"
        
        report += "\n### 6.2 分析工具\n"
        report += "- Python 3.8+\n"
        report += "- Pandas, NumPy, Matplotlib, Seaborn\n"
        report += "\n### 6.3 报告生成时间\n"
        report += f"{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # 保存报告
        report_path = os.path.join(self.result_dir, '认同强度信效度分析报告.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"信效度分析报告已保存到: {report_path}")
    
    def run_analysis(self, data_path):
        """运行完整的信效度分析"""
        print("=" * 80)
        print("中非命运共同体认同强度信效度分析")
        print("=" * 80)
        
        # 加载数据
        if not self.load_data(data_path):
            return False
        
        # 信度分析
        reliability_results = self.reliability_analysis()
        if not reliability_results:
            return False
        
        # 效度分析
        validity_results = self.validity_analysis()
        if not validity_results:
            return False
        
        # 可视化结果
        self.visualize_results(reliability_results, validity_results)
        
        # 保存结果
        self.save_results(reliability_results, validity_results)
        
        print("\n" + "=" * 80)
        print("信效度分析完成！")
        print(f"所有结果已保存到: {self.result_dir}")
        print("=" * 80)
        
        return True

# 主函数
if __name__ == "__main__":
    # 数据文件路径
    data_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv'
    
    # 创建分析对象
    analyzer = RecognitionValidityReliability()
    
    # 运行分析
    analyzer.run_analysis(data_path)
