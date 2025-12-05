# Multi-Profile Fingerprint Automation
# Fingerprint Generator for creating and randomizing browser fingerprints

import json
import os
import random
import uuid
from typing import Dict, Any, Optional, List

from app.data.profile_models import (
    GologinConfig, AudioContextConfig, CanvasConfig, ClientRectsConfig,
    WebGLConfig, WebGLMetadataConfig, NavigatorConfig, TimezoneConfig,
    GeolocationConfig, WebRTCConfig, FontsConfig, MediaDevicesConfig, ProxyConfig
)


class FingerprintGenerator:
    """
    Generator for creating and randomizing browser fingerprint configurations.
    """
    
    # Valid ranges for noise parameters
    AUDIO_NOISE_RANGE = (1e-8, 1e-7)
    CANVAS_NOISE_RANGE = (1.0, 10.0)
    CLIENT_RECTS_NOISE_RANGE = (1, 10)
    WEBGL_NOISE_RANGE = (1.0, 100.0)
    
    # Predefined GPU configurations
    GPU_CONFIGS = [
        {
            "vendor": "Google Inc. (Intel)",
            "renderer": "ANGLE (Intel, Intel(R) HD Graphics Family Direct3D11 vs_5_0 ps_5_0, D3D11)"
        },
        {
            "vendor": "Google Inc. (Intel)",
            "renderer": "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)"
        },
        {
            "vendor": "Google Inc. (Intel)",
            "renderer": "ANGLE (Intel, Intel(R) Iris Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"
        },
        {
            "vendor": "Google Inc. (NVIDIA)",
            "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 Direct3D11 vs_5_0 ps_5_0, D3D11)"
        },
        {
            "vendor": "Google Inc. (NVIDIA)",
            "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0, D3D11)"
        },
        {
            "vendor": "Google Inc. (NVIDIA)",
            "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"
        },
        {
            "vendor": "Google Inc. (AMD)",
            "renderer": "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0, D3D11)"
        },
        {
            "vendor": "Google Inc. (AMD)",
            "renderer": "ANGLE (AMD, AMD Radeon RX 5700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"
        }
    ]
    
    # Screen resolutions
    SCREEN_RESOLUTIONS = [
        (1920, 1080),
        (1366, 768),
        (1536, 864),
        (1440, 900),
        (1280, 720),
        (2560, 1440),
        (1600, 900)
    ]
    
    # Hardware configurations
    HARDWARE_CONCURRENCY = [2, 4, 6, 8, 12, 16]
    DEVICE_MEMORY = [2, 4, 8, 16, 32]
    
    # Timezones
    TIMEZONES = [
        "America/New_York",
        "America/Los_Angeles",
        "America/Chicago",
        "Europe/London",
        "Europe/Paris",
        "Asia/Tokyo",
        "Asia/Singapore",
        "Asia/Ho_Chi_Minh"
    ]
    
    # User agents
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    ]
    
    def __init__(self):
        """Initialize the fingerprint generator."""
        pass
    
    def generate_audio_noise(self) -> float:
        """Generate random audio context noise value."""
        return random.uniform(*self.AUDIO_NOISE_RANGE)
    
    def generate_canvas_noise(self) -> float:
        """Generate random canvas noise value."""
        return random.uniform(*self.CANVAS_NOISE_RANGE)
    
    def generate_client_rects_noise(self) -> int:
        """Generate random client rects noise value."""
        return random.randint(*self.CLIENT_RECTS_NOISE_RANGE)
    
    def generate_webgl_noise(self) -> float:
        """Generate random WebGL noise value."""
        return random.uniform(*self.WEBGL_NOISE_RANGE)
    
    def generate_gpu_config(self) -> Dict[str, str]:
        """Generate random GPU configuration from predefined list."""
        return random.choice(self.GPU_CONFIGS)
    
    def generate_screen_resolution(self) -> tuple:
        """Generate random screen resolution."""
        return random.choice(self.SCREEN_RESOLUTIONS)
    
    def generate_fingerprint(self) -> GologinConfig:
        """
        Generate complete random fingerprint configuration.
        
        Returns:
            GologinConfig with randomized values
        """
        # Generate noise values
        audio_noise = self.generate_audio_noise()
        canvas_noise = self.generate_canvas_noise()
        client_rects_noise = self.generate_client_rects_noise()
        webgl_noise = self.generate_webgl_noise()
        
        # Generate GPU config
        gpu_config = self.generate_gpu_config()
        
        # Generate screen resolution
        width, height = self.generate_screen_resolution()
        
        # Generate hardware config
        hardware_concurrency = random.choice(self.HARDWARE_CONCURRENCY)
        device_memory = random.choice(self.DEVICE_MEMORY)
        
        # Generate other settings
        timezone = random.choice(self.TIMEZONES)
        user_agent = random.choice(self.USER_AGENTS)
        
        # Create config
        config = GologinConfig(
            audioContext=AudioContextConfig(enable=True, noiseValue=audio_noise),
            canvas=CanvasConfig(mode="noise", noise=canvas_noise),
            canvasNoise=canvas_noise,
            canvasMode="noise",
            clientRects=ClientRectsConfig(mode=True, noise=client_rects_noise),
            getClientRectsNoice=client_rects_noise,
            get_client_rects_noise=client_rects_noise,
            webGL=WebGLConfig(mode="noise", noise=webgl_noise, getClientRectsNoise=client_rects_noise),
            webGLMetadata=WebGLMetadataConfig(
                mode="mask",
                renderer=gpu_config["renderer"],
                vendor=gpu_config["vendor"]
            ),
            webglNoiseValue=webgl_noise,
            webglNoiceEnable="noise",
            navigator=NavigatorConfig(
                deviceMemory=device_memory,
                hardwareConcurrency=hardware_concurrency,
                language="en-US",
                platform="Win32",
                userAgent=user_agent,
                maxTouchPoints=0,
                resolution=f"{width}x{height}",
                doNotTrack=True
            ),
            userAgent=user_agent,
            hardwareConcurrency=hardware_concurrency,
            deviceMemory=device_memory,
            devicePixelRatio=random.choice([1.0, 1.25, 1.5, 2.0]),
            screenWidth=width,
            screenHeight=height,
            timezone=TimezoneConfig(id=timezone),
            geolocation=GeolocationConfig(mode="block"),
            geoLocation=GeolocationConfig(mode="block"),
            webRTC=WebRTCConfig(mode="disabled"),
            webRtc=WebRTCConfig(mode="disabled"),
            fonts=FontsConfig(enableMasking=True, enableDomRect=True),
            mediaDevices=MediaDevicesConfig(
                enable=True,
                enableMasking=True,
                audioInputs=random.randint(1, 3),
                audioOutputs=random.randint(1, 2),
                videoInputs=random.randint(0, 1),
                uid=uuid.uuid4().hex
            ),
            proxy=ProxyConfig(mode="none"),
            proxyEnabled=False,
            doNotTrack=True,
            browserType="chrome",
            os="win",
            startUrl="https://google.com",
            langHeader="en-US",
            language="en-US",
            languages="en-US",
            debugMode=False,
            googleServicesEnabled=True,
            checkCookies=False,
            canBeRunning=True,
            lockEnabled=False
        )
        
        return config
    
    def randomize_noise_values(self, config: GologinConfig) -> GologinConfig:
        """
        Randomize all noise values in existing config.
        
        Args:
            config: Existing GologinConfig to modify
            
        Returns:
            Modified GologinConfig with new random noise values
        """
        # Randomize audio noise
        audio_noise = self.generate_audio_noise()
        config.audioContext.noiseValue = audio_noise
        
        # Randomize canvas noise
        canvas_noise = self.generate_canvas_noise()
        config.canvas.noise = canvas_noise
        config.canvasNoise = canvas_noise
        
        # Randomize client rects noise
        client_rects_noise = self.generate_client_rects_noise()
        config.clientRects.noise = client_rects_noise
        config.getClientRectsNoice = client_rects_noise
        config.get_client_rects_noise = client_rects_noise
        config.webGL.getClientRectsNoise = client_rects_noise
        
        # Randomize WebGL noise
        webgl_noise = self.generate_webgl_noise()
        config.webGL.noise = webgl_noise
        config.webglNoiseValue = webgl_noise
        
        # Randomize GPU config
        gpu_config = self.generate_gpu_config()
        config.webGLMetadata.renderer = gpu_config["renderer"]
        config.webGLMetadata.vendor = gpu_config["vendor"]
        
        return config
    
    def read_preferences(self, profile_path: str) -> Optional[Dict[str, Any]]:
        """
        Read and parse Default/Preferences JSON file.
        
        Args:
            profile_path: Path to profile directory
            
        Returns:
            Parsed preferences dict or None if file not found
        """
        prefs_path = os.path.join(profile_path, "Default", "Preferences")
        
        if not os.path.exists(prefs_path):
            return None
        
        try:
            with open(prefs_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading preferences: {e}")
            return None
    
    def write_preferences(self, profile_path: str, prefs: Dict[str, Any]) -> bool:
        """
        Write updated config to Default/Preferences file.
        
        Args:
            profile_path: Path to profile directory
            prefs: Preferences dict to write
            
        Returns:
            True if successful, False otherwise
        """
        prefs_path = os.path.join(profile_path, "Default", "Preferences")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(prefs_path), exist_ok=True)
        
        try:
            with open(prefs_path, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error writing preferences: {e}")
            return False
    
    def extract_gologin_config(self, prefs: Dict[str, Any]) -> Optional[GologinConfig]:
        """
        Extract gologin configuration from preferences dict.
        
        Args:
            prefs: Full preferences dict
            
        Returns:
            GologinConfig or None if not found
        """
        if 'gologin' not in prefs:
            return None
        
        return GologinConfig.from_dict(prefs['gologin'])
    
    def update_gologin_config(self, prefs: Dict[str, Any], config: GologinConfig) -> Dict[str, Any]:
        """
        Update gologin section in preferences dict.
        
        Args:
            prefs: Full preferences dict
            config: New GologinConfig to apply
            
        Returns:
            Updated preferences dict
        """
        prefs['gologin'] = config.to_dict()
        return prefs
    
    def is_gpu_config_valid(self, renderer: str, vendor: str) -> bool:
        """
        Check if GPU configuration is from the valid list.
        
        Args:
            renderer: GPU renderer string
            vendor: GPU vendor string
            
        Returns:
            True if configuration is valid
        """
        for gpu in self.GPU_CONFIGS:
            if gpu["renderer"] == renderer and gpu["vendor"] == vendor:
                return True
        return False
    
    def is_noise_in_range(self, noise_type: str, value: float) -> bool:
        """
        Check if noise value is within valid range.
        
        Args:
            noise_type: Type of noise ('audio', 'canvas', 'client_rects', 'webgl')
            value: Noise value to check
            
        Returns:
            True if value is within valid range
        """
        ranges = {
            'audio': self.AUDIO_NOISE_RANGE,
            'canvas': self.CANVAS_NOISE_RANGE,
            'client_rects': self.CLIENT_RECTS_NOISE_RANGE,
            'webgl': self.WEBGL_NOISE_RANGE
        }
        
        if noise_type not in ranges:
            return False
        
        min_val, max_val = ranges[noise_type]
        return min_val <= value <= max_val

    def update_user_agent(self, profile_path: str, chrome_version: str = "129") -> bool:
        """
        Update User Agent in profile Preferences to match Orbita version.
        
        Args:
            profile_path: Path to profile directory
            chrome_version: Chrome version number (e.g., "129")
            
        Returns:
            True if successful
        """
        prefs = self.read_preferences(profile_path)
        if not prefs:
            return False
        
        # Build new User Agent
        new_ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36"
        
        # Update in gologin section
        if 'gologin' not in prefs:
            prefs['gologin'] = {}
        
        if 'navigator' not in prefs['gologin']:
            prefs['gologin']['navigator'] = {}
        
        prefs['gologin']['navigator']['userAgent'] = new_ua
        
        # Also update userAgent at root level if exists
        if 'userAgent' in prefs['gologin']:
            prefs['gologin']['userAgent'] = new_ua
        
        return self.write_preferences(profile_path, prefs)
    
    def fix_user_agent_mismatch(self, profile_path: str, orbita_version: str = "129.0.6668.101") -> bool:
        """
        Fix User Agent to match Orbita browser version.
        
        Args:
            profile_path: Path to profile directory
            orbita_version: Full Orbita version string
            
        Returns:
            True if successful
        """
        # Extract major version
        major_version = orbita_version.split('.')[0]
        return self.update_user_agent(profile_path, major_version)
