const API_BASE_URL = (typeof API_CONFIG !== "undefined" && API_CONFIG.baseURL) || "";

function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

async function requestJson(path, options = {}) {
  const 超时 = (typeof API_CONFIG !== "undefined" && API_CONFIG.timeout) || 30000;
  const 控制器 = new AbortController();
  const 定时器 = setTimeout(() => 控制器.abort(), 超时);
  try {
    const 响应 = await fetch(apiUrl(path), {
      ...options,
      signal: 控制器.signal,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });
    if (!响应.ok) {
      const 文本 = await 响应.text();
      throw new Error(`请求失败: ${响应.status} ${文本}`);
    }
    if (响应.status === 204) return null;
    return await 响应.json();
  } finally {
    clearTimeout(定时器);
  }
}

function 设置状态文案(文本) {
  const 状态栏 = document.getElementById("app-status");
  状态栏.textContent = 文本;
}

function 状态类名(状态) {
  if (状态 === "running") return "pill-running";
  if (状态 === "completed") return "pill-completed";
  if (状态 === "failed") return "pill-failed";
  if (状态 === "paused") return "pill-paused";
  return "";
}

function 状态中文(状态) {
  if (状态 === "pending") return "等待中";
  if (状态 === "running") return "下载中";
  if (状态 === "paused") return "已暂停";
  if (状态 === "completed") return "已完成";
  if (状态 === "failed") return "失败";
  return 状态 || "未知";
}

function 渲染任务(任务) {
  const percent = Math.max(0, Math.min(100, Number(任务.progress || 0)));
  const speed = 任务.speed || "—";
  const eta = 任务.eta || "—";
  const error = 任务.error || "";
  const item = document.createElement("div");
  item.className = "task-item";
  item.dataset.taskId = 任务.id;

  item.innerHTML = `
    <div class="task-top">
      <div>
        <div class="task-name">${escapeHtml(任务.name)}</div>
        <div class="task-meta">
          <span class="pill ${状态类名(任务.status)}">${状态中文(任务.status)}</span>
          <span class="pill">进度 ${percent.toFixed(1)}%</span>
          <span class="pill">速度 ${escapeHtml(speed)}</span>
          <span class="pill">剩余 ${escapeHtml(eta)}</span>
        </div>
      </div>
      <div class="task-actions">
        <button class="btn btn-success" data-action="start">开始</button>
        <button class="btn btn-warning" data-action="pause">暂停</button>
        <button class="btn" data-action="delete">删除</button>
      </div>
    </div>
    <div class="task-progress">
      <div class="progress-bar"><div style="width:${percent}%"></div></div>
      <div class="task-meta">${error ? `错误：${escapeHtml(error)}` : ""}</div>
    </div>
  `;

  item.querySelectorAll("button[data-action]").forEach((按钮) => {
    按钮.addEventListener("click", async () => {
      const 动作 = 按钮.dataset.action;
      await 执行动作(任务.id, 动作);
    });
  });

  return item;
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

let _加载任务列表序号 = 0;
let _刷新定时器 = null;

function 安排刷新() {
  if (_刷新定时器) return;
  _刷新定时器 = setTimeout(() => {
    _刷新定时器 = null;
    加载任务列表();
  }, 120);
}

async function 加载任务列表() {
  const 列表容器 = document.getElementById("task-list");
  const 当前序号 = ++_加载任务列表序号;
  try {
    const 任务列表 = await requestJson("/api/tasks");
    if (当前序号 !== _加载任务列表序号) return;

    const 片段 = document.createDocumentFragment();
    if (!Array.isArray(任务列表) || 任务列表.length === 0) {
      const 空 = document.createElement("div");
      空.className = "task-item";
      空.textContent = "暂无任务";
      片段.appendChild(空);
      列表容器.replaceChildren(片段);
      return;
    }
    for (const 任务 of 任务列表) {
      片段.appendChild(渲染任务(任务));
    }
    列表容器.replaceChildren(片段);
  } catch (异常) {
    if (当前序号 !== _加载任务列表序号) return;
    const 失败 = document.createElement("div");
    失败.className = "task-item";
    失败.textContent = `加载失败：${异常.message || 异常}`;
    列表容器.replaceChildren(失败);
  }
}

function 更新任务卡片进度(任务ID, percent, speed, eta) {
  const 卡片 = document.querySelector(`.task-item[data-task-id="${CSS.escape(任务ID)}"]`);
  if (!卡片) return;
  const 进度条 = 卡片.querySelector(".progress-bar > div");
  const pills = 卡片.querySelectorAll(".task-meta .pill");
  const 百分比 = Math.max(0, Math.min(100, Number(percent || 0)));
  if (进度条) 进度条.style.width = `${百分比}%`;
  if (pills && pills.length >= 4) {
    pills[1].textContent = `进度 ${百分比.toFixed(1)}%`;
    pills[2].textContent = `速度 ${speed || "—"}`;
    pills[3].textContent = `剩余 ${eta || "—"}`;
  }
}

async function 执行动作(任务ID, 动作) {
  try {
    if (动作 === "start") {
      await requestJson(`/api/tasks/${任务ID}/start`, { method: "POST", body: "{}" });
    } else if (动作 === "pause") {
      await requestJson(`/api/tasks/${任务ID}/pause`, { method: "POST", body: "{}" });
    } else if (动作 === "delete") {
      await requestJson(`/api/tasks/${任务ID}`, { method: "DELETE" });
    }
    await 加载任务列表();
  } catch (异常) {
    设置状态文案(`操作失败：${异常.message || 异常}`);
  }
}

function 启动SSE() {
  const 重连间隔 = (typeof API_CONFIG !== "undefined" && API_CONFIG.reconnectInterval) || 3000;
  let 事件源 = null;
  let 重连定时器 = null;

  function 连接() {
    if (事件源) {
      try {
        事件源.close();
      } catch {}
      事件源 = null;
    }
    设置状态文案("已连接（SSE）");
    事件源 = new EventSource(apiUrl("/api/stream/tasks"));

    事件源.addEventListener("task.created", () => 安排刷新());

    事件源.addEventListener("task.completed", () => 安排刷新());

    事件源.addEventListener("task.failed", () => 安排刷新());

    事件源.addEventListener("task.progress", (事件) => {
      try {
        const 数据 = JSON.parse(事件.data);
        更新任务卡片进度(数据.task_id, 数据.percent, 数据.speed, 数据.eta);
      } catch {}
    });

    事件源.addEventListener("ping", () => {});

    事件源.onerror = () => {
      设置状态文案("连接断开，正在重连…");
      if (重连定时器) return;
      try {
        事件源.close();
      } catch {}
      事件源 = null;
      重连定时器 = setTimeout(() => {
        重连定时器 = null;
        连接();
      }, 重连间隔);
    };
  }

  连接();
}

document.getElementById("refresh-btn").addEventListener("click", async () => {
  await 加载任务列表();
});

document.getElementById("task-form").addEventListener("submit", async (事件) => {
  事件.preventDefault();
  const urlInput = document.getElementById("task-url");
  const nameInput = document.getElementById("task-name");
  const 链接 = urlInput.value.trim();
  const 名称 = nameInput.value.trim();
  if (!链接 || !名称) return;
  try {
    await requestJson("/api/tasks", { method: "POST", body: JSON.stringify({ url: 链接, name: 名称 }) });
    urlInput.value = "";
    nameInput.value = "";
    await 加载任务列表();
  } catch (异常) {
    设置状态文案(`创建失败：${异常.message || 异常}`);
  }
});

(async () => {
  await 加载任务列表();
  启动SSE();
})();

