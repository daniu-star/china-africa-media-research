import pandas as pd

# 读取数据
df = pd.read_csv('c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\清洗数据\\enhanced_data_with_demand_perception.csv', low_memory=False)

print('=== 优化后合作纵深性指数验证 ===')
print('总记录数:', len(df))

# 检查合作纵深性指数的基本统计
print('\n=== 合作纵深性指数统计 ===')
print(df['cooperation_depth_index'].describe())

# 检查指数分布
print('\n=== 指数分布情况 ===')
bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
# 使用pandas cut函数进行分箱
counts = pd.cut(df['cooperation_depth_index'], bins=bins, include_lowest=True).value_counts().sort_index()
for bin_range, count in counts.items():
    print(f'{bin_range}: {count} 条 ({count/len(df)*100:.2f}%)')

# 检查是否还有0值
print('\n=== 0值检查 ===')
zero_count = len(df[df['cooperation_depth_index'] == 0.0])
print('指数为0的记录数:', zero_count)
print('指数为0的比例:', '{:.2f}%'.format(zero_count/len(df)*100))

# 查看样本数据
print('\n=== 样本数据 ===')
sample = df.sample(5)
print('随机5条样本的合作纵深性指数:')
for i, row in sample.iterrows():
    print('样本{}: {:.4f}'.format(i, row['cooperation_depth_index']))
    print('  长期战略词频: {}'.format(row['long_term_word_count']))
    print('  多元主体互动: {}'.format(row['has_multi_agent_interaction']))
    print()

print('=== 验证完成 ===')
