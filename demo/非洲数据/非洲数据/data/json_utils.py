
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
        for line in content.split('\n'):
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
