import os
import json
import hashlib
from datetime import datetime

# 定义要检查的文件夹和文件
TARGET_FOLDERS = [
    'backup',
    'backups',
    'china_africa_results',
    'crawler_results',
    'data',
    'firecrawl_early_data_results',
    'live_playwright_results',
    'local_results',
    'massive_crawler_results',
    'optimized_crawler_results',
    'static',
    'templates'
]

TARGET_FILES = [
    'adaptive_learning_config.json',
    'advanced_sample_investment_data.json',
    'africa_website_optimization.json',
    'all_unique_news_data.json',
    'api_ahram_all_articles.json',
    'api_ahram_economic cooperation_articles.json',
    'api_ahram_egypt_articles.json',
    'api_ahram_investment_articles.json',
    'api_ahram_technology_articles.json',
    'banned_sites.json',
    'brightdata_actual_all_articles.json',
    'brightdata_actual_economic_cooperation_articles.json',
    'brightdata_actual_free_trade_articles.json',
    'brightdata_actual_investment_articles.json',
    'brightdata_actual_market_articles.json',
    'brightdata_ahram_all_articles.json',
    'brightdata_ahram_economic_cooperation_articles.json',
    'brightdata_ahram_free_trade_articles.json',
    'brightdata_ahram_investment_articles.json',
    'brightdata_ahram_market_articles.json',
    'brightdata_config_example.json',
    'brightdata_config_guide.json',
    'brightdata_mcp_all_articles.json',
    'brightdata_mcp_direct_test_results.json',
    'brightdata_mcp_economic_cooperation_articles.json',
    'brightdata_mcp_egypt_articles.json',
    'brightdata_mcp_free_trade_articles.json',
    'brightdata_mcp_investment_articles.json',
    'brightdata_mcp_market_articles.json',
    'crawled_data_formatted.json',
    'crawled_data_summary.json',
    'crawler_optimization_config.json',
    'crawler_progress.json',
    'emergency_backup_2b8be5d2-e85b-4d0c-93ff-9a438ede0c6f_20251120_142552.json',
    'emergency_backup_6e1d113c-2068-448f-bdab-8e2614c245a0_20251120_152644.json',
    'emergency_backup_7afc3c38-4c8b-4377-9244-e94500dcf8eb_20251120_120118.json',
    'emergency_backup_8c7e1c01-8f95-4c99-9bbf-155139d8a51e_20251120_151032.json',
    'emergency_backup_15adb5c9-27a4-4c3c-9d8f-61d0bf8cb797_20251120_120232.json',
    'emergency_backup_17a2ee7f-8b12-4249-8d09-7e7f3f5b03eb_20251120_142216.json',
    'emergency_backup_20e67fab-d9ed-44e2-a6d7-3ebeaa9752cc_20251120_144107.json',
    'emergency_backup_27da0722-7586-48af-a902-0627e20b404a_20251120_152914.json',
    'emergency_backup_27da0722-7586-48af-a902-0627e20b404a_20251120_152915.json',
    'emergency_backup_81e654eb-fc54-4a5e-b238-87ac19a9f8e6_20251120_113758.json',
    'emergency_backup_92a0fc27-7a26-434a-ab63-b292d26fb5ca_20251120_153149.json',
    'emergency_backup_92a0fc27-7a26-434a-ab63-b292d26fb5ca_20251120_153150.json',
    'emergency_backup_412766c0-3c35-414a-ac88-31c4f21a39e4_20251120_150703.json',
    'emergency_backup_52999074-08dd-4682-bdb2-4038541f44b6_20251120_151913.json',
    'emergency_backup_412766c0-3c35-414a-ac88-31c4f21a39e4_20251120_150740.json',
    'emergency_backup_a7e95d54-b60e-4d60-af7d-5a34585cea63_20251120_142658.json',
    'emergency_backup_d62ce4f3-23bd-4fb6-ba17-0a282bc65b31_20251120_151448.json',
    'emergency_backup_d1073851-db3e-44ec-83cf-3f4a069f7f84_20251120_113902.json',
    'emergency_backup_debb540f-58f7-4ad8-aa7f-50afebfe5522_20251120_152429.json',
    'emergency_backup_debb540f-58f7-4ad8-aa7f-50afebfe5522_20251120_152430.json',
    'emergency_backup_df395108-e5e4-47c9-bfd1-8cd3649669ff_20251120_112710.json',
    'emergency_backup_dffdca59-a1b5-418a-a466-c05f921a30a9_20251120_115619.json',
    'emergency_backup_e2b75496-b203-4a30-b2f3-1abd0e6922d1_20251120_145755.json',
    'emergency_backup_e3de9d72-fc11-4008-b661-c50ee714bc18_20251120_143346.json',
    'emergency_backup_ea1c3564-1864-4d16-8bba-6c430a3da8dd_20251120_114510.json',
    'emergency_backup_f08b59db-24f7-4b63-b004-1e12309c139b_20251120_115731.json',
    'emergency_backup_f413ea46-bf32-403f-b563-d6cb7548706d_20251120_142218.json',
    'emergency_backup_f575c80c-b6f7-453d-9253-875d8567a84b_20251120_150047.json',
    'free_proxy_ahram_all_articles.json',
    'free_proxy_ahram_egypt_articles.json',
    'free_proxy_ahram_technology_articles.json',
    'investment_crawler_config.json',
    'large_scale_crawling_config.json',
    'massive_crawler_config.json',
    'massive_crawler_progress.json',
    'adaptive_learning_config.json',
    'optimized_crawler_config.json',
    'proxy_config.json',
    'real_firecrawl_investment_data.json',
    'sample_investment_data.json',
    'scrapingbee_ahram_all_articles.json',
    'scrapingbee_ahram_economic_cooperation_articles.json',
    'scrapingbee_ahram_egypt_articles.json',
    'scrapingbee_ahram_investment_articles.json',
    'scrapingbee_ahram_technology_articles.json',
    'year_filter_data.json'
]

