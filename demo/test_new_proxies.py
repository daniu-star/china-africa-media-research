#!/usr/bin/env python3
"""
测试新的非洲代理服务器配置
"""

import json
import requests
import time
from datetime import datetime

def test_proxy_connection():
    """测试代理连接"""
    
    # 加载代理配置
    try:
        with open('proxy_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 加载代理配置文件失败: {e}")
        return
    
    proxies_list = config.get('proxies', [])
    print(f"📊 共有 {len(proxies_list)} 个代理配置")
    
    # 测试每个代理
    test_urls = [
        "http://httpbin.org/ip",
        "https://httpbin.org/ip",
        "http://www.dailymaverick.co.za",
        "https://www.thecitizen.co.tz"
    ]
    
    for i, proxy_info in enumerate(proxies_list):
        print(f"\n🔍 测试代理 {i+1}: {proxy_info.get('country', 'unknown')}")
        
        # 获取代理URL
        proxy_url = proxy_info.get('http') or proxy_info.get('https')
        if not proxy_url:
            print("   ⚠️  无有效代理URL，跳过")
            continue
            
        print(f"   📡 代理地址: {proxy_url}")
        
        # 设置代理
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        # 测试连接
        for test_url in test_urls:
            try:
                print(f"   🔗 测试 {test_url}")
                
                # 设置超时时间
                timeout = 30
                if proxy_info.get('country') in ['ZA', 'KE', 'NG']:
                    timeout = 60  # 非洲代理使用更长超时
                
                response = requests.get(
                    test_url, 
                    proxies=proxies, 
                    timeout=timeout,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                
                if response.status_code == 200:
                    print(f"   ✅ 连接成功 - 状态码: {response.status_code}")
                    if 'httpbin' in test_url:
                        try:
                            ip_info = response.json()
                            print(f"   🌐 当前IP: {ip_info.get('origin', 'unknown')}")
                        except:
                            pass
                else:
                    print(f"   ⚠️  连接失败 - 状态码: {response.status_code}")
                    
            except requests.exceptions.ProxyError as e:
                print(f"   ❌ 代理错误: {e}")
            except requests.exceptions.ConnectTimeout as e:
                print(f"   ⏰ 连接超时: {e}")
            except requests.exceptions.ReadTimeout as e:
                print(f"   ⏰ 读取超时: {e}")
            except requests.exceptions.ConnectionError as e:
                print(f"   🔌 连接错误: {e}")
            except Exception as e:
                print(f"   ❌ 其他错误: {e}")
        
        # 添加延迟避免过快请求
        time.sleep(2)

def test_direct_connection():
    """测试直接连接"""
    print("\n🔍 测试直接连接（无代理）")
    
    test_urls = [
        "http://httpbin.org/ip",
        "https://httpbin.org/ip",
        "http://www.dailymaverick.co.za",
        "https://www.thecitizen.co.tz"
    ]
    
    for test_url in test_urls:
        try:
            print(f"   🔗 测试 {test_url}")
            response = requests.get(test_url, timeout=30)
            
            if response.status_code == 200:
                print(f"   ✅ 连接成功 - 状态码: {response.status_code}")
                if 'httpbin' in test_url:
                    try:
                        ip_info = response.json()
                        print(f"   🌐 当前IP: {ip_info.get('origin', 'unknown')}")
                    except:
                        pass
            else:
                print(f"   ⚠️  连接失败 - 状态码: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 错误: {e}")

def main():
    """主函数"""
    print("🚀 开始测试新的非洲代理服务器配置")
    print("=" * 60)
    
    # 检查必要文件
    import os
    if not os.path.exists('proxy_config.json'):
        print("❌ proxy_config.json 文件不存在")
        return
    
    # 测试代理连接
    test_proxy_connection()
    
    # 测试直接连接
    test_direct_connection()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")

if __name__ == "__main__":
    main()