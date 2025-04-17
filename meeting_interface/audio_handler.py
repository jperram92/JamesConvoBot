"""
Audio handling for the AI Meeting Assistant.
"""
import os
import time
import wave
from datetime import datetime
from threading import Thread

import pyaudio
import numpy as np

from utils.logging_utils import logger

class AudioHandler:
    """Handle audio recording and processing for meetings."""

    def __init__(self, output_dir="recordings", speech_recognizer=None):
        """
        Initialize the audio handler.

        Args:
            output_dir: Directory to save recordings.
            speech_recognizer: SpeechRecognizer instance for processing audio.
        """
        self.output_dir = output_dir
        self.speech_recognizer = speech_recognizer
        self.is_recording = False
        self.recording_thread = None
        self.audio = None
        self.stream = None
        self.frames = []

        # Audio parameters
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        logger.info("Initialized audio handler")

    def start_recording(self):
        """Start recording audio."""
        if self.is_recording:
            logger.warning("Already recording")
            return

        self.is_recording = True
        self.frames = []

        # Start recording in a separate thread
        self.recording_thread = Thread(target=self._record)
        self.recording_thread.daemon = True
        self.recording_thread.start()

        logger.info("Started recording")

    def stop_recording(self):
        """Stop recording audio and save to file."""
        if not self.is_recording:
            logger.warning("Not recording")
            return

        self.is_recording = False

        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join()

        # Close audio stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if self.audio:
            self.audio.terminate()

        # Save recording
        if self.frames:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"meeting_{timestamp}.wav")

            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.frames))

            logger.info(f"Saved recording to {filename}")
            return filename
        else:
            logger.warning("No audio frames to save")
            return None

    def _record(self):
        """Record audio in a loop."""
        try:
            self.audio = pyaudio.PyAudio()

            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )

            logger.info("Audio stream opened")

            # Record in chunks
            while self.is_recording:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)

                # Process audio for silence detection or other analysis
                # This could be used to detect when someone is speaking
                self._process_audio_chunk(data)

                # Send to speech recognizer if available
                if self.speech_recognizer and hasattr(self.speech_recognizer, 'process_audio_chunk'):
                    # Convert to numpy array for speech recognition
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    self.speech_recognizer.process_audio_chunk(audio_data)

            logger.info("Recording stopped")

        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            self.is_recording = False

    def _process_audio_chunk(self, data):
        """
        Process an audio chunk for analysis.

        Args:
            data: Audio data chunk.
        """
        # Convert to numpy array
        audio_data = np.frombuffer(data, dtype=np.int16)

        # Calculate volume (RMS)
        rms = np.sqrt(np.mean(np.square(audio_data)))

        # Detect if someone is speaking (simple threshold-based)
        speaking_threshold = 500  # Adjust based on testing
        is_speaking = rms > speaking_threshold

        # Log speaking detection periodically (not every chunk to avoid spam)
        if is_speaking and time.time() % 5 < 0.1:  # Log roughly every 5 seconds
            logger.debug(f"Speech detected (volume: {rms:.2f})")