# 获取文件的完整路径
def get_full_path(filename):
    return os.path.join('c:\\Users\\13067\\Desktop\\论文\\非洲\\demo', filename)

# 生成文章的唯一标识符
def generate_article_id(article):
    # 使用标题、URL和内容的组合生成唯一哈希
    # 处理字符串类型的文章对象
    if isinstance(article, str):
        return hashlib.md5(article.encode('utf-8')).hexdigest()
    # 处理列表类型的文章对象
    elif isinstance(article, list):
        return hashlib.md5(str(article).encode('utf-8')).hexdigest()
    # 处理字典类型的文章对象
    elif isinstance(article, dict):
        unique_str = f"{article.get('title', '')}{article.get('url', '')}{article.get('content', '')}"
        return hashlib.md5(unique_str.encode('utf-8')).hexdigest()
    # 处理其他类型的文章对象
    else:
        return hashlib.md5(str(article).encode('utf-8')).hexdigest()

# 从文件中提取文章
def extract_articles_from_file(file_path):
    articles = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 处理不同的数据格式
        if isinstance(data, list):
            # 直接是文章列表
            articles = data
        elif isinstance(data, dict):
            # 检查是否包含articles字段
            if 'articles' in data and isinstance(data['articles'], list):
                articles = data['articles']
            # 检查是否是紧急备份格式
            elif 'result' in data and isinstance(data['result'], dict):
                result = data['result']
                if 'articles' in result and isinstance(result['articles'], list):
                    articles = result['articles']
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return articles

# 遍历文件夹并收集所有JSON文件
def collect_all_json_files():
    all_json_files = []
    base_dir = 'c:\\Users\\13067\\Desktop\\论文\\非洲\\demo'
    
    # 遍历目标文件夹
    for folder in TARGET_FOLDERS:
        folder_path = os.path.join(base_dir, folder)
        if os.path.exists(folder_path):
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.endswith('.json'):
                        all_json_files.append(os.path.join(root, file))
    
    # 添加目标文件
    for file in TARGET_FILES:
        file_path = os.path.join(base_dir, file)
        if os.path.exists(file_path):
            all_json_files.append(file_path)
    
    return all_json_files

# 主函数
def main():
    print("开始分析新闻数据...")
    
    # 收集所有JSON文件
    all_json_files = collect_all_json_files()
    print(f"共找到 {len(all_json_files)} 个JSON文件")
    
    # 提取所有文章
    all_articles = []
    file_article_count = {}
    
    for file_path in all_json_files:
        articles = extract_articles_from_file(file_path)
        if articles:
            all_articles.extend(articles)
            file_article_count[file_path] = len(articles)
            print(f"从 {file_path} 提取了 {len(articles)} 篇文章")
    
    print(f"\n总共提取了 {len(all_articles)} 篇文章")
    
    # 去重处理
    unique_articles = {}
    duplicate_count = 0
    
    for article in all_articles:
        article_id = generate_article_id(article)
        if article_id not in unique_articles:
            unique_articles[article_id] = article
        else:
            duplicate_count += 1
    
    unique_article_list = list(unique_articles.values())
    print(f"去重后剩余 {len(unique_article_list)} 篇文章")
    print(f"共移除了 {duplicate_count} 篇重复文章")
    
    # 保存去重后的结果
    output_file = get_full_path('unique_news_data_final.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_article_list, f, ensure_ascii=False, indent=2)
    
    print(f"\n去重后的文章已保存到: {output_file}")
    
    # 生成统计报告
    report = {
        'total_files_scanned': len(all_json_files),
        'total_articles_extracted': len(all_articles),
        'total_unique_articles': len(unique_article_list),
        'duplicate_articles_removed': duplicate_count,
        'processing_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'file_article_details': file_article_count
    }
    
    report_file = get_full_path('news_data_analysis_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"分析报告已保存到: {report_file}")
    print("\n分析完成！")

if __name__ == "__main__":
    main()