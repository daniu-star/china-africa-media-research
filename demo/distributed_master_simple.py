"""
分布式爬虫主节点 - 简化版（不使用MongoDB）
专门解决Windows网络连接问题
"""

import asyncio
import logging
import time
import json
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[主节点] %(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="分布式爬虫主节点 - 简化版")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLite数据库配置
DB_PATH = "distributed_crawler.db"

# 全局变量
active_workers: Dict[str, Dict[str, Any]] = {}
task_queue: List[Dict[str, Any]] = []
completed_tasks: List[Dict[str, Any]] = []
worker_lock = threading.Lock()
task_lock = threading.Lock()

class SQLiteManager:
    """SQLite数据库管理器"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                spider_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP NULL,
                completed_at TIMESTAMP NULL,
                result TEXT NULL,
                error TEXT NULL,
                worker_id TEXT NULL
            )
        """)
        
        # 创建工作节点表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workers (
                id TEXT PRIMARY KEY,
                last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                tasks_completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("SQLite数据库初始化完成")
    
    def add_task(self, url: str, spider_name: str) -> int:
        """添加任务到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO tasks (url, spider_name) VALUES (?, ?)",
            (url, spider_name)
        )
        task_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # 同时添加到内存队列
        with task_lock:
            task_queue.append({
                "id": task_id,
                "url": url,
                "spider_name": spider_name,
                "status": "pending"
            })
        
        return task_id
    
    def get_pending_task(self) -> Optional[Dict[str, Any]]:
        """获取待处理任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, url, spider_name FROM tasks 
            WHERE status = 'pending' 
            ORDER BY created_at ASC 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "url": row[1],
                "spider_name": row[2],
                "status": "pending"
            }
        return None
    
    def update_task_status(self, task_id: int, status: str, worker_id: str = None, 
                         result: str = None, error: str = None):
        """更新任务状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status == "started":
            cursor.execute("""
                UPDATE tasks SET status = ?, started_at = CURRENT_TIMESTAMP, worker_id = ?
                WHERE id = ?
            """, (status, worker_id, task_id))
        elif status == "completed":
            cursor.execute("""
                UPDATE tasks SET status = ?, completed_at = CURRENT_TIMESTAMP, result = ?
                WHERE id = ?
            """, (status, result, task_id))
        elif status == "failed":
            cursor.execute("""
                UPDATE tasks SET status = ?, completed_at = CURRENT_TIMESTAMP, error = ?
                WHERE id = ?
            """, (status, error, task_id))
        
        conn.commit()
        conn.close()
    
    def update_worker_heartbeat(self, worker_id: str):
        """更新工作节点心跳"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO workers (id, last_heartbeat, status)
            VALUES (?, CURRENT_TIMESTAMP, 'active')
        """, (worker_id,))
        
        conn.commit()
        conn.close()
    
    def increment_worker_tasks(self, worker_id: str):
        """增加工作节点完成任务数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE workers SET tasks_completed = tasks_completed + 1
            WHERE id = ?
        """, (worker_id,))
        
        conn.commit()
        conn.close()

# 初始化数据库管理器
db_manager = SQLiteManager()

# 加载实际爬虫任务
def load_real_tasks():
    """从任务队列文件加载实际的爬虫任务"""
    import os
    import json
    
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    tasks_file = os.path.join(data_dir, "tasks_0.json")
    
    if os.path.exists(tasks_file):
        try:
            with open(tasks_file, 'r', encoding='utf-8') as f:
                tasks = []
                for line in f:
                    if line.strip():
                        task_data = json.loads(line.strip())
                        keyword = task_data.get("keyword", "")
                        year = task_data.get("year", 2024)
                        
                        # 根据关键词和年份构建搜索URL
                        # 这里使用Google学术搜索作为示例
                        search_url = f"https://scholar.google.com/scholar?q={keyword}&as_ylo={year}&as_yhi={year}"
                        
                        tasks.append((search_url, "html_spider"))
            
            # 只加载前20个任务进行测试
            for url, spider_name in tasks[:20]:
                db_manager.add_task(url, spider_name)
            
            logger.info(f"已加载 {len(tasks[:20])} 个实际爬虫任务")
            return True
            
        except Exception as e:
            logger.error(f"加载实际任务失败: {e}")
            return False
    else:
        logger.warning("任务文件不存在，初始化示例任务")
        return init_sample_tasks()

# 初始化示例任务
def init_sample_tasks():
    """初始化示例爬虫任务"""
    sample_tasks = [
        ("https://httpbin.org/json", "json_spider"),
        ("https://httpbin.org/html", "html_spider"),
        ("https://httpbin.org/xml", "xml_spider"),
        ("https://httpbin.org/robots.txt", "robots_spider"),
        ("https://httpbin.org/user-agent", "user_agent_spider"),
    ]
    
    for url, spider_name in sample_tasks:
        db_manager.add_task(url, spider_name)
    
    logger.info(f"已初始化 {len(sample_tasks)} 个示例任务")
    return True

# API端点
@app.get("/")
async def root():
    """根端点"""
    return {"message": "分布式爬虫主节点 - 简化版运行中"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_workers": len(active_workers),
        "pending_tasks": len([t for t in task_queue if t.get("status") == "pending"]),
        "completed_tasks": len(completed_tasks)
    }

@app.post("/worker/heartbeat")
async def worker_heartbeat(worker_id: str):
    """工作节点心跳"""
    with worker_lock:
        active_workers[worker_id] = {
            "last_heartbeat": datetime.now(),
            "status": "active"
        }
    
    # 更新数据库心跳
    db_manager.update_worker_heartbeat(worker_id)
    
    return {"status": "ok", "message": "心跳接收成功"}

@app.get("/task/request")
async def request_task(worker_id: str):
    """请求任务"""
    # 更新工作节点状态
    with worker_lock:
        if worker_id not in active_workers:
            active_workers[worker_id] = {
                "last_heartbeat": datetime.now(),
                "status": "active"
            }
    
    # 从数据库获取任务
    task = db_manager.get_pending_task()
    
    if task:
        # 更新任务状态为已开始
        db_manager.update_task_status(task["id"], "started", worker_id)
        
        return {
            "task_id": task["id"],
            "url": task["url"],
            "spider_name": task["spider_name"],
            "status": "assigned"
        }
    else:
        return {"status": "no_task", "message": "暂无可用任务"}

@app.post("/task/submit")
async def submit_task(
    task_id: int,
    worker_id: str,
    status: str,
    result: Optional[str] = None,
    error: Optional[str] = None
):
    """提交任务结果"""
    if status == "completed":
        db_manager.update_task_status(task_id, "completed", worker_id, result)
        db_manager.increment_worker_tasks(worker_id)
    elif status == "failed":
        db_manager.update_task_status(task_id, "failed", worker_id, None, error)
    
    return {"status": "ok", "message": "任务结果提交成功"}

@app.get("/stats")
async def get_stats():
    """获取统计信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取任务统计
    cursor.execute("""
        SELECT status, COUNT(*) FROM tasks GROUP BY status
    """)
    task_stats = {row[0]: row[1] for row in cursor.fetchall()}
    
    # 获取工作节点统计
    cursor.execute("""
        SELECT COUNT(*) FROM workers 
        WHERE last_heartbeat > datetime('now', '-30 seconds')
    """)
    active_workers_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "task_stats": task_stats,
        "active_workers": active_workers_count,
        "total_tasks": sum(task_stats.values()),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/results")
