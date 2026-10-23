#!/usr/bin/env python3
import requests
import time

def test_master_connection():
    """测试主节点连接"""
    url = "http://localhost:8000/health"
    
    print("=== 测试主节点连接 ===")
    
    # 尝试多种连接方式
    for attempt in range(5):
        try:
            print(f"尝试 {attempt + 1}/5: 连接 {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 主节点连接成功!")
                print(f"状态: {data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ HTTP状态码: {response.status_code}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ 连接错误: {e}")
        except requests.exceptions.Timeout as e:
            print(f"❌ 超时错误: {e}")
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求错误: {e}")
        
        if attempt < 4:
            print("等待5秒后重试...")
            time.sleep(5)
    
    print("❌ 所有连接尝试失败")
    return False

if __name__ == "__main__":
    test_master_connection()