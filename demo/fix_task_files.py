#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复任务文件JSON格式错误脚本
"""

import json
import os
import re
from pathlib import Path

def fix_json_file(file_path):
    """修复单个JSON文件的格式错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # 如果文件为空，返回空列表
        if not content:
            return []
        
        # 尝试直接解析JSON
        try:
            data = json.loads(content)
            # 检查数据类型，如果是字符串则尝试再次解析
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    # 如果是字符串但无法解析，尝试提取JSON对象
                    json_objects = re.findall(r'\{[^}]*\}', data)
                    if json_objects:
                        data = []
                        for obj_str in json_objects:
                            try:
                                obj = json.loads(obj_str)
                                data.append(obj)
                            except:
                                continue
                    else:
                        data = []
            
            # 确保返回的是列表
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                return []
                
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            # 尝试修复格式错误
            
            # 方法1: 尝试提取所有JSON对象
            json_objects = re.findall(r'\{[^{}]*\{[^{}]*\}[^{}]*\}|\{[^}]*\}', content)
            
            if json_objects:
                fixed_data = []
                for obj_str in json_objects:
                    try:
                        # 清理字符串
                        obj_str = obj_str.strip()
                        if obj_str.startswith('{') and obj_str.endswith('}'):
                            obj = json.loads(obj_str)
                            fixed_data.append(obj)
                    except:
                        continue
                
                if fixed_data:
                    return fixed_data
            
            # 方法2: 尝试分割成多个JSON对象
            lines = content.split('\n')
            fixed_data = []
            current_obj = []
            brace_count = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                brace_count += line.count('{')
                brace_count -= line.count('}')
                current_obj.append(line)
                
                if brace_count == 0 and current_obj:
                    obj_str = '\n'.join(current_obj)
                    try:
                        obj = json.loads(obj_str)
                        fixed_data.append(obj)
                    except:
                        pass
                    current_obj = []
            
            if fixed_data:
                return fixed_data
            
            # 方法3: 如果所有方法都失败，返回空列表
            return []
            
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return []

def save_fixed_file(file_path, data):
    """保存修复后的数据"""
    try:
        # 创建备份
        backup_path = str(file_path) + '.backup'
        if os.path.exists(file_path):
            os.rename(str(file_path), backup_path)
        
        # 保存修复后的数据
        with open(str(file_path), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已修复 {file_path}，包含 {len(data)} 个任务")
        return True
        
    except Exception as e:
        print(f"❌ 保存文件 {file_path} 时出错: {e}")
        return False

def main():
    """主修复函数"""
    data_dir = Path("./data")
    
    # 查找所有任务文件
    task_files = []
    task_files.extend(data_dir.glob("tasks_*.json"))
    task_files.extend(data_dir.glob("tasks_expanded_*.json"))
    task_files.extend(data_dir.glob("tasks_merged_*.json"))
    
    print(f"找到 {len(task_files)} 个任务文件")
    
    total_fixed = 0
    total_tasks = 0
    
    for file_path in task_files:
        print(f"\n正在处理: {file_path}")
        
        # 修复文件
        fixed_data = fix_json_file(file_path)
        
        if fixed_data:
            # 保存修复后的文件
            if save_fixed_file(file_path, fixed_data):
                total_fixed += 1
                total_tasks += len(fixed_data)
        else:
            print(f"⚠️  {file_path} 无法修复，可能为空或格式严重损坏")
    
    print(f"\n=== 修复完成 ===")
    print(f"修复文件数: {total_fixed}")
    print(f"总任务数: {total_tasks}")
    
    # 检查结果文件
    results_files = data_dir.glob("results/results_*.json")
    for file_path in results_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ {file_path}: {len(data)} 个结果")
        except Exception as e:
            print(f"❌ {file_path}: 格式错误 - {e}")

if __name__ == "__main__":
    main()