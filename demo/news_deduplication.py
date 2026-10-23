import os
import json
import hashlib
import pandas as pd
import logging
import re
from difflib import SequenceMatcher
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs, urlunparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_deduplication.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 定义要遍历的目录
DIRECTORIES = [
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\零散",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\backup",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\backups",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\china_africa_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\crawler_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\data",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\firecrawl_early_data_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\live_playwright_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\local_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\massive_crawler_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\models",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\optimized_crawler_results",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\static",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\templates",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\test_data",
    r"c:\Users\13067\Desktop\论文\非洲\demo\非洲数据\非洲数据\test_storage"
]

# 支持的文件扩展名
SUPPORTED_EXTENSIONS = ['.json', '.csv', '.xlsx']

# 配置参数
MIN_SIMILARITY_THRESHOLD = 0.9  # 文本相似度阈值
MAX_CONTENT_LENGTH = 1000  # 用于哈希计算的最大内容长度

def normalize_url(url):
    """
    规范化URL，去除查询参数、锚点等
    
    Args:
        url: 原始URL
        
    Returns:
        str: 规范化后的URL
    """
    if not url:
        return ''
    
    try:
        parsed = urlparse(url)
        # 移除查询参数和锚点
        normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return normalized
    except Exception as e:
        logger.warning(f"URL规范化失败: {url}, 错误: {str(e)}")
        return url


def preprocess_text(text):
    """
    预处理文本，去除多余空格、特殊字符等
    
    Args:
        text: 原始文本（可能是字符串、字典或其他类型）
        
    Returns:
        str: 预处理后的文本
    """
    # 处理非字符串类型
    if not isinstance(text, str):
        try:
            # 尝试将字典转换为字符串
            if isinstance(text, dict):
                text = json.dumps(text, ensure_ascii=False)
            else:
                # 其他类型转换为字符串
                text = str(text)
        except Exception as e:
            logger.warning(f"文本预处理失败，转换类型出错: {str(e)}")
            return ''
    
    if not text:
        return ''
    
    # 去除多余空格和换行符
    text = re.sub(r'\s+', ' ', text)
    # 去除特殊字符
    text = re.sub(r'[^\w\s]', '', text)
    # 转为小写
    text = text.lower()
    return text


def get_ngrams(text, n=3):
    """
    获取文本的n-gram集合
    
    Args:
        text: 输入文本
        n: n-gram的n值
        
    Returns:
        set: n-gram集合
    """
    if len(text) < n:
        return set()
    
    ngrams = set()
    for i in range(len(text) - n + 1):
        ngram = text[i:i+n]
        ngrams.add(ngram)
    return ngrams


def calculate_similarity(text1, text2, n=3):
    """
    使用Jaccard相似度计算两个文本的相似度（更快）
    
    Args:
        text1: 第一个文本
        text2: 第二个文本
        n: n-gram的n值
        
    Returns:
        float: 相似度，0-1之间
    """
    if not text1 or not text2:
        return 0.0
    
    # 使用n-gram计算Jaccard相似度
    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)
    
    if not ngrams1 or not ngrams2:
        return 0.0
    
    # 计算交集和并集大小
    intersection = len(ngrams1.intersection(ngrams2))
    union = len(ngrams1.union(ngrams2))
    
    return intersection / union if union > 0 else 0.0


def get_file_hash(url, title, content):
    """
    基于URL、标题和正文生成SHA256哈希值
    优化：URL规范化、文本预处理、截取前N个字符
    
    Args:
        url: 新闻URL
        title: 新闻标题
        content: 新闻正文
        
    Returns:
        str: SHA256哈希值
    """
    # 处理None值
    url = url or ''
    title = title or ''
    content = content or ''
    
    # URL规范化
    normalized_url = normalize_url(url)
    
    # 文本预处理
    processed_title = preprocess_text(title)
    processed_content = preprocess_text(content)
    
    # 截取内容，避免哈希计算过慢
    truncated_content = processed_content[:MAX_CONTENT_LENGTH]
    
    # 组合字符串
    combined = f"{normalized_url}||{processed_title}||{truncated_content}"
    
    # 生成哈希值
    hash_object = hashlib.sha256(combined.encode('utf-8'))
    return hash_object.hexdigest()


