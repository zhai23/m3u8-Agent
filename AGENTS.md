# M3U8 Agent - AI 代理开发指南

本文档为在本 M3U8 下载器项目工作的 AI 编码助手提供指南。**以方便快捷、易于使用为优先原则**。

---

## 中文编程规范（HTML / CSS / JS / Python）

目标：在不破坏生态兼容性（工具链、浏览器、第三方库、接口协议）的前提下，**最大程度**使用中文命名与中文文案。

### 语言使用边界（核心规则）

#### 必须英文（强约束）
协议/标准规定的内容，或需要跨工具/跨语言稳定协作的标识符：
- HTML 标签与标准属性名（如 `class`、`data-*`、`aria-*`）
- CSS 属性名与语法关键字（如 `display`、`@media`）
- URL、HTTP Header、MIME、SSE 事件名、API 路由路径
- **仓库内所有文件/目录/文件夹名**（必须纯英文 ASCII，避免编码与平台兼容问题）
- JSON 字段名（对外协议字段）与数据库字段（如有）
- Python/JS 标准库、第三方库的导入名称
- 配置文件中的键名（如 `config.toml` 的字段名）

#### 必须中文（强约束）
所有内部实现细节且不对外暴露的标识符：
- **类名**：业务类名必须中文（如 `M3U8下载器`、`任务管理器`）
- **方法名**：内部方法/函数名必须中文（如 `下载()`、`解析进度()`）
- **参数名**：函数参数必须中文（如 `链接`、`保存名称`、`线程数`）
- **局部变量**：函数内部变量必须中文（如 `进程`、`命令`、`返回码`）
- **实例变量**：类的实例变量必须中文（如 `self.配置`、`self._当前进程`）
- **异常变量**：`except Exception as 异常`
- **循环变量**：`for 项 in 列表`
- UI 文本、提示语、错误信息、日志内容（面向使用者/排障）

### 文件与目录命名（强约束）
- **只能使用英文 ASCII**：`a-z`、`0-9`、`-`、`_`、`.`（不使用中文、空格、全角符号）
- **统一风格**：目录与静态资源优先 `kebab-case`；Python 模块/包使用 `snake_case`
- **避免歧义**：不使用大小写仅区分的文件名（跨平台容易出问题）

### 命名总规则
- **对外接口一律英文**：凡是会被"外部代码/外部系统/HTML/CSS 选择器/网络协议"引用的名字，用英文
- **内部实现必须中文**：所有不对外暴露的标识符（类名、方法名、参数名、变量名）必须中文
- **格式约定**：
  - 中文类名/方法名/变量名：直接使用中文（如 `M3U8下载器`、`下载()`、`保存名称`）
  - 英文变量/函数：`camelCase`（JS）/ `snake_case`（Python）
  - 英文类名：`PascalCase`
  - 常量：`UPPER_SNAKE_CASE`
  - HTML/CSS 的 class：`kebab-case`

---

## HTML 规范

### 必须英文
- 标签名：`<div>`、`<button>`、`<input>` 等（HTML 标准）
- 属性名：`class`、`id`、`data-*`、`aria-*` 等（HTML 标准）
- class/id 值：用于 CSS/JS 选择器，必须英文 `kebab-case`

### 必须中文
- 文本内容：按钮文案、标题、提示语
- 用户可见属性：`title`、`aria-label`、`placeholder` 等

### 示例
```html
<button class="task-start-btn" aria-label="开始下载">开始下载</button>
<div class="task-status" data-task-id="123">等待中</div>
<input type="text" class="task-name-input" placeholder="请输入任务名称">
```

---

## CSS 规范

### 必须英文
- 选择器：与 HTML `class/id` 一致，保持 `kebab-case`
- 属性名：`display`、`color`、`margin` 等（CSS 标准）
- CSS 变量名：优先用 `--color-*`、`--space-*`、`--font-*` 这类英文命名

