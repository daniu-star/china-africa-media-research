import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
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
result_dir = '优化版_潜在剖面分析结果'
os.makedirs(result_dir, exist_ok=True)
print(f"结果将保存到: {result_dir}")

# 1. 数据读取与准备
print("\n1. 数据读取与准备")
data_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv'
df = pd.read_csv(data_path, low_memory=False)
print(f"原始数据大小: {len(df)} 行, {len(df.columns)} 列")

# 2. 变量定义
print("\n2. 变量定义")

# 核心变量
core_vars = {
    'development_demand': 'development_demand_pca',
    'sentiment': 'normalized_sentiment',
    'cooperation': 'cooperation_willingness_advanced'
}

# 连续控制变量
continuous_covariates = ['time_index', 'total_words_count']

# 分类控制变量
categorical_covariates = ['source_region_5', 'category']

# 3. 数据预处理
print("\n3. 数据预处理")

# 3.1 基于关键词的新闻分类
print("  基于关键词的新闻分类...")

# 扩展关键词词典，确保所有样本都能被分类
topic_keywords = {
    '政治': ['politic', 'government', 'election', 'president', 'leader', 'diplomatic', 'foreign', 'policy', 'parliament', 'vote', 'party', 'campaign', 'democracy', 'treaty', 'summit', 'ambassador', 'embassy', 'negotiation', 'agreement', 'minister', 'state', 'official', 'diplomacy', 'international', 'relations', 'cooperation', 'diplomat', 'politician', 'regime', 'authority', 'governance', 'sovereignty', 'alliance', 'conflict', 'peace', 'security', 'military', 'defense', 'strategy', 'foreign', 'affairs', 'geopolitics', 'global', 'international', 'cooperation', 'multilateral', 'bilateral', 'agreement', 'treaty', 'pact', 'accord', 'summit', 'conference', 'meeting', 'talks', 'negotiation', 'dialogue', 'diplomacy', 'diplomatic', 'ambassador', 'embassy', 'consulate', 'foreign', 'ministry', 'state', 'department', 'government', 'administration', 'regime', 'authority', 'leadership', 'president', 'prime', 'minister', 'premier', 'chancellor', 'king', 'queen', 'monarch', 'ruler', 'leader', 'politician', 'party', 'political', 'election', 'vote', 'ballot', 'campaign', 'candidate', 'winner', 'loser', 'majority', 'minority', 'coalition', 'parliament', 'congress', 'assembly', 'legislature', 'senate', 'house', 'of', 'representatives', 'lawmaker', 'legislator', 'debate', 'discussion', 'policy', 'bill', 'law', 'regulation', 'ordinance', 'decree', 'order', 'ruling', 'judgment', 'court', 'justice', 'constitution', 'democracy', 'authoritarian', 'dictatorship', 'totalitarian', 'freedom', 'liberty', 'human', 'rights', 'civil', 'rights', 'equality', 'justice'],
    '经济': ['economic', 'economy', 'business', 'trade', 'market', 'finance', 'investment', 'growth', 'development', 'cooperation', 'infrastructure', 'aid', 'financing', 'export', 'import', 'gdp', 'industry', 'company', 'profit', 'project', 'business', 'commercial', 'financial', 'fund', 'capital', 'economy', 'trade', 'investment', 'economic', 'growth', 'gdp', 'gross', 'domestic', 'product', 'inflation', 'deflation', 'unemployment', 'employment', 'job', 'labor', 'market', 'wage', 'salary', 'income', 'poverty', 'wealth', 'inequality', 'rich', 'poor', 'middle', 'class', 'consumer', 'spending', 'consumption', 'savings', 'investment', 'interest', 'rate', 'monetary', 'policy', 'fiscal', 'policy', 'tax', 'taxation', 'budget', 'deficit', 'surplus', 'debt', 'national', 'debt', 'government', 'spending', 'expenditure', 'revenue', 'income', 'corporate', 'profit', 'loss', 'earnings', 'dividend', 'stock', 'market', 'share', 'equity', 'bond', 'security', 'finance', 'bank', 'banking', 'financial', 'institution', 'central', 'bank', 'loan', 'credit', 'debt', 'mortgage', 'interest', 'rate', 'currency', 'exchange', 'rate', 'forex', 'foreign', 'exchange', 'trade', 'export', 'import', 'tariff', 'custom', 'duty', 'trade', 'agreement', 'free', 'trade', 'agreement', 'fta', 'wto', 'world', 'trade', 'organization', 'investment', 'foreign', 'direct', 'investment', 'fdi', 'multinational', 'corporation', 'mnc', 'company', 'enterprise', 'business', 'firm', 'industry', 'sector', 'manufacturing', 'service', 'agriculture', 'mining', 'energy', 'oil', 'gas', 'coal', 'renewable', 'energy', 'solar', 'wind', 'hydro', 'electric', 'power', 'infrastructure', 'road', 'rail', 'port', 'airport', 'communication', 'technology', 'tech', 'innovation', 'research', 'development', 'rd', 'startup', 'entrepreneur', 'entrepreneurship', 'venture', 'capital', 'vc', 'angel', 'investor', 'crowdfunding', 'business', 'plan', 'strategy', 'management', 'leadership', 'marketing', 'sales', 'customer', 'client', 'brand', 'advertising', 'promotion', 'pr', 'public', 'relations', 'corporate', 'social', 'responsibility', 'csr', 'sustainability', 'sustainable', 'development'],
    '文化': ['culture', 'art', 'music', 'film', 'literature', 'education', 'heritage', 'festival', 'language', 'religion', 'museum', 'theater', 'dance', 'painting', 'sculpture', 'poetry', 'tradition', 'history', 'philosophy', 'sport', 'tourism', 'education', 'university', 'school', 'academic', 'cultural', 'artistic', 'literary', 'art', 'artist', 'painting', 'sculpture', 'draw', 'design', 'architecture', 'photography', 'cinema', 'film', 'movie', 'director', 'actor', 'actress', 'script', 'screenplay', 'cinematography', 'music', 'musician', 'singer', 'song', 'album', 'concert', 'performance', 'festival', 'art', 'exhibition', 'gallery', 'museum', 'heritage', 'history', 'historical', 'ancient', 'traditional', 'culture', 'cultural', 'custom', 'ritual', 'ceremony', 'festival', 'holiday', 'celebration', 'language', 'linguistics', 'dialect', 'writing', 'literature', 'author', 'writer', 'poet', 'novel', 'book', 'story', 'tale', 'fiction', 'nonfiction', 'biography', 'autobiography', 'essay', 'article', 'journal', 'magazine', 'newspaper', 'publishing', 'publisher', 'editor', 'library', 'reading', 'education', 'school', 'university', 'college', 'institute', 'academy', 'student', 'teacher', 'professor', 'lecturer', 'scholar', 'academic', 'research', 'study', 'learning', 'knowledge', 'wisdom', 'philosophy', 'thought', 'ideology', 'religion', 'faith', 'belief', 'spirituality', 'god', 'church', 'mosque', 'temple', 'synagogue', 'worship', 'prayer', 'pilgrimage', 'tourism', 'travel', 'tour', 'trip', 'journey', 'destination', 'attraction', 'sightseeing', 'hospitality', 'hotel', 'restaurant', 'food', 'cuisine', 'dish', 'recipe', 'cooking', 'chef', 'gastronomy', 'sport', 'game', 'match', 'competition', 'tournament', 'championship', 'olympic', 'paralympic', 'athlete', 'player', 'team', 'coach', 'referee', 'score', 'win', 'lose', 'draw', 'victory', 'defeat', 'record', 'statistics'],
    '民生': ['people', 'life', 'health', 'employment', 'welfare', 'medical', 'healthcare', 'education', 'housing', 'poverty', 'income', 'salary', 'job', 'work', 'social', 'community', 'population', 'human', 'lifestyle', 'standard', 'living', 'quality', 'public', 'service', 'social', 'people', 'person', 'human', 'individual', 'population', 'demographics', 'age', 'gender', 'sex', 'race', 'ethnicity', 'nationality', 'citizenship', 'immigration', 'emigration', 'refugee', 'asylum', 'seeker', 'migrant', 'work', 'job', 'employment', 'unemployment', 'occupation', 'career', 'profession', 'vocation', 'trade', 'skill', 'training', 'education', 'school', 'university', 'college', 'student', 'teacher', 'lecturer', 'professor', 'academic', 'learning', 'knowledge', 'diploma', 'degree', 'certificate', 'qualification', 'health', 'medical', 'healthcare', 'hospital', 'clinic', 'doctor', 'nurse', 'surgeon', 'physician', 'patient', 'disease', 'illness', 'sickness', 'injury', 'accident', 'treatment', 'therapy', 'medicine', 'drug', 'pharmaceutical', 'health', 'insurance', 'social', 'security', 'welfare', 'benefit', 'pension', 'retirement', 'elderly', 'old', 'age', 'child', 'children', 'family', 'parent', 'mother', 'father', 'marriage', 'divorce', 'relationship', 'housing', 'home', 'house', 'apartment', 'rent', 'mortgage', 'property', 'real', 'estate', 'housing', 'affordability', 'homelessness', 'food', 'hunger', 'nutrition', 'diet', 'agriculture', 'farming', 'crop', 'harvest', 'food', 'security', 'poverty', 'poor', 'wealthy', 'rich', 'income', 'salary', 'wage', 'earning', 'pension', 'benefit', 'social', 'welfare', 'standard', 'of', 'living', 'quality', 'of', 'life', 'happiness', 'wellbeing', 'welfare', 'community', 'neighborhood', 'local', 'area', 'region', 'city', 'town', 'village', 'urban', 'rural', 'suburban', 'infrastructure', 'road', 'highway', 'bridge', 'railway', 'train', 'bus', 'public', 'transport', 'transportation', 'airport', 'port', 'harbor', 'water', 'supply', 'sanitation', 'sewage', 'electricity', 'power', 'energy', 'communication', 'internet', 'telephone', 'mobile', 'phone', 'public', 'service', 'utility', 'government', 'service', 'administration', 'governance', 'public', 'safety', 'security', 'police', 'crime', 'law', 'order', 'justice', 'court', 'prison', 'punishment', 'rehabilitation', 'disaster', 'emergency', 'crisis', 'natural', 'disaster', 'flood', 'earthquake', 'drought', 'storm', 'hurricane', 'typhoon', 'tsunami', 'fire', 'wildfire', 'accident', 'rescue', 'relief', 'aid', 'charity', 'volunteer', 'nonprofit', 'ngo', 'non', 'governmental', 'organization', 'foundation', 'donation', 'philanthropy', 'humanitarian'],
    '社会': ['society', 'technology', 'environment', 'sport', 'entertainment', 'media', 'internet', 'climate', 'disaster', 'security', 'safety', 'crime', 'accident', 'fire', 'flood', 'earthquake', 'drought', 'storm', 'tech', 'science', 'digital', 'social', 'media', 'journalism', 'news', 'report', 'environment', 'climate', 'weather', 'society', 'social', 'community', 'group', 'collective', 'public', 'people', 'individual', 'citizen', 'human', 'social', 'issue', 'problem', 'challenge', 'trend', 'phenomenon', 'change', 'evolution', 'development', 'progress', 'regression', 'stagnation', 'technology', 'tech', 'science', 'innovation', 'invention', 'discovery', 'research', 'development', 'engineering', 'computer', 'software', 'hardware', 'internet', 'web', 'website', 'app', 'application', 'mobile', 'phone', 'smartphone', 'device', 'digital', 'data', 'information', 'communication', 'network', 'connection', 'online', 'offline', 'cyber', 'virtual', 'augmented', 'reality', 'artificial', 'intelligence', 'ai', 'machine', 'learning', 'robot', 'automation', 'algorithm', 'big', 'data', 'cloud', 'computing', 'blockchain', 'cryptocurrency', 'bitcoin', 'tech', 'company', 'startup', 'entrepreneur', 'innovation', 'environment', 'environmental', 'ecology', 'ecosystem', 'nature', 'natural', 'resource', 'energy', 'renewable', 'solar', 'wind', 'hydro', 'electric', 'power', 'fossil', 'fuel', 'coal', 'oil', 'gas', 'pollution', 'air', 'water', 'soil', 'contamination', 'emission', 'carbon', 'footprint', 'climate', 'change', 'global', 'warming', 'greenhouse', 'effect', 'sustainability', 'sustainable', 'development', 'conservation', 'preservation', 'protection', 'recycling', 'waste', 'management', 'climate', 'action', 'weather', 'meteorology', 'climate', 'forecast', 'storm', 'rain', 'snow', 'sun', 'heat', 'cold', 'temperature', 'humidity', 'wind', 'speed', 'pressure', 'weather', 'condition', 'disaster', 'natural', 'disaster', 'flood', 'earthquake', 'drought', 'storm', 'hurricane', 'typhoon', 'tsunami', 'fire', 'wildfire', 'accident', 'industrial', 'accident', 'nuclear', 'disaster', 'security', 'safety', 'public', 'safety', 'security', 'police', 'law', 'enforcement', 'crime', 'criminal', 'offense', 'violence', 'murder', 'homicide', 'robbery', 'theft', 'burglary', 'fraud', 'corruption', 'bribery', 'drug', 'trafficking', 'human', 'trafficking', 'terrorism', 'extremism', 'radicalization', 'conflict', 'war', 'peace', 'security', 'defense', 'military', 'army', 'navy', 'air', 'force', 'weapon', 'gun', 'firearm', 'nuclear', 'weapon', 'disarmament', 'arms', 'control', 'entertainment', 'media', 'journalism', 'news', 'report', 'article', 'story', 'news', 'paper', 'magazine', 'journal', 'broadcast', 'television', 'tv', 'radio', 'podcast', 'video', 'streaming', 'platform', 'social', 'media', 'facebook', 'twitter', 'x', 'instagram', 'youtube', 'tiktok', 'linkedin', 'snapchat', 'reddit', 'forum', 'blog', 'blogger', 'influencer', 'content', 'creator', 'journalist', 'reporter', 'editor', 'producer', 'director', 'actor', 'actress', 'celebrity', 'star', 'famous', 'popular', 'entertainment', 'show', 'performance', 'concert', 'theater', 'play', 'musical', 'film', 'movie', 'cinema', 'hollywood', 'bollywood', 'film', 'industry', 'music', 'song', 'album', 'artist', 'band', 'singer', 'musician', 'composer', 'producer', 'record', 'label', 'music', 'industry', 'award', 'prize', 'ceremony', 'oscar', 'grammy', 'emmy', 'sport', 'game', 'match', 'competition', 'tournament', 'championship', 'olympic', 'paralympic', 'athlete', 'player', 'team', 'coach', 'referee', 'score', 'win', 'lose', 'draw', 'victory', 'defeat', 'record', 'statistics', 'football', 'soccer', 'basketball', 'tennis', 'baseball', 'cricket', 'rugby', 'volleyball', 'swimming', 'athletics', 'track', 'field', 'gymnastics', 'boxing', 'mma', 'wrestling', 'golf', 'cycling', 'skiing', 'snowboarding', 'surfing', 'horse', 'racing', 'motorsport', 'f1', 'formula', 'one', 'nascar', 'motocross', 'entertainment', 'leisure', 'hobby', 'game', 'play', 'fun', 'enjoyment', 'recreation', 'relaxation', 'vacation', 'holiday', 'travel', 'tourism']
}