def read_json_file(file_path):
    """
    读取JSON文件，提取新闻条目
    
    Args:
        file_path: JSON文件路径
        
    Returns:
        list: 新闻条目列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = []
        
        # 处理不同的JSON结构
        if isinstance(data, list):
            # 直接是新闻条目列表
            for item in data:
                articles.append(item)
        elif isinstance(data, dict):
            # 包含在键中
            if 'articles' in data:
                articles.extend(data['articles'])
            elif 'items' in data:
                articles.extend(data['items'])
            elif 'results' in data:
                articles.extend(data['results'])
            elif 'tasks' in data:
                # 跳过任务文件
                pass
            else:
                # 可能是单个新闻条目
                articles.append(data)
        
        return articles
    except Exception as e:
        logger.error(f"读取JSON文件失败: {file_path}, 错误: {str(e)}")
        return []


def read_csv_file(file_path):
    """
    读取CSV文件，提取新闻条目
    
    Args:
        file_path: CSV文件路径
        
    Returns:
        list: 新闻条目列表
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"读取CSV文件失败: {file_path}, 错误: {str(e)}")
        return []


def read_xlsx_file(file_path):
    """
    读取XLSX文件，提取新闻条目
    
    Args:
        file_path: XLSX文件路径
        
    Returns:
        list: 新闻条目列表
    """
    try:
        df = pd.read_excel(file_path)
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"读取XLSX文件失败: {file_path}, 错误: {str(e)}")
        return []


def extract_news_fields(article):
    """
    从新闻条目中提取标准化的字段
    
    Args:
        article: 新闻条目（字典或其他类型）
        
    Returns:
        tuple: (url, title, content)
    """
    # 检查article类型
    if not isinstance(article, dict):
        # 如果不是字典类型，尝试转换或返回空值
        try:
            if isinstance(article, str):
                # 尝试将字符串解析为JSON
                import json
                article = json.loads(article)
            else:
                # 其他类型，直接返回空值
                return '', '', ''
        except:
            # 解析失败，返回空值
            return '', '', ''
    
    # 提取URL
    url = article.get('url') or article.get('URL') or article.get('link') or ''
    
    # 提取标题
    title = article.get('title') or article.get('Title') or article.get('headline') or ''
    
    # 提取正文
    content = article.get('content') or article.get('Content') or article.get('body') or ''
    
    # 尝试从summary中获取内容
    if not content:
        content = article.get('summary') or article.get('Summary') or ''
    
    return url, title, content


def process_file(file_path):
    """
    处理单个文件，提取新闻条目并生成哈希值
    
    Args:
        file_path: 文件路径
        
    Returns:
        tuple: (file_path, articles, hashes)
    """
    logger.info(f"处理文件: {file_path}")
    
    # 根据文件扩展名选择读取方法
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.json':
        articles = read_json_file(file_path)
    elif ext == '.csv':
        articles = read_csv_file(file_path)
    elif ext == '.xlsx':
        articles = read_xlsx_file(file_path)
    else:
        logger.warning(f"不支持的文件格式: {file_path}")
        return file_path, [], []
    
    # 提取标准化字段并生成哈希值
    results = []
    for article in articles:
        url, title, content = extract_news_fields(article)
        if url or title or content:  # 至少有一个字段不为空
            hash_val = get_file_hash(url, title, content)
            results.append((hash_val, article))
    
    return file_path, articles, results


