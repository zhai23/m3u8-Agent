# M3U8 下载器设计文档

## 命名与语言约定（中文优先但不破坏兼容性）

- **文件/目录/文件夹名**：必须纯英文 ASCII（`a-z`、`0-9`、`-`、`_`、`.`），不使用中文、空格、全角符号
- **代码标识符**：
  - 对外接口（API 路由、SSE 事件名、JSON 字段名、配置键名）统一英文
  - 内部实现可使用中文变量/函数名（不导出、不进入协议字段、不作为选择器/事件名）
- **前端 DOM/CSS 选择器**：`class/id/data-*` 必须英文 `kebab-case`
- **用户可见内容**：页面文案、状态展示、错误提示、日志内容优先中文

## 环境要求

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| **Python** | 3.11 | **必须使用 Python 3.11** - 长期支持版本，稳定性最佳 |
| **N_m3u8DL-RE** | 最新版 | 核心下载引擎 |

## 1. 项目概述

一个前后端分离的 M3U8 视频下载器，使用 N_m3u8DL-RE 作为核心下载引擎。

### 核心特性
- 纯静态前端，可部署到任意静态服务器
- FastAPI 后端提供 REST API 和实时进度推送
- 无数据库依赖，使用 JSON/TOML 文件存储
- 支持多任务并发下载
- 实时显示下载进度和日志

---

## 2. 架构设计

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (纯静态)                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  HTML5 + 原生 JavaScript + 原生 CSS                    │  │
│  │  - 任务管理页面                                        │  │
│  │  - 实时进度显示 (EventSource)                          │  │
│  │  - 配置管理                                            │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────┐
│                      FastAPI 后端                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  REST API    │  │  WebSocket   │  │  静态文件    │       │
│  │  任务管理    │  │  实时进度    │  │  前端文件    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ 任务队列管理 │  │ N_m3u8DL-RE  │  │ 配置文件管理 │       │
│  │ (内存+JSON)  │  │  子进程调用  │  │ (TOML/JSON)  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
m3u8-agent/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 应用入口
│   ├── config.py               # 配置管理
│   ├── api/                    # API 路由
│   │   ├── tasks.py            # 任务相关接口
│   │   ├── config.py           # 配置相关接口
│   │   └── system.py           # 系统状态接口
│   ├── core/                   # 核心业务逻辑
│   │   ├── task_manager.py     # 任务队列管理
│   │   ├── downloader.py       # N_m3u8DL-RE 调用封装
│   │   └── storage.py          # 文件存储管理
│   ├── models/                 # 数据模型
│   │   ├── task.py             # 任务模型
│   │   └── config.py           # 配置模型
│   └── data/                   # 数据存储目录
│       ├── config.toml         # 配置文件
│       ├── tasks.json          # 任务列表
│       └── logs/               # 任务日志目录
│           └── {task_id}.jsonl
├── frontend/                   # 前端源码
│   ├── index.html              # 主页面
│   ├── css/
│   │   └── style.css           # 样式文件
│   ├── js/
│   │   ├── api.js              # API 客户端
│   │   ├── components.js       # UI 组件
│   │   ├── utils.js            # 工具函数
│   │   └── app.js              # 应用主逻辑
│   └── components/             # HTML 组件模板
│       └── task-card.html
├── downloads/                  # 下载文件存放目录
├── m3u8d/                      # N_m3u8DL-RE 存放目录
│   └── N_m3u8DL-RE.exe
├── requirements.txt            # Python 依赖
└── README.md
```

说明：
- 上述所有目录/文件名保持纯英文 ASCII，避免跨平台与编码问题
- 用户可见的中文文案只出现在 HTML 文本、前端渲染字符串、日志/错误信息中

---

## 3. 数据模型

### 3.1 配置文件 (config.toml)

```toml
[server]
host = "0.0.0.0"
port = 8000
debug = false

[downloader]
# N_m3u8DL-RE 可执行文件路径
executable_path = "./m3u8d/N_m3u8DL-RE.exe"
# 默认下载目录
download_dir = "./downloads"
# 最大并发下载数
max_concurrent = 3
# 默认线程数
threads = 16
# 默认重试次数
retry_count = 3
# 默认超时时间(秒)
timeout = 30

[proxy]
# 是否启用代理
enabled = false
type = "http"  # http, https, socks5
host = "127.0.0.1"
port = 1080
username = ""
password = ""