async def get_results(limit: int = 10):
    """获取已完成的任务结果"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, url, spider_name, result, completed_at 
        FROM tasks 
        WHERE status = 'completed' 
        ORDER BY completed_at DESC 
        LIMIT ?
    """, (limit,))
    
    results = []
    for row in cursor.fetchall():
        task_id, url, spider_name, result_json, completed_at = row
        try:
            result_data = json.loads(result_json) if result_json else {}
        except:
            result_data = {"raw_result": result_json}
        
        results.append({
            "task_id": task_id,
            "url": url,
            "spider_name": spider_name,
            "result": result_data,
            "completed_at": completed_at
        })
    
    conn.close()
    
    return {
        "total_completed": len(results),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

# 后台任务：清理过期工作节点
def cleanup_inactive_workers():
    """清理30秒内无心跳的工作节点"""
    while True:
        time.sleep(30)  # 每30秒清理一次
        
        current_time = datetime.now()
        inactive_workers = []
        
        with worker_lock:
            for worker_id, worker_info in active_workers.items():
                last_heartbeat = worker_info["last_heartbeat"]
                if (current_time - last_heartbeat).total_seconds() > 30:
                    inactive_workers.append(worker_id)
            
            for worker_id in inactive_workers:
                del active_workers[worker_id]
                logger.info(f"清理过期工作节点: {worker_id}")

# 启动清理线程
cleanup_thread = threading.Thread(target=cleanup_inactive_workers, daemon=True)
cleanup_thread.start()

if __name__ == "__main__":
    logger.info("启动分布式爬虫主节点服务（简化版）...")
    
    # 加载实际爬虫任务
    load_real_tasks()
    
    # 启动API服务 - 专门针对Windows网络问题的优化配置
    uvicorn.run(
        app, 
        host="127.0.0.1",  # 使用127.0.0.1而不是0.0.0.0，避免Windows网络问题
        port=8000, 
        log_level="info",
        # Windows网络连接优化参数
        timeout_keep_alive=300,  # 缩短保持连接超时时间到5分钟
        limit_max_requests=1000,  # 降低最大请求数限制，避免资源耗尽
        limit_concurrency=100,    # 降低并发连接数限制
        backlog=1024,            # 减小连接队列大小
        # 性能优化参数
        workers=1,                # 单进程模式（避免多进程同步问题）
        loop="asyncio",           # 使用asyncio事件循环
        http="auto",             # 自动选择HTTP协议实现
        # Windows特定优化
        use_colors=False,         # 禁用颜色输出，减少终端干扰
        access_log=False,          # 禁用访问日志，减少I/O压力
        # 连接池优化
        timeout_graceful_shutdown=30,  # 优雅关闭超时时间
    )