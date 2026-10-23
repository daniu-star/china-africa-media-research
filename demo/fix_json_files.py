#!/usr/bin/env python3
"""
修复JSON文件格式并统计数据条数 - 增强版
"""

import json
import os
import re

def fix_and_count_json_files():
    """修复JSON文件格式并统计数据条数"""
    
    files_to_check = [
        "c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\data\\results_0.json.backup",
        "c:\\Users\\13067\\Desktop\\论文\\非洲\\demo\\data\\results_1.json"
    ]
    
    results = {}
    
    for file_path in files_to_check:
        print(f"\n正在处理文件: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            continue
            
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"原始文件长度: {len(content)} 字符")
        
        # 尝试解析JSON
        try:
            data = json.loads(content)
            print("✓ 文件格式正确，无需修复")
            
            # 统计数据条数
            if 'result' in data and 'articles' in data['result']:
                article_count = len(data['result']['articles'])
                print(f"✓ 有效文章数量: {article_count}")
                results[file_path] = {
                    'status': 'valid',
                    'article_count': article_count,
                    'total_records': 1  # 每个文件是一个完整的记录
                }
            else:
                print("⚠ 文件结构不完整，缺少articles字段")
                results[file_path] = {'status': 'invalid_structure', 'article_count': 0}
                
        except json.JSONDecodeError as e:
            print(f"✗ JSON格式错误: {e}")
            
            # 尝试方法1：查找所有可能的JSON对象
            print("尝试方法1：查找所有JSON对象...")
            
            # 使用正则表达式查找所有可能的JSON对象
            json_objects = []
            
            # 查找以 { 开头，以 } 结尾的对象
            pattern = r'\{[^{}]*\}'
            matches = re.finditer(pattern, content)
            
            valid_objects = []
            for match in matches:
                try:
                    obj = json.loads(match.group())
                    valid_objects.append(obj)
                except:
                    pass
            
            if valid_objects:
                print(f"✓ 找到 {len(valid_objects)} 个有效JSON对象")
                
                # 统计文章数量
                total_articles = 0
                for obj in valid_objects:
                    if 'result' in obj and 'articles' in obj['result']:
                        total_articles += len(obj['result']['articles'])
                
                print(f"✓ 总文章数量: {total_articles}")
                results[file_path] = {
                    'status': 'multiple_objects_found',
                    'article_count': total_articles,
                    'total_records': len(valid_objects)
                }
                
                # 保存修复后的文件
                backup_path = file_path + '.backup'
                fixed_path = file_path.replace('.json', '_fixed.json')
                
                # 创建备份
                os.rename(file_path, backup_path)
                
                # 保存为有效的JSON数组
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(valid_objects, f, ensure_ascii=False, indent=2)
                
                print(f"✓ 文件已修复并保存，备份在: {backup_path}")
                
            else:
                print("✗ 方法1失败，尝试方法2...")
                
                # 方法2：尝试分割文件内容
                lines = content.strip().split('\n')
                valid_objects = []
                
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith('{') or line.startswith('[')):
                        try:
                            obj = json.loads(line)
                            valid_objects.append(obj)
                        except:
                            pass
                
                if valid_objects:
                    print(f"✓ 找到 {len(valid_objects)} 个有效JSON对象")
                    
                    # 统计文章数量
                    total_articles = 0
                    for obj in valid_objects:
                        if isinstance(obj, dict) and 'result' in obj and 'articles' in obj['result']:
                            total_articles += len(obj['result']['articles'])
                    
                    print(f"✓ 总文章数量: {total_articles}")
                    results[file_path] = {
                        'status': 'multiple_objects_found',
                        'article_count': total_articles,
                        'total_records': len(valid_objects)
                    }
                else:
                    print("✗ 所有修复方法都失败")
                    results[file_path] = {'status': 'unfixable', 'article_count': 0}
    
    # 输出统计结果
    print("\n" + "="*50)
    print("统计结果:")
    print("="*50)
    
    total_articles = 0
    total_files = 0
    total_records = 0
    
    for file_path, result in results.items():
        filename = os.path.basename(file_path)
        status = result['status']
        article_count = result.get('article_count', 0)
        record_count = result.get('total_records', 0)
        
        print(f"{filename}: {status} - {article_count} 篇文章 ({record_count} 条记录)")
        
        if status in ['valid', 'multiple_objects_found']:
            total_articles += article_count
            total_files += 1
            total_records += record_count
    
    print(f"\n总计: {total_files} 个有效文件，{total_records} 条记录，{total_articles} 篇文章")
    
    return results

if __name__ == "__main__":
    fix_and_count_json_files()