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
  const error = 任务.status === "failed" ? "下载失败" : 任务.error || "";
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
        <button class="btn btn-danger" data-action="delete">删除</button>
        <button class="btn btn-primary" data-action="url">链接</button>
        <button class="btn btn-info" data-action="logs">日志</button>
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
      if (动作 === "url") {
        打开任务链接(任务);
        return;
      }
      if (动作 === "logs") {
        await 打开任务日志(任务);
        return;
      }
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

let _日志弹窗遮罩 = null;
let _日志内容元素 = null;
let _日志标题元素 = null;
let _当前日志任务ID = null;
let _当前日志任务名 = "";

let _链接弹窗遮罩 = null;
let _链接内容元素 = null;
let _链接标题元素 = null;
let _当前链接任务ID = null;
let _当前链接任务名 = "";
let _当前链接 = "";

function 确保链接弹窗() {
  if (_链接弹窗遮罩) return;
  const 遮罩 = document.createElement("div");
  遮罩.className = "log-modal-backdrop";
  遮罩.innerHTML = `
    <div class="log-modal" role="dialog" aria-label="任务链接">
      <div class="log-modal-head">
        <div class="log-modal-title"></div>
        <div class="log-modal-actions">
          <button class="btn" data-url-action="copy">复制</button>
          <button class="btn btn-danger" data-url-action="close">关闭</button>
        </div>
      </div>
      <div class="log-modal-body"><pre class="log-content"></pre></div>
    </div>
  `;
  document.body.appendChild(遮罩);
  _链接弹窗遮罩 = 遮罩;
  _链接标题元素 = 遮罩.querySelector(".log-modal-title");
  _链接内容元素 = 遮罩.querySelector(".log-content");

  遮罩.addEventListener("click", (事件) => {
    if (事件.target === 遮罩) 关闭任务链接();
  });
  遮罩.querySelectorAll("button[data-url-action]").forEach((按钮) => {
    按钮.addEventListener("click", async () => {
      const 动作 = 按钮.dataset.urlAction;
      if (动作 === "close") {
        关闭任务链接();
      } else if (动作 === "copy") {
        await 复制文本(_当前链接);
        设置状态文案("已复制链接");
      }
    });
  });
}

function 关闭任务链接() {
  if (!_链接弹窗遮罩) return;
  _链接弹窗遮罩.classList.remove("is-open");
  _当前链接任务ID = null;
  _当前链接任务名 = "";
  _当前链接 = "";
}

function 打开任务链接(任务) {
  确保链接弹窗();
  _当前链接任务ID = 任务.id;
  _当前链接任务名 = 任务.name || "";
  _当前链接 = String(任务.url || "");
  _链接标题元素.textContent = `链接：${_当前链接任务名}（${_当前链接任务ID}）`;
  _链接内容元素.textContent = _当前链接 ? `${_当前链接}\n` : "（无链接）\n";
  _链接弹窗遮罩.classList.add("is-open");
  const 容器 = _链接内容元素.parentElement;
  容器.scrollTop = 0;
}

function 确保日志弹窗() {
  if (_日志弹窗遮罩) return;
  const 遮罩 = document.createElement("div");
  遮罩.className = "log-modal-backdrop";
  遮罩.innerHTML = `
    <div class="log-modal" role="dialog" aria-label="任务日志">
      <div class="log-modal-head">
        <div class="log-modal-title"></div>
        <div class="log-modal-actions">
          <button class="btn" data-log-action="refresh">刷新</button>
          <button class="btn" data-log-action="raw">原文</button>
          <button class="btn btn-danger" data-log-action="close">关闭</button>
        </div>
      </div>
      <div class="log-modal-body"><pre class="log-content"></pre></div>
    </div>
  `;
  document.body.appendChild(遮罩);
  _日志弹窗遮罩 = 遮罩;
  _日志标题元素 = 遮罩.querySelector(".log-modal-title");
  _日志内容元素 = 遮罩.querySelector(".log-content");

  遮罩.addEventListener("click", (事件) => {
    if (事件.target === 遮罩) 关闭任务日志();
  });
  遮罩.querySelectorAll("button[data-log-action]").forEach((按钮) => {
    按钮.addEventListener("click", async () => {
      const 动作 = 按钮.dataset.logAction;
      if (动作 === "close") {
        关闭任务日志();
      } else if (动作 === "refresh") {
        await 刷新任务日志();
      } else if (动作 === "raw") {
        if (_当前日志任务ID) {
          window.open(apiUrl(`/api/tasks/${_当前日志任务ID}/logs/raw`), "_blank");
        }
      }
    });
  });
  window.addEventListener("keydown", (事件) => {
    if (事件.key !== "Escape") return;
    if (_日志弹窗遮罩?.classList.contains("is-open")) 关闭任务日志();
    if (_链接弹窗遮罩?.classList.contains("is-open")) 关闭任务链接();
  });
}

