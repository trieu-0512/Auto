# Browser Extensions

Thư mục chứa các Chrome extensions được tự động load khi mở browser.

## Extensions có sẵn

### 1. CapSolver - Tự động giải Captcha

Extension tự động giải các loại captcha:
- ✅ reCAPTCHA v2/v3
- ✅ hCaptcha
- ✅ Cloudflare Turnstile
- ✅ AWS WAF
- ✅ Image to Text (OCR)
- ✅ FunCaptcha

**Cách cấu hình:**

1. Đăng ký tài khoản tại https://www.capsolver.com/
2. Lấy API Key từ dashboard
3. Cập nhật file `data/capsolver_config.json`:
```json
{
  "apiKey": "YOUR_API_KEY_HERE",
  "autoSolve": true,
  "enabledForRecaptcha": true,
  "enabledForHCaptcha": true,
  "enabledForCloudflare": true
}
```

4. Hoặc cấu hình trực tiếp trong extension:
   - Mở browser
   - Click icon CapSolver trên toolbar
   - Nhập API Key
   - Bật các loại captcha cần giải

**Lưu ý:**
- CapSolver là dịch vụ trả phí (có free tier)
- Giá khoảng $0.5-2 / 1000 captcha tùy loại
- Extension tự động detect và giải captcha khi gặp

### 2. TimUID - Tìm UID Facebook

Extension lấy User ID từ profile Facebook.

**Cách sử dụng:**
- Mở profile Facebook
- Click icon TimUID
- Copy UID

## Thêm Extension mới

1. Tải extension (file .crx hoặc thư mục)
2. Giải nén vào thư mục `extensions/`
3. Đảm bảo có file `manifest.json` trong thư mục extension
4. Restart browser

## Cấu trúc thư mục

```
extensions/
├── README.md
├── CapSolver/           # Auto captcha solver
│   ├── manifest.json
│   ├── background.js
│   ├── recaptcha-recognition.js
│   ├── hcaptcha-recognition.js
│   └── ...
└── timuid/              # Facebook UID finder
    └── timuid_1_1/
        ├── manifest.json
        └── background.js
```

## Tắt Extension

Để tắt extension, đổi tên thư mục thêm prefix `_disabled_`:
```
CapSolver → _disabled_CapSolver
```
