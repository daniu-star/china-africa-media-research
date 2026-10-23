#!/usr/bin/env python3
"""
分布式爬虫系统 - 主节点
负责任务分发、状态监控和数据聚合
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue
from pydantic import BaseModel

# MongoDB支持
import pymongo
from pymongo import MongoClient

# 导入智能调度器
from task_scheduler_optimizer import IntelligentTaskScheduler, TaskPriority, ErrorType, classify_error, scheduler
from performance_monitor import performance_monitor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('distributed_master.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="分布式爬虫主节点", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'password123')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'crawler_db')

# 内存队列和文件存储（用于任务队列）
task_queue = Queue()
results_queue = Queue()
results_storage = []
results_lock = threading.Lock()

# 任务分发优化配置
TASK_PRIORITY_WEIGHTS = {
    'high': 3,
    'medium': 2,
    'low': 1
}

# 工作节点负载跟踪
worker_loads = {}
worker_last_active = {}

# 失败任务重试队列
failed_tasks_queue = Queue()
max_retry_attempts = 3
ERROR_RETRY_DELAYS = [5, 10, 30]  # 重试延迟时间（秒）
ERROR_TYPES = {
    'network_error': ['ConnectionError', 'Timeout', 'HTTPError'],
    'parsing_error': ['JSONDecodeError', 'ParseError'],
    'resource_error': ['MemoryError', 'ResourceExhausted'],
    'system_error': ['OSError', 'IOError']
}

class ErrorHandler:
    """错误处理管理器"""
    
    def __init__(self):
        self.error_stats = {
            'total_errors': 0,
            'error_types': {},
            'retry_success': 0,
            'retry_failures': 0
        }
    
    def classify_error(self, error: Exception) -> str:
        """分类错误类型"""
        error_name = type(error).__name__
        
        for error_type, error_names in ERROR_TYPES.items():
            if error_name in error_names:
                return error_type
        
        return 'unknown_error'
    
    def get_retry_delay(self, retry_count: int) -> int:
        """获取重试延迟时间"""
        if retry_count < len(ERROR_RETRY_DELAYS):
            return ERROR_RETRY_DELAYS[retry_count]
        return ERROR_RETRY_DELAYS[-1]  # 使用最后一个延迟时间
    
    def should_retry(self, error_type: str, retry_count: int) -> bool:
        """判断是否应该重试"""
        if retry_count >= max_retry_attempts:
            return False
        
        # 网络错误通常可以重试
        if error_type == 'network_error':
            return True
        
        # 解析错误可能无法通过重试解决
        if error_type == 'parsing_error':
            return retry_count < 1  # 只重试一次
        
        # 资源错误和系统错误通常需要人工干预
        return False
    
    def record_error(self, error: Exception, task_id: str = None):
        """记录错误统计"""
        error_type = self.classify_error(error)
        
        self.error_stats['total_errors'] += 1
        
        if error_type not in self.error_stats['error_types']:
            self.error_stats['error_types'][error_type] = 0
        self.error_stats['error_types'][error_type] += 1
        
        logger.error(f"错误记录 - 类型: {error_type}, 任务ID: {task_id}, 错误: {error}")
    
    def record_retry_result(self, success: bool):
        """记录重试结果"""
        if success:
            self.error_stats['retry_success'] += 1
        else:
            self.error_stats['retry_failures'] += 1
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return self.error_stats.copy()

# 创建全局错误处理器
error_handler = ErrorHandler()

# 数据存储目录
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 文件存储优化配置
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_RECORDS_PER_FILE = 1000  # 每个文件最多1000条记录

# 初始化文件索引，自动检测现有文件
CURRENT_FILE_INDEX = {}

def initialize_file_index():
    """初始化文件索引，自动检测现有文件"""
    global CURRENT_FILE_INDEX
    
    file_types = ['tasks', 'articles', 'results', 'workers']
    
    for file_type in file_types:
        # 查找该类型的所有文件
        max_index = -1
        for filename in os.listdir(DATA_DIR):
            if filename.startswith(f"{file_type}_") and filename.endswith('.json'):
                try:
                    # 提取文件索引
                    index_str = filename[len(file_type)+1:-5]  # 去掉前缀和后缀
                    index = int(index_str)
                    if index > max_index:
                        max_index = index
                except ValueError:
                    continue
        
        # 如果找到文件，检查最大索引文件的大小
        if max_index >= 0:
            current_file = os.path.join(DATA_DIR, f"{file_type}_{max_index}.json")
            if os.path.exists(current_file):
                file_size = os.path.getsize(current_file)
                # 如果文件超过大小限制，使用下一个索引
                if file_size > MAX_FILE_SIZE:
                    CURRENT_FILE_INDEX[file_type] = max_index + 1
                else:
                    CURRENT_FILE_INDEX[file_type] = max_index
            else:
                CURRENT_FILE_INDEX[file_type] = 0
        else:
            CURRENT_FILE_INDEX[file_type] = 0
    
    logger.info(f"初始化文件索引: {CURRENT_FILE_INDEX}")

# 初始化文件索引
initialize_file_index()

# 文件锁机制
file_locks = {}

def load_tasks_from_files() -> List[Dict[str, Any]]:
    """从现有的tasks_*.json文件加载任务到内存队列"""
    try:
        loaded_tasks = []
        tasks_count = 0
        
        # 查找所有tasks_*.json文件
        for filename in os.listdir(DATA_DIR):
            if filename.startswith("tasks_") and filename.endswith('.json'):
                file_path = os.path.join(DATA_DIR, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        
                        # 尝试解析为完整的JSON对象（包含tasks数组）
                        try:
                            data = json.loads(content)
                            if isinstance(data, dict) and 'tasks' in data:
                                # 这是tasks数组格式
                                tasks = data['tasks']
                                for task in tasks:
                                    if isinstance(task, dict) and task.get('status') == 'pending':
                                        loaded_tasks.append(task)
                                        tasks_count += 1
                            elif isinstance(data, list):
                                # 这是直接的任务列表格式
                                for task in data:
                                    if isinstance(task, dict) and task.get('status') == 'pending':
                                        loaded_tasks.append(task)
                                        tasks_count += 1
                        except json.JSONDecodeError:
                            # 如果整体解析失败，尝试按行解析
                            for line in content.split('\n'):
                                if line.strip():
                                    try:
                                        task_data = json.loads(line.strip())
                                        # 只加载状态为pending的任务
                                        if isinstance(task_data, dict) and task_data.get('status') == 'pending':
                                            loaded_tasks.append(task_data)
                                            tasks_count += 1
                                    except json.JSONDecodeError as e:
                                        logger.warning(f"文件 {filename} 中的JSON格式错误: {e}")
                                        continue
                                
                except Exception as e:
                    logger.error(f"读取任务文件 {filename} 失败: {e}")
                    continue
        
        logger.info(f"从文件加载了 {tasks_count} 个待处理任务")
        return loaded_tasks
        
    except Exception as e:
        logger.error(f"加载任务文件失败: {e}")
        return []

def get_current_file_path(file_type: str, base_dir: str = None) -> str:
    """获取当前文件路径，支持文件分片"""
    global CURRENT_FILE_INDEX
    
    # 使用指定的基础目录或默认DATA_DIR
    if base_dir is None:
        base_dir = DATA_DIR
    
    # 检查当前文件大小
    current_file = os.path.join(base_dir, f"{file_type}_{CURRENT_FILE_INDEX[file_type]}.json")
    
    if os.path.exists(current_file):
        # 如果文件超过最大大小或记录数，创建新文件
        file_size = os.path.getsize(current_file)
        if file_size > MAX_FILE_SIZE:
            # 循环查找下一个可用的文件索引
            while True:
                CURRENT_FILE_INDEX[file_type] += 1
                current_file = os.path.join(DATA_DIR, f"{file_type}_{CURRENT_FILE_INDEX[file_type]}.json")
                
                # 如果新文件不存在，或者存在但未超过大小限制，则使用该文件
                if not os.path.exists(current_file):
                    break
                
                new_file_size = os.path.getsize(current_file)
                if new_file_size <= MAX_FILE_SIZE:
                    break
    
    return current_file

def write_to_file(file_type: str, data: Dict[str, Any]) -> None:
    """写入数据到文件，支持分片文件"""
    import time
    
    # 根据文件类型选择存储目录
    base_dir = DATA_DIR
    if file_type == 'results':
        # 结果文件存储在 data/results 目录
        base_dir = os.path.join(DATA_DIR, 'results')
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
    
    file_path = get_current_file_path(file_type, base_dir)
    lock_file = file_path + '.lock'
    
    # 最大重试次数
    max_retries = 5
    retry_delay = 0.1  # 100ms
    
    for attempt in range(max_retries):
        try:
            # 检查锁文件是否存在
            if os.path.exists(lock_file):
                # 如果锁文件存在，等待并重试
                time.sleep(retry_delay)
                continue
            
            # 创建锁文件
            with open(lock_file, 'w') as lock:
                lock.write(str(os.getpid()))
            
            # 读取现有数据
            existing_data = []
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                # 验证JSON格式
                                json.loads(line.strip())
                                existing_data.append(line.strip())
                except json.JSONDecodeError as e:
                    logger.warning(f"文件 {file_path} 格式损坏，将重建文件: {e}")
                    existing_data = []
            
            # 添加新数据（保持原始JSON字符串格式）
            new_record = json.dumps(data, ensure_ascii=False)
            existing_data.append(new_record)
            
            # 如果记录数超过限制，创建新文件
            if len(existing_data) > MAX_RECORDS_PER_FILE:
                # 保存当前文件（保留前MAX_RECORDS_PER_FILE-1条记录）
                with open(file_path, 'w', encoding='utf-8') as f:
                    for record in existing_data[:-1]:
                        f.write(record + '\n')
                
                # 创建新文件
                global CURRENT_FILE_INDEX
                CURRENT_FILE_INDEX[file_type] += 1
                file_path = os.path.join(base_dir, f"{file_type}_{CURRENT_FILE_INDEX[file_type]}.json")
                
                # 写入最后一条记录到新文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(existing_data[-1] + '\n')
            else:
                # 写入所有数据
                with open(file_path, 'w', encoding='utf-8') as f:
                    for record in existing_data:
                        f.write(record + '\n')
            
            # 成功写入，跳出循环
            break
                        
        except Exception as e:
            logger.error(f"写入文件失败 {file_path} (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                logger.error(f"写入文件 {file_path} 失败，已达到最大重试次数")
            else:
                time.sleep(retry_delay)
        finally:
            # 清理锁文件
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except:
                    pass

def read_from_files(file_type: str, limit: int = None) -> List[Dict[str, Any]]:
    """从文件中读取数据，支持分片文件"""
    results = []
    file_index = 0
    
    while True:
        file_path = os.path.join(DATA_DIR, f"{file_type}_{file_index}.json")
        
        if not os.path.exists(file_path):
            break
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        results.append(json.loads(line.strip()))
                        
                        # 如果达到限制，返回结果
                        if limit and len(results) >= limit:
                            return results
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
        
        file_index += 1
    
    return results

# MongoDB连接
mongo_client = None
articles_collection = None
tasks_collection = None
workers_collection = None

# 初始化MongoDB连接
def init_mongodb():
    """初始化MongoDB连接"""
    global mongo_client, articles_collection, tasks_collection, workers_collection
    
    try:
        # 检查MongoDB服务是否可用
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((MONGO_HOST, MONGO_PORT))
        sock.close()
        
        if result != 0:
            logger.warning(f"MongoDB服务不可达: {MONGO_HOST}:{MONGO_PORT}，将使用文件存储方案")
            return False
        
        # 构建MongoDB连接URI
        if MONGO_USERNAME and MONGO_PASSWORD:
            mongo_uri = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}?authSource=admin&connectTimeoutMS=10000&socketTimeoutMS=30000&serverSelectionTimeoutMS=10000"
        else:
            mongo_uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}?connectTimeoutMS=10000&socketTimeoutMS=30000&serverSelectionTimeoutMS=10000"
        
        # 连接MongoDB - 增加连接参数优化
        mongo_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=10000,  # 增加服务器选择超时
            connectTimeoutMS=10000,          # 增加连接超时
            socketTimeoutMS=30000,           # 增加套接字超时
            maxPoolSize=50,                  # 增加连接池大小
            minPoolSize=5,                   # 最小连接池大小
            maxIdleTimeMS=300000,            # 最大空闲时间（5分钟）
            retryWrites=True,                # 启用重试写入
            retryReads=True                  # 启用重试读取
        )
        
        # 测试连接
        mongo_client.admin.command('ping')
        
        # 获取数据库和集合
        db = mongo_client[MONGO_DATABASE]
        articles_collection = db['articles']
        tasks_collection = db['tasks']
        workers_collection = db['worker_status']
        
        logger.info(f"MongoDB连接成功: {MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}")
        
        # 启动MongoDB连接状态监控
        start_mongodb_monitoring()
        
        return True
        
    except Exception as e:
        logger.warning(f"MongoDB连接失败: {e}，将使用文件存储方案")
        logger.info("提示: 如需使用MongoDB，请确保MongoDB服务已启动并配置正确")
        logger.info("启动MongoDB命令: mongod --dbpath /path/to/data --port 27017")
        articles_collection = None
        tasks_collection = None
        workers_collection = None
        return False

# 初始化MongoDB
mongodb_enabled = init_mongodb()
if mongodb_enabled:
    logger.info("MongoDB数据存储已启用")
else:
    logger.info("使用文件存储方案")

class DistributedMaster:
    def __init__(self):
        self.task_queue = "crawler_tasks"
        self.result_queue = "crawler_results"
        self.worker_status_key = "worker_status"
        self.task_counter = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        
        # 任务分发统计
        self.task_distribution_stats = {
            'total_distributed': 0,
            'by_priority': {'high': 0, 'medium': 0, 'low': 0},
            'by_worker': {},
            'failed_retries': 0
        }
        
        # 错误处理器
        self.error_handler = error_handler
        
        # 创建索引
        if articles_collection:
            articles_collection.create_index([("url", pymongo.ASCENDING)], unique=True)
            articles_collection.create_index([("keyword", pymongo.ASCENDING)])
            articles_collection.create_index([("year", pymongo.ASCENDING)])
            articles_collection.create_index([("crawled_at", pymongo.DESCENDING)])
    
    def load_keywords(self) -> List[Dict[str, Any]]:
        """加载关键词配置"""
        try:
            with open('china_imagination_keywords.json', 'r', encoding='utf-8') as f:
                keywords_data = json.load(f)
            
            tasks = []
            
            # 遍历所有包含关键词列表的类别
            keyword_categories = [
                'primary_keywords', 'economic_framework', 'geopolitical_narratives', 
                'cultural_social_representations'
            ]
            
            for category in keyword_categories:
                if category in keywords_data:
                    category_data = keywords_data[category]
                    
                    # 处理嵌套的字典结构（如economic_framework包含多个子类别）
                    if isinstance(category_data, dict):
                        for subcategory, keywords in category_data.items():
                            if isinstance(keywords, list):
                                for keyword in keywords:
                                    for year in range(2010, 2026):
                                        task = {
                                            'task_id': str(uuid.uuid4()),
                                            'keyword': keyword,
                                            'category': f"{category}.{subcategory}",
                                            'year': year,
                                            'status': 'pending',
                                            'created_at': datetime.now().isoformat(),
                                            'priority': 1
                                        }
                                        tasks.append(task)
                    # 处理直接的列表结构（如primary_keywords）
                    elif isinstance(category_data, list):
                        for keyword in category_data:
                            for year in range(2010, 2026):
                                task = {
                                    'task_id': str(uuid.uuid4()),
                                    'keyword': keyword,
                                    'category': category,
                                    'year': year,
                                    'status': 'pending',
                                    'created_at': datetime.now().isoformat(),
                                    'priority': 1
                                }
                                tasks.append(task)
            
            logger.info(f"加载了 {len(tasks)} 个爬虫任务")
            return tasks
        except Exception as e:
            logger.error(f"加载关键词失败: {e}")
            # 返回默认任务
            return [{
                'task_id': str(uuid.uuid4()),
                'keyword': 'china africa cooperation',
                'category': 'default',
                'year': 2020,
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'priority': 1
            }]
    
    def submit_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提交爬虫任务（使用智能分发）"""
        try:
            submitted_count = 0
            
            # 批量处理任务以提高性能
            batch_size = 1000  # 每批处理1000个任务
            
            # 批量计算优先级
            priority_batches = {}
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i+batch_size]
                
                # 批量添加任务到队列
                for task in batch:
                    # 计算任务优先级
                    priority = self.calculate_task_priority(task['keyword'])
                    
                    # 使用智能分发添加任务到队列
                    self.add_task_to_queue(task, priority)
                    
                    submitted_count += 1
                    self.task_counter += 1
                    
                    # 更新分发统计
                    self.task_distribution_stats['total_distributed'] += 1
                    self.task_distribution_stats['by_priority'][priority] += 1
                
                # 批量存储到MongoDB（如果启用）
                if tasks_collection:
                    try:
                        # 批量插入任务
                        batch_to_insert = []
                        for task in batch:
                            priority = self.calculate_task_priority(task['keyword'])
                            # 检查任务是否已存在
                            existing_task = tasks_collection.find_one({'task_id': task['task_id']})
                            if not existing_task:
                                task['priority'] = priority
                                batch_to_insert.append(task)
                        
                        if batch_to_insert:
                            tasks_collection.insert_many(batch_to_insert, ordered=False)
                    except Exception as e:
                        logger.warning(f"MongoDB批量任务存储失败: {e}")
                
                # 批量存储到文件（备用方案）
                write_to_file('tasks', batch)
                
                logger.info(f"已处理 {min(i+batch_size, len(tasks))}/{len(tasks)} 个任务")
            
            logger.info(f"成功提交 {submitted_count} 个任务（优先级分布: {self.task_distribution_stats['by_priority']}）")
            return {
                "status": "success",
                "submitted_count": submitted_count,
                "total_tasks": self.task_counter,
                "priority_distribution": self.task_distribution_stats['by_priority']
            }
        except Exception as e:
            logger.error(f"提交任务失败: {e}")
            raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        try:
            # 直接访问全局队列变量
            global task_queue, results_queue, worker_loads
            
            pending_tasks = task_queue.qsize()
            completed_results = results_queue.qsize()
            
            # 获取活跃工作节点（基于worker_loads字典）
            active_workers = len(worker_loads)
            
            return {
                'pending_tasks': pending_tasks,
                'completed_results': completed_results,
                'active_workers': active_workers,
                'total_submitted': self.task_counter,
                'completed_tasks': self.completed_tasks,
                'failed_tasks': self.failed_tasks,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取队列状态失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取队列状态失败: {str(e)}")

    def get_mongodb_stats(self) -> Dict[str, Any]:
        """获取MongoDB统计信息"""
        try:
            if articles_collection:
                total_articles = articles_collection.count_documents({})
                
                # 按年份统计
                year_stats = []
                try:
                    year_stats = list(articles_collection.aggregate([
                        {"$group": {"_id": "$year", "count": {"$sum": 1}}},
                        {"$sort": {"_id": 1}}
                    ]))
                except Exception as e:
                    logger.warning(f"年份统计失败: {e}")
                
                # 按关键词统计
                keyword_stats = []
                try:
                    keyword_stats = list(articles_collection.aggregate([
                        {"$group": {"_id": "$keyword", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 10}
                    ]))
                except Exception as e:
                    logger.warning(f"关键词统计失败: {e}")
                
                return {
                    'total_articles': total_articles,
                    'year_stats': year_stats,
                    'top_keywords': keyword_stats,
                    'mongodb_enabled': True
                }
            else:
                return {
                    'total_articles': 0,
                    'year_stats': [],
                    'top_keywords': [],
                    'mongodb_enabled': False
                }
        except Exception as e:
            logger.error(f"获取MongoDB统计信息失败: {e}")
            return {
                'total_articles': 0,
                'year_stats': [],
                'top_keywords': [],
                'mongodb_enabled': False,
                'error': str(e)
            }
    
    def update_worker_load(self, worker_id: str, task_count: int = 1) -> None:
        """更新工作节点负载"""
        try:
            if worker_id not in worker_loads:
                worker_loads[worker_id] = 0
            
            # 更新负载（支持增加和减少负载）
            worker_loads[worker_id] += task_count
            
            # 确保负载不会为负数
            if worker_loads[worker_id] < 0:
                worker_loads[worker_id] = 0
                
            worker_last_active[worker_id] = datetime.now()
            
            # 清理长时间不活跃的工作节点
            current_time = datetime.now()
            inactive_workers = []
            for wid, last_active in worker_last_active.items():
                # 处理不同类型的时间戳（datetime对象或float时间戳）
                if isinstance(last_active, datetime):
                    time_diff = (current_time - last_active).total_seconds()
                else:
                    # 如果是float时间戳，转换为datetime对象再计算
                    last_active_dt = datetime.fromtimestamp(last_active)
                    time_diff = (current_time - last_active_dt).total_seconds()
                
                if time_diff > 300:  # 5分钟不活跃
                    inactive_workers.append(wid)
            
            for wid in inactive_workers:
                if wid in worker_loads:
                    del worker_loads[wid]
                if wid in worker_last_active:
                    del worker_last_active[wid]
                    
        except Exception as e:
            logger.warning(f"更新工作节点负载失败: {e}")
    
    def get_least_loaded_worker(self) -> str:
        """获取负载最低的工作节点"""
        try:
            if not worker_loads:
                return "worker-1"  # 默认返回第一个工作节点
            
            # 找到负载最低的工作节点
            min_load = min(worker_loads.values())
            least_loaded = [wid for wid, load in worker_loads.items() if load == min_load]
            
            # 如果有多个负载相同的工作节点，随机选择一个
            import random
            return random.choice(least_loaded)
            
        except Exception as e:
            logger.warning(f"获取负载最低工作节点失败: {e}")
            return "worker-1"
    
    def calculate_task_priority(self, keyword: str) -> str:
        """计算任务优先级"""
        try:
            # 根据关键词长度、重要性等因素计算优先级
            priority_keywords = ['非洲', '中国', '一带一路', '投资', '经济']
            
            if any(priority in keyword for priority in priority_keywords):
                return 'high'
            elif len(keyword) <= 5:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.warning(f"计算任务优先级失败: {e}")
            return 'medium'
    
    def add_task_to_queue(self, task: Dict[str, Any], priority: str = 'medium') -> None:
        """添加任务到队列（带智能优先级）"""
        try:
            # 使用智能调度器计算任务优先级
            intelligent_priority = scheduler.calculate_task_priority(task)
            
            # 将智能优先级映射到系统优先级
            priority_mapping = {
                TaskPriority.CRITICAL: 'high',
                TaskPriority.HIGH: 'high',
                TaskPriority.MEDIUM: 'medium',
                TaskPriority.LOW: 'low',
                TaskPriority.BACKGROUND: 'low'
            }
            
            final_priority = priority_mapping.get(intelligent_priority, priority)
            
            # 添加优先级信息
            task['priority'] = final_priority
            task['priority_weight'] = TASK_PRIORITY_WEIGHTS.get(final_priority, 1)
            task['intelligent_priority'] = intelligent_priority.name
            task['priority_score'] = intelligent_priority.value
            task['created_at'] = datetime.now().isoformat()
            task['attempts'] = 0  # 重试次数
            
            # 根据优先级权重决定插入位置
            if final_priority == 'high':
                # 高优先级任务直接插入队列前端
                # 由于Queue不支持直接插入，我们使用临时队列重新排列
                temp_queue = Queue()
                temp_queue.put(task)
                
                # 将原队列中的任务重新放入
                while not task_queue.empty():
                    temp_queue.put(task_queue.get())
                
                # 将临时队列内容放回原队列
                while not temp_queue.empty():
                    task_queue.put(temp_queue.get())
            else:
                # 中低优先级任务正常放入队列
                task_queue.put(task)
                
            logger.debug(f"任务添加到队列: {task['keyword']} (系统优先级: {final_priority}, 智能优先级: {intelligent_priority.name})")
            
            # 更新调度统计
            scheduler.scheduling_metrics['total_tasks_scheduled'] += 1
            scheduler.scheduling_metrics['successful_schedules'] += 1
            
        except Exception as e:
            logger.error(f"添加任务到队列失败: {e}")
            scheduler.scheduling_metrics['failed_schedules'] += 1
            raise
    
    def process_results(self) -> List[Dict[str, Any]]:
        """处理爬取结果（包含智能失败重试机制）"""
        try:
            results = []
            
            # 从结果队列获取所有结果
            while not results_queue.empty():
                result = results_queue.get()
                results.append(result)
                
                # 更新任务状态
                if result['status'] == 'completed':
                    self.completed_tasks += 1
                    
                    # 存储文章数据到MongoDB（如果启用）
                    if 'articles' in result and articles_collection:
                        try:
                            for article in result['articles']:
                                # 检查文章是否已存在
                                existing_article = articles_collection.find_one({'url': article.get('url')})
                                if not existing_article:
                                    # 添加唯一标识和时间戳
                                    article['article_id'] = str(uuid.uuid4())
                                    article['crawled_at'] = datetime.now().isoformat()
                                    articles_collection.insert_one(article)
                                    logger.debug(f"文章存储到MongoDB: {article.get('title', 'Unknown')}")
                                else:
                                    logger.debug(f"文章已存在，跳过存储: {article.get('title', 'Unknown')}")
                        except Exception as e:
                            logger.warning(f"MongoDB文章存储失败: {e}")
                            self.error_handler.record_error(e, result.get('task_id', 'unknown'))
                    
                    # 存储文章数据到文件（备用方案）
                    if 'articles' in result:
                        for article in result['articles']:
                            try:
                                write_to_file('articles', article)
                            except Exception as e:
                                logger.error(f"存储文章到文件失败: {e}")
                                self.error_handler.record_error(e, result.get('task_id', 'unknown'))
                elif result['status'] == 'failed':
                    self.failed_tasks += 1
                    
                    # 智能失败任务重试逻辑
                    if 'task' in result and result['task']:
                        task = result['task']
                        
                        # 记录错误信息
                        if 'error' in result:
                            error_info = result['error']
                            task['last_error'] = error_info
                            
                            # 记录错误统计
                            if isinstance(error_info, Exception):
                                self.error_handler.record_error(error_info, task.get('task_id', 'unknown'))
                        
                        # 使用智能调度器进行错误分类和重试决策
                        retry_count = task.get('attempts', 0)
                        error_type = 'unknown_error'
                        if 'error' in result:
                            error_info = result['error']
                            if isinstance(error_info, Exception):
                                # 使用智能调度器的错误分类
                                error_type = classify_error(error_info)
                        
                        # 智能重试决策
                        should_retry = scheduler.should_retry_task(task, error_type, retry_count)
                        
                        if should_retry:
                            # 计算智能重试延迟
                            retry_delay = scheduler.calculate_retry_delay(error_type, retry_count)
                            
                            # 添加到重试队列
                            task['attempts'] = retry_count + 1
                            task['error_type'] = error_type
                            task['retry_delay'] = retry_delay
                            task['retry_at'] = (datetime.now() + timedelta(seconds=retry_delay)).isoformat()
                            
                            failed_tasks_queue.put(task)
                            logger.info(f"智能重试任务: {task['keyword']} (第{task.get('attempts', 0)}次重试, 错误类型: {error_type}, 延迟: {retry_delay}秒)")
                            self.task_distribution_stats['failed_retries'] += 1
                            
                            # 更新智能调度器统计
                            scheduler.scheduling_metrics['smart_retries'] += 1
                        else:
                            logger.warning(f"任务不适合重试，放弃: {task['keyword']} (错误类型: {error_type}, 重试次数: {retry_count})")
                            
                            # 更新智能调度器统计
                            scheduler.scheduling_metrics['abandoned_tasks'] += 1
            
            logger.info(f"处理了 {len(results)} 个结果（成功: {self.completed_tasks}, 失败: {self.failed_tasks}, 智能重试: {self.task_distribution_stats['failed_retries']}）")
            return results
        except Exception as e:
            logger.error(f"处理结果失败: {e}")
            self.error_handler.record_error(e, 'process_results')
            return []

# 创建主节点实例
master = DistributedMaster()

# API路由
@app.get("/")
async def root():
    return {"message": "分布式爬虫主节点服务运行中", "version": "1.0.0"}

@app.post("/submit-tasks")
async def submit_tasks(task: Dict[str, Any]):
    """提交爬虫任务"""
    try:
        # 为任务生成唯一ID
        task_id = f"task_{int(time.time() * 1000)}_{hash(task['keyword']) % 10000}"
        task['task_id'] = task_id
        
        # 计算智能优先级
        intelligent_priority = scheduler.calculate_task_priority(task)
        task['intelligent_priority'] = intelligent_priority.name
        
        # 计算系统优先级
        priority = master.calculate_task_priority(task['keyword'])
        task['priority'] = priority
        
        # 添加任务到队列
        master.add_task_to_queue(task, priority)
        
        # 存储任务到文件（备用方案）
        write_to_file('tasks', task)
        
        # 更新分发统计
        master.task_distribution_stats['total_distributed'] += 1
        master.task_distribution_stats['by_priority'][priority] += 1
        
        logger.info(f"成功提交任务: {task['keyword']} (任务ID: {task_id}, 智能优先级: {intelligent_priority.name})")
        
        return {
            "status": "success",
            "task_id": task_id,
            "intelligent_priority": intelligent_priority.name,
            "message": "任务提交成功"
        }
    except Exception as e:
        logger.error(f"提交任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")

@app.get("/queue-status")
async def get_queue_status():
    """获取队列状态"""
    return master.get_queue_status()

@app.get("/tasks/next")
async def get_next_task(worker_id: str = "unknown"):
    """获取下一个任务（带智能负载均衡）"""
    start_time = time.time()
    try:
        # 声明全局变量
        global worker_loads
        
        # 首先检查失败任务重试队列
        if not failed_tasks_queue.empty():
            task = failed_tasks_queue.get()
            task['attempts'] += 1
            task['retry_at'] = datetime.now().isoformat()
            logger.info(f"重试失败任务: {task['keyword']} (第{task['attempts']}次重试)")
            
            # 更新工作节点负载
            master.update_worker_load(worker_id, 1)
            
            # 更新分发统计
            if worker_id not in master.task_distribution_stats['by_worker']:
                master.task_distribution_stats['by_worker'][worker_id] = 0
            master.task_distribution_stats['by_worker'][worker_id] += 1
            
            # 记录性能指标
            response_time = time.time() - start_time
            performance_monitor.collect_metrics(
                queue_size=task_queue.qsize(),
                active_workers=len(worker_loads),
                tasks_processed=1,
                tasks_failed=0,
                response_time=response_time
            )
            
            return {"task": task, "status": "retry_task"}
        
        # 从内存队列获取任务（带智能负载均衡）
        if not task_queue.empty():
            # 获取所有活跃的工作节点
            active_workers = list(worker_loads.keys())
            
            # 使用智能调度器选择最佳工作节点
            if len(active_workers) > 1:
                # 模拟获取任务信息（实际需要查看队列中的任务）
                # 这里我们使用临时队列来查看下一个任务
                temp_queue = Queue()
                next_task = None
                
                if not task_queue.empty():
                    next_task = task_queue.get()
                    temp_queue.put(next_task)
                
                # 将其他任务放回临时队列
                while not task_queue.empty():
                    temp_queue.put(task_queue.get())
                
                # 将任务放回原队列
                while not temp_queue.empty():
                    task_queue.put(temp_queue.get())
                
                if next_task:
                    # 使用智能调度器选择最佳工作节点（基于负载均衡）
                    best_worker = scheduler.select_best_worker(next_task, active_workers, worker_loads)
                    
                    # 如果当前工作节点不是最佳选择，返回空任务让工作节点稍后重试
                    if best_worker != worker_id:
                        logger.debug(f"工作节点 {worker_id} 不是最佳选择，最佳节点是 {best_worker} (负载: {worker_loads.get(best_worker, 0)})")
                        
                        # 记录性能指标（无任务分发）
                        response_time = time.time() - start_time
                        performance_monitor.collect_metrics(
                            queue_size=task_queue.qsize(),
                            active_workers=len(worker_loads),
                            tasks_processed=0,
                            tasks_failed=0,
                            response_time=response_time
                        )
                        
                        return {"task": None, "status": "no_tasks", "suggestion": f"最佳节点: {best_worker}"}
            
            # 获取任务
            task = task_queue.get()
            
            # 更新工作节点负载
            master.update_worker_load(worker_id)
            
            # 更新分发统计
            if worker_id not in master.task_distribution_stats['by_worker']:
                master.task_distribution_stats['by_worker'][worker_id] = 0
            master.task_distribution_stats['by_worker'][worker_id] += 1
            
            logger.debug(f"智能分发任务给 {worker_id}: {task['keyword']} (系统优先级: {task.get('priority', 'medium')}, 智能优先级: {task.get('intelligent_priority', 'MEDIUM')})")
            
            # 记录性能指标
            response_time = time.time() - start_time
            performance_monitor.collect_metrics(
                queue_size=task_queue.qsize(),
                active_workers=len(worker_loads),
                tasks_processed=1,
                tasks_failed=0,
                response_time=response_time
            )
            
            return {"task": task, "status": "success"}
        else:
            # 记录性能指标（无任务）
            response_time = time.time() - start_time
            performance_monitor.collect_metrics(
                queue_size=task_queue.qsize(),
                active_workers=len(worker_loads),
                tasks_processed=0,
                tasks_failed=0,
                response_time=response_time
            )
            
            return {"task": None, "status": "no_tasks"}
    except Exception as e:
        # 记录性能指标（错误）
        response_time = time.time() - start_time
        performance_monitor.collect_metrics(
            queue_size=task_queue.qsize(),
            active_workers=len(worker_loads),
            tasks_processed=0,
            tasks_failed=1,
            response_time=response_time
        )
        
        logger.error(f"获取任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务失败: {e}")

@app.post("/results/submit")
async def submit_result(result: Dict[str, Any]):
    """提交爬取结果"""
    try:
        # 将结果放入结果队列
        results_queue.put(result)
        
        # 存储结果到文件（备用方案）
        write_to_file('results', result)
        
        # 任务完成后减少工作节点负载
        worker_id = result.get('worker_id')
        if worker_id:
            # 减少工作节点负载（任务完成）
            master.update_worker_load(worker_id, -1)
            logger.debug(f"工作节点 {worker_id} 负载减少，当前负载: {worker_loads.get(worker_id, 0)}")
        
        return {"status": "success", "message": "结果提交成功"}
    except Exception as e:
        logger.error(f"提交结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交结果失败: {e}")

@app.post("/workers/heartbeat")
async def worker_heartbeat(worker_info: Dict[str, Any]):
    """工作节点心跳"""
    try:
        worker_id = worker_info['worker_id']
        
        # 更新工作节点负载和最后活动时间
        global worker_loads, worker_last_active
        
        # 从心跳数据中获取负载信息，如果没有则默认为0
        current_load = worker_info.get('current_load', 0)
        
        # 更新工作节点负载
        worker_loads[worker_id] = current_load
        worker_last_active[worker_id] = time.time()
        
        # 记录工作节点状态到文件
        write_to_file('workers', worker_info)
        
        # 添加调试日志，确认worker_loads的更新
        logger.info(f"工作节点 {worker_id} 心跳更新，当前负载: {current_load}, worker_loads大小: {len(worker_loads)}")
        logger.info(f"当前worker_loads内容: {worker_loads}")
        
        return {"status": "success", "message": "心跳接收成功"}
    except Exception as e:
        logger.error(f"处理工作节点心跳失败: {e}")
        raise HTTPException(status_code=500, detail=f"心跳处理失败: {e}")

@app.get("/process-results")
async def process_results():
    """处理爬取结果"""
    results = master.process_results()
    return {"processed_results": len(results), "results": results}

@app.get("/stats")
async def get_stats():
    """获取系统统计信息"""
    try:
        # 获取队列状态
        queue_stats = {
            "task_queue_size": task_queue.qsize(),
            "failed_tasks_queue_size": failed_tasks_queue.qsize(),
            "results_queue_size": results_queue.qsize()
        }
        
        # 获取任务分发统计
        task_stats = master.task_distribution_stats
        
        # 获取工作节点负载
        worker_stats = {
            "total_workers": len(worker_loads),
            "worker_loads": dict(worker_loads)
        }
        
        # 添加调试日志，确认worker_loads的状态
        logger.info(f"统计接口调用 - worker_loads大小: {len(worker_loads)}, 内容: {worker_loads}")
        
        # 获取失败任务队列大小
        failed_stats = {
            "failed_tasks_count": failed_tasks_queue.qsize()
        }
        
        # 获取错误统计
        error_stats = error_handler.get_error_stats()
        
        # 获取数据库统计
        db_stats = master.get_mongodb_stats()
        
        # 获取性能监控统计
        performance_stats = performance_monitor.get_performance_summary()
        
        return {
            "queue_stats": queue_stats,
            "task_stats": task_stats,
            "worker_stats": worker_stats,
            "failed_stats": failed_stats,
            "error_stats": error_stats,
            "db_stats": db_stats,
            "performance_stats": performance_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        # 添加详细的调试信息
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {e}")

@app.get("/performance")
async def get_performance_metrics():
    """获取详细的性能监控指标"""
    try:
        metrics = performance_monitor.get_metrics()
        summary = performance_monitor.get_performance_summary()
        
        # 获取告警状态（从summary中提取）
        alerts = summary.get('alerts', {})
        
        return {
            "metrics": metrics.__dict__ if metrics else None,
            "summary": summary,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {e}")

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查内存队列状态
        queue_size = task_queue.qsize()
        
        # 检查数据目录
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        # 获取工作节点数量
        active_workers = len(worker_loads)
        
        return {
            "status": "healthy", 
            "queue_size": queue_size, 
            "active_workers": active_workers,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务异常: {str(e)}")

# MongoDB连接状态监控
mongodb_monitoring_thread = None
mongodb_connection_status = {
    'connected': False,
    'last_check': None,
    'error_count': 0,
    'last_error': None,
    'reconnect_attempts': 0,
    'last_success': None,
    'connection_quality': 'unknown',  # poor, fair, good, excellent
    'response_time_ms': 0
}

def check_mongodb_connection():
    """检查MongoDB连接状态"""
    global mongodb_connection_status
    
    try:
        if mongo_client:
            # 测试连接并测量响应时间
            start_time = time.time()
            mongo_client.admin.command('ping')
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 评估连接质量
            if response_time < 100:
                quality = 'excellent'
            elif response_time < 500:
                quality = 'good'
            elif response_time < 2000:
                quality = 'fair'
            else:
                quality = 'poor'
            
            mongodb_connection_status = {
                'connected': True,
                'last_check': datetime.now().isoformat(),
                'error_count': 0,
                'last_error': None,
                'reconnect_attempts': 0,
                'last_success': datetime.now().isoformat(),
                'connection_quality': quality,
                'response_time_ms': round(response_time, 2)
            }
            logger.debug(f"MongoDB连接状态检查: 正常 (响应时间: {response_time:.2f}ms, 质量: {quality})")
        else:
            mongodb_connection_status = {
                'connected': False,
                'last_check': datetime.now().isoformat(),
                'error_count': mongodb_connection_status['error_count'],
                'last_error': 'MongoDB客户端未初始化',
                'reconnect_attempts': mongodb_connection_status['reconnect_attempts'],
                'last_success': mongodb_connection_status['last_success'],
                'connection_quality': 'unknown',
                'response_time_ms': 0
            }
            logger.debug("MongoDB连接状态检查: 未初始化")
    except Exception as e:
        mongodb_connection_status = {
            'connected': False,
            'last_check': datetime.now().isoformat(),
            'error_count': mongodb_connection_status['error_count'] + 1,
            'last_error': str(e),
            'reconnect_attempts': mongodb_connection_status['reconnect_attempts'],
            'last_success': mongodb_connection_status['last_success'],
            'connection_quality': 'poor',
            'response_time_ms': 0
        }
        
        # 如果连续失败3次，尝试重新连接
        if mongodb_connection_status['error_count'] >= 3:
            logger.warning("MongoDB连接连续失败，尝试重新连接...")
            try:
                init_mongodb()
                mongodb_connection_status['reconnect_attempts'] += 1
            except Exception as reconnect_error:
                logger.error(f"MongoDB重连失败: {reconnect_error}")
        
        logger.warning(f"MongoDB连接状态检查失败: {e}")

def mongodb_monitoring_worker():
    """MongoDB连接监控工作线程"""
    check_interval = 60  # 默认检查间隔
    
    while True:
        try:
            check_mongodb_connection()
            
            # 根据连接质量动态调整检查间隔
            if mongodb_connection_status['connection_quality'] == 'excellent':
                check_interval = 120  # 2分钟
            elif mongodb_connection_status['connection_quality'] == 'good':
                check_interval = 90   # 1.5分钟
            elif mongodb_connection_status['connection_quality'] == 'fair':
                check_interval = 60   # 1分钟
            else:
                check_interval = 30   # 30秒
                
            time.sleep(check_interval)
        except Exception as e:
            logger.error(f"MongoDB监控线程异常: {e}")
            time.sleep(60)

def start_mongodb_monitoring():
    """启动MongoDB连接状态监控"""
    global mongodb_monitoring_thread
    
    if mongodb_monitoring_thread and mongodb_monitoring_thread.is_alive():
        logger.info("MongoDB监控线程已在运行")
        return
    
    mongodb_monitoring_thread = threading.Thread(
        target=mongodb_monitoring_worker,
        name="MongoDB-Monitoring",
        daemon=True
    )
    mongodb_monitoring_thread.start()
    logger.info("MongoDB连接状态监控已启动（智能间隔调整）")

@app.get("/mongodb-status")
async def get_mongodb_status():
    """获取MongoDB连接状态"""
    return {
        "mongodb_enabled": mongo_client is not None,
        "connection_status": mongodb_connection_status,
        "collections": {
            "articles": articles_collection is not None,
            "tasks": tasks_collection is not None,
            "workers": workers_collection is not None
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    import threading
    
    logger.info("启动分布式爬虫主节点服务...")
    
    def start_api_server():
        """启动API服务的线程函数"""
        try:
            # 启动API服务 - 优化连接参数
            uvicorn.run(
                app, 
                host="0.0.0.0", 
                port=8000, 
                log_level="info",
                # 连接优化参数 - 大幅提升并发处理能力
                timeout_keep_alive=600,  # 延长保持连接超时时间到10分钟
                # 性能优化参数
                workers=1,                # 单进程模式（避免多进程同步问题）
                loop="asyncio",           # 使用asyncio事件循环
                http="auto"              # 自动选择HTTP协议实现
            )
        except Exception as e:
            logger.error(f"API服务启动失败: {e}")
    
    def load_tasks_async():
        """异步加载任务的线程函数"""
        try:
            # 加载初始任务
            tasks = master.load_keywords()
            logger.info(f"已加载 {len(tasks)} 个爬虫任务")
            
            # 加载现有任务文件中的任务到内存队列
            existing_tasks = load_tasks_from_files()
            logger.info(f"从文件加载了 {len(existing_tasks)} 个现有任务")
            
            # 将所有任务添加到队列
            all_tasks = tasks + existing_tasks
            if all_tasks:
                master.submit_tasks(all_tasks)
                logger.info(f"总共 {len(all_tasks)} 个任务已添加到队列")
        except Exception as e:
            logger.error(f"任务加载失败: {e}")
    
    # 先启动API服务线程
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    
    # 等待API服务启动（给服务器一些时间启动）
    import time
    time.sleep(3)
    
    # 然后异步加载任务
    task_thread = threading.Thread(target=load_tasks_async, daemon=True)
    task_thread.start()
    
    # 主线程等待API服务线程（任务线程会在后台运行）
    api_thread.join()