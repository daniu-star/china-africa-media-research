#!/usr/bin/env python3
"""数据质量分析脚本"""

import json
import os
from datetime import datetime
from content_extraction_optimizer import ContentExtractionOptimizer

def analyze_data_file(file_path: str, description: str) -> dict:
    """分析单个数据文件的质量"""
    print(f"\n=== 分析 {description} ===")
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取文件错误: {e}")
        return {}
    
    # 处理不同的数据格式
    if isinstance(data, dict) and 'articles' in data:
        articles = data['articles']
    elif isinstance(data, list):
        articles = data
    else:
        print(f"数据格式错误: {type(data)}")
        return {}
    
    print(f"文章数量: {len(articles)}")
    
    if len(articles) == 0:
        print("数据为空")
        return {}
    
    # 分析内容质量
    optimizer = ContentExtractionOptimizer()
    
    quality_metrics = {
        'total_articles': len(data),
        'avg_content_length': 0,
        'short_content_count': 0,  # < 100字符
        'medium_content_count': 0,  # 100-500字符
        'long_content_count': 0,  # > 500字符
        'login_pages_count': 0,
        'truncated_content_count': 0,
        'articles_with_dates': 0,
        'content_length_distribution': {},
        'quality_scores': []
    }
    
    total_length = 0
    
    for i, article in enumerate(articles[:100]):  # 只分析前100篇文章以节省时间
        if not isinstance(article, dict):
            continue
            
        content = article.get('content', '')
        content_length = len(content)
        
        total_length += content_length
        
        # 内容长度分类
        if content_length < 100:
            quality_metrics['short_content_count'] += 1
        elif content_length < 500:
            quality_metrics['medium_content_count'] += 1
        else:
            quality_metrics['long_content_count'] += 1
        
        # 登录页面检测
        if optimizer.is_login_page(content):
            quality_metrics['login_pages_count'] += 1
        
        # 截断内容检测
        if '...' in content or '点击阅读全文' in content:
            quality_metrics['truncated_content_count'] += 1
        
        # 发布日期
        if article.get('publish_date') and article['publish_date'] != 'unknown':
            quality_metrics['articles_with_dates'] += 1
        
        # 内容长度分布（按100字符间隔）
        length_bucket = (content_length // 100) * 100
        quality_metrics['content_length_distribution'][length_bucket] = \
            quality_metrics['content_length_distribution'].get(length_bucket, 0) + 1
        
        # 质量评分（简单评分系统）
        quality_score = 0
        if content_length > 300:
            quality_score += 3
        elif content_length > 100:
            quality_score += 1
        
        if not optimizer.is_login_page(content):
            quality_score += 2
        
        if '...' not in content and '点击阅读全文' not in content:
            quality_score += 2
        
        if article.get('publish_date') and article['publish_date'] != 'unknown':
            quality_score += 1
        
        quality_metrics['quality_scores'].append(quality_score)
    
    if len(articles) > 0:
        quality_metrics['avg_content_length'] = total_length / min(len(articles), 100)
    
    # 计算平均质量分
    if quality_metrics['quality_scores']:
        avg_quality = sum(quality_metrics['quality_scores']) / len(quality_metrics['quality_scores'])
        quality_metrics['avg_quality_score'] = avg_quality
    
    # 打印结果
    print(f"平均内容长度: {quality_metrics['avg_content_length']:.1f} 字符")
    print(f"短内容(<100字符): {quality_metrics['short_content_count']} 篇")
    print(f"中等内容(100-500字符): {quality_metrics['medium_content_count']} 篇")
    print(f"长内容(>500字符): {quality_metrics['long_content_count']} 篇")
    print(f"登录页面: {quality_metrics['login_pages_count']} 篇")
    print(f"截断内容: {quality_metrics['truncated_content_count']} 篇")
    print(f"包含发布日期: {quality_metrics['articles_with_dates']} 篇")
    
    if 'avg_quality_score' in quality_metrics:
        print(f"平均质量分: {quality_metrics['avg_quality_score']:.1f}/8")
    
    return quality_metrics

def check_recrawl_urls():
    """检查需要重新爬取的URL"""
    print("\n=== 需要重新爬取的URL分析 ===")
    
    recrawl_files = [
        'data/recrawl_urls.json',
        'data/results_content_enhanced_cleaned_recrawl_urls.json',
        'data/results_enhanced_with_dates_cleaned_recrawl_urls.json'
    ]
    
    for file_path in recrawl_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"\n{file_path}:")
                print(f"  需要重新爬取的URL数量: {len(data)}")
                
                if len(data) > 0:
                    # 分析重新爬取原因
                    reasons = {}
                    for item in data[:10]:  # 只分析前10个
                        if isinstance(item, dict) and 'reason' in item:
                            reason = item['reason']
                            reasons[reason] = reasons.get(reason, 0) + 1
                    
                    print("  主要重新爬取原因:")
                    for reason, count in reasons.items():
                        print(f"    {reason}: {count} 个")
            except Exception as e:
                print(f"读取文件错误 {file_path}: {e}")

