import json
import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize
from sklearn.preprocessing import MinMaxScaler

# 初始化情感分析器
sia = SentimentIntensityAnalyzer()

# 读取发展词典
def load_development_dictionary(dict_path):
    with open(dict_path, 'r', encoding='utf-8') as f:
        development_dict = json.load(f)
    
    # 提取所有发展关键词（英文）
    development_keywords = []
    for category in development_dict.values():
        for keyword in category.keys():
            development_keywords.append(keyword)
    
    return development_keywords

# 主函数
def main():
    # 配置文件路径
    dict_path = 'african_development_dictionary.json'
    data_path = '清洗数据\\enhanced_data_with_development_weight.csv'
    output_path = 'enhanced_data_with_demand_perception.csv'
    
    #