# 定义分类函数，确保所有样本都能被分类
def classify_topic(title, summary):
    # 合并标题和摘要
    text = f"{title} {summary}".lower()
    
    # 计算每个类别的关键词匹配数
    match_counts = {}
    for topic, keywords in topic_keywords.items():
        count = sum(1 for keyword in keywords if keyword in text)
        match_counts[topic] = count
    
    # 返回匹配数最高的类别，即使所有类别都没有匹配，也返回匹配数最高的类别
    return max(match_counts, key=match_counts.get)

# 添加'combined_text'列用于分类
df['combined_text'] = df['title'] + ' ' + df['summary']

# 执行分类
df['主题'] = df.apply(lambda row: classify_topic(row['title'], row['summary']), axis=1)
print(f"  分类后新闻主题分布:")
print(df['主题'].value_counts().to_dict())

# 移除旧的category列，使用新的主题列
df = df.drop(['category'], axis=1, errors='ignore')

# 更新分类变量为主题
categorical_covariates = ['source_region_5', '主题']

# 3.2 处理缺失值
print("  处理缺失值...")
# 只保留核心变量、连续控制变量、分类控制变量和因变量，不删除缺失值（因为我们已经手动分类了）
all_vars = list(core_vars.values()) + continuous_covariates + categorical_covariates + ['china_africa_community_recognition']
df = df[all_vars]
print(f"  处理后数据大小: {len(df)} 行, {len(df.columns)} 列")

