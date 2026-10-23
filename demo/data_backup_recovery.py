"""
数据备份和恢复策略系统
实现自动化的数据备份、版本管理和灾难恢复功能
"""

import json
import os
import shutil
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import zipfile

class DataBackupRecovery:
    """数据备份和恢复管理系统"""
    
    def __init__(self, data_dir: str = "data", backup_dir: str = "backups"):
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        self.backup_config = {
            "full_backup_interval": 7,  # 天
            "incremental_backup_interval": 1,  # 天
            "retention_period": 30,  # 天
            "max_backup_versions": 10,
            "backup_types": ["full", "incremental", "differential"],
            "compression": True,
            "encryption": False
        }
        
        # 确保目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
    
    def create_backup(self, backup_type: str = "incremental", description: str = "") -> Dict[str, Any]:
        """创建数据备份"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{backup_type}_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_id)
        
        # 创建备份元数据
        metadata = {
            "backup_id": backup_id,
            "type": backup_type,
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "data_files": [],
            "total_size": 0,
            "file_count": 0,
            "checksums": {}
        }
        
        # 备份数据文件
        if backup_type == "full":
            # 完整备份所有数据文件
            for root, dirs, files in os.walk(self.data_dir):
                for file in files:
                    if file.endswith(('.json', '.csv', '.txt', '.db')):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, self.data_dir)
                        backup_file_path = os.path.join(backup_path, relative_path)
                        
                        # 确保目录存在
                        os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
                        
                        # 复制文件
                        shutil.copy2(file_path, backup_file_path)
                        
                        # 计算文件信息
                        file_size = os.path.getsize(file_path)
                        file_checksum = self._calculate_checksum(file_path)
                        
                        metadata["data_files"].append({
                            "path": relative_path,
                            "size": file_size,
                            "checksum": file_checksum,
                            "modified_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        })
                        metadata["total_size"] += file_size
                        metadata["file_count"] += 1
                        metadata["checksums"][relative_path] = file_checksum
        
        elif backup_type == "incremental":
            # 增量备份：只备份自上次备份后修改的文件
            last_backup_time = self._get_last_backup_time()
            
            for root, dirs, files in os.walk(self.data_dir):
                for file in files:
                    if file.endswith(('.json', '.csv', '.txt', '.db')):
                        file_path = os.path.join(root, file)
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        # 如果文件在最后一次备份后修改过
                        if last_backup_time is None or file_mtime > last_backup_time:
                            relative_path = os.path.relpath(file_path, self.data_dir)
                            backup_file_path = os.path.join(backup_path, relative_path)
                            
                            os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
                            shutil.copy2(file_path, backup_file_path)
                            
                            file_size = os.path.getsize(file_path)
                            file_checksum = self._calculate_checksum(file_path)
                            
                            metadata["data_files"].append({
                                "path": relative_path,
                                "size": file_size,
                                "checksum": file_checksum,
                                "modified_time": file_mtime.isoformat(),
                                "reason": "modified" if last_backup_time else "new"
                            })
                            metadata["total_size"] += file_size
                            metadata["file_count"] += 1
                            metadata["checksums"][relative_path] = file_checksum
        
        # 压缩备份
        if self.backup_config["compression"]:
            zip_filename = f"{backup_path}.zip"
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_path)
                        zipf.write(file_path, arcname)
            
            # 删除原始备份目录
            shutil.rmtree(backup_path)
            backup_path = zip_filename
        
        # 保存备份元数据
        metadata["backup_path"] = backup_path
        metadata_file = os.path.join(self.backup_dir, f"{backup_id}_metadata.json")
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"备份创建成功: {backup_id}")
        print(f"备份文件数量: {metadata['file_count']}")
        print(f"备份总大小: {metadata['total_size'] / 1024 / 1024:.2f} MB")
        
        return metadata
    
    def restore_backup(self, backup_id: str, target_dir: str = None) -> bool:
        """恢复数据备份"""
        
        if target_dir is None:
            target_dir = self.data_dir
        
        # 查找备份元数据文件
        metadata_file = os.path.join(self.backup_dir, f"{backup_id}_metadata.json")
        
        if not os.path.exists(metadata_file):
            print(f"备份元数据文件不存在: {metadata_file}")
            return False
        
        # 读取元数据
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        backup_path = metadata["backup_path"]
        
        if not os.path.exists(backup_path):
            print(f"备份文件不存在: {backup_path}")
            return False
        
        # 解压备份文件
        temp_dir = os.path.join(self.backup_dir, f"temp_restore_{backup_id}")
        
        try:
            if backup_path.endswith('.zip'):
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
            else:
                # 如果是目录备份，直接复制
                shutil.copytree(backup_path, temp_dir)
            
            # 恢复文件到目标目录
            for file_info in metadata["data_files"]:
                source_path = os.path.join(temp_dir, file_info["path"])
                target_path = os.path.join(target_dir, file_info["path"])
                
                # 确保目标目录存在
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                # 复制文件
                shutil.copy2(source_path, target_path)
                
                # 验证文件完整性
                restored_checksum = self._calculate_checksum(target_path)
                if restored_checksum != file_info["checksum"]:
                    print(f"警告: 文件校验和不匹配: {file_info['path']}")
            
            print(f"备份恢复成功: {backup_id}")
            print(f"恢复文件数量: {len(metadata['data_files'])}")
            
            return True
            
        except Exception as e:
            print(f"恢复备份时出错: {e}")
            return False
        
        finally:
            # 清理临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        
        backups = []
        
        for file in os.listdir(self.backup_dir):
            if file.endswith('_metadata.json'):
                metadata_file = os.path.join(self.backup_dir, file)
                
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    # 检查备份文件是否存在
                    if os.path.exists(metadata["backup_path"]):
                        backups.append(metadata)
                    else:
                        print(f"备份文件不存在，跳过: {metadata['backup_id']}")
                        
                except Exception as e:
                    print(f"读取备份元数据失败: {file}, 错误: {e}")
        
        # 按时间排序
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return backups
    
    def cleanup_old_backups(self) -> int:
        """清理过期备份"""
        
        backups = self.list_backups()
        cutoff_time = datetime.now() - timedelta(days=self.backup_config["retention_period"])
        
        deleted_count = 0
        
        for backup in backups:
            backup_time = datetime.fromisoformat(backup["timestamp"])
            
            if backup_time < cutoff_time:
                # 删除备份文件和元数据
                try:
                    if os.path.exists(backup["backup_path"]):
                        os.remove(backup["backup_path"])
                    
                    metadata_file = os.path.join(self.backup_dir, f"{backup['backup_id']}_metadata.json")
                    if os.path.exists(metadata_file):
                        os.remove(metadata_file)
                    
                    print(f"删除过期备份: {backup['backup_id']}")
                    deleted_count += 1
                    
                except Exception as e:
                    print(f"删除备份失败: {backup['backup_id']}, 错误: {e}")
        
        return deleted_count
    
    def verify_data_integrity(self) -> Dict[str, Any]:
        """验证数据完整性"""
        
        integrity_report = {
            "verified_at": datetime.now().isoformat(),
            "total_files": 0,
            "corrupted_files": [],
            "missing_files": [],
            "integrity_score": 1.0
        }
        
        # 获取最新备份
        backups = self.list_backups()
        if not backups:
            integrity_report["status"] = "no_backups_available"
            return integrity_report
        
        latest_backup = backups[0]
        
        # 验证文件完整性
        for file_info in latest_backup["data_files"]:
            file_path = os.path.join(self.data_dir, file_info["path"])
            
            if not os.path.exists(file_path):
                integrity_report["missing_files"].append(file_info["path"])
            else:
                current_checksum = self._calculate_checksum(file_path)
                if current_checksum != file_info["checksum"]:
                    integrity_report["corrupted_files"].append({
                        "path": file_info["path"],
                        "expected_checksum": file_info["checksum"],
                        "actual_checksum": current_checksum
                    })
            
            integrity_report["total_files"] += 1
        
        # 计算完整性评分
        if integrity_report["total_files"] > 0:
            integrity_report["integrity_score"] = 1.0 - (
                len(integrity_report["corrupted_files"]) + 
                len(integrity_report["missing_files"])
            ) / integrity_report["total_files"]
        
        integrity_report["status"] = "verified"
        
        return integrity_report
    
    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        
        hash_md5 = hashlib.md5()
        
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        except Exception as e:
            print(f"计算校验和失败: {file_path}, 错误: {e}")
            return ""
        
        return hash_md5.hexdigest()
    
    def _get_last_backup_time(self) -> Optional[datetime]:
        """获取最后一次备份的时间"""
        
        backups = self.list_backups()
        if backups:
            return datetime.fromisoformat(backups[0]["timestamp"])
        
        return None

def main():
    """主函数"""
    
    print("=" * 60)
    print("数据备份和恢复策略系统")
    print("=" * 60)
    
    backup_system = DataBackupRecovery()
    
    # 创建完整备份
    print("\n1. 创建完整备份...")
    full_backup = backup_system.create_backup("full", "系统初始化完整备份")
    
    # 列出所有备份
    print("\n2. 列出所有备份...")
    backups = backup_system.list_backups()
    
    for i, backup in enumerate(backups):
        print(f"  {i+1}. {backup['backup_id']} - {backup['type']} - {backup['file_count']} 个文件")
    
    # 验证数据完整性
    print("\n3. 验证数据完整性...")
    integrity_report = backup_system.verify_data_integrity()
    
    print(f"  完整性评分: {integrity_report['integrity_score']:.2f}")
    print(f"  损坏文件: {len(integrity_report['corrupted_files'])} 个")
    print(f"  缺失文件: {len(integrity_report['missing_files'])} 个")
    
    # 备份策略报告
    print("\n4. 备份策略报告:")
    print(f"  完整备份间隔: {backup_system.backup_config['full_backup_interval']} 天")
    print(f"  增量备份间隔: {backup_system.backup_config['incremental_backup_interval']} 天")
    print(f"  保留期限: {backup_system.backup_config['retention_period']} 天")
    print(f"  最大备份版本: {backup_system.backup_config['max_backup_versions']}")
    
    # 保存备份清单
    backup_list_file = os.path.join(backup_system.backup_dir, "backup_inventory.json")
    with open(backup_list_file, 'w', encoding='utf-8') as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_backups": len(backups),
            "backups": backups,
            "integrity_report": integrity_report
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n备份清单已保存到: {backup_list_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()