[security]
# API 密钥 (可选)
api_key = ""
# 允许跨域的源
cors_origins = ["*"]
```

### 3.2 任务数据结构

#### 任务列表 (tasks.json)

```json
{
  "version": "1.0",
  "last_updated": "2024-01-15T10:30:00+08:00",
  "tasks": [
    {
      "id": "task_20240115_103000_abc123",
      "url": "https://example.com/video.m3u8",
      "title": "视频标题",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00+08:00",
      "updated_at": "2024-01-15T10:35:00+08:00",
      "progress": {
        "percent": 100,
        "downloaded_bytes": 104857600,
        "total_bytes": 104857600,
        "speed": "0 MB/s",
        "eta": "0s"
      },
      "output_path": "./downloads/video_abc123.mp4",
      "error_message": null
    }
  ],
  "stats": {
    "total": 10,
    "completed": 7,
    "failed": 1,
    "pending": 2
  }
}
```

#### 任务详细日志 (logs/{task_id}.jsonl)

```jsonl
{"timestamp": "2024-01-15T10:30:01+08:00", "level": "INFO", "message": "开始解析 M3U8..."}
{"timestamp": "2024-01-15T10:30:02+08:00", "level": "INFO", "message": "找到 256 个分段"}
{"timestamp": "2024-01-15T10:30:03+08:00", "level": "INFO", "message": "开始下载分段..."}
{"timestamp": "2024-01-15T10:32:15+08:00", "level": "INFO", "message": "下载进度: 50% (128/256)"}
{"timestamp": "2024-01-15T10:35:00+08:00", "level": "INFO", "message": "合并视频文件..."}
{"timestamp": "2024-01-15T10:35:10+08:00", "level": "INFO", "message": "下载完成"}
```

---

## 4. API 设计

### 4.1 REST API

#### 任务管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/tasks` | 获取任务列表 |
| POST | `/api/tasks` | 创建新任务 |
| GET | `/api/tasks/{id}` | 获取任务详情 |
| DELETE | `/api/tasks/{id}` | 删除任务 |
| POST | `/api/tasks/{id}/start` | 开始/恢复任务 |
| POST | `/api/tasks/{id}/pause` | 暂停任务 |
| POST | `/api/tasks/{id}/stop` | 停止任务 |
| GET | `/api/tasks/{id}/logs` | 获取任务日志 |

#### 配置管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/config` | 获取配置 |
| PUT | `/api/config` | 更新配置 |
| GET | `/api/config/default` | 获取默认配置 |

#### 系统状态

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/system/status` | 系统状态 |
| GET | `/api/system/stats` | 下载统计 |
| GET | `/api/system/health` | 健康检查 |

### 4.2 WebSocket / SSE 接口

#### Server-Sent Events (推荐)

```
GET /api/stream/tasks
Content-Type: text/event-stream
```

事件类型：
- `task.created` - 新任务创建
- `task.updated` - 任务状态更新
- `task.progress` - 下载进度更新
- `task.completed` - 任务完成
- `task.failed` - 任务失败
- `task.log` - 实时日志

示例事件格式：
```
event: task.progress
data: {"task_id": "task_abc123", "percent": 45.5, "speed": "2.5 MB/s", "eta": "00:02:30"}

```

---

## 5. 前端设计

### 5.1 页面结构

```
┌────────────────────────────────────────────────────────────┐
│  [Logo]  M3U8下载器                              [设置]    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  M3U8 URL: [                                    ]    │  │
│  │  标题:      [                                    ]    │  │
│  │                                                      │  │
│  │  [选项 ▼]  [开始下载]                                │  │
│  │  ├─ 线程数: [16]                                     │  │
│  │  ├─ 保存路径: [./downloads/]                         │  │
│  │  └─ 代理:   [不使用 ▼]                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 下载任务                                                │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ [全部] [进行中] [已完成] [失败]                        │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ ┌──────────────────────────────────────────────────┐ │  │
│  │ │ [图标] 视频标题                     [暂停] [删除]│ │  │
│  │ │ ████████████████░░░░ 45%  2.5 MB/s  ETA 02:30   │ │  │
│  │ │ 已下载: 50MB / 110MB  状态: 下载中               │ │  │
│  │ └──────────────────────────────────────────────────┘ │  │
│  │ ...                                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 5.2 组件列表

