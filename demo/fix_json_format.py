#!/usr/bin/env python3
"""
修复tasks文件JSON格式不匹配问题
将JSON Lines格式转换为标准JSON数组格式
"""

import json
import os
import logging
from typing import List, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_tasks_json_format():
    """修复tasks文件的JSON格式"""
    
    # 检查并修复tasks_0.json文件
    tasks_file_path = "data/tasks_0.json"
    
    if os.path.exists(tasks_file_path):
        logger.info(f"检查文件: {tasks_file_path}")
        
        try:
            # 读取文件内容
            with open(tasks_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 检查当前格式
            if content.startswith('{"task_id"'):
                logger.info("检测到JSON Lines格式，正在转换为标准JSON数组格式")
                
                # 解析JSON Lines格式
                tasks = []
                for line in content.split('\n'):
                    if line.strip():
                        task = json.loads(line.strip())
                        tasks.append(task)
                
                # 转换为标准JSON格式
                standard_json = {
                    "tasks": tasks
                }
                
                # 备份原文件
                backup_path = tasks_file_path + '.backup'
                os.rename(tasks_file_path, backup_path)
                logger.info(f"已备份原文件到: {backup_path}")
                
                # 写入标准JSON格式
                with open(tasks_file_path, 'w', encoding='utf-8') as f:
                    json.dump(standard_json, f, indent=2, ensure_ascii=False)
                
                logger.info(f"已修复文件格式，转换了 {len(tasks)} 个任务")
                
            elif content.startswith('{"tasks"'):
                logger.info("文件已经是标准JSON数组格式，无需修复")
            else:
                logger.warning("无法识别的JSON格式")
                
        except Exception as e:
            logger.error(f"修复文件失败: {e}")
    else:
        logger.warning(f"文件不存在: {tasks_file_path}")
    
    # 检查并修复tasks_expanded_0.json文件
    expanded_file_path = "data/tasks_expanded_0.json"
    
    if os.path.exists(expanded_file_path):
        logger.info(f"检查文件: {expanded_file_path}")
        
        try:
            # 读取文件内容
            with open(expanded_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 检查当前格式
            if content.startswith('{"tasks"'):
                logger.info("文件已经是标准JSON数组格式，无需修复")
            elif content.startswith('{"task_id"'):
                logger.info("检测到JSON Lines格式，正在转换为标准JSON数组格式")
                
                # 解析JSON Lines格式
                tasks = []
                for line in content.split('\n'):
                    if line.strip():
                        task = json.loads(line.strip())
                        tasks.append(task)
                
                # 转换为标准JSON格式
                standard_json = {
                    "tasks": tasks
                }
                
                # 备份原文件
                backup_path = expanded_file_path + '.backup'
                os.rename(expanded_file_path, backup_path)
                logger.info(f"已备份原文件到: {backup_path}")
                
                # 写入标准JSON格式
                with open(expanded_file_path, 'w', encoding='utf-8') as f:
                    json.dump(standard_json, f, indent=2, ensure_ascii=False)
                
                logger.info(f"已修复文件格式，转换了 {len(tasks)} 个任务")
            else:
                logger.warning("无法识别的JSON格式")
                
        except Exception as e:
            logger.error(f"修复文件失败: {e}")
    else:
        logger.warning(f"文件不存在: {expanded_file_path}")

def create_unified_json_format():
    """创建统一的JSON格式处理函数"""
    
    unified_code = '''
def read_tasks_file(file_path: str) -> List[Dict[str, Any]]:
    """
    统一读取tasks文件，支持JSON Lines和标准JSON数组格式
    """
    import json
    import os
    
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # 尝试解析为标准JSON格式
        try:
            data = json.loads(content)
            if isinstance(data, dict) and 'tasks' in data:
                return data['tasks']
            elif isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
        
        # 尝试解析为JSON Lines格式
        tasks = []
        for line in content.split('\\n'):
            if line.strip():
                try:
                    task = json.loads(line.strip())
                    tasks.append(task)
                except json.JSONDecodeError:
                    continue
        
        return tasks
        
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")
        return []

def write_tasks_file(file_path: str, tasks: List[Dict[str, Any]]) -> bool:
    """
    统一写入tasks文件，使用标准JSON数组格式
    """
    import json
    import os
    
    try:
        # 创建标准JSON格式
        data = {
            "tasks": tasks
        }
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        print(f"写入文件失败 {file_path}: {e}")
        return False
'''
    
    # 保存统一处理函数
    with open("data/json_utils.py", "w", encoding="utf-8") as f:
        f.write(unified_code)
    
    logger.info("已创建统一的JSON格式处理函数: data/json_utils.py")

if __name__ == "__main__":
    logger.info("开始修复JSON格式问题...")
    
    # 修复现有文件格式
    fix_tasks_json_format()
    
    # 创建统一处理函数
    create_unified_json_format()
    
    logger.info("JSON格式修复完成！")
    logger.info("建议：更新相关代码使用统一的JSON处理函数")
    logger.info("使用方法：from data.json_utils import read_tasks_file, write_tasks_file")