def is_duplicate(article, unique_articles, similarity_threshold=MIN_SIMILARITY_THRESHOLD):
    """
    判断新闻是否为重复项
    优化：添加快速过滤条件，减少相似度计算次数
    
    Args:
        article: 当前新闻条目
        unique_articles: 已存在的唯一新闻列表
        similarity_threshold: 相似度阈值
        
    Returns:
        bool: 是否为重复项
    """
    # 提取当前文章的关键信息
    curr_url, curr_title, curr_content = extract_news_fields(article)
    curr_title_processed = preprocess_text(curr_title)
    curr_content_processed = preprocess_text(curr_content)
    
    # 获取当前文章的长度信息
    curr_title_len = len(curr_title_processed)
    curr_content_len = len(curr_content_processed)
    
    # 遍历已存在的唯一新闻
    for unique_article in unique_articles:
        # 提取唯一文章的关键信息
        unique_url, unique_title, unique_content = extract_news_fields(unique_article)
        unique_title_processed = preprocess_text(unique_title)
        unique_content_processed = preprocess_text(unique_content)
        
        # 1. 检查URL是否相同（规范化后）- 快速检查
        if normalize_url(curr_url) == normalize_url(unique_url) and curr_url and unique_url:
            return True
        
        # 2. 标题相似度检查
        unique_title_len = len(unique_title_processed)
        
        # 快速过滤：标题长度差异超过50%，不可能相似
        if curr_title_len > 10 and unique_title_len > 10:
            title_len_diff = abs(curr_title_len - unique_title_len) / max(curr_title_len, unique_title_len)
            if title_len_diff < 0.5:  # 长度差异小于50%才进行相似度计算
                title_similarity = calculate_similarity(curr_title_processed, unique_title_processed)
                if title_similarity >= similarity_threshold:
                    return True
        
        # 3. 正文相似度检查（仅对较长文本）
        unique_content_len = len(unique_content_processed)
        
        # 快速过滤1：至少有一个文本太短，跳过
        if curr_content_len < 50 or unique_content_len < 50:
            continue
        
        # 快速过滤2：正文长度差异超过70%，不可能相似
        content_len_diff = abs(curr_content_len - unique_content_len) / max(curr_content_len, unique_content_len)
        if content_len_diff >= 0.7:
            continue
        
        # 计算正文相似度
        content_similarity = calculate_similarity(curr_content_processed, unique_content_processed)
        if content_similarity >= similarity_threshold:
            return True
    
    return False


