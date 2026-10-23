import json
import os

# 验证文件列表
verify_files = [
    r"c:\Users\13067\Desktop\论文\非洲\demo\data\crawler_results\test\crawl_result_1764161890.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\data\crawler_results\multi_test\multi_test_000.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\data\crawler_results\final_backup\20251128\china_related_hausa_32_20251128_035831.json"
]

def verify_json_file(file_path):
    """验证单个JSON文件的数据完整性"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✓ 成功读取文件: {os.path.basename(file_path)}")
        print(f"  数据类型: {type(data).__name__}")
        
        if isinstance(data, list):
            print(f"  列表长度: {len(data)}")
            if data:
                print(f"  第一个元素类型: {type(data[0]).__name__}")
                print(f"  第一个元素示例: {json.dumps(data[0], ensure_ascii=False, indent=2)[:200]}...")
        elif isinstance(data, dict):
            print(f"  字典键数量: {len(data)}")
            if data:
                first_key = next(iter(data))
                print(f"  第一个键: {first_key}")
                print(f"  第一个值: {json.dumps(data[first_key], ensure_ascii=False, indent=2)[:200]}...")
        else:
            print(f"  数据值: {data}")
        
        print()
        return True
    except Exception as e:
        print(f"✗ 验证失败: {os.path.basename(file_path)} - {e}")
        print()
        return False

def main():
    """主函数，验证多个JSON文件"""
    print("开始验证转换后的JSON文件数据完整性...")
    print("=" * 60)
    
    success_count = 0
    total_count = len(verify_files)
    
    for file_path in verify_files:
        if verify_json_file(file_path):
            success_count += 1
    
    print("=" * 60)
    print(f"验证完成！成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("✓ 所有文件验证通过，数据完整！")
    else:
        print("✗ 部分文件验证失败，需要检查！")

if __name__ == "__main__":
    main()