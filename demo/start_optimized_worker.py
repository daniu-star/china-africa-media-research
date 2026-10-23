#!/usr/bin/env python3
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
