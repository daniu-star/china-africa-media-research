import json
import csv
import sys
from dateutil import parser
import re
import random
from collections import defaultdict

# 增加CSV字段限制，使用一个合适的大整数
csv.field_size_limit(100000000)

# 定义文件路径
json_file_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\清洗数据.json'
csv_file_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_cleaned_data.csv'
output_csv_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_cleaned_data_with_year.csv'

# 读取JSON数据并提取年份
def extract_years_from_json(json_path):
    print("正在从JSON文件中提取年份...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    years = []
    for i, item in enumerate(data):
        year_found = False
        
        # 确保item是字典类型
        if isinstance(item, dict):
            # 检查是否有日期字段
            date_fields = ['year', 'date', 'publish_date', '发布日期', '时间', 'timestamp']
            
            for field in date_fields:
                if field in item:
                    value = item[field]
                    
                    # 直接处理year字段
                    if field == 'year':
                        if isinstance(value, int) or isinstance(value, float):
                            year = str(int(value))
                            years.append(year)
                            year_found = True
                            break
                        elif isinstance(value, str):
                            # 清理字符串并转换
                            clean_value = value.strip()
                            if clean_value.isdigit() and len(clean_value) == 4:
                                years.append(clean_value)
                                year_found = True
                                break
                    # 处理其他日期字段
                    elif value:
                        try:
                            if isinstance(value, str):
                                # 使用dateutil.parser解析日期
                                parsed_date = parser.parse(value)
                                year = str(parsed_date.year)
                                years.append(year)
                                year_found = True
                                break
                        except (ValueError, OverflowError):
                            # 如果dateutil解析失败，尝试正则表达式
                            if isinstance(value, str):
                                match = re.search(r'\b(20[01][0-9]|202[0-5])\b', value)
                                if match:
                                    year = match.group(1)
                                    years.append(year)
                                    year_found = True
                                    break
        
        # 无法提取年份时，添加None
        if not year_found:
            years.append(None)
        
        # 显示进度
        if (i + 1) % 1000 == 0:
            print(f'已处理 {i + 1} 条JSON数据')
    
    return years

# 填充年份到CSV文件
def fill_year_to_csv(csv_path, output_path, years):
    print("正在将年份填充到CSV文件中...")
    
    # 读取CSV文件
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # 确保年份列表长度与CSV行数匹配
    min_length = min(len(years), len(rows))
    
    # 统计信息
    year_added = 0
    random_filled = 0
    
    # 填充年份
    for i in range(min_length):
        row = rows[i]
        year = years[i]
        
        if year:
            # 添加year列
            row['year'] = year
            year_added += 1
        else:
            # 无法提取年份，从2010-2019年中随机选择一个
            # 检查是否包含"一带一路"或"Belt and Road"相关内容
            content = f"{row.get('title', '')} {row.get('summary', '')}" \
                      f"{row.get('cleaned_title', '')} {row.get('cleaned_summary', '')}" \
                      f"{row.get('combined_text', '')}"
            
            # 检查内容是否包含一带一路相关关键词
            belt_road_keywords = ['一带一路', 'Belt and Road', 'One Belt One Road', 'B&R']
            has_belt_road = any(keyword in content for keyword in belt_road_keywords)
            
            # 一带一路倡议2013年提出，所以2013年前不应有相关报道
            if has_belt_road:
                # 一带一路相关报道，年份应在2013-2019之间
                random_year = str(random.randint(2013, 2019))
            else:
                # 非一带一路相关报道，年份在2010-2019之间
                random_year = str(random.randint(2010, 2019))
            
            row['year'] = random_year
            random_filled += 1
        
        # 显示进度
        if (i + 1) % 1000 == 0:
            print(f'已处理 {i + 1} 条CSV数据')
    
    # 处理JSON数据不足的情况
    for i in range(min_length, len(rows)):
        row = rows[i]
        # 检查内容是否包含一带一路相关关键词
        content = f"{row.get('title', '')} {row.get('summary', '')}" \
                  f"{row.get('cleaned_title', '')} {row.get('cleaned_summary', '')}" \
                  f"{row.get('combined_text', '')}"
        
        belt_road_keywords = ['一带一路', 'Belt and Road', 'One Belt One Road', 'B&R']
        has_belt_road = any(keyword in content for keyword in belt_road_keywords)
        
        if has_belt_road:
            random_year = str(random.randint(2013, 2019))
        else:
            random_year = str(random.randint(2010, 2019))
        
        row['year'] = random_year
        random_filled += 1
        
        if (i + 1) % 1000 == 0:
            print(f'已处理 {i + 1} 条CSV数据')
    
    # 写入新的CSV文件
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"年份填充完成！")
    print(f"- 成功从JSON提取年份并填充: {year_added}条")
    print(f"- 随机填充年份: {random_filled}条")
    print(f"- 总处理条数: {len(rows)}条")

# 执行主函数
if __name__ == "__main__":
    years = extract_years_from_json(json_file_path)
    fill_year_to_csv(csv_file_path, output_csv_path, years)
