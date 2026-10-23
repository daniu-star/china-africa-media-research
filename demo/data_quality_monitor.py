#!/usr/bin/env python3
"""数据质量监控脚本 - 确保收集的数据质量稳定"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import statistics

class DataQualityMonitor:
    """数据质量监控器"""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir
        self.quality_log = []
        self.start_time = datetime.now()
    
    def analyze_article_quality(self, article: Dict) -> Dict:
        """分析单篇文章的质量"""
        quality_score = 100
        issues = []
        
        # 检查标题
        title = article.get('title', '')
        if not title or len(title.strip()) < 5:
            quality_score -= 20
            issues.append('标题缺失或过短')
        
        # 检查内容
        content = article.get('content', '')
        content_length = len(content.strip())
        
        if content_length == 0:
            quality_score -= 40
            issues.append('内容为空')
        elif content_length < 100:
            quality_score -= 20
            issues.append('内容过短')
        elif content_length > 5000:
            quality_score -= 10
            issues.append('内容过长')
        
        # 检查URL
        url = article.get('url', '')
        if not url or not url.startswith('http'):
            quality_score -= 15
            issues.append('URL无效')
        
        # 检查发布日期
        publish_date = article.get('publish_date')
        if not publish_date:
            quality_score -= 10
            issues.append('发布日期缺失')
        
        # 检查截断内容
        if '...' in content and content.count('...') > 3:
            quality_score -= 15
            issues.append('内容可能被截断')
        
        # 检查登录页面关键词
        login_keywords = ['login', 'sign in', 'log in', 'password', 'username', '账户', '登录', '密码']
        content_lower = content.lower()
        if any(keyword in content_lower for keyword in login_keywords):
            quality_score -= 25
            issues.append('可能为登录页面')
        
        quality_score = max(0, quality_score)
        
        return {
            'quality_score': quality_score,
            'quality_status': 'excellent' if quality_score >= 90 else 'good' if quality_score >= 70 else 'fair' if quality_score >= 50 else 'poor',
            'issues': issues,
            'content_length': content_length,
            'has_title': bool(title and len(title.strip()) >= 5),
            'has_valid_url': bool(url and url.startswith('http')),
            'has_publish_date': bool(publish_date)
        }
    
    def analyze_data_file(self, file_path: str) -> Dict:
        """分析单个数据文件的质量"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            articles = []
            if isinstance(data, dict) and 'articles' in data:
                articles = data['articles']
            elif isinstance(data, list):
                articles = data
            else:
                return {'error': f'Invalid data format in {file_path}'}
            
            if not articles:
                return {'error': f'No articles found in {file_path}'}
            
            quality_analysis = []
            total_articles = len(articles)
            
            # 限制分析数量以避免内存问题
            max_articles_to_analyze = min(1000, total_articles)
            
            for article in articles[:max_articles_to_analyze]:
                quality_analysis.append(self.analyze_article_quality(article))
            
            # 计算统计信息
            quality_scores = [q['quality_score'] for q in quality_analysis]
            content_lengths = [q['content_length'] for q in quality_analysis]
            
            stats = {
                'file_path': file_path,
                'total_articles_analyzed': len(quality_analysis),
                'total_articles_in_file': total_articles,
                'avg_quality_score': statistics.mean(quality_scores) if quality_scores else 0,
                'median_quality_score': statistics.median(quality_scores) if quality_scores else 0,
                'min_quality_score': min(quality_scores) if quality_scores else 0,
                'max_quality_score': max(quality_scores) if quality_scores else 0,
                'avg_content_length': statistics.mean(content_lengths) if content_lengths else 0,
                'quality_distribution': {
                    'excellent': len([q for q in quality_analysis if q['quality_status'] == 'excellent']),
                    'good': len([q for q in quality_analysis if q['quality_status'] == 'good']),
                    'fair': len([q for q in quality_analysis if q['quality_status'] == 'fair']),
                    'poor': len([q for q in quality_analysis if q['quality_status'] == 'poor'])
                },
                'common_issues': self.analyze_common_issues(quality_analysis),
                'sample_articles': quality_analysis[:5]  # 前5篇文章的详细分析
            }
            
            return stats
            
        except Exception as e:
            return {'error': f'Error analyzing {file_path}: {str(e)}'}
    
    def analyze_common_issues(self, quality_analysis: List[Dict]) -> Dict:
        """分析常见问题"""
        all_issues = []
        for analysis in quality_analysis:
            all_issues.extend(analysis['issues'])
        
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        return dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def generate_quality_report(self) -> Dict:
        """生成数据质量报告"""
        if not os.path.exists(self.data_dir):
            return {'error': f'Data directory {self.data_dir} does not exist'}
        
        # 只分析包含文章数据的文件
        article_data_files = [
            f for f in os.listdir(self.data_dir) 
            if f.endswith('.json') and 
               ('results' in f.lower() or 'articles' in f.lower()) and
               'recrawl' not in f.lower() and
               'report' not in f.lower() and
               'strategy' not in f.lower() and
               'monitor' not in f.lower() and
               'progress' not in f.lower() and
               'optimization' not in f.lower()
        ]
        
        if not article_data_files:
            return {'error': 'No article data files found'}
        
        file_analyses = []
        total_articles = 0
        
        for data_file in article_data_files[:5]:  # 最多分析5个数据文件
            file_path = os.path.join(self.data_dir, data_file)
            analysis = self.analyze_data_file(file_path)
            
            if 'error' not in analysis:
                file_analyses.append(analysis)
                total_articles += analysis['total_articles_in_file']
        
        if not file_analyses:
            return {'error': 'No valid article data files could be analyzed'}
        
        # 计算总体统计
        all_quality_scores = []
        all_content_lengths = []
        quality_distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        
        for analysis in file_analyses:
            all_quality_scores.append(analysis['avg_quality_score'])
            all_content_lengths.append(analysis['avg_content_length'])
            
            for status, count in analysis['quality_distribution'].items():
                quality_distribution[status] += count
        
        overall_quality_score = statistics.mean(all_quality_scores) if all_quality_scores else 0
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'data_files_analyzed': len(file_analyses),
            'total_articles': total_articles,
            'overall_quality_score': overall_quality_score,
            'overall_quality_status': 'excellent' if overall_quality_score >= 90 else 'good' if overall_quality_score >= 70 else 'fair' if overall_quality_score >= 50 else 'poor',
            'avg_content_length': statistics.mean(all_content_lengths) if all_content_lengths else 0,
            'quality_distribution': quality_distribution,
            'file_analyses': file_analyses,
            'trend_analysis': self.analyze_trends()
        }
        
        self.quality_log.append(report)
        return report
    
    def analyze_trends(self) -> Dict:
        """分析质量趋势"""
        if len(self.quality_log) < 2:
            return {'message': '需要更多数据点来分析趋势'}
        
        recent_reports = self.quality_log[-5:]  # 最近5个报告
        
        quality_scores = [r['overall_quality_score'] for r in recent_reports]
        
        if len(quality_scores) >= 2:
            # 计算趋势
            trend = 'stable'
            if quality_scores[-1] > quality_scores[0] + 5:
                trend = 'improving'
            elif quality_scores[-1] < quality_scores[0] - 5:
                trend = 'declining'
            
            return {
                'trend': trend,
                'change_percentage': ((quality_scores[-1] - quality_scores[0]) / quality_scores[0] * 100) if quality_scores[0] > 0 else 0,
                'periods_compared': len(quality_scores)
            }
        
        return {'trend': 'insufficient_data'}
    
    def save_quality_report(self, report: Dict):
        """保存质量报告"""
        report_file = f"data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"数据质量报告已保存到: {report_file}")
        
        # 同时保存到质量日志
        log_file = "data_quality_log.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.quality_log[-50:], f, ensure_ascii=False, indent=2)  # 只保存最近50条记录

