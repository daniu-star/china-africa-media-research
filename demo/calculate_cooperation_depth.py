import pandas as pd
import numpy as np
import re
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 设置结果保存目录
output_dir = 'c:/Users/13067/Desktop/论文/非洲/demo/合作纵深性分析结果'
os.makedirs(output_dir, exist_ok=True)

# 1. 构建关键词库
def build_keyword_libraries():
    """构建表征长期战略和多元主体的关键词库"""
    
    # 长期战略词库：包含表示长期、战略、可持续等含义的词汇
    long_term_strategic = {
        'long-term': '长期',
        'long term': '长期',
        'longterm': '长期',
        'strategic': '战略',
        'strategy': '战略',
        'strategies': '战略',
        'strategically': '战略',
        'sustainable': '可持续',
        'sustainability': '可持续',
        'sustainably': '可持续',
        'enduring': '持久',
        'endurance': '持久',
        'persistent': '持久',
        'persistence': '持久',
        'lasting': '持久',
        'permanent': '永久',
        'permanence': '永久',
        'future-oriented': '面向未来',
        'future oriented': '面向未来',
        'futureoriented': '面向未来',
        'forward-looking': '前瞻性',
        'forward looking': '前瞻性',
        'forwardlooking': '前瞻性',
        'vision': '愿景',
        'visionary': '愿景',
        'visioning': '愿景',
        'perspective': '视角',
        'perspectives': '视角',
        'holistic': '整体',
        'comprehensive': '全面',
        'integrated': '整合',
        'integration': '整合',
        'systematic': '系统',
        'system': '系统',
        'systems': '系统',
        'framework': '框架',
        'frameworks': '框架',
        'blueprint': '蓝图',
        'roadmap': '路线图',
        'road map': '路线图',
        'roadmap': '路线图',
        'action plan': '行动计划',
        'action_plan': '行动计划',
        'actionplan': '行动计划',
        'partnership': '伙伴关系',
        'partnerships': '伙伴关系',
        'alliance': '联盟',
        'alliances': '联盟',
        'cooperation': '合作',
        'cooperative': '合作',
        'collaboration': '协作',
        'collaborative': '协作',
        'joint': '联合',
        'mutual': ' mutual',
        'reciprocal': '互惠',
        'reciprocal': '互惠',
        'win-win': '双赢',
        'win win': '双赢',
        'winwin': '双赢'
    }
    
    # 多元主体词库：包含表示不同主体互动的词汇
    multi_agents = {
        # 政府主体
        'government': '政府',
        'governments': '政府',
        'state': '国家',
        'states': '国家',
        'nation': '国家',
        'nations': '国家',
        'governmental': '政府',
        'official': '官方',
        'officials': '官方',
        'authority': '权威',
        'authorities': '权威',
        'ministry': '部门',
        'ministries': '部门',
        'department': '部门',
        'departments': '部门',
        'agency': '机构',
        'agencies': '机构',
        'administration': '行政',
        'administrations': '行政',
        
        # 企业主体
        'enterprise': '企业',
        'enterprises': '企业',
        'company': '公司',
        'companies': '公司',
        'corporation': '企业',
        'corporations': '企业',
        'business': '商业',
        'businesses': '商业',
        'firm': '公司',
        'firms': '公司',
        'industry': '行业',
        'industries': '行业',
        'private sector': '私营部门',
        'private_sector': '私营部门',
        'privatesector': '私营部门',
        'public sector': '公共部门',
        'public_sector': '公共部门',
        'publicsector': '公共部门',
        'small and medium enterprises': '中小企业',
        'smes': '中小企业',
        
        # 学术和研究机构
        'university': '大学',
        'universities': '大学',
        'college': '学院',
        'colleges': '学院',
        'institute': '研究所',
        'institutes': '研究所',
        'research': '研究',
        'researcher': '研究人员',
        'researchers': '研究人员',
        'academy': '学院',
        'academies': '学院',
        'academic': '学术',
        'academics': '学术界',
        'think tank': '智库',
        'think_tank': '智库',
        'thinktank': '智库',
        'think tanks': '智库',
        'think_tanks': '智库',
        'thinktanks': '智库',
        'research center': '研究中心',
        'research_center': '研究中心',
        'researchcenter': '研究中心',
        'research centres': '研究中心',
        'research_centres': '研究中心',
        'researchcentres': '研究中心',
        
        # 社会组织
        'ngo': '非政府组织',
        'ngos': '非政府组织',
        'civil society': '公民社会',
        'civil_society': '公民社会',
        'civilsociety': '公民社会',
        'organization': '组织',
        'organizations': '组织',
        'association': '协会',
        'associations': '协会',
        'foundation': '基金会',
        'foundations': '基金会',
        'charity': '慈善',
        'charities': '慈善',
        'nonprofit': '非营利',
        'non-profit': '非营利',
        'non_profit': '非营利',
        'nonprofits': '非营利',
        'non-profits': '非营利',
        'non_profits': '非营利',
        
        # 教育和文化主体
        'education': '教育',
        'educational': '教育',
        'school': '学校',
        'schools': '学校',
        'teacher': '教师',
        'teachers': '教师',
        'student': '学生',
        'students': '学生',
        'youth': '青年',
        'youths': '青年',
        'young people': '年轻人',
        'young_people': '年轻人',
        'youngpeople': '年轻人',
        'culture': '文化',
        'cultural': '文化',
        'art': '艺术',
        'arts': '艺术',
        'artist': '艺术家',
        'artists': '艺术家',
        'cultural exchange': '文化交流',
        'cultural_exchange': '文化交流',
        'culturalexchange': '文化交流',
        'educational exchange': '教育交流',
        'educational_exchange': '教育交流',
        'educationalexchange': '教育交流',
        'student exchange': '学生交流',
        'student_exchange': '学生交流',
        'studentexchange': '学生交流',
        'youth exchange': '青年交流',
        'youth_exchange': '青年交流',
        'youthexchange': '青年交流',
        
        # 科技和创新主体
        'technology': '技术',
        'technologies': '技术',
        'tech': '科技',
        'science': '科学',
        'scientific': '科学',
        'scientist': '科学家',
        'scientists': '科学家',
        'innovation': '创新',
        'innovative': '创新',
        'innovator': '创新者',
        'innovators': '创新者',
        'tech transfer': '技术转移',
        'tech_transfer': '技术转移',
        'techtransfer': '技术转移',
        'technology transfer': '技术转移',
        'technology_transfer': '技术转移',
        'technologytransfer': '技术转移',
        'r&d': '研发',
        'rd': '研发',
        'research and development': '研发',
        'research_and_development': '研发',
        'researchanddevelopment': '研发',
        
        # 农业和农村主体
        'agriculture': '农业',
        'agricultural': '农业',
        'farmer': '农民',
        'farmers': '农民',
        'rural': '农村',
        'village': '村庄',
        'villages': '村庄',
        'agricultural cooperation': '农业合作',
        'agricultural_cooperation': '农业合作',
        'agriculturalcooperation': '农业合作',
        
        # 卫生和健康主体
        'health': '卫生',
        'healthcare': '医疗保健',
        'medical': '医疗',
        'medicine': '医学',
        'doctor': '医生',
        'doctors': '医生',
        'nurse': '护士',
        'nurses': '护士',
        'hospital': '医院',
        'hospitals': '医院',
        'health cooperation': '卫生合作',
        'health_cooperation': '卫生合作',
        'healthcooperation': '卫生合作'
    }
    
    return long_term_strategic, multi_agents

