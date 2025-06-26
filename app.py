from flask import Flask, request, jsonify, send_from_directory
import redis
import os
from datetime import datetime, timedelta
from dateutil import parser, tz
from flask_cors import CORS
import re
import json

app = Flask(__name__)

def parse_record(record_str):
    """
    解析记录，支持新旧格式
    新格式: {"timestamp": "...", "tag": "..."}
    旧格式: "2023-01-01T00:00:00Z"
    """
    try:
        # 尝试解析为JSON（新格式）
        record = json.loads(record_str)
        if isinstance(record, dict) and 'timestamp' in record:
            return {
                'timestamp': record['timestamp'],
                'tag': record.get('tag', '签到')
            }
    except (json.JSONDecodeError, TypeError):
        pass
    
    # 如果不是JSON或解析失败，当作旧格式处理
    return {
        'timestamp': record_str,
        'tag': '签到'  # 旧记录默认标记为签到
    }

# 自定义CORS处理
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    # 更精确地匹配xiebaiyuan的主域和子域
    if origin and (re.match(r'https?://([^.]+\.)*xiebaiyuan\.[^.]+', origin) or 
                  origin in ['http://allowed-domain.com', 'http://localhost:3000']):
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# 配置 Redis
redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = os.getenv('REDIS_PORT', 6379)
redis_db = redis.StrictRedis(host=redis_host, port=redis_port, db=0, decode_responses=True)


# 默认路径返回 HTML 网页
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/edit')
def delete_page():
    return send_from_directory('static', 'edit_record.html')


@app.route('/save', methods=['POST'])
def save_device():
    data = request.json
    device_name = data.get('device_name')
    tag = data.get('tag', '签到')  # 默认标记为"签到"

    if not device_name:
        return jsonify({'error': 'Invalid input'}), 400

    # 存储数据到 Redis，使用 UTC 时间，包含标记
    timestamp = datetime.utcnow().isoformat() + 'Z'
    record = {
        'timestamp': timestamp,
        'tag': tag
    }
    redis_db.rpush(device_name, json.dumps(record, ensure_ascii=False))

    return jsonify({'message': 'Data saved successfully', 'tag': tag}), 200


@app.route('/query', methods=['GET'])
def query_device():
    device_name = request.args.get('device_name')

    if not device_name:
        return jsonify({'error': 'Invalid input'}), 400

    # 从 Redis 查询数据
    raw_records = redis_db.lrange(device_name, 0, -1)
    
    # 解析记录并格式化
    records = []
    current_tz = tz.tzlocal()
    
    for raw_record in raw_records:
        record = parse_record(raw_record)
        timestamp_dt = parser.parse(record['timestamp']).astimezone(current_tz)
        records.append({
            'timestamp': timestamp_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'tag': record['tag'],
            'raw_timestamp': record['timestamp']
        })

    # 计算今天最早记录的时间与当前时间的差值
    now = datetime.now(current_tz)
    today_start = datetime(now.year, now.month, now.day, tzinfo=current_tz)
    
    today_records = []
    for raw_record in raw_records:
        record = parse_record(raw_record)
        timestamp_dt = parser.parse(record['timestamp']).astimezone(current_tz)
        if today_start <= timestamp_dt < today_start + timedelta(days=1):
            today_records.append((timestamp_dt, record['tag']))

    if not today_records:
        return jsonify({'records': records, 'message': 'No records for today'}), 200

    first_timestamp, first_tag = min(today_records, key=lambda x: x[0])
    elapsed_time = now - first_timestamp
    elapsed_time_str = str(elapsed_time).split('.')[0]  # 去掉微秒部分

    return jsonify({
        'records': records,
        'today_first_timestamp': first_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'today_first_tag': first_tag,
        'elapsed_time': elapsed_time_str
    }), 200


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
    raw_records = redis_db.lrange(device_name, 0, -1)
    today_records = []
    
    for raw_record in raw_records:
        record = parse_record(raw_record)
        timestamp_dt = parser.parse(record['timestamp']).astimezone(current_tz)
        if today_start <= timestamp_dt < today_start + timedelta(days=1):
            today_records.append((timestamp_dt, record['tag']))

    if not today_records:
        return jsonify({'message': 'No records for today'}), 404

    # 获取今天最早的记录
    first_timestamp, first_tag = min(today_records, key=lambda x: x[0])
    elapsed_time = now - first_timestamp
    elapsed_time_str = str(elapsed_time).split('.')[0]  # 去掉微秒部分

    # 返回最早记录的时间和已过时间
    response = {
        'first_timestamp': first_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'simple_today_timestamps': first_timestamp.strftime('%H:%M'),
        'first_tag': first_tag,
        'elapsed_time': elapsed_time_str,
    }

    return jsonify(response), 200