function 关闭任务日志() {
  if (!_日志弹窗遮罩) return;
  _日志弹窗遮罩.classList.remove("is-open");
  _当前日志任务ID = null;
  _当前日志任务名 = "";
}

async function 打开任务日志(任务) {
  确保日志弹窗();
  _当前日志任务ID = 任务.id;
  _当前日志任务名 = 任务.name || "";
  _日志标题元素.textContent = `日志：${_当前日志任务名}（${_当前日志任务ID}）`;
  _日志内容元素.textContent = "加载中…\n";
  _日志弹窗遮罩.classList.add("is-open");
  await 刷新任务日志();
}

async function 刷新任务日志() {
  if (!_当前日志任务ID || !_日志内容元素) return;
  try {
    const 数据 = await requestJson(`/api/tasks/${_当前日志任务ID}/logs?tail=600`);
    const 行列表 = Array.isArray(数据?.lines) ? 数据.lines : [];
    const 头 = 数据?.truncated ? "（仅显示日志末尾，已截断）" : "";
    _日志标题元素.textContent = `日志：${_当前日志任务名}（${_当前日志任务ID}）${头}`;
    _日志内容元素.textContent = 行列表.join("\n") + (行列表.length ? "\n" : "");
    const 容器 = _日志内容元素.parentElement;
    容器.scrollTop = 容器.scrollHeight;
  } catch (异常) {
    _日志内容元素.textContent = `加载日志失败：${异常.message || 异常}\n`;
  }
}

function 追加任务日志行(行) {
  if (!_日志弹窗遮罩 || !_日志弹窗遮罩.classList.contains("is-open")) return;
  if (!_日志内容元素) return;
  const 容器 = _日志内容元素.parentElement;
  const 贴底 = 容器.scrollTop + 容器.clientHeight >= 容器.scrollHeight - 20;
  _日志内容元素.textContent += `${行}\n`;
  if (_日志内容元素.textContent.length > 300_000) {
    _日志内容元素.textContent = _日志内容元素.textContent.slice(-250_000);
  }
  if (贴底) 容器.scrollTop = 容器.scrollHeight;
}

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

    事件源.addEventListener("task.log", (事件) => {
      try {
        const 数据 = JSON.parse(事件.data);
        if (数据 && dataHasTaskLog(数据)) {
          if (数据.task_id === _当前日志任务ID) {
            追加任务日志行(数据.line);
          }
        }
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

function dataHasTaskLog(数据) {
  return typeof 数据.task_id === "string" && typeof 数据.line === "string";
}

async function 复制文本(文本) {
  const 最终文本 = String(文本 || "");
  try {
    await navigator.clipboard.writeText(最终文本);
    return;
  } catch {}
  const 文本框 = document.createElement("textarea");
  文本框.value = 最终文本;
  文本框.setAttribute("readonly", "readonly");
  文本框.style.position = "fixed";
  文本框.style.left = "-9999px";
  document.body.appendChild(文本框);
  文本框.select();
  try {
    document.execCommand("copy");
  } catch {}
  document.body.removeChild(文本框);
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