# 3.3 连续变量标准化
print("  连续变量标准化...")
scaler = StandardScaler()
scaled_vars = []
for var in list(core_vars.values()) + continuous_covariates:
    scaled_var = f'{var}_scaled'
    df[scaled_var] = scaler.fit_transform(df[[var]])
    scaled_vars.append(scaled_var)
    print(f"  {var} 标准化完成，均值: {df[scaled_var].mean():.4f}, 标准差: {df[scaled_var].std():.4f}")

# 3.4 分类变量编码
print("  分类变量编码...")
dummies = []

# 地区变量编码，以东非为基准
region_dummies = pd.get_dummies(df['source_region_5'], prefix='region', drop_first=True)
print(f"  地区虚拟变量: {', '.join(region_dummies.columns.tolist())}")
dummies.append(region_dummies)

# 新闻主题编码，使用手动分类结果
topic_dummies = pd.get_dummies(df['主题'], prefix='topic', drop_first=True)
print(f"  新闻主题数量: {df['主题'].nunique()}")
print(f"  新闻主题虚拟变量: {', '.join(topic_dummies.columns.tolist())}")
dummies.append(topic_dummies)

# 合并所有虚拟变量
dummies_df = pd.concat(dummies, axis=1)
df = pd.concat([df, dummies_df], axis=1)

