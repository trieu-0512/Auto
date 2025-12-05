# Property-based tests for Profile Models
# Feature: multi-profile-fingerprint-automation

import pytest
from hypothesis import given, strategies as st, settings
import json

from app.data.profile_models import (
    GologinConfig, ProfileData, Profile,
    AudioContextConfig, CanvasConfig, ClientRectsConfig,
    WebGLConfig, WebGLMetadataConfig, NavigatorConfig,
    TimezoneConfig, GeolocationConfig, WebRTCConfig,
    FontsConfig, MediaDevicesConfig, ProxyConfig
)


# Strategies for generating test data
audio_context_strategy = st.builds(
    AudioContextConfig,
    enable=st.booleans(),
    noiseValue=st.floats(min_value=1e-10, max_value=1e-5, allow_nan=False, allow_infinity=False)
)

canvas_strategy = st.builds(
    CanvasConfig,
    mode=st.sampled_from(["noise", "off"]),
    noise=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
)

client_rects_strategy = st.builds(
    ClientRectsConfig,
    mode=st.booleans(),
    noise=st.integers(min_value=0, max_value=100)
)

webgl_strategy = st.builds(
    WebGLConfig,
    mode=st.sampled_from(["noise", "off"]),
    noise=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    getClientRectsNoise=st.integers(min_value=0, max_value=100)
)

