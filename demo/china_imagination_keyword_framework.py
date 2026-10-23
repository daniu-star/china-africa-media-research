"""
非洲媒体中国想象关键词爬虫 - 增强版配置
基于新闻传播学理论构建的comprehensive关键词体系
"""

import json
import logging
from typing import Dict, List, Set
from datetime import datetime

class ChinaImaginationKeywordFramework:
    """中国想象关键词框架 - 基于媒介框架理论和他者化理论"""
    
    def __init__(self):
        self.keywords = self._load_comprehensive_keywords()
        self.search_strategies = self._initialize_search_strategies()
        self.framework_analysis = self._setup_theoretical_framework()
        
    def _load_comprehensive_keywords(self) -> Dict[str, List[str]]:
        """加载comprehensive关键词库"""
        return {
            # 基础身份标识 - 传播者身份建构
            "core_identity": {
                "primary": ["china", "chinese", "beijing", "peoples republic of china", "prc"],
                "secondary": ["中國", "中国", "中国人", "北京的", "中华人民共和国"],
                "theoretical_basis": "身份认同理论 - 他者身份的标签化过程"
            },
            
            # 政治话语框架 - 权力关系再现
            "political_framework": {
                "leadership": ["xi jinping", "president xi", "communist party", "ccp", "chinese government"],
                "policy_initiatives": ["belt and road", "bri", "one belt one road", "china africa cooperation"],
                "ideological": ["socialism", "marxism", "authoritarian", "democracy deficit"],
                "theoretical_basis": "框架理论 - 政治话语的媒介再现机制"
            },
            
            # 经济想象建构 - 新殖民主义vs发展伙伴
            "economic_narratives": {
                "trade_commerce": ["trade war", "tariff", "import", "export", "bilateral trade", "investment"],
                "infrastructure": ["infrastructure", "construction", "railway", "road", "bridge", "port"],
                "technology": ["technology", "digital", "huawei", "5g", "artificial intelligence", "innovation"],
                "resources": ["mining", "minerals", "copper", "cobalt", "lithium", "rare earth"],
                "debt_discourse": ["debt trap", "debt diplomacy", "predatory lending", "loan", "default"],
                "theoretical_basis": "依附理论 - 中心-边缘关系的经济维度"
            },
            
            # 地缘政治想象 - 全球南方vs新帝国主义
            "geopolitical_imagination": {
                "soft_power": ["soft power", "cultural diplomacy", "confucius institute", "panda diplomacy"],
                "military_security": ["military", "defense", "security", "weapon", "defense cooperation"],
                "global_governance": ["multilateralism", "global governance", "brics", "south south cooperation"],
                "imperialism_critique": ["neocolonialism", "imperialism", "exploitation", "resource grab"],
                "theoretical_basis": "后殖民理论 - 新帝国主义话语分析"
            },
            
            # 文化社会表征 - 文化他者化过程
            "cultural_social_representations": {
                "cultural_exchange": ["culture", "tradition", "festival", "art", "confucius", "chinese new year"],
                "diaspora_communities": ["chinese people", "chinese diaspora", "chinese community", "migration"],
                "internal_affairs": ["uighur", "tibet", "hong kong", "taiwan question", "ethnic minority"],
                "media_communication": ["cgtn", "xinhua", "china daily", "tiktok", "censorship", "propaganda"],
                "theoretical_basis": "文化研究理论 - 他者文化的媒介表征"
            },
            
            # 发展话语框架 - 现代化vs传统
            "development_discourses": {
                "modernization": ["development", "modernization", "progress", "growth", "transformation"],
                "assistance_cooperation": ["aid", "assistance", "support", "grant", "capacity building"],
                "connectivity": ["connectivity", "integration", "regional integration", "trade facilitation"],
                "sustainability": ["sustainable", "green development", "environment", "climate"],
                "theoretical_basis": "发展传播学 - 现代化理论的话语建构"
            },
            
            # 批判性话语 - 反话语和抵抗
            "critical_counter_discourses": {
                "transparency_governance": ["transparency", "corruption", "governance", "accountability", "human rights"],
                "environmental_concerns": ["environmental impact", "pollution", "deforestation", "wildlife"],
                "labor_conditions": ["labor rights", "working conditions", "wages", "local employment"],
                "quality_concerns": ["quality", "fake", "substandard", "durability", "safety"],
                "theoretical_basis": "批判话语分析 - 权力关系的揭露和挑战"
            },
            
            # 区域特定术语 - 空间差异化表征
            "regional_specific_terms": {
                "east_africa": ["sgr", "standard gauge railway", "mombasa nairobi", "ethiopia djibouti"],
                "west_africa": ["ecowas", "lagos ibadan", "cotonou", "dakar", "port of abidjan"],
                "southern_africa": ["zambia", "zimbabwe", "botswana", "kariba dam", "beira corridor"],
                "north_africa": ["egypt", "cairo", "suez canal", "algeria", "morocco", "tunisia"],
                "theoretical_basis": "地理学话语 - 空间差异的媒介再现"
            },
            
            # 多语言等价词 - 跨文化传播
            "multilingual_equivalents": {
                "french": ["chine", "chinois", "route de la soie", "coopération sino africaine"],
                "arabic": ["الصين", "الصيني", "بكين", "الحزب الشيوعي", "طريق الحرير"],
                "portuguese": ["china", "chinês", "rota da seda", "cooperação sino-africana"],
                "swahili": ["china", "kichina", "beijing", "barabara ya hariri"],
                "theoretical_basis": "跨文化传播理论 - 语言转换中的意义变迁"
            }
        }
    
    def _initialize_search_strategies(self) -> Dict:
        """初始化搜索策略"""
        return {
            "boolean_operators": {
                "cooperation_frame": ["china AND africa", "chinese AND cooperation", "beijing AND partnership"],
                "conflict_frame": ["china AND debt", "chinese AND colonialism", "beijing AND exploitation"],
                "neutral_frame": ["china AND trade", "chinese AND investment", "beijing AND visit"]
            },
            "proximity_searches": [
                "china africa cooperation", "chinese investment africa", "belt road initiative",
                "sino african relations", "china aid africa", "beijing consensus"
            ],
            "temporal_markers": {
                "historical": ["bandung conference", "tanzam railway", "focac 2000", "focac 2018"],
                "contemporary": ["covid 19 china", "china vaccine diplomacy", "belt road 2024"]
            }
        }
    
    def _setup_theoretical_framework(self) -> Dict:
        """设置理论框架分析"""
        return {
            "media_framing_theory": {
                "definition": "媒介框架理论 - 分析媒体如何选择、强调和排除某些方面来建构现实",
                "application": "识别非洲媒体如何框架化中国形象",
                "key_concepts": ["框架设置", "议程设置", "属性议程设置"]
            },
            "othering_theory": {
                "definition": "他者化理论 - 分析如何通过话语建构文化他者",
                "application": "理解非洲媒体如何建构中国作为文化他者",
                "key_concepts": ["自我-他者二元对立", "文化差异强调", "权力关系再现"]
            },
            "postcolonial_discourse_analysis": {
                "definition": "后殖民话语分析 - 分析殖民权力关系在新语境下的延续和变化",
                "application": "理解中国作为新兴大国在非洲话语中的位置",
                "key_concepts": ["新殖民主义话语", "抵抗话语", "混杂性身份"]
            },
            "development_communication_theory": {
                "definition": "发展传播学理论 - 分析发展话语如何建构现代化想象",
                "application": "理解中国发展模式在非洲的媒介呈现",
                "key_concepts": ["现代化理论", "依赖理论", "可持续发展话语"]
            }
        }
    
    def get_comprehensive_search_queries(self) -> List[str]:
        """生成comprehensive搜索查询"""
        queries = []
        
        # 基础身份搜索
        for keyword in self.keywords["core_identity"]["primary"]:
            queries.extend([
                f'{keyword} AND africa',
                f'{keyword} AND (investment OR trade)',
                f'{keyword} AND (cooperation OR partnership)',
                f'{keyword} AND (development OR infrastructure)'
            ])
        
        # 特定话语框架搜索
        cooperation_frame = ["cooperation", "partnership", "win-win", "mutual benefit"]
        critique_frame = ["debt trap", "colonialism", "exploitation", "transparency"]
        neutral_frame = ["trade", "investment", "infrastructure", "technology"]
        
        for base_word in ["china", "chinese", "beijing"]:
            for frame_word in cooperation_frame:
                queries.append(f'{base_word} AND "{frame_word}"')
            for frame_word in critique_frame:
                queries.append(f'{base_word} AND "{frame_word}"')
            for frame_word in neutral_frame:
                queries.append(f'{base_word} AND "{frame_word}"')
        
        # 区域特定搜索
        regions = ["east africa", "west africa", "southern africa", "north africa"]
        for region in regions:
            queries.append(f'china AND "{region}"')
            queries.append(f'chinese AND investment AND "{region}"')
        
        # 时间敏感搜索
        temporal_queries = [
            'china AND covid AND africa',
            'china AND vaccine AND africa',
            'china AND pandemic AND africa',
            'belt AND road AND 2024',
            'focac AND 2024'
        ]
        queries.extend(temporal_queries)
        
        return list(set(queries))  # 去重
    
    def get_discourse_analysis_keywords(self) -> Dict[str, List[str]]:
        """获取话语分析关键词"""
        return {
            "positive_frames": [
                "cooperation", "partnership", "win-win", "mutual benefit",
                "development", "assistance", "support", "infrastructure",
                "modernization", "progress", "growth", "opportunity"
            ],
            "negative_frames": [
                "debt trap", "colonialism", "exploitation", "predatory",
                "transparency", "corruption", "accountability", "concern",
                "risk", "threat", "challenge", "problem"
            ],
            "neutral_frames": [
                "trade", "investment", "agreement", "deal", "project",
                "meeting", "visit", "conference", "summit", "policy"
            ],
            "power_relations": [
                "dominance", "influence", "control", "dependence", "asymmetry",
                "equality", "balance", "reciprocity", "sovereignty", "autonomy"
            ],
            "temporal_markers": [
                "new", "emerging", "rising", "growing", "increasing",
                "traditional", "historical", "long-term", "future", "changing"
            ]
        }
    
    def generate_crawler_config(self) -> Dict:
        """生成爬虫配置"""
        return {
            "search_configuration": {
                "search_engines": ["google", "bing", "duckduckgo"],
                "african_news_sources": [
                    "allafrica.com", "english.ahram.org.eg", "theeastafrican.co.ke",
                    "mg.co.za", "dailymaverick.co.za", "nation.africa",
                    "guardian.ng", "premiumtimesng.com", "africanarguments.org",
                    "www.dailynews.co.tz", "www.newtimes.co.rw", "www.monitor.co.ug",
                    "www.addisfortune.net", "www.ghanaweb.com", "www.panapress.com",
                    "www.africanews.com", "www.iol.co.za", "www.news24.com",
                    "www.businesslive.co.za", "www.fin24.com", "www.leconomistemaghrebin.com",
                    "www.liberte-algerie.com", "www.aps.dz", "www.tunisienumerique.com",
                    "www.maghrebemergent.com", "www.medi1tv.com", "www.le360.ma",
                    "www.leconomiste.com", "www.lesiteinfo.com", "www.lematin.ma",
                    "www.lequotidien.sn", "www.iwacu-burundi.org", "www.cameroon-tribune.cm",
                    "www.lesoleil.sn", "www.lefaso.net", "www.maliweb.net",
                    "www.liberationafrique.org", "www.jeuneafrique.com", "www.rfi.fr/afrique",
                    "www.bbc.com/afrique", "www.aljazeera.com/africa", "www.france24.com/en/africa/"
                ],
                "search_depth": 10,
                "language_filter": ["en", "fr", "ar", "pt"],
                "date_range": {
                    "start": "2020-01-01",
                    "end": datetime.now().strftime("%Y-%m-%d")
                }
            },
            
            "keyword_application": {
                "title_search": self.get_primary_keywords(),
                "content_analysis": self.get_comprehensive_search_queries(),
                "discourse_markers": self.get_discourse_analysis_keywords()
            },
            
            "quality_filters": {
                "minimum_word_count": 300,
                "exclude_advertisement": True,
                "require_author": False,
                "language_detection": True,
                "content_duplication_check": True
            },
            
            "ethical_considerations": {
                "respect_robots_txt": True,
                "rate_limiting": {
                    "delay_range": [2, 5],
                    "max_concurrent_requests": 3
                },
                "user_agent_rotation": True,
                "ip_rotation": False  # 基于伦理考虑
            }
        }
    
    def get_primary_keywords(self) -> List[str]:
        """获取主要关键词"""
        return self.keywords["core_identity"]["primary"] + \
               self.keywords["political_framework"]["leadership"] + \
               self.keywords["economic_narratives"]["trade_commerce"][:5]
    
    def analyze_keyword_coverage(self, text_content: str) -> Dict:
        """分析文本中的关键词覆盖度"""
        text_lower = text_content.lower()
        coverage_analysis = {}
        
        for category, subcategories in self.keywords.items():
            if isinstance(subcategories, dict):
                coverage_analysis[category] = {}
                for subcat, keywords in subcategories.items():
                    if isinstance(keywords, list):
                        found_keywords = [kw for kw in keywords if kw.lower() in text_lower]
                        coverage_analysis[category][subcat] = {
                            "found": found_keywords,
                            "total": len(keywords),
                            "coverage_rate": len(found_keywords) / len(keywords) if keywords else 0
                        }
        
        return coverage_analysis
    
    def export_for_crawler(self, output_file: str):
        """导出为爬虫可用的格式"""
        crawler_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "theoretical_framework": "Media Framing Theory + Othering Theory + Postcolonial Discourse Analysis",
                "target_audience": "African Media Representation of China",
                "version": "2.0"
            },
            "search_queries": self.get_comprehensive_search_queries(),
            "primary_keywords": self.get_primary_keywords(),
            "discourse_analysis_keywords": self.get_discourse_analysis_keywords(),
            "crawler_config": self.generate_crawler_config(),
            "theoretical_notes": self.framework_analysis
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(crawler_data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"关键词框架已导出到 {output_file}")

# 使用示例和测试
if __name__ == "__main__":
    # 初始化关键词框架
    framework = ChinaImaginationKeywordFramework()
    
    # 导出爬虫配置
    framework.export_for_crawler("china_imagination_crawler_config.json")
    
    # 测试关键词覆盖度分析
    sample_text = """
    China has significantly increased its investment in Africa through the Belt and Road Initiative.
    While some praise the infrastructure development, others warn about debt trap diplomacy.
    The cooperation between China and African countries continues to grow, with Beijing
    emphasizing win-win partnerships and mutual benefits.
    """
    
    coverage = framework.analyze_keyword_coverage(sample_text)
    print("关键词覆盖度分析:")
    print(json.dumps(coverage, ensure_ascii=False, indent=2))
    
    print(f"\n生成 {len(framework.get_comprehensive_search_queries())} 个搜索查询")
    print(f"主要关键词: {len(framework.get_primary_keywords())} 个")
    print("关键词框架构建完成！")