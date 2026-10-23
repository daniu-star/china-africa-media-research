import json
from collections import defaultdict
from dateutil import parser
import re

# 定义文件路径
json_file_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\清洗数据.json'

# 读取JSON文件
try:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print('=== 数据基本信息 ===')
    print(f'数据类型: {type(data)}')
    
    if isinstance(data, list):
        print(f'数据总量: {len(data)}')
        
        if len(data) > 0:
            print(f'第一条数据类型: {type(data[0])}')
            
            if isinstance(data[0], dict):
                print(f'数据字段: {list(data[0].keys())}')
                
                # 提取年份信息
                print('\n=== 提取年份信息 ===')
                year_counts = defaultdict(int)
                
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        # 检查是否有日期字段
                        date_fields = ['year', 'date', 'publish_date', '发布日期', '时间', 'timestamp']
                        year_found = False
                        
                        for field in date_fields:
                            if field in item:
                                value = item[field]
                                
                                # 直接处理year字段
                                if field == 'year':
                                    if isinstance(value, int) or isinstance(value, float):
                                        year = str(int(value))
                                        year_counts[year] += 1
                                        year_found = True
                                        break
                                    elif isinstance(value, str):
                                        # 清理字符串并转换
                                        clean_value = value.strip()
                                        if clean_value.isdigit() and len(clean_value) == 4:
                                            year_counts[clean_value] += 1
                                            year_found = True
                                            break
                                # 处理其他日期字段
                                elif value:
                                    try:
                                        if isinstance(value, str):
                                            # 使用dateutil.parser解析日期
                                            parsed_date = parser.parse(value)
                                            year = str(parsed_date.year)
                                            year_counts[year] += 1
                                            year_found = True
                                            break
                                    except (ValueError, OverflowError):
                                        # 如果dateutil解析失败，尝试正则表达式
                                        if isinstance(value, str):
                                            match = re.search(r'\b(20[01][0-9]|202[0-5])\b', value)
                                            if match:
                                                year = match.group(1)
                                                year_counts[year] += 1
                                                year_found = True
                                                break
                        
                        # 记录无法解析的日期（可选，用于调试）
                        # if not year_found:
                        #     print(f"无法解析日期: {item}")
                        
                    # 显示进度
                    if (i + 1) % 1000 == 0:
                        print(f'已处理 {i + 1} 条数据')
                
                # 显示年份分布
                print('\n=== 年份分布统计 ===')
                if year_counts:
                    total = sum(year_counts.values())
                    print(f'总有效数据量: {total}')
                    print('\n各年份分布:')
                    
                    # 按年份排序
                    for year in sorted(year_counts.keys()):
                        count = year_counts[year]
                        percentage = (count / total) * 100
                        print(f'{year}: {count} 条 ({percentage:.2f}%)')
                    
                    print('\n=== 年份分布总结 ===')
                    print(f'年份范围: {min(year_counts.keys())} - {max(year_counts.keys())}')
                    print(f'覆盖年份数量: {len(year_counts.keys())} 年')
                else:
                    print('未找到有效的年份信息')
            else:
                print('数据项不是字典类型，无法提取年份信息')
    else:
        print('数据不是列表类型，无法处理')
        
except Exception as e:
    print(f'处理文件时出错: {e}')
    import traceback
    traceback.print_exc()
