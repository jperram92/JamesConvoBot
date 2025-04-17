"""
Transcript processor for AI Meeting Assistant.
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from utils.config import get_config
from utils.logging_utils import logger
from utils.security import get_security_manager

# Get configuration and security manager
config = get_config()
security_manager = get_security_manager()


class TranscriptProcessor:
    """Processor for meeting transcripts."""
    
    def __init__(self):
        """Initialize the transcript processor."""
        self.include_timestamps = config.get('summarization.include_timestamps', True)
        self.max_chunk_size = config.get('summarization.max_chunk_size', 4000)
        
        logger.info("Initialized transcript processor")
    
    def process_transcript(self, transcript: List[Dict[str, Any]]) -> str:
        """
        Process a transcript into a formatted text.
        
        Args:
            transcript: List of transcript entries.
            
        Returns:
            Formatted transcript text.
        """
        text = ""
        
        for entry in transcript:
            # Format timestamp
            if self.include_timestamps and "timestamp" in entry:
                timestamp = datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M:%S")
                text += f"[{timestamp}] "
            
            # Add speaker and text
            text += f"{entry['speaker']}: {entry['text']}\n"
        
        return text
    
    def chunk_transcript(self, transcript: List[Dict[str, Any]]) -> List[str]:
        """
        Chunk a transcript into smaller pieces for processing.
        
        Args:
            transcript: List of transcript entries.
            
        Returns:
            List of transcript chunks.
        """
        # Process transcript into text
        full_text = self.process_transcript(transcript)
        
        # Split into chunks
        chunks = []
        current_chunk = ""
        
        for line in full_text.split("\n"):
            # If adding this line would exceed the chunk size, start a new chunk
            if len(current_chunk) + len(line) + 1 > self.max_chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                if current_chunk:
                    current_chunk += "\n"
                current_chunk += line
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def extract_speakers(self, transcript: List[Dict[str, Any]]) -> List[str]:
        """
        Extract unique speakers from a transcript.
        
        Args:
            transcript: List of transcript entries.
            
        Returns:
            List of unique speaker names.
        """
        speakers = set()
        
        for entry in transcript:
            if "speaker" in entry:
                speakers.add(entry["speaker"])
        
        return list(speakers)
    
    def extract_topics(self, transcript_text: str) -> List[str]:
        """
        Extract potential topics from a transcript.
        
        Args:
            transcript_text: Transcript text.
            
        Returns:
            List of potential topics.
        """
        # This is a simple implementation that looks for capitalized phrases
        # In a real implementation, you would use NLP techniques
        
        # Find capitalized phrases (potential topics)
        topic_pattern = r'\b[A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)*\b'
        potential_topics = re.findall(topic_pattern, transcript_text)
        
        # Filter out common non-topics (names, etc.)
        common_non_topics = {"I", "You", "He", "She", "They", "We", "It", "My", "Your", "His", "Her", "Their", "Our"}
        
        filtered_topics = [topic for topic in potential_topics if topic not in common_non_topics]
        
        # Count occurrences and keep only those mentioned multiple times
        topic_counts = {}
        for topic in filtered_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Return topics mentioned at least twice
        return [topic for topic, count in topic_counts.items() if count >= 2]
    
    def extract_action_items(self, transcript_text: str) -> List[Dict[str, str]]:
        """
        Extract potential action items from a transcript.
        
        Args:
            transcript_text: Transcript text.
            
        Returns:
            List of potential action items with assignees.
        """
        # This is a simple implementation that looks for phrases like "X will do Y"
        # In a real implementation, you would use NLP techniques
        
        action_items = []
        
        # Look for phrases like "X will do Y" or "X needs to do Y"
        patterns = [
            r'([A-Za-z]+) will ([^\.]+)',
            r'([A-Za-z]+) needs to ([^\.]+)',
            r'([A-Za-z]+) should ([^\.]+)',
            r'([A-Za-z]+) is going to ([^\.]+)',
            r'([A-Za-z]+) has to ([^\.]+)',
            r'([A-Za-z]+) must ([^\.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, transcript_text)
            
            for match in matches:
                assignee, task = match
                
                # Skip if the assignee is a common pronoun
                if assignee.lower() in {"i", "you", "he", "she", "they", "we", "it"}:
                    continue
                
                action_items.append({
                    "assignee": assignee,
                    "task": task
                })
        
        return action_items
    
    def extract_decisions(self, transcript_text: str) -> List[str]:
        """
        Extract potential decisions from a transcript.
        
        Args:
            transcript_text: Transcript text.
            
        Returns:
            List of potential decisions.
        """
        # This is a simple implementation that looks for phrases like "we decided to X"
        # In a real implementation, you would use NLP techniques
        
        decisions = []
        
        # Look for phrases like "we decided to X" or "the decision is to X"
        patterns = [
            r'we decided to ([^\.]+)',
            r'the decision is to ([^\.]+)',
            r'we agreed to ([^\.]+)',
            r'it was decided to ([^\.]+)',
            r'we will ([^\.]+)',
            r'we are going to ([^\.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, transcript_text, re.IGNORECASE)
            
            for match in matches:
                decisions.append(match)
        
        return decisions