### 可中文部分
- `content:` 等直接呈现给用户的文本（但更推荐由 HTML/JS 控制文案）

### 示例
```css
:root {
  --color-primary: #2563eb;
  --color-success: #10b981;
  --space-2: 8px;
  --space-4: 16px;
}

.task-status {
  color: var(--color-primary);
  margin-top: var(--space-2);
}

.task-item:hover {
  background-color: var(--color-success);
}
```

---

## JavaScript 规范

### 必须英文
- 文件名、目录名（如 `task-manager.js`）
- 模块导出的函数/变量/类名（对外 API）
- DOM 选择器相关：`class/id/data-*` 的值与查询字符串
- 与后端交互的字段名：请求/响应 JSON 的 key、SSE 事件名、API 路径
- 标准库/第三方库的导入和调用

### 必须中文
- **局部变量**：函数内部变量、短生命周期的中间变量
- **内部私有函数**：不导出、不作为事件名/回调协议名的函数
- **循环变量**：`for (const 任务 of 任务列表)`
- **异常变量**：`catch (异常)`

### 示例
```javascript
// 对外导出的 API - 英文
export async function fetchTasks() {
    const 响应 = await fetch(`${API_BASE_URL}/api/tasks`);
    const 数据 = await 响应.json();
    return 数据;
}

// 内部函数 - 中文
function 渲染任务列表(任务列表) {
    const 容器 = document.querySelector('.task-list');
    const HTML片段 = 任务列表.map((任务) => {
        const 状态类名 = 任务.status === 'running' ? 'task-running' : 'task-idle';
        return `<div class="task-item ${状态类名}">${任务.name}</div>`;
    }).join('');
    容器.innerHTML = HTML片段;
}

// 事件处理 - 内部变量中文
document.querySelector('.task-start-btn').addEventListener('click', async (事件) => {
    const 按钮 = 事件.target;
    const 任务ID = 按钮.dataset.taskId;
    
    try {
        const 结果 = await startTask(任务ID);
        if (结果.success) {
            显示成功提示('任务已启动');
        }
    } catch (异常) {
        console.error('启动任务失败:', 异常);
        显示错误提示('启动失败');
    }
});

// SSE 实时更新 - 事件名英文，内部变量中文
const 事件源 = new EventSource(`${API_BASE_URL}/api/stream/tasks`);
事件源.addEventListener('task.progress', (事件) => {
    const 数据 = JSON.parse(事件.data);
    更新进度条(数据.task_id, 数据.percent);
});
```

---

## Python 规范

### 必须英文
- 文件名/模块名/包名（如 `backend/core/downloader.py`）
- 配置键名、持久化 JSON 的字段名（对外可读/兼容性优先）
- Pydantic 模型的字段名（对外协议字段）
- 标准库/第三方库的导入和调用

### 必须中文
- **类名**：业务类名必须中文（如 `M3U8下载器`、`简单下载器`）
- **方法名**：类的方法名必须中文（如 `下载()`、`取消()`、`获取下载路径()`）
- **参数名**：函数参数必须中文（如 `链接`、`保存名称`、`线程数`、`**其他参数`）
- **局部变量**：函数内部变量必须中文（如 `进程`、`命令`、`返回码`）
- **实例变量**：类的实例变量必须中文（如 `self.配置`、`self._当前进程`）
- **异常变量**：`except Exception as 异常`
- **循环变量**：`for 项 in 列表`

