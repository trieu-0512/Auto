# Multi-Profile Fingerprint Automation
# Data Models for Profile Management

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
import json


@dataclass
class AudioContextConfig:
    """Audio fingerprint configuration."""
    enable: bool = True
    noiseValue: float = 0.0


@dataclass
class CanvasConfig:
    """Canvas fingerprint configuration."""
    mode: str = "noise"
    noise: float = 0.0


@dataclass
class ClientRectsConfig:
    """Client rects fingerprint configuration."""
    mode: bool = True
    noise: int = 0


@dataclass
class WebGLConfig:
    """WebGL noise configuration."""
    mode: str = "noise"
    noise: float = 0.0
    getClientRectsNoise: int = 0


@dataclass
class WebGLMetadataConfig:
    """WebGL metadata (GPU) configuration."""
    mode: str = "mask"
    renderer: str = ""
    vendor: str = ""


@dataclass
class NavigatorConfig:
    """Navigator fingerprint configuration."""
    deviceMemory: int = 8
    hardwareConcurrency: int = 4
    language: str = "en-US"
    platform: str = "Win32"
    userAgent: str = ""
    maxTouchPoints: int = 0
    resolution: str = "1920x1080"
    doNotTrack: bool = True


@dataclass
class TimezoneConfig:
    """Timezone configuration."""
    id: str = "America/New_York"


@dataclass
class GeolocationConfig:
    """Geolocation configuration."""
    mode: str = "block"
    enabled: bool = True
    customize: bool = True
    fillBasedOnIp: bool = True
    latitude: float = 0.0
    longitude: float = 0.0
    accuracy: int = 100


@dataclass
class WebRTCConfig:
    """WebRTC configuration."""
    mode: str = "disabled"
    enabled: bool = True
    customize: bool = True
    fillBasedOnIp: bool = True
    localIpMasking: bool = True
    publicIp: str = ""
    localIps: List[str] = field(default_factory=list)


@dataclass
class FontsConfig:
    """Fonts configuration."""
    enableMasking: bool = True
    enableDomRect: bool = True
    families: List[str] = field(default_factory=list)


@dataclass
class MediaDevicesConfig:
    """Media devices configuration."""
    enable: bool = True
    enableMasking: bool = True
    audioInputs: int = 2
    audioOutputs: int = 1
    videoInputs: int = 0
    uid: str = ""


@dataclass
class ProxyConfig:
    """Proxy configuration."""
    mode: str = "none"
    host: str = ""
    port: str = ""
    username: str = ""
    password: str = ""



