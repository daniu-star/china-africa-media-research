#!/usr/bin/env python3
"""
工作节点优化脚本
用于检查和优化工作节点的配置和运行状态
"""

import os
import sys
import time
import requests
import json
from pathlib import Path

def check_firecrawl_availability():
    """检查Firecrawl是否可用"""
    print("检查Firecrawl可用性...")
    
    # 检查Firecrawl配置
    config_path = Path("massive_crawler_config.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        firecrawl_enabled = config.get('firecrawl_enabled', False)
        print(f"Firecrawl配置状态: {'启用' if firecrawl_enabled else '禁用'}")
    else:
        print("警告: 未找到massive_crawler_config.json配置文件")
    
    # 检查Firecrawl导入
    try:
        import firecrawl
        print("✓ Firecrawl包导入成功")
        return True
    except ImportError as e:
        print(f"✗ Firecrawl包导入失败: {e}")
        print("建议: 运行 'pip install firecrawl' 安装Firecrawl包")
        return False

def check_worker_config():
    """检查工作节点配置"""
    print("\n检查工作节点配置...")
    
    # 检查环境文件
    env_path = Path(".env")
    if env_path.exists():
        print("✓ 环境配置文件存在")
        with open(env_path, 'r', encoding='utf-8') as f:
            print("环境配置内容:")
            print(f.read())
    else:
        print("✗ 环境配置文件不存在")
    
    # 检查工作节点文件
    worker_path = Path("distributed_worker.py")
    if worker_path.exists():
        print("✓ 工作节点文件存在")
        
        # 检查关键配置
        with open(worker_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ("REQUEST_TIMEOUT", "请求超时配置"),
            ("HEARTBEAT_TIMEOUT", "心跳超时配置"),
            ("MAX_RETRY_ATTEMPTS", "最大重试次数"),
            ("request_with_retry", "重试机制方法"),
            ("Firecrawl", "Firecrawl集成")
        ]
        
        for keyword, description in checks:
            if keyword in content:
                print(f"✓ {description} 存在")
            else:
                print(f"✗ {description} 缺失")
    else:
        print("✗ 工作节点文件不存在")

def check_master_connectivity():
    """检查主节点连接性"""
    print("\n检查主节点连接性...")
    
    master_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{master_url}/workers/status", timeout=10)
        if response.status_code == 200:
            print("✓ 主节点连接正常")
            data = response.json()
            print(f"工作节点数量: {len(data.get('workers', []))}")
            return True
        else:
            print(f"✗ 主节点响应异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ 主节点连接失败: {e}")
        print("请确保主节点正在运行: python distributed_master.py")
        return False

def optimize_url_handling():
    """优化URL处理逻辑"""
    print("\n优化URL处理逻辑...")
    
    # 检查URL构建逻辑
    worker_path = Path("distributed_worker.py")
    if worker_path.exists():
        with open(worker_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查URL编码处理
        if 'urllib.parse.quote' in content:
            print("✓ URL编码处理存在")
        else:
            print("✗ URL编码处理缺失")
            print("建议: 在build_search_urls方法中添加URL编码")
        
        # 检查404错误处理
        if '404' in content and 'Client Error' in content:
            print("✓ 404错误处理存在")
        else:
            print("✗ 404错误处理需要优化")

def create_optimized_worker_script():
    """创建优化的工作节点启动脚本"""
    print("\n创建优化的工作节点启动脚本...")
    
    script_content = '''#!/usr/bin/env python3
"""
工作节点优化启动脚本
自动处理配置检查和优化
"""

import os
import sys
import time
from pathlib import Path

def main():
    # 检查环境配置
    env_path = Path(".env")
    if not env_path.exists():
        print("警告: 未找到环境配置文件，使用默认配置")
    
    # 检查Firecrawl
    try:
        import firecrawl
        print("Firecrawl可用，启用高级爬取功能")
    except ImportError:
        print("Firecrawl不可用，使用传统爬取模式")
    
    # 启动工作节点
    print("启动优化的工作节点...")
    os.system("python distributed_worker.py --worker-id worker-optimized --master-url http://localhost:8000")

if __name__ == "__main__":
    main()
'''
    
    with open("start_optimized_worker.py", 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✓ 优化的工作节点启动脚本已创建: start_optimized_worker.py")

def main():
    """主函数"""
    print("=" * 50)
    print("工作节点优化检查脚本")
    print("=" * 50)
    
    # 执行检查
    firecrawl_ok = check_firecrawl_availability()
    check_worker_config()
    master_ok = check_master_connectivity()
    optimize_url_handling()
    create_optimized_worker_script()
    
    # 总结
    print("\n" + "=" * 50)
    print("优化检查完成")
    print("=" * 50)
    
    if firecrawl_ok and master_ok:
        print("✓ 系统状态良好，可以正常运行")
        print("运行优化的工作节点: python start_optimized_worker.py")
    else:
        print("⚠ 系统存在一些问题，建议先解决上述问题")
        if not firecrawl_ok:
            print("- 安装Firecrawl: pip install firecrawl")
        if not master_ok:
            print("- 启动主节点: python distributed_master.py")

if __name__ == "__main__":
    main()