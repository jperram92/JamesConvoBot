"""
Memory management for AI Meeting Assistant.
"""
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain.memory import ConversationBufferMemory

from utils.config import get_config
from utils.logging_utils import logger
from utils.security import get_security_manager

# Get configuration and security manager
config = get_config()
security_manager = get_security_manager()


class MeetingMemory:
    """Memory manager for meeting transcripts and conversations."""
    
    def __init__(self, meeting_id: str):
        """
        Initialize the meeting memory.
        
        Args:
            meeting_id: ID of the meeting.
        """
        self.meeting_id = meeting_id
        self.transcript: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.participants: List[str] = []
        
        # Create LangChain memory for the agent
        self.agent_memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        logger.info(f"Initialized memory for meeting {meeting_id}")
    
    def add_transcript_entry(
        self,
        speaker: str,
        text: str,
        timestamp: Optional[float] = None,
        is_assistant: bool = False
    ) -> None:
        """
        Add an entry to the transcript.
        
        Args:
            speaker: Name or ID of the speaker.
            text: Transcribed text.
            timestamp: Timestamp of the entry. If None, uses current time.
            is_assistant: Whether the entry is from the assistant.
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Filter PII if enabled
        if security_manager.pii_filtering:
            text = security_manager.filter_pii(text)
        
        # Add entry to transcript
        entry = {
            "speaker": speaker,
            "text": text,
            "timestamp": timestamp,
            "is_assistant": is_assistant
        }
        
        self.transcript.append(entry)
        
        # Add to agent memory if it's a user query or assistant response
        if is_assistant:
            self.agent_memory.chat_memory.add_ai_message(text)
        else:
            # Only add to memory if it seems like a direct query to the assistant
            trigger_word = config.get('agent.trigger_word', 'Augment').lower()
            if trigger_word.lower() in text.lower():
                self.agent_memory.chat_memory.add_user_message(text)
    
    def add_participant(self, participant_id: str) -> None:
        """
        Add a participant to the meeting.
        
        Args:
            participant_id: ID of the participant.
        """
        if participant_id not in self.participants:
            self.participants.append(participant_id)
            logger.info(f"Added participant {participant_id} to meeting {self.meeting_id}")
    
    def remove_participant(self, participant_id: str) -> None:
        """
        Remove a participant from the meeting.
        
        Args:
            participant_id: ID of the participant.
        """
        if participant_id in self.participants:
            self.participants.remove(participant_id)
            logger.info(f"Removed participant {participant_id} from meeting {self.meeting_id}")
    
    def end_meeting(self) -> None:
        """End the meeting and record the end time."""
        self.end_time = datetime.now()
        logger.info(f"Ended meeting {self.meeting_id}")
    
    def get_full_transcript(self) -> List[Dict[str, Any]]:
        """
        Get the full meeting transcript.
        
        Returns:
            List of transcript entries.
        """
        return self.transcript
    
    def get_transcript_text(self) -> str:
        """
        Get the transcript as plain text.
        
        Returns:
            Transcript as plain text.
        """
        text = ""
        for entry in self.transcript:
            timestamp = datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M:%S")
            text += f"[{timestamp}] {entry['speaker']}: {entry['text']}\n"
        
        return text
    
    def save_transcript(self, output_dir: str = "transcripts") -> str:
        """
        Save the transcript to a file.
        
        Args:
            output_dir: Directory to save the transcript.
            
        Returns:
            Path to the saved transcript file.
        """
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Create filename with meeting ID and date
        date_str = self.start_time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{output_dir}/{self.meeting_id}_{date_str}.json"
        
        # Prepare data to save
        data = {
            "meeting_id": self.meeting_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "participants": self.participants,
            "transcript": self.transcript
        }
        
        # Encrypt data if enabled
        if security_manager.encrypt_transcripts:
            encrypted_data = security_manager.encrypt_data(json.dumps(data))
            
            with open(filename, "w") as f:
                f.write(encrypted_data)
        else:
            # Save as JSON
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
        
        logger.info(f"Saved transcript to {filename}")
        return filename
    
    @staticmethod
    def load_transcript(filename: str) -> Dict[str, Any]:
        """
        Load a transcript from a file.
        
        Args:
            filename: Path to the transcript file.
            
        Returns:
            Loaded transcript data.
        """
        try:
            with open(filename, "r") as f:
                content = f.read()
            
            # Check if the content is encrypted
            try:
                # Try to parse as JSON first
                data = json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, assume it's encrypted
                decrypted = security_manager.decrypt_data(content)
                data = json.loads(decrypted)
            
            return data
        
        except Exception as e:
            logger.error(f"Error loading transcript: {e}")
            return {}
