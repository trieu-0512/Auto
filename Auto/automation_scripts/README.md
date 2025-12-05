# Automation Scripts - Hướng dẫn sử dụng

Thư mục chứa các automation scripts cho ứng dụng **Orbita Multi-Profile Browser**.

---

## 🚀 Cách ứng dụng hoạt động

### 1. Mở Browser với Profile

Ứng dụng sử dụng **Orbita Browser** (Chrome-based) với 2 chế độ:

#### Chế độ Manual (Subprocess)
```
Người dùng → Click "Open Browser" → Subprocess mở Orbita → Browser hiển thị
```
- Mở browser với profile data đã lưu
- Không cần ChromeDriver
- Người dùng tự thao tác trên browser

#### Chế độ Automation (Selenium)
```
Người dùng → Chọn Script → Click "Run" → Selenium WebDriver điều khiển browser → Tự động thực hiện các bước
```
- Sử dụng Selenium WebDriver
- Yêu cầu ChromeDriver phù hợp với phiên bản Orbita
- Tự động thực hiện các thao tác theo script

### 2. Quy trình đăng bài tự động

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Chọn Profile(s) trong danh sách                             │
│  2. Chọn Script (VD: Instagram Post Video)                      │
│  3. Nhập tham số (đường dẫn video, caption, v.v.)               │
│  4. Click "Run Selected"                                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Automation Executor:                                    │   │
│  │  - Mở browser với profile đã chọn                        │   │
│  │  - Load script JSON                                      │   │
│  │  - Thực hiện từng step:                                  │   │
│  │    → open_url: Mở trang web                              │   │
│  │    → click: Click vào element                            │   │
│  │    → enter_text: Nhập nội dung                           │   │
│  │    → upload_file: Upload file                            │   │
│  │    → wait: Đợi load                                      │   │
│  │  - Báo cáo tiến độ                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  5. Hoàn thành → Cập nhật trạng thái profile                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Cấu trúc thư mục

```
automation_scripts/
├── README.md           # File này
├── facebook/           # Scripts cho Facebook
│   └── auto_post.json
├── instagram/          # Scripts cho Instagram
│   └── post_video.json
├── telegram/           # Scripts cho Telegram
├── tiktok/             # Scripts cho TikTok
├── general/            # Scripts chung (login, logout, etc.)
│   └── login_template.json
└── custom/             # Scripts tùy chỉnh của người dùng
```

---

## 📝 Định dạng Script JSON

```json
{
  "script_id": "unique_id",
  "name": "Tên script hiển thị",
  "description": "Mô tả chi tiết script",
  "platform": "facebook|instagram|telegram|tiktok|general",
  "version": "1.0",
  "steps": [
    {
      "step_id": 1,
      "action": "open_url",
      "input": "https://www.instagram.com/",
      "description": "Mở Instagram"
    },
    {
      "step_id": 2,
      "action": "click",
      "locator": "xpath://button[@aria-label='New post']",
      "description": "Click nút tạo bài mới"
    }
  ]
}
```

---

## ⚡ Actions hỗ trợ

| Action | Mô tả | Ví dụ |
|--------|-------|-------|
| `open_url` | Mở URL | `"input": "https://facebook.com"` |
| `click` | Click vào element | `"locator": "xpath://button[@id='submit']"` |
| `enter_text` | Nhập text vào input | `"locator": "css:input[name='email']", "input": "text"` |
| `wait` | Đợi (giây) | `"input": "3"` |
| `scroll` | Cuộn trang (pixels) | `"input": "500"` |
| `upload_file` | Upload file | `"locator": "xpath://input[@type='file']", "input": "{video_path}"` |

---

## 🔍 Cách viết Locator

### XPath
```json
"locator": "xpath://button[contains(text(),'Đăng')]"
"locator": "xpath://input[@type='email']"
"locator": "xpath://div[@aria-label='Like']"
```

### CSS Selector
```json
"locator": "css:button.submit-btn"
"locator": "css:input[name='password']"
"locator": "css:#login-form input[type='email']"
```

---

## 🔄 Biến động (Variables)

Sử dụng `{variable_name}` để truyền tham số khi chạy:

```json
{
  "step_id": 5,
  "action": "upload_file",
  "locator": "xpath://input[@type='file']",
  "input": "{video_path}",
  "description": "Upload video từ tham số"
}
```

Các biến thường dùng:
- `{video_path}` - Đường dẫn video
- `{caption}` - Nội dung caption
- `{username}` - Tên đăng nhập
- `{password}` - Mật khẩu
- `{post_content}` - Nội dung bài đăng

---

## 📌 Ví dụ Script hoàn chỉnh

### Instagram Post Video
```json
{
  "script_id": "ig_post_video",
  "name": "Instagram Post Video",
  "description": "Tự động đăng video lên Instagram",
  "platform": "instagram",
  "steps": [
    {"step_id": 1, "action": "open_url", "input": "https://www.instagram.com/"},
    {"step_id": 2, "action": "wait", "input": "3"},
    {"step_id": 3, "action": "click", "locator": "xpath://span[contains(text(),'Create')]"},
    {"step_id": 4, "action": "upload_file", "locator": "xpath://input[@type='file']", "input": "{video_path}"},
    {"step_id": 5, "action": "wait", "input": "5"},
    {"step_id": 6, "action": "click", "locator": "xpath://button[contains(text(),'Next')]"},
    {"step_id": 7, "action": "enter_text", "locator": "xpath://textarea", "input": "{caption}"},
    {"step_id": 8, "action": "click", "locator": "xpath://button[contains(text(),'Share')]"}
  ]
}
```

---

## 🛠️ Tạo Script mới

1. Tạo file JSON trong thư mục platform tương ứng
2. Định nghĩa `script_id` duy nhất
3. Viết các steps theo thứ tự thực hiện
4. Test với 1 profile trước khi chạy batch

---

## ⚠️ Lưu ý quan trọng

1. **ChromeDriver**: Phải phù hợp với phiên bản Orbita Browser
2. **Locator**: Kiểm tra XPath/CSS trên browser trước khi viết script
3. **Wait time**: Thêm đủ thời gian chờ để trang load
4. **Rate limit**: Không chạy quá nhanh để tránh bị block
5. **Profile data**: Đảm bảo profile đã đăng nhập sẵn vào platform
