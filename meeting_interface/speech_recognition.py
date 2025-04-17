"""
Speech recognition for the AI Meeting Assistant.
"""
import os
import queue
import threading
import time
# No need for datetime import

import numpy as np
import speech_recognition as sr

# Try to import Google Cloud Speech, but make it optional
try:
    from google.cloud import speech
    GOOGLE_CLOUD_SPEECH_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_SPEECH_AVAILABLE = False

from utils.logging_utils import logger

class SpeechRecognizer:
    """Handle speech recognition for meetings."""

    def __init__(self, browser_automation=None, use_google=False):
        """
        Initialize the speech recognizer.

        Args:
            browser_automation: BrowserAutomation instance for adding to transcript.
            use_google: Whether to use Google Cloud Speech-to-Text (requires API key).
        """
        self.browser_automation = browser_automation
        self.use_google = use_google
        self.is_recognizing = False
        self.recognition_thread = None
        self.audio_queue = queue.Queue()

        # Initialize recognizer
        self.recognizer = sr.Recognizer()

        # Adjust for ambient noise
        self.recognizer.energy_threshold = 300  # Default is 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_adjustment_ratio = 1.5

        # Set up Google Cloud Speech if enabled and available
        if self.use_google:
            if not GOOGLE_CLOUD_SPEECH_AVAILABLE:
                logger.warning("Google Cloud Speech library not installed. "
                              "Using offline recognition instead.")
                self.use_google = False
            else:
                # Check for environment variable
                if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
                    logger.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable not set. "
                                "Google Cloud Speech-to-Text will not work.")
                    self.use_google = False
                else:
                    try:
                        self.google_client = speech.SpeechClient()
                        logger.info("Initialized Google Cloud Speech-to-Text client")
                    except Exception as e:
                        logger.error(f"Failed to initialize Google Cloud Speech-to-Text: {e}")
                        self.use_google = False

        logger.info("Initialized speech recognizer")

    def start_recognition(self):
        """Start speech recognition."""
        if self.is_recognizing:
            logger.warning("Already recognizing speech")
            return

        self.is_recognizing = True

        # Start recognition in a separate thread
        self.recognition_thread = threading.Thread(target=self._recognize_speech)
        self.recognition_thread.daemon = True
        self.recognition_thread.start()

        logger.info("Started speech recognition")

    def stop_recognition(self):
        """Stop speech recognition."""
        if not self.is_recognizing:
            logger.warning("Not recognizing speech")
            return

        self.is_recognizing = False

        # Wait for recognition thread to finish
        if self.recognition_thread:
            self.recognition_thread.join(timeout=2)

        logger.info("Stopped speech recognition")

    def process_audio_chunk(self, audio_data):
        """
        Process an audio chunk for speech recognition.

        Args:
            audio_data: Audio data as numpy array.
        """
        if not self.is_recognizing:
            return

        # Add audio data to queue
        self.audio_queue.put(audio_data)

    def _recognize_speech(self):
        """Recognize speech from audio chunks."""
        # Buffer for accumulating audio data
        audio_buffer = []
        last_process_time = time.time()

        try:
            while self.is_recognizing:
                # Get audio data from queue (non-blocking)
                try:
                    audio_data = self.audio_queue.get(block=False)
                    audio_buffer.append(audio_data)
                except queue.Empty:
                    # No new audio data, sleep briefly
                    time.sleep(0.1)

                # Process accumulated audio every 3 seconds
                current_time = time.time()
                if current_time - last_process_time >= 3 and audio_buffer:
                    # Combine audio chunks
                    combined_audio = np.concatenate(audio_buffer)

                    # Convert to audio data format for speech_recognition
                    audio = sr.AudioData(
                        combined_audio.tobytes(),
                        sample_rate=16000,
                        sample_width=2  # 16-bit audio
                    )

                    # Recognize speech
                    text = self._recognize_audio(audio)

                    if text:
                        # Add to transcript
                        if self.browser_automation:
                            # Try to get the current speaker from the browser
                            speaker = "Unknown Speaker"
                            self.browser_automation.add_to_transcript(speaker, text)

                        logger.info(f"Transcribed: {text}")

                    # Reset buffer and timer
                    audio_buffer = []
                    last_process_time = current_time

        except Exception as e:
            logger.error(f"Error in speech recognition thread: {e}")
            self.is_recognizing = False

    def _recognize_audio(self, audio):
        """
        Recognize speech from audio data.

        Args:
            audio: AudioData object from speech_recognition.

        Returns:
            Recognized text or None if no speech detected.
        """
        try:
            if self.use_google and GOOGLE_CLOUD_SPEECH_AVAILABLE:
                # Use Google Cloud Speech-to-Text
                audio_content = audio.get_raw_data()

                audio_config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="en-US",
                    enable_automatic_punctuation=True,
                    model="default"
                )

                response = self.google_client.recognize(
                    config=audio_config,
                    audio=speech.RecognitionAudio(content=audio_content)
                )

                if response.results:
                    return response.results[0].alternatives[0].transcript
                return None
            else:
                # Use offline recognizer (CMU Sphinx)
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    return text
                except AttributeError:
                    logger.warning("Sphinx recognizer not available. Make sure pocketsphinx is installed.")
                    return None

        except sr.UnknownValueError:
            # Speech was unintelligible
            return None
        except sr.RequestError as e:
            logger.error(f"Recognition error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error recognizing speech: {e}")
            return None
