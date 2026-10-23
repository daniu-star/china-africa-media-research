import json
import pandas as pd
import re

# 测试关键词匹配问题
print("=== 调试关键词匹配 ===")

# 读取少量原始数据进行测试
raw_data_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/原始数据.json'
with open(raw_data_path, 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# 只取前10条数据测试
test_data = raw_data[:10]
print(f"测试数据量: {len(test_data)}")

df = pd.DataFrame(test_data)

# 确保必要的列存在
if 'title' not in df.columns:
    df['title'] = ''
if 'summary' not in df.columns:
    df['summary'] = ''
if 'content' not in df.columns:
    df['content'] = ''

# 创建combined_text列
df['combined_text'] = df['title'].fillna('') + ' ' + df['summary'].fillna('') + ' ' + df['content'].fillna('')

# 简单的文本处理
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

# 处理文本
df['processed_text'] = df['combined_text'].apply(simple_preprocess)

# 显示样本文本内容
print("\n=== 样本文本内容 ===")
for i, row in df.iterrows():
    print(f"样本{i}:")
    print(f"原始标题: {row['title'][:100]}...")
    print(f"处理后文本: {row['processed_text'][:200]}...")
    print(f"文本长度: {len(row['processed_text'])}")
    print()

# 测试关键词匹配
print("\n=== 关键词匹配测试 ===")

# 测试长期战略词匹配
long_term_words = ['long-term', 'strategic', 'strategy', 'sustainable', 'cooperation', 'partnership', 'alliance', 'joint']
print(f"测试关键词: {long_term_words[:5]}...")

def test_keyword_match(text):
    if not isinstance(text, str) or not text:
        return []
    
    matched_words = []
    for word in long_term_words:
        if word in text:
            matched_words.append(word)
    return matched_words

df['matched_long_term'] = df['processed_text'].apply(test_keyword_match)

df['matched_count'] = df['matched_long_term'].apply(len)

print("\n=== 匹配结果 ===")
for i, row in df.iterrows():
    print(f"样本{i}:")
    print(f"匹配的关键词: {row['matched_long_term']}")
    print(f"匹配数量: {row['matched_count']}")
    print(f"处理后文本: {row['processed_text'][:200]}...")
    print()

# 测试多元主体关键词
print("\n=== 多元主体关键词测试 ===")
multi_agent_words = ['government', 'enterprise', 'company', 'university', 'research', 'ngo']

def test_multi_agent_match(text):
    if not isinstance(text, str) or not text:
        return []
    
    matched_words = []
    for word in multi_agent_words:
        if word in text:
            matched_words.append(word)
    return matched_words

df['matched_multi_agent'] = df['processed_text'].apply(test_multi_agent_match)
df['multi_agent_count'] = df['matched_multi_agent'].apply(len)

for i, row in df.iterrows():
    print(f"样本{i}:")
    print(f"匹配的多元主体关键词: {row['matched_multi_agent']}")
    print(f"匹配数量: {row['multi_agent_count']}")
    print()

# 检查文本处理是否有问题
print("\n=== 文本处理检查 ===")
print("是否有空文本:", any(df['processed_text'] == ''))
print("文本长度统计:")
print(df['processed_text'].apply(len).describe())