### 示例
```python
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import asyncio

from .config import get_config, Config


class M3U8下载器:
    """M3U8 下载器类"""
    
    def __init__(self, 配置: Optional[Config] = None):
        """初始化下载器"""
        self.配置 = 配置 or get_config()
        self.m3u8d路径 = Path(self.配置.m3u8d_path)
        self.默认保存目录 = Path(self.配置.save_dir)
        self._当前进程: Optional[asyncio.subprocess.Process] = None
    
    async def 下载(
        self,
        链接: str,
        保存名称: str,
        保存目录: Optional[str] = None,
        线程数: Optional[int] = None,
        进度回调: Optional[Callable[[Dict[str, Any]], None]] = None,
        **其他参数
    ) -> bool:
        """下载 M3U8 视频"""
        最终保存目录 = Path(保存目录) if 保存目录 else self.默认保存目录
        
        # 构建命令
        命令 = self._构建下载命令(
            链接=链接,
            保存名称=保存名称,
            保存目录=最终保存目录,
            线程数=线程数,
            **其他参数
        )
        
        try:
            成功 = await self._执行下载(命令, 进度回调)
            return 成功
        except Exception as 异常:
            print(f"下载出错: {str(异常)}")
            return False
    
    def _构建下载命令(
        self,
        链接: str,
        保存名称: str,
        保存目录: Path,
        线程数: Optional[int] = None,
        **其他参数
    ) -> list:
        """构建 N_m3u8DL-RE 命令"""
        命令 = [str(self.m3u8d路径), 链接]
        命令.extend(["--save-dir", str(保存目录)])
        命令.extend(["--save-name", 保存名称])
        
        最终线程数 = 线程数 if 线程数 is not None else self.配置.thread_count
        命令.extend(["--thread-count", str(最终线程数)])
        
        return 命令
    
    async def _执行下载(
        self,
        命令: list,
        进度回调: Optional[Callable[[Dict[str, Any]], None]]
    ) -> bool:
        """执行下载命令并解析输出"""
        进程 = None
        try:
            进程 = await asyncio.create_subprocess_exec(
                *命令,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            self._当前进程 = 进程
            
            while True:
                行 = await 进程.stdout.readline()
                if not 行:
                    break
                
                行文本 = 行.decode('utf-8', errors='ignore').strip()
                
                if 进度回调:
                    进度信息 = self._解析进度(行文本)
                    if 进度信息:
                        进度回调(进度信息)
            
            返回码 = await 进程.wait()
            return 返回码 == 0
            
        except Exception as 异常:
            print(f"执行命令出错: {str(异常)}")
            return False
        finally:
            self._当前进程 = None
    
    async def 取消(self):
        """取消当前下载"""
        if self._当前进程 and self._当前进程.returncode is None:
            self._当前进程.terminate()
            await self._当前进程.wait()


# 使用示例
async def 主函数():
    下载器 = M3U8下载器()
    
    def 进度回调(进度: Dict[str, Any]):
        百分比 = 进度.get("percent", 0)
        速度 = 进度.get("speed", "N/A")
        print(f"进度: {百分比:.1f}% | 速度: {速度}")
    
    成功 = await 下载器.下载(
        链接="https://example.com/video.m3u8",
        保存名称="我的视频",
        线程数=8,
        进度回调=进度回调
    )
    
    if 成功:
        print("下载成功!")
    else:
        print("下载失败!")
```

### 配置文件字段名保持英文
```python
# config.py
class Config:
    @property
    def m3u8d_path(self) -> str:
        """N_m3u8DL-RE 可执行文件路径"""
        return self._config["downloader"]["m3u8d_path"]
    
    @property
    def thread_count(self) -> int:
        """下载线程数"""
        return self._config["downloader"]["thread_count"]
```

---

## 推荐落地策略

### 前端（HTML/CSS/JS）
- **HTML/CSS 选择器**：全部英文 `kebab-case`
- **接口字段**：全部英文（JSON key、API 路径、SSE 事件名）
- **页面文案**：全部中文
- **JS 内部变量**：全部中文

### 后端（Python）
- **文件名/模块名**：全部英文 `snake_case`
- **类名**：全部中文（如 `M3U8下载器`）
- **方法名**：全部中文（如 `下载()`、`取消()`）
- **参数名**：全部中文（如 `链接`、`保存名称`）
- **局部变量**：全部中文（如 `进程`、`命令`）
- **配置字段**：全部英文（对外兼容性）
- **日志与错误信息**：全部中文

---

## Python 后端指南