@dataclass
class GologinConfig:
    """
    Complete GoLogin fingerprint configuration.
    Maps to the 'gologin' section in Default/Preferences file.
    """
    # Audio fingerprint
    audioContext: AudioContextConfig = field(default_factory=AudioContextConfig)
    
    # Canvas fingerprint
    canvas: CanvasConfig = field(default_factory=CanvasConfig)
    canvasNoise: float = 0.0
    canvasMode: str = "noise"
    
    # Client rects
    clientRects: ClientRectsConfig = field(default_factory=ClientRectsConfig)
    getClientRectsNoice: int = 0
    get_client_rects_noise: int = 0
    
    # WebGL
    webGL: WebGLConfig = field(default_factory=WebGLConfig)
    webGLMetadata: WebGLMetadataConfig = field(default_factory=WebGLMetadataConfig)
    webglNoiseValue: float = 0.0
    webglNoiceEnable: str = "noise"
    
    # Navigator
    navigator: NavigatorConfig = field(default_factory=NavigatorConfig)
    userAgent: str = ""
    hardwareConcurrency: int = 4
    deviceMemory: int = 8
    devicePixelRatio: float = 1.0
    
    # Screen
    screenWidth: int = 1920
    screenHeight: int = 1080
    
    # Timezone & Location
    timezone: TimezoneConfig = field(default_factory=TimezoneConfig)
    geolocation: GeolocationConfig = field(default_factory=GeolocationConfig)
    geoLocation: GeolocationConfig = field(default_factory=GeolocationConfig)
    
    # WebRTC
    webRTC: WebRTCConfig = field(default_factory=WebRTCConfig)
    webRtc: WebRTCConfig = field(default_factory=WebRTCConfig)
    
    # Fonts
    fonts: FontsConfig = field(default_factory=FontsConfig)
    
    # Media devices
    mediaDevices: MediaDevicesConfig = field(default_factory=MediaDevicesConfig)
    
    # Proxy
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    proxyEnabled: bool = False
    
    # Other settings
    doNotTrack: bool = True
    browserType: str = "chrome"
    os: str = "win"
    name: str = ""
    profile_id: str = ""
    startUrl: str = "https://google.com"
    langHeader: str = "en-US"
    language: str = "en-US"
    languages: str = "en-US"
    debugMode: bool = False
    googleServicesEnabled: bool = True
    checkCookies: bool = False
    canBeRunning: bool = True
    lockEnabled: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GologinConfig':
        """Create GologinConfig from dictionary."""
        config = cls()
        
        # Audio context
        if 'audioContext' in data:
            ac = data['audioContext']
            config.audioContext = AudioContextConfig(
                enable=ac.get('enable', True),
                noiseValue=ac.get('noiseValue', 0.0)
            )
        
        # Canvas
        if 'canvas' in data:
            c = data['canvas']
            config.canvas = CanvasConfig(
                mode=c.get('mode', 'noise'),
                noise=c.get('noise', 0.0)
            )
        config.canvasNoise = data.get('canvasNoise', 0.0)
        config.canvasMode = data.get('canvasMode', 'noise')
        
        # Client rects
        if 'clientRects' in data:
            cr = data['clientRects']
            config.clientRects = ClientRectsConfig(
                mode=cr.get('mode', True),
                noise=cr.get('noise', 0)
            )
        config.getClientRectsNoice = data.get('getClientRectsNoice', 0)
        config.get_client_rects_noise = data.get('get_client_rects_noise', 0)
        
        # WebGL
        if 'webGL' in data:
            wgl = data['webGL']
            config.webGL = WebGLConfig(
                mode=wgl.get('mode', 'noise'),
                noise=wgl.get('noise', 0.0),
                getClientRectsNoise=wgl.get('getClientRectsNoise', 0)
            )
        if 'webGLMetadata' in data:
            wglm = data['webGLMetadata']
            config.webGLMetadata = WebGLMetadataConfig(
                mode=wglm.get('mode', 'mask'),
                renderer=wglm.get('renderer', ''),
                vendor=wglm.get('vendor', '')
            )
        config.webglNoiseValue = data.get('webglNoiseValue', 0.0)
        config.webglNoiceEnable = data.get('webglNoiceEnable', 'noise')
        
        # Navigator
        if 'navigator' in data:
            nav = data['navigator']
            config.navigator = NavigatorConfig(
                deviceMemory=nav.get('deviceMemory', 8),
                hardwareConcurrency=nav.get('hardwareConcurrency', 4),
                language=nav.get('language', 'en-US'),
                platform=nav.get('platform', 'Win32'),
                userAgent=nav.get('userAgent', ''),
                maxTouchPoints=nav.get('maxTouchPoints', 0),
                resolution=nav.get('resolution', '1920x1080'),
                doNotTrack=nav.get('doNotTrack', True)
            )
        config.userAgent = data.get('userAgent', '')
        config.hardwareConcurrency = data.get('hardwareConcurrency', 4)
        config.deviceMemory = data.get('deviceMemory', 8)
        config.devicePixelRatio = data.get('devicePixelRatio', 1.0)
        
        # Screen
        config.screenWidth = data.get('screenWidth', 1920)
        config.screenHeight = data.get('screenHeight', 1080)
        
        # Timezone
        if 'timezone' in data:
            tz = data['timezone']
            config.timezone = TimezoneConfig(id=tz.get('id', 'America/New_York'))
        
        # Geolocation
        for geo_key in ['geolocation', 'geoLocation']:
            if geo_key in data:
                geo = data[geo_key]
                geo_config = GeolocationConfig(
                    mode=geo.get('mode', 'block'),
                    enabled=geo.get('enabled', True),
                    customize=geo.get('customize', True),
                    fillBasedOnIp=geo.get('fillBasedOnIp', True),
                    latitude=geo.get('latitude', 0.0),
                    longitude=geo.get('longitude', 0.0),
                    accuracy=geo.get('accuracy', 100)
                )
                if geo_key == 'geolocation':
                    config.geolocation = geo_config
                else:
                    config.geoLocation = geo_config
        
        # WebRTC
        for rtc_key in ['webRTC', 'webRtc']:
            if rtc_key in data:
                rtc = data[rtc_key]
                rtc_config = WebRTCConfig(
                    mode=rtc.get('mode', 'disabled'),
                    enabled=rtc.get('enabled', True),
                    customize=rtc.get('customize', True),
                    fillBasedOnIp=rtc.get('fillBasedOnIp', True),
                    localIpMasking=rtc.get('localIpMasking', True),
                    publicIp=rtc.get('publicIp', '') or rtc.get('publicIP', '') or '',
                    localIps=rtc.get('localIps', [])
                )
                if rtc_key == 'webRTC':
                    config.webRTC = rtc_config
                else:
                    config.webRtc = rtc_config
        
        # Fonts
        if 'fonts' in data:
            f = data['fonts']
            config.fonts = FontsConfig(
                enableMasking=f.get('enableMasking', True),
                enableDomRect=f.get('enableDomRect', True),
                families=f.get('families', [])
            )
        
        # Media devices
        if 'mediaDevices' in data:
            md = data['mediaDevices']
            config.mediaDevices = MediaDevicesConfig(
                enable=md.get('enable', True),
                enableMasking=md.get('enableMasking', True),
                audioInputs=md.get('audioInputs', 2),
                audioOutputs=md.get('audioOutputs', 1),
                videoInputs=md.get('videoInputs', 0),
                uid=md.get('uid', '')
            )
        
        # Proxy
        if 'proxy' in data:
            p = data['proxy']
            config.proxy = ProxyConfig(
                mode=p.get('mode', 'none'),
                host=str(p.get('host', '')),
                port=str(p.get('port', '')),
                username=p.get('username', ''),
                password=p.get('password', '')
            )
        config.proxyEnabled = data.get('proxyEnabled', False)
        
        # Other settings
        config.doNotTrack = data.get('doNotTrack', True)
        config.browserType = data.get('browserType', 'chrome')
        config.os = data.get('os', 'win')
        config.name = data.get('name', '')
        config.profile_id = data.get('profile_id', '')
        config.startUrl = data.get('startUrl', 'https://google.com')
        config.langHeader = data.get('langHeader', 'en-US')
        config.language = data.get('language', 'en-US')
        config.languages = data.get('languages', 'en-US')
        config.debugMode = data.get('debugMode', False)
        config.googleServicesEnabled = data.get('googleServicesEnabled', True)
        config.checkCookies = data.get('checkCookies', False)
        config.canBeRunning = data.get('canBeRunning', True)
        config.lockEnabled = data.get('lockEnabled', False)
        
        return config


