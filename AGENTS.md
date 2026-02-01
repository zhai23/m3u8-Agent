# M3U8 Agent - AI 代理开发指南

本文档为在本 M3U8 下载器项目工作的 AI 编码助手提供指南。**以方便快捷、易于使用为优先原则**。

---

## 中文编程规范（HTML / CSS / JS / Python）

目标：在不破坏生态兼容性（工具链、浏览器、第三方库、接口协议）的前提下，尽可能在“可控范围”内使用中文命名与中文文案。

### 语言使用边界（先定规则）
- **必须英文（强约束）**：协议/标准规定的内容，或需要跨工具/跨语言稳定协作的标识符
  - HTML 标签与标准属性名（如 `class`、`data-*`、`aria-*`）
  - CSS 属性名与语法关键字（如 `display`、`@media`）
  - URL、HTTP Header、MIME、SSE 事件名、API 路由路径
  - 仓库内所有文件/目录/文件夹名（必须纯英文 ASCII，避免编码与平台兼容问题）
  - JSON 字段名（对外协议字段）与数据库字段（如有）
- **优先中文（强建议）**：面向用户的文案与业务概念表达
  - UI 文本、提示语、错误信息、日志内容（面向使用者/排障）
  - 任务名称、状态描述（如在前端展示或日志中持久化）
- **允许中文（可选）**：仅限“内部实现细节”且不对外暴露的标识符
  - JS/Python 的局部变量、内部函数（不导出/不作为回调事件名/不进入协议字段）
  - 小范围脚本或一次性工具代码（维护成本可接受）

### 文件与目录命名（强约束）
- **只能使用英文 ASCII**：`a-z`、`0-9`、`-`、`_`、`.`（不使用中文、空格、全角符号）
- **统一风格**：目录与静态资源优先 `kebab-case`；Python 模块/包使用 `snake_case`
- **避免歧义**：不使用大小写仅区分的文件名（跨平台容易出问题）

### 命名总规则
- **对外接口一律英文**：凡是会被“外部代码/外部系统/HTML/CSS 选择器/网络协议”引用的名字，用英文。
- **内部实现可中文**：仅在作用域很小、没有被导出/序列化/反射依赖时，才用中文变量/函数名。
- **一个文件一种语言为主**：不要在同一层级 API/导出符号上中英混搭；内部变量可按需要中文化。
- **格式约定**：
  - 英文变量/函数：`camelCase`（JS）/ `snake_case`（Python）
  - 英文类名：`PascalCase`
  - 常量：`UPPER_SNAKE_CASE`
  - HTML/CSS 的 class：`kebab-case`

### HTML 规范
- **标签/属性名**：只用标准英文（HTML 规范要求）
- **class/id/data-*（必须英文）**：用于 CSS/JS 选择器，必须英文 `kebab-case`
- **可中文部分**：
  - 文本内容（按钮文案、标题、提示语）
  - `title`、`aria-label`、`placeholder` 等面向用户的字符串
- **示例**
  ```html
  <button class="task-start-btn" aria-label="开始下载">开始下载</button>
  <div class="task-status" data-task-id="123">等待中</div>
  ```

### CSS 规范
- **选择器（必须英文）**：与 HTML `class/id` 一致，保持 `kebab-case`
- **CSS 变量（建议英文）**：优先用 `--color-*`、`--space-*`、`--font-*` 这类英文命名
- **可中文部分**：仅限 `content:` 等直接呈现给用户的文本（但更推荐由 HTML/JS 控制文案）
- **示例**
  ```css
  :root {
    --color-primary: #2563eb;
    --space-2: 8px;
  }

  .task-status {
    color: var(--color-primary);
    margin-top: var(--space-2);
  }
  ```

### JavaScript 规范
- **必须英文（强约束）**
  - 文件名、目录名、模块导出（`export` 的函数/变量/类）
  - DOM 选择器相关：`class/id/data-*` 的值与查询字符串
  - 与后端交互的字段名：请求/响应 JSON 的 key、SSE 事件名、API 路径
- **允许中文（可选）**
  - 局部变量（函数内部）、短生命周期的中间变量
  - 内部私有函数（不导出、不作为事件名/回调协议名）
- **建议**：对外用英文、对内可中文，用“业务名词中文化 + 技术接口英文化”的方式降低歧义。
- **示例**
  ```javascript
  export async function fetchTasks() {
      const response = await fetch(`${API_BASE_URL}/api/tasks`);
      return await response.json();
  }

  function 渲染任务列表(tasks) {
      const 容器 = document.querySelector('.task-list');
      容器.innerHTML = tasks.map((t) => `<div class="task-item">${t.name}</div>`).join('');
  }
  ```

### Python 规范
- **必须英文（强约束）**
  - 文件名/模块名/包名（如 `backend/services/downloader.py`）
  - 对外 API：FastAPI 路由函数名（可中文但不建议）、Pydantic 模型类名与字段名（对外协议字段）
  - 配置键名、持久化 JSON 的字段名（对外可读/兼容性优先）
- **允许中文（可选）**
  - 内部函数名、局部变量名（不进入序列化/不作为反射依据）
  - 业务流程中间变量（例如“分片列表”“任务队列”）在函数体内可用中文
- **示例**
  ```python
  def build_task_display_name(task_id: str) -> str:
      return f"任务 {task_id}"

  async def 计算下载进度(已完成: int, 总数: int) -> float:
      return 0.0 if 总数 == 0 else 已完成 / 总数
  ```

### 推荐落地策略（避免“全中文”带来的维护风险）
- **前端**：HTML/CSS 选择器与接口字段全部英文；页面文案与状态值中文；JS 内部中间变量可中文。
- **后端**：路由路径/模型字段/存储结构英文；日志与错误信息中文；Python 内部变量可中文。

## Python 后端指南

### 环境设置

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
- **命名规范**: 类用 `PascalCase`，函数/变量用 `snake_case`，常量用 `UPPER_SNAKE_CASE`
- **错误处理**: 简单的 try-except 即可，不必过度复杂
  ```python
  try:
      result = await process_task(task_id)
  except Exception as e:
      logger.error(f"Error: {e}")
      raise HTTPException(status_code=500, detail=str(e))
  ```

- **Async/await**: I/O 操作使用 async/await

#### Pydantic 模型
- 使用 Pydantic v2 语法
- 在 `backend/models/` 目录定义模型
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

  ```javascript
  async function getTasks() {
      const response = await fetch(`${API_BASE_URL}/api/tasks`);
      return await response.json();
  }

  // SSE 实时更新
  const eventSource = new EventSource(`${API_BASE_URL}/api/stream/tasks`);
  eventSource.addEventListener('task.progress', (e) => {
      const data = JSON.parse(e.data);
      updateProgress(data.task_id, data.percent);
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
- 配置：`backend/data/config.toml`
- 任务数据：`backend/data/tasks.json`
- 日志：`backend/data/logs/*.jsonl`

---

## 开发原则

1. **快速优先**: 不要过度设计，先实现功能
2. **简洁实用**: 代码清晰易读即可，不必追求完美
3. **灵活调整**: 根据实际情况调整规范
4. **无需复杂检查**: 跳过繁琐的安全验证和输入清理
5. **直接可用**: 能跑起来就 OK

---

## 提交前检查（简化版）

1. 确保 `python backend/main.py` 能运行
2. 确保前端页面正常显示
3. 无明显错误即可