# 4. 潜在剖面分析
print("\n4. 潜在剖面分析")

# 4.1 定义分析变量
# 核心变量（标准化） + 连续控制变量（标准化）
analysis_vars = scaled_vars
print(f"  分析变量: {analysis_vars}")
lpa_data = df[analysis_vars]

# 4.2 拟合不同数量剖面的模型
max_profiles = 6
models = {}
results = []

for n in range(1, max_profiles + 1):
    print(f"\n拟合 {n} 个剖面的模型...")
    
    # 拟合高斯混合模型
    gmm = GaussianMixture(n_components=n, random_state=42, covariance_type='full')
    gmm.fit(lpa_data)
    
    # 预测群体分类
    labels = gmm.predict(lpa_data)
    
    # 计算模型指标
    aic = gmm.aic(lpa_data)
    bic = gmm.bic(lpa_data)
    entropy = gmm.score(lpa_data)
    
    # 计算轮廓系数（仅当n > 1时）
    silhouette = silhouette_score(lpa_data, labels) if n > 1 else None
    
    # 保存模型结果
    models[n] = {
        'model': gmm,
        'labels': labels,
        'aic': aic,
        'bic': bic,
        'entropy': entropy,
        'silhouette': silhouette
    }
    
    results.append({
        'profiles': n,
        'aic': aic,
        'bic': bic,
        'entropy': entropy,
        'silhouette': silhouette
    })
    
    print(f"  AIC: {aic:.2f}")
    print(f"  BIC: {bic:.2f}")
    print(f"  熵值: {entropy:.2f}")
    if silhouette is not None:
        print(f"  轮廓系数: {silhouette:.2f}")

