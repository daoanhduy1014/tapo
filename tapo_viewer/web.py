"""Bản web của Tapo Viewer: xem camera qua trình duyệt, có đăng nhập.

Chạy trên một máy tính CÙNG MẠNG với camera:  python web.py
Rồi mở http://<IP-máy-đó>:8080 (hoặc link Tailscale/Cloudflare để xem từ xa).
"""

from __future__ import annotations

import secrets
import socket
import threading
import time
from collections import defaultdict, deque
from datetime import timedelta
from functools import wraps

import cv2
from flask import Flask, Response, abort, jsonify, redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from . import __version__
from .camera import CameraStream
from .config import AppConfig, CameraConfig, load_config, save_config
from .ptz import PTZController
from .web_ui import LOGIN_HTML, MAIN_HTML, SETUP_HTML, page

CAMERA_FIELDS = ("name", "ip", "username", "stream", "port", "custom_url")
SECRET_FIELDS = ("password", "cloud_password")


# =============================================================================
class Manager:
    """Giữ cấu hình + các luồng camera, dùng chung cho mọi người xem."""

    def __init__(self):
        self.lock = threading.RLock()
        self.cfg: AppConfig = load_config()
        if not self.cfg.web_secret:
            self.cfg.web_secret = secrets.token_hex(32)
            self.save()
        self.streams: list[CameraStream] = []
        self.ptz: dict[int, PTZController] = {}
        self._jpeg: dict[tuple[int, int], tuple[int, bytes]] = {}
        self._jpeg_lock = threading.Lock()
        self.restart_streams()

    def save(self):
        save_config(self.cfg)

    def restart_streams(self):
        with self.lock:
            for s in self.streams:
                s.stop()
            self.streams = [CameraStream(c) for c in self.cfg.cameras]
            self.ptz = {}
            with self._jpeg_lock:
                self._jpeg.clear()
            for s in self.streams:
                s.start()

    def get(self, idx: int) -> CameraStream | None:
        with self.lock:
            return self.streams[idx] if 0 <= idx < len(self.streams) else None

    def get_ptz(self, idx: int) -> PTZController | None:
        with self.lock:
            s = self.get(idx)
            if s is None:
                return None
            if idx not in self.ptz:
                self.ptz[idx] = PTZController(s.cam)
            return self.ptz[idx]

    def jpeg(self, s: CameraStream, width: int, quality: int = 75) -> tuple[int, bytes | None]:
        """Mã hóa JPEG một lần cho mỗi khung hình + kích thước, dùng chung cho mọi người xem."""
        fid, frame = s.get_frame()
        if frame is None:
            return -1, None
        key = (id(s), width)
        with self._jpeg_lock:
            hit = self._jpeg.get(key)
            if hit and hit[0] == fid:
                return hit
        h, w = frame.shape[:2]
        if width and w > width:
            frame = cv2.resize(frame, (width, int(h * width / w)), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if not ok:
            return -1, None
        data = (fid, buf.tobytes())
        with self._jpeg_lock:
            self._jpeg[key] = data
        return data


# =============================================================================
class LoginLimiter:
    """Chống dò mật khẩu: khóa tạm sau nhiều lần đăng nhập sai."""

    WINDOW = 600  # 10 phút

    def __init__(self, per_ip=5, total=30):
        self.per_ip, self.total = per_ip, total
        self.fails: dict[str, deque] = defaultdict(deque)
        self.all: deque = deque()
        self.lock = threading.Lock()

    def _trim(self, q: deque, now: float):
        while q and now - q[0] > self.WINDOW:
            q.popleft()

    def blocked(self, ip: str) -> bool:
        now = time.time()
        with self.lock:
            self._trim(self.fails[ip], now)
            self._trim(self.all, now)
            return len(self.fails[ip]) >= self.per_ip or len(self.all) >= self.total

    def fail(self, ip: str):
        now = time.time()
        with self.lock:
            self.fails[ip].append(now)
            self.all.append(now)

    def ok(self, ip: str):
        with self.lock:
            self.fails.pop(ip, None)


# =============================================================================
def create_app(mgr: Manager | None = None) -> Flask:
    mgr = mgr or Manager()
    app = Flask(__name__)
    app.secret_key = mgr.cfg.web_secret
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        MAX_CONTENT_LENGTH=64 * 1024,
    )
    limiter = LoginLimiter()
    app.extensions["tapo_manager"] = mgr

    def client_ip() -> str:
        # Khi chạy sau Cloudflare Tunnel / Tailscale, kết nối đến từ 127.0.0.1
        if request.remote_addr in ("127.0.0.1", "::1"):
            fwd = request.headers.get("CF-Connecting-IP") or request.headers.get("X-Forwarded-For", "")
            if fwd:
                return fwd.split(",")[0].strip()
        return request.remote_addr or "?"

    def current_user():
        name = session.get("user")
        if not name:
            return None
        u = mgr.cfg.web_users.get(name)
        # Đăng xuất nếu tài khoản bị xóa hoặc đổi mật khẩu
        if not u or session.get("v") != u["hash"][-12:]:
            session.clear()
            return None
        return {"name": name, "role": u.get("role", "viewer")}

    def login_required(admin=False):
        def deco(fn):
            @wraps(fn)
            def wrapper(*a, **kw):
                u = current_user()
                is_api = request.path.startswith(("/api/", "/stream/", "/snapshot/"))
                if not u:
                    if is_api:
                        return jsonify(error="Chưa đăng nhập"), 401
                    return redirect("/setup" if not mgr.cfg.web_users else "/login")
                if admin and u["role"] != "admin":
                    return jsonify(error="Chỉ quản trị viên được làm thao tác này"), 403
                # Chống CSRF: yêu cầu thay đổi phải do JavaScript của trang gửi
                if request.method != "GET" and request.headers.get("X-Requested-With") != "tapo":
                    return jsonify(error="Yêu cầu không hợp lệ"), 400
                return fn(*a, **kw)
            return wrapper
        return deco

    def start_session(name: str):
        session.clear()
        session.permanent = True
        session["user"] = name
        session["v"] = mgr.cfg.web_users[name]["hash"][-12:]

    @app.after_request
    def headers(resp):
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "no-referrer"
        if resp.mimetype == "text/html":
            resp.headers["Cache-Control"] = "no-store"
        return resp

    # ------------------------------------------------------------- pages
    @app.get("/")
    @login_required()
    def index():
        return page(MAIN_HTML, version=__version__)

    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        if mgr.cfg.web_users:
            return redirect("/login")
        err = ""
        if request.method == "POST":
            name = request.form.get("username", "").strip()
            pw = request.form.get("password", "")
            if not name or len(name) > 32:
                err = "Tên đăng nhập không hợp lệ."
            elif len(pw) < 8:
                err = "Mật khẩu cần ít nhất 8 ký tự."
            elif pw != request.form.get("password2", ""):
                err = "Hai mật khẩu không khớp."
            else:
                with mgr.lock:
                    if mgr.cfg.web_users:  # có người tạo trước
                        return redirect("/login")
                    mgr.cfg.web_users[name] = {"hash": generate_password_hash(pw), "role": "admin"}
                    mgr.save()
                start_session(name)
                return redirect("/")
        return page(SETUP_HTML, error=err)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if not mgr.cfg.web_users:
            return redirect("/setup")
        err = ""
        if request.method == "POST":
            ip = client_ip()
            if limiter.blocked(ip):
                err = "Sai quá nhiều lần. Vui lòng thử lại sau 10 phút."
            else:
                name = request.form.get("username", "").strip()
                pw = request.form.get("password", "")
                u = mgr.cfg.web_users.get(name)
                if u and check_password_hash(u["hash"], pw):
                    limiter.ok(ip)
                    start_session(name)
                    return redirect("/")
                limiter.fail(ip)
                time.sleep(0.5)
                err = "Sai tên đăng nhập hoặc mật khẩu."
        return page(LOGIN_HTML, error=err)

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect("/login")

    # ----------------------------------------------------------- streams
    @app.get("/stream/<int:idx>.mjpg")
    @login_required()
    def stream(idx):
        s = mgr.get(idx)
        if s is None:
            abort(404)
        width = max(160, min(int(request.args.get("w", 640)), 1920))
        fps = max(1, min(int(request.args.get("fps", 10)), 25))
        quality = 80 if width >= 1280 else 70

        def gen():
            last, interval = -1, 1.0 / fps
            idle = 0
            while True:
                cur = mgr.get(idx)
                if cur is not s:  # camera bị sửa/xóa: kết thúc luồng
                    return
                fid, jpg = mgr.jpeg(s, width, quality)
                if jpg is not None and fid != last:
                    last, idle = fid, 0
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                           + str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n")
                else:
                    idle += 1
                    if idle > 600 / interval and jpg is None:  # 10 phút không có hình
                        return
                time.sleep(interval)

        return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame",
                        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})

    @app.get("/snapshot/<int:idx>.jpg")
    @login_required()
    def snapshot(idx):
        s = mgr.get(idx)
        if s is None:
            abort(404)
        _, frame = s.get_frame()
        if frame is None:
            return jsonify(error="Chưa có hình"), 503
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        name = time.strftime(f"{_ascii(s.cam.name)}_%Y%m%d_%H%M%S.jpg")
        return Response(buf.tobytes(), mimetype="image/jpeg", headers={
            "Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store"})

    # --------------------------------------------------------------- API
    @app.get("/api/status")
    @login_required()
    def status():
        u = current_user()
        cams = []
        with mgr.lock:
            for i, s in enumerate(mgr.streams):
                cams.append({
                    "id": i, "name": s.cam.name, "connected": s.connected, "status": s.status,
                    "fps": round(s.fps, 1), "recording": s.recording,
                    "ptz": bool(s.cam.ip) and PTZController.available(),
                })
        return jsonify(user=u, cameras=cams)

    @app.post("/api/cam/<int:idx>/<action>")
    @login_required()
    def cam_action(idx, action):
        u = current_user()
        s = mgr.get(idx)
        if s is None:
            abort(404)
        data = request.get_json(silent=True) or {}
        admin_only = {"record", "privacy", "led", "night", "calibrate", "save_preset"}
        if action in admin_only and u["role"] != "admin":
            return jsonify(error="Chỉ quản trị viên được làm thao tác này"), 403

        if action == "record":
            if s.recording:
                path = s.stop_recording()
                return jsonify(ok=True, recording=False, msg=f"Đã lưu video trên máy chủ: {path.name if path else ''}")
            if not s.connected:
                return jsonify(error="Camera chưa kết nối"), 409
            path = s.start_recording(mgr.cfg.record_path())
            return jsonify(ok=True, recording=True, msg=f"Bắt đầu ghi: {path.name}")

        p = mgr.get_ptz(idx)
        if p is None or not s.cam.ip:
            return jsonify(error="Camera này không hỗ trợ điều khiển"), 400
        if not PTZController.available():
            return jsonify(error="Máy chủ chưa cài pytapo"), 500

        if action == "move":
            x = _clamp(data.get("x", 0), -90, 90)
            y = _clamp(data.get("y", 0), -90, 90)
            return _wait(lambda cb: p.move(x, y, cb))
        if action == "calibrate":
            return _wait(lambda cb: p.calibrate(cb))
        if action == "privacy":
            return _wait(lambda cb: p.set_privacy(bool(data.get("enabled")), cb))
        if action == "led":
            return _wait(lambda cb: p.set_led(bool(data.get("enabled")), cb))
        if action == "night":
            mode = data.get("mode")
            if mode not in ("auto", "on", "off"):
                return jsonify(error="Chế độ không hợp lệ"), 400
            return _wait(lambda cb: p.set_day_night(mode, cb))
        if action == "presets":
            return _wait(lambda cb: p.get_presets(cb), key="presets")
        if action == "goto_preset":
            return _wait(lambda cb: p.goto_preset(str(data.get("id", "")), cb))
        if action == "save_preset":
            name = str(data.get("name", "")).strip()[:30]
            if not name:
                return jsonify(error="Thiếu tên vị trí"), 400
            return _wait(lambda cb: p.save_preset(name, cb))
        abort(404)

    # ------------------------------------------------- admin: cameras
    @app.get("/api/cameras")
    @login_required(admin=True)
    def list_cameras():
        out = []
        for c in mgr.cfg.cameras:
            d = {k: getattr(c, k) for k in CAMERA_FIELDS}
            for k in SECRET_FIELDS:  # không gửi mật khẩu về trình duyệt
                d["has_" + k] = bool(getattr(c, k))
            out.append(d)
        return jsonify(cameras=out)

    @app.post("/api/cameras")
    @app.post("/api/cameras/<int:idx>")
    @login_required(admin=True)
    def save_camera(idx=None):
        d = request.get_json(silent=True) or {}
        with mgr.lock:
            old = mgr.cfg.cameras[idx] if idx is not None and idx < len(mgr.cfg.cameras) else None
            if idx is not None and old is None:
                abort(404)
            try:
                port = int(d.get("port") or 554)
            except (TypeError, ValueError):
                return jsonify(error="Cổng phải là số"), 400
            cam = CameraConfig(
                name=str(d.get("name", "")).strip()[:40] or str(d.get("ip", "")),
                ip=str(d.get("ip", "")).strip(),
                username=str(d.get("username", "")).strip(),
                stream="stream2" if d.get("stream") == "stream2" else "stream1",
                port=port,
                custom_url=str(d.get("custom_url", "")).strip(),
            )
            for k in SECRET_FIELDS:  # để trống = giữ mật khẩu cũ
                v = d.get(k) or ""
                setattr(cam, k, v if v else (getattr(old, k) if old else ""))
            if not cam.ip and not cam.custom_url:
                return jsonify(error="Cần nhập địa chỉ IP camera"), 400
            if old is None:
                mgr.cfg.cameras.append(cam)
            else:
                mgr.cfg.cameras[idx] = cam
            mgr.save()
            mgr.restart_streams()
        return jsonify(ok=True)

    @app.delete("/api/cameras/<int:idx>")
    @login_required(admin=True)
    def delete_camera(idx):
        with mgr.lock:
            if not 0 <= idx < len(mgr.cfg.cameras):
                abort(404)
            del mgr.cfg.cameras[idx]
            mgr.save()
            mgr.restart_streams()
        return jsonify(ok=True)

    # --------------------------------------------------- admin: users
    @app.get("/api/users")
    @login_required(admin=True)
    def list_users():
        return jsonify(users=[{"name": n, "role": u.get("role", "viewer")}
                              for n, u in mgr.cfg.web_users.items()])

    @app.post("/api/users")
    @login_required(admin=True)
    def save_user():
        d = request.get_json(silent=True) or {}
        name = str(d.get("name", "")).strip()
        pw = str(d.get("password", ""))
        role = "admin" if d.get("role") == "admin" else "viewer"
        if not name or len(name) > 32:
            return jsonify(error="Tên đăng nhập không hợp lệ"), 400
        with mgr.lock:
            exists = name in mgr.cfg.web_users
            if not exists and len(pw) < 8:
                return jsonify(error="Mật khẩu cần ít nhất 8 ký tự"), 400
            if pw and len(pw) < 8:
                return jsonify(error="Mật khẩu cần ít nhất 8 ký tự"), 400
            if exists and role != "admin" and _admins(mgr) == [name]:
                return jsonify(error="Phải còn ít nhất một quản trị viên"), 400
            u = mgr.cfg.web_users.get(name, {})
            if pw:
                u["hash"] = generate_password_hash(pw)
            u["role"] = role
            mgr.cfg.web_users[name] = u
            mgr.save()
            if name == session.get("user") and pw:
                start_session(name)  # giữ đăng nhập sau khi tự đổi mật khẩu
        return jsonify(ok=True)

    @app.delete("/api/users/<name>")
    @login_required(admin=True)
    def delete_user(name):
        with mgr.lock:
            if name not in mgr.cfg.web_users:
                abort(404)
            if _admins(mgr) == [name]:
                return jsonify(error="Không thể xóa quản trị viên cuối cùng"), 400
            del mgr.cfg.web_users[name]
            mgr.save()
        return jsonify(ok=True)

    return app


