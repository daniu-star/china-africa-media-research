import json
import re

# 手动修复JSON文件
def fix_json_manual(file_path):
    print(f"正在手动修复JSON文件: {file_path}")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"文件共有 {len(lines)} 行")
    
    # 修复最后一行
    if lines:
        # 修改第786行（最后一行），修复多余的括号
        lines[-1] = re.sub(r'}}$}}', '}}}', lines[-1])
        print("修复了最后一行的多余括号")
    
    # 修复第785行（倒数第二行），移除可能的错误逗号
    if len(lines) >= 2:
        lines[-2] = lines[-2].rstrip()
        if lines[-2].endswith(','):
            lines[-2] = lines[-2][:-1]
        print("修复了倒数第二行的逗号")
    
    # 重新组合文件内容
    fixed_content = ''.join(lines)
    
    # 尝试解析修复后的JSON
    try:
        parsed = json.loads(fixed_content)
        print("JSON解析成功！")
        print(f"JSON结构: {list(parsed.keys())}")
        
        # 保存修复后的文件
        fixed_file_path = file_path.replace('.json', '_fixed.json')
        with open(fixed_file_path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        print(f"修复后的文件已保存到: {fixed_file_path}")
        return fixed_file_path
    
    except json.JSONDecodeError as e:
        print(f"修复后仍无法解析JSON: {e}")
        print(f"错误位置: 行 {e.lineno}, 列 {e.colno}")
        # 写出修复后的内容到临时文件，以便手动检查
        temp_file = file_path.replace('.json', '_temp.txt')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"临时文件已保存到: {temp_file}")
        return None

if __name__ == "__main__":
    file_path = r'c:\Users\13067\Desktop\论文\非洲\demo\african_development_dictionary.json'
    fix_json_manual(file_path)