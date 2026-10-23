import json

# 检查原始数据的结构
print("=== 检查原始数据结构 ===")

raw_data_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/原始数据.json'
with open(raw_data_path, 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

print(f"原始数据记录数: {len(raw_data)}")

# 查看第一条数据的结构
if raw_data:
    first_item = raw_data[0]
    print("\n第一条数据的字段:")
    for key, value in first_item.items():
        print(f"  {key}: {type(value).__name__}")
        # 显示前100个字符的内容
        if isinstance(value, str):
            print(f"     内容前100字符: {value[:100]}...")
        elif isinstance(value, list):
            print(f"     列表长度: {len(value)}")
        elif isinstance(value, dict):
            print(f"     字典键: {list(value.keys())}")

# 查看数据的字段分布
print("\n=== 字段分布分析 ===")
field_counts = {}
for item in raw_data[:100]:  # 只检查前100条数据
    for key in item.keys():
        field_counts[key] = field_counts.get(key, 0) + 1

print("字段出现次数:")
for field, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {field}: {count} 次")
