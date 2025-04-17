"""
Google Meet client for AI Meeting Assistant.
"""
import threading
import time
import uuid
from typing import Callable, List, Optional

from agent_core.agent import MeetingAgent
from audio_streaming.audio_processor import AudioProcessor
from meeting_interface.audio_routing import AudioRouting
from meeting_interface.browser_automation import BrowserAutomation
from utils.config import get_config
from utils.logging_utils import logger
from utils.security import get_security_manager

# Get configuration and security manager
config = get_config()
security_manager = get_security_manager()


class MeetClient:
    """Google Meet client for AI Meeting Assistant."""
    
    def __init__(self):
        """Initialize the Google Meet client."""
        self.browser = BrowserAutomation()
        self.audio_routing = AudioRouting()
        self.audio_processor = AudioProcessor()
        self.meeting_id = None
        self.agent = None
        self.is_running = False
        self.thread = None
        
        logger.info("Initialized Google Meet client")
    
    def join_meeting(self, meeting_url: str) -> bool:
        """
        Join a Google Meet meeting.
        
        Args:
            meeting_url: URL of the meeting to join.
            
        Returns:
            True if joined successfully, False otherwise.
        """
        try:
            # Generate meeting ID
            self.meeting_id = str(uuid.uuid4())
            
            # Initialize agent
            self.agent = MeetingAgent(self.meeting_id)
            
            # Set up audio routing
            if not self.audio_routing.setup_virtual_devices():
                logger.error("Failed to set up virtual audio devices")
                return False
            
            # Join meeting
            if not self.browser.join_meeting(meeting_url):
                logger.error("Failed to join meeting")
                self.audio_routing.cleanup_virtual_devices()
                return False
            
            # Get participants
            participants = self.browser.get_participants()
            logger.info(f"Participants: {participants}")
            
            # Add participants to agent memory
            for participant in participants:
                self.agent.memory.add_participant(participant)
            
            # Start audio processing
            self.audio_processor.start_processing(self._handle_transcript)
            
            # Start meeting thread
            self.is_running = True
            self.thread = threading.Thread(target=self._meeting_loop)
            self.thread.daemon = True
            self.thread.start()
            
            logger.info(f"Joined meeting: {meeting_url}")
            return True
        
        except Exception as e:
            logger.error(f"Error joining meeting: {e}")
            self.leave_meeting()
            return False
    
    def leave_meeting(self) -> None:
        """Leave the current meeting."""
        self.is_running = False
        
        if self.thread:
            self.thread.join(timeout=5.0)
        
        if self.audio_processor:
            self.audio_processor.stop_processing()
        
        if self.browser:
            self.browser.leave_meeting()
        
        if self.audio_routing:
            self.audio_routing.cleanup_virtual_devices()
        
        if self.agent and self.agent.memory:
            self.agent.memory.end_meeting()
            self.agent.memory.save_transcript()
        
        logger.info("Left meeting")
    
    def send_summary_email(self, recipients: List[str]) -> str:
        """
        Send a summary email to the specified recipients.
        
        Args:
            recipients: List of email recipients.
            
        Returns:
            Status message.
        """
        if not self.agent:
            return "No active meeting agent"
        
        return self.agent.send_summary_email(recipients)
    
    def _meeting_loop(self) -> None:
        """Main meeting loop."""
        check_interval = 10  # seconds
        
        while self.is_running:
            try:
                # Check if we're still in the meeting
                if not self._is_in_meeting():
                    logger.info("No longer in meeting")
                    self.is_running = False
                    break
                
                # Update participants
                participants = self.browser.get_participants()
                
                # Update agent memory
                current_participants = set(self.agent.memory.participants)
                new_participants = set(participants)
                
                # Add new participants
                for participant in new_participants - current_participants:
                    self.agent.memory.add_participant(participant)
                
                # Remove participants who left
                for participant in current_participants - new_participants:
                    self.agent.memory.remove_participant(participant)
                
                # Sleep for a bit
                time.sleep(check_interval)
            
            except Exception as e:
                logger.error(f"Error in meeting loop: {e}")
                time.sleep(check_interval)
    
    def _is_in_meeting(self) -> bool:
        """
        Check if we're still in the meeting.
        
        Returns:
            True if in meeting, False otherwise.
        """
        if not self.browser or not self.browser.driver:
            return False
        
        try:
            # Check if we're still on the Meet page
            return "Meet" in self.browser.driver.title
        except:
            return False
    
    def _handle_transcript(self, speaker: str, text: str) -> None:
        """
        Handle transcribed text.
        
        Args:
            speaker: Name or ID of the speaker.
            text: Transcribed text.
        """
        if not self.agent:
            return
        
        # Process transcript with agent
        response = self.agent.process_transcript(speaker, text)
        
        # Speak response if there is one
        if response:
            self.audio_processor.speak(response)
