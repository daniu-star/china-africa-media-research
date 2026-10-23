#!/usr/bin/env python3
"""
统一数据存储管理器
提供数据存储、备份、压缩、加密和恢复功能
"""

import json
import os
import shutil
import gzip
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

class DataStorageManager:
    """统一数据存储管理器"""
    
    def __init__(self, base_dir: str = "data", backup_dir: str = "backup"):
        """
        初始化数据存储管理器
        
        Args:
            base_dir: 基础数据目录
            backup_dir: 备份目录
        """
        self.base_dir = Path(base_dir)
        self.backup_dir = Path(backup_dir)
        
        # 创建必要的目录结构
        self._create_directories()
        
        # 设置日志
        self.logger = self._setup_logging()
        
        # 备份策略配置
        self.backup_config = {
            'daily_backups': 7,      # 保留7天每日备份
            'weekly_backups': 4,     # 保留4周每周备份
            'monthly_backups': 12,    # 保留12月每月备份
            'compression': True,      # 启用压缩
            'encryption': False       # 暂时禁用加密
        }
    
    def _create_directories(self):
        """创建必要的目录结构"""
        directories = [
            self.base_dir,
            self.backup_dir,
            self.base_dir / 'tasks',
            self.base_dir / 'results',
            self.base_dir / 'events',
            self.base_dir / 'logs',
            self.backup_dir / 'daily',
            self.backup_dir / 'weekly',
            self.backup_dir / 'monthly'
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志系统"""
        logger = logging.getLogger('DataStorageManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # 文件处理器
            log_file = self.base_dir / 'logs' / 'storage_manager.log'
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def save_data(self, data: Any, filename: str, subdir: str = "", 
                  compress: bool = True, backup: bool = True) -> bool:
        """
        保存数据到文件
        
        Args:
            data: 要保存的数据
            filename: 文件名
            subdir: 子目录
            compress: 是否压缩
            backup: 是否创建备份
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 构建完整文件路径
            if subdir:
                file_path = self.base_dir / subdir / filename
            else:
                file_path = self.base_dir / filename
            
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存数据
            if compress:
                # 压缩保存
                compressed_path = Path(f"{file_path}.gz")
                with gzip.open(compressed_path, 'wt', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                actual_path = compressed_path
            else:
                # 普通保存
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                actual_path = file_path
            
            # 计算文件哈希值用于完整性验证
            file_hash = self._calculate_file_hash(actual_path)
            
            # 记录元数据
            metadata = {
                'filename': filename,
                'file_path': str(actual_path),
                'size': os.path.getsize(actual_path),
                'hash': file_hash,
                'timestamp': datetime.now().isoformat(),
                'compressed': compress,
                'backup_created': False
            }
            
            # 保存元数据
            self._save_metadata(metadata)
            
            # 创建备份
            if backup:
                backup_success = self._create_backup(actual_path, metadata)
                metadata['backup_created'] = backup_success
                self._save_metadata(metadata)
            
            self.logger.info(f"数据已保存到: {actual_path} (大小: {metadata['size']} 字节)")
            return True
            
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")
            return False
    
    def load_data(self, filename: str, subdir: str = "", 
                  compressed: bool = True) -> Optional[Any]:
        """
        从文件加载数据
        
        Args:
            filename: 文件名
            subdir: 子目录
            compressed: 是否压缩文件
            
        Returns:
            Optional[Any]: 加载的数据，失败返回None
        """
        try:
            # 构建完整文件路径
            if subdir:
                file_path = self.base_dir / subdir / filename
            else:
                file_path = self.base_dir / filename
            
            # 检查压缩文件
            if compressed and os.path.exists(f"{file_path}.gz"):
                file_path = Path(f"{file_path}.gz")
            
            if not file_path.exists():
                self.logger.warning(f"文件不存在: {file_path}")
                return None
            
            # 验证文件完整性
            if not self._verify_file_integrity(file_path):
                self.logger.warning(f"文件完整性验证失败: {file_path}")
                # 尝试从备份恢复
                restored = self._restore_from_backup(file_path)
                if not restored:
                    return None
            
            # 加载数据
            if str(file_path).endswith('.gz'):
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            self.logger.info(f"数据已从 {file_path} 加载")
            return data
            
        except Exception as e:
            self.logger.error(f"加载数据失败: {e}")
            return None
    
    def _create_backup(self, file_path: Path, metadata: Dict) -> bool:
        """创建备份文件"""
        try:
            # 确定备份类型
            now = datetime.now()
            
            # 每日备份
            daily_backup_dir = self.backup_dir / 'daily' / now.strftime('%Y%m%d')
            daily_backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 每周备份（每周日）
            if now.weekday() == 6:  # 周日
                weekly_backup_dir = self.backup_dir / 'weekly' / now.strftime('%Y%W')
                weekly_backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 每月备份（每月第一天）
            if now.day == 1:
                monthly_backup_dir = self.backup_dir / 'monthly' / now.strftime('%Y%m')
                monthly_backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制文件到备份目录
            backup_filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{file_path.name}"
            
            # 确保file_path是Path对象
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            # 每日备份
            daily_backup_path = daily_backup_dir / backup_filename
            shutil.copy2(file_path, daily_backup_path)
            
            # 每周备份
            if now.weekday() == 6:
                weekly_backup_path = weekly_backup_dir / backup_filename
                shutil.copy2(file_path, weekly_backup_path)
            
            # 每月备份
            if now.day == 1:
                monthly_backup_path = monthly_backup_dir / backup_filename
                shutil.copy2(file_path, monthly_backup_path)
            
            # 清理旧备份
            self._cleanup_old_backups()
            
            self.logger.info(f"备份已创建: {backup_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建备份失败: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """清理旧备份文件"""
        try:
            now = datetime.now()
            
            # 清理每日备份
            daily_dir = self.backup_dir / 'daily'
            if daily_dir.exists():
                for backup_date in daily_dir.iterdir():
                    if backup_date.is_dir():
                        backup_time = datetime.strptime(backup_date.name, '%Y%m%d')
                        if (now - backup_time).days > self.backup_config['daily_backups']:
                            shutil.rmtree(backup_date)
                            self.logger.info(f"清理旧每日备份: {backup_date.name}")
            
            # 清理每周备份
            weekly_dir = self.backup_dir / 'weekly'
            if weekly_dir.exists():
                for backup_week in weekly_dir.iterdir():
                    if backup_week.is_dir():
                        # 解析周数
                        year = int(backup_week.name[:4])
                        week = int(backup_week.name[4:])
                        # 计算该周的第一天
                        first_day = datetime.strptime(f'{year}-W{week}-1', '%Y-W%W-%w')
                        if (now - first_day).days > self.backup_config['weekly_backups'] * 7:
                            shutil.rmtree(backup_week)
                            self.logger.info(f"清理旧每周备份: {backup_week.name}")
            
            # 清理每月备份
            monthly_dir = self.backup_dir / 'monthly'
            if monthly_dir.exists():
                for backup_month in monthly_dir.iterdir():
                    if backup_month.is_dir():
                        backup_time = datetime.strptime(backup_month.name, '%Y%m')
                        months_diff = (now.year - backup_time.year) * 12 + (now.month - backup_time.month)
                        if months_diff > self.backup_config['monthly_backups']:
                            shutil.rmtree(backup_month)
                            self.logger.info(f"清理旧每月备份: {backup_month.name}")
            
        except Exception as e:
            self.logger.error(f"清理备份失败: {e}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.error(f"计算文件哈希失败: {e}")
            return ""
    
    def _verify_file_integrity(self, file_path: Path) -> bool:
        """验证文件完整性"""
        try:
            # 检查文件是否存在
            if not file_path.exists():
                return False
            
            # 检查文件大小
            if file_path.stat().st_size == 0:
                return False
            
            # 验证文件格式（尝试解析JSON）
            if str(file_path).endswith('.gz'):
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    json.load(f)  # 尝试解析
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)  # 尝试解析
            
            return True
            
        except Exception:
            return False
    
    def _restore_from_backup(self, original_path: Path) -> bool:
        """从备份恢复文件"""
        try:
            # 查找最近的备份
            backup_files = []
            
            # 检查每日备份
            daily_dir = self.backup_dir / 'daily'
            if daily_dir.exists():
                for date_dir in sorted(daily_dir.iterdir(), reverse=True):
                    if date_dir.is_dir():
                        for backup_file in sorted(date_dir.iterdir(), reverse=True):
                            if original_path.name in backup_file.name:
                                backup_files.append(backup_file)
            
            # 尝试恢复
            for backup_file in backup_files:
                try:
                    shutil.copy2(backup_file, original_path)
                    self.logger.info(f"从备份恢复文件: {backup_file} -> {original_path}")
                    return True
                except Exception:
                    continue
            
            self.logger.error(f"无法从备份恢复文件: {original_path}")
            return False
            
        except Exception as e:
            self.logger.error(f"恢复备份失败: {e}")
            return False
    
    def _save_metadata(self, metadata: Dict):
        """保存文件元数据"""
        try:
            metadata_file = self.base_dir / 'metadata.json'
            
            # 加载现有元数据
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    all_metadata = json.load(f)
            else:
                all_metadata = {}
            
            # 更新元数据
            all_metadata[metadata['filename']] = metadata
            
            # 保存元数据
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(all_metadata, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存元数据失败: {e}")
    
    def list_files(self, subdir: str = "", pattern: str = "*") -> List[str]:
        """
        列出指定目录下的文件
        
        Args:
            subdir: 子目录路径
            pattern: 文件匹配模式
            
        Returns:
            List[str]: 文件路径列表
        """
        try:
            # 构建目录路径
            if subdir:
                target_dir = self.base_dir / subdir
            else:
                target_dir = self.base_dir
            
            if not target_dir.exists():
                return []
            
            # 列出匹配的文件
            files = []
            for file_path in target_dir.rglob(pattern):
                if file_path.is_file():
                    # 返回相对于基础目录的相对路径
                    relative_path = file_path.relative_to(self.base_dir)
                    files.append(str(relative_path))
            
            # 按修改时间排序（最新的在前）
            files.sort(key=lambda x: (self.base_dir / x).stat().st_mtime, reverse=True)
            
            return files
            
        except Exception as e:
            self.logger.error(f"列出文件失败: {e}")
            return []
    
    def get_storage_stats(self) -> Dict:
        """获取存储统计信息"""
        try:
            stats = {
                'total_files': 0,
                'total_size': 0,
                'compressed_files': 0,
                'backup_count': 0,
                'backup_size': 0,
                'last_backup': None
            }
            
            # 统计主数据目录
            for file_path in self.base_dir.rglob('*'):
                if file_path.is_file():
                    stats['total_files'] += 1
                    stats['total_size'] += file_path.stat().st_size
                    if file_path.suffix == '.gz':
                        stats['compressed_files'] += 1
            
            # 统计备份目录
            for backup_path in self.backup_dir.rglob('*'):
                if backup_path.is_file():
                    stats['backup_count'] += 1
                    stats['backup_size'] += backup_path.stat().st_size
            
            # 查找最后备份时间
            backup_files = list(self.backup_dir.rglob('*'))
            if backup_files:
                latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
                stats['last_backup'] = datetime.fromtimestamp(latest_backup.stat().st_mtime).isoformat()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取存储统计失败: {e}")
            return {}
    
    def export_data(self, output_dir: str, include_backups: bool = False) -> bool:
        """导出数据到指定目录"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 导出主数据
            shutil.copytree(self.base_dir, output_path / 'data', dirs_exist_ok=True)
            
            # 导出备份
            if include_backups:
                shutil.copytree(self.backup_dir, output_path / 'backup', dirs_exist_ok=True)
            
            # 生成导出报告
            export_report = {
                'export_timestamp': datetime.now().isoformat(),
                'source_directory': str(self.base_dir),
                'destination_directory': str(output_path),
                'include_backups': include_backups,
                'stats': self.get_storage_stats()
            }
            
            with open(output_path / 'export_report.json', 'w', encoding='utf-8') as f:
                json.dump(export_report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"数据已导出到: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            return False

# 便捷函数
def create_storage_manager() -> DataStorageManager:
    """创建数据存储管理器实例"""
    return DataStorageManager()

def save_task_data(tasks: List[Dict], filename: str = "tasks.json") -> bool:
    """保存任务数据"""
    manager = create_storage_manager()
    return manager.save_data({'tasks': tasks}, filename, 'tasks')

def load_task_data(filename: str = "tasks.json") -> Optional[List[Dict]]:
    """加载任务数据"""
    manager = create_storage_manager()
    data = manager.load_data(filename, 'tasks')
    return data.get('tasks', []) if data else None

def save_crawler_results(results: List[Dict], filename: str) -> bool:
    """保存爬虫结果"""
    manager = create_storage_manager()
    return manager.save_data({'results': results}, filename, 'results')

def load_crawler_results(filename: str) -> Optional[List[Dict]]:
    """加载爬虫结果"""
    manager = create_storage_manager()
    data = manager.load_data(filename, 'results')
    return data.get('results', []) if data else None

if __name__ == "__main__":
    # 测试数据存储管理器
    manager = DataStorageManager()
    
    # 测试数据保存
    test_data = {
        'test_timestamp': datetime.now().isoformat(),
        'message': '这是测试数据',
        'status': 'success'
    }
    
    if manager.save_data(test_data, 'test_data.json'):
        print("✓ 数据保存成功")
        
        # 测试数据加载
        loaded_data = manager.load_data('test_data.json')
        if loaded_data:
            print("✓ 数据加载成功")
            print(f"加载的数据: {loaded_data}")
        
        # 显示存储统计
        stats = manager.get_storage_stats()
        print(f"存储统计: {stats}")
    else:
        print("✗ 数据保存失败")