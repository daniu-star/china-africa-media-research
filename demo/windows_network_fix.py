#!/usr/bin/env python3
"""
Windows网络连接问题诊断和修复工具
专门解决分布式爬虫系统中的WinError 64问题
"""

import os
import sys
import time
import socket
import psutil
import subprocess
import platform
from datetime import datetime
import requests

def check_system_info():
    """检查系统信息"""
    print("=== 系统信息检查 ===")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"系统版本: {platform.version()}")
    print(f"处理器: {platform.processor()}")
    print(f"Python版本: {platform.python_version()}")
    print()

def check_network_interfaces():
    """检查网络接口"""
    print("=== 网络接口检查 ===")
    
    try:
        interfaces = psutil.net_if_addrs()
        for interface_name, interface_addresses in interfaces.items():
            print(f"接口: {interface_name}")
            for addr in interface_addresses:
                if addr.family == socket.AF_INET:
                    print(f"  IPv4地址: {addr.address} 掩码: {addr.netmask}")
                elif addr.family == socket.AF_INET6:
                    print(f"  IPv6地址: {addr.address}")
            print()
    except Exception as e:
        print(f"网络接口检查失败: {e}")

def check_port_availability(port=8000):
    """检查端口可用性"""
    print(f"=== 端口 {port} 可用性检查 ===")
    
    try:
        # 检查端口是否被占用
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            print(f"端口 {port} 已被占用")
            
            # 查找占用端口的进程
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    for conn in proc.info.get('connections', []):
                        if hasattr(conn, 'laddr') and conn.laddr.port == port:
                            print(f"  占用进程: {proc.info['name']} (PID: {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return False
        else:
            print(f"端口 {port} 可用")
            return True
            
    except Exception as e:
        print(f"端口检查失败: {e}")
        return False

def check_firewall_settings():
    """检查防火墙设置"""
    print("=== 防火墙检查 ===")
    
    try:
        # 检查Windows防火墙状态
        if platform.system() == 'Windows':
            result = subprocess.run(
                ['netsh', 'advfirewall', 'show', 'allprofiles'],
                capture_output=True, text=True
            )
            
            if 'ON' in result.stdout:
                print("Windows防火墙已启用")
                
                # 检查Python是否在防火墙例外列表中
                python_exe = sys.executable
                result = subprocess.run(
                    ['netsh', 'advfirewall', 'firewall', 'show', 'rule', f'name={python_exe}'],
                    capture_output=True, text=True
                )
                
                if 'No rules match' in result.stdout:
                    print("⚠ Python程序不在防火墙例外列表中")
                else:
                    print("✓ Python程序已在防火墙例外列表中")
            else:
                print("Windows防火墙已禁用")
        else:
            print("非Windows系统，跳过防火墙检查")
            
    except Exception as e:
        print(f"防火墙检查失败: {e}")

def check_socket_limits():
    """检查Socket限制"""
    print("=== Socket限制检查 ===")
    
    try:
        if platform.system() == 'Windows':
            # Windows系统检查
            print("Windows系统Socket限制检查:")
            
            # 检查TCP连接限制
            result = subprocess.run(
                ['netsh', 'int', 'ipv4', 'show', 'dynamicport', 'tcp'],
                capture_output=True, text=True
            )
            
            if 'Start Port' in result.stdout:
                print("TCP动态端口范围:")
                for line in result.stdout.split('\n'):
                    if 'Start Port' in line or 'Number of Ports' in line:
                        print(f"  {line.strip()}")
            
            # 检查TCP连接数限制
            result = subprocess.run(
                ['reg', 'query', 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters', '/v', 'MaxUserPort'],
                capture_output=True, text=True
            )
            
            if 'MaxUserPort' in result.stdout:
                print("最大用户端口数:")
                for line in result.stdout.split('\n'):
                    if 'MaxUserPort' in line:
                        print(f"  {line.strip()}")
                        
        else:
            print("非Windows系统，跳过Socket限制检查")
            
    except Exception as e:
        print(f"Socket限制检查失败: {e}")

def check_dns_resolution():
    """检查DNS解析"""
    print("=== DNS解析检查 ===")
    
    try:
        # 检查localhost解析
        localhost_ip = socket.gethostbyname('localhost')
        print(f"localhost解析: {localhost_ip}")
        
        # 检查127.0.0.1解析
        hostname = socket.gethostbyaddr('127.0.0.1')
        print(f"127.0.0.1反向解析: {hostname[0]}")
        
        print("✓ DNS解析正常")
        
    except Exception as e:
        print(f"DNS解析失败: {e}")

def check_network_connectivity():
    """检查网络连接性"""
    print("=== 网络连接性检查 ===")
    
    # 测试本地连接
    test_urls = [
        ('http://127.0.0.1:8000/health', '主节点健康检查'),
        ('http://localhost:8000/health', 'localhost健康检查'),
    ]
    
    for url, description in test_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✓ {description}: 连接成功")
            else:
                print(f"⚠ {description}: HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"✗ {description}: 连接失败")
        except requests.exceptions.Timeout:
            print(f"✗ {description}: 连接超时")
        except Exception as e:
            print(f"✗ {description}: {e}")

def check_system_resources():
    """检查系统资源"""
    print("=== 系统资源检查 ===")
    
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"CPU使用率: {cpu_percent:.1f}%")
        
        # 内存使用率
        memory = psutil.virtual_memory()
        print(f"内存使用率: {memory.percent:.1f}%")
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        print(f"磁盘使用率: {disk.percent:.1f}%")
        
        # 网络连接数
        connections = psutil.net_connections()
        print(f"网络连接数: {len(connections)}")
        
        # 进程数
        processes = len(psutil.pids())
        print(f"系统进程数: {processes}")
        
    except Exception as e:
        print(f"系统资源检查失败: {e}")

def check_python_network_settings():
    """检查Python网络设置"""
    print("=== Python网络设置检查 ===")
    
    try:
        import socket
        
        # 检查默认超时设置
        default_timeout = socket.getdefaulttimeout()
        print(f"默认Socket超时: {default_timeout}")
        
        # 检查Socket选项
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # 检查SO_REUSEADDR
        reuse_addr = sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)
        print(f"SO_REUSEADDR: {reuse_addr}")
        
        # 检查TCP_NODELAY
        tcp_nodelay = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY)
        print(f"TCP_NODELAY: {tcp_nodelay}")
        
        sock.close()
        
        print("✓ Python网络设置正常")
        
    except Exception as e:
        print(f"Python网络设置检查失败: {e}")

