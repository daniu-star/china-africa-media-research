#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据文件查看工具
用于查看非洲数据研究项目中的各种数据文件
"""

import json
import os
import sqlite3
from pathlib import Path

def view_task_file():
    """查看任务配置文件"""
    file_path = "data/20000_crawling_tasks_20251126_100526.json"
    
    if os.path.exists(file_path):
        print(f"=== 任务配置文件: {file_path} ===")
        print(f"文件大小: {os.path.getsize(file_path) / 1024 / 1024:.2f} MB")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"任务总数: {len(data)}")
        print("\n前5个任务示例:")
        for i, task in enumerate(data[:5]):
            print(f"{i+1}. {task['task_id']}")
            print(f"   关键词: {task['keyword']}")
            print(f"   类别: {task['category']}")
            print(f"   国家: {task['country']}")
            print(f"   状态: {task['status']}")
            print()
        
        # 统计信息
        categories = set(task['category'] for task in data)
        countries = set(task['country'] for task in data)
        
        print(f"覆盖类别: {len(categories)} 个")
        print(f"覆盖国家: {len(countries)} 个")
        print(f"类别列表: {list(categories)}")
        print(f"国家列表: {list(countries)}")
        
    else:
        print(f"文件不存在: {file_path}")

def view_database():
    """查看数据库内容"""
    db_path = "data/articles.db"
    
    if os.path.exists(db_path):
        print(f"\n=== 数据库文件: {db_path} ===")
        print(f"文件大小: {os.path.getsize(db_path) / 1024 / 1024:.2f} MB")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 获取表结构
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"数据库表数量: {len(tables)}")
            print(f"表名列表: {[table[0] for table in tables]}")
            
            # 查看articles表结构
            if 'articles' in [table[0] for table in tables]:
                cursor.execute("PRAGMA table_info(articles);")
                columns = cursor.fetchall()
                print(f"\narticles表字段 ({len(columns)} 个):")
                for col in columns:
                    print(f"  {col[1]} ({col[2]})")
                
                # 获取文章数量
                cursor.execute("SELECT COUNT(*) FROM articles;")
                count = cursor.fetchone()[0]
                print(f"\n文章总数: {count}")
                
                # 查看前3篇文章
                cursor.execute("SELECT * FROM articles LIMIT 3;")
                articles = cursor.fetchall()
                
                print("\n前3篇文章示例:")
                for i, article in enumerate(articles):
                    print(f"{i+1}. ID: {article[0]}")
                    print(f"   标题: {article[1][:50]}..." if len(article[1]) > 50 else f"   标题: {article[1]}")
                    print(f"   来源: {article[2]}")
                    print(f"   国家: {article[3]}")
                    print(f"   类别: {article[4]}")
                    print()
            
            conn.close()
            
        except Exception as e:
            print(f"数据库访问错误: {e}")
    else:
        print(f"数据库文件不存在: {db_path}")

def list_data_files():
    """列出数据目录中的文件"""
    data_dir = "data"
    
    if os.path.exists(data_dir):
        print(f"\n=== 数据目录结构: {data_dir} ===")
        
        # 统计各类文件
        file_types = {}
        total_size = 0
        
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                file_size = os.path.getsize(file_path)
                
                if file_ext not in file_types:
                    file_types[file_ext] = {'count': 0, 'size': 0}
                
                file_types[file_ext]['count'] += 1
                file_types[file_ext]['size'] += file_size
                total_size += file_size
        
        print(f"总数据量: {total_size / 1024 / 1024:.2f} MB")
        print("\n文件类型分布:")
        for ext, info in file_types.items():
            print(f"  {ext if ext else '无扩展名'}: {info['count']} 个文件, {info['size'] / 1024 / 1024:.2f} MB")
        
        # 列出主要文件
        print("\n主要数据文件:")
        important_files = [
            "articles.db", "tasks.db", "20000_crawling_tasks_20251126_100526.json",
            "crawling_strategy.json", "progress_report.json"
        ]
        
        for file in important_files:
            file_path = os.path.join(data_dir, file)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path) / 1024 / 1024
                print(f"  {file}: {size:.2f} MB")
    else:
        print(f"数据目录不存在: {data_dir}")

if __name__ == "__main__":
    print("非洲数据研究项目 - 数据文件查看工具")
    print("=" * 50)
    
    # 查看任务文件
    view_task_file()
    
    # 查看数据库
    view_database()
    
    # 列出数据文件
    list_data_files()
    
    print("\n数据文件位置总结:")
    print("1. 任务配置: data/20000_crawling_tasks_20251126_100526.json")
    print("2. 文章数据: data/articles.db (SQLite数据库)")
    print("3. 任务数据: data/tasks.db (SQLite数据库)")
    print("4. 抓取结果: data/results_*.json 和 data/results/ 目录")
    print("5. 备份数据: data/backup/ 目录")
    print("6. 系统配置: data/crawling_strategy.json 等")