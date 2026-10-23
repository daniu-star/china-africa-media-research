#!/usr/bin/env python3
"""
任务扩展脚本 - 增加新的关键词和年份范围
"""

import json
import uuid
from datetime import datetime

def expand_tasks():
    """扩展任务队列"""
    
    # 定义扩展的关键词类别 - 扩展到所有中国报道数据
    keyword_categories = {
        "primary_keywords.core_identity": [
            "china", "chinese", "中国", "中国人", "chinese government", "chinese communist party", 
            "ccp", "xi jinping", "beijing", "peoples republic of china", "prc", "一带一路", "belt and road"
        ],
        "economic_framework.investment_trade": [
            "chinese investment", "china trade", "chinese economy", "chinese companies", 
            "chinese business", "chinese market", "chinese exports", "chinese imports"
        ],
        "economic_framework.infrastructure_development": [
            "chinese infrastructure", "chinese construction", "chinese projects", "chinese development",
            "chinese engineering", "chinese technology", "chinese innovation"
        ],
        "geopolitical_narratives.diplomacy_relations": [
            "chinese diplomacy", "china foreign policy", "chinese relations", "chinese foreign minister",
            "chinese embassy", "chinese ambassador", "chinese foreign affairs"
        ],
        "geopolitical_narratives.global_governance": [
            "chinese global governance", "china un", "chinese united nations", "chinese international",
            "chinese multilateral", "chinese global leadership"
        ],
        "cultural_social_representations.media_communication": [
            "chinese media", "china news", "chinese press", "chinese journalism", "chinese broadcasting",
            "chinese television", "chinese radio", "chinese internet"
        ],
        "cultural_social_representations.education_research": [
            "chinese education", "china research", "chinese universities", "chinese students",
            "chinese academics", "chinese scholarship", "chinese learning"
        ],
        "cultural_social_representations.arts_culture": [
            "chinese culture", "chinese art", "chinese music", "chinese film", "chinese literature",
            "chinese heritage", "chinese traditions", "chinese festivals"
        ],
        "development_cooperation.aid_assistance": [
            "chinese aid", "china assistance", "chinese development", "chinese cooperation",
            "chinese support", "chinese grants", "chinese technical assistance"
        ],
        "development_cooperation.health_medical": [
            "chinese health", "china medical", "chinese doctors", "chinese hospitals",
            "chinese medicine", "chinese healthcare", "chinese pandemic response"
        ],
        "security_defense.military_police": [
            "chinese military", "china defense", "chinese army", "chinese navy", "chinese air force",
            "chinese police", "chinese security", "chinese defense policy"
        ],
        "security_defense.peacekeeping": [
            "chinese peacekeeping", "china un peacekeeping", "chinese peacekeepers",
            "chinese peace operations", "chinese peace missions"
        ],
        "technology_digital.digital_economy": [
            "chinese technology", "china digital", "chinese internet", "chinese e-commerce",
            "chinese digital economy", "chinese tech companies", "chinese innovation"
        ],
        "technology_digital.telecommunications": [
            "chinese telecom", "china telecommunications", "chinese 5g", "chinese mobile",
            "chinese networks", "chinese communications"
        ],
        "environment_energy.climate_environment": [
            "chinese environment", "china climate", "chinese pollution", "chinese green",
            "chinese environmental protection", "chinese climate change"
        ],
        "environment_energy.energy_resources": [
            "chinese energy", "china resources", "chinese oil", "chinese gas", "chinese coal",
            "chinese renewable energy", "chinese power"
        ],
        "transportation_logistics.aviation_shipping": [
            "chinese aviation", "china shipping", "chinese airlines", "chinese ports",
            "chinese logistics", "chinese transportation"
        ],
        "transportation_logistics.rail_roads": [
            "chinese railways", "china rail", "chinese trains", "chinese high speed rail",
            "chinese roads", "chinese infrastructure"
        ],
        "agriculture_food.food_security": [
            "chinese agriculture", "china food", "chinese farming", "chinese food security",
            "chinese crops", "chinese agricultural technology"
        ],
        "tourism_travel.travel_tourism": [
            "chinese tourism", "china travel", "chinese tourists", "chinese travel industry",
            "chinese destinations", "chinese hospitality"
        ]
    }
    
    # 年份范围：扩展到1990-2025年
    years = list(range(1990, 2026))
    
    # 优先级设置 - 根据类别重要性调整
    priorities = {
        "primary_keywords.core_identity": "high",
        "economic_framework.investment_trade": "high",
        "economic_framework.infrastructure_development": "high",
        "geopolitical_narratives.diplomacy_relations": "high",
        "geopolitical_narratives.global_governance": "medium",
        "cultural_social_representations.media_communication": "medium",
        "cultural_social_representations.education_research": "medium",
        "cultural_social_representations.arts_culture": "medium",
        "development_cooperation.aid_assistance": "medium",
        "development_cooperation.health_medical": "medium",
        "security_defense.military_police": "medium",
        "security_defense.peacekeeping": "medium",
        "technology_digital.digital_economy": "medium",
        "technology_digital.telecommunications": "medium",
        "environment_energy.climate_environment": "low",
        "environment_energy.energy_resources": "low",
        "transportation_logistics.aviation_shipping": "low",
        "transportation_logistics.rail_roads": "low",
        "agriculture_food.food_security": "low",
        "tourism_travel.travel_tourism": "low"
    }
    
    # 生成扩展任务 - 目标20000条数据
    expanded_tasks = []
    task_id_counter = 0
    
    # 计算每个关键词需要覆盖的年份数量以达到20000条目标
    total_keywords = sum(len(keywords) for keywords in keyword_categories.values())
    target_tasks = 20000
    
    # 如果关键词数量不足，则增加年份覆盖密度
    if total_keywords * len(years) < target_tasks:
        # 需要重复年份来达到目标
        years_per_keyword = (target_tasks + total_keywords - 1) // total_keywords
        print(f"需要每个关键词覆盖 {years_per_keyword} 个年份来达到 {target_tasks} 条目标")
    else:
        years_per_keyword = len(years)
    
    for category, keywords in keyword_categories.items():
        priority = priorities[category]
        
        for keyword in keywords:
            # 为每个关键词选择年份，优先覆盖2010-2025年
            selected_years = []
            
            # 优先选择2010-2025年
            recent_years = [year for year in years if 2010 <= year <= 2025]
            
            # 如果需要更多年份，添加1990-2009年
            if len(recent_years) < years_per_keyword:
                older_years = [year for year in years if 1990 <= year <= 2009]
                # 随机选择或按顺序选择
                selected_years = recent_years + older_years[:years_per_keyword - len(recent_years)]
            else:
                # 如果近期年份足够，随机选择或按顺序选择
                selected_years = recent_years[:years_per_keyword]
            
            for year in selected_years:
                task_id = str(uuid.uuid4())
                
                task = {
                    "task_id": task_id,
                    "keyword": keyword,
                    "year": year,
                    "category": category,
                    "priority": priority,
                    "status": "pending",
                    "created_date": datetime.now().isoformat(),
                    "assigned_worker": None,
                    "attempts": 0
                }
                
                expanded_tasks.append(task)
                task_id_counter += 1
                
                # 如果已达到目标数量，停止生成
                if len(expanded_tasks) >= target_tasks:
                    break
            
            if len(expanded_tasks) >= target_tasks:
                break
        
        if len(expanded_tasks) >= target_tasks:
            break
    
    print(f"生成了 {len(expanded_tasks)} 个扩展任务")
    
    # 按优先级和类别统计
    stats = {}
    for task in expanded_tasks:
        key = f"{task['category']}_{task['priority']}"
        stats[key] = stats.get(key, 0) + 1
    
    print("任务分布统计:")
    for key, count in stats.items():
        print(f"  {key}: {count} 个任务")
    
    # 将任务分批保存到文件
    batch_size = 1000
    total_batches = (len(expanded_tasks) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, len(expanded_tasks))
        batch_tasks = expanded_tasks[start_idx:end_idx]
        
        batch_filename = f"data/tasks_expanded_{batch_num}.json"
        
        batch_data = {
            "tasks": batch_tasks,
            "batch_number": batch_num,
            "total_batches": total_batches,
            "created_date": datetime.now().isoformat(),
            "total_tasks": len(batch_tasks)
        }
        
        with open(batch_filename, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)
        
        print(f"保存批次 {batch_num}: {len(batch_tasks)} 个任务到 {batch_filename}")
    
    # 创建任务索引文件
    index_data = {
        "total_tasks": len(expanded_tasks),
        "total_batches": total_batches,
        "categories": list(keyword_categories.keys()),
        "years_range": f"{years[0]}-{years[-1]}",
        "created_date": datetime.now().isoformat(),
        "batch_files": [f"tasks_expanded_{i}.json" for i in range(total_batches)]
    }
    
    with open("data/tasks_expanded_index.json", 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n任务扩展完成！总共生成了 {len(expanded_tasks)} 个任务")
    print(f"任务索引文件已保存到 data/tasks_expanded_index.json")
    
    return len(expanded_tasks)

def merge_with_existing_tasks():
    """合并现有任务和扩展任务"""
    
    # 读取现有任务
    existing_tasks = []
    for i in range(60):  # 现有任务文件编号0-59
        filename = f"data/tasks_{i}.json"
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 检查数据类型，可能是数组或对象
                if isinstance(data, list):
                    existing_tasks.extend(data)
                elif isinstance(data, dict):
                    existing_tasks.extend(data.get('tasks', []))
        except FileNotFoundError:
            continue
    
    print(f"现有任务数量: {len(existing_tasks)}")
    
    # 生成扩展任务
    expanded_count = expand_tasks()
    
    print(f"\n合并后总任务数量: {len(existing_tasks) + expanded_count}")
    
    # 创建合并索引
    merged_index = {
        "existing_tasks": len(existing_tasks),
        "expanded_tasks": expanded_count,
        "total_tasks": len(existing_tasks) + expanded_count,
        "merge_date": datetime.now().isoformat(),
        "description": "合并现有任务和扩展任务"
    }
    
    with open("data/tasks_merged_index.json", 'w', encoding='utf-8') as f:
        json.dump(merged_index, f, indent=2, ensure_ascii=False)
    
    print("任务合并完成！")

if __name__ == "__main__":
    merge_with_existing_tasks()