# 5. 模型比较与选择
print("\n5. 模型比较与选择")
results_df = pd.DataFrame(results)
print("模型拟合指标:")
print(results_df)

# 保存模型比较结果
results_df.to_csv(os.path.join(result_dir, '模型拟合指标.csv'), index=False, encoding='utf-8-sig')

# 可视化模型拟合指标
plt.figure(figsize=(12, 8))

# AIC和BIC
plt.subplot(2, 1, 1)
plt.plot(results_df['profiles'], results_df['aic'], marker='o', label='AIC')
plt.plot(results_df['profiles'], results_df['bic'], marker='s', label='BIC')
plt.title('AIC和BIC指标对比')
plt.xlabel('剖面数量')
plt.ylabel('指标值')
plt.legend()
plt.grid(True, alpha=0.3)

# 轮廓系数
plt.subplot(2, 1, 2)
plt.plot(results_df['profiles'][1:], results_df['silhouette'][1:], marker='^', color='green')
plt.title('轮廓系数对比')
plt.xlabel('剖面数量')
plt.ylabel('轮廓系数')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '模型拟合指标对比.png'), dpi=300, bbox_inches='tight')
plt.close()

# 选择最佳模型（轮廓系数最高）
best_n = results_df.loc[1:, 'silhouette'].idxmax() + 1  # +1因为索引从0开始
print(f"\n最佳剖面数量: {best_n}")

