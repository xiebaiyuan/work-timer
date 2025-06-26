#!/bin/bash

# 本地开发调试启动脚本
echo "🚀 启动工作时间小助手 - 开发模式"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3 未安装，请先安装 Python3"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "app.py" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 设置环境变量
export FLASK_ENV=development
export FLASK_DEBUG=1
export REDIS_HOST=localhost
export REDIS_PORT=6379

echo "📦 检查依赖包..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "🔨 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔌 激活虚拟环境..."
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装依赖
echo "📚 安装依赖包..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt 未找到，手动安装必要依赖..."
    pip install flask redis python-dateutil flask-cors
fi

# 检查Redis是否运行
echo "🔍 检查Redis服务..."
# if ! pgrep -x "redis-server" > /dev/null; then
#     echo "⚠️  Redis服务未运行"
#     echo "🔧 尝试启动Redis..."
    
#     # 尝试不同的Redis启动方式
#     if command -v redis-server &> /dev/null; then
#         redis-server --daemonize yes --port 6379
#         sleep 2
#         if pgrep -x "redis-server" > /dev/null; then
#             echo "✅ Redis已成功启动"
#         else
#             echo "❌ 无法启动Redis，请手动启动Redis服务"
#             echo "   macOS: brew services start redis"
#             echo "   Ubuntu: sudo systemctl start redis"
#             echo "   或者使用Docker: docker run -d -p 6379:6379 redis:alpine"
#             read -p "按Enter继续（如果Redis已在其他方式运行）..."
#         fi
#     else
#         echo "❌ Redis未安装，请先安装Redis"
#         echo "   macOS: brew install redis"
#         echo "   Ubuntu: sudo apt-get install redis-server"
#         echo "   或者使用Docker: docker run -d -p 6379:6379 redis:alpine"
#         read -p "按Enter继续（如果Redis已在其他方式运行）..."
#     fi
# else
#     echo "✅ Redis服务正在运行"
# fi

# 创建本地数据目录
mkdir -p redis-data

echo ""
echo "🌐 启动开发服务器..."
echo "📱 访问地址: http://localhost:5000"
echo "🔧 编辑页面: http://localhost:5000/edit"
echo "🛑 停止服务: Ctrl+C"
echo ""

# 启动Flask应用
python3 app.py
