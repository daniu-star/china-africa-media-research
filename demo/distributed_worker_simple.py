"""
分布式爬虫工作节点 - 简化版
专门解决Windows网络连接问题
"""

import time
import requests
import logging
import threading
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[工作节点] %(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class SimpleWorker:
    """简化版工作节点"""
    
    def __init__(self, master_url: str = "http://127.0.0.1:8000"):
        self.master_url = master_url
        self.worker_id = f"worker-{uuid.uuid4().hex[:8]}"
        self.running = False
        
        # 连接配置
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # 适配器配置 - Windows网络优化
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,      # 减少连接池大小
            pool_maxsize=10,         # 减少最大连接数
            max_retries=3,           # 重试次数
            pool_block=True          # 连接池阻塞模式
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 请求超时配置
        self.timeout = 60  # 60秒超时
        
        logger.info(f"工作节点 {self.worker_id} 初始化完成，主节点: {self.master_url}")
    
    def send_heartbeat(self) -> bool:
        """发送心跳到主节点"""
        try:
            response = self.session.post(
                f"{self.master_url}/worker/heartbeat",
                params={"worker_id": self.worker_id},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"心跳发送失败: {e}")
            return False
    
    def request_task(self) -> Optional[Dict[str, Any]]:
        """向主节点请求任务"""
        try:
            response = self.session.get(
                f"{self.master_url}/task/request",
                params={"worker_id": self.worker_id},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "assigned":
                    return data
                else:
                    logger.info(f"暂无可用任务: {data.get('message')}")
                    return None
            else:
                logger.error(f"任务请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"任务请求异常: {e}")
            return None
    
    def submit_task_result(self, task_id: int, status: str, 
                          result: Optional[str] = None, error: Optional[str] = None) -> bool:
        """提交任务结果"""
        try:
            response = self.session.post(
                f"{self.master_url}/task/submit",
                params={
                    "task_id": task_id,
                    "worker_id": self.worker_id,
                    "status": status,
                    "result": result,
                    "error": error
                },
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"任务结果提交失败: {e}")
            return False
    
    def execute_spider(self, url: str, spider_name: str) -> Dict[str, Any]:
        """执行爬虫任务"""
        try:
            logger.info(f"开始执行爬虫任务: {spider_name} - {url}")
            
            # 根据爬虫类型执行不同的爬取逻辑
            if spider_name == "json_spider":
                result = self.fetch_json(url)
            elif spider_name == "html_spider":
                result = self.fetch_html(url)
            elif spider_name == "xml_spider":
                result = self.fetch_xml(url)
            elif spider_name == "robots_spider":
                result = self.fetch_robots(url)
            elif spider_name == "user_agent_spider":
                result = self.fetch_user_agent(url)
            else:
                result = self.fetch_generic(url)
            
            logger.info(f"爬虫任务完成: {spider_name} - {url}")
            return {"status": "completed", "result": json.dumps(result, ensure_ascii=False)}
            
        except Exception as e:
            logger.error(f"爬虫任务执行失败: {e}")
            return {"status": "failed", "error": str(e)}
    
    def fetch_json(self, url: str) -> Dict[str, Any]:
        """获取JSON数据"""
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return {
            "type": "json",
            "content": response.json(),
            "status_code": response.status_code,
            "headers": dict(response.headers)
        }
    
    def fetch_html(self, url: str) -> Dict[str, Any]:
        """获取HTML数据"""
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return {
            "type": "html",
            "content_length": len(response.text),
            "status_code": response.status_code,
            "title": self.extract_title(response.text)
        }
    
    def fetch_xml(self, url: str) -> Dict[str, Any]:
        """获取XML数据"""
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return {
            "type": "xml",
            "content_length": len(response.text),
            "status_code": response.status_code
        }
    
    def fetch_robots(self, url: str) -> Dict[str, Any]:
        """获取robots.txt"""
        response = self.session.get(url, timeout=self.timeout)
        return {
            "type": "robots",
            "content": response.text,
            "status_code": response.status_code
        }
    
    def fetch_user_agent(self, url: str) -> Dict[str, Any]:
        """获取User-Agent信息"""
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return {
            "type": "user_agent",
            "user_agent": response.json().get("user-agent", ""),
            "status_code": response.status_code
        }
    
    def fetch_generic(self, url: str) -> Dict[str, Any]:
        """通用爬取"""
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return {
            "type": "generic",
            "content_length": len(response.text),
            "status_code": response.status_code,
            "url": url
        }
    
    def extract_title(self, html: str) -> str:
        """提取HTML标题"""
        import re
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        return title_match.group(1) if title_match else "No title found"
    
    def heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                self.send_heartbeat()
                time.sleep(30)  # 每30秒发送一次心跳
            except Exception as e:
                logger.error(f"心跳循环异常: {e}")
                time.sleep(10)  # 异常时等待10秒后重试
    
    def work_loop(self):
        """工作循环"""
        while self.running:
            try:
                # 请求任务
                task = self.request_task()
                
                if task:
                    # 执行任务
                    task_id = task["task_id"]
                    url = task["url"]
                    spider_name = task["spider_name"]
                    
                    # 执行爬虫
                    result = self.execute_spider(url, spider_name)
                    
                    # 提交结果
                    if result["status"] == "completed":
                        self.submit_task_result(task_id, "completed", result["result"])
                        logger.info(f"任务 {task_id} 完成")
                    else:
                        self.submit_task_result(task_id, "failed", error=result["error"])
                        logger.warning(f"任务 {task_id} 失败: {result['error']}")
                else:
                    # 没有任务时等待5秒
                    time.sleep(5)
                    
            except Exception as e:
                logger.error(f"工作循环异常: {e}")
                time.sleep(10)  # 异常时等待10秒后重试
    
    def start(self):
        """启动工作节点"""
        self.running = True
        
        # 启动心跳线程
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # 启动工作线程
        work_thread = threading.Thread(target=self.work_loop, daemon=True)
        work_thread.start()
        
        logger.info(f"工作节点 {self.worker_id} 已启动")
        
        # 主线程等待
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """停止工作节点"""
        self.running = False
        logger.info(f"工作节点 {self.worker_id} 正在停止...")
        
        # 关闭会话
        self.session.close()
        logger.info(f"工作节点 {self.worker_id} 已停止")

def main():
    """主函数"""
    # 创建并启动工作节点
    worker = SimpleWorker()
    
    try:
        worker.start()
    except KeyboardInterrupt:
        worker.stop()
    except Exception as e:
        logger.error(f"工作节点异常终止: {e}")
        worker.stop()

if __name__ == "__main__":
    main()