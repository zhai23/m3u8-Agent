"""
配置管理模块
负责读取和管理 config.toml 配置文件
"""

import tomllib
from pathlib import Path
from typing import Optional, List, Any, Dict, Union

import toml


class Config:
    """配置管理类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路径（默认为 backend/config.toml）
        """
        if config_path is None:
            # 默认配置文件路径：backend/config.toml
            当前文件目录 = Path(__file__).parent.parent
            config_path = 当前文件目录 / "config.toml"
        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._base_dir = self.config_path.parent.resolve()

    def _解析路径(self, 路径: str) -> str:
        if not 路径:
            return 路径
        p = Path(路径)
        if p.is_absolute():
            return str(p)
        return str((self._base_dir / p).resolve())
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, "rb") as f:
            return tomllib.load(f)
    
    def reload(self):
        """重新加载配置文件"""
        self._config = self._load_config()
    
    # ========== 下载器配置 ==========
    
    @property
    def m3u8d_path(self) -> str:
        """N_m3u8DL-RE 可执行文件路径"""
        return self._解析路径(self._config["downloader"]["m3u8d_path"])
    
    @property
    def save_dir(self) -> str:
        """最终文件保存目录"""
        return self._解析路径(self._config["downloader"]["save_dir"])
    
    @property
    def tmp_dir(self) -> str:
        """临时文件目录"""
        return self._解析路径(self._config["downloader"]["tmp_dir"])
    
    @property
    def thread_count(self) -> int:
        """下载线程数"""
        return self._config["downloader"]["thread_count"]
    
    @property
    def download_retry_count(self) -> int:
        """每个分片异常时的重试次数"""
        return self._config["downloader"]["download_retry_count"]
    
    @property
    def http_request_timeout(self) -> int:
        """HTTP 请求超时时间（秒）"""
        return self._config["downloader"]["http_request_timeout"]
    
    @property
    def check_segments_count(self) -> bool:
        """检查实际下载的分片数量是否与预期匹配"""
        return self._config["downloader"]["check_segments_count"]
    
    @property
    def del_after_done(self) -> bool:
        """完成后删除临时文件"""
        return self._config["downloader"]["del_after_done"]
    
    @property
    def binary_merge(self) -> bool:
        """使用二进制合并"""
        return self._config["downloader"]["binary_merge"]
    
    @property
    def skip_merge(self) -> bool:
        """跳过合并分片"""
        return self._config["downloader"]["skip_merge"]
    
    @property
    def skip_download(self) -> bool:
        """跳过下载（仅解析）"""
        return self._config["downloader"]["skip_download"]
    
    @property
    def no_log(self) -> bool:
        """关闭日志文件写入"""
        return self._config["downloader"]["no_log"]
    
    @property
    def log_level(self) -> str:
        """日志级别"""
        return self._config["downloader"]["log_level"]
    
    @property
    def write_meta_json(self) -> bool:
        """是否将信息写入 json 文件"""
        return self._config["downloader"]["write_meta_json"]
    
    @property
    def max_speed(self) -> str:
        """限速（如 "15M" 或 "100K"）"""
        return self._config["downloader"]["max_speed"]
    
    @property
    def use_system_proxy(self) -> bool:
        """使用系统默认代理"""
        return self._config["downloader"]["use_system_proxy"]
    
    @property
    def custom_proxy(self) -> str:
        """自定义代理"""
        return self._config["downloader"]["custom_proxy"]
    
    @property
    def auto_select(self) -> bool:
        """自动选择所有类型的轨道并下载"""
        return self._config["downloader"]["auto_select"]
    
    @property
    def append_url_params(self) -> bool:
        """将 Url Params 添加至分片"""
        return self._config["downloader"]["append_url_params"]
    
    @property
    def no_date_info(self) -> bool:
        """写入时不写入日期信息"""
        return self._config["downloader"]["no_date_info"]
    
    @property
    def force_ansi_console(self) -> bool:
        """强制认定终端为支持 ANSI 的终端"""
        return self._config["downloader"]["force_ansi_console"]
    
    @property
    def sub_only(self) -> bool:
        """只选取字幕轨道"""
        return self._config["downloader"]["sub_only"]
    
    @property
    def sub_format(self) -> str:
        """字幕格式"""
        return self._config["downloader"]["sub_format"]
    
    @property
    def auto_subtitle_fix(self) -> bool:
        """自动修正字幕"""
        return self._config["downloader"]["auto_subtitle_fix"]
    
    @property
    def decryption_engine(self) -> str:
        """解密引擎"""
        return self._config["downloader"]["decryption_engine"]
    
    @property
    def mp4_real_time_decryption(self) -> bool:
        """实时解密 MP4 分片"""
        return self._config["downloader"]["mp4_real_time_decryption"]
    
    @property
    def custom_headers(self) -> List[str]:
        """自定义 HTTP 请求头"""
        return self._config["downloader"]["custom_headers"]
    
    @property
    def ffmpeg_binary_path(self) -> str:
        """FFmpeg 路径"""
        return self._解析路径(self._config["downloader"]["ffmpeg_binary_path"])
    
    @property
    def decryption_binary_path(self) -> str:
        """解密工具路径"""
        return self._解析路径(self._config["downloader"]["decryption_binary_path"])


def _默认配置文件路径() -> Path:
    return Path(__file__).resolve().parent.parent / "config.toml"


def read_config_toml(config_path: Union[str, Path, None] = None) -> Dict[str, Any]:
    路径 = Path(config_path) if config_path is not None else _默认配置文件路径()
    if not 路径.exists():
        return {}
    with open(路径, "rb") as f:
        return tomllib.load(f)


def write_config_toml(config: Dict[str, Any], config_path: Union[str, Path, None] = None):
    路径 = Path(config_path) if config_path is not None else _默认配置文件路径()
    路径.parent.mkdir(parents=True, exist_ok=True)
    文本 = toml.dumps(config or {})
    路径.write_text(文本, encoding="utf-8")


def deep_merge_dict(旧: Dict[str, Any], 新: Dict[str, Any]) -> Dict[str, Any]:
    结果: Dict[str, Any] = dict(旧 or {})
    for 键, 值 in (新 or {}).items():
        if isinstance(值, dict) and isinstance(结果.get(键), dict):
            结果[键] = deep_merge_dict(结果[键], 值)
        else:
            结果[键] = 值
    return 结果


# 全局配置实例
_global_config: Optional[Config] = None


def get_config(config_path: str = None) -> Config:
    """
    获取全局配置实例
    
    Args:
        config_path: 配置文件路径（默认为 backend/config.toml）
        
    Returns:
        Config: 配置实例
    """
    global _global_config
    if _global_config is None:
        _global_config = Config(config_path)
    return _global_config


def reload_config():
    """重新加载全局配置"""
    global _global_config
    if _global_config is not None:
        _global_config.reload()
