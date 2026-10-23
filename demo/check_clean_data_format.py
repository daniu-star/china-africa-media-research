import json

# 检查清洗数据目录下的其他JSON文件
print("=== 检查清洗数据目录下的其他JSON文件 ===")

json_files = [
    'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/清洗数据.json',
    'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/高级遍历数据.json'
]

for file_path in json_files:
    print(f"\n=== 检查文件: {file_path.split('/')[-1]} ===")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"成功解析为{type(data).__name__}")
        
        if isinstance(data, list):
            print(f"数组长度: {len(data)}")
            # 查找第一条字典类型的数据
            dict_items = [item for item in data[:100] if isinstance(item, dict)]
            if dict_items:
                first_dict = dict_items[0]
                print(f"找到字典数据，前100条中有{len(dict_items)}个字典")
                print(f"字典包含的字段: {list(first_dict.keys())}")
                # 显示第一条字典的内容
                print("第一条字典内容:")
                for key, value in first_dict.items():
                    if isinstance(value, str):
                        print(f"  {key}: {value[:100]}...")
                    else:
                        print(f"  {key}: {type(value).__name__}")
            else:
                print("前100条数据中没有字典类型")
        elif isinstance(data, dict):
            print(f"字典键: {list(data.keys())}")
            # 检查是否包含data字段
            if 'data' in data and isinstance(data['data'], list):
                print(f"data字段是数组，长度: {len(data['data'])}")
                if data['data']:
                    first_item = data['data'][0]
                    print(f"data数组第一条类型: {type(first_item).__name__}")
                    if isinstance(first_item, dict):
                        print(f"data数组第一条字典字段: {list(first_item.keys())[:5]}")
    except Exception as e:
        print(f"解析错误: {e}")
