"""
Speech-to-text module for AI Meeting Assistant.
"""
import os
import tempfile
import wave
from typing import Optional

import numpy as np
import sounddevice as sd
from pydub import AudioSegment

from agent_core.llm_manager import get_openai_manager
from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()


class SpeechToText:
    """Speech-to-text processor for the AI Meeting Assistant."""
    
    def __init__(self):
        """Initialize the speech-to-text processor."""
        self.provider = config.get('audio.stt.provider', 'openai')
        self.language = config.get('audio.stt.language', 'en-US')
        self.sample_rate = config.get('audio.stt.sample_rate', 16000)
        self.chunk_size = config.get('audio.stt.chunk_size', 1024)
        
        # Initialize OpenAI manager for Whisper API
        if self.provider == 'openai':
            self.openai_manager = get_openai_manager()
        
        logger.info(f"Initialized speech-to-text with provider {self.provider}")
    
    def transcribe_file(self, audio_file_path: str) -> str:
        """
        Transcribe an audio file.
        
        Args:
            audio_file_path: Path to the audio file.
            
        Returns:
            Transcribed text.
        """
        if self.provider == 'openai':
            return self._transcribe_with_openai(audio_file_path)
        else:
            logger.error(f"Unsupported STT provider: {self.provider}")
            return ""
    
    def _transcribe_with_openai(self, audio_file_path: str) -> str:
        """
        Transcribe an audio file using OpenAI Whisper API.
        
        Args:
            audio_file_path: Path to the audio file.
            
        Returns:
            Transcribed text.
        """
        try:
            # Convert audio to the format expected by Whisper API if needed
            file_to_transcribe = audio_file_path
            
            # Check if the file is in a supported format (mp3, mp4, mpeg, mpga, m4a, wav, webm)
            supported_formats = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
            if not any(audio_file_path.endswith(fmt) for fmt in supported_formats):
                # Convert to WAV
                audio = AudioSegment.from_file(audio_file_path)
                file_to_transcribe = tempfile.mktemp(suffix='.wav')
                audio.export(file_to_transcribe, format='wav')
                logger.info(f"Converted audio file to WAV: {file_to_transcribe}")
            
            # Transcribe with Whisper API
            transcription = self.openai_manager.transcribe_audio(
                file_to_transcribe,
                language=self.language
            )
            
            # Clean up temporary file if created
            if file_to_transcribe != audio_file_path and os.path.exists(file_to_transcribe):
                os.remove(file_to_transcribe)
            
            return transcription
        
        except Exception as e:
            logger.error(f"Error transcribing audio with OpenAI: {e}")
            return ""
    
    def start_streaming(self, callback=None):
        """
        Start streaming audio for real-time transcription.
        
        Args:
            callback: Function to call with transcribed text.
        """
        try:
            # Create a buffer to store audio data
            buffer = []
            
            # Define callback function for audio stream
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio status: {status}")
                
                # Add audio data to buffer
                buffer.append(indata.copy())
                
                # If buffer is large enough, transcribe
                if len(buffer) * self.chunk_size / self.sample_rate >= 5:  # 5 seconds of audio
                    # Concatenate buffer
                    audio_data = np.concatenate(buffer)
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                        temp_file = f.name
                    
                    with wave.open(temp_file, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(self.sample_rate)
                        wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
                    
                    # Transcribe
                    transcription = self.transcribe_file(temp_file)
                    
                    # Call callback with transcription
                    if callback and transcription:
                        callback(transcription)
                    
                    # Clear buffer
                    buffer.clear()
                    
                    # Remove temporary file
                    os.unlink(temp_file)
            
            # Start audio stream
            stream = sd.InputStream(
                callback=audio_callback,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size
            )
            
            stream.start()
            logger.info("Started audio streaming for transcription")
            
            return stream
        
        except Exception as e:
            logger.error(f"Error starting audio streaming: {e}")
            return None
    
    def stop_streaming(self, stream):
        """
        Stop streaming audio.
        
        Args:
            stream: Audio stream to stop.
        """
        if stream:
            stream.stop()
            stream.close()
            logger.info("Stopped audio streaming")
