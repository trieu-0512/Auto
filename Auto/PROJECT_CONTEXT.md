# Orbita Multi-Profile Automation - Project Context

## 🎯 Tổng quan ứng dụng

Ứng dụng quản lý nhiều profile browser với fingerprint riêng biệt, hỗ trợ automation cho các nền tảng mạng xã hội (Facebook, Instagram, TikTok, Telegram).

---

## 🚀 Cách ứng dụng mở Browser

### Quy trình mở Browser

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        QUY TRÌNH MỞ BROWSER                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Người dùng chọn Profile từ danh sách                                │
│                    ↓                                                    │
│  2. BrowserManager nhận profile_id                                      │
│                    ↓                                                    │
│  3. ProfileManager load thông tin profile từ database                   │
│     - Đường dẫn profile: profile/{profile_id}/                          │
│     - Fingerprint: profile/{profile_id}/Default/Preferences             │
│     - Proxy settings                                                    │
│                    ↓                                                    │
│  4. Build Chrome Options:                                               │
│     --user-data-dir=profile/{profile_id}  (load profile data)           │
│     --window-position=x,y                 (vị trí cửa sổ)               │
│     --load-extension=extensions/...       (load extensions)             │
│     --force-dark-mode                     (giao diện tối)               │
│                    ↓                                                    │
│  5. Khởi chạy Orbita Browser (trinhduyet/orbita-browser/chrome.exe)     │
│                    ↓                                                    │
│  6. Browser hiển thị với:                                               │
│     - Fingerprint đã cấu hình (User Agent, WebGL, Canvas, etc.)         │
│     - Cookies/Sessions đã lưu                                           │
│     - Proxy đã thiết lập (nếu có)                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2 Chế độ mở Browser

#### Chế độ 1: Manual (Subprocess) - Không cần ChromeDriver
```python
# BrowserManager._launch_with_subprocess()
args = [
    "trinhduyet/orbita-browser/chrome.exe",
    f"--user-data-dir={profile_path}",
    "--window-position=0,0",
    "--force-dark-mode",
    "--load-extension=extensions/...",
]
process = subprocess.Popen(args)
```
- Dùng khi: Người dùng muốn tự thao tác trên browser
- Ưu điểm: Không cần ChromeDriver, đơn giản

#### Chế độ 2: Automation (Selenium) - Cần ChromeDriver
```python
# BrowserManager._launch_with_selenium()
options = ChromeOptions()
options.binary_location = "trinhduyet/orbita-browser/chrome.exe"
options.add_argument(f"--user-data-dir={profile_path}")
driver = webdriver.Chrome(service=Service("chromedriver.exe"), options=options)
```
- Dùng khi: Chạy automation scripts
- Yêu cầu: ChromeDriver phù hợp với phiên bản Orbita

---

## 📤 Cách ứng dụng đăng bài tự động

### Quy trình Automation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     QUY TRÌNH ĐĂNG BÀI TỰ ĐỘNG                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  BƯỚC 1: Chuẩn bị                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ - Chọn profile(s) đã đăng nhập sẵn vào platform                 │   │
│  │ - Chọn script automation (VD: Instagram Post Video)             │   │
│  │ - Nhập tham số: đường dẫn video, caption, số lần, delay...      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              ↓                                          │
│  BƯỚC 2: Khởi chạy                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ SessionManager:                                                  │   │
│  │ - Kiểm tra số session đang chạy (max concurrent)                │   │
│  │ - Tạo queue cho các profile được chọn                           │   │
│  │ - Khởi chạy browser với Selenium cho từng profile               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              ↓                                          │
│  BƯỚC 3: Thực thi Script                                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ AutomationExecutor:                                              │   │
│  │ - Load script JSON từ automation_scripts/                        │   │
│  │ - Thực hiện từng step:                                          │   │
│  │                                                                  │   │
│  │   Step 1: open_url → driver.get("https://instagram.com")        │   │
│  │   Step 2: wait → time.sleep(3)                                  │   │
│  │   Step 3: click → element.click() (nút Create)                  │   │
│  │   Step 4: upload_file → input.send_keys(video_path)             │   │
│  │   Step 5: enter_text → textarea.send_keys(caption)              │   │
│  │   Step 6: click → element.click() (nút Share)                   │   │
│  │                                                                  │   │
│  │ - Báo cáo tiến độ qua callback                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              ↓                                          │
│  BƯỚC 4: Hoàn thành                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ - Cập nhật trạng thái profile (completed/error)                 │   │
│  │ - Đóng browser hoặc giữ mở (tùy cấu hình)                       │   │
│  │ - Chuyển sang profile tiếp theo trong queue                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Ví dụ Code thực thi

