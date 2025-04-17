"""
Audio processor for AI Meeting Assistant.
"""
import os
import queue
import tempfile
import threading
import time
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
from pydub import AudioSegment

from audio_streaming.speech_to_text import SpeechToText
from audio_streaming.text_to_speech import TextToSpeech
from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()


class AudioProcessor:
    """Audio processor for the AI Meeting Assistant."""
    
    def __init__(self):
        """Initialize the audio processor."""
        self.sample_rate = config.get('audio.stt.sample_rate', 16000)
        self.chunk_size = config.get('audio.stt.chunk_size', 1024)
        
        # Initialize STT and TTS
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        
        # Create audio queues
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        # Create flags for controlling audio processing
        self.is_processing = False
        self.is_speaking = False
        
        # Create locks
        self.speaking_lock = threading.Lock()
        
        logger.info("Initialized audio processor")
    
    def start_processing(self, transcript_callback: Optional[Callable[[str, str], None]] = None) -> None:
        """
        Start processing audio.
        
        Args:
            transcript_callback: Function to call with transcribed text.
        """
        if self.is_processing:
            logger.warning("Audio processing already started")
            return
        
        self.is_processing = True
        
        # Start input stream
        self.input_stream = sd.InputStream(
            callback=self._input_callback,
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.chunk_size
        )
        
        # Start output stream
        self.output_stream = sd.OutputStream(
            callback=self._output_callback,
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.chunk_size
        )
        
        # Start streams
        self.input_stream.start()
        self.output_stream.start()
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._process_audio,
            args=(transcript_callback,),
            daemon=True
        )
        self.processing_thread.start()
        
        logger.info("Started audio processing")
    
    def stop_processing(self) -> None:
        """Stop processing audio."""
        if not self.is_processing:
            logger.warning("Audio processing not started")
            return
        
        self.is_processing = False
        
        # Stop streams
        self.input_stream.stop()
        self.input_stream.close()
        self.output_stream.stop()
        self.output_stream.close()
        
        # Wait for processing thread to finish
        self.processing_thread.join(timeout=2.0)
        
        logger.info("Stopped audio processing")
    
    def speak(self, text: str) -> None:
        """
        Speak text using text-to-speech.
        
        Args:
            text: Text to speak.
        """
        try:
            # Acquire speaking lock
            with self.speaking_lock:
                self.is_speaking = True
                
                # Synthesize speech
                audio_file = self.tts.synthesize_speech(text)
                
                if not audio_file:
                    logger.error("Failed to synthesize speech")
                    self.is_speaking = False
                    return
                
                # Load audio file
                audio = AudioSegment.from_file(audio_file)
                
                # Convert to numpy array
                samples = np.array(audio.get_array_of_samples())
                
                # Normalize to float32
                samples = samples.astype(np.float32) / 32767.0
                
                # Add to output queue in chunks
                for i in range(0, len(samples), self.chunk_size):
                    chunk = samples[i:i+self.chunk_size]
                    
                    # Pad chunk if needed
                    if len(chunk) < self.chunk_size:
                        chunk = np.pad(chunk, (0, self.chunk_size - len(chunk)))
                    
                    self.output_queue.put(chunk)
                
                # Remove temporary file
                os.unlink(audio_file)
                
                # Wait for queue to empty
                while not self.output_queue.empty() and self.is_processing:
                    time.sleep(0.1)
                
                self.is_speaking = False
        
        except Exception as e:
            logger.error(f"Error speaking text: {e}")
            self.is_speaking = False
    
    def _input_callback(self, indata, frames, time, status):
        """
        Callback for input stream.
        
        Args:
            indata: Input audio data.
            frames: Number of frames.
            time: Stream time.
            status: Stream status.
        """
        if status:
            logger.warning(f"Input stream status: {status}")
        
        # Add input data to queue
        self.input_queue.put(indata.copy())
    
    def _output_callback(self, outdata, frames, time, status):
        """
        Callback for output stream.
        
        Args:
            outdata: Output audio data.
            frames: Number of frames.
            time: Stream time.
            status: Stream status.
        """
        if status:
            logger.warning(f"Output stream status: {status}")
        
        # Get output data from queue
        try:
            data = self.output_queue.get_nowait()
            outdata[:] = data.reshape(-1, 1)
        except queue.Empty:
            outdata[:] = np.zeros((frames, 1), dtype=np.float32)
    
    def _process_audio(self, transcript_callback: Optional[Callable[[str, str], None]] = None) -> None:
        """
        Process audio for transcription.
        
        Args:
            transcript_callback: Function to call with transcribed text.
        """
        buffer = []
        silence_threshold = 0.01
        silence_frames = 0
        is_speaking = False
        
        while self.is_processing:
            try:
                # Get input data from queue
                data = self.input_queue.get(timeout=1.0)
                
                # Skip if we're currently speaking
                if self.is_speaking:
                    continue
                
                # Check if audio contains speech
                if np.max(np.abs(data)) > silence_threshold:
                    silence_frames = 0
                    is_speaking = True
                else:
                    silence_frames += 1
                
                # Add data to buffer if speaking
                if is_speaking:
                    buffer.append(data)
                
                # Process buffer if silence detected after speech
                if is_speaking and silence_frames > 10:  # About 0.5 seconds of silence
                    is_speaking = False
                    
                    # Skip if buffer is too small
                    if len(buffer) < 5:  # Less than 0.25 seconds
                        buffer = []
                        continue
                    
                    # Concatenate buffer
                    audio_data = np.concatenate(buffer)
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                        temp_file = f.name
                    
                    # Convert to int16 and save
                    with open(temp_file, 'wb') as f:
                        AudioSegment(
                            data=(audio_data * 32767).astype(np.int16).tobytes(),
                            sample_width=2,
                            frame_rate=self.sample_rate,
                            channels=1
                        ).export(f, format='wav')
                    
                    # Transcribe
                    transcription = self.stt.transcribe_file(temp_file)
                    
                    # Call callback with transcription
                    if transcript_callback and transcription:
                        transcript_callback("user", transcription)
                    
                    # Clear buffer
                    buffer = []
                    
                    # Remove temporary file
                    os.unlink(temp_file)
            
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                buffer = []
