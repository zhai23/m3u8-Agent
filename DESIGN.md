# M3U8 下载器设计文档

## 核心原则

**简单、直接、实用** - 最小化复杂度，快速实现功能

---

## 1. 项目概述

一个轻量级 M3U8 视频下载器，使用 N_m3u8DL-RE 作为下载引擎。

### 核心特性
- 纯静态前端（HTML + CSS + JS）
- FastAPI 后端提供 API 和实时进度
- 无数据库，使用 JSON 文件存储
- 支持多任务下载
- 实时进度显示

### 环境要求
- **Python**: 3.11 / 3.12 / 3.13
- **N_m3u8DL-RE**: 最新版

---

## 2. 系统架构

```
┌─────────────────────────────────────┐
│         前端 (纯静态)                │
│    HTML + CSS + JavaScript          │
│         ↓ HTTP/SSE                  │
├─────────────────────────────────────┤
│         FastAPI 后端                │
│    ┌──────────┬──────────┐          │
│    │ REST API │ SSE 推送 │          │
│    └──────────┴──────────┘          │
│    ┌──────────┬──────────┐          │
│    │ 任务管理 │ 下载调用 │          │
│    └──────────┴──────────┘          │
│         ↓                           │
│    N_m3u8DL-RE (子进程)             │
└─────────────────────────────────────┘
```

---

## 3. 目录结构

```
m3u8-agent/
├── backend/                    # 后端代码
│   ├── main.py                 # 应用入口（FastAPI app）
│   ├── config.toml             # 配置文件
│   ├── tasks.json              # 任务数据（自动生成）
│   │
│   ├── core/                   # 核心逻辑
│   │   ├── config.py           # 配置管理
│   │   ├── downloader.py       # 下载器封装
│   │   ├── task_manager.py     # 任务管理
│   │   └── progress_parser.py  # 进度解析
│   │
│   ├── api/                    # API 路由
│   │   ├── tasks.py            # 任务接口
│   │   ├── config.py           # 配置接口
│   │   └── stream.py           # SSE 推送
│   │
│   └── models/                 # 数据模型
│       ├── task.py             # 任务模型
│       └── config.py           # 配置模型
│
├── frontend/                   # 前端代码（纯静态）
│   ├── index.html              # 主页面
│   ├── style.css               # 样式
│   └── app.js                  # 应用逻辑
│
├── m3u8d/                      # N_m3u8DL-RE 存放目录
│   └── N_m3u8DL-RE.exe
│
├── downloads/                  # 下载完成文件
├── downloads_tmp/              # 临时下载文件
│
├── requirements.txt            # Python 依赖
├── README.md                   # 使用说明
├── DESIGN.md                   # 设计文档（本文件）
├── AGENTS.md                   # AI 开发规范
└── CONFIG.md                   # 配置说明
```

### 目录说明

#### 后端目录
- **`backend/main.py`**: FastAPI 应用入口，包含所有路由注册
- **`backend/core/`**: 核心业务逻辑
  - `config.py`: 读取和管理 `config.toml`
  - `downloader.py`: 封装 N_m3u8DL-RE 调用
  - `task_manager.py`: 任务队列、状态管理、并发控制
  - `progress_parser.py`: 解析下载器输出，提取进度信息
- **`backend/api/`**: API 路由模块
  - `tasks.py`: 任务 CRUD 接口
  - `config.py`: 配置读写接口
  - `stream.py`: SSE 实时推送
- **`backend/models/`**: Pydantic 数据模型

#### 前端目录
- **`frontend/index.html`**: 单页面应用
- **`frontend/style.css`**: 所有样式
- **`frontend/app.js`**: 所有逻辑（API 调用、UI 更新、SSE 监听）

#### 数据目录
- **`downloads/`**: 下载完成的视频文件
- **`downloads_tmp/`**: 下载过程中的临时文件

---

## 4. 数据模型

### 任务模型 (Task)

```python
class Task:
    id: str                    # 任务 ID（UUID）
    url: str                   # M3U8 链接
    name: str                  # 保存名称
    status: str                # pending/running/paused/completed/failed
    progress: float            # 进度百分比 (0-100)
    speed: str                 # 下载速度
    eta: str                   # 预计剩余时间
    created_at: datetime       # 创建时间
    started_at: datetime       # 开始时间
    completed_at: datetime     # 完成时间
    error: str                 # 错误信息
```

### 配置模型 (Config)

```toml
[downloader]
m3u8d_path = "m3u8d/N_m3u8DL-RE.exe"
save_dir = "downloads"
tmp_dir = "downloads_tmp"
thread_count = 16
retry_count = 3
max_concurrent_tasks = 3

[server]
host = "0.0.0.0"
port = 8000
```

---

## 5. API 设计

### REST API

| 方法 | 路径 | 描述 |
|------|------|------|
| **任务管理** |
| GET | `/api/tasks` | 获取所有任务 |
| POST | `/api/tasks` | 创建新任务 |
| GET | `/api/tasks/{id}` | 获取任务详情 |
| DELETE | `/api/tasks/{id}` | 删除任务 |
| POST | `/api/tasks/{id}/start` | 开始任务 |
| POST | `/api/tasks/{id}/pause` | 暂停任务 |
| POST | `/api/tasks/{id}/cancel` | 取消任务 |
| **配置管理** |
| GET | `/api/config` | 获取配置 |
| PUT | `/api/config` | 更新配置 |
| **系统状态** |
| GET | `/api/status` | 系统状态 |

### SSE 推送

