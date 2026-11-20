"""Đọc/ghi cấu hình camera (config.json)."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import quote


def app_dir() -> Path:
    """Thư mục chứa dữ liệu của ứng dụng (cạnh file .exe hoặc main.py)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


CONFIG_PATH = app_dir() / "config.json"
SNAPSHOT_DIR = app_dir() / "snapshots"
RECORD_DIR = app_dir() / "recordings"


@dataclass
class CameraConfig:
    name: str = "Camera"
    ip: str = ""
    username: str = ""          # Tài khoản camera (Tapo app > Cài đặt nâng cao > Tài khoản camera)
    password: str = ""
    stream: str = "stream1"     # stream1 = HD (1080p), stream2 = SD (360p)
    port: int = 554
    cloud_password: str = ""    # Mật khẩu tài khoản TP-Link/Tapo, dùng cho điều khiển xoay (PTZ)
    custom_url: str = ""        # Nếu điền: dùng URL/đường dẫn này thay cho RTSP tự tạo

    def rtsp_url(self) -> str:
        if self.custom_url.strip():
            return self.custom_url.strip()
        user = quote(self.username, safe="")
        pwd = quote(self.password, safe="")
        auth = f"{user}:{pwd}@" if user else ""
        return f"rtsp://{auth}{self.ip}:{self.port}/{self.stream}"

    def safe_url(self) -> str:
        """URL đã ẩn mật khẩu, dùng để hiển thị/log."""
        if self.custom_url.strip():
            return self.custom_url.strip()
        return f"rtsp://{self.username}:***@{self.ip}:{self.port}/{self.stream}"


@dataclass
class AppConfig:
    cameras: list[CameraConfig] = field(default_factory=list)
    layout: str = "auto"        # auto | 1 | 4 | 9 | 16
    record_dir: str = ""
    snapshot_dir: str = ""

    def snapshot_path(self) -> Path:
        return Path(self.snapshot_dir) if self.snapshot_dir else SNAPSHOT_DIR

    def record_path(self) -> Path:
        return Path(self.record_dir) if self.record_dir else RECORD_DIR


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    if not path.exists():
        return AppConfig()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AppConfig()
    known = set(CameraConfig.__dataclass_fields__)
    cams = [CameraConfig(**{k: v for k, v in c.items() if k in known})
            for c in data.get("cameras", [])]
    return AppConfig(
        cameras=cams,
        layout=str(data.get("layout", "auto")),
        record_dir=data.get("record_dir", ""),
        snapshot_dir=data.get("snapshot_dir", ""),
    )


def save_config(cfg: AppConfig, path: Path = CONFIG_PATH) -> None:
    data = {
        "cameras": [asdict(c) for c in cfg.cameras],
        "layout": cfg.layout,
        "record_dir": cfg.record_dir,
        "snapshot_dir": cfg.snapshot_dir,
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
