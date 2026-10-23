#!/bin/bash

# 分布式爬虫部署脚本

echo "开始部署分布式爬虫系统..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 创建数据目录
mkdir -p distributed_data
mkdir -p logs

# 复制环境配置文件
if [ ! -f .env ]; then
    echo "复制环境配置文件..."
    cp .env.example .env
    echo "请编辑 .env 文件配置您的环境变量"
fi

# 构建镜像
echo "构建Docker镜像..."
docker-compose build

# 启动服务
echo "启动分布式爬虫服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

echo ""
echo "部署完成！"
echo ""
echo "服务访问地址："
echo "- 主节点API: http://localhost:8000"
echo "- Redis监控: http://localhost:8081"
echo ""
echo "管理命令："
echo "- 查看日志: docker-compose logs -f"
echo "- 停止服务: docker-compose down"
echo "- 重启服务: docker-compose restart"
echo "- 扩展工作节点: docker-compose up -d --scale worker=4"
echo ""
echo "现在可以开始提交爬虫任务了！"