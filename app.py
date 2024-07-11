from flask import Flask, request, jsonify, send_from_directory
import redis
import os
from datetime import datetime, timedelta
from dateutil import parser, tz

app = Flask(__name__)

# 配置 Redis
redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = os.getenv('REDIS_PORT', 6379)
redis_db = redis.StrictRedis(host=redis_host, port=redis_port, db=0, decode_responses=True)

# 默认路径返回 HTML 网页
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/save', methods=['POST'])
def save_device():
    data = request.json
    device_name = data.get('device_name')

    if not device_name:
        return jsonify({'error': 'Invalid input'}), 400

    # 存储数据到 Redis，使用 UTC 时间
    timestamp = datetime.utcnow().isoformat() + 'Z'
    redis_db.rpush(device_name, timestamp)

    return jsonify({'message': 'Data saved successfully'}), 200

@app.route('/query', methods=['GET'])
def query_device():
    device_name = request.args.get('device_name')

    if not device_name:
        return jsonify({'error': 'Invalid input'}), 400

    # 从 Redis 查询数据
    timestamps = redis_db.lrange(device_name, 0, -1)

    # 将 UTC 时间转换为当前时区时间
    current_tz = tz.tzlocal()
    formatted_timestamps = [parser.parse(ts).astimezone(current_tz).strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps]

    # 计算今天最早记录的时间与当前时间的差值
    now = datetime.now(current_tz)
    today_start = datetime(now.year, now.month, now.day, tzinfo=current_tz)
    today_timestamps = [parser.parse(ts).astimezone(current_tz) for ts in timestamps if today_start <= parser.parse(ts).astimezone(current_tz) < today_start + timedelta(days=1)]

    if not today_timestamps:
        return jsonify({'timestamps': formatted_timestamps, 'message': 'No records for today'}), 200

    first_timestamp = min(today_timestamps)
    elapsed_time = now - first_timestamp
    elapsed_time_str = str(elapsed_time).split('.')[0]  # 去掉微秒部分

    return jsonify({'timestamps': formatted_timestamps, 'today_first_timestamp': first_timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'elapsed_time': elapsed_time_str}), 200

@app.route('/query_today_first', methods=['GET'])
def query_today_first():
    device_name = request.args.get('device_name')

    if not device_name:
        return jsonify({'error': 'Invalid input'}), 400

    # 获取当前日期的起始时间和结束时间
    current_tz = tz.tzlocal()
    now = datetime.now(current_tz)
    today_start = datetime(now.year, now.month, now.day, tzinfo=current_tz)

    # 从 Redis 查询数据
    timestamps = redis_db.lrange(device_name, 0, -1)
    today_timestamps = [parser.parse(ts).astimezone(current_tz) for ts in timestamps if today_start <= parser.parse(ts).astimezone(current_tz) < today_start + timedelta(days=1)]

    if not today_timestamps:
        return jsonify({'message': 'No records for today'}), 404

    # 获取今天最早的记录
    first_timestamp = min(today_timestamps)
    elapsed_time = now - first_timestamp
    elapsed_time_str = str(elapsed_time).split('.')[0]  # 去掉微秒部分

    # 返回最早记录的时间和已过时间
    response = {
        'first_timestamp': first_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'elapsed_time': elapsed_time_str
    }

    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)