### 环境设置
```bash
# 检查 Python 版本（3.11、3.12 或 3.13）
python check_python.py

# 安装依赖
pip install -r requirements.txt

# 运行后端服务器
python backend/main.py

# 开发模式（自动重载）
uvicorn backend.main:app --reload
```

### 代码风格（保持简洁即可）

#### 快速格式化（可选）
```bash
pip install black
black backend/
```

#### Python 代码规范（基础即可）
- **导入顺序**: 标准库 → 第三方库 → 本地模块
- **类型提示**: 建议使用，但不必强制
- **命名规范**: 
  - 类名：中文（如 `M3U8下载器`）
  - 方法/参数/变量：中文（如 `下载()`、`链接`、`进程`）
  - 配置字段：英文 `snake_case`
  - 常量：`UPPER_SNAKE_CASE`
- **错误处理**: 简单的 try-except 即可，不必过度复杂
  ```python
  try:
      结果 = await 处理任务(任务ID)
  except Exception as 异常:
      print(f"错误: {异常}")
      raise HTTPException(status_code=500, detail=str(异常))
  ```
- **Async/await**: I/O 操作使用 async/await

#### Pydantic 模型
- 使用 Pydantic v2 语法
- 在 `backend/models/` 目录定义模型
- 字段名保持英文（对外协议）
- 字段描述可省略，保持代码简洁

---

## JavaScript 前端指南

### 环境设置
```bash
# 无需构建，纯静态文件

# 本地开发服务器
cd frontend
python -m http.server 3000
```

### 代码风格

#### JavaScript 规范
- **使用 ES6+ 特性**: const/let、箭头函数、模板字符串
- **简洁优先**: 不要过度抽象，直接实现功能即可
- **错误处理**: 简单的 try-catch，console.error 即可
- **内部变量必须中文**: 所有局部变量、循环变量、异常变量使用中文

```javascript
// 对外 API - 英文
export async function fetchTasks() {
    const 响应 = await fetch(`${API_BASE_URL}/api/tasks`);
    return await 响应.json();
}

// 内部函数 - 中文
function 更新进度条(任务ID, 百分比) {
    const 进度条 = document.querySelector(`[data-task-id="${任务ID}"] .progress-bar`);
    进度条.style.width = `${百分比}%`;
}

// SSE 实时更新
const 事件源 = new EventSource(`${API_BASE_URL}/api/stream/tasks`);
事件源.addEventListener('task.progress', (事件) => {
    const 数据 = JSON.parse(事件.data);
    更新进度条(数据.task_id, 数据.percent);
});
```

- **CSS**: 使用 CSS 变量，保持简单易读

---

## 测试指南（可选）

### Python 测试
```bash
# 运行测试（如果存在）
pytest

# 运行单个测试
pytest tests/test_tasks.py::test_create_task -v
```

### 前端测试
- 浏览器手动测试即可

---

## 文件结构说明

- 后端：`backend/` 目录
- 前端：`frontend/` 目录（纯静态）
- 配置：`backend/config.toml`
- 任务数据：默认 `backend/var/tasks.json`（可用环境变量 `M3U8_AGENT_DATA_DIR` 覆盖）
- 日志：默认 `backend/var/logs/*.log`（可用环境变量 `M3U8_AGENT_DATA_DIR` 覆盖）

---

## 开发原则

1. **快速优先**: 不要过度设计，先实现功能
2. **简洁实用**: 代码清晰易读即可，不必追求完美
3. **灵活调整**: 根据实际情况调整规范
4. **无需复杂检查**: 跳过繁琐的安全验证和输入清理
5. **直接可用**: 能跑起来就 OK
6. **中文优先**: 所有内部实现（类名、方法名、参数名、变量名）必须中文

---

## 提交前检查（简化版）

1. 确保 `python backend/main.py` 能运行
2. 确保前端页面正常显示
3. 无明显错误即可
4. 检查内部实现是否使用中文命名
