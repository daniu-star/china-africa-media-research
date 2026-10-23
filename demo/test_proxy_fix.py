#!/usr/bin/env python3
"""
测试代理配置修复和数据保存功能
"""

import json
import requests
import time
import os
from datetime import datetime

def test_proxy_connection():
    """测试代理连接"""
    print("=== 代理连接测试 ===")
    
    # 加载代理配置
    with open('proxy_config.json', 'r', encoding='utf-8') as f:
        proxy_config = json.load(f)
    
    proxies_list = proxy_config.get('proxies', [])
    print(f"代理池中有 {len(proxies_list)} 个代理")
    
    # 测试前5个代理
    test_urls = [
        'http://httpbin.org/ip',
        'https://httpbin.org/ip',
        'http://www.allafrica.com/',
        'https://www.businesslive.co.za/'
    ]
    
    for i, proxy_info in enumerate(proxies_list[:5]):
        proxy_url = proxy_info.get('http') or proxy_info.get('https')
        
        if not proxy_url:
            print(f"\n测试代理 {i+1}: 无有效代理URL (直接连接)")
            proxy_url = None
        else:
            print(f"\n测试代理 {i+1}: {proxy_url}")
        
        for test_url in test_urls:
            try:
                start_time = time.time()
                
                if proxy_url:
                    proxies = {'http': proxy_url, 'https': proxy_url}
                else:
                    proxies = None  # 直接连接
                
                response = requests.get(
                    test_url,
                    proxies=proxies,
                    timeout=30
                )
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    print(f"  ✓ {test_url} - 成功 (耗时: {elapsed:.2f}s)")
                    if 'httpbin' in test_url:
                        print(f"    当前IP: {response.json().get('origin', '未知')}")
                else:
                    print(f"  ✗ {test_url} - 状态码: {response.status_code}")
                    
            except Exception as e:
                print(f"  ✗ {test_url} - 错误: {type(e).__name__}")

def test_data_saving():
    """测试数据保存功能"""
    print("\n=== 数据保存测试 ===")
    
    # 创建测试数据目录
    data_dir = 'crawled_data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"创建数据目录: {data_dir}")
    
    # 生成测试数据
    test_data = {
        'timestamp': datetime.now().isoformat(),
        'url': 'https://example.com/test',
        'title': '测试页面',
        'content': '这是测试数据内容',
        'status': 'success'
    }
    
    # 保存测试数据
    filename = f"test_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(data_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"测试数据已保存到: {filepath}")
    
    # 验证文件存在
    if os.path.exists(filepath):
        print("✓ 数据保存功能正常")
        
        # 读取验证
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        if loaded_data['status'] == 'success':
            print("✓ 数据读取验证成功")
        else:
            print("✗ 数据读取验证失败")
    else:
        print("✗ 数据保存失败")

def check_system_status():
    """检查系统状态"""
    print("\n=== 系统状态检查 ===")
    
    # 检查必要文件
    required_files = ['proxy_config.json', 'africa_website_optimization.json']
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} 存在")
        else:
            print(f"✗ {file} 不存在")
    
    # 检查Python包
    required_packages = ['requests', 'urllib3', 'fake_useragent']
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} 已安装")
        except ImportError:
            print(f"✗ {package} 未安装")

if __name__ == "__main__":
    print("开始测试代理配置修复和数据保存功能...")
    
    check_system_status()
    test_proxy_connection()
    test_data_saving()
    
    print("\n=== 测试完成 ===")