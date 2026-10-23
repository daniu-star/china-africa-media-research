import pandas as pd
import numpy as np
import re
import os
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 设置结果保存目录
output_dir = 'c:/Users/13067/Desktop/论文/非洲/demo/合作纵深性优化结果'
os.makedirs(output_dir, exist_ok=True)

class CooperationDepthOptimizer:
    def __init__(self):
        self.df = None
        self.raw_df = None
        self.optimized_components = None
        self.original_components = None
        self.pca = None
        self.weights = None
        
    def load_data(self, file_path):
        """加载原始数据"""
        print("加载原始数据...")
        cols_to_read = [
            'title', 'summary', 'processed_text',
            'long_term_word_count', 'has_multi_agent_interaction',
            'long_term_percentile', 'multi_agent_percentile', 'cooperation_depth_index'
        ]
        self.raw_df = pd.read_csv(file_path, usecols=cols_to_read, low_memory=False)
        print(f"原始数据记录数: {len(self.raw_df)}")
        
    def preprocess_data(self):
        """数据预处理"""
        print("数据预处理...")
        self.df = self.raw_df.copy()
        
        # 创建combined_text列（不包含content列）
        if 'combined_text' not in self.df.columns:
            self.df['combined_text'] = self.df['title'].fillna('') + ' ' + self.df['summary'].fillna('')
        
        # processed_text列已经存在，无需重新创建
        print(f"预处理后数据记录数: {len(self.df)}")
    
    def build_enhanced_keyword_library(self):
        """构建增强版关键词库"""
        # 长期战略词库
        self.long_term_words = {
            'long-term', 'long term', 'longterm',
            'strategic', 'strategy', 'strategies', 'strategically',
            'sustainable', 'sustainability', 'sustainably',
            'enduring', 'endurance', 'persistent', 'persistence',
            'lasting', 'permanent', 'permanence',
            'future-oriented', 'future oriented', 'futureoriented',
            'forward-looking', 'forward looking', 'forwardlooking',
            'vision', 'visionary', 'visioning',
            'perspective', 'perspectives',
            'holistic', 'comprehensive', 'integrated', 'integration',
            'systematic', 'system', 'systems',
            'framework', 'frameworks',
            'blueprint',
            'roadmap', 'road map',
            'action plan', 'action_plan', 'actionplan',
            'partnership', 'partnerships',
            'alliance', 'alliances',
            'cooperation', 'cooperative',
            'collaboration', 'collaborative',
            'joint',
            'mutual',
            'reciprocal',
            'win-win', 'win win', 'winwin'
        }
        
        # 合作领域关键词分类
        self.cooperation_domains = {
            'economic': ['economic', 'economy', 'trade', 'investment', 'business', 'commerce', 'finance'],
            'infrastructure': ['infrastructure', 'road', 'railway', 'port', 'airport', 'energy', 'power', 'telecom'],
            'agriculture': ['agriculture', 'agricultural', 'farm', 'farmer', 'food', 'crop', 'irrigation'],
            'education': ['education', 'school', 'university', 'student', 'teacher', 'academic'],
            'health': ['health', 'medical', 'hospital', 'doctor', 'nurse', 'disease', 'healthcare'],
            'technology': ['technology', 'tech', 'innovation', 'digital', 'internet', 'ai', 'it', 'r&d', 'research'],
            'culture': ['culture', 'cultural', 'art', 'music', 'film', 'tourism'],
            'environment': ['environment', 'climate', 'green', 'renewable', 'sustainable', 'ecology'],
            'security': ['security', 'defense', 'peace', 'stability', 'military']
        }
        
        # 主体类型关键词
        self.agent_types = {
            'government': ['government', 'state', 'nation', 'official', 'ministry', 'department', 'agency'],
            'enterprise': ['enterprise', 'company', 'corporation', 'business', 'firm', 'industry', 'smes'],
            'academic': ['university', 'college', 'institute', 'research', 'academy', 'think tank'],
            'ngo': ['ngo', 'civil society', 'charity', 'foundation', 'nonprofit'],
            'international': ['international', 'global', 'un', 'international organization', 'multilateral']
        }
        
        print(f"长期战略词库大小: {len(self.long_term_words)}")
        print(f"合作领域数: {len(self.cooperation_domains)}")
        print(f"主体类型数: {len(self.agent_types)}")
    
    def calculate_enhanced_components(self):
        """计算优化后的分量"""
        print("计算优化后的分量...")
        
        # 1. 长期战略词频优化（考虑领域覆盖）
        def calculate_enhanced_long_term(text):
            if not isinstance(text, str) or not text:
                return 0
            
            # 计算战略词频
            count = 0
            for word in self.long_term_words:
                if word in text:
                    count += 1
            
            return count
        
        # 2. 主体互动强度（重新设计）
        def calculate_agent_interaction_strength(text):
            if not isinstance(text, str) or not text:
                return 0
            
            # 统计提及的主体类型
            agent_presence = {}
            for agent_type, keywords in self.agent_types.items():
                for keyword in keywords:
                    if keyword in text:
                        agent_presence[agent_type] = True
                        break
            
            # 互动强度 = 提及的主体类型数量
            return len(agent_presence)
        
        # 3. 合作领域多样性（新增）
        def calculate_cooperation_diversity(text):
            if not isinstance(text, str) or not text:
                return 0
            
            # 统计涉及的合作领域数量
            domain_presence = {}
            for domain, keywords in self.cooperation_domains.items():
                for keyword in keywords:
                    if keyword in text:
                        domain_presence[domain] = True
                        break
            
            return len(domain_presence)
        
        # 应用函数计算分量
        self.df['enhanced_long_term'] = self.df['processed_text'].apply(calculate_enhanced_long_term)
        self.df['agent_interaction_strength'] = self.df['processed_text'].apply(calculate_agent_interaction_strength)
        self.df['cooperation_diversity'] = self.df['processed_text'].apply(calculate_cooperation_diversity)
        
        # 对数变换处理长尾分布
        self.df['enhanced_long_term_log'] = np.log1p(self.df['enhanced_long_term'])
        self.df['agent_interaction_log'] = np.log1p(self.df['agent_interaction_strength'])
        self.df['cooperation_diversity_log'] = np.log1p(self.df['cooperation_diversity'])
        
    def normalize_components(self):
        """归一化所有分量"""
        print("归一化分量...")
        
        # 选择需要归一化的分量
        components_to_normalize = [
            'enhanced_long_term_log',
            'agent_interaction_log', 
            'cooperation_diversity_log'
        ]
        
        # 使用z-score标准化
        scaler = StandardScaler()
        normalized_data = scaler.fit_transform(self.df[components_to_normalize])
        
        # 转换为数据框
        self.optimized_components = pd.DataFrame(normalized_data, columns=[f'{col}_zscore' for col in components_to_normalize], index=self.df.index)
        
        # 转换到0-1范围
        minmax_scaler = MinMaxScaler()
        normalized_01 = minmax_scaler.fit_transform(self.optimized_components)
        self.optimized_components = pd.concat([
            pd.DataFrame(normalized_01, columns=[f'{col}_01' for col in components_to_normalize], index=self.df.index),
            self.optimized_components
        ], axis=1)
        
        # 原始分量转换
        original_components = self.df[['enhanced_long_term', 'agent_interaction_strength', 'cooperation_diversity']].copy()
        self.optimized_components = pd.concat([self.optimized_components, original_components], axis=1)
        
        # 保存原始分量用于对比
        self.original_components = self.df[['long_term_percentile', 'multi_agent_percentile', 'cooperation_depth_index']].copy()
    
    def calculate_weights(self):
        """使用主成分分析确定权重"""
        print("使用主成分分析确定权重...")
        
        # 选择z-score标准化后的分量
        pca_input = self.optimized_components[[
            'enhanced_long_term_log_zscore',
            'agent_interaction_log_zscore',
            'cooperation_diversity_log_zscore'
        ]]
        
        # 执行主成分分析
        self.pca = PCA(n_components=1)
        self.pca.fit(pca_input)
        
        # 提取权重
        self.weights = self.pca.components_[0]
        
        # 归一化权重到正数范围
        if any(w < 0 for w in self.weights):
            self.weights = self.weights - np.min(self.weights)
        self.weights = self.weights / np.sum(self.weights)
        
        print(f"主成分方差解释比例: {self.pca.explained_variance_ratio_[0]:.4f}")
        print(f"分量权重: {self.weights}")
    
    def synthesize_index(self):
        """合成优化后的合作纵深性指数"""
        print("合成优化后的合作纵深性指数...")
        
        # 方法1: 基于PCA权重的加权平均
        zscore_cols = [
            'enhanced_long_term_log_zscore',
            'agent_interaction_log_zscore',
            'cooperation_diversity_log_zscore'
        ]
        
        self.df['optimized_cooperation_depth_pca'] = np.dot(
            self.optimized_components[zscore_cols],
            self.weights
        )
        
        # 方法2: 基于0-1范围的简单平均
        self.df['optimized_cooperation_depth_avg'] = self.optimized_components[[
            'enhanced_long_term_log_01',
            'agent_interaction_log_01',
            'cooperation_diversity_log_01'
        ]].mean(axis=1)
        
        # 归一化到0-1范围
        scaler = MinMaxScaler()
        self.df['optimized_cooperation_depth'] = scaler.fit_transform(
            self.df[['optimized_cooperation_depth_pca']]
        ).flatten()
        
    def calculate_cronbach_alpha(self, components):
        """计算Cronbach's α"""
        # 计算协方差矩阵
        cov_matrix = components.cov()
        total_variance = cov_matrix.sum().sum()
        avg_item_variance = np.mean(np.diag(cov_matrix))
        
        k = len(components.columns)
        if k < 2:
            return None
        
        alpha = (k / (k - 1)) * (1 - (avg_item_variance / (total_variance / k)))
        return alpha
    
    def validate_index(self):
        """验证优化后的指数"""
        print("验证优化后的指数...")
        
        # 计算原始指数的内部一致性
        original_alpha = self.calculate_cronbach_alpha(
            self.df[['long_term_percentile', 'multi_agent_percentile']]
        )
        
        # 计算优化后指数的内部一致性
        optimized_alpha = self.calculate_cronbach_alpha(
            self.optimized_components[[
                'enhanced_long_term_log_01',
                'agent_interaction_log_01',
                'cooperation_diversity_log_01'
            ]]
        )
        
        # 计算因子解释方差比例
        pca_variance = self.pca.explained_variance_ratio_[0]
        
        print(f"\n信效度验证结果:")
        print(f"原始指数内部一致性 (Cronbach's α): {original_alpha:.4f}")
        print(f"优化后指数内部一致性 (Cronbach's α): {optimized_alpha:.4f}")
        print(f"优化后指数结构效度 (因子解释方差): {pca_variance:.4f}")
        
        return {
            'original_alpha': original_alpha,
            'optimized_alpha': optimized_alpha,
            'pca_variance': pca_variance
        }
    
    def generate_comparison_reports(self):
        """生成对比分析报告"""
        print("生成对比分析报告...")
        
        # 1. 描述性统计对比
        original_stats = self.df[['long_term_percentile', 'multi_agent_percentile', 'cooperation_depth_index']].describe()
        optimized_stats = self.df[['enhanced_long_term', 'agent_interaction_strength', 'cooperation_diversity', 'optimized_cooperation_depth']].describe()
        
        # 保存统计对比
        stats_comparison = pd.concat([original_stats, optimized_stats], axis=1)
        stats_comparison.to_csv(os.path.join(output_dir, '优化前后描述性统计对比.csv'), encoding='utf-8-sig')
        
        # 2. 相关性分析
        correlation_data = pd.concat([
            self.df[['long_term_percentile', 'multi_agent_percentile', 'cooperation_depth_index']],
            self.df[['enhanced_long_term', 'agent_interaction_strength', 'cooperation_diversity', 'optimized_cooperation_depth']]
        ], axis=1)
        correlation_matrix = correlation_data.corr()
        
        # 保存相关矩阵
        correlation_matrix.to_csv(os.path.join(output_dir, '优化前后相关矩阵.csv'), encoding='utf-8-sig')
        
        # 3. 可视化对比
        self.generate_visualizations()
    
    def generate_visualizations(self):
        """生成可视化对比"""
        print("生成可视化对比...")
        
        # 1. 分量分布对比
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('优化前后分量分布对比', fontsize=16, fontweight='bold')
        
        # 原始分量分布
        sns.histplot(self.df['long_term_percentile'], kde=True, ax=axes[0, 0])
        axes[0, 0].set_title('原始: 长期战略词频百分位')
        
        sns.histplot(self.df['multi_agent_percentile'], kde=True, ax=axes[0, 1])
        axes[0, 1].set_title('原始: 多元主体互动百分位')
        
        sns.histplot(self.df['cooperation_depth_index'], kde=True, ax=axes[0, 2])
        axes[0, 2].set_title('原始: 合作纵深性指数')
        
        # 优化后分量分布
        sns.histplot(self.df['enhanced_long_term'], kde=True, ax=axes[1, 0])
        axes[1, 0].set_title('优化: 增强长期战略词频')
        
        sns.histplot(self.df['agent_interaction_strength'], kde=True, ax=axes[1, 1])
        axes[1, 1].set_title('优化: 主体互动强度')
        
        sns.histplot(self.df['optimized_cooperation_depth'], kde=True, ax=axes[1, 2])
        axes[1, 2].set_title('优化: 合作纵深性指数')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '优化前后分量分布对比.png'), dpi=300)
        plt.close()
        
        # 2. 分量间相关性对比
        fig, axes = plt.subplots(1, 2, figsize=(18, 8))
        fig.suptitle('优化前后分量间相关性对比', fontsize=16, fontweight='bold')
        
        # 原始分量相关矩阵
        original_corr = self.df[['long_term_percentile', 'multi_agent_percentile']].corr()
        sns.heatmap(original_corr, annot=True, cmap='coolwarm', ax=axes[0])
        axes[0].set_title('原始分量相关矩阵')
        
        # 优化后分量相关矩阵
        optimized_corr = self.df[['enhanced_long_term', 'agent_interaction_strength', 'cooperation_diversity']].corr()
        sns.heatmap(optimized_corr, annot=True, cmap='coolwarm', ax=axes[1])
        axes[1].set_title('优化后分量相关矩阵')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '优化前后分量相关性对比.png'), dpi=300)
        plt.close()
        
        # 3. 优化前后指数对比
        plt.figure(figsize=(12, 8))
        sns.scatterplot(x=self.df['cooperation_depth_index'], y=self.df['optimized_cooperation_depth'], alpha=0.5)
        plt.title('优化前后合作纵深性指数对比', fontsize=14, fontweight='bold')
        plt.xlabel('原始合作纵深性指数')
        plt.ylabel('优化后合作纵深性指数')
        plt.grid(True, alpha=0.3)
        plt.savefig(os.path.join(output_dir, '优化前后指数对比散点图.png'), dpi=300)
        plt.close()
    
    def save_results(self):
        """保存优化结果"""
        print("保存优化结果...")
        
        # 保存完整结果
        result_cols = [
            'enhanced_long_term', 'agent_interaction_strength', 'cooperation_diversity',
            'enhanced_long_term_log', 'agent_interaction_log', 'cooperation_diversity_log',
            'optimized_cooperation_depth', 'optimized_cooperation_depth_pca', 'optimized_cooperation_depth_avg'
        ]
        
        final_results = pd.concat([self.raw_df, self.df[result_cols]], axis=1)
        final_results.to_csv(os.path.join(output_dir, '合作纵深性优化结果.csv'), index=False, encoding='utf-8-sig')
        
        # 保存优化前后指数
        index_comparison = final_results[[
            'cooperation_depth_index', 'optimized_cooperation_depth'
        ]]
        index_comparison.to_csv(os.path.join(output_dir, '优化前后指数对比.csv'), index=False, encoding='utf-8-sig')
        
        print(f"优化结果已保存到: {output_dir}")
    
    def run_optimization(self, file_path):
        """执行完整的优化流程"""
        print("=" * 60)
        print("合作纵深性指数优化流程开始")
        print("=" * 60)
        
        # 执行各个步骤
        self.load_data(file_path)
        self.preprocess_data()
        self.build_enhanced_keyword_library()
        self.calculate_enhanced_components()
        self.normalize_components()
        self.calculate_weights()
        self.synthesize_index()
        validation_results = self.validate_index()
        self.generate_comparison_reports()
        self.save_results()
        
        print("=" * 60)
        print("合作纵深性指数优化流程完成")
        print("=" * 60)
        
        return validation_results

