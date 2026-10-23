import pandas as pd
import re

# 读取数据
df = pd.read_csv('c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\清洗数据\\enhanced_data_with_demand_perception.csv', low_memory=False)

print('=== 合作纵深性指数为0的原因分析 ===')
print('总记录数:', len(df))
print('指数为0的记录数:', len(df[df['cooperation_depth_index'] == 0.0]))
print('指数为0的比例:', len(df[df['cooperation_depth_index'] == 0.0])/len(df)*100:.2f, '%')
print()

# 分析文本长度
df['text_length'] = df['processed_text'].apply(lambda x: len(str(x)))
print('=== 文本长度分析 ===')
print('文本长度统计:')
print(df['text_length'].describe())
print()

# 分析文本长度与指数的关系
print('文本长度小于50的记录数:', len(df[df['text_length'] < 50]))
print('其中指数为0的比例:', len(df[(df['text_length'] < 50) & (df['cooperation_depth_index'] == 0.0)])/len(df[df['text_length'] < 50])*100:.2f, '%')
print()

# 分析关键词匹配情况
print('=== 关键词匹配分析 ===')
print('长期战略词频为0的记录数:', len(df[df['long_term_word_count'] == 0]))
print('多元主体互动为0的记录数:', len(df[df['has_multi_agent_interaction'] == 0]))
print('两者都为0的记录数:', len(df[(df['long_term_word_count'] == 0) & (df['has_multi_agent_interaction'] == 0)]))
print('指数为0且两者都为0的记录数:', len(df[(df['cooperation_depth_index'] == 0.0) & (df['long_term_word_count'] == 0) & (df['has_multi_agent_interaction'] == 0)]))
print()

# 查看样本数据
print('=== 指数为0的样本分析 ===')
sample_size = 3
zero_samples = df[df['cooperation_depth_index'] == 0.0].head(sample_size)

for i, row in zero_samples.iterrows():
    print(f'样本{i+1}:')
    print(f'  文本长度: {len(str(row["processed_text"]))}')
    print(f'  长期战略词频: {row["long_term_word_count"]}')
    print(f'  多元主体互动: {row["has_multi_agent_interaction"]}')
    print(f'  文本内容: {str(row["processed_text"])[:200]}...')
    print('-' * 50)

# 分析关键词库覆盖情况
print('=== 关键词库分析 ===')
# 从原始代码中提取关键词库
def build_keyword_libraries():
    long_term_strategic = {
        'long-term': '长期', 'long term': '长期', 'longterm': '长期',
        'strategic': '战略', 'strategy': '战略', 'strategies': '战略', 'strategically': '战略',
        'sustainable': '可持续', 'sustainability': '可持续', 'sustainably': '可持续',
        'enduring': '持久', 'endurance': '持久', 'persistent': '持久', 'persistence': '持久',
        'lasting': '持久', 'permanent': '永久', 'permanence': '永久',
        'future-oriented': '面向未来', 'future oriented': '面向未来', 'futureoriented': '面向未来',
        'forward-looking': '前瞻性', 'forward looking': '前瞻性', 'forwardlooking': '前瞻性',
        'vision': '愿景', 'visionary': '愿景', 'visioning': '愿景',
        'perspective': '视角', 'perspectives': '视角',
        'holistic': '整体', 'comprehensive': '全面',
        'integrated': '整合', 'integration': '整合',
        'systematic': '系统', 'system': '系统', 'systems': '系统',
        'framework': '框架', 'frameworks': '框架',
        'blueprint': '蓝图',
        'roadmap': '路线图', 'road map': '路线图', 'roadmap': '路线图',
        'action plan': '行动计划', 'action_plan': '行动计划', 'actionplan': '行动计划',
        'partnership': '伙伴关系', 'partnerships': '伙伴关系',
        'alliance': '联盟', 'alliances': '联盟',
        'cooperation': '合作', 'cooperative': '合作',
        'collaboration': '协作', 'collaborative': '协作',
        'joint': '联合',
        'mutual': 'mutual',
        'reciprocal': '互惠', 'reciprocal': '互惠',
        'win-win': '双赢', 'win win': '双赢', 'winwin': '双赢'
    }
    return list(long_term_strategic.keys())

long_term_words = build_keyword_libraries()
print(f'长期战略词库大小: {len(long_term_words)} 个词')
print('部分关键词:', long_term_words[:10])
print()

# 分析可能的改进方向
print('=== 可能的改进方向 ===')
print('1. 检查文本质量: 部分文本可能过短或为空，无法包含足够的关键词')
print('2. 扩展关键词库: 增加更多相关的长期战略和多元主体词汇')
print('3. 调整匹配规则: 考虑使用更灵活的匹配方式，如部分匹配或同义词扩展')
print('4. 分析文本内容: 部分报道可能确实没有涉及长期战略或多元主体互动')
print('5. 调整权重分配: 考虑对不同类型的报道采用不同的权重')
