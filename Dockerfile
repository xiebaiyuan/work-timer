# 使用官方的 Python Alpine 镜像
FROM python:3.8-alpine

# 设置工作目录
WORKDIR /app

# 安装必要的依赖
RUN apk add --no-cache build-base

# 复制项目的依赖文件并安装依赖
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV FLASK_APP=app.py

# 运行应用
CMD ["flask", "run", "--host=0.0.0.0"]