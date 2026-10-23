import os
import json
import gzip
from collections import defaultdict

# 指定要遍历的文件夹列表
folders = [
    r"c:\Users\13067\Desktop\论文\非洲\demo\data",
    r"c:\Users\13067\Desktop\论文\非洲\demo\firecrawl_early_data_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\live_playwright_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\local_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\massive_crawler_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\optimized_crawler_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\crawler_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\china_africa_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\backups",
    r"c:\Users\13067\Desktop\论文\非洲\demo\backup"
]

# 存储所有新闻报道的唯一标识符（URL或标题）
all_news = defaultdict(set)  # 键：文件夹路径，值：该文件夹中的新闻URL集合
unique_news = set()  # 所有去重后的新闻URL集合

# 统计信息
stats = {
    "total_files": 0,
    "processed_files": 0,
    "error_files": 0,
    "total_news": 0,
    "unique_news_count": 0
}

def read_json_file(file_path):
    """读取JSON文件，支持普通JSON和gzipped JSON"""
    try:
        if file_path.endswith('.gz'):
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"错误：无法读取文件 {file_path} - {e}")
        stats["error_files"] += 1
        return None

def extract_news_items(data):
    """从JSON数据中提取新闻报道项"""
    news_items = []
    
    # 处理不同的数据结构
    if isinstance(data, list):
        # 直接是新闻列表
        news_items = data
    elif isinstance(data, dict):
        # 可能是包含新闻列表的对象
        # 尝试常见的键名
        for key in ['articles', 'news', 'items', 'results', 'data']:
            if key in data and isinstance(data[key], list):
                news_items = data[key]
                break
        # 如果没有找到列表，可能整个对象就是一条新闻
        else:
            news_items = [data]
    
    return news_items

def get_news_identifier(news_item):
    """获取新闻报道的唯一标识符"""
    # 优先使用URL作为唯一标识符
    if isinstance(news_item, dict):
        for key in ['url', 'link', 'article_url', 'source_url']:
            if key in news_item and news_item[key]:
                return news_item[key]
        # 如果没有URL，尝试使用标题
        for key in ['title', 'headline', 'article_title']:
            if key in news_item and news_item[key]:
                return news_item[key]
    # 如果是字符串，直接返回
    elif isinstance(news_item, str):
        return news_item
    # 其他情况返回None
    return None

def process_file(file_path, folder_path):
    """处理单个文件，提取新闻报道"""
    stats["total_files"] += 1
    
    # 只处理JSON文件
    if not (file_path.endswith('.json') or file_path.endswith('.json.gz')):
        return
    
    print(f"正在处理：{file_path}")
    
    # 读取文件
    data = read_json_file(file_path)
    if data is None:
        return
    
    stats["processed_files"] += 1
    
    # 提取新闻项
    news_items = extract_news_items(data)
    
    # 处理每个新闻项
    for news_item in news_items:
        identifier = get_news_identifier(news_item)
        if identifier:
            # 添加到文件夹的新闻集合
            all_news[folder_path].add(identifier)
            # 添加到全局唯一集合
            unique_news.add(identifier)
            stats["total_news"] += 1

def main():
    """主函数，遍历所有文件夹并处理文件"""
    print("开始统计和去重新闻报道数据...")
    print("=" * 70)
    
    # 遍历所有文件夹
    for folder in folders:
        print(f"\n处理文件夹：{folder}")
        print("-" * 50)
        
        # 检查文件夹是否存在
        if not os.path.exists(folder):
            print(f"警告：文件夹不存在 - {folder}")
            continue
        
        # 遍历文件夹及其子目录
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                process_file(file_path, folder)
    
    # 计算去重后的新闻数量
    stats["unique_news_count"] = len(unique_news)
    
    # 生成统计报告
    print("\n" + "=" * 70)
    print("新闻报道数据统计报告")
    print("=" * 70)
    print(f"总文件数：{stats['total_files']}")
    print(f"成功处理文件数：{stats['processed_files']}")
    print(f"处理失败文件数：{stats['error_files']}")
    print(f"原始新闻报道总数：{stats['total_news']}")
    print(f"去重后新闻报道总数：{stats['unique_news_count']}")
    print(f"重复率：{(1 - stats['unique_news_count'] / stats['total_news']) * 100:.2f}%" if stats['total_news'] > 0 else "无数据")
    print("=" * 70)
    
    # 各文件夹详细统计
    print("\n各文件夹新闻报道统计：")
    print("-" * 70)
    print(f"{'文件夹名称':<50} {'新闻数量':<15} {'唯一新闻数量':<15}")
    print("-" * 70)
    
    for folder in folders:
        if folder in all_news:
            folder_news = all_news[folder]
            print(f"{os.path.basename(folder):<50} {len(folder_news):<15} {len(folder_news):<15}")
        else:
            print(f"{os.path.basename(folder):<50} {'0':<15} {'0':<15}")
    
    print("-" * 70)
    print(f"{'总计':<50} {stats['total_news']:<15} {stats['unique_news_count']:<15}")
    
    # 保存统计结果到文件
    report_path = r"c:\Users\13067\Desktop\论文\非洲\demo\news_statistics_report.json"
    report_data = {
        "stats": stats,
        "folder_stats": {folder: len(news) for folder, news in all_news.items()},
        "unique_news_count": stats["unique_news_count"]
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n统计报告已保存到：{report_path}")
    print("\n统计和去重完成！")

if __name__ == "__main__":
    main()