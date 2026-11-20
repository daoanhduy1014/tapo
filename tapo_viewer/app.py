"""Giao diện chính của Tapo Viewer (Tkinter)."""

from __future__ import annotations

import math
import os
import subprocess
import sys
import tkinter as tk
from dataclasses import replace
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import cv2
from PIL import Image, ImageTk

from . import __version__
from .camera import CameraStream
from .config import AppConfig, CameraConfig, load_config, save_config
from .ptz import PTZController

BG = "#111418"
TILE_BG = "#000000"
SEL_COLOR = "#2f8cff"
REC_COLOR = "#ff3b30"
REFRESH_MS = 40  # ~25 khung hình/giây cho giao diện


# =============================================================================
class CameraDialog(tk.Toplevel):
    """Hộp thoại thêm/sửa camera."""

    def __init__(self, master, cam: CameraConfig | None = None):
        super().__init__(master)
        self.title("Sửa camera" if cam else "Thêm camera")
        self.resizable(False, False)
        self.transient(master)
        self.result: CameraConfig | None = None
        cam = cam or CameraConfig(name=f"Camera {len(master.cfg.cameras) + 1}")

        self.vars = {
            "name": tk.StringVar(value=cam.name),
            "ip": tk.StringVar(value=cam.ip),
            "username": tk.StringVar(value=cam.username),
            "password": tk.StringVar(value=cam.password),
            "stream": tk.StringVar(value=cam.stream),
            "port": tk.StringVar(value=str(cam.port)),
            "cloud_password": tk.StringVar(value=cam.cloud_password),
            "custom_url": tk.StringVar(value=cam.custom_url),
        }

        f = ttk.Frame(self, padding=14)
        f.pack(fill="both", expand=True)
        rows = [
            ("Tên camera", "name", {}),
            ("Địa chỉ IP", "ip", {}),
            ("Tài khoản camera", "username", {}),
            ("Mật khẩu camera", "password", {"show": "•"}),
            ("Cổng RTSP", "port", {}),
        ]
        r = 0
        for label, key, kw in rows:
            ttk.Label(f, text=label).grid(row=r, column=0, sticky="w", pady=3)
            ttk.Entry(f, textvariable=self.vars[key], width=34, **kw).grid(row=r, column=1, sticky="ew", pady=3)
            r += 1

        ttk.Label(f, text="Chất lượng").grid(row=r, column=0, sticky="w", pady=3)
        q = ttk.Frame(f)
        q.grid(row=r, column=1, sticky="w")
        ttk.Radiobutton(q, text="HD (stream1)", value="stream1", variable=self.vars["stream"]).pack(side="left")
        ttk.Radiobutton(q, text="SD (stream2)", value="stream2", variable=self.vars["stream"]).pack(side="left", padx=8)
        r += 1

        ttk.Separator(f).grid(row=r, column=0, columnspan=2, sticky="ew", pady=8)
        r += 1
        ttk.Label(f, text="Mật khẩu TP-Link\n(cho xoay camera)").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Entry(f, textvariable=self.vars["cloud_password"], width=34, show="•").grid(row=r, column=1, sticky="ew")
        r += 1
        ttk.Label(f, text="URL tùy chỉnh\n(không bắt buộc)").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Entry(f, textvariable=self.vars["custom_url"], width=34).grid(row=r, column=1, sticky="ew")
        r += 1

        hint = ("Tài khoản camera tạo trong app Tapo: Cài đặt camera → Advanced Settings\n"
                "→ Camera Account. Đây KHÔNG phải tài khoản đăng nhập app Tapo.")
        ttk.Label(f, text=hint, foreground="#666").grid(row=r, column=0, columnspan=2, sticky="w", pady=(8, 4))
        r += 1

        btns = ttk.Frame(f)
        btns.grid(row=r, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(btns, text="Kiểm tra kết nối", command=self._test).pack(side="left", padx=4)
        ttk.Button(btns, text="Hủy", command=self.destroy).pack(side="left", padx=4)
        ttk.Button(btns, text="Lưu", command=self._ok).pack(side="left", padx=4)

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self.grab_set()
        self.wait_visibility()
        self.focus_set()

    def _collect(self) -> CameraConfig | None:
        v = {k: var.get().strip() for k, var in self.vars.items()}
        if not v["custom_url"] and not v["ip"]:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập địa chỉ IP của camera.", parent=self)
            return None
        try:
            port = int(v["port"] or 554)
        except ValueError:
            messagebox.showwarning("Sai cổng", "Cổng RTSP phải là số (mặc định 554).", parent=self)
            return None
        return CameraConfig(
            name=v["name"] or v["ip"], ip=v["ip"], username=v["username"],
            password=self.vars["password"].get(), stream=v["stream"], port=port,
            cloud_password=self.vars["cloud_password"].get(), custom_url=v["custom_url"],
        )

    def _test(self):
        cam = self._collect()
        if not cam:
            return
        self.config(cursor="watch")
        self.update()
        cap = cv2.VideoCapture(cam.rtsp_url(), cv2.CAP_FFMPEG)
        ok = cap.isOpened() and cap.read()[0]
        cap.release()
        self.config(cursor="")
        if ok:
            messagebox.showinfo("Thành công", "Kết nối camera thành công!", parent=self)
        else:
            messagebox.showerror(
                "Thất bại",
                f"Không kết nối được tới:\n{cam.safe_url()}\n\n"
                "Kiểm tra lại:\n• PC và camera cùng mạng LAN/Wi-Fi\n• Địa chỉ IP đúng\n"
                "• Tài khoản/mật khẩu camera (Camera Account)\n• Camera không bật Privacy Mode",
                parent=self)

    def _ok(self):
        cam = self._collect()
        if cam:
            self.result = cam
            self.destroy()


# =============================================================================
class Tile(tk.Frame):
    """Ô hiển thị một camera."""

    def __init__(self, master, app: "TapoViewerApp", index: int):
        super().__init__(master, bg=TILE_BG, highlightthickness=3, highlightbackground=BG)
        self.app = app
        self.index = index
        self.label = tk.Label(self, bg=TILE_BG, fg="#bbb", font=("Segoe UI", 11))
        self.label.pack(fill="both", expand=True)
        self.caption = tk.Label(self, bg="#000", fg="#fff", anchor="w", font=("Segoe UI", 9))
        self.caption.place(x=0, y=0)
        self._photo = None
        self._last_id = -1
        self._last_size = (0, 0)
        for w in (self, self.label, self.caption):
            w.bind("<Button-1>", lambda e: app.select(self.index))
            w.bind("<Double-Button-1>", lambda e: app.toggle_single(self.index))
            w.bind("<Button-3>", self._menu)

    def _menu(self, event):
        self.app.select(self.index)
        m = tk.Menu(self, tearoff=0)
        m.add_command(label="Xem một mình / Quay lại lưới", command=lambda: self.app.toggle_single(self.index))
        m.add_command(label="Chụp ảnh", command=self.app.snapshot)
        m.add_command(label="Bắt đầu / Dừng ghi hình", command=self.app.toggle_record)
        m.add_separator()
        m.add_command(label="Sửa camera...", command=self.app.edit_camera)
        m.add_command(label="Kết nối lại", command=self.app.reconnect)
        m.tk_popup(event.x_root, event.y_root)

    def refresh(self, stream: CameraStream | None):
        if stream is None:
            self.label.configure(image="", text="")
            self.caption.configure(text="")
            self._photo = None
            return
        rec = " ● REC" if stream.recording else ""
        info = f"  {stream.fps:.0f} fps" if stream.connected else f"  - {stream.status}"
        self.caption.configure(text=f" {stream.cam.name}{info}{rec} ",
                               fg=REC_COLOR if rec else "#fff")
        fid, frame = stream.get_frame()
        w, h = self.label.winfo_width(), self.label.winfo_height()
        if frame is None:
            self.label.configure(image="", text=stream.status)
            self._photo = None
            self._last_id = -1
            return
        if fid == self._last_id and (w, h) == self._last_size:
            return
        self._last_id, self._last_size = fid, (w, h)
        if w < 10 or h < 10:
            return
        fh, fw = frame.shape[:2]
        scale = min(w / fw, h / fh)
        nw, nh = max(1, int(fw * scale)), max(1, int(fh * scale))
        interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
        img = cv2.cvtColor(cv2.resize(frame, (nw, nh), interpolation=interp), cv2.COLOR_BGR2RGB)
        self._photo = ImageTk.PhotoImage(Image.fromarray(img))
        self.label.configure(image=self._photo, text="")


# =============================================================================
class TapoViewerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Tapo Viewer {__version__} - Xem camera Tapo C200")
        self.geometry("1280x760")
        self.minsize(800, 500)
        self.configure(bg=BG)

        self.cfg: AppConfig = load_config()
        self.streams: list[CameraStream] = []
        self.ptz: dict[int, PTZController] = {}
        self.tiles: list[Tile] = []
        self.selected = 0
        self.single: int | None = None
        self.page = 0
        self._fullscreen = False

        self._build_ui()
        self._start_streams()
        self._relayout()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(REFRESH_MS, self._tick)
        if not self.cfg.cameras:
            self.after(300, self._first_run)

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        bar = ttk.Frame(self, padding=(6, 4))
        bar.pack(side="top", fill="x")
        ttk.Button(bar, text="➕ Thêm camera", command=self.add_camera).pack(side="left", padx=2)
        ttk.Button(bar, text="📷 Chụp ảnh", command=self.snapshot).pack(side="left", padx=2)
        self.rec_btn = ttk.Button(bar, text="⏺ Ghi hình", command=self.toggle_record)
        self.rec_btn.pack(side="left", padx=2)
        ttk.Button(bar, text="⛶ Toàn màn hình (F11)", command=self.toggle_fullscreen).pack(side="left", padx=2)

        ttk.Label(bar, text="  Bố cục:").pack(side="left")
        self.layout_var = tk.StringVar(value=self.cfg.layout)
        cb = ttk.Combobox(bar, textvariable=self.layout_var, width=8, state="readonly",
                          values=["auto", "1", "4", "9", "16"])
        cb.pack(side="left", padx=2)
        cb.bind("<<ComboboxSelected>>", lambda e: self._set_layout())
        ttk.Button(bar, text="◀", width=3, command=lambda: self._page(-1)).pack(side="left", padx=(8, 0))
        self.page_lbl = ttk.Label(bar, text="")
        self.page_lbl.pack(side="left", padx=4)
        ttk.Button(bar, text="▶", width=3, command=lambda: self._page(1)).pack(side="left")

        ttk.Button(bar, text="📁 Ảnh", command=lambda: _open_folder(self.cfg.snapshot_path())).pack(side="right", padx=2)
        ttk.Button(bar, text="📁 Video", command=lambda: _open_folder(self.cfg.record_path())).pack(side="right", padx=2)
        ttk.Button(bar, text="⚙ Thư mục lưu", command=self._choose_dirs).pack(side="right", padx=2)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        # Cột trái: danh sách camera
        self.side = ttk.Frame(body, padding=6, width=230)
        self.side.pack(side="left", fill="y")
        ttk.Label(self.side, text="Danh sách camera", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.listbox = tk.Listbox(self.side, width=28, height=12, activestyle="none", exportselection=False)
        self.listbox.pack(fill="x", pady=4)
        self.listbox.bind("<<ListboxSelect>>", self._on_list_select)
        self.listbox.bind("<Double-Button-1>", lambda e: self.edit_camera())
        lb = ttk.Frame(self.side)
        lb.pack(fill="x")
        ttk.Button(lb, text="Sửa", command=self.edit_camera).pack(side="left", expand=True, fill="x")
        ttk.Button(lb, text="Xóa", command=self.delete_camera).pack(side="left", expand=True, fill="x")
        ttk.Button(lb, text="↑", width=3, command=lambda: self._move_cam(-1)).pack(side="left")
        ttk.Button(lb, text="↓", width=3, command=lambda: self._move_cam(1)).pack(side="left")

        # Bảng điều khiển PTZ
        ptz = ttk.LabelFrame(self.side, text="Điều khiển xoay (PTZ)", padding=6)
        ptz.pack(fill="x", pady=(12, 0))
        pad = ttk.Frame(ptz)
        pad.pack()
        self.step_var = tk.IntVar(value=10)
        arrows = [("▲", 0, 1, 0, 1), ("◀", 1, 0, -1, 0), ("▶", 1, 2, 1, 0), ("▼", 2, 1, 0, -1)]
        for txt, r, c, dx, dy in arrows:
            ttk.Button(pad, text=txt, width=4,
                       command=lambda dx=dx, dy=dy: self._ptz_move(dx, dy)).grid(row=r, column=c, padx=2, pady=2)
        ttk.Button(pad, text="⟲", width=4, command=self._ptz_calibrate).grid(row=1, column=1)
        sf = ttk.Frame(ptz)
        sf.pack(fill="x", pady=(4, 0))
        ttk.Label(sf, text="Bước:").pack(side="left")
        ttk.Scale(sf, from_=5, to=60, variable=self.step_var, orient="horizontal").pack(side="left", fill="x", expand=True)

        self.privacy_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ptz, text="Chế độ riêng tư (Privacy)", variable=self.privacy_var,
                        command=self._ptz_privacy).pack(anchor="w", pady=(6, 0))
        self.led_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(ptz, text="Đèn LED trạng thái", variable=self.led_var,
                        command=self._ptz_led).pack(anchor="w")
        nf = ttk.Frame(ptz)
        nf.pack(fill="x", pady=(4, 0))
        ttk.Label(nf, text="Hồng ngoại:").pack(side="left")
        self.night_var = tk.StringVar(value="auto")
        ncb = ttk.Combobox(nf, textvariable=self.night_var, width=8, state="readonly", values=["auto", "on", "off"])
        ncb.pack(side="left", padx=4)
        ncb.bind("<<ComboboxSelected>>", lambda e: self._ptz_night())

        pf = ttk.Frame(ptz)
        pf.pack(fill="x", pady=(6, 0))
        ttk.Button(pf, text="Vị trí đã lưu...", command=self._ptz_presets).pack(side="left", expand=True, fill="x")
        ttk.Button(pf, text="Lưu vị trí", command=self._ptz_save_preset).pack(side="left", expand=True, fill="x")

        ttk.Label(self.side, text="Phím tắt: mũi tên = xoay, S = chụp,\nR = ghi hình, F11 = toàn màn hình,\n"
                                  "Nhấp đúp ô camera = phóng to",
                  foreground="#777").pack(anchor="w", pady=(12, 0))

        # Lưới camera
        self.grid_frame = tk.Frame(body, bg=BG)
        self.grid_frame.pack(side="left", fill="both", expand=True)

        self.status = ttk.Label(self, text="", anchor="w", padding=(6, 2))
        self.status.pack(side="bottom", fill="x")

        self.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.bind("<Escape>", lambda e: self._escape())
        for key, dx, dy in (("<Up>", 0, 1), ("<Down>", 0, -1), ("<Left>", -1, 0), ("<Right>", 1, 0)):
            self.bind(key, lambda e, dx=dx, dy=dy: self._key_ptz(e, dx, dy))
        self.bind("<KeyPress-s>", lambda e: self._key(e, self.snapshot))
        self.bind("<KeyPress-r>", lambda e: self._key(e, self.toggle_record))

    def _key(self, event, fn):
        if isinstance(event.widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
            return
        fn()

    def _key_ptz(self, event, dx, dy):
        if isinstance(event.widget, (tk.Entry, ttk.Entry, ttk.Combobox, tk.Listbox)):
            return
        self._ptz_move(dx, dy)

    def _first_run(self):
        messagebox.showinfo(
            "Chào mừng",
            "Chưa có camera nào.\n\nChuẩn bị trong app Tapo trên điện thoại:\n"
            "1. Mở camera → biểu tượng Cài đặt (bánh răng)\n"
            "2. Kéo xuống Advanced Settings → Camera Account\n"
            "3. Tạo tên đăng nhập + mật khẩu cho camera\n"
            "4. Xem IP camera tại Device Info\n\nSau đó bấm OK để thêm camera.")
        self.add_camera()

    # ------------------------------------------------------------ streams
    def _start_streams(self):
        for s in self.streams:
            s.stop()
        self.streams = [CameraStream(c) for c in self.cfg.cameras]
        self.ptz = {}
        for s in self.streams:
            s.start()
        self._refresh_list()

    def _refresh_list(self):
        self.listbox.delete(0, "end")
        for c in self.cfg.cameras:
            self.listbox.insert("end", f"  {c.name}  ({c.ip or 'URL'})")
        if self.cfg.cameras:
            self.selected = min(self.selected, len(self.cfg.cameras) - 1)
            self.listbox.selection_set(self.selected)

    def _save(self):
        try:
            save_config(self.cfg)
        except OSError as e:
            messagebox.showerror("Lỗi", f"Không lưu được cấu hình:\n{e}")

    # ------------------------------------------------------------- layout
    def _per_page(self) -> int:
        if self.single is not None:
            return 1
        n = len(self.streams)
        lay = self.layout_var.get()
        if lay == "auto":
            if n <= 1:
                return 1
            return min(16, math.ceil(math.sqrt(n)) ** 2)
        return int(lay)

    def _relayout(self):
        for t in self.tiles:
            t.destroy()
        self.tiles = []
        per = self._per_page()
        cols = int(math.ceil(math.sqrt(per)))
        rows = int(math.ceil(per / cols))
        for i in range(cols):
            self.grid_frame.columnconfigure(i, weight=1, uniform="c")
        for i in range(rows):
            self.grid_frame.rowconfigure(i, weight=1, uniform="r")
        for i in range(cols, 5):
            self.grid_frame.columnconfigure(i, weight=0, uniform="")
        for i in range(rows, 5):
            self.grid_frame.rowconfigure(i, weight=0, uniform="")
        pages = max(1, math.ceil(len(self.streams) / per))
        self.page = max(0, min(self.page, pages - 1))
        for k in range(per):
            idx = self.single if self.single is not None else self.page * per + k
            t = Tile(self.grid_frame, self, idx)
            t.grid(row=k // cols, column=k % cols, sticky="nsew", padx=1, pady=1)
            self.tiles.append(t)
        self.page_lbl.configure(text="Xem 1 camera" if self.single is not None
                                else f"Trang {self.page + 1}/{pages}")
        self.listbox.selection_clear(0, "end")
        if self.streams:
            self.listbox.selection_set(self.selected)
        self._highlight()

    def _set_layout(self):
        self.cfg.layout = self.layout_var.get()
        self.single = None
        self._save()
        self._relayout()

    def _page(self, d):
        self.single = None
        self.page += d
        self._relayout()

    def toggle_single(self, idx):
        if idx >= len(self.streams):
            return
        self.selected = idx
        self.single = None if self.single is not None else idx
        if self.single is None:
            per = self._per_page()
            self.page = idx // per
        self._relayout()

    def select(self, idx):
        if idx >= len(self.streams):
            return
        self.selected = idx
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(idx)
        self._highlight()

    def _highlight(self):
        for t in self.tiles:
            t.configure(highlightbackground=SEL_COLOR if t.index == self.selected else BG)

    def _on_list_select(self, _e):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.selected = idx
        if self.single is not None:
            self.single = idx
            self._relayout()
            return
        per = self._per_page()
        if idx // per != self.page:
            self.page = idx // per
            self._relayout()
        self._highlight()

    def toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        self.attributes("-fullscreen", self._fullscreen)
        if self._fullscreen:
            self.side.pack_forget()
        else:
            self.side.pack(side="left", fill="y", before=self.grid_frame)

    def _escape(self):
        if self._fullscreen:
            self.toggle_fullscreen()
        elif self.single is not None:
            self.toggle_single(self.single)

    # -------------------------------------------------------------- loop
    def _tick(self):
        for t in self.tiles:
            t.refresh(self.streams[t.index] if t.index < len(self.streams) else None)
        s = self._current()
        if s:
            rec = f"  |  Đang ghi: {s.record_file.name}" if s.record_file else ""
            self.status.configure(text=f"{s.cam.name}: {s.status}  |  {s.cam.safe_url()}{rec}")
            self.rec_btn.configure(text="⏹ Dừng ghi" if s.recording else "⏺ Ghi hình")
        else:
            self.status.configure(text="Chưa có camera. Bấm 'Thêm camera' để bắt đầu.")
        self.after(REFRESH_MS, self._tick)

    def _current(self) -> CameraStream | None:
        if 0 <= self.selected < len(self.streams):
            return self.streams[self.selected]
        return None

    # ------------------------------------------------------- camera CRUD
    def add_camera(self):
        dlg = CameraDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self.cfg.cameras.append(dlg.result)
            self._save()
            s = CameraStream(dlg.result)
            s.start()
            self.streams.append(s)
            self.selected = len(self.streams) - 1
            self._refresh_list()
            self.single = None
            self.page = self.selected // max(1, self._per_page())
            self._relayout()

    def edit_camera(self):
        s = self._current()
        if not s:
            return
        dlg = CameraDialog(self, replace(s.cam))
        self.wait_window(dlg)
        if dlg.result:
            i = self.selected
            if s.recording:
                s.stop_recording()
            s.stop()
            self.cfg.cameras[i] = dlg.result
            self.streams[i] = CameraStream(dlg.result)
            self.streams[i].start()
            self.ptz.pop(i, None)
            self._save()
            self._refresh_list()

    def delete_camera(self):
        s = self._current()
        if not s or not messagebox.askyesno("Xóa camera", f"Xóa camera '{s.cam.name}'?"):
            return
        i = self.selected
        s.stop()
        del self.streams[i]
        del self.cfg.cameras[i]
        self.ptz = {}
        self.single = None
        self._save()
        self._refresh_list()
        self._relayout()

    def _move_cam(self, d):
        i, j = self.selected, self.selected + d
        if not (0 <= i < len(self.streams) and 0 <= j < len(self.streams)):
            return
        self.streams[i], self.streams[j] = self.streams[j], self.streams[i]
        self.cfg.cameras[i], self.cfg.cameras[j] = self.cfg.cameras[j], self.cfg.cameras[i]
        self.ptz = {}
        self.selected = j
        self._save()
        self._refresh_list()
        self._relayout()

    def reconnect(self):
        s = self._current()
        if s:
            s.stop()
            s.start()

    # ---------------------------------------------------- snapshot / rec
    def snapshot(self):
        s = self._current()
        if not s:
            return
        path = s.snapshot(self.cfg.snapshot_path())
        self._flash(f"Đã chụp ảnh: {path}" if path else "Chưa có hình để chụp")

    def toggle_record(self):
        s = self._current()
        if not s:
            return
        if s.recording:
            path = s.stop_recording()
            self._flash(f"Đã lưu video: {path}")
        else:
            if not s.connected:
                self._flash("Camera chưa kết nối, không thể ghi hình")
                return
            path = s.start_recording(self.cfg.record_path())
            self._flash(f"Bắt đầu ghi: {path}")

    def _choose_dirs(self):
        d = filedialog.askdirectory(title="Chọn thư mục lưu ảnh và video",
                                    initialdir=str(self.cfg.record_path().parent))
        if d:
            self.cfg.snapshot_dir = str(Path(d) / "snapshots")
            self.cfg.record_dir = str(Path(d) / "recordings")
            self._save()
            self._flash(f"Ảnh/video sẽ được lưu vào: {d}")

    def _flash(self, msg):
        self.title(f"Tapo Viewer - {msg}")
        self.after(4000, lambda: self.title(f"Tapo Viewer {__version__} - Xem camera Tapo C200"))

    # ------------------------------------------------------------- PTZ
    def _ptz(self) -> PTZController | None:
        s = self._current()
        if not s:
            return None
        if not PTZController.available():
            messagebox.showwarning("Thiếu thư viện", "Cần cài pytapo để điều khiển camera:\npip install pytapo")
            return None
        if s.cam.custom_url and not s.cam.ip:
            self._flash("Camera dùng URL tùy chỉnh, không hỗ trợ điều khiển")
            return None
        if self.selected not in self.ptz:
            self.ptz[self.selected] = PTZController(s.cam)
        return self.ptz[self.selected]

    def _ptz_done(self, label):
        def cb(_res, err):
            if err:
                self.after(0, lambda: self._flash(
                    f"{label} lỗi: {err}. Thử nhập 'Mật khẩu TP-Link' trong Sửa camera."))
        return cb

    def _ptz_move(self, dx, dy):
        p = self._ptz()
        if p:
            st = int(self.step_var.get())
            p.move(dx * st, dy * st, self._ptz_done("Xoay camera"))

    def _ptz_calibrate(self):
        p = self._ptz()
        if p and messagebox.askyesno("Hiệu chỉnh", "Camera sẽ xoay một vòng để hiệu chỉnh vị trí. Tiếp tục?"):
            p.calibrate(self._ptz_done("Hiệu chỉnh"))

    def _ptz_privacy(self):
        p = self._ptz()
        if p:
            p.set_privacy(self.privacy_var.get(), self._ptz_done("Chế độ riêng tư"))

    def _ptz_led(self):
        p = self._ptz()
        if p:
            p.set_led(self.led_var.get(), self._ptz_done("Đèn LED"))

    def _ptz_night(self):
        p = self._ptz()
        if p:
            p.set_day_night(self.night_var.get(), self._ptz_done("Hồng ngoại"))

    def _ptz_save_preset(self):
        p = self._ptz()
        if not p:
            return
        name = _ask_string(self, "Lưu vị trí", "Tên vị trí:")
        if name:
            p.save_preset(name, self._ptz_done("Lưu vị trí"))

    def _ptz_presets(self):
        p = self._ptz()
        if not p:
            return

        def done(res, err):
            self.after(0, lambda: self._show_presets(p, res, err))
        p.get_presets(done)

    def _show_presets(self, p: PTZController, presets, err):
        if err:
            self._flash(f"Không lấy được danh sách vị trí: {err}")
            return
        if not presets:
            messagebox.showinfo("Vị trí đã lưu", "Camera chưa có vị trí nào được lưu.")
            return
        win = tk.Toplevel(self)
        win.title("Vị trí đã lưu")
        win.transient(self)
        lb = tk.Listbox(win, width=30, height=10)
        lb.pack(padx=8, pady=8)
        items = list(presets.items())
        for pid, name in items:
            lb.insert("end", f"{name}  (#{pid})")

        def go(_e=None):
            sel = lb.curselection()
            if sel:
                p.goto_preset(items[sel[0]][0], self._ptz_done("Đi tới vị trí"))
        lb.bind("<Double-Button-1>", go)
        ttk.Button(win, text="Đi tới", command=go).pack(pady=(0, 8))

    # ------------------------------------------------------------- close
    def _on_close(self):
        for s in self.streams:
            s.stop()
        self.destroy()


def _ask_string(parent, title, prompt) -> str | None:
    from tkinter import simpledialog
    return simpledialog.askstring(title, prompt, parent=parent)


def _open_folder(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except OSError as e:
        messagebox.showerror("Lỗi", f"Không mở được thư mục:\n{e}")


def main():
    app = TapoViewerApp()
    app.mainloop()
