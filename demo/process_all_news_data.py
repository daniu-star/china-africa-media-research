import os
import json
import gzip
from collections import defaultdict

# 指定要处理的路径列表
paths = [
    r"c:\Users\13067\Desktop\论文\非洲\demo\backup",
    r"c:\Users\13067\Desktop\论文\非洲\demo\backups",
    r"c:\Users\13067\Desktop\论文\非洲\demo\china_africa_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\crawler_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\firecrawl_early_data_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\data",
    r"c:\Users\13067\Desktop\论文\非洲\demo\live_playwright_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\local_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\optimized_crawler_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\massive_crawler_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\templates",
    r"c:\Users\13067\Desktop\论文\非洲\demo\static",
    r"c:\Users\13067\Desktop\论文\非洲\demo\models",
    r"c:\Users\13067\Desktop\论文\非洲\demo\api_ahram_all_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\api_ahram_economic cooperation_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\api_ahram_egypt_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\api_ahram_investment_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\api_ahram_technology_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\banned_sites.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_actual_all_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_actual_economic_cooperation_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_actual_free_trade_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_actual_investment_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_actual_market_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_ahram_all_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_ahram_economic_cooperation_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_ahram_free_trade_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_ahram_investment_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_ahram_market_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_config_example.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_config_guide.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_mcp_all_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_mcp_direct_test_results.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_mcp_economic_cooperation_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_mcp_egypt_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_mcp_free_trade_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_mcp_investment_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\brightdata_mcp_market_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\massive_crawler_config.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\massive_crawler_progress.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\free_proxy_ahram_all_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\free_proxy_ahram_egypt_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\free_proxy_ahram_technology_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\investment_crawler_config.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\large_scale_crawling_config.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_f575c80c-b6f7-453d-9253-875d8567a84b_20251120_150047.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_f413ea46-bf32-403f-b563-d6cb7548706d_20251120_142218.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_f08b59db-24f7-4b63-b004-1e12309c139b_20251120_115731.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_ea1c3564-1864-4d16-8bba-6c430a3da8dd_20251120_114510.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_e3de9d72-fc11-4008-b661-c50ee714bc18_20251120_143346.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_e2b75496-b203-4a30-b2f3-1abd0e6922d1_20251120_145755.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_dffdca59-a1b5-418a-a466-c05f921a30a9_20251120_115619.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_debb540f-58f7-4ad8-aa7f-50afebfe5522_20251120_152430.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_df395108-e5e4-47c9-bfd1-8cd3649669ff_20251120_112710.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_debb540f-58f7-4ad8-aa7f-50afebfe5522_20251120_152429.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_d1073851-db3e-44ec-83cf-3f4a069f7f84_20251120_113902.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_a7e95d54-b60e-4d60-af7d-5a34585cea63_20251120_142658.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_d62ce4f3-23bd-4fb6-ba17-0a282bc65b31_20251120_151448.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_52999074-08dd-4682-bdb2-4038541f44b6_20251120_151913.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_412766c0-3c35-414a-ac88-31c4f21a39e4_20251120_150740.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_412766c0-3c35-414a-ac88-31c4f21a39e4_20251120_150703.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_92a0fc27-7a26-434a-ab63-b292d26fb5ca_20251120_153150.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_92a0fc27-7a26-434a-ab63-b292d26fb5ca_20251120_153149.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_27da0722-7586-48af-a902-0627e20b404a_20251120_152915.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_81e654eb-fc54-4a5e-b238-87ac19a9f8e6_20251120_113758.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_27da0722-7586-48af-a902-0627e20b404a_20251120_152914.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_20e67fab-d9ed-44e2-a6d7-3ebeaa9752cc_20251120_144107.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_15adb5c9-27a4-4c3c-9d8f-61d0bf8cb797_20251120_120232.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_17a2ee7f-8b12-4249-8d09-7e7f3f5b03eb_20251120_142216.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_8c7e1c01-8f95-4c99-9bbf-155139d8a51e_20251120_151032.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_6e1d113c-2068-448f-bdab-8e2614c245a0_20251120_152644.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_7afc3c38-4c8b-4377-9244-e94500dcf8eb_20251120_120118.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\emergency_backup_2b8be5d2-e85b-4d0c-93ff-9a438ede0c6f_20251120_142552.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\free_proxy_ahram_all_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\free_proxy_ahram_egypt_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\free_proxy_ahram_technology_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\investment_crawler_config.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\large_scale_crawling_config.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\massive_crawler_config.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\massive_crawler_progress.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\optimized_crawler_config.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\proxy_config.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\real_firecrawl_investment_data.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\sample_investment_data.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\scrapingbee_ahram_all_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\scrapingbee_ahram_economic_cooperation_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\scrapingbee_ahram_egypt_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\scrapingbee_ahram_investment_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\scrapingbee_ahram_technology_articles.json",
    r"c:\Users\13067\Desktop\论文\非洲\demo\year_filter_data.json"
]

# 存储所有新闻报道的唯一标识符（URL或标题）
news_dict = {}
all_news = []

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
        # 检查是否是紧急备份格式
        if "result" in data and isinstance(data["result"], dict):
            if "articles" in data["result"] and isinstance(data["result"]["articles"], list):
                news_items = data["result"]["articles"]
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

def process_file(file_path):
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
            # 去重：如果标识符不存在，则添加到字典和列表中
            if identifier not in news_dict:
                news_dict[identifier] = news_item
                all_news.append(news_item)
                stats["unique_news_count"] += 1
            stats["total_news"] += 1

def process_path(path):
    """处理单个路径，可能是文件或文件夹"""
    if os.path.isfile(path):
        # 处理单个文件
        process_file(path)
    elif os.path.isdir(path):
        # 处理文件夹，遍历所有子目录和文件
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                process_file(file_path)
    else:
        print(f"警告：路径不存在 - {path}")

def main():
    """主函数，处理所有路径"""
    print("开始处理所有新闻数据...")
    print("=" * 70)
    
    # 处理所有路径
    for path in paths:
        process_path(path)
    
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
    
    # 保存去重后的所有数据
    output_path = r"c:\Users\13067\Desktop\论文\非洲\demo\all_unique_news_data.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
    
    print(f"\n去重后的所有新闻数据已保存到：{output_path}")
    print(f"保存的新闻数量：{len(all_news)}")
    print("\n处理完成！")

if __name__ == "__main__":
    main()