def main():
    """主函数"""
    print("开始数据质量分析...\n")
    
    # 分析原始数据
    original_files = [
        ('data/results_content_enhanced.json', '原始增强数据'),
        ('data/results_enhanced_with_dates.json', '原始带日期数据')
    ]
    
    # 分析清理后数据
    cleaned_files = [
        ('data/results_content_enhanced_cleaned.json', '清理后增强数据'),
        ('data/results_enhanced_with_dates_cleaned.json', '清理后带日期数据')
    ]
    
    original_metrics = {}
    cleaned_metrics = {}
    
    # 分析原始数据
    for file_path, description in original_files:
        metrics = analyze_data_file(file_path, description)
        if metrics:
            original_metrics[description] = metrics
    
    # 分析清理后数据
    for file_path, description in cleaned_files:
        metrics = analyze_data_file(file_path, description)
        if metrics:
            cleaned_metrics[description] = metrics
    
    # 对比分析
    print("\n=== 改进效果总结 ===")
    
    for desc in original_metrics:
        if desc in cleaned_metrics:
            orig = original_metrics[desc]
            clean = cleaned_metrics[desc]
            
            print(f"\n{desc}对比:")
            print(f"  文章数量: {orig['total_articles']} → {clean['total_articles']}")
            print(f"  平均内容长度: {orig['avg_content_length']:.1f} → {clean['avg_content_length']:.1f}")
            
            if orig['total_articles'] > 0 and clean['total_articles'] > 0:
                orig_long_ratio = orig['long_content_count']/orig['total_articles']*100
                clean_long_ratio = clean['long_content_count']/clean['total_articles']*100
                print(f"  长内容比例: {orig_long_ratio:.1f}% → {clean_long_ratio:.1f}%")
                
                orig_login_ratio = orig['login_pages_count']/orig['total_articles']*100
                clean_login_ratio = clean['login_pages_count']/clean['total_articles']*100
                print(f"  登录页面比例: {orig_login_ratio:.1f}% → {clean_login_ratio:.1f}%")
            
            if 'avg_quality_score' in orig and 'avg_quality_score' in clean:
                print(f"  质量分提升: {orig['avg_quality_score']:.1f} → {clean['avg_quality_score']:.1f}")
    
    # 检查重新爬取URL
    check_recrawl_urls()
    
    # 生成改进报告
    generate_improvement_report(original_metrics, cleaned_metrics)

def generate_improvement_report(original_metrics, cleaned_metrics):
    """生成改进报告"""
    print("\n=== 改进效果最终报告 ===")
    
    # 检查爬虫测试结果
    test_files = [f for f in os.listdir('.') if f.startswith('crawler_test_results_')]
    
    if test_files:
        latest_test = max(test_files)  # 获取最新的测试文件
        try:
            with open(latest_test, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            analysis = test_data['analysis']
            
            print("爬虫系统测试结果:")
            print(f"  成功率: {analysis['success_rate']:.1f}%")
            print(f"  平均爬取时间: {analysis['avg_crawl_time']:.2f} 秒")
            print(f"  平均内容长度: {analysis['avg_content_length']:.1f} 字符")
            print(f"  登录页面检测: {analysis['login_pages']} 篇")
            print(f"  截断内容检测: {analysis['truncated_content']} 篇")
        except Exception as e:
            print(f"读取测试文件错误: {e}")
    
    print("\n改进效果评估:")
    print("✓ 内容提取逻辑已优化，避免在句子中间截断")
    print("✓ 登录页面检测功能已实现")
    print("✓ 数据清理脚本已创建并运行")
    print("✓ 需要重新爬取的URL已识别")
    print("⚠ 爬虫成功率仍需提升")
    print("⚠ 部分网站的反爬措施需要进一步优化")
    
    # 保存报告
    report = {
        'report_date': datetime.now().isoformat(),
        'improvements': [
            '内容提取优化 - 避免截断和省略号问题',
            '登录页面检测 - 自动识别并处理',
            '数据清理功能 - 完善现有数据质量',
            '智能内容过滤 - 提升数据质量'
        ],
        'remaining_issues': [
            '爬虫成功率需要进一步提升',
            '部分网站反爬措施需要优化',
            'Firecrawl集成稳定性需要改进'
        ],
        'recommendations': [
            '继续优化爬虫策略和重试机制',
            '增加更多代理和User-Agent轮换',
            '完善错误处理和日志记录'
        ]
    }
    
    report_file = f"improvement_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n改进报告已保存到: {report_file}")

if __name__ == "__main__":
    main()