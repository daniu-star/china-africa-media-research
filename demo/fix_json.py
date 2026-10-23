import json

# 读取JSON文件内容
def fix_json_file(file_path):
    print(f"正在检查并修复JSON文件: {file_path}")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"文件长度: {len(content)} 字符")
    
    # 尝试修复JSON格式
    # 1. 检查并修复最后一个元素后的逗号
    content = re.sub(r',\s*}', '}', content)
    content = re.sub(r',\s*]', ']', content)
    
    # 2. 确保文件以正确的括号结尾
    if not content.strip().endswith('}}}'):
        print("修复文件结尾...")
        # 移除所有结尾的错误字符，然后添加正确的结尾
        content = content.rstrip()
        # 找到最后一个{的位置
        last_open_brace = content.rfind('{')
        if last_open_brace != -1:
            # 保留到最后一个{之前的内容，然后添加正确的结尾
            content = content[:last_open_brace].rstrip() + '}}'
    
    # 3. 尝试解析修复后的JSON
    try:
        parsed = json.loads(content)
        print("JSON解析成功！")
        print(f"修复后的JSON结构: {list(parsed.keys())}")
        
        # 保存修复后的文件
        fixed_file_path = file_path.replace('.json', '_fixed.json')
        with open(fixed_file_path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        print(f"修复后的文件已保存到: {fixed_file_path}")
        return fixed_file_path
    
    except json.JSONDecodeError as e:
        print(f"修复后仍无法解析JSON: {e}")
        print(f"错误位置: 行 {e.lineno}, 列 {e.colno}")
        # 打印错误位置前后的内容
        lines = content.split('\n')
        if e.lineno <= len(lines):
            print(f"第 {e.lineno} 行内容: {lines[e.lineno-1]}")
            if e.lineno > 1:
                print(f"第 {e.lineno-1} 行内容: {lines[e.lineno-2]}")
            if e.lineno < len(lines):
                print(f"第 {e.lineno+1} 行内容: {lines[e.lineno]}")
    
    return None

if __name__ == "__main__":
    import re
    file_path = r'c:\Users\13067\Desktop\论文\非洲\demo\african_development_dictionary.json'
    fix_json_file(file_path)