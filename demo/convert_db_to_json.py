#!/usr/bin/env python3
"""
将SQLite数据库转换为JSON格式文件
确保数据完整无丢失，包含所有表、索引和关系信息
"""

import sqlite3
import json
import os
from datetime import datetime

def get_database_info(db_path):
    """获取数据库的完整信息"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取数据库基本信息
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    database_info = {
        "database_name": os.path.basename(db_path),
        "conversion_date": datetime.now().isoformat(),
        "tables": {},
        "indexes": {},
        "total_records": 0
    }
    
    # 获取每个表的结构和数据
    for table_name in tables:
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        
        # 获取表数据
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # 构建表信息
        table_info = {
            "columns": [],
            "data": [],
            "row_count": len(rows)
        }
        
        # 添加列信息
        for col in columns_info:
            table_info["columns"].append({
                "cid": col[0],
                "name": col[1],
                "type": col[2],
                "notnull": bool(col[3]),
                "default_value": col[4],
                "pk": bool(col[5])
            })
        
        # 添加数据
        for row in rows:
            row_data = {}
            for i, col in enumerate(columns_info):
                col_name = col[1]
                value = row[i]
                # 处理特殊类型
                if isinstance(value, bytes):
                    value = value.hex()  # 将二进制数据转换为十六进制字符串
                elif value is None:
                    value = None
                row_data[col_name] = value
            table_info["data"].append(row_data)
        
        database_info["tables"][table_name] = table_info
        database_info["total_records"] += len(rows)
    
    # 获取索引信息
    cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index';")
    indexes = cursor.fetchall()
    
    for index in indexes:
        index_name, table_name, sql = index
        database_info["indexes"][index_name] = {
            "table": table_name,
            "sql": sql
        }
    
    conn.close()
    return database_info

def convert_to_readable_json(db_path, output_path):
    """将数据库转换为可读的JSON格式"""
    
    print("正在分析数据库结构...")
    database_info = get_database_info(db_path)
    
    print("正在生成JSON文件...")
    
    # 创建可读性更好的JSON格式
    readable_json = {
        "metadata": {
            "source_database": database_info["database_name"],
            "conversion_date": database_info["conversion_date"],
            "total_tables": len(database_info["tables"]),
            "total_records": database_info["total_records"]
        },
        "tables": {}
    }
    
    # 处理每个表
    for table_name, table_info in database_info["tables"].items():
        readable_json["tables"][table_name] = {
            "schema": {
                "columns": table_info["columns"],
                "row_count": table_info["row_count"]
            },
            "data": table_info["data"]
        }
    
    # 添加索引信息
    readable_json["indexes"] = database_info["indexes"]
    
    # 保存JSON文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(readable_json, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"转换完成！JSON文件已保存到: {output_path}")
    
    # 显示转换统计信息
    print(f"\n转换统计:")
    print(f"- 源数据库: {database_info['database_name']}")
    print(f"- 表数量: {len(database_info['tables'])}")
    print(f"- 总记录数: {database_info['total_records']}")
    
    for table_name, table_info in database_info["tables"].items():
        print(f"- {table_name}: {table_info['row_count']} 条记录")
    
    return readable_json

def create_editable_json_version(db_path, output_path):
    """创建便于编辑的JSON版本"""
    
    print("正在创建便于编辑的JSON版本...")
    
    database_info = get_database_info(db_path)
    
    # 创建便于编辑的格式（按表分开）
    editable_data = {
        "metadata": {
            "source_database": database_info["database_name"],
            "conversion_date": database_info["conversion_date"],
            "description": "便于编辑的数据库JSON格式，每个表的数据可以独立修改"
        }
    }
    
    # 为每个表创建独立的数据结构
    for table_name, table_info in database_info["tables"].items():
        # 创建便于编辑的格式
        editable_data[table_name] = {
            "_schema": table_info["columns"],
            "_data": table_info["data"]
        }
    
    # 保存便于编辑的版本
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(editable_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"便于编辑的版本已保存到: {output_path}")
    return editable_data

def main():
    """主函数"""
    db_path = "data/articles.db"
    
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件 {db_path} 不存在")
        return
    
    # 创建输出目录
    os.makedirs("data/json_export", exist_ok=True)
    
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. 完整可读版本
    readable_output = f"data/json_export/articles_db_readable_{timestamp}.json"
    convert_to_readable_json(db_path, readable_output)
    
    # 2. 便于编辑版本
    editable_output = f"data/json_export/articles_db_editable_{timestamp}.json"
    create_editable_json_version(db_path, editable_output)
    
    # 3. 纯数据版本（仅包含articles表的数据，便于分析）
    data_only_output = f"data/json_export/articles_data_only_{timestamp}.json"
    create_data_only_version(db_path, data_only_output)
    
    print(f"\n所有转换完成！文件保存在 data/json_export/ 目录下")
    print(f"1. 完整可读版本: {readable_output}")
    print(f"2. 便于编辑版本: {editable_output}")
    print(f"3. 纯数据版本: {data_only_output}")

def create_data_only_version(db_path, output_path):
    """创建仅包含articles表数据的简化版本"""
    
    print("正在创建纯数据版本...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取articles表数据
    cursor.execute("SELECT * FROM articles")
    rows = cursor.fetchall()
    
    # 获取列名
    cursor.execute("PRAGMA table_info(articles)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # 构建数据
    articles_data = []
    for row in rows:
        article = {}
        for i, col_name in enumerate(columns):
            value = row[i]
            # 处理特殊类型
            if isinstance(value, bytes):
                value = value.hex()
            article[col_name] = value
        articles_data.append(article)
    
    conn.close()
    
    # 保存纯数据版本
    data_only = {
        "metadata": {
            "source": "articles table only",
            "record_count": len(articles_data),
            "conversion_date": datetime.now().isoformat()
        },
        "articles": articles_data
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data_only, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"纯数据版本已保存到: {output_path}")
    return data_only

if __name__ == "__main__":
    main()