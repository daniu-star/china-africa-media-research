#!/usr/bin/env python3
"""
JavaScript渲染引擎 - 处理动态内容和单页应用
支持DOM操作模拟、AJAX请求处理和事件系统模拟
"""

import re
import time
import random
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from urllib.parse import urljoin, urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

class DOMElement:
    """DOM元素模拟"""
    
    def __init__(self, tag_name: str, attributes: Dict[str, str] = None, 
                 parent: 'DOMElement' = None):
        self.tag_name = tag_name
        self.attributes = attributes or {}
        self.parent = parent
        self.children = []
        self.text_content = ""
        self.style = {}
        self.classes = []
        self.event_listeners = {}
        
        # 解析class属性
        if 'class' in self.attributes:
            self.classes = self.attributes['class'].split()
    
    def query_selector(self, selector: str) -> Optional['DOMElement']:
        """模拟querySelector"""
        if selector.startswith('#'):
            # ID选择器
            target_id = selector[1:]
            return self._find_by_id(target_id)
        elif selector.startswith('.'):
            # Class选择器
            target_class = selector[1:]
            return self._find_by_class(target_class)
        else:
            # 标签选择器
            return self._find_by_tag(selector)
    
    def _find_by_id(self, element_id: str) -> Optional['DOMElement']:
        """通过ID查找元素"""
        if self.attributes.get('id') == element_id:
            return self
        
        for child in self.children:
            result = child._find_by_id(element_id)
            if result:
                return result
        
        return None
    
    def _find_by_class(self, class_name: str) -> Optional['DOMElement']:
        """通过Class查找元素"""
        if class_name in self.classes:
            return self
        
        for child in self.children:
            result = child._find_by_class(class_name)
            if result:
                return result
        
        return None
    
    def _find_by_tag(self, tag_name: str) -> Optional['DOMElement']:
        """通过标签名查找元素"""
        if self.tag_name == tag_name:
            return self
        
        for child in self.children:
            result = child._find_by_tag(tag_name)
            if result:
                return result
        
        return None
    
    def append_child(self, child: 'DOMElement') -> None:
        """添加子元素"""
        child.parent = self
        self.children.append(child)
    
    def set_attribute(self, name: str, value: str) -> None:
        """设置属性"""
        self.attributes[name] = value
        
        if name == 'class':
            self.classes = value.split()
    
    def add_event_listener(self, event_type: str, handler: Callable) -> None:
        """添加事件监听器"""
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
        self.event_listeners[event_type].append(handler)
    
    def trigger_event(self, event_type: str, event_data: Dict = None) -> None:
        """触发事件"""
        if event_type in self.event_listeners:
            for handler in self.event_listeners[event_type]:
                try:
                    handler(event_data or {})
                except Exception as e:
                    logger.warning(f"事件处理错误: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'tag_name': self.tag_name,
            'attributes': self.attributes,
            'text_content': self.text_content,
            'children_count': len(self.children),
            'classes': self.classes,
            'event_listeners': list(self.event_listeners.keys())
        }

