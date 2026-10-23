"""
数据来源清单系统
列出所有使用的数据来源和消息来源
"""

import json
from datetime import datetime
from typing import Dict, List, Any

class DataSourcesInventory:
    """数据来源清单管理系统"""
    
    def __init__(self):
        self.sources = {
            "african_news_portals": {
                "name": "非洲新闻门户网站",
                "description": "非洲主要新闻门户和媒体网站",
                "sources": [
                    {
                        "name": "AllAfrica",
                        "url": "allafrica.com",
                        "country": "Pan-Africa",
                        "language": "en/fr",
                        "coverage": "全非洲",
                        "focus": "新闻、政治、经济",
                        "quality_score": 0.85,
                        "reliability": "高",
                        "last_accessed": "2025-11-26"
                    },
                    {
                        "name": "News24",
                        "url": "news24.com",
                        "country": "South Africa",
                        "language": "en",
                        "coverage": "南非及非洲",
                        "focus": "新闻、商业、科技",
                        "quality_score": 0.82,
                        "reliability": "高",
                        "last_accessed": "2025-11-26"
                    },
                    {
                        "name": "Fin24",
                        "url": "fin24.com",
                        "country": "South Africa",
                        "language": "en",
                        "coverage": "南非",
                        "focus": "金融、经济",
                        "quality_score": 0.88,
                        "reliability": "高",
                        "last_accessed": "2025-11-26"
                    },
                    {
                        "name": "Premium Times Nigeria",
                        "url": "premiumtimesng.com",
                        "country": "Nigeria",
                        "language": "en",
                        "coverage": "尼日利亚",
                        "focus": "新闻、调查报道",
                        "quality_score": 0.80,
                        "reliability": "中高",
                        "last_accessed": "2025-11-26"
                    },
                    {
                        "name": "Daily Nation",
                        "url": "nation.africa",
                        "country": "Kenya",
                        "language": "en",
                        "coverage": "肯尼亚及东非",
                        "focus": "新闻、商业",
                        "quality_score": 0.83,
                        "reliability": "高",
                        "last_accessed": "2025-11-26"
                    },
                    {
                        "name": "ThisDay Live",
                        "url": "thisdaylive.com",
                        "country": "Nigeria",
                        "language": "en",
                        "coverage": "尼日利亚",
                        "focus": "新闻、商业",
                        "quality_score": 0.78,
                        "reliability": "中",
                        "last_accessed": "2025-11-26"
                    },
                    {
                        "name": "Tunisie Numerique",
                        "url": "tunisienumerique.com",
                        "country": "Tunisia",
                        "language": "fr",
                        "coverage": "突尼斯",
                        "focus": "科技、数字",
                        "quality_score": 0.75,
                        "reliability": "中",
                        "last_accessed": "2025-11-26"
                    }
                ]
            },
            "chinese_media": {
                "name": "中国媒体",
                "description": "中国主要媒体对非洲报道",
                "sources": [
                    {
                        "name": "新华网",
                        "url": "xinhuanet.com",
                        "country": "China",
                        "language": "zh",
                        "coverage": "全球",
                        "focus": "中非合作、一带一路",
                        "quality_score": 0.90,
                        "reliability": "高",
                        "last_accessed": "2025-11-26"
                    },
                    {
                        "name": "人民网",
                        "url": "people.com.cn",
                        "country": "China",
                        "language": "zh",
                        "coverage": "全球",
                        "focus": "中非关系、投资",
                        "quality_score": 0.88,
                        "reliability": "高",
                        "last_accessed": "2025-11-26"
                    },
                    {
                        "name": "中国日报",
                        "url": "chinadaily.com.cn",
                        "country": "China",
                        "language": "en",
                        "coverage": "全球",
                        "focus": "中非投资、经济合作",
                        "quality_score": 0.85,
                        "reliability": "高",
                        "last_accessed": "2025-11-26"
                    }
                ]
            },
            "international_media": {
                "name": "国际媒体",
                "description": "国际媒体对非洲报道",
                "sources": [
                    {
                        "name": "Africanews",
                        "url": "africanews.com",
                        "country": "Pan-Africa",
                        "language": "en/fr",
                        "coverage": "全非洲",
                        "focus": "新闻、商业",
                        "quality_score": 0.82,
                        "reliability": "高",
                        "last_accessed": "2025-11-26"
                    },
                    {
                        "name": "Business Daily Africa",
                        "url": "businessdailyafrica.com",
                        "country": "Kenya",
                        "language": "en",
                        "coverage": "东非",
                        "focus": "商业、经济",
                        "quality_score": 0.86,
                        "reliability": "高",
                        "last_accessed": "2025-11-26"
                    },
                    {
                        "name": "The East African",
                        "url": "theeastafrican.co.ke",
                        "country": "Kenya",
                        "language": "en",
                        "coverage": "东非",
                        "focus": "新闻、商业",
                        "quality_score": 0.84,
                        "reliability": "高",
                        "last_accessed": "2025-11-26"
                    },
                    {
                        "name": "Mail & Guardian",
                        "url": "mg.co.za",
                        "country": "South Africa",
                        "language": "en",
                        "coverage": "南非",
                        "focus": "新闻、调查报道",
                        "quality_score": 0.87,
                        "reliability": "高",
                        "last_accessed": "2025-11-26"
                    },
                    {
                        "name": "Algerie Eco",
                        "url": "algerie-eco.com",
                        "country": "Algeria",
                        "language": "fr",
                        "coverage": "阿尔及利亚",
                        "focus": "经济、商业",
                        "quality_score": 0.79,
                        "reliability": "中",
                        "last_accessed": "2025-11-26"
                    }
                ]
            },
            "search_engines": {
                "name": "搜索引擎",
                "description": "用于发现和抓取数据的搜索引擎",
                "sources": [
                    {
                        "name": "Google Search",
                        "url": "google.com",
                        "purpose": "关键词搜索发现",
                        "coverage": "全球",
                        "usage": "发现相关文章和新闻",
                        "quality_score": 0.95,
                        "reliability": "极高",
                        "last_accessed": "2025-11-26"
                    },
                    {
                        "name": "Bing Search",
                        "url": "bing.com",
                        "purpose": "备用搜索引擎",
                        "coverage": "全球",
                        "usage": "补充搜索结果",
                        "quality_score": 0.88,
                        "reliability": "高",
                        "last_accessed": "2025-11-26"
                    }
                ]
            }
        }
        
        # 数据抓取工具
        self.crawling_tools = {
            "bright_data": {
                "name": "Bright Data",
                "type": "企业级爬虫平台",
                "capabilities": ["反爬虫规避", "代理网络", "数据提取"],
                "usage": "高难度网站爬取",
                "reliability": "极高"
            },
            "firecrawl": {
                "name": "Firecrawl",
                "type": "智能爬虫工具",
                "capabilities": ["智能解析", "多格式支持", "批量处理"],
                "usage": "结构化数据提取",
                "reliability": "高"
            },
            "puppeteer": {
                "name": "Puppeteer",
                "type": "浏览器自动化",
                "capabilities": ["动态内容", "JavaScript渲染", "截图"],
                "usage": "动态网站爬取",
                "reliability": "高"
            }
        }
    
    def generate_inventory_report(self) -> Dict[str, Any]:
        """生成数据来源清单报告"""
        
        total_sources = 0
        quality_summary = {
            "high_quality": 0,
            "medium_quality": 0,
            "low_quality": 0,
            "average_quality": 0.0
        }
        
        # 统计各类来源
        for category, data in self.sources.items():
            total_sources += len(data["sources"])
            for source in data["sources"]:
                score = source["quality_score"]
                if score >= 0.85:
                    quality_summary["high_quality"] += 1
                elif score >= 0.70:
                    quality_summary["medium_quality"] += 1
                else:
                    quality_summary["low_quality"] += 1
                
                quality_summary["average_quality"] += score
        
        if total_sources > 0:
            quality_summary["average_quality"] /= total_sources
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_data_sources": total_sources,
            "quality_summary": quality_summary,
            "categories": self.sources,
            "crawling_tools": self.crawling_tools,
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """生成数据来源优化建议"""
        
        recommendations = [
            "优先使用质量评分高于0.85的来源进行核心数据抓取",
            "对于非洲本地新闻，优先使用AllAfrica和News24等高质量门户",
            "对于中非投资相关报道，优先使用新华网和中国日报",
            "定期更新来源的质量评分和可靠性评估",
            "建立来源轮换机制以避免单一来源依赖",
            "监控来源的可访问性和反爬虫措施变化",
            "建立来源黑名单机制，及时淘汰低质量来源"
        ]
        
        return recommendations
    
    def save_report(self, filename: str = None):
        """保存清单报告到文件"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/sources_inventory_{timestamp}.json"
        
        report = self.generate_inventory_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"数据来源清单报告已保存到: {filename}")
        return filename

def main():
    """主函数"""
    
    print("=" * 60)
    print("数据来源清单系统")
    print("=" * 60)
    
    inventory = DataSourcesInventory()
    report = inventory.generate_inventory_report()
    
    # 打印摘要信息
    print(f"总数据来源数量: {report['total_data_sources']}")
    print(f"平均质量评分: {report['quality_summary']['average_quality']:.2f}")
    print(f"高质量来源: {report['quality_summary']['high_quality']} 个")
    print(f"中等质量来源: {report['quality_summary']['medium_quality']} 个")
    print(f"低质量来源: {report['quality_summary']['low_quality']} 个")
    
    # 按类别统计
    print("\n按类别统计:")
    for category, data in report['categories'].items():
        print(f"  {data['name']}: {len(data['sources'])} 个来源")
    
    # 保存报告
    filename = inventory.save_report()
    
    print(f"\n报告文件: {filename}")
    print("=" * 60)

if __name__ == "__main__":
    main()