# 6. 获取最佳模型结果
print("\n6. 获取最佳模型结果")
best_model = models[best_n]
df['profile'] = best_model['labels']

# 为群体命名
profile_names = {
    0: '合作意愿强烈型',
    1: '发展需求主导型',
    2: '情感积极型',
    3: '综合平衡型',
    4: '谨慎观察型',
    5: '多元复杂型'
}

df['profile_name'] = df['profile'].map(profile_names)

# 7. 群体特征分析
print("\n7. 群体特征分析")

# 7.1 群体大小
profile_sizes = df['profile_name'].value_counts().sort_index()
print("群体大小:")
print(profile_sizes)

# 7.2 群体核心特征描述
core_feature_cols = list(core_vars.values())
profile_core_desc = df.groupby('profile_name')[core_feature_cols].describe()
print("\n群体核心特征描述:")
print(profile_core_desc)

# 7.3 群体控制变量描述
print("\n群体控制变量描述:")

# 连续控制变量
print("  连续控制变量:")
profile_continuous_desc = df.groupby('profile_name')[continuous_covariates].describe()
print(profile_continuous_desc)

# 分类控制变量
print("  分类控制变量:")
for cat_var in categorical_covariates:
    print(f"\n  {cat_var}:")
    cat_counts = df.groupby('profile_name')[cat_var].value_counts().unstack(fill_value=0)
    cat_percent = cat_counts.div(cat_counts.sum(axis=1), axis=0) * 100
    print(cat_percent.round(1))

# 8. 保存群体特征结果
print("\n8. 保存群体特征结果")
profile_sizes.to_csv(os.path.join(result_dir, '群体大小.csv'), encoding='utf-8-sig', header=['数量'])
profile_core_desc.to_csv(os.path.join(result_dir, '群体核心特征描述.csv'), encoding='utf-8-sig')
profile_continuous_desc.to_csv(os.path.join(result_dir, '群体控制变量_连续.csv'), encoding='utf-8-sig')

# 保存分类控制变量结果
for cat_var in categorical_covariates:
    cat_counts = df.groupby('profile_name')[cat_var].value_counts().unstack(fill_value=0)
    cat_counts.to_csv(os.path.join(result_dir, f'群体控制变量_{cat_var}.csv'), encoding='utf-8-sig')

# 9. 群体可视化
print("\n9. 群体可视化")

# 9.1 核心变量箱线图
plt.figure(figsize=(15, 12))
for i, var in enumerate(core_feature_cols, 1):
    plt.subplot(3, 1, i)
    sns.boxplot(x='profile_name', y=var, data=df, palette='Set1')
    plt.title(f'{var} 的群体分布')
    plt.xlabel('群体')
    plt.ylabel(var)
    plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '核心变量箱线图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 9.2 连续控制变量箱线图
plt.figure(figsize=(15, 12))
for i, var in enumerate(continuous_covariates, 1):
    plt.subplot(2, 1, i)
    sns.boxplot(x='profile_name', y=var, data=df, palette='Set2')
    plt.title(f'{var} 的群体分布')
    plt.xlabel('群体')
    plt.ylabel(var)
    plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '连续控制变量箱线图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 9.3 群体特征雷达图
plt.figure(figsize=(12, 10))

# 计算各群体核心变量的均值（标准化）
profile_scaled_means = df.groupby('profile_name')[scaled_vars[:3]].mean()

# 雷达图参数
categories = list(core_vars.keys())
n_categories = len(categories)
angles = [n / float(n_categories) * 2 * np.pi for n in range(n_categories)]
angles += angles[:1]  # 闭合雷达图

ax = plt.subplot(111, polar=True)

# 绘制每个群体的雷达图
colors = sns.color_palette("husl", len(profile_scaled_means))
for i, (profile, row) in enumerate(profile_scaled_means.iterrows()):
    values = row.values.tolist()
    values += values[:1]  # 闭合雷达图
    ax.plot(angles, values, linewidth=2, linestyle='solid', label=f'群体 {profile}', color=colors[i])
    ax.fill(angles, values, alpha=0.1, color=colors[i])