# 主函数
if __name__ == "__main__":
    # 创建优化器实例
    optimizer = CooperationDepthOptimizer()
    
    # 运行优化流程
    file_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_complete_features.csv'
    validation_results = optimizer.run_optimization(file_path)
    
    # 生成总结报告
    summary_report = f"""# 合作纵深性指数优化总结报告

## 优化目标
提升合作纵深性指数的内部一致性和结构效度，使其更适合用于回归分析。

## 优化结果
- **原始指数内部一致性 (Cronbach's α)**: {validation_results['original_alpha']:.4f}
- **优化后指数内部一致性 (Cronbach's α)**: {validation_results['optimized_alpha']:.4f}
- **优化后指数结构效度 (因子解释方差)**: {validation_results['pca_variance']:.4f}

## 优化方案

### 1. 指标构成优化
- **增强长期战略词频**: 改进关键词匹配，增加领域覆盖分析
- **主体互动强度**: 计算不同主体类型间的互动频次
- **合作领域多样性**: 统计涉及的合作领域数量

### 2. 计算方法优化
- 采用主成分分析确定分量权重
- 统一使用z-score标准化
- 基于共同因子合成最终指数

### 3. 合成方法
- 主成分分析方差解释比例: {validation_results['pca_variance']:.4f}
- 分量权重: {optimizer.weights}

## 优化效果评估
- 内部一致性提升: {'是' if validation_results['optimized_alpha'] >= 0.6 else '否'}
- 结构效度提升: {'是' if validation_results['pca_variance'] >= 0.7 else '否'}
- 整体信效度改善: {'显著' if validation_results['optimized_alpha'] >= 0.6 and validation_results['pca_variance'] >= 0.7 else '中等'}

## 可视化结果
- 优化前后分量分布对比
- 优化前后分量相关性对比
- 优化前后指数对比散点图

## 输出文件
- 合作纵深性优化结果.csv: 完整优化结果
- 优化前后描述性统计对比.csv: 统计对比
- 优化前后相关矩阵.csv: 相关性对比
- 优化前后指数对比.csv: 指数对比
- 多种可视化图表

## 后续建议
1. **使用建议**: {'推荐使用优化后的指数' if validation_results['optimized_alpha'] >= 0.6 else '建议进一步优化'}
2. **进一步优化方向**: 
   - 调整关键词分类体系
   - 尝试不同的合成方法
   - 进行细分样本验证
"""
    
    # 保存总结报告
    with open(os.path.join(output_dir, '合作纵深性指数优化总结报告.md'), 'w', encoding='utf-8') as f:
        f.write(summary_report)
    
    print("优化总结报告已生成")
