# 数据与分析目录导览

## 主要输入

- `清洗数据/清洗数据.json`：约 1.32 GB，JSON 数组，原始数据入口。抽查首条记录字段为 `title`、`summary`、`date`、`category`、`source`、`scraped_time`，均为字符串；这只描述首条记录，不代表全量一致。
- `最终优化结果/data_with_5_regions.csv`：约 4.91 GB，41 列，含新闻文本与派生指标。保留原貌，不在此次上传中重算或修订。
- `非洲数据/非洲数据/`：历史采集数据、备份、分散结果、模型及网页模板等；含与其他目录完全相同的文件，清单记录文件级重复关系。

## 分析表列名

```text
original_index, data_type, title, summary, cleaned_title, cleaned_summary,
combined_text, date, category, source, scraped_time, year, sentiment_label,
全部情感强度, positive_words_count, negative_words_count, total_words_count,
text_for_similarity, community_similarity, normalized_sentiment,
china_africa_community_recognition, processed_text, development_terms_weight,
local_sentiment, standardized_tfidf_weight, standardized_local_sentiment,
development_demand_perception, development_keyword_count,
development_keyword_density, processed_title, long_term_word_count,
has_multi_agent_interaction, long_term_word_count_log, long_term_percentile,
multi_agent_percentile, cooperation_depth_index, long_term_word_count_scaled,
has_multi_agent_interaction_scaled, cooperation_depth_index_pred,
prediction_confidence, source_region_5
```

这是文件表头索引，不是已经核验的操作化定义。需结合生成脚本追溯 `cooperation_depth_index_pred` 等预测字段、标准化字段与实际建模变量。

## 分析材料

| 原目录 | 主要用途（按目录名称识别） |
|---|---|
| `变量关系检验/` | 变量关系检验与可视化产物 |
| `因变量结果/` | 因变量相关输出 |
| `自变量分析结果/` | 自变量描述与分析输出 |
| `模型建构结果/` | 模型构建输出 |
| `认同路径/` | 认同路径相关图表与结果 |
| `可视化/`、`ppt_charts/` | 论文或汇报图表 |
| `非洲_诊断输出/`、`清洗数据/非洲_诊断输出/` | 既有诊断报告、字段映射与打包结果 |
| `清洗数据/审计工具/` | 已有数据审计工具 |

根目录保留多轮脚本。可从 `模型建构分析.py`、`多群组结构方程模型.py`、`情感维度细化与多重中介分析.py` 等名称开始检索，但这些不是已经验证的统一流水线。上传整理没有执行这些分析脚本，也没有替研究者选择唯一最终模型。