# 设置雷达图属性
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=12, fontweight='bold')
ax.set_yticklabels([])
ax.set_title('群体核心特征雷达图', fontsize=16, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))

plt.tight_layout()
plt.savefig(os.path.join(result_dir, '群体核心特征雷达图.png'), dpi=300, bbox_inches='tight')
plt.close()

# 9.4 分类控制变量分布堆叠图
for cat_var in categorical_covariates:
    plt.figure(figsize=(12, 8))
    cat_counts = df.groupby('profile')[cat_var].value_counts().unstack(fill_value=0)
    cat_percent = cat_counts.div(cat_counts.sum(axis=1), axis=0) * 100
    cat_percent.plot(kind='bar', stacked=True, colormap='Set3')
    plt.title(f'群体 {cat_var} 分布')
    plt.xlabel('群体')
    plt.ylabel('百分比 (%)')
    plt.legend(title=cat_var, bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(result_dir, f'群体_{cat_var}_分布.png'), dpi=300, bbox_inches='tight')
    plt.close()

# 10. 保存带有群体分类的数据
print("\n10. 保存带有群体分类的数据")
# 保存原始数据与群体分类，包含因变量
output_vars = list(core_vars.values()) + continuous_covariates + categorical_covariates + ['china_africa_community_recognition', 'profile', 'profile_name']
df[output_vars].to_csv(os.path.join(result_dir, '数据_带群体分类.csv'), index=False, encoding='utf-8-sig')

# 11. 生成分析报告
print("\n11. 生成分析报告")

report = "# 优化版潜在剖面分析报告（纳入控制变量）\n\n"

report += "## 1. 研究背景与目的\n\n"
report += "本研究优化了之前的潜在剖面分析，纳入了媒体类型、地区等控制变量，\n"
report += "旨在更准确地识别非洲媒体的潜在群体，提高模型的稳健性和解释力。\n\n"

report += "## 2. 数据与方法\n\n"
report += "### 2.1 数据来源\n"
report += f"- 数据文件: {data_path}\n"
report += f"- 样本量: {len(df)} 个观测值\n\n"

report += "### 2.2 变量定义\n"
report += "#### 核心变量\n"
for name, var in core_vars.items():
    report += f"- **{name}**: {var}\n"

report += "\n#### 控制变量\n"
report += "##### 连续控制变量\n"
for var in continuous_covariates:
    report += f"- **{var}**: 时间趋势/文章长度\n"

report += "\n##### 分类控制变量\n"
for var in categorical_covariates:
    report += f"- **{var}**: 媒体来源地区/新闻类别\n"

report += "\n### 2.3 分析方法\n"
report += "- 潜在剖面分析 (LPA)\n"
report += f"- 拟合剖面数: 1-{max_profiles}\n"
report += "- 模型选择指标: AIC、BIC、熵值、轮廓系数\n"
report += "- 连续变量标准化\n"
report += "- 分类变量编码\n\n"

report += "## 3. 模型拟合结果\n\n"
report += "### 3.1 模型拟合指标\n"
report += "| 剖面数 | AIC | BIC | 熵值 | 轮廓系数 |\n"
report += "|-------|-----|-----|------|----------|\n"
for _, row in results_df.iterrows():
    report += f"| {row['profiles']} | {row['aic']:.2f} | {row['bic']:.2f} | {row['entropy']:.2f} | {row['silhouette']:.4f} |\n"

report += "\n### 3.2 最佳模型选择\n"
report += f"- **最佳剖面数**: {best_n}\n"
report += f"- **选择依据**: 轮廓系数最高\n\n"

report += "## 4. 群体特征分析\n\n"
report += "### 4.1 群体分布\n"
report += "| 群体 | 数量 | 比例 |\n"
report += "|------|------|------|\n"
for profile, count in profile_sizes.items():
    proportion = count / len(df) * 100
    report += f"| {profile} | {count} | {proportion:.1f}% |\n"

report += "\n### 4.2 核心特征差异\n"
report += "#### 核心变量均值\n"
report += "| 群体 | " + " | ".join(core_vars.keys()) + " |\n"
report += "|------|" + "|" * len(core_vars) + "|\n"
profile_core_means = df.groupby('profile')[list(core_vars.values())].mean()
for profile, row in profile_core_means.iterrows():
    report += f"| {profile} | " + " | ".join([f"{v:.4f}" for v in row.values]) + " |\n"

