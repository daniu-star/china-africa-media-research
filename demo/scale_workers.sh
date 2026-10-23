#!/bin/bash

# 工作节点扩展脚本

echo "扩展分布式爬虫工作节点..."

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <工作节点数量>"
    echo "示例: $0 4"
    exit 1
fi

WORKER_COUNT=$1

# 检查Docker Compose是否运行
if ! docker-compose ps | grep -q "Up"; then
    echo "错误: 服务未运行，请先启动服务: docker-compose up -d"
    exit 1
fi

# 扩展工作节点
echo "扩展工作节点到 $WORKER_COUNT 个..."
docker-compose up -d --scale worker=$WORKER_COUNT

# 等待扩展完成
echo "等待扩展完成..."
sleep 5

# 检查扩展结果
echo "当前运行的工作节点:"
docker-compose ps | grep worker

echo ""
echo "工作节点扩展完成！"
echo "当前共有 $WORKER_COUNT 个工作节点运行"