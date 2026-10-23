import json

# 读取JSON文件并检查数据类型分布
def check_data_types(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 统计总数据量
    total_count = len(data)
    print(f"总数据量: {total_count} 条")
    
    # 统计不同类型的数据量
    type_counts = {}
    non_dict_items = []
    
    for i, item in enumerate(data):
        item_type = type(item).__name__
        type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        # 收集非字典类型的数据
        if not isinstance(item, dict):
            non_dict_items.append((i, item_type, item))
    
    # 打印类型分布
    print("\n数据类型分布:")
    for type_name, count in type_counts.items():
        print(f"  {type_name}: {count} 条")
    
    # 打印非字典类型的数据示例
    print(f"\n非字典类型数据共 {len(non_dict_items)} 条，占比 {len(non_dict_items)/total_count*100:.2f}%")
    
    if non_dict_items:
        print("\n非字典类型数据示例（前5条）:")
        for i, item_type, item in non_dict_items[:5]:
            print(f"  第 {i+1} 条: 类型={item_type}, 内容={item[:100]}..." if isinstance(item, str) else f"  第 {i+1} 条: 类型={item_type}, 内容={item}")
    
    return type_counts

# 主函数
def main():
    file_path = '清洗数据.json'
    check_data_types(file_path)

if __name__ == "__main__":
    main()