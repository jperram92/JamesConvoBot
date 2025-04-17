"""
Browser automation for Google Meet integration.
"""
import os
import time
from datetime import datetime
from typing import Optional

import undetected_chromedriver as uc
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from meeting_interface.audio_handler import AudioHandler
from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()


class BrowserAutomation:
    """Browser automation for Google Meet integration."""

    def __init__(self):
        """Initialize the browser automation."""
        self.headless = config.get('google_meet.headless', True)
        self.user_agent = config.get('google_meet.user_agent',
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.join_audio = config.get('google_meet.join_audio', True)
        self.join_video = config.get('google_meet.join_video', False)
        self.record_audio = config.get('google_meet.record_audio', True)
        self.auto_transcribe = config.get('google_meet.auto_transcribe', True)

        # Google account credentials
        self.google_email = config.get('google_meet.bot_email', '')
        self.google_password = config.get('google_meet.bot_password', '')

        # Initialize components
        self.driver = None
        self.audio_handler = AudioHandler()
        self.is_in_meeting = False
        self.meeting_start_time = None
        self.meeting_transcript = []

        logger.info("Initialized browser automation")

    def initialize_driver(self) -> None:
        """Initialize the Chrome driver."""
        try:
            # Set up Chrome options
            options = Options()

            # Use a persistent profile directory
            user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
            options.add_argument(f"--user-data-dir={user_data_dir}")

            if self.headless:
                options.add_argument('--headless')

            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--use-fake-ui-for-media-stream')  # Auto-allow camera/mic
            options.add_argument(f'--user-agent={self.user_agent}')

            # Add arguments for audio/video
            if not self.join_video:
                options.add_argument('--use-fake-device-for-media-stream')

            # Initialize driver
            self.driver = uc.Chrome(options=options)

            # Set window size
            self.driver.set_window_size(1280, 720)

            logger.info("Initialized Chrome driver with persistent profile")

        except Exception as e:
            logger.error(f"Error initializing Chrome driver: {e}")
            raise

    def join_meeting(self, meeting_url: str) -> bool:
        """
        Join a Google Meet meeting.

        Args:
            meeting_url: URL of the meeting to join.

        Returns:
            True if joined successfully, False otherwise.
        """
        if not self.driver:
            self.initialize_driver()

        try:
            # Navigate to meeting URL
            self.driver.get(meeting_url)
            logger.info(f"Navigating to meeting URL: {meeting_url}")

            # Wait for page to load
            time.sleep(5)

            # Check if we need to sign in
            if "Sign in" in self.driver.title:
                logger.error("Authentication required. Please run create_chrome_profile.py first to set up a logged-in profile.")
                return False

            # Wait for join button - try multiple possible selectors
            join_button = None
            possible_join_selectors = [
                "//span[contains(text(), 'Join now')]",
                "//span[contains(text(), 'Ask to join')]",
                "//div[contains(@role, 'button')]/span[contains(text(), 'Join')]",
                "//button[contains(., 'Join')]",
                "//button[contains(., 'Ask to join')]",
                "//div[@role='button']/span[text()='Join now']",
                "//div[@role='button']/span[text()='Ask to join']"
            ]

            for selector in possible_join_selectors:
                join_button = self._wait_for_element(selector, timeout=5)
                if join_button:
                    logger.info(f"Found join button with selector: {selector}")
                    break

            if not join_button:
                # Check if we're in the waiting room
                waiting_selectors = [
                    "//div[contains(text(), 'You can\'t join this video call')]",
                    "//div[contains(text(), 'waiting')]",
                    "//div[contains(text(), 'to admit you')]",
                    "//div[text()='Your meeting is safe']"
                ]

                waiting_text = None
                for selector in waiting_selectors:
                    waiting_text = self._wait_for_element(selector, timeout=2)
                    if waiting_text:
                        break

                if waiting_text:
                    logger.info("Bot is in the waiting room. Waiting to be admitted by the host...")
                    # Wait for up to 5 minutes to be admitted
                    for _ in range(60):  # 60 * 5 seconds = 5 minutes
                        time.sleep(5)
                        try:
                            # Check if we've been admitted
                            if "Meet" in self.driver.title and (not waiting_text.is_displayed() or "meeting" in self.driver.page_source.lower()):
                                logger.info("Bot has been admitted to the meeting")
                                return True
                        except Exception as e:
                            # If element is stale, we might have been admitted
                            if "stale element" in str(e).lower():
                                if "Meet" in self.driver.title:
                                    logger.info("Bot appears to have been admitted (stale element)")
                                    return True

                    logger.error("Timed out waiting to be admitted to the meeting")
                    return False
                else:
                    logger.error("Could not find join button or waiting room indicator")
                    return False

            # Toggle audio/video if needed
            if not self.join_audio:
                # Try different mic button selectors
                mic_selectors = [
                    "//div[contains(@aria-label, 'microphone')]",
                    "//div[contains(@aria-label, 'mic')]",
                    "//button[contains(@aria-label, 'microphone')]",
                    "//button[contains(@aria-label, 'mic')]"
                ]

                for selector in mic_selectors:
                    mic_button = self._wait_for_element(selector, timeout=2)
                    if mic_button:
                        try:
                            mic_button.click()
                            logger.info("Turned off microphone")
                            break
                        except Exception as e:
                            logger.warning(f"Failed to click mic button: {e}")

            if not self.join_video:
                # Try different camera button selectors
                camera_selectors = [
                    "//div[contains(@aria-label, 'camera')]",
                    "//div[contains(@aria-label, 'video')]",
                    "//button[contains(@aria-label, 'camera')]",
                    "//button[contains(@aria-label, 'video')]"
                ]

                for selector in camera_selectors:
                    video_button = self._wait_for_element(selector, timeout=2)
                    if video_button:
                        try:
                            video_button.click()
                            logger.info("Turned off camera")
                            break
                        except Exception as e:
                            logger.warning(f"Failed to click camera button: {e}")

            # Click join button with retry logic
            max_retries = 3
            for retry in range(max_retries):
                try:
                    # Re-find the button each time to avoid stale element
                    for selector in possible_join_selectors:
                        join_button = self._wait_for_element(selector, timeout=2)
                        if join_button:
                            join_button.click()
                            logger.info(f"Clicked join button on attempt {retry+1}")
                            # Wait to confirm we're joining
                            time.sleep(3)
                            # Success - break out of retry loop
                            break

                    # If we successfully clicked, break out of retry loop
                    if join_button:
                        break
                except Exception as e:
                    logger.warning(f"Failed to click join button on attempt {retry+1}: {e}")
                    # Wait before retrying
                    time.sleep(2)

            if retry == max_retries - 1 and not join_button:
                logger.error("Failed to click join button after multiple attempts")
                return False

            # Wait longer for meeting to load
            logger.info("Waiting for meeting to load...")
            time.sleep(10)

            # Check if we're in the meeting
            in_meeting = False

            # First check: title contains 'Meet'
            if "Meet" in self.driver.title:
                logger.info("Successfully joined meeting (detected from title)")
                in_meeting = True

            # Second check: look for meeting elements
            if not in_meeting:
                meeting_elements = [
                    "//div[contains(@aria-label, 'meeting')]",
                    "//div[contains(@aria-label, 'call')]",
                    "//button[contains(@aria-label, 'leave')]",
                    "//div[contains(@aria-label, 'chat')]",
                    "//div[contains(@aria-label, 'people')]",
                    "//div[contains(@aria-label, 'participants')]",
                    "//div[contains(@class, 'meeting')]"
                ]

                for selector in meeting_elements:
                    if self._wait_for_element(selector, timeout=2):
                        logger.info(f"Successfully joined meeting (detected meeting element: {selector})")
                        in_meeting = True
                        break

            # Third check: look for meeting-specific content in page source
            if not in_meeting and self.driver:
                page_source = self.driver.page_source.lower()
                meeting_indicators = ["meeting", "participant", "microphone", "camera", "leave call", "chat"]

                for indicator in meeting_indicators:
                    if indicator in page_source:
                        logger.info(f"Successfully joined meeting (detected keyword: {indicator})")
                        in_meeting = True
                        break

            if in_meeting:
                # Start meeting activities
                self.is_in_meeting = True
                self.meeting_start_time = datetime.now()

                # Start recording if enabled
                if self.record_audio:
                    self.audio_handler.start_recording()
                    logger.info("Started audio recording")

                # Start active participation
                self._start_meeting_participation()

                return True
            else:
                logger.error("Failed to join meeting")
                return False

        except Exception as e:
            logger.error(f"Error joining meeting: {e}")
            return False

    def leave_meeting(self) -> None:
        """Leave the current meeting."""
        if not self.driver:
            logger.warning("Driver not initialized")
            return

        try:
            # Stop recording if active
            if self.is_in_meeting and self.record_audio:
                recording_file = self.audio_handler.stop_recording()
                if recording_file:
                    logger.info(f"Saved meeting recording to {recording_file}")

                # Save transcript if available
                if self.meeting_transcript:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    transcript_file = os.path.join("recordings", f"transcript_{timestamp}.txt")
                    with open(transcript_file, "w") as f:
                        f.write("\n".join(self.meeting_transcript))
                    logger.info(f"Saved meeting transcript to {transcript_file}")

            # Reset meeting state
            self.is_in_meeting = False

            # Try different leave button selectors
            leave_selectors = [
                "//div[@aria-label='Leave call']",
                "//button[@aria-label='Leave call']",
                "//button[contains(@aria-label, 'leave')]",
                "//div[contains(@aria-label, 'leave')]",
                "//button[contains(., 'Leave')]",
                "//span[contains(text(), 'Leave')]/parent::div[@role='button']",
                "//span[contains(text(), 'Leave meeting')]/parent::div",
                "//span[contains(text(), 'Leave call')]/parent::div"
            ]

            leave_button = None
            for selector in leave_selectors:
                leave_button = self._wait_for_element(selector, timeout=2)
                if leave_button:
                    try:
                        leave_button.click()
                        logger.info(f"Left meeting using selector: {selector}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to click leave button with selector {selector}: {e}")

            if not leave_button:
                logger.warning("Could not find leave button, trying to close the window")
                # If we can't find the leave button, just close the window
                if self.driver:
                    self.driver.close()
                    logger.info("Closed browser window")

        except Exception as e:
            logger.error(f"Error leaving meeting: {e}")

        # Close browser
        self.close()

    def close(self) -> None:
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Closed browser")

    def _start_meeting_participation(self) -> None:
        """Start active participation in the meeting."""
        logger.info("Starting active meeting participation")

        # Send a greeting message in the chat
        self._send_chat_message("Hello! I'm the AI Meeting Assistant. I'm here to take notes and assist with the meeting.")

        # TODO: Start a thread for continuous monitoring and participation
        # For now, we'll just do some basic setup

        # Check if captions are available and enable them
        self._enable_captions()

    def _send_chat_message(self, message: str) -> bool:
        """Send a message in the meeting chat."""
        max_retries = 3
        for retry in range(max_retries):
            try:
                # Try different chat button selectors
                chat_button_selectors = [
                    "//div[@aria-label='Chat with everyone']",
                    "//button[@aria-label='Chat with everyone']",
                    "//button[contains(@aria-label, 'chat')]",
                    "//div[contains(@aria-label, 'chat')]",
                    "//span[contains(text(), 'Chat')]/parent::div",
                    "//div[contains(@data-tooltip, 'Chat')]",
                    "//button[contains(@data-tooltip, 'Chat')]",
                    "//div[contains(@class, 'chat')]",
                    "//button[contains(@class, 'chat')]"
                ]

                chat_button = None
                for selector in chat_button_selectors:
                    chat_button = self._wait_for_element(selector, timeout=2)
                    if chat_button:
                        try:
                            chat_button.click()
                            logger.info(f"Opened chat using selector: {selector}")
                            break
                        except Exception as e:
                            logger.warning(f"Failed to click chat button with selector {selector}: {e}")

                if not chat_button:
                    # Try clicking by JavaScript as a fallback
                    for selector in chat_button_selectors:
                        try:
                            element = self.driver.find_element(By.XPATH, selector)
                            self.driver.execute_script("arguments[0].click();", element)
                            logger.info(f"Opened chat using JavaScript click on selector: {selector}")
                            chat_button = True
                            break
                        except Exception:
                            pass

                if not chat_button:
                    logger.warning(f"Could not find chat button on attempt {retry+1}")
                    if retry < max_retries - 1:
                        time.sleep(2)
                        continue
                    return False

                # Wait for chat input field
                time.sleep(2)

                # Try different chat input selectors
                chat_input_selectors = [
                    "//textarea[@aria-label='Send a message to everyone']",
                    "//textarea[contains(@aria-label, 'message')]",
                    "//div[@role='textbox']",
                    "//textarea[contains(@placeholder, 'message')]",
                    "//textarea[contains(@placeholder, 'Send')]",
                    "//div[contains(@class, 'chat-input')]",
                    "//div[contains(@class, 'message-input')]"
                ]

                chat_input = None
                for selector in chat_input_selectors:
                    chat_input = self._wait_for_element(selector, timeout=2)
                    if chat_input:
                        break

                if not chat_input:
                    logger.warning(f"Could not find chat input field on attempt {retry+1}")
                    if retry < max_retries - 1:
                        time.sleep(2)
                        continue
                    return False

                # Clear any existing text
                chat_input.clear()

                # Type and send message
                chat_input.send_keys(message)
                time.sleep(0.5)  # Small delay to ensure text is entered
                chat_input.send_keys(Keys.ENTER)
                logger.info(f"Sent chat message: {message}")

                # Wait a moment to ensure message is sent
                time.sleep(1)

                return True

            except Exception as e:
                logger.error(f"Error sending chat message on attempt {retry+1}: {e}")
                if retry < max_retries - 1:
                    time.sleep(2)
                    continue
                return False

        return False

    def _enable_captions(self) -> bool:
        """Enable captions in the meeting."""
        max_retries = 2
        for retry in range(max_retries):
            try:
                # First try to open the more options menu if needed
                more_options_selectors = [
                    "//div[@aria-label='More options']",
                    "//button[@aria-label='More options']",
                    "//button[contains(@aria-label, 'more')]",
                    "//div[contains(@aria-label, 'more')]",
                    "//span[contains(text(), 'More')]/parent::div",
                    "//div[contains(@data-tooltip, 'More')]",
                    "//button[contains(@data-tooltip, 'More')]"
                ]

                # Try to click the more options button
                for selector in more_options_selectors:
                    more_button = self._wait_for_element(selector, timeout=2)
                    if more_button:
                        try:
                            more_button.click()
                            logger.info(f"Clicked more options button using selector: {selector}")
                            time.sleep(1)  # Wait for menu to appear
                            break
                        except Exception as e:
                            logger.warning(f"Failed to click more options button with selector {selector}: {e}")

                # Try different caption button selectors
                caption_button_selectors = [
                    "//div[@aria-label='Turn on captions']",
                    "//button[@aria-label='Turn on captions']",
                    "//button[contains(@aria-label, 'caption')]",
                    "//div[contains(@aria-label, 'caption')]",
                    "//span[contains(text(), 'Caption')]/parent::div",
                    "//div[contains(@data-tooltip, 'Caption')]",
                    "//button[contains(@data-tooltip, 'Caption')]",
                    "//div[contains(text(), 'captions')]/parent::div",
                    "//div[contains(text(), 'Captions')]/parent::div",
                    "//span[contains(text(), 'captions')]/parent::div",
                    "//span[contains(text(), 'Captions')]/parent::div"
                ]

                caption_button = None
                for selector in caption_button_selectors:
                    caption_button = self._wait_for_element(selector, timeout=2)
                    if caption_button:
                        try:
                            caption_button.click()
                            logger.info(f"Enabled captions using selector: {selector}")
                            return True
                        except Exception as e:
                            logger.warning(f"Failed to click caption button with selector {selector}: {e}")

                # Try JavaScript click as a fallback
                for selector in caption_button_selectors:
                    try:
                        element = self.driver.find_element(By.XPATH, selector)
                        self.driver.execute_script("arguments[0].click();", element)
                        logger.info(f"Enabled captions using JavaScript click on selector: {selector}")
                        return True
                    except Exception:
                        pass

                logger.warning(f"Could not find caption button on attempt {retry+1}")
                if retry < max_retries - 1:
                    time.sleep(2)
                    continue

            except Exception as e:
                logger.error(f"Error enabling captions on attempt {retry+1}: {e}")
                if retry < max_retries - 1:
                    time.sleep(2)
                    continue

        logger.warning("Could not enable captions after multiple attempts")
        return False

    def add_to_transcript(self, speaker: str, text: str) -> None:
        """Add a line to the meeting transcript."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {speaker}: {text}"
        self.meeting_transcript.append(line)
        logger.info(f"Added to transcript: {line}")

    def _wait_for_element(self, xpath: str, timeout: int = 10) -> Optional[object]:
        """
        Wait for an element to be present.

        Args:
            xpath: XPath of the element to wait for.
            timeout: Timeout in seconds.

        Returns:
            Element if found, None otherwise.
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
            logger.warning(f"Element not found: {xpath}")
            return None

    def _sign_in_to_google(self) -> bool:
        """
        Sign in to Google account.

        Returns:
            True if signed in successfully, False otherwise.
        """
        try:
            # Navigate to Google sign-in page
            self.driver.get("https://accounts.google.com/signin")
            logger.info("Navigating to Google sign-in page")

            # Wait for page to load
            time.sleep(3)

            # Enter email
            email_input = self._wait_for_element("//input[@type='email']", timeout=10)
            if not email_input:
                logger.error("Could not find email input field")
                return False

            email_input.send_keys(self.google_email)
            logger.info("Entered email")

            # Click Next
            next_button = self._wait_for_element("//button[contains(., 'Next')]", timeout=5)
            if not next_button:
                # Try alternative button
                next_button = self._wait_for_element("//div[contains(text(), 'Next')]", timeout=5)

            if not next_button:
                logger.error("Could not find Next button")
                return False

            next_button.click()
            logger.info("Clicked Next button")

            # Wait for password field
            time.sleep(3)

            # Enter password
            password_input = self._wait_for_element("//input[@type='password']", timeout=10)
            if not password_input:
                logger.error("Could not find password input field")
                return False

            password_input.send_keys(self.google_password)
            logger.info("Entered password")

            # Click Next/Sign in
            signin_button = self._wait_for_element("//button[contains(., 'Next')]", timeout=5)
            if not signin_button:
                # Try alternative button
                signin_button = self._wait_for_element("//div[contains(text(), 'Next')]", timeout=5)

            if not signin_button:
                logger.error("Could not find Sign in button")
                return False

            signin_button.click()
            logger.info("Clicked Sign in button")

            # Wait for sign-in to complete
            time.sleep(5)

            # Check if sign-in was successful
            if "myaccount.google.com" in self.driver.current_url or "accounts.google.com/signin/v2/challenge" in self.driver.current_url:
                logger.info("Successfully signed in to Google account")
                return True
            else:
                logger.error("Failed to sign in to Google account")
                return False

        except Exception as e:
            logger.error(f"Error signing in to Google account: {e}")
            return False

    def get_participants(self) -> list:
        """
        Get the list of participants in the meeting.

        Returns:
            List of participant names.
        """
        if not self.driver:
            logger.warning("Driver not initialized")
            return []

        try:
            # Try different participant button selectors
            participant_button_selectors = [
                "//div[@aria-label='Show everyone']",
                "//button[@aria-label='Show everyone']",
                "//button[contains(@aria-label, 'participant')]",
                "//div[contains(@aria-label, 'participant')]",
                "//button[contains(., 'participant')]",
                "//span[contains(text(), 'participant')]/parent::div",
                "//div[@aria-label='People']",
                "//button[@aria-label='People']",
                "//button[contains(@aria-label, 'People')]"
            ]

            participants_button = None
            for selector in participant_button_selectors:
                participants_button = self._wait_for_element(selector, timeout=2)
                if participants_button:
                    try:
                        participants_button.click()
                        logger.info(f"Clicked participants button using selector: {selector}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to click participants button with selector {selector}: {e}")

            if not participants_button:
                logger.warning("Could not find participants button")
                return []

            # Wait for participants panel
            time.sleep(2)

            # Try different participant element selectors
            participant_selectors = [
                "//div[contains(@aria-label, 'participant')]",
                "//div[contains(@role, 'listitem')]",
                "//div[contains(@class, 'participant')]",
                "//div[contains(@data-participant-id, '')]"
            ]

            participants = []
            for selector in participant_selectors:
                try:
                    participant_elements = self.driver.find_elements(By.XPATH, selector)
                    if participant_elements:
                        # Extract names
                        for element in participant_elements:
                            try:
                                # Try different ways to get the name
                                name = None
                                if element.get_attribute("aria-label"):
                                    name = element.get_attribute("aria-label").replace(" (participant)", "")
                                elif element.text:
                                    name = element.text.split('\n')[0]  # Take first line of text

                                if name and name not in participants:
                                    participants.append(name)
                            except Exception as inner_e:
                                logger.warning(f"Error extracting participant name: {inner_e}")

                        if participants:
                            logger.info(f"Found {len(participants)} participants using selector: {selector}")
                            break
                except Exception as e:
                    logger.warning(f"Error finding participants with selector {selector}: {e}")

            # Try to close participants panel
            close_selectors = [
                "//button[@aria-label='Close']",
                "//button[contains(@aria-label, 'close')]",
                "//div[contains(@aria-label, 'close')]",
                "//button[contains(., 'Close')]",
                "//span[contains(text(), 'Close')]/parent::div"
            ]

            for selector in close_selectors:
                close_button = self._wait_for_element(selector, timeout=2)
                if close_button:
                    try:
                        close_button.click()
                        logger.info(f"Closed participants panel using selector: {selector}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to close participants panel with selector {selector}: {e}")

            return participants

        except Exception as e:
            logger.error(f"Error getting participants: {e}")
            return []