# =============================================================================
def _admins(mgr: Manager) -> list[str]:
    return [n for n, u in mgr.cfg.web_users.items() if u.get("role") == "admin"]


def _clamp(v, lo, hi) -> int:
    try:
        return max(lo, min(hi, int(v)))
    except (TypeError, ValueError):
        return 0


def _ascii(name: str) -> str:
    import unicodedata
    name = unicodedata.normalize("NFD", name.replace("đ", "d").replace("Đ", "D"))
    name = "".join(c for c in name if not unicodedata.combining(c))
    return "".join(c if c.isascii() and (c.isalnum() or c in "-_") else "_" for c in name).strip("_") or "camera"


def _wait(start, key="result", timeout=15):
    """Chạy lệnh pytapo (bất đồng bộ) và chờ kết quả để trả về cho trình duyệt."""
    done = threading.Event()
    box = {}

    def cb(res, err):
        box["res"], box["err"] = res, err
        done.set()

    start(cb)
    if not done.wait(timeout):
        return jsonify(error="Camera không phản hồi"), 504
    if box["err"]:
        return jsonify(error=f"{box['err']}. Thử nhập 'Mật khẩu TP-Link' cho camera trong Cài đặt."), 502
    res = box["res"]
    if key == "presets":
        res = [{"id": k, "name": v} for k, v in (res or {}).items()]
    return jsonify(ok=True, **{key: res if isinstance(res, (list, dict, bool, str, int)) or res is None else str(res)})


def lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Tapo Viewer - bản web")
    ap.add_argument("--host", default="0.0.0.0", help="Địa chỉ lắng nghe (mặc định 0.0.0.0 = mọi mạng)")
    ap.add_argument("--port", type=int, default=None, help="Cổng (mặc định 8080)")
    args = ap.parse_args(argv)

    mgr = Manager()
    port = args.port or mgr.cfg.web_port
    app = create_app(mgr)
    print("=" * 60)
    print(f" Tapo Viewer Web {__version__}")
    print(f" Mở trên máy này:      http://localhost:{port}")
    print(f" Mở từ máy khác (LAN): http://{lan_ip()}:{port}")
    if not mgr.cfg.web_users:
        print(" Lần đầu: trang web sẽ yêu cầu tạo tài khoản quản trị.")
    print(" Nhấn Ctrl+C để dừng.")
    print("=" * 60)
    try:
        from waitress import serve
        serve(app, host=args.host, port=port, threads=48, channel_timeout=30,
              connection_limit=200, ident="TapoViewer")
    except ImportError:
        app.run(host=args.host, port=port, threaded=True)
    finally:
        for s in mgr.streams:
            s.stop()