def monitor_data_quality_continuously(interval_hours: int = 6, duration_days: int = 7):
    """持续监控数据质量"""
    monitor = DataQualityMonitor()
    end_time = datetime.now() + timedelta(days=duration_days)
    
    print(f"开始数据质量监控，将持续{duration_days}天，每{interval_hours}小时检查一次")
    print(f"监控结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    while datetime.now() < end_time:
        try:
            print(f"\n=== 数据质量检查 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
            
            report = monitor.generate_quality_report()
            
            if 'error' in report:
                print(f"错误: {report['error']}")
            else:
                # 打印摘要信息
                print(f"总体质量: {report['overall_quality_score']:.1f}/100 ({report['overall_quality_status']})")
                print(f"分析文件数: {report['data_files_analyzed']}")
                print(f"总文章数: {report['total_articles']}")
                print(f"平均内容长度: {report['avg_content_length']:.0f} 字符")
                
                # 质量分布
                dist = report['quality_distribution']
                total = sum(dist.values())
                if total > 0:
                    print(f"质量分布: 优秀{dist['excellent']}({dist['excellent']/total*100:.1f}%) "
                          f"良好{dist['good']}({dist['good']/total*100:.1f}%) "
                          f"一般{dist['fair']}({dist['fair']/total*100:.1f}%) "
                          f"较差{dist['poor']}({dist['poor']/total*100:.1f}%)")
                
                # 趋势分析
                if 'trend' in report['trend_analysis']:
                    trend = report['trend_analysis']['trend']
                    if trend != 'insufficient_data':
                        print(f"质量趋势: {trend}")
                
                # 保存报告
                monitor.save_quality_report(report)
            
            # 等待下一次检查
            print(f"\n等待{interval_hours}小时后进行下一次检查...")
            time.sleep(interval_hours * 3600)
            
        except KeyboardInterrupt:
            print("\n监控被用户中断")
            break
        except Exception as e:
            print(f"监控过程中发生错误: {e}")
            time.sleep(3600)  # 出错后等待1小时再继续
    
    print(f"\n数据质量监控完成")

def quick_quality_check():
    """快速数据质量检查"""
    monitor = DataQualityMonitor()
    report = monitor.generate_quality_report()
    
    if 'error' in report:
        print(f"错误: {report['error']}")
        return report
    
    print("=== 快速数据质量检查报告 ===")
    print(f"总体质量: {report['overall_quality_score']:.1f}/100 ({report['overall_quality_status']})")
    print(f"分析文件数: {report['data_files_analyzed']}")
    print(f"总文章数: {report['total_articles']}")
    print(f"平均内容长度: {report['avg_content_length']:.0f} 字符")
    
    # 质量分布
    dist = report['quality_distribution']
    total = sum(dist.values())
    if total > 0:
        print(f"质量分布:")
        print(f"  优秀: {dist['excellent']} 篇 ({dist['excellent']/total*100:.1f}%)")
        print(f"  良好: {dist['good']} 篇 ({dist['good']/total*100:.1f}%)")
        print(f"  一般: {dist['fair']} 篇 ({dist['fair']/total*100:.1f}%)")
        print(f"  较差: {dist['poor']} 篇 ({dist['poor']/total*100:.1f}%)")
    
    # 显示常见问题
    if report['file_analyses'] and 'common_issues' in report['file_analyses'][0]:
        common_issues = report['file_analyses'][0]['common_issues']
        if common_issues:
            print("\n常见问题:")
            for issue, count in list(common_issues.items())[:5]:
                print(f"  • {issue}: {count} 次")
    
    # 保存报告
    monitor.save_quality_report(report)
    
    return report

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='数据质量监控工具')
    parser.add_argument('--mode', choices=['continuous', 'quick'], default='quick',
                       help='监控模式: continuous(持续监控) 或 quick(快速检查)')
    parser.add_argument('--interval', type=int, default=6,
                       help='持续监控的检查间隔(小时)')
    parser.add_argument('--duration', type=int, default=7,
                       help='持续监控的持续时间(天)')
    
    args = parser.parse_args()
    
    if args.mode == 'continuous':
        monitor_data_quality_continuously(args.interval, args.duration)
    else:
        quick_quality_check()