```
GET /api/stream/tasks
Content-Type: text/event-stream
```

**事件类型**:
- `task.created` - 任务创建
- `task.progress` - 进度更新
- `task.completed` - 任务完成
- `task.failed` - 任务失败

**事件格式**:
```
event: task.progress
data: {"task_id": "xxx", "percent": 45.5, "speed": "2.5 MB/s", "eta": "00:02:30"}

```

---

## 6. 核心逻辑

### 任务状态流转

```
pending → running → completed
            ↓           ↑
          paused -------┘
            ↓
          failed
```

### 下载流程

1. 用户提交 M3U8 链接和保存名称
2. 创建任务（状态: `pending`）
3. 任务管理器检查并发数，启动下载（状态: `running`）
4. 调用 N_m3u8DL-RE 子进程
5. 解析输出，通过 SSE 推送进度
6. 下载完成，移动文件到 `downloads/`（状态: `completed`）
7. 失败则记录错误（状态: `failed`）

### N_m3u8DL-RE 调用

```bash
N_m3u8DL-RE.exe "https://example.com/video.m3u8" \
  --save-dir "./downloads_tmp" \
  --save-name "video_title" \
  --thread-count 16 \
  --retry-count 3 \
  --del-after-done
```

### 进度解析

通过正则表达式解析标准输出：
- 进度百分比: `(\d+\.\d+)%`
- 下载速度: `(\d+\.\d+\s*[KMG]B/s)`
- 预计时间: `ETA:\s*(\d{2}:\d{2}:\d{2})`

---

## 7. 前端设计

### 页面布局

```
┌────────────────────────────────────────┐
│  M3U8 下载器                    [设置] │
├────────────────────────────────────────┤
│  M3U8 链接: [________________]         │
│  保存名称:   [________________]         │
│             [开始下载]                  │
├────────────────────────────────────────┤
│  下载任务                               │
│  [全部] [进行中] [已完成] [失败]       │
│  ┌──────────────────────────────────┐  │
│  │ 视频标题          [暂停] [删除]  │  │
│  │ ████████░░░░ 45%  2.5 MB/s       │  │
│  └──────────────────────────────────┘  │
│  ...                                   │
└────────────────────────────────────────┘
```

### 技术栈

- **HTML5**: 语义化标签
- **CSS3**: 原生 CSS + CSS Variables
- **JavaScript**: ES6+ 原生 JS
- **HTTP**: Fetch API
- **实时通信**: EventSource (SSE)

### 核心功能

1. **任务创建**: 表单提交 → POST `/api/tasks`
2. **任务列表**: 页面加载 → GET `/api/tasks`
3. **实时进度**: EventSource 监听 `/api/stream/tasks`
4. **任务控制**: 按钮点击 → POST `/api/tasks/{id}/start|pause|cancel`
5. **任务筛选**: 前端过滤显示

---

## 8. 开发计划

### Phase 1: 核心功能 ✓
- [x] 配置管理
- [x] 下载器封装
- [ ] 任务管理器
- [ ] REST API
- [ ] 基础前端

### Phase 2: 实时功能
- [ ] SSE 推送
- [ ] 进度解析
- [ ] 前端实时更新

### Phase 3: 完善优化
- [ ] 错误处理
- [ ] 并发控制
- [ ] 文件管理
- [ ] 文档完善

---

## 9. 依赖列表

### Python 依赖 (requirements.txt)

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
toml>=0.10.2
```

### 前端依赖

**无依赖** - 纯原生实现

---

## 10. 命名规范

### 文件/目录命名
- **必须英文**: `a-z`, `0-9`, `-`, `_`, `.`
- **风格**: `snake_case` (Python) / `kebab-case` (前端)

### 代码命名
- **对外接口**: 英文（API 路径、JSON 字段、配置键名）
- **内部实现**: 中文（类名、方法名、参数名、变量名）
- **HTML/CSS**: class/id 必须英文 `kebab-case`
- **用户可见**: 中文（页面文案、提示、日志）

### 示例

```python
# 类名 - 中文
class M3U8下载器:
    def __init__(self, 配置: Config):
        self.配置 = 配置
    
    # 方法名 - 中文
    async def 下载(self, 链接: str, 保存名称: str):
        进程 = await self._启动进程(链接, 保存名称)
        return await self._等待完成(进程)
```

```javascript
// 对外 API - 英文
async function fetchTasks() {
    const 响应 = await fetch('/api/tasks');
    return await 响应.json();
}

// 内部函数 - 中文
function 更新进度条(任务ID, 百分比) {
    const 进度条 = document.querySelector(`[data-task-id="${任务ID}"]`);
    进度条.style.width = `${百分比}%`;
}
```

---

## 11. 部署说明

### 本地开发

```bash
# 后端
python backend/main.py

# 前端（可选）
cd frontend
python -m http.server 3000
```

### 生产部署

**后端**: 
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**前端**: 
- 直接部署 `frontend/` 目录到任意静态服务器
- 或由 FastAPI 直接提供静态文件服务

---

## 12. 安全说明

**内网使用，无需复杂安全措施**

- 无需身份认证
- 无需 HTTPS
- 无需 CORS 限制
- 可选 API 密钥（防止内网误用）

---

## 附录

### 相关文档
- `README.md` - 使用说明
- `AGENTS.md` - AI 开发规范
- `CONFIG.md` - 配置说明

### 参考资料
- [N_m3u8DL-RE 文档](https://github.com/nilaoda/N_m3u8DL-RE)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
