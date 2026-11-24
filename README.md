# Tapo Viewer – Xem camera Tapo C200 trên PC/Laptop

Phần mềm (bản **desktop** và bản **web**) xem trực tiếp camera **TP-Link Tapo C200** (và các camera Tapo khác hỗ trợ RTSP như C100, C210, C310, C320WS…) trên máy tính Windows / macOS / Linux, qua mạng LAN.

## Tính năng

- Xem **nhiều camera cùng lúc** (lưới 1 / 4 / 9 / 16 ô, tự động hoặc chọn tay, có chuyển trang)
- Nhấp đúp vào một camera để **phóng to**, nhấp đúp lần nữa để quay lại lưới
- Chọn chất lượng **HD 1080p (stream1)** hoặc **SD 360p (stream2)** – SD nhẹ hơn khi xem nhiều camera
- **Chụp ảnh** (JPG) và **ghi hình** (MP4) ra máy tính
- **Xoay / nghiêng camera (PTZ)** bằng nút hoặc phím mũi tên, lưu và gọi lại vị trí
- Bật/tắt **Privacy Mode**, **đèn LED**, **hồng ngoại** (tự động / bật / tắt)
- **Tự kết nối lại** khi mất mạng, toàn màn hình (F11)

## Bước 1 – Chuẩn bị trên app Tapo (điện thoại)

1. Mở app Tapo → chọn camera → bấm biểu tượng **Cài đặt** (bánh răng).
2. Kéo xuống dưới cùng → **Advanced Settings** (Cài đặt nâng cao) → **Camera Account** (Tài khoản camera).
3. Tạo **tên đăng nhập** và **mật khẩu** riêng cho camera (6–32 ký tự).
   > Đây **không phải** tài khoản đăng nhập app Tapo.
4. Xem **địa chỉ IP** của camera: bấm **Device Info** ở đầu trang cài đặt (ví dụ `192.168.1.50`).
   Nên đặt IP tĩnh cho camera trong router để IP không bị đổi.
5. Đảm bảo **Privacy Mode đang tắt** (nếu bật, camera sẽ không phát hình).

## Bước 2 – Cài và chạy phần mềm

### Windows
1. Cài **Python 3.10+** tại <https://www.python.org/downloads/> – nhớ tick **“Add Python to PATH”**.
2. Tải thư mục này về, nhấp đúp **`run_windows.bat`**.
   Lần đầu sẽ tự cài thư viện (mất 1–2 phút), các lần sau mở ngay.

Muốn tạo file **`TapoViewer.exe`** để chạy không cần Python (chép sang máy khác được): nhấp đúp **`build_exe_windows.bat`**, file nằm trong thư mục `dist\`.

### macOS / Linux
```bash
./run_mac_linux.sh
```
(Linux cần thêm gói Tkinter, ví dụ Ubuntu: `sudo apt install python3-tk python3-venv`)

### Chạy thủ công
```bash
pip install -r requirements.txt
python main.py
```

## Bước 3 – Thêm camera

Bấm **➕ Thêm camera** và điền:

| Ô | Ví dụ | Ghi chú |
|---|---|---|
| Tên camera | Tầng G | Tùy ý |
| Địa chỉ IP | 192.168.1.50 | Xem ở Device Info |
| Tài khoản / Mật khẩu camera | admin123 / ****** | Tạo ở Camera Account (Bước 1) |
| Chất lượng | HD (stream1) | SD (stream2) nếu mạng yếu |
| Mật khẩu TP-Link | (tùy chọn) | Mật khẩu tài khoản app Tapo – chỉ cần nếu nút **xoay camera** báo lỗi |

Bấm **Kiểm tra kết nối** để thử, rồi **Lưu**.

## 🌐 Bản Web – xem camera bằng trình duyệt, có đăng nhập

Mở trình duyệt (máy tính hoặc điện thoại), đăng nhập và xem camera **ở bất cứ đâu**, không cần cài gì trên máy xem.

> **Quan trọng:** camera chỉ phát hình trong mạng nội bộ, nên bản web phải chạy trên **một máy tính đặt cùng mạng với camera** (cùng router "Wintop G"), và **máy đó phải luôn bật**. Máy xem từ xa thì không cần cùng mạng.

```
[Camera Tapo] ──LAN── [PC tại chỗ: chạy web.py] ──đường hầm HTTPS── Internet ── [Trình duyệt của bạn ở bất cứ đâu]
```

### 1. Chạy máy chủ web (trên PC tại chỗ)
- **Windows:** nhấp đúp **`run_web_windows.bat`** (lần đầu tự cài thư viện). Trình duyệt tự mở `http://localhost:8080`.
- **macOS/Linux:** `./run_web_mac_linux.sh`
- Lần đầu mở trang, phần mềm yêu cầu **tạo tài khoản quản trị** (mật khẩu ≥ 8 ký tự).
- Vào **⚙ Cài đặt** để thêm camera (IP + Camera Account như hướng dẫn ở trên) và tạo thêm tài khoản cho nhân viên (quyền *Chỉ xem*).