class DOMParser:
    """DOM解析器"""
    
    def __init__(self):
        self.current_element = None
        self.root = None
    
    def parse_html(self, html_content: str) -> DOMElement:
        """解析HTML内容"""
        # 简化版HTML解析器
        # 实际实现应该使用更复杂的解析逻辑
        
        # 创建根元素
        self.root = DOMElement('html')
        self.current_element = self.root
        
        # 提取head和body
        head_match = re.search(r'<head>(.*?)</head>', html_content, re.DOTALL)
        body_match = re.search(r'<body>(.*?)</body>', html_content, re.DOTALL)
        
        if head_match:
            head_content = head_match.group(1)
            self._parse_head(head_content)
        
        if body_match:
            body_content = body_match.group(1)
            self._parse_body(body_content)
        
        return self.root
    
    def _parse_head(self, head_content: str) -> None:
        """解析head部分"""
        head_element = DOMElement('head')
        self.root.append_child(head_element)
        
        # 提取title
        title_match = re.search(r'<title>(.*?)</title>', head_content)
        if title_match:
            title_element = DOMElement('title')
            title_element.text_content = title_match.group(1)
            head_element.append_child(title_element)
        
        # 提取meta标签
        meta_matches = re.findall(r'<meta[^>]*>', head_content)
        for meta_tag in meta_matches:
            meta_element = self._parse_tag(meta_tag)
            if meta_element:
                head_element.append_child(meta_element)
    
    def _parse_body(self, body_content: str) -> None:
        """解析body部分"""
        body_element = DOMElement('body')
        self.root.append_child(body_element)
        
        # 提取div元素
        div_matches = re.findall(r'<div[^>]*>.*?</div>', body_content, re.DOTALL)
        for div_tag in div_matches:
            div_element = self._parse_div(div_tag)
            if div_element:
                body_element.append_child(div_element)
        
        # 提取script元素
        script_matches = re.findall(r'<script[^>]*>.*?</script>', body_content, re.DOTALL)
        for script_tag in script_matches:
            script_element = self._parse_script(script_tag)
            if script_element:
                body_element.append_child(script_element)
    
    def _parse_div(self, div_tag: str) -> Optional[DOMElement]:
        """解析div元素"""
        # 提取属性
        attributes = self._extract_attributes(div_tag)
        
        # 提取内容
        content_match = re.search(r'<div[^>]*>(.*?)</div>', div_tag, re.DOTALL)
        if content_match:
            content = content_match.group(1).strip()
        else:
            content = ""
        
        div_element = DOMElement('div', attributes)
        div_element.text_content = content
        
        return div_element
    
    def _parse_script(self, script_tag: str) -> Optional[DOMElement]:
        """解析script元素"""
        attributes = self._extract_attributes(script_tag)
        
        # 提取脚本内容
        content_match = re.search(r'<script[^>]*>(.*?)</script>', script_tag, re.DOTALL)
        if content_match:
            script_content = content_match.group(1).strip()
        else:
            script_content = ""
        
        script_element = DOMElement('script', attributes)
        script_element.text_content = script_content
        
        return script_element
    
    def _parse_tag(self, tag: str) -> Optional[DOMElement]:
        """解析通用标签"""
        tag_match = re.match(r'<([a-zA-Z]+)[^>]*>', tag)
        if tag_match:
            tag_name = tag_match.group(1)
            attributes = self._extract_attributes(tag)
            return DOMElement(tag_name, attributes)
        return None
    
    def _extract_attributes(self, tag: str) -> Dict[str, str]:
        """提取标签属性"""
        attributes = {}
        
        # 匹配属性名和值
        attr_matches = re.findall(r'([a-zA-Z_-]+)="([^"]*)"', tag)
        for name, value in attr_matches:
            attributes[name] = value
        
        return attributes

