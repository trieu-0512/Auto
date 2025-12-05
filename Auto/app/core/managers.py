from app.helpers.tools import Communicate, Singleton




class Global:
    __metaclass__ = Singleton
    communicate = Communicate()


# Re-export new managers for convenience
from app.core.fingerprint_generator import FingerprintGenerator
from app.core.profile_manager import ProfileManager
from app.core.browser_manager import BrowserManager
from app.core.proxy_manager import ProxyManager
from app.core.session_manager import SessionManager
