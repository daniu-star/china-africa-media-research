#!/usr/bin/env python3
"""
Bright Data Zone配置测试工具
用于检查当前MCP配置中的Zone设置
"""

import json
import os

def check_current_config():
    """检查当前MCP配置状态"""
    print("=== Bright Data Zone配置检查 ===")
    print("当前错误信息显示Zone设置为: 'unblocker'")
    print("")
    
    print("可用的Zone类型:")
    print("1. 'residential' - 住宅代理IP (推荐)")
    print("2. 'datacenter' - 数据中心代理")
    print("3. 'mobile' - 移动网络代理")
    print("")
    
    print("配置步骤:")
    print("1. 打开你的MCP配置界面")
    print("2. 找到Zone或zone字段")
    print("3. 将值从'custom'或'unblocker'改为'residential'")
    print("4. 保存配置并重新加载")
    print("")
    
    print("验证方法:")
    print("- 重新运行测试命令")
    print("- 如果不再出现'zone not found'错误，说明配置成功")
    print("- 如果仍有错误，尝试'datacenter'或'mobile'")
    
    return {
        "current_zone": "unblocker",
        "recommended_zones": ["residential", "datacenter", "mobile"],
        "status": "需要更新配置"
    }

def create_config_example():
    """创建配置示例"""
    config_example = {
        "brightdata_config_example": {
            "zone": "residential",  # 正确的Zone设置
            "api_key": "your_api_key_here",
            "description": "使用residential zone进行非洲新闻爬虫"
        }
    }
    
    with open("brightdata_config_example.json", "w", encoding="utf-8") as f:
        json.dump(config_example, f, indent=2, ensure_ascii=False)
    
    print("已创建配置示例文件: brightdata_config_example.json")
    return config_example

if __name__ == "__main__":
    print("Bright Data Zone配置检查工具")
    print("=" * 50)
    
    # 检查当前配置状态
    status = check_current_config()
    
    # 创建配置示例
    example = create_config_example()
    
    print("\n下一步操作:")
    print("1. 按照上述步骤更新MCP配置中的Zone字段")
    print("2. 将Zone值改为'residential'")
    print("3. 保存并重新加载配置")
    print("4. 重新测试Bright Data工具")
    print("")
    print("如果仍有问题，请检查:")
    print("- API密钥是否正确")
    print("- 账户是否有足够的配额")
    print("- 网络连接是否正常")