class AJAXSimulator:
    """AJAX请求模拟器"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.request_history = []
        self.mock_responses = self._initialize_mock_responses()
    
    def _initialize_mock_responses(self) -> Dict[str, Dict]:
        """初始化模拟响应"""
        return {
            '/api/content': {
                'status': 200,
                'data': {'content': 'Mock API content', 'items': ['item1', 'item2']}
            },
            '/api/comments': {
                'status': 200,
                'data': {'comments': ['comment1', 'comment2'], 'total': 2}
            },
            '/api/user': {
                'status': 200,
                'data': {'name': 'Test User', 'id': 123}
            }
        }
    
    def simulate_request(self, url: str, method: str = 'GET', 
                        data: Dict = None) -> Dict[str, Any]:
        """模拟AJAX请求"""
        # 记录请求
        request_id = len(self.request_history) + 1
        request_data = {
            'id': request_id,
            'url': url,
            'method': method,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        self.request_history.append(request_data)
        
        # 模拟网络延迟
        time.sleep(random.uniform(0.1, 1.0))
        
        # 检查是否有模拟响应
        path = urlparse(url).path
        if path in self.mock_responses:
            response = self.mock_responses[path].copy()
        else:
            # 默认响应
            response = {
                'status': 404,
                'data': {'error': 'Endpoint not found'}
            }
        
        # 更新请求状态
        request_data['status'] = 'completed'
        request_data['response'] = response
        
        return response
    
    def get_request_history(self) -> List[Dict[str, Any]]:
        """获取请求历史"""
        return self.request_history.copy()
    
    def clear_history(self) -> None:
        """清空请求历史"""
        self.request_history.clear()

class EventSystem:
    """事件系统模拟"""
    
    def __init__(self):
        self.global_listeners = {}
        self.event_queue = []
        self.is_running = False
    
    def add_global_listener(self, event_type: str, handler: Callable) -> None:
        """添加全局事件监听器"""
        if event_type not in self.global_listeners:
            self.global_listeners[event_type] = []
        self.global_listeners[event_type].append(handler)
    
    def trigger_global_event(self, event_type: str, event_data: Dict = None) -> None:
        """触发全局事件"""
        if event_type in self.global_listeners:
            for handler in self.global_listeners[event_type]:
                try:
                    handler(event_data or {})
                except Exception as e:
                    logger.warning(f"全局事件处理错误: {e}")
    
    def queue_event(self, event_type: str, target: DOMElement = None, 
                   event_data: Dict = None) -> None:
        """排队事件"""
        self.event_queue.append({
            'type': event_type,
            'target': target,
            'data': event_data or {},
            'timestamp': time.time()
        })
    
    def process_event_queue(self) -> None:
        """处理事件队列"""
        while self.event_queue:
            event = self.event_queue.pop(0)
            
            # 触发目标元素事件
            if event['target']:
                event['target'].trigger_event(event['type'], event['data'])
            
            # 触发全局事件
            self.trigger_global_event(event['type'], event['data'])
    
    def start_event_loop(self) -> None:
        """启动事件循环"""
        self.is_running = True
        
        while self.is_running:
            self.process_event_queue()
            time.sleep(0.1)  # 100ms间隔
    
    def stop_event_loop(self) -> None:
        """停止事件循环"""
        self.is_running = False

class JavaScriptRenderingEngine:
    """JavaScript渲染引擎"""
    
    def __init__(self, base_url: str = ""):
        self.base_url = base_url
        self.dom_parser = DOMParser()
        self.ajax_simulator = AJAXSimulator(base_url)
        self.event_system = EventSystem()
        self.dom_tree = None
        self.rendered_content = ""
        self.execution_context = {}
        
        # 初始化全局函数
        self._initialize_global_functions()
        
        logger.info(f"JavaScript渲染引擎初始化完成，基础URL: {base_url}")
    
    def _initialize_global_functions(self) -> None:
        """初始化全局函数"""
        self.execution_context['console'] = {
            'log': lambda *args: logger.info(f"JS Console: {' '.join(map(str, args))}"),
            'warn': lambda *args: logger.warning(f"JS Console: {' '.join(map(str, args))}"),
            'error': lambda *args: logger.error(f"JS Console: {' '.join(map(str, args))}")
        }
        
        self.execution_context['setTimeout'] = self._set_timeout
        self.execution_context['setInterval'] = self._set_interval
        self.execution_context['XMLHttpRequest'] = self._mock_xml_http_request
        
        # 模拟window对象
        self.execution_context['window'] = {
            'location': {'href': self.base_url},
            'document': {},
            'addEventListener': self.event_system.add_global_listener
        }
    
    def _set_timeout(self, callback: Callable, delay: int) -> None:
        """模拟setTimeout"""
        def timeout_wrapper():
            time.sleep(delay / 1000.0)  # 转换为秒
            callback()
        
        # 在实际实现中应该使用线程
        # 这里简化处理，直接执行
        timeout_wrapper()
    
    def _set_interval(self, callback: Callable, interval: int) -> None:
        """模拟setInterval"""
        def interval_wrapper():
            while True:
                time.sleep(interval / 1000.0)
                callback()
        
        # 在实际实现中应该使用线程
        # 这里简化处理，只执行一次
        callback()
    
    def _mock_xml_http_request(self) -> 'MockXMLHttpRequest':
        """模拟XMLHttpRequest"""
        return MockXMLHttpRequest(self.ajax_simulator)
    
    def render_page(self, html_content: str, execute_scripts: bool = True) -> Dict[str, Any]:
        """渲染页面"""
        start_time = time.time()
        
        # 解析DOM
        self.dom_tree = self.dom_parser.parse_html(html_content)
        
        # 执行脚本
        if execute_scripts:
            self._execute_scripts()
        
        # 处理AJAX请求
        self._simulate_ajax_requests()
        
        # 触发页面加载事件
        self.event_system.queue_event('DOMContentLoaded')
        self.event_system.queue_event('load')
        
        # 处理事件队列
        self.event_system.process_event_queue()
        
        # 生成渲染结果
        rendering_time = time.time() - start_time
        
        result = {
            'dom_tree': self._dom_to_dict(self.dom_tree),
            'ajax_requests': self.ajax_simulator.get_request_history(),
            'rendering_time': rendering_time,
            'element_count': self._count_elements(self.dom_tree),
            'script_count': self._count_scripts(self.dom_tree),
            'rendered_content': self._generate_rendered_content()
        }
        
        logger.info(f"页面渲染完成，耗时: {rendering_time:.2f}秒")
        
        return result
    
    def _execute_scripts(self) -> None:
        """执行脚本"""
        if not self.dom_tree:
            return
        
        # 查找所有script元素
        script_elements = self._find_script_elements(self.dom_tree)
        
        for script_element in script_elements:
            script_content = script_element.text_content
            if script_content:
                try:
                    # 在实际实现中应该使用JavaScript解释器
                    # 这里简化处理，只记录执行
                    logger.info(f"执行脚本: {script_content[:100]}...")
                except Exception as e:
                    logger.warning(f"脚本执行错误: {e}")
    
    def _find_script_elements(self, element: DOMElement) -> List[DOMElement]:
        """查找所有script元素"""
        scripts = []
        
        if element.tag_name == 'script':
            scripts.append(element)
        
        for child in element.children:
            scripts.extend(self._find_script_elements(child))
        
        return scripts
    
    def _simulate_ajax_requests(self) -> None:
        """模拟AJAX请求"""
        # 模拟常见的API端点请求
        endpoints = ['/api/content', '/api/comments', '/api/user']
        
        for endpoint in endpoints:
            if random.random() < 0.7:  # 70%概率发起请求
                url = urljoin(self.base_url, endpoint)
                self.ajax_simulator.simulate_request(url)
    
    def _dom_to_dict(self, element: DOMElement) -> Dict[str, Any]:
        """将DOM转换为字典"""
        result = element.to_dict()
        
        if element.children:
            result['children'] = [self._dom_to_dict(child) for child in element.children]
        
        return result
    
    def _count_elements(self, element: DOMElement) -> int:
        """计算元素数量"""
        count = 1  # 当前元素
        
        for child in element.children:
            count += self._count_elements(child)
        
        return count
    
    def _count_scripts(self, element: DOMElement) -> int:
        """计算脚本数量"""
        count = 1 if element.tag_name == 'script' else 0
        
        for child in element.children:
            count += self._count_scripts(child)
        
        return count
    
    def _generate_rendered_content(self) -> str:
        """生成渲染后的内容"""
        if not self.dom_tree:
            return ""
        
        # 简化版内容生成
        # 实际实现应该生成完整的HTML
        content_parts = []
        
        def extract_text(element: DOMElement):
            if element.text_content:
                content_parts.append(element.text_content)
            
            for child in element.children:
                extract_text(child)
        
        extract_text(self.dom_tree)
        
        return " ".join(content_parts)
    
    def simulate_user_interaction(self, interaction_type: str, 
                                 target_selector: str = None) -> Dict[str, Any]:
        """模拟用户交互"""
        if not self.dom_tree:
            return {'error': 'DOM树未初始化'}
        
        target_element = None
        if target_selector:
            target_element = self.dom_tree.query_selector(target_selector)
        
        # 排队交互事件
        self.event_system.queue_event(interaction_type, target_element)
        
        # 处理事件队列
        self.event_system.process_event_queue()
        
        return {
            'interaction_type': interaction_type,
            'target_found': target_element is not None,
            'timestamp': datetime.now().isoformat()
        }

class MockXMLHttpRequest:
    """模拟XMLHttpRequest"""
    
    def __init__(self, ajax_simulator: AJAXSimulator):
        self.ajax_simulator = ajax_simulator
        self.onreadystatechange = None
        self.readyState = 0
        self.status = 0
        self.responseText = ""
    
    def open(self, method: str, url: str, async: bool = True) -> None:
        """模拟open方法"""
        self.method = method
        self.url = url
        self.async = async
        self.readyState = 1  # OPENED
    
    def send(self, data: str = None) -> None:
        """模拟send方法"""
        self.readyState = 2  # HEADERS_RECEIVED
        
        # 模拟请求
        response = self.ajax_simulator.simulate_request(self.url, self.method, 
                                                        {'data': data} if data else None)
        
        self.status = response['status']
        self.responseText = json.dumps(response['data'])
        self.readyState = 4  # DONE
        
        # 触发回调
        if self.onreadystatechange:
            self.onreadystatechange()

# 测试示例
def test_javascript_rendering_engine():
    """测试JavaScript渲染引擎"""
    print("=== 测试JavaScript渲染引擎 ===")
    
    # 测试URL
    test_urls = [
        'https://www.news24.com',
        'https://www.dstv.com', 
        'https://www.jumia.co.ke'
    ]
    
    for url in test_urls:
        print(f"\n测试URL: {url}")
        
        # 创建渲染引擎
        engine = JavaScriptRenderingEngine(url)
        
        # 测试HTML内容
        test_html = """
        <html>
            <head>
                <title>测试页面 - {url}</title>
                <meta name="description" content="测试页面描述">
            </head>
            <body>
                <div id="header">
                    <h1>欢迎来到 {url}</h1>
                </div>
                <div id="content" class="main-content">
                    <p>这是主要内容区域</p>
                    <div id="dynamic-content">动态内容将在这里加载</div>
                </div>
                <script>
                    console.log('页面脚本执行');
                    setTimeout(function() {
                        console.log('延迟执行完成');
                    }, 1000);
                </script>
            </body>
        </html>
        """.format(url=url)
        
        # 渲染页面
        result = engine.render_page(test_html)
        
        print(f"渲染耗时: {result['rendering_time']:.2f}秒")
        print(f"DOM元素数量: {result['element_count']}")
        print(f"脚本数量: {result['script_count']}")
        print(f"AJAX请求数量: {len(result['ajax_requests'])}")
        
        # 模拟用户交互
        interactions = ['click', 'scroll', 'mouseover']
        for interaction in interactions:
            interaction_result = engine.simulate_user_interaction(
                interaction, '#content'
            )
            print(f"{interaction}交互结果: {interaction_result['target_found']}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_javascript_rendering_engine()