| 组件 | 描述 |
|------|------|
| `TaskInput` | URL 输入和选项配置 |
| `TaskList` | 任务列表容器 |
| `TaskCard` | 单个任务卡片 |
| `ProgressBar` | 进度条组件 |
| `TaskFilter` | 任务筛选标签 |
| `SettingsModal` | 设置弹窗 |
| `LogViewer` | 日志查看器 |

### 5.3 技术栈

- **语言**: 原生 JavaScript (ES6+)
- **构建工具**: 无需构建工具，直接部署
- **样式**: 原生 CSS + CSS Variables
- **HTTP 客户端**: 原生 Fetch API
- **实时通信**: EventSource (SSE)

### 5.4 部署说明

**1Panel 静态网站部署步骤：**

1. 将 `frontend/` 目录内容打包上传到 1Panel
2. 在 1Panel 创建静态网站，指向上传的目录
3. 确保所有 `.js` 文件路径正确引用

**本地开发：**
```bash
# 方式一：直接打开 (推荐简单测试)
直接双击 frontend/index.html

# 方式二：本地 HTTP 服务器 (推荐，避免 CORS 问题)
cd frontend
python -m http.server 3000
# 访问 http://localhost:3000
```

---

## 6. 后端核心逻辑

### 6.1 任务状态流转

```
┌─────────┐    创建     ┌─────────┐    开始     ┌─────────┐
│  NULL   │ ──────────→ │ pending │ ──────────→ │running  │
└─────────┘             └─────────┘             └────┬────┘
                                                    │
        ┌───────────────────────────────────────────┼───────────┐
        │                                           │           │
        ▼                                           ▼           ▼
  ┌─────────┐                                 ┌─────────┐ ┌─────────┐
  │ paused  │ ←───────────────────────────────│completed│ │ failed  │
  └────┬────┘  暂停                            └─────────┘ └─────────┘
       │
       └──────── 恢复 ───────→ running
```

### 6.2 下载器调用

N_m3u8DL-RE 命令行示例：
```bash
N_m3u8DL-RE.exe "https://example.com/video.m3u8" \
  --save-dir "./downloads" \
  --save-name "video_title" \
  --thread-count 16 \
  --retry-count 3 \
  --check-segments-count \
  --del-after-done \
  --no-log
```

进度解析：通过正则表达式解析 N_m3u8DL-RE 的标准输出，提取进度百分比、速度、ETA等信息。

### 6.3 并发控制

使用 asyncio 的 Semaphore 控制并发数：

```dockerfile
# Python 3.12 是推荐版本，提供最佳性能和兼容性
# 支持版本: 3.11, 3.12, 3.13
FROM python:3.12-slim

WORKDIR /app

# 复制后端代码
COPY backend/ ./backend/

# 复制前端静态文件
COPY frontend/ ./backend/static/

# 复制 N_m3u8DL-RE
COPY m3u8d/ ./m3u8d/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r backend/requirements.txt

EXPOSE 8000

CMD ["python", "backend/main.py"]
```

---

## 8. 开发计划

### Phase 1: 基础框架 (MVP)
- [ ] 后端 FastAPI 基础结构
- [ ] 配置管理 (TOML)
- [ ] 任务存储 (JSON)
- [ ] N_m3u8DL-RE 调用封装
- [ ] 基础 REST API

### Phase 2: 前端开发
- [ ] 纯静态前端页面
- [ ] 任务管理界面
- [ ] API 客户端封装
- [ ] SSE 实时进度

### Phase 3: 功能完善
- [ ] 任务队列并发控制
- [ ] 日志系统
- [ ] 错误处理和重试
- [ ] 文件管理和清理

### Phase 4: 优化完善
- [ ] 性能优化
- [ ] 文档完善

---

## 9. 依赖列表

### Python 依赖

**要求**: Python 3.11 (必须使用此版本)

所有依赖要写到requirements.txt中

### 前端依赖

**无依赖！** 使用原生 JavaScript，无需 npm 包管理。

如需增强开发体验（可选）：
- 使用 VS Code + ESLint 插件进行代码检查
- 使用浏览器 DevTools 进行调试
- 使用 Live Server 插件进行实时预览

---

## 10. 安全考虑

1. **安全**: 完全不需要考虑安全，仅在内网使用
2. **CORS**: 完全不限制跨域，方便用户使用
3. **API 密钥**: 可选的 API 密钥认证机制，轻微防止内网其他用户访问
