# work-timer

## 用来记录和展示今天工作了多久

### 新功能
- ✅ **标记功能**: 支持为每个时间记录添加标记（如：签到、下班、午休、外出、会议、培训等）
- ✅ **数据持久化**: Redis数据自动保存到本地目录，重启不丢失
- ✅ **向后兼容**: 完全兼容旧版本数据格式

### RoadMap
- [x] 记录和查询的API
- [x] 简单的Web界面
- [x] 自动化docker构建
- [x] 快捷指令 
- [x] 标记功能支持
- [x] Redis数据持久化
- [ ] OpenWRT插件

### 网页

![网页](images/web.png)


### IOS 快捷指令实现自动记录
https://www.icloud.com/shortcuts/a582f25607024a989c5aaa2b1a19784e

![快捷指令](images/ios_fast.png)


### API

#### 记录时间（支持标记）

```http
POST https://demo.com/save
Content-Type: application/json

{
  "device_name": "your_device",
  "tag": "签到"
}
```

#### 带标记保存记录的专用API

```http
POST https://demo.com/save_with_tag
Content-Type: application/json

{
  "device_name": "your_device",
  "tag": "下班",
  "custom_time": "2023-01-01T18:00:00Z"  // 可选，不传则使用当前时间
}
```

#### 查询特定设备所有记录的时间

```http
GET http://demo.com/query?device_name=your_device
```

#### 查询特定设备今天工作了多久

```http
GET https://demo.com/query_today_first?device_name=your_device
```

#### 按标记查询记录

```http
GET https://demo.com/query_by_tag?device_name=your_device&tag=签到&date=2023-01-01
```

#### 获取可用标记列表

```http
GET https://demo.com/get_tags?device_name=your_device
```

#### 更新记录（支持修改标记）

```http
POST https://demo.com/update
Content-Type: application/json

{
  "device_name": "your_device",
  "old_timestamp": "2023-01-01T09:00:00Z",
  "new_timestamp": "2023-01-01T09:30:00Z",
  "new_tag": "会议"
}
```


## 部署

推荐使用docker-compose部署, 支持Redis数据持久化

```yaml
version: '3'
services:
  web:
    build: .
    ports:
      - "8000:5000"
    environment:
      - FLASK_ENV=development
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - TZ=Asia/Shanghai
    depends_on:
      - redis
  redis:
    image: "redis:alpine"
    ports:
      - "6379:6379"
    environment:
      - TZ=Asia/Shanghai
    volumes:
      - ./redis-data:/data  # 数据持久化到本地目录
    command: redis-server --appendonly yes  # 启用AOF持久化
```

或者使用预构建镜像：

```docker-compose
version: '3.7'
services:
web:
image: xiebaiyuan/work-timer:lastest
platform: linux/amd64
ports:
- "8888:5000"
environment:
- FLASK_ENV=development
- REDIS_HOST=redis
- REDIS_PORT=6379
depends_on:
- redis
volumes:
- /etc/localtime:/etc/localtime:ro  # 共享主机时间
redis:
image: "redis:alpine"
platform: linux/amd64
ports:
- "6379:6379"
volumes:
- /etc/localtime:/etc/localtime:ro  # 共享主机时间

```

## 数据持久化说明

- Redis数据会自动保存到项目根目录的 `redis-data/` 文件夹中
- 即使重启Docker容器，数据也不会丢失
- `redis-data/` 目录已添加到 `.gitignore`，不会被提交到版本控制

## PS

家人公司要求若干小时， 导致每天都得记一下几点来的，不然夜里可能都不达标？

网上找半天没找到，想想就低成本实现了一个，
奈何本人前端后端都是很弱，就随便用flask + redis实现了一个部署在nas上了，欢迎大神搞个完美方案。

## [**我的博客**](https://www.xiebaiyuan.top)