# 2. 计算每篇报道的合作纵深性指数
def calculate_cooperation_depth():
    """计算每篇报道的合作纵深性指数"""
    
    print("=== 合作纵深性指数计算开始 ===")
    
    # 读取清洗数据
    clean_data_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/清洗数据.json'
    print(f"读取清洗数据: {clean_data_path}")
    with open(clean_data_path, 'r', encoding='utf-8') as f:
        clean_data = json.load(f)
    print(f"清洗数据记录数: {len(clean_data)}")
    
    # 过滤掉非字典类型的数据
    dict_data = [item for item in clean_data if isinstance(item, dict)]
    print(f"过滤后字典记录数: {len(dict_data)}")
    
    # 转换为DataFrame
    df = pd.DataFrame(dict_data)
    print(f"转换后记录数: {len(df)}")
    
    # 创建content列（如果不存在）
    if 'content' not in df.columns:
        df['content'] = ''
    
    # 创建combined_text列
    df['combined_text'] = df['title'].fillna('') + ' ' + df['summary'].fillna('') + ' ' + df['content'].fillna('')
    
    # 创建processed_text列（简化处理）
    def simple_preprocess(text):
        if not isinstance(text, str):
            return ''
        # 转换为小写
        text = text.lower()
        # 移除特殊字符，只保留字母、数字和空格
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        # 多个空格替换为一个
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    print("处理文本...")
    df['processed_text'] = df['combined_text'].apply(simple_preprocess)
    
    # 构建关键词库
    long_term_strategic, multi_agents = build_keyword_libraries()
    print(f"长期战略词库大小: {len(long_term_strategic)} 个词")
    print(f"多元主体词库大小: {len(multi_agents)} 个词")
    
    # 提取关键词列表
    long_term_words = list(long_term_strategic.keys())
    multi_agent_words = list(multi_agents.keys())
    
    # 计算每篇报道的长期战略词频
    def count_long_term_words(text):
        """计算文本中包含的长期战略词频"""
        if not isinstance(text, str) or not text:
            return 0
        
        text_lower = text.lower()
        count = 0
        for word in long_term_words:
            # 使用简单的字符串匹配，确保能够匹配到关键词
            # 暂时不使用正则表达式边界匹配，避免匹配不到
            if word.lower() in text_lower:
                count += 1
        return count
    
    # 判断是否提及多元主体互动
    def has_multi_agent_interaction(text):
        """计算文本中提及的多元主体类别数量"""
        if not isinstance(text, str) or not text:
            return 0
        
        text_lower = text.lower()
        
        # 简化的多元主体词库，使用简单的字符串匹配
        multi_agent_words_simple = ['government', 'enterprise', 'company', 'university', 'research', 
                                   'ngo', 'education', 'cultural', 'technology', 'agriculture', 
                                   'health', 'medical', 'state', 'nation', 'business', 'firm']
        
        # 统计提及的多元主体数量
        count = 0
        for word in multi_agent_words_simple:
            if word in text_lower:
                count += 1
        return count
    
    # 应用函数计算指标
    print("计算长期战略词频...")
    df['long_term_word_count'] = df['processed_text'].apply(count_long_term_words)
    
    print("判断多元主体互动...")
    df['has_multi_agent_interaction'] = df['processed_text'].apply(has_multi_agent_interaction)
    
    # 标准化指标
    print("标准化指标...")
    
    # 1. 对长期战略词频进行对数变换处理长尾分布（方案一建议）
    df['long_term_word_count_log'] = np.log1p(df['long_term_word_count'])  # log1p = log(1 + x)，处理0值
    
    # 2. 采用百分位数赋值（方案一建议）
    # 将长期战略词频转换为百分位数（0-100）
    df['long_term_percentile'] = df['long_term_word_count_log'].rank(pct=True) * 100
    
    # 将多元主体互动转换为百分位数（0-100）
    df['multi_agent_percentile'] = df['has_multi_agent_interaction'].rank(pct=True) * 100
    
    # 3. 计算综合指数：采用百分位数平均值（方案一建议）
    df['cooperation_depth_index'] = (df['long_term_percentile'] + df['multi_agent_percentile']) / 200  # 归一化到0-1范围
    
    # 4. 保存中间结果
    df['long_term_word_count_scaled'] = df['long_term_percentile'] / 100  # 归一化到0-1范围
    df['has_multi_agent_interaction_scaled'] = df['multi_agent_percentile'] / 100  # 归一化到0-1范围
    
    # 保存中间结果和最终结果
    print("保存结果...")
    
    # 定义输出路径
    output_csv_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_demand_perception.csv'
    
    # 保存中间结果
    intermediate_cols = ['long_term_word_count', 'has_multi_agent_interaction', 
                        'long_term_word_count_scaled', 'has_multi_agent_interaction_scaled', 
                        'cooperation_depth_index']
    intermediate_df = df[intermediate_cols]
    intermediate_df.to_csv(os.path.join(output_dir, '合作纵深性指数中间结果.csv'), index=False, encoding='utf-8-sig')
    
    # 保存最终结果
    df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"最终结果保存到: {output_csv_path}")
    
    # 生成统计报告
    generate_statistical_report(df, output_dir)
    
    # 暂时跳过可视化图表生成，加快执行速度
    # generate_visualizations(df, output_dir)
    
    print("=== 合作纵深性指数计算完成 ===")

