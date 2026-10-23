#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库内容和结构
"""

import sqlite3
import os
import json

def check_database():
    """检查数据库内容和结构"""
    db_path = os.path.join('data', 'articles.db')
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    print(f"✅ 数据库文件存在: {db_path}")
    print(f"📊 文件大小: {os.path.getsize(db_path) / 1024 / 1024:.2f} MB")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📋 数据库中的表: {len(tables)}个")
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
            
            # 检查表结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"    字段结构:")
            for col in columns:
                print(f"      {col[1]} ({col[2]})")
            
            # 检查数据量
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"    数据量: {count}条记录")
            
            # 如果是articles表，显示更多信息
            if table_name == 'articles':
                cursor.execute("SELECT DISTINCT country FROM articles")
                countries = cursor.fetchall()
                print(f"    覆盖国家: {len(countries)}个")
                
                cursor.execute("SELECT DISTINCT category FROM articles")
                categories = cursor.fetchall()
                print(f"    文章类别: {len(categories)}个")
                
                # 显示前5条记录示例
                cursor.execute("SELECT title, country, category, date FROM articles LIMIT 5")
                samples = cursor.fetchall()
                print(f"    示例数据:")
                for i, sample in enumerate(samples, 1):
                    print(f"      {i}. {sample[0]} - {sample[1]} - {sample[2]} - {sample[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 数据库访问错误: {e}")

def check_data_files():
    """检查数据文件"""
    data_dir = 'data'
    
    print(f"\n📁 数据目录结构: {data_dir}")
    
    # 统计文件类型
    file_types = {}
    total_size = 0
    
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()
            file_size = os.path.getsize(file_path)
            total_size += file_size
            
            if file_ext not in file_types:
                file_types[file_ext] = {'count': 0, 'size': 0}
            file_types[file_ext]['count'] += 1
            file_types[file_ext]['size'] += file_size
    
    print(f"📊 总数据大小: {total_size / 1024 / 1024:.2f} MB")
    print(f"📋 文件类型分布:")
    for ext, info in file_types.items():
        print(f"  {ext if ext else '无扩展名'}: {info['count']}个文件, {info['size'] / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    print("🔍 非洲数据研究项目 - 数据存储检查")
    print("=" * 50)
    
    check_database()
    check_data_files()
    
    print("\n" + "=" * 50)
    print("✅ 检查完成")