import json

# 重新构建JSON结构
def rebuild_json(file_path):
    print(f"正在重新构建JSON文件: {file_path}")
    
    # 创建一个新的发展词典结构
    new_dictionary = {
        "economic_development": {
            "industrialization": "工业化",
            "economic_growth": "经济增长",
            "trade_liberalization": "贸易自由化",
            "foreign_direct_investment": "外国直接投资",
            "poverty_reduction": "减贫",
            "infrastructure": "基础设施",
            "agriculture": "农业",
            "healthcare": "医疗保健",
            "education": "教育",
            "technology": "技术",
            "digital_economy": "数字经济",
            "sustainable_development": "可持续发展",
            "green_growth": "绿色增长",
            "employment": "就业",
            "small_and_medium_enterprises": "中小企业",
            "financial_inclusion": "金融包容性",
            "regional_integration": "区域一体化",
            "good_governance": "善治",
            "gender_equality": "性别平等"
        },
        "infrastructure": {
            "transport_infrastructure": "交通基础设施",
            "energy_infrastructure": "能源基础设施",
            "digital_infrastructure": "数字基础设施",
            "water_infrastructure": "水利基础设施",
            "sanitation": "卫生设施",
            "housing_infrastructure": "住房基础设施",
            "urban_infrastructure": "城市基础设施",
            "rural_infrastructure": "农村基础设施",
            "railway_system": "铁路系统",
            "port_development": "港口发展",
            "air_transport": "航空运输",
            "renewable_energy": "可再生能源",
            "electricity_access": "电力接入",
            "broadband_connectivity": "宽带连接",
            "smart_cities": "智慧城市"
        },
        "social_development": {
            "education_for_all": "全民教育",
            "quality_education": "优质教育",
            "healthcare_access": "医疗保健获取",
            "disease_prevention": "疾病预防",
            "poverty_alleviation": "扶贫",
            "social_protection": "社会保护",
            "gender_empowerment": "性别赋权",
            "youth_development": "青年发展",
            "elderly_care": "老年人护理",
            "child_protection": "儿童保护",
            "disability_inclusion": "残疾人包容",
            "food_security": "粮食安全",
            "nutrition": "营养",
            "clean_water": "清洁用水",
            "hygiene": "卫生",
            "employment_creation": "创造就业"
        },
        "environmental_sustainability": {
            "climate_change_mitigation": "气候变化减缓",
            "climate_change_adaptation": "气候变化适应",
            "biodiversity_conservation": "生物多样性保护",
            "desertification_control": "荒漠化控制",
            "deforestation_prevention": "防止毁林",
            "reforestation": "重新造林",
            "sustainable_land_use": "可持续土地利用",
            "clean_energy": "清洁能源",
            "pollution_control": "污染控制",
            "waste_management": "废物管理",
            "water_conservation": "水资源保护",
            "sustainable_agriculture": "可持续农业",
            "green_economy": "绿色经济",
            "circular_economy": "循环经济",
            "environmental_governance": "环境治理"
        },
        "governance": {
            "democratic_governance": "民主治理",
            "rule_of_law": "法治",
            "anti_corruption": "反腐败",
            "transparency": "透明度",
            "accountability": "问责制",
            "decentralization": "权力下放",
            "public_sector_reform": "公共部门改革",
            "civil_society_participation": "公民社会参与",
            "human_rights": "人权",
            "gender_mainstreaming": "性别主流化",
            "conflict_prevention": "冲突预防",
            "peacebuilding": "建设和平",
            "security_sector_reform": "安全部门改革",
            "disaster_risk_reduction": "减少灾害风险",
            "crisis_management": "危机管理"
        },
        "regional_integration": {
            "african_integration": "非洲一体化",
            "continental_free_trade_area": "非洲大陆自由贸易区",
            "regional_economic_communities": "区域经济共同体",
            "cross_border_cooperation": "跨境合作",
            "trade_facilitation": "贸易便利化",
            "customs_union": "关税同盟",
            "monetary_union": "货币同盟",
            "infrastructure_connectivity": "基础设施互联互通",
            "digital_integration": "数字一体化",
            "energy_integration": "能源一体化",
            "transport_integration": "交通一体化",
            "cultural_exchange": "文化交流",
            "people_to_people_cooperation": "人文合作",
            "scientific_cooperation": "科学合作",
            "technological_cooperation": "技术合作"
        },
        "digital_transformation": {
            "digital_economy": "数字经济",
            "digital_governance": "数字治理",
            "e_government": "电子政务",
            "digital_education": "数字教育",
            "digital_health": "数字健康",
            "digital_finance": "数字金融",
            "e_commerce": "电子商务",
            "digital_skills": "数字技能",
            "digital_inclusion": "数字包容",
            "cybersecurity": "网络安全",
            "digital_infrastructure": "数字基础设施",
            "data_governance": "数据治理",
            "artificial_intelligence": "人工智能",
            "blockchain": "区块链",
            "internet_of_things": "物联网"
        },
        "agriculture": {
            "agricultural_modernization": "农业现代化",
            "food_security": "粮食安全",
            "sustainable_agriculture": "可持续农业",
            "agricultural_productivity": "农业生产率",
            "smallholder_farmers": "小农户",
            "agricultural_research": "农业研究",
            "agricultural_extension": "农业推广",
            "agricultural_finance": "农业金融",
            "value_addition": "增值",
            "agribusiness": "农业企业",
            "agricultural_markets": "农业市场",
            "climate_smart_agriculture": "气候智能型农业",
            "irrigation": "灌溉",
            "fertilizer_use": "肥料使用",
            "pest_management": "害虫管理"
        }
    }
    
    # 保存重新构建的JSON文件
    fixed_file_path = file_path.replace('.json', '_rebuilt.json')
    with open(fixed_file_path, 'w', encoding='utf-8') as f:
        json.dump(new_dictionary, f, ensure_ascii=False, indent=2)
    
    print(f"重新构建的JSON文件已保存到: {fixed_file_path}")
    print(f"新词典包含 {len(new_dictionary)} 个类别，总计 {sum(len(v) for v in new_dictionary.values())} 个关键词")
    
    return fixed_file_path

if __name__ == "__main__":
    file_path = r'c:\Users\13067\Desktop\论文\非洲\demo\african_development_dictionary.json'
    rebuild_json(file_path)