@app.route('/delete', methods=['POST'])
def delete_device_record():
    data = request.json
    device_name = data.get('device_name')
    timestamp = data.get('timestamp')  # 可以是原始时间戳或完整记录

    if not device_name or not timestamp:
        return jsonify({'error': 'Invalid input'}), 400

    try:
        # 获取所有记录
        raw_records = redis_db.lrange(device_name, 0, -1)
        
        # 查找要删除的记录
        record_to_delete = None
        for raw_record in raw_records:
            record = parse_record(raw_record)
            if record['timestamp'] == timestamp or raw_record == timestamp:
                record_to_delete = raw_record
                break
        
        if not record_to_delete:
            return jsonify({'error': 'Record not found'}), 404
        
        # 删除找到的记录
        result = redis_db.lrem(device_name, 1, record_to_delete)
        if result == 0:
            return jsonify({'error': 'Record not found or already deleted'}), 404

        return jsonify({'message': 'Record deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/update', methods=['POST'])
def update_device_record():
    data = request.json
    device_name = data.get('device_name')
    old_timestamp = data.get('old_timestamp')
    new_timestamp = data.get('new_timestamp')
    new_tag = data.get('new_tag', '签到')  # 新增标记支持

    if not device_name or not old_timestamp or not new_timestamp:
        return jsonify({'error': 'Invalid input'}), 400

    try:
        # 获取所有记录以查找要更新的记录
        raw_records = redis_db.lrange(device_name, 0, -1)
        
        old_record_to_delete = None
        for raw_record in raw_records:
            record = parse_record(raw_record)
            if record['timestamp'] == old_timestamp or raw_record == old_timestamp:
                old_record_to_delete = raw_record
                break
        
        if not old_record_to_delete:
            return jsonify({'error': 'Old record not found'}), 404

        # 删除旧记录
        result = redis_db.lrem(device_name, 1, old_record_to_delete)
        if result == 0:
            return jsonify({'error': 'Old record not found'}), 404

        # 创建新记录
        new_record = {
            'timestamp': new_timestamp,
            'tag': new_tag
        }
        redis_db.rpush(device_name, json.dumps(new_record, ensure_ascii=False))

        return jsonify({'message': 'Record updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_devices', methods=['GET'])
def get_devices():
    # 获取所有设备名称的列表
    devices = redis_db.keys('*')  # 这里假设所有设备名称都作为键存储在Redis中
    return jsonify({'devices': devices}), 200


@app.route('/get_timestamps', methods=['GET'])
def get_timestamps():
    device_name = request.args.get('device_name')

    if not device_name:
        return jsonify({'error': 'Invalid input'}), 400

    # 从 Redis 查询设备的所有记录
    raw_records = redis_db.lrange(device_name, 0, -1)
    
    # 解析并返回结构化数据
    records = []
    for raw_record in raw_records:
        record = parse_record(raw_record)
        records.append({
            'timestamp': record['timestamp'],
            'tag': record['tag'],
            'raw_record': raw_record  # 用于删除和更新操作
        })
    
    return jsonify({'records': records}), 200


@app.route('/badge', methods=['GET'])
def get_badge():
    device_name = request.args.get('device_name')
    
    if not device_name:
        return jsonify({
            "schemaVersion": 1,
            "label": " ",
            "message": "缺少设备名称",
            "color": "1ea54c55",
            "style": "flat-square",
            "isError": True
        }), 400
    
    # 获取当前日期的起始时间和结束时间
    current_tz = tz.tzlocal()
    now = datetime.now(current_tz)
    today_start = datetime(now.year, now.month, now.day, tzinfo=current_tz)
    
    # 从 Redis 查询数据
    raw_records = redis_db.lrange(device_name, 0, -1)
    today_records = []
    
    for raw_record in raw_records:
        record = parse_record(raw_record)
        timestamp_dt = parser.parse(record['timestamp']).astimezone(current_tz)
        if today_start <= timestamp_dt < today_start + timedelta(days=1):
            today_records.append((timestamp_dt, record['tag']))
    
    # 准备返回数据
    badge_data = {
        "schemaVersion": 1,
        "label": " " ,
    }
    
    if not today_records:
        # 如果今天没有记录
        badge_data["message"] = "尚未签到"
        badge_data["color"] = "#1ea54c55"  # 使用提供的浅色
        badge_data["style"] = "flat-square"
    else:
        # 按时间排序
        today_records.sort(key=lambda x: x[0])
        
        # 查找最后一个下班记录
        last_checkout = None
        for timestamp_dt, tag in reversed(today_records):
            if tag == '下班':
                last_checkout = timestamp_dt
                break
        
        if last_checkout:
            # 如果今天已经下班，显示下班时间
            time_message = f"于{last_checkout.strftime('%H:%M')}下班"
            badge_data["color"] = "#28a745"  # 绿色表示已下班
        else:
            # 如果还没下班，显示第一次签到时间
            first_timestamp, first_tag = min(today_records, key=lambda x: x[0])
            time_message = f"{first_timestamp.strftime('%H:%M')}({first_tag})"
            badge_data["color"] = "#1ea54c55"  # 原来的颜色
        
        badge_data["message"] = time_message
        badge_data["style"] = "flat-square"
    
    return jsonify(badge_data)

@app.route('/get_tags', methods=['GET'])
def get_tags():
    """获取所有可用的标记类型"""
    # 预定义的标记类型
    predefined_tags = ['签到', '下班', '午休', '外出', '会议', '培训']
    
    # 也可以从所有设备记录中提取已使用的标记
    device_name = request.args.get('device_name')
    used_tags = set(predefined_tags)
    
    if device_name:
        raw_records = redis_db.lrange(device_name, 0, -1)
        for raw_record in raw_records:
            record = parse_record(raw_record)
            used_tags.add(record['tag'])
    
    return jsonify({'tags': sorted(list(used_tags))}), 200


@app.route('/save_with_tag', methods=['POST'])
def save_device_with_tag():
    """带标记保存记录的专用API"""
    data = request.json
    device_name = data.get('device_name')
    tag = data.get('tag', '签到')
    custom_time = data.get('custom_time')  # 可选的自定义时间

    if not device_name:
        return jsonify({'error': 'Invalid input'}), 400

    # 使用自定义时间或当前时间
    if custom_time:
        try:
            # 验证时间格式
            parser.parse(custom_time)
            timestamp = custom_time
        except ValueError:
            return jsonify({'error': 'Invalid time format'}), 400
    else:
        timestamp = datetime.utcnow().isoformat() + 'Z'

    # 存储数据到 Redis
    record = {
        'timestamp': timestamp,
        'tag': tag
    }
    redis_db.rpush(device_name, json.dumps(record, ensure_ascii=False))

    return jsonify({'message': 'Data saved successfully', 'tag': tag, 'timestamp': timestamp}), 200


@app.route('/query_by_tag', methods=['GET'])
def query_by_tag():
    """按标记查询记录"""
    device_name = request.args.get('device_name')
    tag = request.args.get('tag')
    date_filter = request.args.get('date')  # 可选的日期过滤 YYYY-MM-DD

    if not device_name:
        return jsonify({'error': 'Invalid input'}), 400

    # 从 Redis 查询数据
    raw_records = redis_db.lrange(device_name, 0, -1)
    
    # 过滤记录
    filtered_records = []
    current_tz = tz.tzlocal()
    
    for raw_record in raw_records:
        record = parse_record(raw_record)
        timestamp_dt = parser.parse(record['timestamp']).astimezone(current_tz)
        
        # 标记过滤
        if tag and record['tag'] != tag:
            continue
            
        # 日期过滤
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                if timestamp_dt.date() != filter_date:
                    continue
            except ValueError:
                continue
        
        filtered_records.append({
            'timestamp': timestamp_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'tag': record['tag'],
            'raw_timestamp': record['timestamp']
        })

    return jsonify({'records': filtered_records, 'total': len(filtered_records)}), 200


@app.route('/query_daily_work_hours', methods=['GET'])
def query_daily_work_hours():
    """查询每天工作时间"""
    device_name = request.args.get('device_name')
    start_date = request.args.get('start_date')  # 可选的开始日期 YYYY-MM-DD
    end_date = request.args.get('end_date')    # 可选的结束日期 YYYY-MM-DD
    
    if not device_name:
        return jsonify({'error': 'Invalid input'}), 400
    
    # 从 Redis 查询数据
    raw_records = redis_db.lrange(device_name, 0, -1)
    
    # 按日期分组记录
    daily_records = {}
    current_tz = tz.tzlocal()
    
    for raw_record in raw_records:
        record = parse_record(raw_record)
        timestamp_dt = parser.parse(record['timestamp']).astimezone(current_tz)
        date_str = timestamp_dt.strftime('%Y-%m-%d')
        
        # 日期过滤
        if start_date and date_str < start_date:
            continue
        if end_date and date_str > end_date:
            continue
            
        if date_str not in daily_records:
            daily_records[date_str] = []
        daily_records[date_str].append((timestamp_dt, record['tag']))
    
    # 计算每天的工作时间
    work_hours_data = []
    
    for date_str, records in sorted(daily_records.items()):
        # 按时间排序
        records.sort(key=lambda x: x[0])
        
        # 找到第一个签到记录
        first_checkin = None
        for timestamp_dt, tag in records:
            if tag == '签到':
                first_checkin = timestamp_dt
                break
        
        # 找到最后一个下班记录
        last_checkout = None
        for timestamp_dt, tag in reversed(records):
            if tag == '下班':
                last_checkout = timestamp_dt
                break
        
        # 计算工作时间
        work_duration = None
        work_hours = 0
        status = "未完成"
        
        if first_checkin and last_checkout:
            work_duration = last_checkout - first_checkin
            work_hours = work_duration.total_seconds() / 3600  # 转换为小时
            status = "已完成"
        elif first_checkin:
            # 如果只有签到没有下班，计算到当前时间（仅限今天）
            now = datetime.now(current_tz)
            if date_str == now.strftime('%Y-%m-%d'):
                work_duration = now - first_checkin
                work_hours = work_duration.total_seconds() / 3600
                status = "进行中"
        
        work_hours_data.append({
            'date': date_str,
            'first_checkin': first_checkin.strftime('%H:%M') if first_checkin else None,
            'last_checkout': last_checkout.strftime('%H:%M') if last_checkout else None,
            'work_hours': round(work_hours, 2),
            'work_duration': str(work_duration).split('.')[0] if work_duration else None,
            'status': status,
            'records_count': len(records)
        })
    
    return jsonify({
        'daily_work_hours': work_hours_data,
        'total_days': len(work_hours_data),
        'completed_days': len([d for d in work_hours_data if d['status'] == '已完成'])
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