@dataclass
class ProfileData:
    """
    Database record for profile from danhsachacc table.
    """
    id: int = 0
    name: str = ""
    idprofile: str = ""
    proxymode: str = "none"
    proxy: str = ""
    status: str = "inactive"
    username_fb: str = ""
    password_fb: str = ""
    ma2fa: str = ""
    list_uid: str = ""
    list_group: str = ""
    control_fb: str = ""
    username_gmail: str = ""
    password_gmail: str = ""
    gmail_khoiphuc: str = ""
    sothutu: int = 0
    notes: str = ""
    cookies: str = ""
    group_profile: str = ""
    last_run: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfileData':
        """Create ProfileData from dictionary."""
        return cls(
            id=data.get('id', 0),
            name=data.get('name', ''),
            idprofile=data.get('idprofile', ''),
            proxymode=data.get('proxymode', 'none'),
            proxy=data.get('proxy', ''),
            status=data.get('status', 'inactive'),
            username_fb=data.get('username_fb', ''),
            password_fb=data.get('password_fb', ''),
            ma2fa=data.get('ma2fa', ''),
            list_uid=data.get('list_uid', ''),
            list_group=data.get('list_group', ''),
            control_fb=data.get('control_fb', ''),
            username_gmail=data.get('username_gmail', ''),
            password_gmail=data.get('password_gmail', ''),
            gmail_khoiphuc=data.get('gmail_khoiphuc', ''),
            sothutu=data.get('sothutu', 0) or 0,
            notes=data.get('notes', ''),
            cookies=data.get('cookies', ''),
            group_profile=data.get('group_profile', ''),
            last_run=data.get('last_run', '')
        )
    
    @classmethod
    def from_db_row(cls, row: tuple, columns: List[str]) -> 'ProfileData':
        """Create ProfileData from database row."""
        data = dict(zip(columns, row))
        return cls(
            id=data.get('id', 0),
            name=data.get('name', ''),
            idprofile=data.get('idprofile', ''),
            proxymode=data.get('proxymode', 'none'),
            proxy=data.get('proxy', ''),
            status=data.get('status', 'inactive'),
            username_fb=data.get('username_fb', ''),
            password_fb=data.get('password_fb', ''),
            ma2fa=data.get('ma2fa', ''),
            list_uid=data.get('list_uid', ''),
            list_group=data.get('list_group', ''),
            control_fb=data.get('control_fb', ''),
            username_gmail=data.get('username_gmail', ''),
            password_gmail=data.get('password_gmail', ''),
            gmail_khoiphuc=data.get('gmail_khoiphuc', ''),
            sothutu=data.get('sothutu', 0) or 0,
            notes=data.get('notes', ''),
            cookies=data.get('cookies', ''),
            group_profile=data.get('group_profile', ''),
            last_run=data.get('last_run', '')
        )


@dataclass
class Profile:
    """
    Business object combining database data and fingerprint configuration.
    """
    data: ProfileData
    fingerprint: Optional[GologinConfig] = None
    path: str = ""
    exists: bool = False
    
    @property
    def profile_id(self) -> str:
        """Get profile ID."""
        return self.data.idprofile
    
    @property
    def name(self) -> str:
        """Get profile name."""
        return self.data.name
    
    @property
    def status(self) -> str:
        """Get profile status."""
        return self.data.status
    
    @property
    def proxy(self) -> str:
        """Get proxy configuration."""
        return self.data.proxy
    
    def to_display_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for display."""
        return {
            'id': self.data.id,
            'profile_id': self.data.idprofile,
            'name': self.data.name,
            'status': self.data.status,
            'proxy': self.data.proxy,
            'proxymode': self.data.proxymode,
            'username': self.data.username_fb,
            'last_run': self.data.last_run,
            'group': self.data.group_profile,
            'exists': self.exists,
            'path': self.path
        }
