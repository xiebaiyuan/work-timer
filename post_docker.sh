#!/bin/bash
# mac上发布arm x64双版本docker

# 设置变量
IMAGE_NAME="work-timer"
TAG=$(date +"%Y%m%d%H%M")
DOCKERHUB_USERNAME="xiebaiyuan"  # 请替换为你的DockerHub用户名

# 确保已启用buildx
docker buildx inspect --bootstrap

# 创建一个新的构建器实例（如果不存在）
if ! docker buildx ls | grep -q "mybuilder"; then
  docker buildx create --name mybuilder --use
fi

# 构建并推送多架构镜像
echo "构建并推送 $IMAGE_NAME:$TAG 和 $IMAGE_NAME:latest 的ARM64和AMD64版本..."
docker buildx build --platform linux/amd64,linux/arm64 \
  -t $DOCKERHUB_USERNAME/$IMAGE_NAME:$TAG \
  -t $DOCKERHUB_USERNAME/$IMAGE_NAME:latest \
  --push .

echo "多架构镜像已成功构建并推送到DockerHub"

# 显示推送的镜像信息
echo "镜像详情:"
echo "- $DOCKERHUB_USERNAME/$IMAGE_NAME:$TAG"
echo "- $DOCKERHUB_USERNAME/$IMAGE_NAME:latest"

# 可以检查镜像的架构信息
echo "你可以通过以下命令检查镜像的架构信息："
echo "docker buildx imagetools inspect $DOCKERHUB_USERNAME/$IMAGE_NAME:latest"
