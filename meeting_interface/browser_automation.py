"""
Browser automation for Google Meet integration.
"""
import os
import time
from typing import Optional

import undetected_chromedriver as uc
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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
        
        self.driver = None
        
        logger.info("Initialized browser automation")
    
    def initialize_driver(self) -> None:
        """Initialize the Chrome driver."""
        try:
            # Set up Chrome options
            options = Options()
            
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
            
            logger.info("Initialized Chrome driver")
        
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
                logger.error("Authentication required. Please sign in manually or use authenticated cookies.")
                return False
            
            # Wait for join button
            join_button = self._wait_for_element("//span[contains(text(), 'Join now')]", timeout=30)
            
            if not join_button:
                # Try alternative button
                join_button = self._wait_for_element("//span[contains(text(), 'Ask to join')]", timeout=10)
            
            if not join_button:
                logger.error("Could not find join button")
                return False
            
            # Toggle audio/video if needed
            if not self.join_audio:
                mic_button = self._wait_for_element("//div[@aria-label='Turn off microphone (⌘+d)']", timeout=5)
                if mic_button:
                    mic_button.click()
                    logger.info("Turned off microphone")
            
            if not self.join_video:
                video_button = self._wait_for_element("//div[@aria-label='Turn off camera (⌘+e)']", timeout=5)
                if video_button:
                    video_button.click()
                    logger.info("Turned off camera")
            
            # Click join button
            join_button.click()
            logger.info("Clicked join button")
            
            # Wait for meeting to load
            time.sleep(5)
            
            # Check if we're in the meeting
            if "Meet" in self.driver.title:
                logger.info("Successfully joined meeting")
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
            # Find and click leave button
            leave_button = self._wait_for_element("//div[@aria-label='Leave call']", timeout=5)
            
            if leave_button:
                leave_button.click()
                logger.info("Left meeting")
            else:
                logger.warning("Could not find leave button")
        
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
            # Click participants button
            participants_button = self._wait_for_element("//div[@aria-label='Show everyone']", timeout=5)
            
            if not participants_button:
                logger.warning("Could not find participants button")
                return []
            
            participants_button.click()
            logger.info("Clicked participants button")
            
            # Wait for participants panel
            time.sleep(2)
            
            # Get participant elements
            participant_elements = self.driver.find_elements(By.XPATH, "//div[contains(@aria-label, 'participant')]")
            
            # Extract names
            participants = []
            for element in participant_elements:
                try:
                    name = element.get_attribute("aria-label").replace(" (participant)", "")
                    participants.append(name)
                except:
                    pass
            
            # Close participants panel
            close_button = self._wait_for_element("//button[@aria-label='Close']", timeout=5)
            if close_button:
                close_button.click()
            
            return participants
        
        except Exception as e:
            logger.error(f"Error getting participants: {e}")
            return []
