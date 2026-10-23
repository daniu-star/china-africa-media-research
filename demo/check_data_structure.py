#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据文件结构
"""

import json
import os

def check_data_structure():
    """检查数据文件结构"""
    
    # 加载数据文件
    data_file = 'data/results_enhanced_with_dates.json'
    if not os.path.exists(data_file):
        print(f'错误: 数据文件 {data_file} 不存在')
        return
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f'加载数据文件失败: {e}')
        return
    
    print(f'数据类型: {type(data)}')
    
    if isinstance(data, list):
        print(f'数据长度: {len(data)}')
        if len(data) > 0:
            print(f'第一个元素类型: {type(data[0])}')
            print('第一个元素键:')
            if isinstance(data[0], dict):
                for key in data[0].keys():
                    print(f'  {key}')
            else:
                print(f'  {data[0]}')
    elif isinstance(data, dict):
        print('数据是字典，键为:')
        for key in data.keys():
            print(f'  {key}')
            if isinstance(data[key], list) and len(data[key]) > 0:
                print(f'    {key} 列表长度: {len(data[key])}')
                if isinstance(data[key][0], dict):
                    print(f'    第一个元素键: {list(data[key][0].keys())}')

if __name__ == '__main__':
    check_data_structure()