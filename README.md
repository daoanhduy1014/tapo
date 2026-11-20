# Tapo Viewer – Xem camera Tapo C200 trên PC/Laptop

Phần mềm xem trực tiếp camera **TP-Link Tapo C200** (và các camera Tapo khác hỗ trợ RTSP như C100, C210, C310, C320WS…) trên máy tính Windows / macOS / Linux, qua mạng LAN.

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

## Phím tắt

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
main.py                  # Điểm khởi chạy
tapo_viewer/app.py       # Giao diện (Tkinter)
tapo_viewer/camera.py    # Đọc luồng RTSP (OpenCV/FFmpeg), chụp ảnh, ghi hình
tapo_viewer/ptz.py       # Xoay camera, privacy, LED, hồng ngoại (pytapo)
tapo_viewer/config.py    # Lưu/đọc cấu hình camera
```