```python
# 1. Khởi tạo các manager
profile_manager = ProfileManager()
browser_manager = BrowserManager(profile_manager)
automation_executor = AutomationExecutor()

# 2. Mở browser với Selenium
driver = browser_manager.launch_profile(
    profile_id="profile_123",
    use_selenium=True  # Bật chế độ automation
)

# 3. Chạy script
params = {
    "video_path": "C:/videos/my_video.mp4",
    "caption": "Hello Instagram! #automation"
}
automation_executor.execute_script(
    driver=driver,
    script_id="ig_post_video",
    params=params
)

# 4. Đóng browser
browser_manager.close_session("profile_123")
```

---

## Project Structure

```
Auto/
├── main.py                     # Main entry point - run this to start app
├── PROJECT_CONTEXT.md          # This file - project documentation
│
├── app/                        # Main application code
│   ├── __init__.py
│   ├── __main__.py
│   │
│   ├── core/                   # Core business logic
│   │   ├── __init__.py
│   │   ├── browser_manager.py  # Browser session management (subprocess/Selenium)
│   │   ├── profile_manager.py  # Profile lifecycle management
│   │   ├── fingerprint_generator.py  # Fingerprint randomization
│   │   ├── proxy_manager.py    # Proxy validation and auth extension
│   │   ├── session_manager.py  # Concurrent session management
│   │   ├── backup_manager.py   # Profile backup/restore
│   │   ├── script_manager.py   # Load và quản lý automation scripts
│   │   └── automation_executor.py  # Thực thi automation scripts
│   │
│   ├── data/                   # Data layer
│   │   ├── __init__.py
│   │   ├── profile_models.py   # Data models (ProfileData, GologinConfig, etc.)
│   │   └── profile_repository.py  # Database access (dual-database architecture)
│   │
│   ├── ui/                     # User interface (PyQt5)
│   │   ├── __init__.py
│   │   ├── styles.py           # White theme CSS styles
│   │   ├── widgets.py          # Custom widgets (StatusBadge, StatsCard, etc.)
│   │   └── main_window.py      # Main window with tabs
│   │
│   ├── gui/                    # Legacy GUI (from original project)
│   ├── helpers/                # Helper utilities
│   └── services/               # Service layer
│
├── automation_scripts/         # 🆕 Automation scripts (tách riêng)
│   ├── README.md               # Hướng dẫn viết script
│   ├── facebook/               # Facebook scripts
│   ├── instagram/              # Instagram scripts
│   ├── telegram/               # Telegram scripts
│   ├── tiktok/                 # TikTok scripts
│   ├── general/                # General scripts (login, etc.)
│   └── custom/                 # User custom scripts
│
├── data/                       # Data files
│   ├── data.db                 # Main database (READ-ONLY) - profiles from external app
│   ├── app_data.db             # App database (READ-WRITE) - app-specific data
│   ├── backup/                 # Profile backups
│   └── config.json             # App configuration
│
├── profile/                    # Chrome profile directories
│   └── {profile_id}/           # Each profile has its own folder
│       └── Default/            # Chrome Default profile folder
│           └── Preferences     # Fingerprint configuration (gologin section)
│
├── trinhduyet/                 # Browser binaries
│   └── orbita-browser/
│       └── chrome.exe          # Orbita browser executable
│
├── extensions/                 # Chrome extensions to load
│
├── tests/                      # Test files
│   ├── __init__.py
│   ├── conftest.py             # Pytest configuration (isolated temp databases)
│   ├── test_profile_models.py
│   ├── test_profile_repository.py
│   ├── test_profile_manager.py
│   ├── test_fingerprint_generator.py
│   ├── test_browser_manager.py
│   ├── test_proxy_manager.py
│   ├── test_session_manager.py
│   └── test_backup_manager.py
│
├── examples/                   # Demo and example scripts
│   ├── demo_database_sync.py
│   ├── demo_full_system.py
│   ├── demo_launch_profile.py
│   ├── demo_profile_manager.py
│   └── reset_app_database.py
│
└── .kiro/specs/                # Kiro spec files
    └── multi-profile-fingerprint-automation/
        ├── requirements.md
        ├── design.md
        └── tasks.md
```