def main():
    """
    主函数，执行去重流程
    """
    logger.info("开始新闻数据去重处理")
    
    # 收集所有支持的文件
    all_files = []
    for directory in DIRECTORIES:
        if not os.path.exists(directory):
            logger.warning(f"目录不存在: {directory}")
            continue
        
        for root, _, files in os.walk(directory):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    all_files.append(os.path.join(root, file))
    
    logger.info(f"找到 {len(all_files)} 个支持的文件")
    
    # 使用线程池处理文件
    all_articles = []
    total_articles = 0
    processed_files = 0
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        # 提交所有文件处理任务
        futures = [executor.submit(process_file, file_path) for file_path in all_files]
        
        # 处理结果
        for future in tqdm(as_completed(futures), total=len(futures), desc="处理文件"):
            file_path, articles, results = future.result()
            processed_files += 1
            total_articles += len(articles)
            
            # 收集所有新闻条目
            all_articles.extend(articles)
    
    logger.info(f"开始去重处理，总新闻数: {len(all_articles)}")
    
    # 去重逻辑：先按哈希分组，再进行相似度比较
    unique_articles = []
    hash_groups = {}
    
    # 第一步：按哈希值分组
    for article in tqdm(all_articles, desc="按哈希值分组"):
        url, title, content = extract_news_fields(article)
        if url or title or content:  # 至少有一个字段不为空
            hash_val = get_file_hash(url, title, content)
            if hash_val not in hash_groups:
                hash_groups[hash_val] = []
            hash_groups[hash_val].append(article)
    
    logger.info(f"按哈希值分组完成，共 {len(hash_groups)} 个组")
    
    # 第二步：组内去重（每组保留一个代表）
    group_representatives = []
    for group_articles in tqdm(hash_groups.values(), desc="组内去重"):
        if group_articles:
            group_representatives.append(group_articles[0])
    
    logger.info(f"组内去重完成，剩余 {len(group_representatives)} 个代表文章")
    
    # 第三步：代表文章间的相似度去重
    # 优化：先按标题长度分组，减少比较次数
    # 1. 按标题长度分组
    title_length_groups = {}
    for article in group_representatives:
        _, title, _ = extract_news_fields(article)
        title_len = len(preprocess_text(title))
        length_group = title_len // 10  # 每10个字符为一个组
        if length_group not in title_length_groups:
            title_length_groups[length_group] = []
        title_length_groups[length_group].append(article)
    
    # 2. 组内去重：只比较相似长度组内的文章
    unique_articles = []
    
    for length_group, group_articles in tqdm(title_length_groups.items(), desc="按标题长度分组去重"):
        # 组内相似度去重
        for article in group_articles:
            # 只与已存在的唯一文章比较
            if not is_duplicate(article, unique_articles):
                unique_articles.append(article)
    
    # 3. 跨组去重：只比较相邻长度组的文章
    logger.info(f"开始跨组去重，当前唯一文章数: {len(unique_articles)}")
    
    # 先保存初始唯一文章列表
    initial_unique = unique_articles.copy()
    final_unique = []
    
    for article in tqdm(initial_unique, desc="跨组相似度去重"):
        if not is_duplicate(article, final_unique):
            final_unique.append(article)
    
    unique_articles = final_unique
    
    # 输出统计信息
    logger.info(f"处理完成！")
    logger.info(f"总文件数: {len(all_files)}")
    logger.info(f"处理文件数: {processed_files}")
    logger.info(f"去重前新闻总数: {total_articles}")
    logger.info(f"按哈希值分组后: {len(group_representatives)}")
    logger.info(f"去重后新闻总数: {len(unique_articles)}")
    logger.info(f"重复新闻数: {total_articles - len(unique_articles)}")
    logger.info(f"总去重率: {((total_articles - len(unique_articles)) / total_articles * 100):.2f}%")
    logger.info(f"哈希去重率: {((total_articles - len(group_representatives)) / total_articles * 100):.2f}%")
    logger.info(f"相似度去重率: {((len(group_representatives) - len(unique_articles)) / len(group_representatives) * 100):.2f}%")
    
    # 保存去重后的结果
    output_file = "deduplicated_news_optimized.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_articles, f, ensure_ascii=False, indent=2)
        logger.info(f"优化后的去重结果已保存到: {output_file}")
    except Exception as e:
        logger.error(f"保存优化后的去重结果失败: {str(e)}")
    
    # 生成统计报告
    report_file = "deduplication_report_optimized.txt"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("新闻数据去重报告（优化版）\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"总目录数: {len(DIRECTORIES)}\n")
            f.write(f"总文件数: {len(all_files)}\n")
            f.write(f"处理文件数: {processed_files}\n")
            f.write(f"去重前新闻总数: {total_articles}\n")
            f.write(f"按哈希值分组后: {len(group_representatives)}\n")
            f.write(f"去重后新闻总数: {len(unique_articles)}\n")
            f.write(f"重复新闻数: {total_articles - len(unique_articles)}\n")
            f.write(f"总去重率: {((total_articles - len(unique_articles)) / total_articles * 100):.2f}%\n")
            f.write(f"哈希去重率: {((total_articles - len(group_representatives)) / total_articles * 100):.2f}%\n")
            f.write(f"相似度去重率: {((len(group_representatives) - len(unique_articles)) / len(group_representatives) * 100):.2f}%\n")
            f.write(f"相似度阈值: {MIN_SIMILARITY_THRESHOLD}\n")
        logger.info(f"优化后的去重报告已保存到: {report_file}")
    except Exception as e:
        logger.error(f"保存优化后的去重报告失败: {str(e)}")
    
    # 生成优化前后对比报告
    comparison_file = "deduplication_comparison.txt"
    try:
        with open(comparison_file, 'w', encoding='utf-8') as f:
            f.write("新闻数据去重优化前后对比\n")
            f.write("=" * 40 + "\n\n")
            f.write("优化前：\n")
            f.write("- 去重方法：仅基于哈希值完全匹配\n")
            f.write("- 优点：速度快，无误判\n")
            f.write("- 缺点：过于严格，无法处理URL变化、文本细微差异等情况\n")
            f.write("\n优化后：\n")
            f.write("- 去重方法：哈希分组 + 相似度比较\n")
            f.write("- 优点：\n")
            f.write("  * 放宽了查重条件，减少了漏判\n")
            f.write("  * 支持URL规范化，处理不同URL格式\n")
            f.write("  * 支持文本预处理，提高相似度比较准确性\n")
            f.write("  * 分层去重策略，兼顾速度和准确性\n")
            f.write("- 缺点：处理时间稍长\n")
            f.write("\n优化效果：\n")
            f.write(f"- 总文件数：{len(all_files)}\n")
            f.write(f"- 原始新闻数：{total_articles}\n")
            f.write(f"- 哈希分组后：{len(group_representatives)}\n")
            f.write(f"- 最终唯一新闻数：{len(unique_articles)}\n")
        logger.info(f"去重优化对比报告已保存到: {comparison_file}")
    except Exception as e:
        logger.error(f"保存去重优化对比报告失败: {str(e)}")


if __name__ == "__main__":
    main()
