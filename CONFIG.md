# 配置文件说明

本文档说明 `config.toml` 配置文件中各参数的含义和用法。

## 配置文件位置

- 默认位置：`backend/config.toml`
- 可以通过代码指定其他位置

## 配置项说明

### [downloader] - 下载器配置

#### 路径配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `m3u8d_path` | string | `"./m3u8d/N_m3u8DL-RE.exe"` | N_m3u8DL-RE 可执行文件路径（相对路径以 `backend/` 为基准） |
| `save_dir` | string | `"./downloads"` | 最终文件保存目录（相对路径以 `backend/` 为基准） |
| `tmp_dir` | string | `"./downloads_tmp"` | 临时文件目录（相对路径以 `backend/` 为基准） |

#### 下载参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `thread_count` | int | `16` | 下载线程数，建议 4-32 |
| `download_retry_count` | int | `3` | 每个分片异常时的重试次数 |
| `http_request_timeout` | int | `100` | HTTP 请求超时时间（秒） |

#### 下载行为

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `check_segments_count` | bool | `true` | 检查实际下载的分片数量是否与预期匹配 |
| `del_after_done` | bool | `true` | 完成后删除临时文件 |
| `binary_merge` | bool | `false` | 使用二进制合并（更快但可能不精确） |
| `skip_merge` | bool | `false` | 跳过合并分片（仅下载不合并） |
| `skip_download` | bool | `false` | 跳过下载（仅解析 M3U8） |

#### 日志配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `no_log` | bool | `false` | 关闭日志文件写入 |
| `log_level` | string | `"INFO"` | 日志级别：DEBUG, INFO, WARN, ERROR, OFF |
| `write_meta_json` | bool | `true` | 是否将元信息写入 json 文件 |

#### 速度限制

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_speed` | string | `""` | 限速，如 `"15M"` 或 `"100K"`，留空表示不限速 |

#### 代理配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `use_system_proxy` | bool | `true` | 使用系统默认代理 |
| `custom_proxy` | string | `""` | 自定义代理，如 `"http://127.0.0.1:8888"` |

#### 高级选项

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `auto_select` | bool | `false` | 自动选择所有类型的轨道并下载 |
| `append_url_params` | bool | `false` | 将 URL 参数添加至分片（某些网站需要） |
| `no_date_info` | bool | `false` | 写入时不写入日期信息 |
| `force_ansi_console` | bool | `false` | 强制认定终端为支持 ANSI 的终端 |

#### 字幕相关

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `sub_only` | bool | `false` | 只选取字幕轨道 |
| `sub_format` | string | `"SRT"` | 字幕格式：SRT 或 VTT |
| `auto_subtitle_fix` | bool | `true` | 自动修正字幕 |

#### 解密相关

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `decryption_engine` | string | `"MP4DECRYPT"` | 解密引擎：MP4DECRYPT, SHAKA_PACKAGER, FFMPEG |
| `mp4_real_time_decryption` | bool | `false` | 实时解密 MP4 分片 |

#### 自定义工具路径

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `ffmpeg_binary_path` | string | `""` | FFmpeg 路径，留空则使用系统 PATH |
| `decryption_binary_path` | string | `""` | 解密工具路径，留空则使用默认 |

#### 自定义 HTTP 请求头

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `custom_headers` | array | `[]` | 自定义 HTTP 请求头列表 |

**示例**：
```toml
custom_headers = [
    "Cookie: mycookie=value",
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer: https://example.com"
]
```

## 使用示例

### 1. 基础使用（使用配置文件默认值）

```python
from backend.core.downloader import SimpleDownloader

下载器 = SimpleDownloader()
下载器.download(
    url="https://example.com/video.m3u8",
    save_name="我的视频"
)
```

### 2. 覆盖部分配置

```python
下载器.download(
    url="https://example.com/video.m3u8",
    save_name="我的视频",
    thread_count=8,  # 覆盖配置文件中的线程数
    save_dir="./custom_dir"  # 覆盖保存目录
)
```

### 3. 使用自定义请求头

```python
下载器.download(
    url="https://example.com/video.m3u8",
    save_name="我的视频",
    custom_headers=[
        "Cookie: session=abc123",
        "User-Agent: MyApp/1.0"
    ]
)
```

### 4. 覆盖更多参数

```python
下载器.download(
    url="https://example.com/video.m3u8",
    save_name="我的视频",
    thread_count=4,
    download_retry_count=5,  # 增加重试次数
    max_speed="10M",  # 限速 10MB/s
    binary_merge=True  # 使用二进制合并
)
```

## 常见配置场景

### 场景 1：快速下载（不限速，多线程）

```toml
thread_count = 32
max_speed = ""
binary_merge = true
```

### 场景 2：稳定下载（限速，少线程）

```toml
thread_count = 4
max_speed = "5M"
download_retry_count = 5
```

### 场景 3：需要代理

```toml
use_system_proxy = false
custom_proxy = "http://127.0.0.1:7890"
```

### 场景 4：需要自定义请求头

```toml
custom_headers = [
    "Cookie: auth_token=your_token",
    "User-Agent: Mozilla/5.0",
    "Referer: https://source-website.com"
]
```

## 注意事项

1. **路径分隔符**：Windows 下可以使用 `/` 或 `\\`，建议使用 `/`
2. **布尔值**：使用 `true` 或 `false`（小写）
3. **字符串**：使用双引号 `""`
4. **数组**：使用方括号 `[]`，元素用逗号分隔
5. **修改配置后**：需要重启程序或调用 `reload_config()` 重新加载

## 配置优先级

参数的优先级从高到低：

1. 代码中直接传递的参数（`download()` 方法的参数）
2. 配置文件中的值
3. 程序内置的默认值

这意味着你可以在配置文件中设置常用值，在需要时通过代码参数临时覆盖。
