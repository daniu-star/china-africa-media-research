#!/usr/bin/env python3
"""
测试数据存储管理器功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_storage_manager import DataStorageManager, save_task_data, load_task_data
from datetime import datetime
import json
import shutil

def test_basic_operations():
    """测试基本操作"""
    print("=== 测试基本操作 ===")
    
    # 创建管理器实例
    manager = DataStorageManager()
    
    # 测试数据保存
    test_data = {
        'timestamp': datetime.now().isoformat(),
        'message': '这是测试数据',
        'status': 'success'
    }
    
    # 保存数据
    if manager.save_data(test_data, 'test_basic.json'):
        print("✓ 基本数据保存成功")
    else:
        print("✗ 基本数据保存失败")
        return False
    
    # 加载数据
    loaded_data = manager.load_data('test_basic.json')
    if loaded_data and loaded_data['message'] == test_data['message']:
        print("✓ 基本数据加载成功")
    else:
        print("✗ 基本数据加载失败")
        return False
    
    return True

def test_task_operations():
    """测试任务数据操作"""
    print("\n=== 测试任务数据操作 ===")
    
    # 创建测试任务数据
    test_tasks = [
        {
            'task_id': 'test_task_001',
            'keyword': 'china',
            'category': 'primary_keywords.core_identity',
            'year': 2023,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'priority': 'medium',
            'priority_weight': 1,
            'attempts': 0
        },
        {
            'task_id': 'test_task_002',
            'keyword': 'chinese',
            'category': 'primary_keywords.core_identity',
            'year': 2024,
            'status': 'completed',
            'created_at': datetime.now().isoformat(),
            'priority': 'high',
            'priority_weight': 2,
            'attempts': 1
        }
    ]
    
    # 保存任务数据
    if save_task_data(test_tasks, 'test_tasks.json'):
        print("✓ 任务数据保存成功")
    else:
        print("✗ 任务数据保存失败")
        return False
    
    # 加载任务数据
    loaded_tasks = load_task_data('test_tasks.json')
    if loaded_tasks and len(loaded_tasks) == len(test_tasks):
        print("✓ 任务数据加载成功")
        print(f"  加载了 {len(loaded_tasks)} 个任务")
    else:
        print("✗ 任务数据加载失败")
        return False
    
    return True

def test_backup_functionality():
    """测试备份功能"""
    print("\n=== 测试备份功能 ===")
    
    manager = DataStorageManager()
    
    # 创建测试数据
    backup_test_data = {
        'timestamp': datetime.now().isoformat(),
        'purpose': '备份功能测试',
        'data': list(range(100))
    }
    
    # 保存数据并创建备份
    if manager.save_data(backup_test_data, 'backup_test.json', backup=True):
        print("✓ 数据保存和备份创建成功")
    else:
        print("✗ 数据保存和备份创建失败")
        return False
    
    # 检查备份目录
    backup_dir = manager.backup_dir / 'daily'
    if backup_dir.exists():
        print("✓ 备份目录存在")
        
        # 检查是否有备份文件
        backup_files = list(backup_dir.rglob('*backup_test.json*'))
        if backup_files:
            print(f"✓ 找到 {len(backup_files)} 个备份文件")
        else:
            print("✗ 未找到备份文件")
            return False
    else:
        print("✗ 备份目录不存在")
        return False
    
    return True

def test_integrity_verification():
    """测试完整性验证"""
    print("\n=== 测试完整性验证 ===")
    
    manager = DataStorageManager()
    
    # 创建测试数据
    integrity_data = {
        'timestamp': datetime.now().isoformat(),
        'test_type': '完整性验证',
        'values': ['A', 'B', 'C', 'D']
    }
    
    # 保存数据
    if manager.save_data(integrity_data, 'integrity_test.json'):
        print("✓ 完整性测试数据保存成功")
    else:
        print("✗ 完整性测试数据保存失败")
        return False
    
    # 验证文件完整性
    file_path = manager.base_dir / 'integrity_test.json.gz'
    if manager._verify_file_integrity(file_path):
        print("✓ 文件完整性验证通过")
    else:
        print("✗ 文件完整性验证失败")
        return False
    
    # 故意损坏文件
    try:
        with open(file_path, 'wb') as f:
            f.write(b'corrupted data')
        print("✓ 文件已故意损坏")
    except Exception as e:
        print(f"✗ 文件损坏操作失败: {e}")
        return False
    
    # 再次验证完整性（应该失败）
    if not manager._verify_file_integrity(file_path):
        print("✓ 损坏文件检测成功")
    else:
        print("✗ 损坏文件检测失败")
        return False
    
    return True

def test_storage_stats():
    """测试存储统计"""
    print("\n=== 测试存储统计 ===")
    
    manager = DataStorageManager()
    
    # 获取存储统计
    stats = manager.get_storage_stats()
    
    if stats:
        print("✓ 存储统计获取成功")
        print(f"  总文件数: {stats.get('total_files', 0)}")
        print(f"  总大小: {stats.get('total_size', 0)} 字节")
        print(f"  压缩文件数: {stats.get('compressed_files', 0)}")
        print(f"  备份数量: {stats.get('backup_count', 0)}")
        print(f"  备份大小: {stats.get('backup_size', 0)} 字节")
        print(f"  最后备份: {stats.get('last_backup', '无')}")
    else:
        print("✗ 存储统计获取失败")
        return False
    
    return True

def test_export_functionality():
    """测试导出功能"""
    print("\n=== 测试导出功能 ===")
    
    manager = DataStorageManager()
    
    # 创建导出目录
    export_dir = 'test_export'
    
    # 导出数据
    if manager.export_data(export_dir, include_backups=True):
        print("✓ 数据导出成功")
        
        # 检查导出目录
        if os.path.exists(export_dir):
            print("✓ 导出目录存在")
            
            # 检查导出文件
            export_files = []
            for root, dirs, files in os.walk(export_dir):
                for file in files:
                    export_files.append(os.path.join(root, file))
            
            if export_files:
                print(f"✓ 找到 {len(export_files)} 个导出文件")
            else:
                print("✗ 未找到导出文件")
                return False
        else:
            print("✗ 导出目录不存在")
            return False
    else:
        print("✗ 数据导出失败")
        return False
    
    # 清理测试导出目录
    try:
        shutil.rmtree(export_dir)
        print("✓ 测试导出目录已清理")
    except Exception as e:
        print(f"⚠ 清理导出目录失败: {e}")
    
    return True

def run_all_tests():
    """运行所有测试"""
    print("开始测试数据存储管理器...\n")
    
    tests = [
        ("基本操作测试", test_basic_operations),
        ("任务数据操作测试", test_task_operations),
        ("备份功能测试", test_backup_functionality),
        ("完整性验证测试", test_integrity_verification),
        ("存储统计测试", test_storage_stats),
        ("导出功能测试", test_export_functionality)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✓ {test_name} - 通过")
                passed += 1
            else:
                print(f"✗ {test_name} - 失败")
                failed += 1
        except Exception as e:
            print(f"✗ {test_name} - 异常: {e}")
            failed += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"总计: {passed + failed}")
    
    if failed == 0:
        print("🎉 所有测试通过！数据存储管理器功能正常。")
        return True
    else:
        print("❌ 部分测试失败，请检查实现。")
        return False

if __name__ == "__main__":
    # 运行测试
    success = run_all_tests()
    
    # 清理测试文件
    print("\n=== 清理测试文件 ===")
    test_files = [
        'data/test_basic.json.gz',
        'data/tasks/test_tasks.json.gz',
        'data/backup_test.json.gz',
        'data/integrity_test.json.gz',
        'data/metadata.json'
    ]
    
    cleaned = 0
    for file_path in test_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✓ 清理: {file_path}")
                cleaned += 1
        except Exception as e:
            print(f"✗ 清理失败 {file_path}: {e}")
    
    print(f"清理了 {cleaned} 个测试文件")
    
    sys.exit(0 if success else 1)