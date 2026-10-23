import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from scipy import stats

# 文件路径
unique_merged_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/unique_merged_data.csv'

print("=== 预测缺失的合作纵深性指数 ===")

# 读取去重后的融合数据
print("\n1. 读取去重后的融合数据...")
df = pd.read_csv(unique_merged_file, low_memory=False)
print(f"   总记录数: {len(df)}")

# 分离匹配和未匹配的数据
print("\n2. 分离匹配和未匹配的数据...")
matched_df = df[df['cooperation_depth_index'].notnull()]
unmatched_df = df[df['cooperation_depth_index'].isnull()]
print(f"   - 匹配到的记录数: {len(matched_df)}")
print(f"   - 未匹配到的记录数: {len(unmatched_df)}")

# 准备训练数据
print("\n3. 准备训练数据...")
# 选择特征列
feature_columns = [
    # 数值特征
    'year',
    '全部情感强度',
    'positive_words_count',
    'negative_words_count',
    'total_words_count',
    'community_similarity',
    'normalized_sentiment',
    'china_africa_community_recognition',
    'development_terms_weight',
    'local_sentiment',
    'standardized_tfidf_weight',
    'standardized_local_sentiment',
    'development_demand_perception',
    'development_keyword_count',
    'development_keyword_density'
]

# 检查特征列是否存在
available_features = [col for col in feature_columns if col in df.columns]
print(f"   - 可用特征数: {len(available_features)}")
print(f"   - 特征列表: {available_features}")

# 准备训练数据
X_train = matched_df[available_features]
y_train = matched_df['cooperation_depth_index']

# 准备测试数据
X_test = unmatched_df[available_features]

# 训练随机森林回归模型
print("\n4. 训练随机森林回归模型...")
model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1, max_depth=10)
model.fit(X_train, y_train)

# 模型评估
print("\n5. 模型评估...")
y_train_pred = model.predict(X_train)
train_mse = mean_squared_error(y_train, y_train_pred)
train_r2 = r2_score(y_train, y_train_pred)
print(f"   - 训练集MSE: {train_mse:.4f}")
print(f"   - 训练集R²: {train_r2:.4f}")

# 预测未匹配记录
print("\n6. 预测未匹配记录...")
y_pred = model.predict(X_test)

# 计算预测置信度
print("\n7. 计算预测置信度...")
# 使用随机森林的预测标准差作为置信度指标
# 获取每个样本的预测分布（每个决策树的预测值）
tree_preds = np.array([tree.predict(X_test) for tree in model.estimators_])
# 计算每个样本的预测标准差
pred_std = np.std(tree_preds, axis=0)
# 计算置信度：标准差越小，置信度越高
# 置信度计算公式：1 / (1 + pred_std)
confidence = 1 / (1 + pred_std)

# 确保置信度在0-1之间
confidence = np.clip(confidence, 0, 1)

# 检查置信度分布
print(f"   - 平均置信度: {confidence.mean():.4f}")
print(f"   - 置信度中位数: {np.median(confidence):.4f}")
print(f"   - 置信度最小值: {confidence.min():.4f}")
print(f"   - 置信度最大值: {confidence.max():.4f}")

# 统计置信度>0.6的记录数
high_confidence_count = (confidence > 0.6).sum()
print(f"   - 置信度>0.6的记录数: {high_confidence_count} ({high_confidence_count/len(confidence)*100:.2f}%)")

# 应用置信度阈值
print("\n8. 应用置信度阈值...")
# 对于置信度>0.6的记录，使用预测值；否则使用均值填充
y_pred_final = np.where(confidence > 0.6, y_pred, y_train.mean())

# 检查填充后的值分布
print(f"   - 预测值平均值: {y_pred_final.mean():.4f}")
print(f"   - 预测值标准差: {y_pred_final.std():.4f}")
print(f"   - 预测值最小值: {y_pred_final.min():.4f}")
print(f"   - 预测值最大值: {y_pred_final.max():.4f}")

# 将预测值合并回原始数据
print("\n9. 将预测值合并回原始数据...")
# 创建预测结果数据框
pred_results = pd.DataFrame({
    'original_index': unmatched_df['original_index'],
    'cooperation_depth_index_pred': y_pred_final,
    'prediction_confidence': confidence
})

# 合并到原始数据
df = df.merge(pred_results, on='original_index', how='left')

# 填充缺失的合作纵深性指数
coop_fields = ['long_term_word_count', 'has_multi_agent_interaction', 
               'long_term_word_count_log', 'long_term_percentile', 
               'multi_agent_percentile', 'cooperation_depth_index',
               'long_term_word_count_scaled', 'has_multi_agent_interaction_scaled']

# 对于未匹配的记录，填充预测值
for field in coop_fields:
    if field == 'cooperation_depth_index':
        df[field] = df[field].fillna(df['cooperation_depth_index_pred'])
    else:
        # 对于其他字段，使用均值填充
        field_mean = matched_df[field].mean()
        df[field] = df[field].fillna(field_mean)

# 检查填充后的完整性
print("\n10. 检查填充后的完整性...")
for field in coop_fields:
    non_null_count = df[field].notnull().sum()
    print(f"   - {field}: 非空值数 = {non_null_count} ({non_null_count/len(df)*100:.2f}%)")

# 保存最终结果
print("\n11. 保存最终结果...")
final_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_complete_features.csv'
df.to_csv(final_file, index=False, encoding='utf-8-sig')
print(f"   - 最终文件已保存到: {final_file}")

print(f"\n=== 预测完成 ===")
print(f"✅ 匹配到的记录数: {len(matched_df)}")
print(f"✅ 预测记录数: {len(unmatched_df)}")
print(f"✅ 置信度>0.6的记录数: {high_confidence_count} ({high_confidence_count/len(unmatched_df)*100:.2f}%)")
print(f"✅ 最终记录数: {len(df)}")
print(f"✅ 所有合作纵深性字段都已填充")
