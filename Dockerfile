# 使用官方的 Python 基础镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 复制项目的依赖文件并安装依赖
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV FLASK_APP=app.py

# 运行应用
CMD ["flask", "run", "--host=0.0.0.0"]