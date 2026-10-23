#!/usr/bin/env python3
"""
分布式爬虫系统 - 修复版主节点
专门解决Windows网络连接问题（WinError 64）
集成智能任务调度器
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
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

# 智能调度器
from task_scheduler_optimizer import IntelligentTaskScheduler, TaskPriority

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('distributed_master_fixed.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="分布式爬虫主节点（修复版）", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置 - 优化网络连接设置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'password123')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'crawler_db')

# 网络连接优化配置
CONNECTION_TIMEOUT = 30  # 连接超时时间（秒）
REQUEST_TIMEOUT = 60     # 请求超时时间（秒）
RETRY_DELAY_BASE = 5     # 重试延迟基础时间（秒）
MAX_RETRIES = 5          # 最大重试次数

# 主机绑定配置 - 解决Windows网络连接问题
HOST = "0.0.0.0"         # 绑定所有网络接口
MASTER_PORT = 8000       # 主节点端口
WORKER_PORT = 5000       # 工作节点端口

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
    
    def log_event(self, event_type: str, event_data: Dict[str, Any]):
        """记录系统事件"""
        try:
            event_log = {
                'event_type': event_type,
                'event_data': event_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # 写入事件日志文件
            write_to_file('events', event_log)
            
            logger.info(f"系统事件记录 - 类型: {event_type}, 数据: {event_data}")
        except Exception as e:
            logger.error(f"记录系统事件失败: {e}")

# 创建全局错误处理器
error_handler = ErrorHandler()

# 数据存储配置 - 统一数据目录路径
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 创建子目录用于分类存储
RESULTS_DIR = os.path.join(DATA_DIR, "results")
TASKS_DIR = os.path.join(DATA_DIR, "tasks") 
WORKERS_DIR = os.path.join(DATA_DIR, "workers")
EVENTS_DIR = os.path.join(DATA_DIR, "events")
BACKUP_DIR = os.path.join(DATA_DIR, "backup")

for dir_path in [RESULTS_DIR, TASKS_DIR, WORKERS_DIR, EVENTS_DIR, BACKUP_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# 文件存储优化参数
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_RECORDS_PER_FILE = 500  # 降低单文件记录数，提高可靠性

# 文件索引管理
CURRENT_FILE_INDEX = {}

def initialize_file_index():
    """初始化文件索引，自动检测现有文件"""
    global CURRENT_FILE_INDEX
    
    file_types = ['tasks', 'articles', 'results', 'workers', 'events']
    
    for file_type in file_types:
        # 根据文件类型选择正确的存储目录
        if file_type == 'results':
            search_dir = RESULTS_DIR
        elif file_type == 'tasks':
            search_dir = TASKS_DIR
        elif file_type == 'workers':
            search_dir = WORKERS_DIR
        elif file_type == 'events':
            search_dir = EVENTS_DIR
        else:
            search_dir = DATA_DIR
        
        # 查找该类型的所有文件
        max_index = -1
        if os.path.exists(search_dir):
            for filename in os.listdir(search_dir):
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
            current_file = os.path.join(search_dir, f"{file_type}_{max_index}.json")
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
    
    # 强制设置results文件索引为8，确保新数据保存到results_8.json
    if 'results' in CURRENT_FILE_INDEX:
        CURRENT_FILE_INDEX['results'] = 8

# 初始化文件索引
initialize_file_index()

def write_to_file(file_type: str, data: Dict[str, Any]):
    """写入数据到文件 - 修复版：支持JSON文件追加模式"""
    try:
        # 数据完整性检查
        if not isinstance(data, dict):
            logger.error(f"数据格式错误，期望字典类型，实际类型: {type(data)}")
            return False
        
        # 根据文件类型检查不同的必需字段
        if file_type == 'results':
            # 结果数据需要任务ID和工作节点ID，status字段由工作节点自动添加
            required_fields = ['task_id', 'worker_id']
        elif file_type == 'tasks':
            # 任务数据需要任务ID和状态
            required_fields = ['task_id', 'status']
        elif file_type == 'workers':
            # 工作节点心跳数据只需要工作节点ID和状态
            required_fields = ['worker_id', 'status']
        else:
            # 其他类型数据使用默认检查
            required_fields = []
        
        # 为结果数据自动添加status字段
        if file_type == 'results' and 'status' not in data:
            data['status'] = 'completed'
        
        # 检查必需字段
        for field in required_fields:
            if field not in data:
                logger.warning(f"数据缺少必需字段: {field}")
        
        # 根据数据类型选择存储目录
        if file_type == 'results':
            storage_dir = RESULTS_DIR
        elif file_type == 'tasks':
            storage_dir = TASKS_DIR
        elif file_type == 'workers':
            storage_dir = WORKERS_DIR
        elif file_type == 'events':
            storage_dir = EVENTS_DIR
        else:
            storage_dir = DATA_DIR
        
        # 获取当前文件索引
        if file_type not in CURRENT_FILE_INDEX:
            CURRENT_FILE_INDEX[file_type] = 0
        
        current_index = CURRENT_FILE_INDEX[file_type]
        filename = os.path.join(storage_dir, f"{file_type}_{current_index}.json")
        
        # 检查文件是否存在且不为空
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            # 读取现有数据
            with open(filename, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        # 如果文件不是列表格式，转换为列表
                        existing_data = [existing_data]
                except json.JSONDecodeError:
                    logger.warning(f"文件 {filename} JSON格式错误，创建新文件")
                    existing_data = []
        else:
            existing_data = []
        
        # 检查数据重复性（基于task_id）
        if 'task_id' in data:
            for existing_item in existing_data:
                if isinstance(existing_item, dict) and 'task_id' in existing_item:
                    if existing_item['task_id'] == data['task_id']:
                        logger.warning(f"检测到重复数据，task_id: {data['task_id']}")
                        # 更新现有数据而不是重复添加
                        existing_data.remove(existing_item)
                        break
        
        # 添加新数据
        existing_data.append(data)
        
        # 检查文件大小和记录数，决定是否需要创建新文件
        if len(existing_data) >= MAX_RECORDS_PER_FILE or (os.path.exists(filename) and os.path.getsize(filename) > MAX_FILE_SIZE):
            # 创建新文件
            CURRENT_FILE_INDEX[file_type] += 1
            filename = os.path.join(storage_dir, f"{file_type}_{CURRENT_FILE_INDEX[file_type]}.json")
            existing_data = [data]  # 新文件只包含当前数据
        
        # 写入文件 - 使用追加模式写入JSON数组
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
        # 创建备份文件
        backup_filename = os.path.join(BACKUP_DIR, f"{file_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"数据已写入文件: {filename}，备份文件: {backup_filename}")
        return True
        
    except Exception as e:
        logger.error(f"写入文件失败: {e}")
        
        # 紧急备份机制
        try:
            emergency_file = os.path.join(BACKUP_DIR, f"emergency_{file_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(emergency_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"紧急备份已保存到: {emergency_file}")
        except Exception as backup_error:
            logger.error(f"紧急备份也失败: {backup_error}")
        
        return False

class Task(BaseModel):
    """任务模型"""
    task_id: str
    keyword: str
    priority: str = "medium"
    created_at: str
    status: str = "pending"

class Worker(BaseModel):
    """工作节点模型"""
    worker_id: str
    status: str = "active"
    last_heartbeat: str
    load: int = 0

class DistributedMaster:
    """分布式主节点管理器"""
    
    def __init__(self):
        self.tasks = []
        self.results = []
        self.workers = {}
        self.task_distribution_stats = {
            'total_distributed': 0,
            'by_priority': {'high': 0, 'medium': 0, 'low': 0},
            'by_worker': {}
        }
        
        # MongoDB连接
        self.mongo_client = None
        self.articles_collection = None
        self.tasks_collection = None
        self.workers_collection = None
        
        # 智能调度器
        self.scheduler = IntelligentTaskScheduler()
        
        self.initialize_mongodb()
    
    def initialize_mongodb(self):
        """初始化MongoDB连接"""
        try:
            # 构建MongoDB连接字符串
            if MONGO_USERNAME and MONGO_PASSWORD:
                mongo_uri = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
            else:
                mongo_uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"
            
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            
            # 测试连接
            self.mongo_client.admin.command('ping')
            
            # 获取数据库和集合
            db = self.mongo_client[MONGO_DATABASE]
            self.articles_collection = db['articles']
            self.tasks_collection = db['tasks']
            self.workers_collection = db['workers']
            
            logger.info("MongoDB连接成功")
            
        except Exception as e:
            logger.warning(f"MongoDB连接失败，将使用文件存储: {e}")
            self.mongo_client = None
    
    def load_keywords(self) -> List[Dict[str, Any]]:
        """加载关键词任务 - 集成中国与非洲关系关键词"""
        
        # 尝试加载中国与非洲关系关键词
        china_africa_tasks = self.load_china_africa_keywords()
        
        # 如果中国与非洲关系关键词加载成功，优先使用它们
        if china_africa_tasks:
            tasks = china_africa_tasks
            logger.info(f"已加载 {len(tasks)} 个中国与非洲关系关键词任务")
        else:
            # 备用关键词列表
            keywords = [
                "人工智能", "机器学习", "深度学习", "自然语言处理", "计算机视觉",
                "大数据", "云计算", "物联网", "区块链", "网络安全",
                "Python编程", "Java开发", "前端开发", "后端开发", "移动开发",
                "数据科学", "数据分析", "数据挖掘", "数据可视化", "统计学",
                "金融科技", "电子商务", "社交媒体", "数字营销", "内容创作"
            ]
            
            tasks = []
            for keyword in keywords:
                task = {
                    "task_id": str(uuid.uuid4()),
                    "keyword": keyword,
                    "priority": "medium",
                    "created_at": datetime.now().isoformat(),
                    "status": "pending"
                }
                tasks.append(task)
            
            logger.info(f"已加载 {len(tasks)} 个默认爬虫任务到队列")
        
        # 按优先级排序任务：high > medium > low
        tasks.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x.get('priority', 'medium'), 1))
        
        # 将任务放入队列（高优先级任务先入队）
        for task in tasks:
            task_queue.put(task)
        
        # 记录优先级分布
        priority_counts = {}
        for task in tasks:
            priority = task.get('priority', 'medium')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        logger.info(f"任务优先级分布: {priority_counts}")
        
        return tasks
    
    def load_china_africa_keywords(self) -> List[Dict[str, Any]]:
        """加载中国与非洲关系关键词"""
        try:
            # 检查关键词文件是否存在
            if not os.path.exists('china_africa_keywords.json'):
                logger.warning("中国与非洲关系关键词文件不存在，使用默认关键词")
                return []
            
            # 加载关键词配置
            with open('china_africa_keywords.json', 'r', encoding='utf-8') as f:
                keywords_data = json.load(f)
            
            tasks = []
            task_id_counter = 1
            
            # 处理中国相关关键词
            china_related = keywords_data['chinese_keywords']['china_related']
            for language, keywords in china_related.items():
                for keyword in keywords:
                    task = {
                        "task_id": f"china_related_{language}_{task_id_counter}",
                        "keyword": keyword,
                        "language": language,
                        "category": "china_related",
                        "priority": "high",
                        "created_at": datetime.now().isoformat(),
                        "status": "pending"
                    }
                    tasks.append(task)
                    task_id_counter += 1
            
            # 处理中国省份关键词
            if 'chinese_provinces' in keywords_data['chinese_keywords']:
                provinces = keywords_data['chinese_keywords']['chinese_provinces']['english']
                for province in provinces:
                    task = {
                        "task_id": f"province_{task_id_counter}",
                        "keyword": province,
                        "language": "english",
                        "category": "chinese_provinces",
                        "priority": "medium",
                        "created_at": datetime.now().isoformat(),
                        "status": "pending"
                    }
                    tasks.append(task)
                    task_id_counter += 1
            
            # 处理搜索分类
            if 'search_categories' in keywords_data['chinese_keywords']:
                categories = keywords_data['chinese_keywords']['search_categories']
                for category_name, keywords in categories.items():
                    for keyword in keywords:
                        task = {
                            "task_id": f"{category_name}_{task_id_counter}",
                            "keyword": keyword,
                            "language": "english",
                            "category": category_name,
                            "priority": "medium",
                            "created_at": datetime.now().isoformat(),
                            "status": "pending"
                        }
                        tasks.append(task)
                        task_id_counter += 1
            
            logger.info(f"成功加载 {len(tasks)} 个中国与非洲关系关键词任务")
            return tasks
            
        except Exception as e:
            logger.error(f"加载中国与非洲关系关键词失败: {e}")
            return []
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            "task_queue_size": task_queue.qsize(),
            "results_queue_size": results_queue.qsize(),
            "failed_tasks_queue_size": failed_tasks_queue.qsize(),
            "active_workers": len([w for w in worker_last_active if time.time() - worker_last_active[w] < 300]),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_mongodb_stats(self) -> Dict[str, Any]:
        """获取MongoDB统计信息"""
        if not self.mongo_client:
            return {"mongodb_enabled": False}
        
        try:
            db = self.mongo_client[MONGO_DATABASE]
            return {
                "mongodb_enabled": True,
                "articles_count": db.articles.count_documents({}),
                "tasks_count": db.tasks.count_documents({}),
                "workers_count": db.workers.count_documents({})
            }
        except Exception as e:
            logger.error(f"获取MongoDB统计失败: {e}")
            return {"mongodb_enabled": False, "error": str(e)}
    
    def process_results(self) -> List[Dict[str, Any]]:
        """处理爬取结果"""
        processed_results = []
        
        while not results_queue.empty():
            try:
                result = results_queue.get()
                
                # 存储到MongoDB（如果可用）
                if self.articles_collection:
                    self.articles_collection.insert_one(result)
                
                # 存储到文件 - 修复：使用正确的文件类型'results'
                write_to_file('results', result)
                
                processed_results.append(result)
                
            except Exception as e:
                logger.error(f"处理结果失败: {e}")
                error_handler.record_error(e)
        
        logger.info(f"已处理 {len(processed_results)} 个爬取结果")
        return processed_results

# 创建主节点实例
master = DistributedMaster()

# API路由
@app.get("/")
async def root():
    return {"message": "分布式爬虫主节点服务运行中（修复版）", "version": "1.0.0"}

@app.post("/submit-tasks")
async def submit_tasks():
    """提交爬虫任务"""
    tasks = master.load_keywords()
    return {"submitted_tasks": len(tasks), "tasks": tasks}

@app.get("/tasks/next")
async def get_next_task(worker_id: str):
    """获取下一个任务（智能调度版本）"""
    try:
        if not task_queue.empty():
            # 获取任务但不立即分配（使用peek方式避免永久移除）
            task = task_queue.get()
            
            # 使用智能调度器计算任务优先级
            priority = master.scheduler.calculate_task_priority(task)
            task['priority'] = priority.name.lower()
            
            # 获取所有活跃工作节点
            active_workers = [w for w in worker_last_active if time.time() - worker_last_active[w] < 300]
            
            # 检查所有工作节点负载是否都为0（初始状态）
            all_zero_load = all(worker_loads.get(w, 0) == 0 for w in active_workers)
            
            if all_zero_load:
                # 如果所有节点负载都为0，直接分配给请求的工作节点，避免死锁
                assigned_worker = worker_id
                logger.debug(f"初始状态：直接分配任务给 {assigned_worker}")
            else:
                # 使用智能调度器选择最佳工作节点
                best_worker = master.scheduler.select_best_worker(task, active_workers, worker_loads)
                
                # 如果智能调度器返回了最佳工作节点，使用它；否则使用请求的工作节点
                assigned_worker = best_worker if best_worker else worker_id
                
                # 记录调度决策
                if best_worker and best_worker != worker_id:
                    logger.info(f"智能调度器优化：将任务从 {worker_id} 重定向到 {best_worker}")
            
            # 如果智能调度器返回None（表示没有合适的工作节点），将任务重新放回队列
            if not assigned_worker:
                task_queue.put(task)
                logger.warning(f"智能调度器返回None，任务 {task['task_id']} 重新放回队列")
                return {"task": None, "status": "no_available_worker"}
            
            task['status'] = 'assigned'
            task['assigned_to'] = assigned_worker
            task['assigned_at'] = datetime.now().isoformat()
            
            # 更新工作节点负载
            if assigned_worker not in worker_loads:
                worker_loads[assigned_worker] = 0
            worker_loads[assigned_worker] += 1
            
            # 更新任务分发统计
            master.task_distribution_stats['total_distributed'] += 1
            master.task_distribution_stats['by_priority'][task['priority']] += 1
            
            if assigned_worker not in master.task_distribution_stats['by_worker']:
                master.task_distribution_stats['by_worker'][assigned_worker] = 0
            master.task_distribution_stats['by_worker'][assigned_worker] += 1
            
            logger.debug(f"智能分发任务给 {assigned_worker}: {task['keyword']} (优先级: {task['priority']})")
            
            return {"task": task, "status": "success"}
        else:
            return {"task": None, "status": "no_tasks"}
    except Exception as e:
        logger.error(f"获取任务失败: {e}")
        # 如果发生异常，确保任务不会丢失
        if 'task' in locals():
            task_queue.put(task)
        raise HTTPException(status_code=500, detail=f"获取任务失败: {e}")

@app.post("/results/submit")
async def submit_result(result: Dict[str, Any]):
    """提交爬取结果"""
    try:
        # 将结果放入结果队列
        results_queue.put(result)
        
        # 存储结果到文件（备用方案）
        write_to_file('results', result)
        
        return {"status": "success", "message": "结果提交成功"}
    except Exception as e:
        logger.error(f"提交结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交结果失败: {e}")

@app.post("/workers/heartbeat")
async def worker_heartbeat(worker_info: Dict[str, Any]):
    """工作节点心跳（包含性能统计）"""
    try:
        worker_id = worker_info['worker_id']
        
        # 更新工作节点负载和最后活动时间
        global worker_loads, worker_last_active
        if worker_id not in worker_loads:
            worker_loads[worker_id] = 0
        worker_last_active[worker_id] = time.time()
        
        # 如果有性能统计信息，更新智能调度器
        if 'stats' in worker_info:
            master.scheduler.update_worker_performance(worker_id, worker_info['stats'])
            logger.debug(f"工作节点 {worker_id} 心跳，更新性能统计")
        
        # 记录工作节点状态到文件
        write_to_file('workers', worker_info)
        
        logger.info(f"工作节点 {worker_id} 心跳更新")
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
    """获取统计信息"""
    queue_status = master.get_queue_status()
    
    # 添加任务分发统计
    queue_status['task_distribution'] = master.task_distribution_stats
    queue_status['worker_loads'] = worker_loads
    queue_status['failed_tasks_queue_size'] = failed_tasks_queue.qsize()
    
    # 添加错误统计
    queue_status['error_stats'] = error_handler.get_error_stats()
    
    # 获取数据库统计
    if master.mongo_client:
        mongodb_stats = master.get_mongodb_stats()
        queue_status.update(mongodb_stats)
    
    return queue_status

@app.get("/health")
async def health_check(request: Request):
    """健康检查 - 支持HTML和JSON响应"""
    try:
        # 检查内存队列状态
        queue_size = task_queue.qsize()
        
        # 检查数据目录
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        # 检查请求头，判断是否请求HTML
        accept_header = request.headers.get("accept", "")
        user_agent = request.headers.get("user-agent", "")
        
        # 检查查询参数，如果指定format=json，强制返回JSON
        format_param = request.query_params.get("format", "")
        if format_param == "json":
            return {"status": "healthy", "queue_size": queue_size, "timestamp": datetime.now().isoformat()}
        
        # 如果是浏览器请求或明确请求HTML，返回HTML页面
        if "text/html" in accept_header or "Mozilla" in user_agent:
            # 读取HTML模板文件
            try:
                with open("templates/health.html", "r", encoding="utf-8") as f:
                    html_content = f.read()
                
                # 替换占位符为实际数据
                html_content = html_content.replace(
                    "{\"status\": \"healthy\", \"queue_size\": 0, \"timestamp\": \"2025-11-20T09:31:26.260350\"}",
                    f'{{"status": "healthy", "queue_size": {queue_size}, "timestamp": "{datetime.now().isoformat()}"}}'
                )
                
                return HTMLResponse(content=html_content)
            except FileNotFoundError:
                # 如果模板文件不存在，返回简单的HTML页面
                simple_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>分布式爬虫系统健康监控</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                        .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .status {{ color: green; font-weight: bold; }}
                        .queue {{ color: blue; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🌐 分布式爬虫系统健康状态</h1>
                        <p><span class="status">状态:</span> 健康 ✓</p>
                        <p><span class="queue">任务队列:</span> {queue_size}</p>
                        <p><span>最后检查:</span> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><a href="/health?format=json">查看JSON格式数据</a></p>
                    </div>
                </body>
                </html>
                """
                return HTMLResponse(content=simple_html)
        
        # 默认返回JSON格式
        return {"status": "healthy", "queue_size": queue_size, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        
        # 如果是HTML请求，返回错误页面
        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header:
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>系统错误</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                    .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .error {{ color: red; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ 系统错误</h1>
                    <p class="error">健康检查失败: {str(e)}</p>
                    <p>请检查系统日志或联系管理员。</p>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=error_html, status_code=500)
        
        raise HTTPException(status_code=500, detail=f"服务异常: {str(e)}")

@app.post("/trigger-test-event")
async def trigger_test_event():
    """手动触发测试事件 - 用于验证事件记录功能"""
    try:
        # 记录测试事件
        error_handler.log_event("TEST_EVENT", {
            "message": "手动触发的测试事件",
            "test_data": {
                "string_field": "测试字符串",
                "number_field": 12345,
                "boolean_field": True,
                "array_field": ["item1", "item2", "item3"],
                "timestamp": datetime.now().isoformat()
            }
        })
        
        return {
            "status": "success", 
            "message": "测试事件已触发并记录",
            "event_type": "TEST_EVENT",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"触发测试事件失败: {e}")
        raise HTTPException(status_code=500, detail=f"触发测试事件失败: {e}")

if __name__ == "__main__":
    import uvicorn
    import asyncio
    
    logger.info("启动分布式爬虫主节点服务（修复版）...")
    
    # 加载初始任务
    tasks = master.load_keywords()
    logger.info(f"已加载 {len(tasks)} 个爬虫任务")
    
    # 创建后台任务检查器
    async def task_queue_monitor():
        """后台任务队列监控器，确保队列不会归零"""
        while True:
            try:
                # 检查当前队列状态
                current_queue_size = task_queue.qsize()
                
                # 如果队列为空或任务数量少于阈值，自动补充任务
                if current_queue_size <= 5:
                    logger.info(f"任务队列即将归零（当前大小: {current_queue_size}），自动补充任务...")
                    
                    # 重新加载任务
                    new_tasks = master.load_keywords()
                    logger.info(f"已自动补充 {len(new_tasks)} 个爬虫任务")
                    
                    # 记录补充任务事件
                    error_handler.log_event("TASK_QUEUE_REPLENISHED", {
                        "previous_size": current_queue_size,
                        "added_tasks": len(new_tasks),
                        "timestamp": datetime.now().isoformat()
                    })
                
                # 每30秒检查一次队列状态
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"任务队列监控器错误: {e}")
                await asyncio.sleep(60)  # 出错时等待更长时间
    
    # 启动后台监控任务
    async def main():
        # 启动任务队列监控器
        monitor_task = asyncio.create_task(task_queue_monitor())
        
        # 配置服务器 - 使用优化的网络设置
        config = uvicorn.Config(
            app, 
            host=HOST,  # 使用优化的主机绑定配置
            port=MASTER_PORT, 
            log_level="info",
            # 网络连接优化参数
            timeout_keep_alive=CONNECTION_TIMEOUT,  # 使用配置的连接超时时间
            limit_max_requests=500,  # 进一步降低最大请求数限制
            limit_concurrency=50,    # 进一步降低并发连接数限制
            backlog=512,             # 减小连接队列大小
            # 性能优化参数
            workers=1,                # 单进程模式（避免多进程同步问题）
            loop="asyncio",           # 使用asyncio事件循环
            http="auto",             # 自动选择HTTP协议实现
            # Windows特定优化
            use_colors=False,         # 禁用颜色输出，减少终端干扰
            access_log=False,         # 禁用访问日志，减少I/O压力
            # 连接池优化
            timeout_graceful_shutdown=30,  # 优雅关闭超时时间
        )
        
        server = uvicorn.Server(config)
        
        try:
            # 启动服务器
            await server.serve()
        finally:
            # 停止监控任务
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
    
    # 运行主程序
    asyncio.run(main())