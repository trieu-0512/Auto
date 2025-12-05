# Property-based tests for Fingerprint Generator
# Feature: multi-profile-fingerprint-automation

import pytest
from hypothesis import given, strategies as st, settings

from app.core.fingerprint_generator import FingerprintGenerator
from app.data.profile_models import GologinConfig


@pytest.fixture
def generator():
    """Create a FingerprintGenerator instance."""
    return FingerprintGenerator()


class TestNoiseValuesWithinValidRanges:
    """
    **Feature: multi-profile-fingerprint-automation, Property 8: Noise Values Within Valid Ranges**
    **Validates: Requirements 2.3**
    
    For any generated fingerprint, audioContext.noiseValue SHALL be in [1e-8, 1e-7],
    canvas.noise in [1.0, 10.0], clientRects.noise in [1, 10], and webGL.noise in [1.0, 100.0].
    """
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_audio_noise_in_range(self, _):
        """Test that audio noise is within valid range."""
        gen = FingerprintGenerator()
        config = gen.generate_fingerprint()
        
        assert gen.AUDIO_NOISE_RANGE[0] <= config.audioContext.noiseValue <= gen.AUDIO_NOISE_RANGE[1]
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_canvas_noise_in_range(self, _):
        """Test that canvas noise is within valid range."""
        gen = FingerprintGenerator()
        config = gen.generate_fingerprint()
        
        assert gen.CANVAS_NOISE_RANGE[0] <= config.canvas.noise <= gen.CANVAS_NOISE_RANGE[1]
        assert gen.CANVAS_NOISE_RANGE[0] <= config.canvasNoise <= gen.CANVAS_NOISE_RANGE[1]
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_client_rects_noise_in_range(self, _):
        """Test that client rects noise is within valid range."""
        gen = FingerprintGenerator()
        config = gen.generate_fingerprint()
        
        assert gen.CLIENT_RECTS_NOISE_RANGE[0] <= config.clientRects.noise <= gen.CLIENT_RECTS_NOISE_RANGE[1]
        assert gen.CLIENT_RECTS_NOISE_RANGE[0] <= config.getClientRectsNoice <= gen.CLIENT_RECTS_NOISE_RANGE[1]
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_webgl_noise_in_range(self, _):
        """Test that WebGL noise is within valid range."""
        gen = FingerprintGenerator()
        config = gen.generate_fingerprint()
        
        assert gen.WEBGL_NOISE_RANGE[0] <= config.webGL.noise <= gen.WEBGL_NOISE_RANGE[1]
        assert gen.WEBGL_NOISE_RANGE[0] <= config.webglNoiseValue <= gen.WEBGL_NOISE_RANGE[1]
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_all_noise_values_in_range(self, _):
        """Test that all noise values are within valid ranges in a single fingerprint."""
        gen = FingerprintGenerator()
        config = gen.generate_fingerprint()
        
        # Audio
        assert gen.is_noise_in_range('audio', config.audioContext.noiseValue)
        
        # Canvas
        assert gen.is_noise_in_range('canvas', config.canvas.noise)
        
        # Client rects
        assert gen.is_noise_in_range('client_rects', config.clientRects.noise)
        
        # WebGL
        assert gen.is_noise_in_range('webgl', config.webGL.noise)


class TestGPUConfigurationFromValidList:
    """
    **Feature: multi-profile-fingerprint-automation, Property 9: GPU Configuration From Valid List**
    **Validates: Requirements 2.4**
    
    For any generated fingerprint, the webGLMetadata (renderer, vendor) combination
    SHALL be from the predefined list of valid GPU configurations.
    """
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_gpu_config_from_valid_list(self, _):
        """Test that GPU config is from the predefined list."""
        gen = FingerprintGenerator()
        config = gen.generate_fingerprint()
        
        # Check that the GPU config is valid
        assert gen.is_gpu_config_valid(
            config.webGLMetadata.renderer,
            config.webGLMetadata.vendor
        )
    
    @given(st.integers(min_value=1, max_value=50))
    @settings(max_examples=50)
    def test_randomize_preserves_valid_gpu(self, _):
        """Test that randomizing noise values produces valid GPU config."""
        gen = FingerprintGenerator()
        
        # Create initial config
        config = GologinConfig()
        
        # Randomize
        config = gen.randomize_noise_values(config)
        
        # Check GPU config is valid
        assert gen.is_gpu_config_valid(
            config.webGLMetadata.renderer,
            config.webGLMetadata.vendor
        )


class TestFingerprintGeneration:
    """Test general fingerprint generation."""
    
    def test_generate_fingerprint_creates_valid_config(self, generator):
        """Test that generate_fingerprint creates a valid config."""
        config = generator.generate_fingerprint()
        
        assert isinstance(config, GologinConfig)
        assert config.audioContext.enable is True
        assert config.canvas.mode == "noise"
        assert config.webGL.mode == "noise"
        assert config.webGLMetadata.mode == "mask"
    
    def test_generate_fingerprint_unique_values(self, generator):
        """Test that multiple generations produce different values."""
        configs = [generator.generate_fingerprint() for _ in range(10)]
        
        # Check that not all audio noise values are the same
        audio_noises = [c.audioContext.noiseValue for c in configs]
        assert len(set(audio_noises)) > 1
        
        # Check that not all canvas noise values are the same
        canvas_noises = [c.canvas.noise for c in configs]
        assert len(set(canvas_noises)) > 1
    
    def test_randomize_changes_values(self, generator):
        """Test that randomize_noise_values changes the values."""
        config = GologinConfig()
        original_audio = config.audioContext.noiseValue
        original_canvas = config.canvas.noise
        
        # Randomize
        config = generator.randomize_noise_values(config)
        
        # At least one value should change (with high probability)
        # Since original values are 0.0, any random value will be different
        assert config.audioContext.noiseValue != original_audio or \
               config.canvas.noise != original_canvas


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