# 3. 生成统计报告
def generate_statistical_report(df, output_dir):
    """生成合作纵深性指数的统计报告"""
    
    report_path = os.path.join(output_dir, '合作纵深性指数统计报告.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=== 合作纵深性指数统计报告 ===\n\n")
        
        # 数据基本信息
        f.write(f"数据总量: {len(df)} 条记录\n")
        f.write(f"包含合作纵深性指数的记录数: {df['cooperation_depth_index'].count()} 条\n\n")
        
        # 长期战略词频统计
        f.write("1. 长期战略词频统计\n")
        f.write(f"   平均值: {df['long_term_word_count'].mean():.4f}\n")
        f.write(f"   中位数: {df['long_term_word_count'].median():.4f}\n")
        f.write(f"   标准差: {df['long_term_word_count'].std():.4f}\n")
        f.write(f"   最小值: {df['long_term_word_count'].min():.4f}\n")
        f.write(f"   最大值: {df['long_term_word_count'].max():.4f}\n\n")
        
        # 多元主体互动统计
        f.write("2. 多元主体互动统计\n")
        f.write(f"   平均提及主体类别数: {df['has_multi_agent_interaction'].mean():.4f}\n")
        f.write(f"   中位数: {df['has_multi_agent_interaction'].median():.4f}\n")
        f.write(f"   标准差: {df['has_multi_agent_interaction'].std():.4f}\n")
        f.write(f"   最大值提及类别数: {df['has_multi_agent_interaction'].max():.0f}\n\n")
        
        # 合作纵深性指数统计
        f.write("3. 合作纵深性指数统计\n")
        f.write(f"   平均值: {df['cooperation_depth_index'].mean():.4f}\n")
        f.write(f"   中位数: {df['cooperation_depth_index'].median():.4f}\n")
        f.write(f"   标准差: {df['cooperation_depth_index'].std():.4f}\n")
        f.write(f"   最小值: {df['cooperation_depth_index'].min():.4f}\n")
        f.write(f"   最大值: {df['cooperation_depth_index'].max():.4f}\n\n")
        
        # 合作纵深性指数分布
        f.write("4. 合作纵深性指数分布\n")
        bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        counts, edges = np.histogram(df['cooperation_depth_index'], bins=bins)
        for i in range(len(counts)):
            f.write(f"   {edges[i]:.1f}-{edges[i+1]:.1f}: {counts[i]} 条 ({counts[i]/len(df)*100:.2f}%)\n")
        f.write(f"\n")
        
        # 相关性分析
        f.write("5. 相关性分析\n")
        corr_matrix = df[['long_term_word_count', 'has_multi_agent_interaction', 'cooperation_depth_index']].corr()
        f.write(f"   长期战略词频与合作纵深性指数相关系数: {corr_matrix.loc['long_term_word_count', 'cooperation_depth_index']:.4f}\n")
        f.write(f"   多元主体互动与合作纵深性指数相关系数: {corr_matrix.loc['has_multi_agent_interaction', 'cooperation_depth_index']:.4f}\n")
        f.write(f"   长期战略词频与多元主体互动相关系数: {corr_matrix.loc['long_term_word_count', 'has_multi_agent_interaction']:.4f}\n")

# 4. 生成可视化图表
def generate_visualizations(df, output_dir):
    """生成合作纵深性指数的可视化图表"""
    print("生成可视化图表...")
    
    # 设置图表风格
    sns.set(style="whitegrid", font_scale=1.2)
    
    # 1. 合作纵深性指数直方图
    plt.figure(figsize=(12, 8))
    sns.histplot(df['cooperation_depth_index'], bins=30, kde=True, color='skyblue')
    plt.title('合作纵深性指数分布直方图', fontsize=16)
    plt.xlabel('合作纵深性指数', fontsize=14)
    plt.ylabel('报道数量', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '合作纵深性指数直方图.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. 合作纵深性指数箱线图
    plt.figure(figsize=(10, 8))
    sns.boxplot(y=df['cooperation_depth_index'], color='lightgreen', showmeans=True)
    plt.title('合作纵深性指数箱线图', fontsize=16)
    plt.ylabel('合作纵深性指数', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '合作纵深性指数箱线图.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. 长期战略词频与多元主体互动散点图
    plt.figure(figsize=(12, 8))
    # 使用hue但不使用colorbar，改为使用legend
    sns.scatterplot(x='long_term_word_count', y='has_multi_agent_interaction', 
                    hue='cooperation_depth_index', size='cooperation_depth_index',
                    data=df, palette='viridis', alpha=0.7, sizes=(20, 200),
                    legend='brief')
    plt.title('长期战略词频与多元主体互动散点图', fontsize=16)
    plt.xlabel('长期战略词频', fontsize=14)
    plt.ylabel('提及的主体类别数', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(title='合作纵深性指数', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '长期战略词频与多元主体互动散点图.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. 合作纵深性指数分布累积图
    plt.figure(figsize=(12, 8))
    sns.ecdfplot(df['cooperation_depth_index'], color='purple')
    plt.title('合作纵深性指数累积分布', fontsize=16)
    plt.xlabel('合作纵深性指数', fontsize=14)
    plt.ylabel('累积比例', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '合作纵深性指数累积分布.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 5. 各类主体提及情况条形图
    # 重新计算各类主体提及情况
    def count_agent_categories(text):
        if not isinstance(text, str) or not text:
            return {}
        
        text_lower = text.lower()
        agent_categories = {
            '政府': [
                'government', 'governments', 'state', 'states', 'nation', 'nations',
                'governmental', 'official', 'officials', 'authority', 'authorities',
                'ministry', 'ministries', 'department', 'departments', 'agency', 'agencies',
                'administration', 'administrations'
            ],
            '企业': [
                'enterprise', 'enterprises', 'company', 'companies', 'corporation', 'corporations',
                'business', 'businesses', 'firm', 'firms', 'industry', 'industries',
                'private sector', 'private_sector', 'privatesector', 'public sector',
                'public_sector', 'publicsector', 'small and medium enterprises', 'smes'
            ],
            '学术研究': [
                'university', 'universities', 'college', 'colleges', 'institute', 'institutes',
                'research', 'researcher', 'researchers', 'academy', 'academies', 'academic',
                'academics', 'think tank', 'think_tank', 'thinktank', 'think tanks',
                'think_tanks', 'thinktanks', 'research center', 'research_center',
                'researchcenter', 'research centres', 'research_centres', 'researchcentres'
            ],
            '社会组织': [
                'ngo', 'ngos', 'civil society', 'civil_society', 'civilsociety',
                'organization', 'organizations', 'association', 'associations',
                'foundation', 'foundations', 'charity', 'charities', 'nonprofit',
                'non-profit', 'non_profit', 'nonprofits', 'non-profits', 'non_profits'
            ],
            '教育文化': [
                'education', 'educational', 'school', 'schools', 'teacher', 'teachers',
                'student', 'students', 'youth', 'youths', 'young people', 'young_people',
                'youngpeople', 'culture', 'cultural', 'art', 'arts', 'artist', 'artists',
                'cultural exchange', 'cultural_exchange', 'culturalexchange',
                'educational exchange', 'educational_exchange', 'educationalexchange',
                'student exchange', 'student_exchange', 'studentexchange',
                'youth exchange', 'youth_exchange', 'youthexchange'
            ],
            '科技创新': [
                'technology', 'technologies', 'tech', 'science', 'scientific', 'scientist',
                'scientists', 'innovation', 'innovative', 'innovator', 'innovators',
                'tech transfer', 'tech_transfer', 'techtransfer', 'technology transfer',
                'technology_transfer', 'technologytransfer', 'r&d', 'rd',
                'research and development', 'research_and_development', 'researchanddevelopment'
            ]
        }
        
        category_counts = {}
        for category, words in agent_categories.items():
            for word in words:
                pattern = r'\b' + re.escape(word.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    category_counts[category] = category_counts.get(category, 0) + 1
                    break
        return category_counts
    
    # 计算各类主体提及次数
    agent_count = {}
    for text in df['processed_text']:
        categories = count_agent_categories(text)
        for category in categories:
            agent_count[category] = agent_count.get(category, 0) + 1
    
    # 生成条形图
    plt.figure(figsize=(12, 8))
    categories = list(agent_count.keys())
    counts = list(agent_count.values())
    
    # 按提及次数排序
    sorted_pairs = sorted(zip(counts, categories), reverse=True)
    counts, categories = zip(*sorted_pairs)
    
    sns.barplot(x=list(categories), y=list(counts), palette='Set3')
    plt.title('各类主体提及情况条形图', fontsize=16)
    plt.xlabel('主体类别', fontsize=14)
    plt.ylabel('提及次数', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '各类主体提及情况条形图.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print("可视化图表生成完成")

# 主函数
def main():
    calculate_cooperation_depth()

if __name__ == "__main__":
    main()
