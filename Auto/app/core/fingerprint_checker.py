# Fingerprint Checker - Kiểm tra fingerprint browser và báo cáo vấn đề
# Truy cập các trang test và phân tích kết quả

import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class FingerprintIssue:
    """Một vấn đề được phát hiện."""
    category: str  # webgl, canvas, timezone, etc.
    severity: str  # critical, warning, info
    message: str
    details: str = ""


@dataclass
class FingerprintReport:
    """Báo cáo kiểm tra fingerprint."""
    profile_id: str
    timestamp: str
    ip_address: str = ""
    location: str = ""
    browser_info: str = ""
    issues: List[FingerprintIssue] = field(default_factory=list)
    scores: Dict[str, str] = field(default_factory=dict)
    
    def add_issue(self, category: str, severity: str, message: str, details: str = ""):
        self.issues.append(FingerprintIssue(category, severity, message, details))
    
    def has_critical_issues(self) -> bool:
        return any(i.severity == "critical" for i in self.issues)
    
    def get_summary(self) -> str:
        critical = sum(1 for i in self.issues if i.severity == "critical")
        warning = sum(1 for i in self.issues if i.severity == "warning")
        info = sum(1 for i in self.issues if i.severity == "info")
        return f"Critical: {critical}, Warning: {warning}, Info: {info}"


