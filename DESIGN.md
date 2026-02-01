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
│   ├── config.js               # 前端配置（后端地址等）
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
- **`frontend/config.js`**: 前端配置文件（后端地址、超时设置等）
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

### 设计原则

**极简优先** - 功能实现为主，界面后期美化

- 使用原生 HTML 表单和按钮
- 最小化 CSS，只保证基本可用性
- 无需复杂组件，直接 DOM 操作
- 先实现功能，后续专门美化

### 页面布局（极简版）

```html
<!DOCTYPE html>
<html>
<head>
    <title>M3U8 下载器</title>
    <script src="config.js"></script>
</head>
<body>
    <h1>M3U8 下载器</h1>
    
    <!-- 创建任务 -->
    <form id="task-form">
        <input type="text" id="url" placeholder="M3U8 链接" required>
        <input type="text" id="name" placeholder="保存名称" required>
        <button type="submit">开始下载</button>
    </form>
    
    <!-- 任务列表 -->
    <h2>下载任务</h2>
    <div id="task-list"></div>
    
    <script src="app.js"></script>
</body>
</html>
```

### 任务卡片（极简版）

```html
<!-- 单个任务 -->
<div data-task-id="xxx">
    <p>视频标题</p>
    <p>进度: 45% | 速度: 2.5 MB/s</p>
    <button onclick="暂停任务('xxx')">暂停</button>
    <button onclick="删除任务('xxx')">删除</button>
</div>
```

### 技术栈

- **HTML5**: 原生表单和按钮
- **CSS3**: 最小化样式（可选）
- **JavaScript**: ES6+ 原生 JS
- **HTTP**: Fetch API
- **实时通信**: EventSource (SSE)

### 前端配置

**`frontend/config.js`** - 配置后端地址：

```javascript
// 前端配置文件
const API_CONFIG = {
    // 后端地址（根据部署环境修改）
    baseURL: 'http://localhost:8000',
    
    // 超时设置（毫秒）
    timeout: 30000,
    
    // SSE 重连间隔（毫秒）
    reconnectInterval: 3000
};
```

**使用方式**：

在 [`index.html`](frontend/index.html:1) 中先引入配置文件：
```html
<script src="config.js"></script>
<script src="app.js"></script>
```

在 [`app.js`](frontend/app.js:1) 中使用：
```javascript
// 使用配置的后端地址
const API_BASE_URL = API_CONFIG.baseURL;

async function fetchTasks() {
    const 响应 = await fetch(`${API_BASE_URL}/api/tasks`);
    return await 响应.json();
}
```

**部署说明**：
- 本地开发：使用默认配置 `http://localhost:8000`
- 生产部署：修改 `config.js` 中的 `baseURL` 为实际后端地址
- 跨域部署：前端和后端分离部署时，修改为后端完整 URL（如 `http://192.168.1.100:8000`）

### 核心功能（极简实现）

#### 1. 任务创建

```javascript
document.getElementById('task-form').addEventListener('submit', async (事件) => {
    事件.preventDefault();
    const 链接 = document.getElementById('url').value;
    const 名称 = document.getElementById('name').value;
    
    await fetch(`${API_BASE_URL}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: 链接, name: 名称 })
    });
    
    加载任务列表();
});
```

#### 2. 任务列表

```javascript
async function 加载任务列表() {
    const 响应 = await fetch(`${API_BASE_URL}/api/tasks`);
    const 任务列表 = await 响应.json();
    
    const 容器 = document.getElementById('task-list');
    容器.innerHTML = 任务列表.map(任务 => `
        <div data-task-id="${任务.id}">
            <p>${任务.name}</p>
            <p>进度: ${任务.progress}% | 速度: ${任务.speed}</p>
            <button onclick="暂停任务('${任务.id}')">暂停</button>
            <button onclick="删除任务('${任务.id}')">删除</button>
        </div>
    `).join('');
}
```

#### 3. 实时进度

```javascript
const 事件源 = new EventSource(`${API_BASE_URL}/api/stream/tasks`);

事件源.addEventListener('task.progress', (事件) => {
    const 数据 = JSON.parse(事件.data);
    const 任务元素 = document.querySelector(`[data-task-id="${数据.task_id}"]`);
    if (任务元素) {
        任务元素.querySelector('p:nth-child(2)').textContent =
            `进度: ${数据.percent}% | 速度: ${数据.speed}`;
    }
});
```

#### 4. 任务控制

```javascript
async function 暂停任务(任务ID) {
    await fetch(`${API_BASE_URL}/api/tasks/${任务ID}/pause`, { method: 'POST' });
}

async function 删除任务(任务ID) {
    await fetch(`${API_BASE_URL}/api/tasks/${任务ID}`, { method: 'DELETE' });
    加载任务列表();
}
```

### 文件结构（极简版）

```
frontend/
├── index.html          # 50 行以内，纯 HTML 结构
├── config.js           # 5 行，配置后端地址
├── style.css           # 可选，基础样式（后期美化）
└── app.js              # 100 行以内，所有逻辑
```

### 开发建议

1. **先不写 CSS**：使用浏览器默认样式即可
2. **直接 DOM 操作**：不需要虚拟 DOM 或组件化
3. **全局函数**：按钮直接 `onclick="函数名()"`
4. **最小化代码**：能用一行就不用两行
5. **后期美化**：功能完成后再统一美化界面

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
# 1. 启动后端
python backend/main.py

# 2. 前端配置（可选，如果后端不在 localhost:8000）
# 编辑 frontend/config.js，修改 baseURL

# 3. 访问前端
# 方式一：直接打开 frontend/index.html
# 方式二：启动本地服务器
cd frontend
python -m http.server 3000
# 访问 http://localhost:3000
```

### 生产部署

#### 方案 1: 前后端同服务器

```bash
# 后端提供静态文件服务
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# frontend/config.js 配置
baseURL: ''  # 空字符串表示同源
```

#### 方案 2: 前后端分离部署

```bash
# 后端
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 前端部署到静态服务器（如 Nginx、1Panel）
# 修改 frontend/config.js
baseURL: 'http://192.168.1.100:8000'  # 后端实际地址
```

**注意事项**：
- 前后端分离部署时，需要配置后端 CORS（已在设计中允许）
- 修改 `frontend/config.js` 后无需重新构建，直接生效

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