def apply_windows_network_fixes():
    """应用Windows网络修复"""
    print("=== 应用Windows网络修复 ===")
    
    if platform.system() != 'Windows':
        print("非Windows系统，跳过修复")
        return
    
    try:
        # 1. 重置TCP/IP协议栈
        print("1. 重置TCP/IP协议栈...")
        subprocess.run(['netsh', 'int', 'ip', 'reset'], capture_output=True)
        
        # 2. 重置Winsock目录
        print("2. 重置Winsock目录...")
        subprocess.run(['netsh', 'winsock', 'reset'], capture_output=True)
        
        # 3. 刷新DNS缓存
        print("3. 刷新DNS缓存...")
        subprocess.run(['ipconfig', '/flushdns'], capture_output=True)
        
        # 4. 释放和续订IP地址
        print("4. 释放和续订IP地址...")
        subprocess.run(['ipconfig', '/release'], capture_output=True)
        subprocess.run(['ipconfig', '/renew'], capture_output=True)
        
        print("✓ Windows网络修复完成，建议重启系统")
        
    except Exception as e:
        print(f"Windows网络修复失败: {e}")

def optimize_network_settings():
    """优化网络设置"""
    print("=== 优化网络设置 ===")
    
    try:
        # 优化TCP连接参数
        if platform.system() == 'Windows':
            print("优化Windows TCP设置...")
            
            # 设置最大用户端口数
            subprocess.run(['reg', 'add', 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters', '/v', 'MaxUserPort', '/t', 'REG_DWORD', '/d', '65534', '/f'], capture_output=True)
            
            # 设置TCP等待时间
            subprocess.run(['reg', 'add', 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters', '/v', 'TcpTimedWaitDelay', '/t', 'REG_DWORD', '/d', '30', '/f'], capture_output=True)
            
            print("✓ Windows网络优化完成")
        else:
            print("非Windows系统，跳过优化")
            
    except Exception as e:
        print(f"网络优化失败: {e}")

def generate_diagnostic_report():
    """生成诊断报告"""
    print("\n" + "="*60)
    print("=== 网络诊断报告 ===")
    print("="*60)
    
    check_system_info()
    check_network_interfaces()
    check_port_availability()
    check_firewall_settings()
    check_socket_limits()
    check_dns_resolution()
    check_network_connectivity()
    check_system_resources()
    check_python_network_settings()
    
    print("\n=== 建议修复措施 ===")
    print("1. 如果端口被占用，请终止占用进程")
    print("2. 如果防火墙阻止，请添加Python程序到例外列表")
    print("3. 如果DNS解析失败，请检查hosts文件")
    print("4. 如果系统资源不足，请关闭不必要的程序")
    print("5. 运行Windows网络修复工具")
    print("6. 优化网络设置")
    
    print("\n=== 修复命令 ===")
    print("netsh int ip reset")
    print("netsh winsock reset") 
    print("ipconfig /flushdns")
    print("ipconfig /release")
    print("ipconfig /renew")

def main():
    """主函数"""
    print("Windows网络连接问题诊断工具")
    print("专门解决分布式爬虫系统中的WinError 64问题")
    print("="*60)
    
    # 生成诊断报告
    generate_diagnostic_report()
    
    # 询问是否应用修复
    print("\n是否应用Windows网络修复? (y/n): ")
    choice = input().strip().lower()
    
    if choice == 'y':
        apply_windows_network_fixes()
        
        print("\n是否优化网络设置? (y/n): ")
        choice = input().strip().lower()
        
        if choice == 'y':
            optimize_network_settings()
    
    print("\n诊断完成！")
    print("建议重启系统后重新运行分布式爬虫系统")

if __name__ == "__main__":
    main()