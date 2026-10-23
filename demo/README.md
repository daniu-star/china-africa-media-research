# 金字塔报大规模分布式并行爬虫系统

## 系统概述

这是一个专门针对埃及金字塔报（Ahram Pyramid）的大规模分布式并行爬虫系统，支持高效、稳定地爬取新闻文章数据。

### 主要特性

- **分布式并行爬取**: 支持多线程并行处理，提高爬取效率
- **智能反爬虫策略**: 自适应延迟、用户代理轮换、请求频率控制
- **增强翻页功能**: 自动处理搜索结果翻页，确保完整爬取
- **多选择器策略**: 多种CSS选择器组合，提高解析成功率
- **实时数据保存**: 按关键词生成独立JSON文件，支持实时保存
- **性能监控**: 实时统计爬取进度、成功率、响应时间等指标
- **文章体裁推断**: 自动识别新闻、评论、访谈等不同体裁
- **转载检测**: 智能判断文章是否为转载内容

## 系统架构

```
final_pyramid_crawler_system.py  # 核心爬虫系统
run_final_system.py             # 启动脚本
final_config.json               # 配置文件
expanded_keywords_clusters.json  # 关键词文件
requirements.txt                # 依赖包列表
README.md                       # 使用说明
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 验证配置

```bash
# 干运行模式验证配置
python run_final_system.py --dry-run
```

### 3. 测试运行

```bash
# 测试模式（只处理前3个关键词）
python run_final_system.py --mode test
```

### 4. 完整运行

```bash
# 并行模式（默认）
python run_final_system.py

# 顺序模式（单线程）
python run_final_system.py --mode sequential
```

## 详细使用说明

### 命令行参数

| 参数 | 缩写 | 默认值 | 说明 |
|------|------|--------|------|
| `--config` | `-c` | `final_config.json` | 配置文件路径 |
| `--keywords` | `-k` | `expanded_keywords_clusters.json` | 关键词文件路径 |
| `--output` | `-o` | `final_pyramid_data` | 输出目录 |
| `--workers` | `-w` | `5` | 并行工作线程数 |
| `--mode` | `-m` | `parallel` | 运行模式（parallel/sequential/test） |
| `--limit` | `-l` | 无限制 | 限制处理的关键词数量 |
| `--log-level` | 无 | `INFO` | 日志级别 |
| `--dry-run` | 无 | `false` | 干运行模式 |

### 运行模式

1. **并行模式（parallel）**: 多线程并行处理关键词，效率最高
2. **顺序模式（sequential）**: 单线程顺序处理，稳定性最好
3. **测试模式（test）**: 只处理前3个关键词，用于功能验证

### 配置文件说明

`final_config.json` 包含以下主要配置项：

```json
{
    "keywords_file": "expanded_keywords_clusters.json",
    "output_dir": "final_pyramid_data",
    "max_workers": 5,
    "max_retries": 3,
    "request_timeout": 15,
    "min_delay": 2,
    "max_delay": 5,
    "max_pages": 10,
    "max_articles_per_keyword": 50,
    "log_level": "INFO",
    "start_date": "2010-01-01",
    "end_date": "2025-12-31"
}
```

### 关键词文件格式

关键词文件应为JSON格式，包含关键词聚类：

```json
{
    "clusters": [
        {
            "name": "政治",
            "keywords": ["埃及政府", "总统", "议会", "选举"]
        },
        {
            "name": "经济", 
            "keywords": ["经济", "贸易", "投资", "GDP"]
        }
    ]
}
```

## 输出数据格式

### 文件命名规则

```
pyramid_关键词_时间戳.json
```

示例：`pyramid_egypt_20241215_143022.json`

### 数据结构

```json
{
    "metadata": {
        "keyword": "搜索关键词",
        "newspaper": "Ahram Pyramid",
        "crawl_time": "2024-12-15 14:30:22",
        "total_articles": 25,
        "time_range": "2010-01-01 - 2025-12-31",
        "system_version": "FinalPyramidCrawlerSystem v1.0"
    },
    "articles": [
        {
            "title": "文章标题",
            "url": "文章链接",
            "keyword": "搜索关键词",
            "newspaper": "Ahram Pyramid",
            "crawl_time": "爬取时间",
            "search_time": "搜索时间",
            "publish_time": "发布时间",
            "content": "正文内容",
            "word_count": 字数,
            "author": "作者",
            "source": "来源",
            "article_type": "文章体裁",
            "source_type": "原创/转载",
            "tags": ["标签1", "标签2"],
            "categories": ["分类1", "分类2"]
        }
    ]
}
```

## 高级功能

### 1. 自适应延迟控制

系统根据请求频率自动调整延迟时间，避免触发反爬虫机制。

### 2. 用户代理轮换

每次请求使用不同的用户代理，模拟真实浏览器行为。

### 3. 智能翻页处理

自动识别并处理搜索结果翻页，支持多种翻页模式。

### 4. 多选择器策略

使用多种CSS选择器组合，提高页面元素解析的成功率。

### 5. 线程安全操作

所有共享数据操作都使用线程锁，确保多线程环境下的数据一致性。

### 6. 实时性能监控

实时监控请求成功率、响应时间、爬取进度等关键指标。

## 故障排除

### 常见问题

1. **依赖包安装失败**
   ```bash
   # 使用国内镜像源
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

2. **关键词文件格式错误**
   - 确保文件为有效的JSON格式
   - 检查文件编码是否为UTF-8

3. **网络连接问题**
   - 检查网络连接是否正常
   - 尝试使用代理服务器

4. **反爬虫限制**
   - 增加延迟时间配置
   - 减少并行线程数
   - 使用更真实的用户代理

### 日志文件

系统生成以下日志文件：
- `final_system.log`: 系统运行日志
- `final_pyramid_data/system.log`: 爬虫详细日志

## 性能优化建议

1. **网络优化**
   - 使用高速稳定的网络连接
   - 考虑使用代理服务器池

2. **硬件优化**
   - 增加内存容量
   - 使用SSD硬盘提高IO性能

3. **配置优化**
   - 根据网络状况调整延迟时间
   - 合理设置并行线程数
   - 优化关键词聚类策略

## 版本历史

- **v1.0** (2024-12-15): 初始版本发布
  - 实现基本爬虫功能
  - 支持并行处理
  - 增强反爬虫策略

## 技术支持

如有问题或建议，请联系开发团队。

## 免责声明

本系统仅供学术研究使用，请遵守相关法律法规和网站的使用条款。