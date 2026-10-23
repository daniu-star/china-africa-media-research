# 非洲媒体论文原始数据：本地诊断报告

> 生成时间：2026-10-22T21:29:56 ｜ 审计脚本：1.2.0
> **无新闻正文、标题、网址或逐条记录写入报告。** 本报告为代码自动诊断，不等于专家核验或因果识别。

## 1. 文件与分析数据集识别
- 扫描文件数：1；已读取：1；失败或跳过：0
- 检出字段结构：1组（文件结构不同时不能直接相加为论文样本）。
- 选定主要分析结构：`c53af3b04c26`，共 3118215 条；可能用于模型的完整主变量观测 0 条。
- 论文声称：22646条有效报道、44家新闻网站、2000—2025年。

## 2. 变量匹配及缺失
| 角色 | 匹配列名 | 缺失率 |
|---|---|---:|
| identity | （未识别） | — |
| development | （未识别） | — |
| cooperation | （未识别） | — |
| emotion | （未识别） | — |
| region | （未识别） | — |
| outlet | source | 99.403% |
| year | （未识别） | — |
| sentiment | （未识别） | — |
| semantic | （未识别） | — |
| trust | （未识别） | — |
| expectation | （未识别） | — |
| worry | （未识别） | — |
| confusion | （未识别） | — |
| word_count | （未识别） | — |
| cluster | （未识别） | — |

## 3. 各区域样本
| 区域 | N | 占比 | 论文报告 |
|---|---:|---:|---:|

## 4. 数值统计（在全部有效数值上计算均值/标准差；分位数及偏度为抽样估计）
| 指标 | N | 均值 | 标准差 | 最小值 | 中位数* | 最大值 |
|---|---:|---:|---:|---:|---:|---:|

## 5. 与论文核心主张相关的核验
### 5.1 因变量公式复算
无法复算：没有同时匹配认同、情感值、语义关联度列。
### 5.2 关键相关系数
### 5.3 历史年分与数据粒度
- 2013年前记录数：0
- 2025年后记录数：0
- 无法解析年份数：3118116
- 新闻文本精确重复候选：0；标题重复候选：14606；ID重复候选：0
- 媒体机构识别数量：76
- 超出论文声明取值范围的条数：{}

### 5.4 可选描述性回归（非因果）
- 状态：skipped
- 跳过原因：No rows with identity, development, emotion as valid numerics

## 6. 按优先级排列的自动警报
1. **[P1] Valid corpus does not match manuscript N** — 证据：Current schema family 3118215 vs manuscript 22646；下一步：Confirm whether this family is raw, cleaned or analytical; document selection funnel
2. **[P0] Field mapping missing: identity** — 证据：Cannot find unambiguous header；下一步：Edit field_mapping.json override then rerun
3. **[P0] Field mapping missing: development** — 证据：Cannot find unambiguous header；下一步：Edit field_mapping.json override then rerun
4. **[P1] Field mapping missing: cooperation** — 证据：Cannot find unambiguous header；下一步：Edit field_mapping.json override then rerun
5. **[P0] Field mapping missing: emotion** — 证据：Cannot find unambiguous header；下一步：Edit field_mapping.json override then rerun
6. **[P1] Field mapping missing: region** — 证据：Cannot find unambiguous header；下一步：Edit field_mapping.json override then rerun

## 6.1 PCA和聚类附加核查
- 无法执行：当前文件中缺乏匹配的PCA三个源指标或已有聚类标签。

## 7. 当前数据不能单独证明的事项
- “媒体机构认同”是否能由文章文本推及：需要理论定义与人工效标。
- BERT 是否真在5万条标注语料上训练、87.3%何种准确率：需要训练日志、完整类别指标及500条人工双人复核。
- PCA是否确为第一主成分69.45%：需要原始3个成分、标准化方式、载荷及特征值。
- 词库是否相互独立且关键词重叠率<5%：需要词表和构造代码。
- 因果“发展→情感→认同”：横截面文本的回归/Bootstrap本身不解决反向因果或遗漏变量。
- K=6聚类是否合理：需要聚类输入的标准化、选择K理由、稳定性和簇中心。

## 8. 数据安全和再次反馈
- 请**只上传**同目录下 `africa_audit_result.zip`，不要上传原始新闻正文。
- `field_mapping_suggestions.json` 包含列名以帮助识别字段；如列名涉及敏感信息，请先检查后上传。
- 如自动识别错误，在 `field_mapping.json` 中人工指定角色→列名，重新运行。
