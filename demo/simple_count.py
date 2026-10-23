import json

# 读取JSON文件并统计数据数量
def count_json_entries(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 统计数据数量
    count = len(data)
    print(f"✓ JSON文件中共有 {count} 条数据")
    
    # 检查前5条数据的结构
    print("\n前5条数据的结构:")
    for i, item in enumerate(data[:5]):
        print(f"\n第 {i+1} 条数据:")
        print(f"  类型: {type(item).__name__}")
        if isinstance(item, dict):
            print(f"  键: {list(item.keys())}")
        elif isinstance(item, str):
            print(f"  内容（前100字符）: {item[:100]}...")
        else:
            print(f"  内容: {item}")

# 主函数
def main():
    file_path = '清洗数据.json'
    count_json_entries(file_path)

if __name__ == "__main__":
    main()