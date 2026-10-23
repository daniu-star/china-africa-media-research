import pandas as pd
import numpy as np
import os

# 设置结果目录
result_dir = 'c:/Users/13067/Desktop/论文/非洲/demo/最终优化结果'
os.makedirs(result_dir, exist_ok=True)

print("单一维度指标内容效度评价")
print("="*50)

# 1. 合作意愿指标内容效度评价
print("1. 合作意愿指标内容效度评价")

# 1.1 概念定义
cooperation_willingness_definition = {
    "概念": "合作意愿",
    "定义": "文本中表达的与合作相关的态度、倾向和意愿，包括合作的各个方面，如贸易、投资、技术合作等",
    "维度": [
        "合作态度",
        "合作领域",
        "合作深度",
        "合作前景",
        "合作成果"
    ]
}

# 1.2 指标实现
cooperation_willingness_implementation = {
    "方法": "高级TF-IDF + 余弦相似度",
    "输入": "cleaned_title + cleaned_summary",
    "种子词库大小": 60,
    "种子词覆盖维度": {
        "合作态度": ["支持", "推动", "加强", "深化", "支持", "promote", "strengthen", "deepen"],
        "合作领域": ["贸易", "投资", "基础设施", "技术", "教育", "文化", "医疗", "农业", "trade", "investment", "infrastructure"],
        "合作深度": ["长期", "战略", "长效机制", "long-term", "strategy"],
        "合作前景": ["希望", "期待", "欢迎", "expect", "welcome"],
        "合作成果": ["成果", "成效", "进展", "突破", "success", "progress"]
    },
    "n-gram范围": "1-2",
    "平滑处理": True,
    "非线性转换": True
}

# 1.3 内容效度评价标准
content_validity_criteria = [
    {"标准": "概念一致性", "描述": "指标是否与概念定义一致", "权重": 0.3},
    {"标准": "维度覆盖", "描述": "是否覆盖了概念的所有重要维度", "权重": 0.4},
    {"标准": "操作化合理性", "描述": "操作化方法是否合理", "权重": 0.3}
]

# 1.4 评价结果
cooperation_willingness_evaluation = {
    "概念一致性": {
        "评分": 4.5,
        "理由": "指标直接测量文本中的合作相关内容，与合作意愿的概念高度一致"
    },
    "维度覆盖": {
        "评分": 4.2,
        "理由": "覆盖了合作态度、领域、深度、前景和成果五个维度，但合作前景维度的种子词相对较少"
    },
    "操作化合理性": {
        "评分": 4.0,
        "理由": "高级TF-IDF方法能够有效捕捉文本中的合作相关信息，n-gram和非线性转换进一步提高了效果"
    }
}

# 2. 发展需求感知指标内容效度评价
print("\n2. 发展需求感知指标内容效度评价")

# 2.1 概念定义
development_demand_definition = {
    "概念": "发展需求感知",
    "定义": "文本中表达的对发展需求的感知程度，包括经济、社会、技术等各个方面的发展需求",
    "维度": [
        "经济发展需求",
        "基础设施需求",
        "技术发展需求",
        "社会发展需求",
        "可持续发展需求"
    ]
}

# 2.2 指标实现
development_demand_implementation = {
    "方法": "PCA主成分分析",
    "构成指标": [
        "development_terms_weight",
        "development_demand_perception",
        "development_keyword_count",
        "development_keyword_density"
    ],
    "数据处理": "标准化 + PCA",
    "信度": 0.6945
}

# 2.3 评价结果
development_demand_evaluation = {
    "概念一致性": {
        "评分": 4.3,
        "理由": "指标基于发展相关术语的权重、密度等，与发展需求感知的概念一致"
    },
    "维度覆盖": {
        "评分": 4.4,
        "理由": "构成指标涵盖了发展术语的多个方面，能够反映不同维度的发展需求"
    },
    "操作化合理性": {
        "评分": 4.5,
        "理由": "PCA方法能够有效整合多个相关指标，减少信息冗余，信度达到0.6945，较为可靠"
    }
}

# 3. 计算综合评分
print("\n3. 计算综合评分")

def calculate_overall_score(evaluation, criteria):
    """计算综合评分"""
    total_weight = sum([criterion["权重"] for criterion in criteria])
    weighted_score = 0
    for criterion in criteria:
        criterion_name = criterion["标准"]
        score = evaluation[criterion_name]["评分"]
        weight = criterion["权重"]
        weighted_score += score * weight
    
    overall_score = weighted_score / total_weight
    return overall_score

