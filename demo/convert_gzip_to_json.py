import os
import gzip
import json

# 源目录
source_dir = r"c:\Users\13067\Desktop\论文\非洲\demo\data\crawler_results"

def convert_gzip_to_json(file_path):
    """将单个 gzip 文件转换为 JSON 文件"""
    try:
        # 读取 gzip 文件
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        
        # 生成输出文件路径
        output_path = file_path[:-3]  # 去除 .gz 扩展名
        
        # 保存为 JSON 文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    """主函数，递归处理所有文件"""
    # 统计文件数量
    total_files = 0
    for root, dirs, files in os.walk(source_dir):
        total_files += len([f for f in files if f.endswith('.json.gz')])
    
    print(f"发现 {total_files} 个 .json.gz 文件需要转换")
    
    # 开始转换
    success_count = 0
    failure_count = 0
    failed_files = []
    
    print("开始转换...")
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.json.gz'):
                file_path = os.path.join(root, file)
                print(f"正在转换: {file_path}")
                success, error = convert_gzip_to_json(file_path)
                if success:
                    success_count += 1
                    print(f"✓ 成功转换: {file}")
                else:
                    failure_count += 1
                    failed_files.append((file_path, error))
                    print(f"✗ 转换失败: {file} - {error}")
    
    # 输出转换结果
    print(f"\n转换完成！")
    print(f"成功转换: {success_count} 个文件")
    print(f"转换失败: {failure_count} 个文件")
    
    if failed_files:
        print("\n失败文件列表:")
        for file_path, error in failed_files:
            print(f"  {file_path}: {error}")

if __name__ == "__main__":
    main()