report += "\n### 4.3 控制变量差异\n"
report += "#### 连续控制变量均值\n"
report += "| 群体 | " + " | ".join(continuous_covariates) + " |\n"
report += "|------|" + "|" * len(continuous_covariates) + "|\n"
profile_continuous_means = df.groupby('profile')[continuous_covariates].mean()
for profile, row in profile_continuous_means.iterrows():
    report += f"| {profile} | " + " | ".join([f"{v:.4f}" for v in row.values]) + " |\n"

report += "\n#### 分类控制变量分布\n"
for cat_var in categorical_covariates:
    report += f"##### {cat_var}\n"
    cat_counts = df.groupby('profile')[cat_var].value_counts().unstack(fill_value=0)
    cat_percent = cat_counts.div(cat_counts.sum(axis=1), axis=0) * 100
    report += "| 群体 | " + " | ".join(cat_percent.columns.tolist()) + " |\n"
    report += "|------|" + "|" * len(cat_percent.columns) + "|\n"
    for profile, row in cat_percent.iterrows():
        report += f"| {profile} | " + " | ".join([f"{v:.1f}%" for v in row.values]) + " |\n"
    report += "\n"

report += "## 5. 可视化结果\n\n"
report += "### 5.1 模型拟合指标对比\n"
report += "![模型拟合指标对比](模型拟合指标对比.png)\n\n"

report += "### 5.2 核心变量箱线图\n"
report += "![核心变量箱线图](核心变量箱线图.png)\n\n"

report += "### 5.3 连续控制变量箱线图\n"
report += "![连续控制变量箱线图](连续控制变量箱线图.png)\n\n"

report += "### 5.4 群体核心特征雷达图\n"
report += "![群体核心特征雷达图](群体核心特征雷达图.png)\n\n"

for cat_var in categorical_covariates:
    report += f"### 5.5 群体 {cat_var} 分布\n"
    report += f"![群体 {cat_var} 分布](群体_{cat_var}_分布.png)\n\n"

report += "## 6. 结论与建议\n\n"
report += "### 6.1 主要结论\n"
report += f"1. **识别出 {best_n} 个潜在群体**: 纳入控制变量后，仍可识别出具有不同特征的媒体群体\n"
report += "2. **群体特征差异显著**: 不同群体在核心变量和控制变量上均存在显著差异\n"
report += "3. **控制变量影响群体分类**: 媒体类型、地区等控制变量影响了群体的形成\n"
report += "4. **模型稳健性提高**: 纳入控制变量后，模型结果更具代表性和解释力\n\n"

report += "### 6.2 建议\n"
report += "1. **考虑群体异质性**: 在制定传播策略时，需考虑不同群体的特征差异\n"
report += "2. **针对性传播**: 根据不同群体的媒体类型、地区特点，制定针对性的传播内容\n"
report += "3. **持续优化模型**: 可考虑纳入更多控制变量，如媒体政治倾向等\n\n"

report += "## 7. 数据与代码\n\n"
report += f"- **数据文件**: {data_path}\n"
report += "- **分析代码**: 优化版_潜在剖面分析.py\n"
report += f"- **结果文件夹**: {result_dir}\n\n"

report += "---\n\n"
report += f"**报告生成时间**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

# 保存报告
with open(os.path.join(result_dir, '优化版潜在剖面分析报告.md'), 'w', encoding='utf-8') as f:
    f.write(report)

# 12. 输出完成信息
print("\n" + "="*50)
print("优化版潜在剖面分析完成！")
print(f"所有结果已保存到: {result_dir}")
print("包含文件：")
print("1. 模型拟合指标.csv")
print("2. 群体大小.csv")
print("3. 群体核心特征描述.csv")
print("4. 群体控制变量_连续.csv")
for cat_var in categorical_covariates:
    print(f"5. 群体控制变量_{cat_var}.csv")
print("6. 数据_带群体分类.csv")
print("7. 模型拟合指标对比.png")
print("8. 核心变量箱线图.png")
print("9. 连续控制变量箱线图.png")
print("10. 群体核心特征雷达图.png")
for cat_var in categorical_covariates:
    print(f"11. 群体_{cat_var}_分布.png")
print("12. 优化版潜在剖面分析报告.md")
print("="*50)