class FingerprintChecker:
    """
    Kiểm tra fingerprint browser qua các trang test.
    Phân tích kết quả và báo cáo vấn đề.
    """
    
    # Các trang test fingerprint
    TEST_SITES = {
        "browserscan": "https://www.browserscan.net/",
        "pixelscan": "https://pixelscan.net/",
        "iphey": "https://iphey.com/",
        "creepjs": "https://abrahamjuliot.github.io/creepjs/",
        "bot_detection": "https://bot.sannysoft.com/",
    }
    
    def __init__(self, report_dir: str = "data/fingerprint_reports"):
        self.report_dir = report_dir
        os.makedirs(report_dir, exist_ok=True)
    
    def check_fingerprint(self, driver, profile_id: str) -> FingerprintReport:
        """
        Kiểm tra fingerprint đầy đủ.
        
        Args:
            driver: Selenium WebDriver
            profile_id: ID của profile đang kiểm tra
            
        Returns:
            FingerprintReport với các vấn đề được phát hiện
        """
        report = FingerprintReport(
            profile_id=profile_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Kiểm tra từng trang
        print(f"[FingerprintChecker] Bắt đầu kiểm tra profile {profile_id}...")
        
        # 1. Kiểm tra BrowserScan
        self._check_browserscan(driver, report)
        
        # 2. Kiểm tra PixelScan
        self._check_pixelscan(driver, report)
        
        # 3. Kiểm tra Bot Detection
        self._check_bot_detection(driver, report)
        
        # 4. Kiểm tra thông tin cơ bản
        self._check_basic_info(driver, report)
        
        # Lưu báo cáo
        self._save_report(report)
        
        return report
    
    def _check_browserscan(self, driver, report: FingerprintReport):
        """Kiểm tra BrowserScan.net"""
        try:
            print("[FingerprintChecker] Checking BrowserScan...")
            driver.get(self.TEST_SITES["browserscan"])
            time.sleep(8)  # Đợi scan hoàn tất
            
            # Lấy kết quả từ trang
            page_source = driver.page_source.lower()
            
            # Kiểm tra các vấn đề phổ biến
            if "bot detected" in page_source or "automation detected" in page_source:
                report.add_issue("automation", "critical", 
                    "Bot/Automation bị phát hiện", "BrowserScan phát hiện dấu hiệu automation")
            
            if "webgl" in page_source and "mismatch" in page_source:
                report.add_issue("webgl", "warning",
                    "WebGL không khớp", "Thông tin WebGL có thể không nhất quán")
            
            if "timezone" in page_source and ("mismatch" in page_source or "inconsistent" in page_source):
                report.add_issue("timezone", "warning",
                    "Timezone không khớp với IP", "Timezone browser không khớp với vị trí IP")
            
            if "canvas" in page_source and "blocked" in page_source:
                report.add_issue("canvas", "info",
                    "Canvas bị block", "Canvas fingerprint đang bị chặn")
            
            # Lấy điểm nếu có
            try:
                score_element = driver.execute_script("""
                    var scoreEl = document.querySelector('.score, [class*="score"], [class*="Score"]');
                    return scoreEl ? scoreEl.textContent : '';
                """)
                if score_element:
                    report.scores["browserscan"] = score_element.strip()
            except:
                pass
                
        except Exception as e:
            print(f"[FingerprintChecker] BrowserScan error: {e}")
    
    def _check_pixelscan(self, driver, report: FingerprintReport):
        """Kiểm tra PixelScan.net"""
        try:
            print("[FingerprintChecker] Checking PixelScan...")
            driver.get(self.TEST_SITES["pixelscan"])
            time.sleep(8)
            
            page_source = driver.page_source.lower()
            
            # Kiểm tra kết quả
            if "inconsistent" in page_source:
                report.add_issue("fingerprint", "warning",
                    "Fingerprint không nhất quán", "PixelScan phát hiện sự không nhất quán")
            
            if "proxy detected" in page_source or "vpn detected" in page_source:
                report.add_issue("proxy", "info",
                    "Proxy/VPN bị phát hiện", "Hệ thống phát hiện đang sử dụng proxy hoặc VPN")
            
            if "webrtc leak" in page_source:
                report.add_issue("webrtc", "critical",
                    "WebRTC leak", "IP thật bị lộ qua WebRTC")
            
            # Lấy điểm
            try:
                result = driver.execute_script("""
                    var el = document.querySelector('[class*="result"], [class*="status"]');
                    return el ? el.textContent : '';
                """)
                if result:
                    report.scores["pixelscan"] = result.strip()[:100]
            except:
                pass
                
        except Exception as e:
            print(f"[FingerprintChecker] PixelScan error: {e}")
    
    def _check_bot_detection(self, driver, report: FingerprintReport):
        """Kiểm tra Bot Detection (sannysoft)"""
        try:
            print("[FingerprintChecker] Checking Bot Detection...")
            driver.get(self.TEST_SITES["bot_detection"])
            time.sleep(5)
            
            # Kiểm tra các test cụ thể
            checks = {
                "webdriver": "WebDriver property",
                "chrome": "Chrome property",
                "permissions": "Permissions API",
                "plugins": "Plugins",
                "languages": "Languages",
                "webgl vendor": "WebGL Vendor",
                "broken image": "Broken Image",
            }
            
            for check_id, check_name in checks.items():
                try:
                    result = driver.execute_script(f"""
                        var rows = document.querySelectorAll('tr');
                        for (var row of rows) {{
                            if (row.textContent.toLowerCase().includes('{check_id}')) {{
                                var cells = row.querySelectorAll('td');
                                if (cells.length > 1) {{
                                    return cells[1].className || cells[1].textContent;
                                }}
                            }}
                        }}
                        return '';
                    """)
                    
                    if result and ("failed" in result.lower() or "red" in result.lower()):
                        report.add_issue("bot_detection", "critical",
                            f"{check_name} FAILED", f"Test {check_id} không pass")
                except:
                    pass
            
            report.scores["bot_detection"] = "Checked"
            
        except Exception as e:
            print(f"[FingerprintChecker] Bot Detection error: {e}")
    
    def _check_basic_info(self, driver, report: FingerprintReport):
        """Kiểm tra thông tin cơ bản của browser"""
        try:
            print("[FingerprintChecker] Checking basic info...")
            
            # Lấy User Agent
            user_agent = driver.execute_script("return navigator.userAgent;")
            report.browser_info = user_agent
            
            # Kiểm tra WebDriver property
            webdriver_present = driver.execute_script("return navigator.webdriver;")
            if webdriver_present:
                report.add_issue("webdriver", "critical",
                    "navigator.webdriver = true", "Browser bị đánh dấu là automation")
            
            # Kiểm tra plugins
            plugins_count = driver.execute_script("return navigator.plugins.length;")
            if plugins_count == 0:
                report.add_issue("plugins", "warning",
                    "Không có plugins", "Browser không có plugins, có thể bị nghi ngờ")
            
            # Kiểm tra languages
            languages = driver.execute_script("return navigator.languages;")
            if not languages or len(languages) == 0:
                report.add_issue("languages", "warning",
                    "Không có languages", "navigator.languages trống")
            
            # Kiểm tra screen resolution
            screen_width = driver.execute_script("return screen.width;")
            screen_height = driver.execute_script("return screen.height;")
            if screen_width == 0 or screen_height == 0:
                report.add_issue("screen", "warning",
                    "Screen resolution bất thường", f"Resolution: {screen_width}x{screen_height}")
            
            # Kiểm tra timezone
            timezone = driver.execute_script("return Intl.DateTimeFormat().resolvedOptions().timeZone;")
            report.scores["timezone"] = timezone
            
            # Lấy IP (nếu có thể)
            try:
                driver.get("https://api.ipify.org?format=text")
                time.sleep(2)
                ip = driver.find_element("tag name", "body").text
                report.ip_address = ip
            except:
                pass
                
        except Exception as e:
            print(f"[FingerprintChecker] Basic info error: {e}")
    
    def _save_report(self, report: FingerprintReport):
        """Lưu báo cáo ra file txt"""
        filename = f"fingerprint_{report.profile_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(self.report_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("       FINGERPRINT CHECK REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Profile ID: {report.profile_id}\n")
            f.write(f"Timestamp: {report.timestamp}\n")
            f.write(f"IP Address: {report.ip_address}\n")
            f.write(f"Browser: {report.browser_info[:80]}...\n" if len(report.browser_info) > 80 else f"Browser: {report.browser_info}\n")
            f.write("\n")
            
            f.write("-" * 60 + "\n")
            f.write("SUMMARY\n")
            f.write("-" * 60 + "\n")
            f.write(f"{report.get_summary()}\n")
            f.write(f"Status: {'❌ CÓ VẤN ĐỀ NGHIÊM TRỌNG' if report.has_critical_issues() else '✅ OK'}\n")
            f.write("\n")
            
            if report.issues:
                f.write("-" * 60 + "\n")
                f.write("ISSUES DETECTED\n")
                f.write("-" * 60 + "\n")
                
                for i, issue in enumerate(report.issues, 1):
                    severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(issue.severity, "⚪")
                    f.write(f"\n{i}. {severity_icon} [{issue.severity.upper()}] {issue.category}\n")
                    f.write(f"   Message: {issue.message}\n")
                    if issue.details:
                        f.write(f"   Details: {issue.details}\n")
            else:
                f.write("-" * 60 + "\n")
                f.write("✅ KHÔNG PHÁT HIỆN VẤN ĐỀ\n")
                f.write("-" * 60 + "\n")
            
            f.write("\n")
            if report.scores:
                f.write("-" * 60 + "\n")
                f.write("SCORES & INFO\n")
                f.write("-" * 60 + "\n")
                for key, value in report.scores.items():
                    f.write(f"  {key}: {value}\n")
            
            f.write("\n" + "=" * 60 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 60 + "\n")
        
        print(f"[FingerprintChecker] Report saved: {filepath}")
        return filepath
    
    def quick_check(self, driver, profile_id: str) -> Tuple[bool, str]:
        """
        Kiểm tra nhanh các vấn đề cơ bản.
        
        Returns:
            (is_ok, message) - True nếu không có vấn đề critical
        """
        issues = []
        
        try:
            # Kiểm tra webdriver
            if driver.execute_script("return navigator.webdriver;"):
                issues.append("WebDriver detected")
            
            # Kiểm tra plugins
            if driver.execute_script("return navigator.plugins.length;") == 0:
                issues.append("No plugins")
            
            # Kiểm tra automation flags
            chrome_present = driver.execute_script("""
                return window.chrome && window.chrome.runtime;
            """)
            if not chrome_present:
                issues.append("Chrome runtime missing")
            
        except Exception as e:
            issues.append(f"Check error: {e}")
        
        if issues:
            return False, f"Issues: {', '.join(issues)}"
        return True, "OK - No critical issues"
