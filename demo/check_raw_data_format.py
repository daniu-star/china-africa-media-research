import json

# 检查原始数据的完整格式
print("=== 检查原始数据格式 ===")

raw_data_path = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/原始数据.json'

# 先读取前1000个字符查看文件头
with open(raw_data_path, 'r', encoding='utf-8') as f:
    file_header = f.read(1000)

print("文件头1000字符:")
print(file_header)
print("\n=== 文件格式分析 ===")

# 尝试使用不同的方式解析
print("\n=== 尝试解析为JSON数组 ===")
try:
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"成功解析为{type(data).__name__}")
    if isinstance(data, list):
        print(f"数组长度: {len(data)}")
        # 查看前10条数据的类型
        print("前10条数据的类型:")
        for i, item in enumerate(data[:10]):
            print(f"  {i}: {type(item).__name__}")
            if isinstance(item, int):
                print(f"     整数值: {item}")
            elif isinstance(item, dict):
                print(f"     字典键: {list(item.keys())[:5]}")
    elif isinstance(data, dict):
        print(f"字典键: {list(data.keys())}")
except Exception as e:
    print(f"解析错误: {e}")
