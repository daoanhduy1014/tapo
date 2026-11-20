"""Điều khiển xoay/nghiêng (PTZ) và tính năng camera qua thư viện pytapo."""

from __future__ import annotations

import threading
from typing import Callable

from .config import CameraConfig

try:
    from pytapo import Tapo  # type: ignore
except Exception:  # pragma: no cover - pytapo là tùy chọn
    Tapo = None


class PTZController:
    """Gửi lệnh tới camera trong thread nền để không làm đơ giao diện."""

    def __init__(self, cam: CameraConfig):
        self.cam = cam
        self._client = None
        self._lock = threading.Lock()

    @staticmethod
    def available() -> bool:
        return Tapo is not None

    def _get_client(self):
        if Tapo is None:
            raise RuntimeError("Chưa cài thư viện pytapo (pip install pytapo)")
        if self._client is None:
            if self.cam.cloud_password:
                # Firmware mới: đăng nhập bằng 'admin' + mật khẩu tài khoản TP-Link
                self._client = Tapo(self.cam.ip, "admin", self.cam.cloud_password,
                                    self.cam.cloud_password, printWarnInformation=False)
            else:
                self._client = Tapo(self.cam.ip, self.cam.username, self.cam.password,
                                    printWarnInformation=False)
        return self._client

    def _run(self, fn: Callable, on_done: Callable[[object, Exception | None], None] | None):
        def worker():
            with self._lock:
                try:
                    result = fn(self._get_client())
                    err = None
                except Exception as e:  # noqa: BLE001
                    self._client = None  # buộc đăng nhập lại lần sau
                    result, err = None, e
            if on_done:
                on_done(result, err)
        threading.Thread(target=worker, daemon=True).start()

    # Các lệnh -----------------------------------------------------------------
    def move(self, x: int, y: int, on_done=None):
        self._run(lambda c: c.moveMotor(x, y), on_done)

    def calibrate(self, on_done=None):
        self._run(lambda c: c.calibrateMotor(), on_done)

    def get_privacy(self, on_done=None):
        self._run(lambda c: c.getPrivacyMode().get("enabled") == "on", on_done)

    def set_privacy(self, enabled: bool, on_done=None):
        self._run(lambda c: c.setPrivacyMode(enabled), on_done)

    def set_led(self, enabled: bool, on_done=None):
        self._run(lambda c: c.setLEDEnabled(enabled), on_done)

    def set_day_night(self, mode: str, on_done=None):
        # mode: "auto" | "on" (hồng ngoại/ban đêm) | "off" (ban ngày)
        self._run(lambda c: c.setDayNightMode(mode), on_done)

    def get_presets(self, on_done=None):
        self._run(lambda c: c.getPresets(), on_done)

    def goto_preset(self, preset_id: str, on_done=None):
        self._run(lambda c: c.setPreset(preset_id), on_done)

    def save_preset(self, name: str, on_done=None):
        self._run(lambda c: c.savePreset(name), on_done)
