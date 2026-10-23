import json
import re

# 修复JSON文件的语法问题
def fix_json_file(file_path):
    print(f"正在修复JSON文件: {file_path}")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"原始文件长度: {len(content)} 字符")
    
    # 修复JSON格式问题
    # 1. 移除多余的括号
    # 找到最后一个有效的}}}}位置，然后截断
    content = re.sub(r'\}\}\}\}\s*$', '}}}}', content)
    
    # 2. 确保文件以正确的格式结尾
    if not content.strip().endswith('}}}'):
        print("修复文件结尾格式...")
        # 找到最后一个}的位置
        last_brace_pos = content.rfind('}')
        if last_brace_pos != -1:
            content = content[:last_brace_pos+1]
    
    # 3. 修复第785行的多余逗号
    lines = content.split('\n')
    if len(lines) >= 2:
        # 处理倒数第二行
        second_last_line = lines[-2].rstrip()
        if second_last_line.endswith(','):
            lines[-2] = second_last_line[:-1]
    
    # 4. 重新组合内容
    content = '\n'.join(lines)
    
    # 尝试解析修复后的JSON
    try:
        parsed = json.loads(content)
        print("JSON解析成功！")
        print(f"JSON结构: {list(parsed.keys())}")
        print(f"各类别关键词数量: {[len(v) for v in parsed.values()]}")
        
        # 保存修复后的文件（覆盖原文件）
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        print(f"修复后的文件已保存到: {file_path}")
        return True
    
    except json.JSONDecodeError as e:
        print(f"修复后仍无法解析JSON: {e}")
        print(f"错误位置: 行 {e.lineno}, 列 {e.colno}")
        return False

if __name__ == "__main__":
    json_file = r'c:\Users\13067\Desktop\论文\非洲\demo\african_development_dictionary.json'
    success = fix_json_file(json_file)
    if success:
        print("JSON修复成功！")
    else:
        print("JSON修复失败，请手动检查文件。")