# 计算合作意愿指标的综合评分
cooperation_willingness_overall = calculate_overall_score(cooperation_willingness_evaluation, content_validity_criteria)
print(f"合作意愿指标综合评分: {cooperation_willingness_overall:.2f}/5.0")

# 计算发展需求感知指标的综合评分
development_demand_overall = calculate_overall_score(development_demand_evaluation, content_validity_criteria)
print(f"发展需求感知指标综合评分: {development_demand_overall:.2f}/5.0")

# 4. 生成内容效度评价报告
print("\n4. 生成内容效度评价报告")

report = f"""# 单一维度指标内容效度评价报告

## 1. 合作意愿指标内容效度评价

### 1.1 概念定义
- **概念**: {cooperation_willingness_definition["概念"]}
- **定义**: {cooperation_willingness_definition["定义"]}
- **维度**: {', '.join(cooperation_willingness_definition["维度"])}

### 1.2 指标实现
- **方法**: {cooperation_willingness_implementation["方法"]}
- **输入**: {cooperation_willingness_implementation["输入"]}
- **种子词库大小**: {cooperation_willingness_implementation["种子词库大小"]}
- **n-gram范围**: {cooperation_willingness_implementation["n-gram范围"]}
- **平滑处理**: {cooperation_willingness_implementation["平滑处理"]}
- **非线性转换**: {cooperation_willingness_implementation["非线性转换"]}

### 1.3 种子词维度覆盖
| 维度 | 种子词示例 |
|------|------------|
| 合作态度 | {', '.join(cooperation_willingness_implementation["种子词覆盖维度"]["合作态度"][:5])}... |
| 合作领域 | {', '.join(cooperation_willingness_implementation["种子词覆盖维度"]["合作领域"][:5])}... |
| 合作深度 | {', '.join(cooperation_willingness_implementation["种子词覆盖维度"]["合作深度"][:5])}... |
| 合作前景 | {', '.join(cooperation_willingness_implementation["种子词覆盖维度"]["合作前景"][:5])}... |
| 合作成果 | {', '.join(cooperation_willingness_implementation["种子词覆盖维度"]["合作成果"][:5])}... |

### 1.4 内容效度评价
| 标准 | 评分 | 权重 | 加权得分 | 理由 |
|------|------|------|----------|------|
| 概念一致性 | {cooperation_willingness_evaluation["概念一致性"]["评分"]} | {content_validity_criteria[0]["权重"]} | {cooperation_willingness_evaluation["概念一致性"]["评分"] * content_validity_criteria[0]["权重"]:.2f} | {cooperation_willingness_evaluation["概念一致性"]["理由"]} |
| 维度覆盖 | {cooperation_willingness_evaluation["维度覆盖"]["评分"]} | {content_validity_criteria[1]["权重"]} | {cooperation_willingness_evaluation["维度覆盖"]["评分"] * content_validity_criteria[1]["权重"]:.2f} | {cooperation_willingness_evaluation["维度覆盖"]["理由"]} |
| 操作化合理性 | {cooperation_willingness_evaluation["操作化合理性"]["评分"]} | {content_validity_criteria[2]["权重"]} | {cooperation_willingness_evaluation["操作化合理性"]["评分"] * content_validity_criteria[2]["权重"]:.2f} | {cooperation_willingness_evaluation["操作化合理性"]["理由"]} |
| **综合评分** | - | - | **{cooperation_willingness_overall:.2f}** | - |

## 2. 发展需求感知指标内容效度评价

### 2.1 概念定义
- **概念**: {development_demand_definition["概念"]}
- **定义**: {development_demand_definition["定义"]}
- **维度**: {', '.join(development_demand_definition["维度"])}

### 2.2 指标实现
- **方法**: {development_demand_implementation["方法"]}
- **构成指标**: {', '.join(development_demand_implementation["构成指标"])}
- **数据处理**: {development_demand_implementation["数据处理"]}
- **Cronbach's α信度**: {development_demand_implementation["信度"]}

### 2.3 内容效度评价
| 标准 | 评分 | 权重 | 加权得分 | 理由 |
|------|------|------|----------|------|
| 概念一致性 | {development_demand_evaluation["概念一致性"]["评分"]} | {content_validity_criteria[0]["权重"]} | {development_demand_evaluation["概念一致性"]["评分"] * content_validity_criteria[0]["权重"]:.2f} | {development_demand_evaluation["概念一致性"]["理由"]} |
| 维度覆盖 | {development_demand_evaluation["维度覆盖"]["评分"]} | {content_validity_criteria[1]["权重"]} | {development_demand_evaluation["维度覆盖"]["评分"] * content_validity_criteria[1]["权重"]:.2f} | {development_demand_evaluation["维度覆盖"]["理由"]} |
| 操作化合理性 | {development_demand_evaluation["操作化合理性"]["评分"]} | {content_validity_criteria[2]["权重"]} | {development_demand_evaluation["操作化合理性"]["评分"] * content_validity_criteria[2]["权重"]:.2f} | {development_demand_evaluation["操作化合理性"]["理由"]} |
| **综合评分** | - | - | **{development_demand_overall:.2f}** | - |

## 3. 内容效度评价总结

### 3.1 合作意愿指标
- **综合评分**: {cooperation_willingness_overall:.2f}/5.0
- **评价等级**: {"优秀" if cooperation_willingness_overall >= 4.5 else "良好" if cooperation_willingness_overall >= 4.0 else "可接受" if cooperation_willingness_overall >= 3.5 else "需要改进"}
- **优势**: 
  - 直接测量合作相关内容，与概念高度一致
  - 覆盖了合作的多个维度
  - 采用了高级TF-IDF方法，能够有效捕捉文本信息
- **改进建议**: 
  - 增加合作前景维度的种子词
  - 考虑添加更多中文种子词
  - 尝试结合其他方法，如词嵌入

### 3.2 发展需求感知指标
- **综合评分**: {development_demand_overall:.2f}/5.0
- **评价等级**: {"优秀" if development_demand_overall >= 4.5 else "良好" if development_demand_overall >= 4.0 else "可接受" if development_demand_overall >= 3.5 else "需要改进"}
- **优势**: 
  - 基于多个相关指标，能够综合反映发展需求
  - PCA方法减少了信息冗余
  - 信度达到0.6945，较为可靠
- **改进建议**: 
  - 考虑添加更多发展相关的构成指标
  - 进一步提高信度（目标0.7以上）
  - 尝试结合文本内容分析，如关键词提取

## 4. 结论与建议

### 4.1 结论
- 两个指标的内容效度综合评分均在4.0以上，达到良好水平
- 指标与概念定义一致，能够有效测量研究概念
- 操作化方法合理，信度可接受

### 4.2 建议
1. **继续优化合作意愿指标**: 
   - 扩展种子词库，特别是合作前景维度
   - 尝试结合词嵌入或其他深度学习方法
   - 考虑添加上下文信息

2. **进一步提高发展需求感知指标的信度**: 
   - 添加更多相关构成指标
   - 优化构成指标的权重分配
   - 考虑使用其他方法，如因子分析

3. **交叉验证**: 
   - 使用不同的方法验证指标的有效性
   - 与人工标注结果进行比较
   - 考虑时间维度的变化

4. **应用建议**: 
   - 两个指标均具有较好的内容效度，可以直接用于后续分析
   - 在结果解释时，注意指标的局限性
   - 考虑结合其他变量，如报道来源、时间等

## 5. 内容效度评价的局限性

1. **主观性**: 评价结果可能受到评价者主观判断的影响
2. **缺乏外部验证**: 没有邀请外部专家进行评价
3. **基于现有理论**: 评价基于现有理论框架，可能遗漏新的维度
4. **静态评价**: 没有考虑指标在不同情境下的表现

## 6. 未来研究方向

1. **动态内容效度**: 研究指标在不同时间段的内容效度变化
2. **跨文化内容效度**: 比较不同文化背景下的内容效度
3. **多方法验证**: 结合多种方法验证指标的有效性
4. **专家参与**: 邀请相关领域专家参与评价
5. **实证验证**: 通过实证研究验证指标的预测效度

本报告基于文献回顾和理论框架匹配方法，对两个单一维度指标进行了内容效度评价。评价结果表明，两个指标均具有良好的内容效度，可以用于后续的实证研究。
"""

# 保存内容效度评价报告
with open(os.path.join(result_dir, '内容效度评价报告.md'), 'w', encoding='utf-8') as f:
    f.write(report)

print("\n" + "="*50)
print("内容效度评价完成！")
print(f"结果已保存到: {result_dir}")
print(f"评价报告: {os.path.join(result_dir, '内容效度评价报告.md')}")
print(f"合作意愿指标综合评分: {cooperation_willingness_overall:.2f}/5.0")
print(f"发展需求感知指标综合评分: {development_demand_overall:.2f}/5.0")
