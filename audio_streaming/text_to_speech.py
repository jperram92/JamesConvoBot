"""
Text-to-speech module for AI Meeting Assistant.
"""
import os
import tempfile
from typing import Optional

import boto3
import sounddevice as sd
from gtts import gTTS
from pydub import AudioSegment

from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()


class TextToSpeech:
    """Text-to-speech processor for the AI Meeting Assistant."""
    
    def __init__(self):
        """Initialize the text-to-speech processor."""
        self.provider = config.get('audio.tts.provider', 'google')
        self.voice = config.get('audio.tts.voice', 'en-US-Neural2-F')
        self.speaking_rate = config.get('audio.tts.speaking_rate', 1.0)
        self.pitch = config.get('audio.tts.pitch', 0.0)
        
        # Initialize AWS Polly client if using AWS
        if self.provider == 'aws':
            self.polly_client = boto3.client(
                'polly',
                aws_access_key_id=config.get_nested_value(['api_keys', 'aws', 'access_key_id']),
                aws_secret_access_key=config.get_nested_value(['api_keys', 'aws', 'secret_access_key']),
                region_name=config.get_nested_value(['api_keys', 'aws', 'region'], 'us-east-1')
            )
        
        logger.info(f"Initialized text-to-speech with provider {self.provider}")
    
    def synthesize_speech(self, text: str, output_file: Optional[str] = None) -> str:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize.
            output_file: Path to save the audio file. If None, a temporary file is created.
            
        Returns:
            Path to the audio file.
        """
        if not output_file:
            output_file = tempfile.mktemp(suffix='.mp3')
        
        if self.provider == 'google':
            return self._synthesize_with_google(text, output_file)
        elif self.provider == 'aws':
            return self._synthesize_with_aws(text, output_file)
        else:
            logger.error(f"Unsupported TTS provider: {self.provider}")
            return ""
    
    def _synthesize_with_google(self, text: str, output_file: str) -> str:
        """
        Synthesize speech using Google Text-to-Speech.
        
        Args:
            text: Text to synthesize.
            output_file: Path to save the audio file.
            
        Returns:
            Path to the audio file.
        """
        try:
            # Create gTTS object
            tts = gTTS(text=text, lang=self.voice[:5])
            
            # Save to file
            tts.save(output_file)
            
            return output_file
        
        except Exception as e:
            logger.error(f"Error synthesizing speech with Google: {e}")
            return ""
    
    def _synthesize_with_aws(self, text: str, output_file: str) -> str:
        """
        Synthesize speech using AWS Polly.
        
        Args:
            text: Text to synthesize.
            output_file: Path to save the audio file.
            
        Returns:
            Path to the audio file.
        """
        try:
            # Synthesize speech
            response = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=self.voice,
                Engine='neural'
            )
            
            # Save to file
            with open(output_file, 'wb') as f:
                f.write(response['AudioStream'].read())
            
            return output_file
        
        except Exception as e:
            logger.error(f"Error synthesizing speech with AWS: {e}")
            return ""
    
    def speak(self, text: str) -> None:
        """
        Speak text using text-to-speech.
        
        Args:
            text: Text to speak.
        """
        try:
            # Synthesize speech
            audio_file = self.synthesize_speech(text)
            
            if not audio_file:
                logger.error("Failed to synthesize speech")
                return
            
            # Load audio file
            audio = AudioSegment.from_file(audio_file)
            
            # Convert to numpy array
            samples = np.array(audio.get_array_of_samples())
            
            # Play audio
            sd.play(samples, audio.frame_rate)
            sd.wait()
            
            # Remove temporary file
            os.unlink(audio_file)
        
        except Exception as e:
            logger.error(f"Error speaking text: {e}")


# Add missing import
import numpy as np
