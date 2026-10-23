"""
数据质量管理系统 - 综合监控、分析和优化数据质量
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from data_quality_monitor import DataQualityMonitor
from data_quality_enhancer import DataQualityEnhancer
from smart_page_filter import SmartPageFilter
from login_page_filter import LoginPageFilter

class DataQualityManagementSystem:
    """数据质量管理系统"""
    
    def __init__(self, data_dir: str = "data/results"):
        """
        初始化数据质量管理系统
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.enhanced_dir = "data/enhanced"
        self.reports_dir = "data/quality_reports"
        
        # 初始化组件
        self.monitor = DataQualityMonitor()
        self.enhancer = DataQualityEnhancer()
        self.smart_filter = SmartPageFilter()
        self.login_filter = LoginPageFilter()
        
        # 创建目录
        os.makedirs(self.enhanced_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # 系统状态
        self.system_status = {
            'last_monitor_time': None,
            'last_enhancement_time': None,
            'total_articles_processed': 0,
            'quality_score_history': [],
            'issues_resolved': 0
        }
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """运行综合分析"""
        print("=== 开始数据质量综合分析 ===")
        
        # 1. 数据质量监控
        print("\n1. 执行数据质量监控...")
        monitor_report = self.monitor.generate_quality_report()
        
        # 2. 数据质量增强
        print("\n2. 执行数据质量增强...")
        enhancement_result = self.enhancer.enhance_data(self.data_dir)
        
        # 3. 趋势分析
        print("\n3. 执行质量趋势分析...")
        trend_analysis = self.analyze_quality_trends()
        
        # 4. 生成综合报告
        print("\n4. 生成综合报告...")
        comprehensive_report = self.generate_comprehensive_report(
            monitor_report, 
            enhancement_result, 
            trend_analysis
        )
        
        # 5. 保存系统状态
        self.update_system_status(comprehensive_report)
        
        print("\n=== 数据质量综合分析完成 ===")
        return comprehensive_report
    
    def analyze_quality_trends(self) -> Dict[str, Any]:
        """分析质量趋势"""
        # 加载历史报告
        history_reports = self.load_history_reports()
        
        if len(history_reports) < 2:
            return {
                'trend': 'insufficient_data',
                'message': '需要更多历史数据来进行趋势分析'
            }
        
        # 分析质量分数趋势
        quality_scores = [report.get('overall_score', 0) for report in history_reports]
        
        # 计算趋势
        if len(quality_scores) >= 2:
            recent_scores = quality_scores[-5:]  # 最近5个分数
            if len(recent_scores) >= 2:
                trend = 'improving' if recent_scores[-1] > recent_scores[0] else 'declining'
                trend_strength = abs(recent_scores[-1] - recent_scores[0])
            else:
                trend = 'stable'
                trend_strength = 0
        else:
            trend = 'stable'
            trend_strength = 0
        
        return {
            'trend': trend,
            'trend_strength': trend_strength,
            'recent_scores': quality_scores[-5:],
            'average_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'total_reports': len(history_reports)
        }
    
    def load_history_reports(self) -> List[Dict[str, Any]]:
        """加载历史报告"""
        reports = []
        
        if not os.path.exists(self.reports_dir):
            return reports
        
        for filename in os.listdir(self.reports_dir):
            if filename.startswith('comprehensive_report_') and filename.endswith('.json'):
                filepath = os.path.join(self.reports_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                        reports.append(report)
                except Exception as e:
                    print(f"加载历史报告失败 {filename}: {e}")
        
        # 按时间排序
        reports.sort(key=lambda x: x.get('timestamp', ''))
        return reports
    
    def generate_comprehensive_report(self, 
                                    monitor_report: Dict[str, Any], 
                                    enhancement_result: Dict[str, Any],
                                    trend_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合报告"""
        
        enhancement_report = enhancement_result.get('report', {})
        
        # 计算总体质量评分
        monitor_score = monitor_report.get('overall_score', 0)
        enhancement_rate = enhancement_report.get('improvement_rate', 0)
        
        # 综合评分公式
        overall_score = (monitor_score * 0.6 + enhancement_rate * 0.4)
        
        # 评估质量等级
        if overall_score >= 90:
            quality_grade = '优秀'
        elif overall_score >= 80:
            quality_grade = '良好'
        elif overall_score >= 70:
            quality_grade = '一般'
        else:
            quality_grade = '需要改进'
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': round(overall_score, 2),
            'quality_grade': quality_grade,
            'monitoring_section': {
                'original_articles': monitor_report.get('total_articles', 0),
                'quality_distribution': monitor_report.get('quality_distribution', {}),
                'common_issues': monitor_report.get('common_issues', []),
                'monitor_score': monitor_score
            },
            'enhancement_section': {
                'enhanced_articles': enhancement_report.get('enhanced_count', 0),
                'improvement_rate': enhancement_report.get('improvement_rate', 0),
                'issues_resolved': enhancement_report.get('details', {}),
                'quality_improvement': enhancement_report.get('quality_improvement', 0)
            },
            'trend_analysis': trend_analysis,
            'recommendations': self.generate_recommendations(monitor_report, enhancement_report, trend_analysis)
        }
        
        # 保存报告
        self.save_comprehensive_report(report)
        
        return report
    
    def generate_recommendations(self, 
                               monitor_report: Dict[str, Any], 
                               enhancement_report: Dict[str, Any],
                               trend_analysis: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于监控报告的建议
        common_issues = monitor_report.get('common_issues', [])
        for issue in common_issues:
            if issue['count'] > 50:  # 问题出现次数较多
                if 'login' in issue['issue'].lower():
                    recommendations.append("优化爬虫策略，避免抓取登录页面")
                elif 'short' in issue['issue'].lower():
                    recommendations.append("提高内容长度阈值，过滤过短内容")
                elif 'duplicate' in issue['issue'].lower():
                    recommendations.append("加强去重机制，避免重复内容")
        
        # 基于增强报告的建议
        enhancement_details = enhancement_report.get('details', {})
        if enhancement_details.get('login_pages_removed', 0) > 0:
            recommendations.append("登录页面过滤效果良好，继续保持")
        if enhancement_details.get('short_content_removed', 0) > 0:
            recommendations.append("内容过短问题已有效处理")
        
        # 基于趋势分析的建议
        trend = trend_analysis.get('trend', 'stable')
        if trend == 'declining':
            recommendations.append("数据质量呈下降趋势，需要优化爬虫策略")
        elif trend == 'improving':
            recommendations.append("数据质量持续改善，继续保持当前策略")
        
        # 通用建议
        if len(recommendations) == 0:
            recommendations.append("数据质量良好，建议定期监控和维护")
        
        return recommendations[:5]  # 最多返回5条建议
    
    def save_comprehensive_report(self, report: Dict[str, Any]):
        """保存综合报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_report_{timestamp}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"综合报告已保存到: {filepath}")
    
    def update_system_status(self, report: Dict[str, Any]):
        """更新系统状态"""
        self.system_status['last_monitor_time'] = datetime.now().isoformat()
        self.system_status['last_enhancement_time'] = datetime.now().isoformat()
        
        # 更新质量分数历史
        self.system_status['quality_score_history'].append({
            'timestamp': report['timestamp'],
            'score': report['overall_score']
        })
        
        # 保留最近10个分数
        if len(self.system_status['quality_score_history']) > 10:
            self.system_status['quality_score_history'] = self.system_status['quality_score_history'][-10:]
        
        # 保存系统状态
        status_file = os.path.join(self.reports_dir, 'system_status.json')
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(self.system_status, f, ensure_ascii=False, indent=2)
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return self.system_status
    
    def run_continuous_monitoring(self, interval_hours: int = 24):
        """运行持续监控"""
        print(f"启动持续监控，每 {interval_hours} 小时执行一次")
        
        while True:
            try:
                # 执行综合分析
                report = self.run_comprehensive_analysis()
                
                # 打印监控结果
                self.print_monitoring_summary(report)
                
                # 等待指定时间间隔
                print(f"等待 {interval_hours} 小时后执行下一次监控...")
                time.sleep(interval_hours * 3600)
                
            except KeyboardInterrupt:
                print("\n监控已停止")
                break
            except Exception as e:
                print(f"监控执行出错: {e}")
                time.sleep(3600)  # 出错后等待1小时
    
    def print_monitoring_summary(self, report: Dict[str, Any]):
        """打印监控摘要"""
        print("\n=== 数据质量监控摘要 ===")
        print(f"总体质量评分: {report['overall_score']}/100 ({report['quality_grade']})")
        print(f"原始文章数量: {report['monitoring_section']['original_articles']}")
        print(f"增强后文章数量: {report['enhancement_section']['enhanced_articles']}")
        print(f"质量提升率: {report['enhancement_section']['improvement_rate']}%")
        print(f"趋势分析: {report['trend_analysis']['trend']}")
        print("主要建议:")
        for i, rec in enumerate(report['recommendations'][:3], 1):
            print(f"  {i}. {rec}")

    def evaluate_article_quality(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估单篇文章的质量
        
        Args:
            article: 文章数据字典
            
        Returns:
            包含评估结果的字典:
            {
                'is_valid': bool,  # 文章是否有效
                'issues': List[str],  # 质量问题列表
                'quality_score': float,  # 质量评分(0-100)
                'recommendations': List[str]  # 改进建议
            }
        """
        issues = []
        quality_score = 100.0  # 初始满分
        
        # 1. 检查标题
        title = article.get('title', '').strip()
        if not title or len(title) < 5:
            issues.append("标题过短或缺失")
            quality_score -= 20
        elif len(title) > 200:
            issues.append("标题过长")
            quality_score -= 10
        
        # 2. 检查内容
        content = article.get('content', '').strip()
        if not content or len(content) < 100:
            issues.append("内容过短或缺失")
            quality_score -= 30
        elif len(content) < 300:
            issues.append("内容较短")
            quality_score -= 10
        
        # 3. 检查URL
        url = article.get('url', '').strip()
        if not url or not url.startswith(('http://', 'https://')):
            issues.append("URL无效")
            quality_score -= 15
        
        # 4. 检查发布日期
        publish_date = article.get('publish_date', '').strip()
        if not publish_date:
            issues.append("发布日期缺失")
            quality_score -= 10
        
        # 5. 检查来源
        source = article.get('source', '').strip()
        if not source:
            issues.append("来源信息缺失")
            quality_score -= 5
        
        # 6. 检查爬取时间
        crawl_time = article.get('crawl_time', '').strip()
        if not crawl_time:
            issues.append("爬取时间缺失")
            quality_score -= 5
        
        # 7. 检查内容质量指标
        # 计算内容密度（非空字符比例）
        if content:
            non_space_chars = len([c for c in content if not c.isspace()])
            content_density = non_space_chars / len(content) if len(content) > 0 else 0
            if content_density < 0.3:
                issues.append("内容密度较低")
                quality_score -= 10
        
        # 8. 检查特殊字符比例
        if content:
            special_chars = len([c for c in content if not c.isalnum() and not c.isspace()])
            special_ratio = special_chars / len(content) if len(content) > 0 else 0
            if special_ratio > 0.4:
                issues.append("特殊字符比例过高")
                quality_score -= 10
        
        # 确保质量分数在合理范围内
        quality_score = max(0, min(100, quality_score))
        
        # 生成改进建议
        recommendations = []
        if quality_score < 70:
            recommendations.append("文章质量较低，建议重新爬取或优化")
        if '标题过短' in issues:
            recommendations.append("确保标题包含足够信息")
        if '内容过短' in issues:
            recommendations.append("目标网站可能内容较少，考虑更换来源")
        
        # 判断文章是否有效
        is_valid = quality_score >= 60 and len(issues) < 5
        
        return {
            'is_valid': is_valid,
            'issues': issues,
            'quality_score': round(quality_score, 2),
            'recommendations': recommendations
        }

    def enhance_article_data(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        增强文章数据质量
        
        Args:
            article: 原始文章数据
            
        Returns:
            增强后的文章数据
        """
        enhanced_article = article.copy()
        
        # 1. 清理和标准化标题
        title = enhanced_article.get('title', '').strip()
        if title:
            # 移除多余空格和换行符
            title = ' '.join(title.split())
            # 确保标题首字母大写
            if title and not title[0].isupper():
                title = title[0].upper() + title[1:]
            enhanced_article['title'] = title
        
        # 2. 清理和标准化内容
        content = enhanced_article.get('content', '').strip()
        if content:
            # 移除多余空格和换行符
            content = ' '.join(content.split())
            # 确保段落之间有适当的分隔
            content = content.replace('。', '。\\n\\n')
            enhanced_article['content'] = content
        
        # 3. 标准化发布日期格式
        publish_date = enhanced_article.get('publish_date', '').strip()
        if publish_date:
            # 尝试标准化日期格式
            try:
                # 这里可以添加更复杂的日期解析逻辑
                enhanced_article['publish_date'] = publish_date
            except:
                # 如果解析失败，保持原格式
                pass
        
        # 4. 添加质量评估信息
        quality_result = self.evaluate_article_quality(enhanced_article)
        enhanced_article['quality_score'] = quality_result['quality_score']
        enhanced_article['quality_issues'] = quality_result['issues']
        enhanced_article['quality_recommendations'] = quality_result['recommendations']
        
        # 5. 添加增强时间戳
        enhanced_article['enhanced_at'] = datetime.now().isoformat()
        
        return enhanced_article

def main():
    """主函数"""
    # 初始化管理系统
    system = DataQualityManagementSystem()
    
    # 执行综合分析
    report = system.run_comprehensive_analysis()
    
    # 打印详细报告
    print("\n" + "="*60)
    print("数据质量管理系统 - 详细报告")
    print("="*60)
    
    print(f"\n📊 总体评估:")
    print(f"   评分: {report['overall_score']}/100")
    print(f"   等级: {report['quality_grade']}")
    print(f"   时间: {report['timestamp']}")
    
    print(f"\n📈 监控数据:")
    monitor = report['monitoring_section']
    print(f"   原始文章: {monitor['original_articles']}")
    print(f"   监控评分: {monitor['monitor_score']}/100")
    
    print(f"\n🔄 增强效果:")
    enhance = report['enhancement_section']
    print(f"   增强后文章: {enhance['enhanced_articles']}")
    print(f"   质量提升率: {enhance['improvement_rate']}%")
    print(f"   质量改进: {enhance['quality_improvement']} 篇文章")
    
    print(f"\n📋 问题解决:")
    issues = enhance['issues_resolved']
    for issue_type, count in issues.items():
        print(f"   {issue_type}: {count}")
    
    print(f"\n📈 趋势分析:")
    trend = report['trend_analysis']
    print(f"   趋势: {trend['trend']}")
    if 'trend_strength' in trend:
        print(f"   趋势强度: {trend['trend_strength']:.2f}")
    if 'average_score' in trend:
        print(f"   平均评分: {trend['average_score']:.2f}")
    print(f"   总报告数: {trend.get('total_reports', 0)}")
    
    print(f"\n💡 改进建议:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    print("\n" + "="*60)
    print("报告生成完成")
    print("="*60)

if __name__ == "__main__":
    main()