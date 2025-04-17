"""
Audio routing for Google Meet integration.
"""
import os
import subprocess
import time
from typing import Optional, Tuple

from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()


class AudioRouting:
    """Audio routing for Google Meet integration using PulseAudio."""
    
    def __init__(self):
        """Initialize the audio routing."""
        self.virtual_mic_name = "virtual-mic"
        self.virtual_speaker_name = "virtual-speaker"
        self.virtual_mic_device = None
        self.virtual_speaker_device = None
        self.loopback_module = None
        
        logger.info("Initialized audio routing")
    
    def setup_virtual_devices(self) -> bool:
        """
        Set up virtual audio devices.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Check if PulseAudio is available
            if not self._is_pulseaudio_available():
                logger.error("PulseAudio is not available")
                return False
            
            # Create virtual microphone
            result = subprocess.run(
                ["pactl", "load-module", "module-null-sink", f"sink_name={self.virtual_mic_name}", f"sink_properties=device.description={self.virtual_mic_name}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Error creating virtual microphone: {result.stderr}")
                return False
            
            self.virtual_mic_device = result.stdout.strip()
            logger.info(f"Created virtual microphone: {self.virtual_mic_device}")
            
            # Create virtual speaker
            result = subprocess.run(
                ["pactl", "load-module", "module-null-sink", f"sink_name={self.virtual_speaker_name}", f"sink_properties=device.description={self.virtual_speaker_name}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Error creating virtual speaker: {result.stderr}")
                return False
            
            self.virtual_speaker_device = result.stdout.strip()
            logger.info(f"Created virtual speaker: {self.virtual_speaker_device}")
            
            # Create loopback from virtual microphone to default source
            result = subprocess.run(
                ["pactl", "load-module", "module-loopback", f"source={self.virtual_mic_name}.monitor", "sink=@DEFAULT_SINK@"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Error creating loopback: {result.stderr}")
                return False
            
            self.loopback_module = result.stdout.strip()
            logger.info(f"Created loopback: {self.loopback_module}")
            
            # Set default source to virtual microphone
            result = subprocess.run(
                ["pactl", "set-default-source", f"{self.virtual_mic_name}.monitor"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Error setting default source: {result.stderr}")
                return False
            
            logger.info("Set default source to virtual microphone")
            
            return True
        
        except Exception as e:
            logger.error(f"Error setting up virtual devices: {e}")
            return False
    
    def cleanup_virtual_devices(self) -> None:
        """Clean up virtual audio devices."""
        try:
            # Unload loopback module
            if self.loopback_module:
                subprocess.run(
                    ["pactl", "unload-module", self.loopback_module],
                    capture_output=True,
                    text=True
                )
                logger.info(f"Unloaded loopback module: {self.loopback_module}")
            
            # Unload virtual microphone
            if self.virtual_mic_device:
                subprocess.run(
                    ["pactl", "unload-module", self.virtual_mic_device],
                    capture_output=True,
                    text=True
                )
                logger.info(f"Unloaded virtual microphone: {self.virtual_mic_device}")
            
            # Unload virtual speaker
            if self.virtual_speaker_device:
                subprocess.run(
                    ["pactl", "unload-module", self.virtual_speaker_device],
                    capture_output=True,
                    text=True
                )
                logger.info(f"Unloaded virtual speaker: {self.virtual_speaker_device}")
        
        except Exception as e:
            logger.error(f"Error cleaning up virtual devices: {e}")
    
    def get_virtual_device_names(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Get the names of the virtual devices.
        
        Returns:
            Tuple of (virtual microphone name, virtual speaker name).
        """
        return (
            f"{self.virtual_mic_name}.monitor" if self.virtual_mic_device else None,
            self.virtual_speaker_name if self.virtual_speaker_device else None
        )
    
    def _is_pulseaudio_available(self) -> bool:
        """
        Check if PulseAudio is available.
        
        Returns:
            True if available, False otherwise.
        """
        try:
            result = subprocess.run(
                ["pactl", "info"],
                capture_output=True,
                text=True
            )
            
            return result.returncode == 0
        
        except Exception:
            return False
    
    def play_to_virtual_mic(self, audio_data: bytes) -> bool:
        """
        Play audio data to the virtual microphone.
        
        Args:
            audio_data: Audio data to play.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.virtual_mic_device:
            logger.error("Virtual microphone not set up")
            return False
        
        try:
            # Create temporary file
            temp_file = "/tmp/virtual_mic_audio.wav"
            
            # Write audio data to file
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            
            # Play audio to virtual microphone
            result = subprocess.run(
                ["paplay", "--device", f"{self.virtual_mic_name}", temp_file],
                capture_output=True,
                text=True
            )
            
            # Remove temporary file
            os.unlink(temp_file)
            
            if result.returncode != 0:
                logger.error(f"Error playing audio to virtual microphone: {result.stderr}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error playing audio to virtual microphone: {e}")
            return False
    
    def record_from_virtual_speaker(self, duration: float = 5.0) -> Optional[bytes]:
        """
        Record audio from the virtual speaker.
        
        Args:
            duration: Duration to record in seconds.
            
        Returns:
            Recorded audio data, or None if failed.
        """
        if not self.virtual_speaker_device:
            logger.error("Virtual speaker not set up")
            return None
        
        try:
            # Create temporary file
            temp_file = "/tmp/virtual_speaker_audio.wav"
            
            # Record audio from virtual speaker
            result = subprocess.run(
                ["parec", "--device", f"{self.virtual_speaker_name}.monitor", "--file-format=wav", temp_file],
                capture_output=True,
                text=True,
                timeout=duration
            )
            
            if result.returncode != 0:
                logger.error(f"Error recording from virtual speaker: {result.stderr}")
                return None
            
            # Read audio data from file
            with open(temp_file, "rb") as f:
                audio_data = f.read()
            
            # Remove temporary file
            os.unlink(temp_file)
            
            return audio_data
        
        except Exception as e:
            logger.error(f"Error recording from virtual speaker: {e}")
            return None
