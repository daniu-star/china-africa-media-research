import pandas as pd
import numpy as np
import os

class CooperationDepthFiller:
    def __init__(self, original_file, optimized_file):
        self.original_file = original_file
        self.optimized_file = optimized_file
        self.original_df = None
        self.optimized_df = None
        self.merged_df = None
        
    def load_files(self):
        """读取原始文件和优化结果文件"""
        print(f"读取原始文件: {self.original_file}")
        self.original_df = pd.read_csv(self.original_file, low_memory=False)
        print(f"原始文件记录数: {len(self.original_df)}")
        
        print(f"\n读取优化结果文件: {self.optimized_file}")
        self.optimized_df = pd.read_csv(self.optimized_file)
        print(f"优化结果记录数: {len(self.optimized_df)}")
    
    def merge_and_replace(self):
        """合并数据并替换合作纵深性指数"""
        print("\n合并数据...")
        
        # 验证两个文件记录数相同
        assert len(self.original_df) == len(self.optimized_df), "两个文件记录数不一致"
        print("✓ 两个文件记录数相同")
        
        # 直接按索引合并
        self.merged_df = self.original_df.copy()
        self.merged_df['optimized_cooperation_depth'] = self.optimized_df['optimized_cooperation_depth'].values
        
        print(f"合并后记录数: {len(self.merged_df)}")
        print(f"成功匹配记录数: {self.merged_df['optimized_cooperation_depth'].notna().sum()}")
        print(f"匹配失败记录数: {self.merged_df['optimized_cooperation_depth'].isna().sum()}")
        
        # 替换原始合作纵深性指数
        print("\n替换合作纵深性指数...")
        self.merged_df['cooperation_depth_index'] = self.merged_df['optimized_cooperation_depth']
    
    def validate_data(self):
        """验证数据完整性"""
        print("\n验证数据完整性...")
        
        # 验证记录数不变
        assert len(self.merged_df) == len(self.original_df), "记录数发生变化"
        print("✓ 记录数保持不变")
        
        # 验证其他字段值未改变
        columns_to_check = [col for col in self.original_df.columns if col != 'cooperation_depth_index' and col != 'match_key']
        for col in columns_to_check:
            assert self.merged_df[col].equals(self.original_df[col]), f"字段 {col} 值发生变化"
        print("✓ 其他字段值保持不变")
        
        # 验证合作纵深性指数已更新
        changed_count = (self.merged_df['cooperation_depth_index'] != self.original_df['cooperation_depth_index']).sum()
        print(f"✓ 成功更新 {changed_count} 条记录的合作纵深性指数")
    
    def save_result(self):
        """保存结果文件"""
        print("\n保存结果文件...")
        
        # 清理不需要的列
        final_df = self.merged_df.drop(['match_key', 'optimized_cooperation_depth'], axis=1, errors='ignore')
        
        # 保存到原文件路径
        final_df.to_csv(self.original_file, index=False, encoding='utf-8-sig')
        print(f"✓ 结果已保存到: {self.original_file}")
        
        # 保存备份文件
        backup_file = self.original_file.replace('.csv', '_backup.csv')
        self.original_df.to_csv(backup_file, index=False, encoding='utf-8-sig')
        print(f"✓ 原始文件已备份到: {backup_file}")
    
    def run(self):
        """执行完整的填充流程"""
        print("开始填充优化后的合作纵深性指数...")
        
        self.load_files()
        self.merge_and_replace()
        self.validate_data()
        self.save_result()
        
        print("\n填充完成!")

# 主函数
if __name__ == "__main__":
    # 定义文件路径
    original_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_complete_features.csv'
    optimized_file = 'c:/Users/13067/Desktop/论文/非洲/demo/合作纵深性优化结果/合作纵深性优化结果.csv'
    
    # 创建填充器实例
    filler = CooperationDepthFiller(original_file, optimized_file)
    
    # 执行填充流程
    filler.run()
