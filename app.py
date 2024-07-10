from flask import Flask, request, jsonify
import redis
import os

app = Flask(__name__)

# 配置 Redis
redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = os.getenv('REDIS_PORT', 6379)
redis_db = redis.StrictRedis(host=redis_host, port=redis_port, db=0, decode_responses=True)


@app.route('/save', methods=['POST'])
def save_device():
    data = request.json
    device_name = data.get('device_name')
    timestamp = data.get('timestamp')

    if not device_name or not timestamp:
        return jsonify({'error': 'Invalid input'}), 400

    # 存储数据到 Redis
    redis_db.rpush(device_name, timestamp)

    return jsonify({'message': 'Data saved successfully'}), 200


@app.route('/query', methods=['GET'])
def query_device():
    device_name = request.args.get('device_name')

    if not device_name:
        return jsonify({'error': 'Invalid input'}), 400

    # 从 Redis 查询数据
    timestamps = redis_db.lrange(device_name, 0, -1)

    return jsonify(timestamps), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
