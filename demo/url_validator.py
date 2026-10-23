#!/usr/bin/env python3
"""
URL有效性检测工具
用于检测results_6.json中的URL是否真实可用
"""

import json
import requests
import time
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class URLValidator:
    def __init__(self, max_workers=5, timeout=10):
        self.max_workers = max_workers
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def check_url(self, url):
        """检查单个URL的有效性"""
        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            return {
                'url': url,
                'status_code': response.status_code,
                'valid': response.status_code == 200,
                'error': None
            }
        except requests.exceptions.RequestException as e:
            return {
                'url': url,
                'status_code': None,
                'valid': False,
                'error': str(e)
            }
    
    def validate_urls(self, urls):
        """批量验证URL"""
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.check_url, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results[url] = result
                    status = "有效" if result['valid'] else "无效"
                    logger.info(f"URL检查: {url} - {status} (状态码: {result.get('status_code', 'N/A')})")
                except Exception as e:
                    results[url] = {
                        'url': url,
                        'status_code': None,
                        'valid': False,
                        'error': str(e)
                    }
                    logger.error(f"URL检查异常: {url} - {e}")
        
        return results

def extract_urls_from_results6():
    """从results_6.json中提取所有URL"""
    file_path = r"c:\Users\13067\Desktop\论文\非洲\demo\data\results\results_6.json"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        urls = set()
        for task in data:
            if 'results' in task and isinstance(task['results'], list):
                for article in task['results']:
                    if 'url' in article:
                        urls.add(article['url'])
        
        logger.info(f"从results_6.json中提取到{len(urls)}个唯一URL")
        return list(urls)
    
    except Exception as e:
        logger.error(f"读取results_6.json失败: {e}")
        return []

def analyze_url_patterns(urls):
    """分析URL模式，识别问题"""
    domain_count = {}
    invalid_patterns = []
    
    for url in urls:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            domain_count[domain] = domain_count.get(domain, 0) + 1
            
            # 检查可能的无效模式
            if '/2016/' in url or '/2017/' in url:
                invalid_patterns.append(url)
                
        except Exception as e:
            logger.warning(f"URL解析失败: {url} - {e}")
    
    logger.info("域名统计:")
    for domain, count in sorted(domain_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"  {domain}: {count}个URL")
    
    if invalid_patterns:
        logger.warning(f"发现{len(invalid_patterns)}个可能无效的历史URL")
    
    return domain_count, invalid_patterns

def generate_valid_african_news_urls():
    """生成有效的非洲新闻URL模板"""
    # 基于真实可用的非洲新闻网站
    valid_templates = [
        "https://www.premiumtimesng.com/news/headlines/{year}/month/{slug}",
        "https://www.vanguardngr.com/{year}/{month}/{day}/{slug}",
        "https://mg.co.za/article/{year}-{month}-{day}-{slug}",
        "https://allafrica.com/stories/{year}{month}{day}{slug}.html",
        "https://africanews.com/{year}/{month}/{day}/{slug}",
        "https://www.nation.africa/news/{slug}-{year}",
        "https://www.thecitizen.co.tz/news/{slug}-{year}",
        "https://www.ghanaweb.com/GhanaHomePage/NewsArchive/{slug}-{year}"
    ]
    
    return valid_templates

def main():
    """主函数"""
    logger.info("开始分析results_6.json中的URL有效性...")
    
    # 1. 提取URL
    urls = extract_urls_from_results6()
    if not urls:
        logger.error("未找到URL，程序结束")
        return
    
    # 2. 分析URL模式
    domain_count, invalid_patterns = analyze_url_patterns(urls)
    
    # 3. 验证URL有效性（抽样检查前50个）
    sample_urls = urls[:50] if len(urls) > 50 else urls
    logger.info(f"抽样检查{len(sample_urls)}个URL...")
    
    validator = URLValidator(max_workers=3, timeout=15)
    validation_results = validator.validate_urls(sample_urls)
    
    # 4. 统计结果
    valid_count = sum(1 for result in validation_results.values() if result['valid'])
    invalid_count = len(validation_results) - valid_count
    
    logger.info(f"URL有效性统计:")
    logger.info(f"  有效URL: {valid_count}")
    logger.info(f"  无效URL: {invalid_count}")
    logger.info(f"  有效率: {valid_count/len(validation_results)*100:.1f}%")
    
    # 5. 生成报告
    report = {
        'total_urls': len(urls),
        'sampled_urls': len(sample_urls),
        'valid_urls': valid_count,
        'invalid_urls': invalid_count,
        'validation_rate': valid_count/len(validation_results)*100,
        'domain_distribution': domain_count,
        'sample_results': validation_results
    }
    
    # 保存报告
    with open('url_validation_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info("URL验证报告已保存到: url_validation_report.json")
    
    # 6. 提供修复建议
    if invalid_count > valid_count:
        logger.warning("发现大量无效URL，建议:")
        logger.warning("  1. 使用真实的非洲新闻爬虫重新抓取数据")
        logger.warning("  2. 避免使用历史数据URL模板")
        logger.warning("  3. 使用当前可用的非洲新闻网站")
        
        # 生成有效的URL模板
        valid_templates = generate_valid_african_news_urls()
        logger.info("有效的非洲新闻URL模板:")
        for template in valid_templates:
            logger.info(f"  {template}")

if __name__ == "__main__":
    main()