webgl_metadata_strategy = st.builds(
    WebGLMetadataConfig,
    mode=st.sampled_from(["mask", "off"]),
    renderer=st.text(min_size=0, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S'))),
    vendor=st.text(min_size=0, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S')))
)

navigator_strategy = st.builds(
    NavigatorConfig,
    deviceMemory=st.sampled_from([2, 4, 8, 16, 32]),
    hardwareConcurrency=st.integers(min_value=1, max_value=16),
    language=st.sampled_from(["en-US", "en-GB", "vi-VN", "zh-CN"]),
    platform=st.sampled_from(["Win32", "Win64", "MacIntel", "Linux x86_64"]),
    userAgent=st.text(min_size=0, max_size=200, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S', 'Z'))),
    maxTouchPoints=st.integers(min_value=0, max_value=10),
    resolution=st.sampled_from(["1920x1080", "1366x768", "1280x720", "2560x1440"]),
    doNotTrack=st.booleans()
)

timezone_strategy = st.builds(
    TimezoneConfig,
    id=st.sampled_from(["America/New_York", "Europe/London", "Asia/Ho_Chi_Minh", "UTC"])
)

geolocation_strategy = st.builds(
    GeolocationConfig,
    mode=st.sampled_from(["block", "allow", "prompt"]),
    enabled=st.booleans(),
    customize=st.booleans(),
    fillBasedOnIp=st.booleans(),
    latitude=st.floats(min_value=-90.0, max_value=90.0, allow_nan=False, allow_infinity=False),
    longitude=st.floats(min_value=-180.0, max_value=180.0, allow_nan=False, allow_infinity=False),
    accuracy=st.integers(min_value=1, max_value=1000)
)

webrtc_strategy = st.builds(
    WebRTCConfig,
    mode=st.sampled_from(["disabled", "public", "real"]),
    enabled=st.booleans(),
    customize=st.booleans(),
    fillBasedOnIp=st.booleans(),
    localIpMasking=st.booleans(),
    publicIp=st.from_regex(r'^(\d{1,3}\.){3}\d{1,3}$|^$', fullmatch=True),
    localIps=st.lists(st.from_regex(r'^(\d{1,3}\.){3}\d{1,3}$', fullmatch=True), max_size=3)
)

fonts_strategy = st.builds(
    FontsConfig,
    enableMasking=st.booleans(),
    enableDomRect=st.booleans(),
    families=st.lists(st.sampled_from(["Arial", "Verdana", "Times New Roman", "Courier New"]), max_size=10)
)

media_devices_strategy = st.builds(
    MediaDevicesConfig,
    enable=st.booleans(),
    enableMasking=st.booleans(),
    audioInputs=st.integers(min_value=0, max_value=5),
    audioOutputs=st.integers(min_value=0, max_value=5),
    videoInputs=st.integers(min_value=0, max_value=3),
    uid=st.text(min_size=0, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))
)

proxy_strategy = st.builds(
    ProxyConfig,
    mode=st.sampled_from(["none", "http", "socks5"]),
    host=st.from_regex(r'^(\d{1,3}\.){3}\d{1,3}$|^$', fullmatch=True),
    port=st.from_regex(r'^\d{1,5}$|^$', fullmatch=True),
    username=st.text(min_size=0, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N'))),
    password=st.text(min_size=0, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N')))
)


# Composite strategy for GologinConfig
@st.composite
def gologin_config_strategy(draw):
    return GologinConfig(
        audioContext=draw(audio_context_strategy),
        canvas=draw(canvas_strategy),
        canvasNoise=draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
        canvasMode=draw(st.sampled_from(["noise", "off"])),
        clientRects=draw(client_rects_strategy),
        getClientRectsNoice=draw(st.integers(min_value=0, max_value=100)),
        get_client_rects_noise=draw(st.integers(min_value=0, max_value=100)),
        webGL=draw(webgl_strategy),
        webGLMetadata=draw(webgl_metadata_strategy),
        webglNoiseValue=draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
        webglNoiceEnable=draw(st.sampled_from(["noise", "off"])),
        navigator=draw(navigator_strategy),
        userAgent=draw(st.text(min_size=0, max_size=200, alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S', 'Z')))),
        hardwareConcurrency=draw(st.integers(min_value=1, max_value=16)),
        deviceMemory=draw(st.sampled_from([2, 4, 8, 16, 32])),
        devicePixelRatio=draw(st.floats(min_value=0.5, max_value=3.0, allow_nan=False, allow_infinity=False)),
        screenWidth=draw(st.sampled_from([1280, 1366, 1920, 2560])),
        screenHeight=draw(st.sampled_from([720, 768, 1080, 1440])),
        timezone=draw(timezone_strategy),
        geolocation=draw(geolocation_strategy),
        geoLocation=draw(geolocation_strategy),
        webRTC=draw(webrtc_strategy),
        webRtc=draw(webrtc_strategy),
        fonts=draw(fonts_strategy),
        mediaDevices=draw(media_devices_strategy),
        proxy=draw(proxy_strategy),
        proxyEnabled=draw(st.booleans()),
        doNotTrack=draw(st.booleans()),
        browserType=draw(st.sampled_from(["chrome", "firefox"])),
        os=draw(st.sampled_from(["win", "mac", "lin"])),
        name=draw(st.text(min_size=0, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'P')))),
        profile_id=draw(st.text(min_size=0, max_size=30, alphabet=st.characters(whitelist_categories=('N',)))),
        startUrl=draw(st.sampled_from(["https://google.com", "https://facebook.com", "about:blank"])),
        langHeader=draw(st.sampled_from(["en-US", "en-GB", "vi-VN"])),
        language=draw(st.sampled_from(["en-US", "en-GB", "vi-VN"])),
        languages=draw(st.sampled_from(["en-US", "en-GB", "vi-VN"])),
        debugMode=draw(st.booleans()),
        googleServicesEnabled=draw(st.booleans()),
        checkCookies=draw(st.booleans()),
        canBeRunning=draw(st.booleans()),
        lockEnabled=draw(st.booleans())
    )


class TestGologinConfigRoundTrip:
    """
    **Feature: multi-profile-fingerprint-automation, Property 3: Preferences JSON Round-Trip**
    **Validates: Requirements 1.3, 1.6, 2.6**
    
    For any valid GologinConfig object, serializing to dict and parsing back
    SHALL produce an equivalent configuration object.
    """
    
    @given(
        audio_noise=st.floats(min_value=1e-10, max_value=1e-5, allow_nan=False, allow_infinity=False),
        canvas_noise=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        webgl_noise=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        client_rects_noise=st.integers(min_value=0, max_value=100),
        renderer=st.sampled_from(["ANGLE (Intel)", "ANGLE (NVIDIA)", "ANGLE (AMD)"]),
        vendor=st.sampled_from(["Google Inc. (Intel)", "Google Inc. (NVIDIA)", "Google Inc. (AMD)"])
    )
    @settings(max_examples=100)
    def test_gologin_config_round_trip(self, audio_noise, canvas_noise, webgl_noise, 
                                        client_rects_noise, renderer, vendor):
        """Test that GologinConfig survives round-trip through dict conversion."""
        # Create config with random values
        config = GologinConfig()
        config.audioContext.noiseValue = audio_noise
        config.canvas.noise = canvas_noise
        config.canvasNoise = canvas_noise
        config.webGL.noise = webgl_noise
        config.webglNoiseValue = webgl_noise
        config.clientRects.noise = client_rects_noise
        config.getClientRectsNoice = client_rects_noise
        config.webGLMetadata.renderer = renderer
        config.webGLMetadata.vendor = vendor
        
        # Serialize to dict
        config_dict = config.to_dict()
        
        # Parse back from dict
        restored_config = GologinConfig.from_dict(config_dict)
        
        # Verify key noise values are preserved
        assert restored_config.audioContext.noiseValue == audio_noise
        assert restored_config.canvas.noise == canvas_noise
        assert restored_config.canvasNoise == canvas_noise
        assert restored_config.clientRects.noise == client_rects_noise
        assert restored_config.getClientRectsNoice == client_rects_noise
        assert restored_config.webGL.noise == webgl_noise
        assert restored_config.webglNoiseValue == webgl_noise
        
        # Verify WebGL metadata
        assert restored_config.webGLMetadata.renderer == renderer
        assert restored_config.webGLMetadata.vendor == vendor
    
    @given(
        audio_noise=st.floats(min_value=1e-10, max_value=1e-5, allow_nan=False, allow_infinity=False),
        canvas_noise=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        webgl_noise=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_gologin_config_json_round_trip(self, audio_noise, canvas_noise, webgl_noise):
        """Test that GologinConfig survives round-trip through JSON serialization."""
        # Create config
        config = GologinConfig()
        config.audioContext.noiseValue = audio_noise
        config.canvas.noise = canvas_noise
        config.webGL.noise = webgl_noise
        
        # Serialize to JSON string
        config_dict = config.to_dict()
        json_str = json.dumps(config_dict)
        
        # Parse back from JSON
        parsed_dict = json.loads(json_str)
        restored_config = GologinConfig.from_dict(parsed_dict)
        
        # Verify key values are preserved
        assert restored_config.audioContext.noiseValue == audio_noise
        assert restored_config.canvas.noise == canvas_noise
        assert restored_config.webGL.noise == webgl_noise


class TestProfileDataRoundTrip:
    """Test ProfileData serialization."""
    
    @given(
        id=st.integers(min_value=1, max_value=10000),
        name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        idprofile=st.text(min_size=10, max_size=25, alphabet=st.characters(whitelist_categories=('N',))),
        status=st.sampled_from(["active", "inactive", "running", "error", "missing"])
    )
    @settings(max_examples=100)
    def test_profile_data_to_dict(self, id, name, idprofile, status):
        """Test ProfileData to_dict preserves all fields."""
        profile_data = ProfileData(
            id=id,
            name=name,
            idprofile=idprofile,
            status=status
        )
        
        result = profile_data.to_dict()
        
        assert result['id'] == id
        assert result['name'] == name
        assert result['idprofile'] == idprofile
        assert result['status'] == status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestProfileDisplayContainsRequiredFields:
    """
    **Feature: multi-profile-fingerprint-automation, Property 5: Profile Display Contains Required Fields**
    **Validates: Requirements 1.5**
    
    For any profile in the display list, the rendered output SHALL contain:
    profile ID, name, status, proxy configuration, username, and last run time.
    """
    
    @given(
        profile_id=st.text(min_size=10, max_size=20, alphabet=st.characters(whitelist_categories=('N',))),
        name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'Zs'))),
        status=st.sampled_from(["active", "inactive", "running", "error", "missing"]),
        proxy=st.text(min_size=0, max_size=50),
        username=st.text(min_size=0, max_size=30),
        last_run=st.text(min_size=0, max_size=20)
    )
    @settings(max_examples=100)
    def test_display_dict_contains_required_fields(self, profile_id, name, status, proxy, username, last_run):
        """Test that to_display_dict contains all required fields."""
        profile_data = ProfileData(
            name=name,
            idprofile=profile_id,
            status=status,
            proxy=proxy,
            username_fb=username,
            last_run=last_run
        )
        
        profile = Profile(
            data=profile_data,
            fingerprint=None,
            path=f"/test/path/{profile_id}",
            exists=True
        )
        
        display_dict = profile.to_display_dict()
        
        # Check all required fields are present
        assert 'profile_id' in display_dict
        assert 'name' in display_dict
        assert 'status' in display_dict
        assert 'proxy' in display_dict
        assert 'username' in display_dict
        assert 'last_run' in display_dict
        
        # Check values match
        assert display_dict['profile_id'] == profile_id
        assert display_dict['name'] == name
        assert display_dict['status'] == status
        assert display_dict['proxy'] == proxy
        assert display_dict['username'] == username
        assert display_dict['last_run'] == last_run