## Database Architecture

### Dual-Database Design
- **data/data.db** (READ-ONLY): Original database with profiles from external app
- **data/app_data.db** (READ-WRITE): App database for status tracking, new profiles

### Auto-Sync
- On startup, new profiles from `data.db` are automatically imported to `app_data.db`
- Status updates only affect `app_data.db`, never `data.db`

## Key Features

### 1. Profile Management
- Load profiles from database
- View profile details (fingerprint, proxy, status)
- Filter and search profiles
- Backup/restore profiles

### 2. Browser Control
- **Manual Mode**: Opens browser with subprocess (no ChromeDriver needed)
- **Automation Mode**: Uses Selenium WebDriver (requires matching ChromeDriver)
- Window position calculation for non-overlapping windows

### 3. Fingerprint Management
- Read/write Preferences JSON
- Randomize noise values (audioContext, canvas, webGL, etc.)
- GPU configuration from predefined list

### 4. Proxy Support
- Validate proxy format (host:port or host:port:user:pass)
- Generate proxy auth extension for authenticated proxies

### 5. Session Management
- Concurrent session limit
- Batch execution with delay
- Session status tracking

## Running the App

```bash
# Install dependencies
pip install PyQt5 psutil selenium hypothesis pytest

# Run the app
python main.py

# Run tests
python -m pytest tests/ -v
```

## UI Overview

### Tab 1: Automation
- Script selection panel (left)
- Batch settings (max concurrent, delay)
- Profile table with checkboxes for batch selection
- Stats cards (Total, Selected, Running, Completed, Errors)
- Run Selected / Stop All buttons

### Tab 2: Profiles
- Profile table with actions
- Detail panel (right) with tabs:
  - Overview: ID, Name, Platform, Username, Path, Last Run
  - Fingerprint: User Agent, OS, WebGL info
  - Proxy: Host, Port, Status
- Open Browser (manual mode)
- Open Folder, Backup, Delete

## Tech Stack
- **Python 3.x**
- **PyQt5** - UI framework
- **SQLite** - Database
- **Selenium** - Browser automation (optional)
- **Hypothesis** - Property-based testing
- **psutil** - System monitoring

---

## 🔧 Các thành phần chính

### BrowserManager
Quản lý việc mở/đóng browser:
- `launch_profile(profile_id, use_selenium=False)` - Mở browser
- `close_session(profile_id)` - Đóng browser
- `get_active_sessions()` - Lấy danh sách session đang chạy

### AutomationExecutor
Thực thi automation scripts:
- `execute_script(driver, script_id, params)` - Chạy script
- `execute_step(driver, step, params)` - Thực hiện 1 bước
- `stop()` - Dừng automation

### ScriptManager
Quản lý automation scripts:
- `get_all_scripts()` - Lấy danh sách scripts
- `load_custom_script(script_id)` - Load script từ file

### SessionManager
Quản lý concurrent sessions:
- `start_batch(profile_ids, script_id, params)` - Chạy batch
- `stop_all()` - Dừng tất cả

---

## 📋 Workflow đầy đủ

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           WORKFLOW ĐẦY ĐỦ                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │   UI/GUI    │───▶│  Session    │───▶│  Browser    │                  │
│  │ main_window │    │  Manager    │    │  Manager    │                  │
│  └─────────────┘    └─────────────┘    └─────────────┘                  │
│         │                  │                  │                          │
│         │                  │                  ▼                          │
│         │                  │           ┌─────────────┐                  │
│         │                  │           │   Profile   │                  │
│         │                  │           │   Manager   │                  │
│         │                  │           └─────────────┘                  │
│         │                  │                  │                          │
│         │                  ▼                  ▼                          │
│         │           ┌─────────────┐    ┌─────────────┐                  │
│         │           │ Automation  │    │ Fingerprint │                  │
│         │           │  Executor   │    │  Generator  │                  │
│         │           └─────────────┘    └─────────────┘                  │
│         │                  │                                             │
│         │                  ▼                                             │
│         │           ┌─────────────┐                                     │
│         └──────────▶│   Script    │                                     │
│                     │   Manager   │                                     │
│                     └─────────────┘                                     │
│                            │                                             │
│                            ▼                                             │
│                     ┌─────────────┐                                     │
│                     │ automation_ │                                     │
│                     │  scripts/   │                                     │
│                     └─────────────┘                                     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```
