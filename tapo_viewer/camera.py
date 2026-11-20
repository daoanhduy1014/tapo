"""Luồng đọc video RTSP từ camera (chạy nền, tự kết nối lại)."""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime
from pathlib import Path

# RTSP qua TCP ổn định hơn UDP qua Wi-Fi; timeout 5s để phát hiện mất kết nối nhanh.
os.environ.setdefault(
    "OPENCV_FFMPEG_CAPTURE_OPTIONS",
    "rtsp_transport;tcp|timeout;5000000",
)
os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")
os.environ.setdefault("OPENCV_FFMPEG_LOGLEVEL", "-8")

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from .config import CameraConfig  # noqa: E402


class CameraStream:
    """Đọc khung hình liên tục trong một thread riêng."""

    def __init__(self, cam: CameraConfig):
        self.cam = cam
        self._lock = threading.Lock()
        self._frame: np.ndarray | None = None
        self.frame_id = 0
        self.status = "Đang kết nối..."
        self.connected = False
        self.fps = 0.0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._writer: cv2.VideoWriter | None = None
        self._record_request: Path | None = None
        self.record_file: Path | None = None
        self._stop_record = False

    # ------------------------------------------------------------------ control
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name=f"cam-{self.cam.name}", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self.stop_recording()
        if self._thread:
            self._thread.join(timeout=3)
        self._close_writer()

    def get_frame(self) -> tuple[int, np.ndarray | None]:
        with self._lock:
            return self.frame_id, self._frame

    # ---------------------------------------------------------------- recording
    @property
    def recording(self) -> bool:
        return self._writer is not None or self._record_request is not None

    def start_recording(self, folder: Path) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = folder / f"{_safe_name(self.cam.name)}_{ts}.mp4"
        self._stop_record = False
        self._record_request = path
        return path

    def stop_recording(self) -> Path | None:
        path = self.record_file or self._record_request
        self._record_request = None
        self._stop_record = True
        return path

    def snapshot(self, folder: Path) -> Path | None:
        _, frame = self.get_frame()
        if frame is None:
            return None
        folder.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = folder / f"{_safe_name(self.cam.name)}_{ts}.jpg"
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if not ok:
            return None
        path.write_bytes(buf.tobytes())  # ghi bằng Python để hỗ trợ đường dẫn tiếng Việt
        return path

    # ------------------------------------------------------------------ worker
    def _run(self) -> None:
        backoff = 1.0
        while not self._stop.is_set():
            self.status = "Đang kết nối..."
            cap = cv2.VideoCapture(self.cam.rtsp_url(), cv2.CAP_FFMPEG)
            if not cap.isOpened():
                cap.release()
                self.connected = False
                self.status = f"Không kết nối được, thử lại sau {int(backoff)}s"
                if self._stop.wait(backoff):
                    break
                backoff = min(backoff * 2, 30)
                continue

            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            src_fps = cap.get(cv2.CAP_PROP_FPS)
            if not src_fps or src_fps > 60 or src_fps < 1:
                src_fps = 15.0
            is_file = os.path.isfile(self.cam.rtsp_url())
            self.connected = True
            self.status = "Đang phát"
            backoff = 1.0
            fails = 0
            t0, n = time.monotonic(), 0

            while not self._stop.is_set():
                ok, frame = cap.read()
                if not ok or frame is None:
                    if is_file:  # file video thử nghiệm: phát lặp lại
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    fails += 1
                    if fails > 20:
                        break
                    time.sleep(0.05)
                    continue
                fails = 0
                with self._lock:
                    self._frame = frame
                    self.frame_id += 1
                self._handle_recording(frame, src_fps)

                n += 1
                dt = time.monotonic() - t0
                if dt >= 2:
                    self.fps = n / dt
                    t0, n = time.monotonic(), 0
                if is_file:
                    time.sleep(1.0 / src_fps)

            cap.release()
            self.connected = False
            self._close_writer()
            if not self._stop.is_set():
                self.status = "Mất kết nối, đang kết nối lại..."
                self._stop.wait(1)
        self.connected = False
        self.status = "Đã dừng"

    def _handle_recording(self, frame: np.ndarray, fps: float) -> None:
        if self._stop_record:
            self._stop_record = False
            self._close_writer()
        if self._record_request is not None and self._writer is None:
            path = self._record_request
            self._record_request = None
            h, w = frame.shape[:2]
            writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
            if writer.isOpened():
                self._writer = writer
                self.record_file = path
            else:
                writer.release()
                self.status = "Lỗi: không tạo được file ghi hình"
        if self._writer is not None:
            self._writer.write(frame)

    def _close_writer(self) -> None:
        if self._writer is not None:
            self._writer.release()
            self._writer = None
        self.record_file = None


def _safe_name(name: str) -> str:
    keep = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return keep.strip("_") or "camera"
