#!/bin/bash

# work-timer 启动脚本
echo "正在启动 work-timer..."

# 检查是否存在 redis-data 目录，如果不存在则创建
if [ ! -d "redis-data" ]; then
    echo "创建 Redis 数据目录..."
    mkdir -p redis-data
    # 设置正确的权限（Redis在Docker中以用户ID 999运行）
    chmod 755 redis-data
fi

# 检查 Docker 和 docker-compose 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: docker-compose 未安装，请先安装 docker-compose"
    exit 1
fi

# 启动服务
echo "启动 Docker 服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 5

# 检查服务状态
if docker-compose ps | grep -q "Up"; then
    echo "✅ 服务启动成功！"
    echo "📱 访问地址: http://localhost:8000"
    echo "🔧 编辑页面: http://localhost:8000/edit"
    echo "📊 API文档: 请查看 README.md"
    echo ""
    echo "🗂️  Redis数据保存在: ./redis-data/"
    echo "📝 查看日志: docker-compose logs -f"
    echo "🛑 停止服务: docker-compose down"
else
    echo "❌ 服务启动失败，请检查日志："
    docker-compose logs
fi