Trong cùng mạng, máy khác/điện thoại mở `http://<IP-của-PC>:8080` (cửa sổ đen sẽ in sẵn địa chỉ này).

### 2. Xem từ xa qua Internet (chọn MỘT cách)

**Cách A – Tailscale Funnel (miễn phí, link cố định, khuyên dùng)**
1. Cài Tailscale trên PC tại chỗ: <https://tailscale.com/download>, đăng nhập.
2. Mở **Command Prompt** và chạy: `tailscale funnel --bg 8080`
   (Lần đầu nó sẽ hiện link để bật HTTPS/Funnel cho tài khoản – mở link và bấm đồng ý.)
3. Bạn nhận được link dạng `https://ten-may.tail1234.ts.net` – mở link này ở bất cứ đâu để đăng nhập.

**Cách B – Cloudflare Tunnel (miễn phí, không cần tài khoản)**
1. Tải `cloudflared` cho Windows: <https://github.com/cloudflare/cloudflared/releases/latest> (file `cloudflared-windows-amd64.exe`).
2. Chạy: `cloudflared-windows-amd64.exe tunnel --url http://localhost:8080`
3. Nó in ra link `https://xxxx.trycloudflare.com`. *Lưu ý: link đổi mỗi lần chạy lại;* muốn link cố định cần có tên miền trên Cloudflare.

Cả hai cách đều **không cần mở cổng router** và đều có HTTPS (mã hóa).

### 3. Để chạy ổn định 24/7
- Tắt chế độ ngủ của PC: *Settings → System → Power → Sleep: Never*.
- Tự chạy khi bật máy: nhấn `Win + R`, gõ `shell:startup`, rồi tạo shortcut của `run_web_windows.bat` vào thư mục đó.

### Lưu ý bản web
- Ở màn hình xem một camera có nút **HD / Tiết kiệm**: dùng *Tiết kiệm* khi xem bằng 4G. Tab bị ẩn sẽ tự dừng tải hình.
- **Chụp ảnh** tải ảnh về máy đang xem; **Ghi hình** lưu video trên PC tại chỗ (thư mục `recordings/`).
- Bảo mật: mật khẩu được mã hóa (hash), sai 5 lần sẽ bị khóa 10 phút, mật khẩu camera không bao giờ gửi ra trình duyệt. Hãy đặt mật khẩu mạnh vì trang có thể truy cập từ Internet.
- Camera Tapo chỉ cho số kết nối RTSP đồng thời có hạn – không nên chạy cùng lúc bản desktop và bản web cho một camera. Bản web dùng **một** kết nối cho mỗi camera dù có nhiều người xem.

## Phím tắt (bản desktop)

| Phím | Chức năng |
|---|---|
| ← ↑ → ↓ | Xoay camera đang chọn |
| S | Chụp ảnh |
| R | Bắt đầu / dừng ghi hình |
| F11 | Toàn màn hình |
| Esc | Thoát toàn màn hình / quay lại lưới |
| Nhấp đúp | Phóng to / thu nhỏ camera |
| Chuột phải | Menu nhanh của camera |

## Xử lý sự cố

- **“Không kết nối được”**: kiểm tra PC và camera cùng mạng Wi-Fi/LAN; ping thử IP camera; kiểm tra lại tài khoản Camera Account; tắt Privacy Mode.
- **Hình trễ / giật**: chuyển sang SD (stream2), hoặc đặt PC dùng dây LAN.
- **Nút xoay báo lỗi**: nhập *Mật khẩu TP-Link* (mật khẩu đăng nhập app Tapo) trong **Sửa camera**.
- **Xem từ xa (ngoài mạng nhà)**: RTSP chỉ dùng trong mạng LAN. Muốn xem từ xa an toàn hãy dùng VPN (ví dụ Tailscale, WireGuard) về mạng nhà – **không nên** mở cổng 554 ra Internet.

## Lưu ý

- Cấu hình camera (gồm mật khẩu) lưu trong `config.json` cạnh chương trình, **dạng chữ thường** – không chia sẻ file này.
- Video ghi ra không có âm thanh. Ảnh lưu ở `snapshots/`, video ở `recordings/` (đổi bằng nút **⚙ Thư mục lưu**).

## Cấu trúc mã nguồn

```
main.py                  # Chạy bản desktop
web.py                   # Chạy bản web
tapo_viewer/web.py       # Máy chủ web: đăng nhập, phát hình MJPEG, API điều khiển
tapo_viewer/web_ui.py    # Giao diện trang web (HTML/CSS/JS)
tapo_viewer/app.py       # Giao diện (Tkinter)
tapo_viewer/camera.py    # Đọc luồng RTSP (OpenCV/FFmpeg), chụp ảnh, ghi hình
tapo_viewer/ptz.py       # Xoay camera, privacy, LED, hồng ngoại (pytapo)
tapo_viewer/config.py    # Lưu/đọc cấu hình camera
```
