"""
Meeting summarization for the AI Meeting Assistant.
"""
import os
import re

# Try to import OpenAI, but make it optional
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()

class MeetingSummarizer:
    """Generate summaries of meeting transcripts."""

    def __init__(self):
        """Initialize the meeting summarizer."""
        self.api_key = config.get('openai.api_key', '')
        self.use_openai = bool(self.api_key) and OPENAI_AVAILABLE

        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not installed. Using basic summarization.")
        elif self.use_openai:
            openai.api_key = self.api_key
            logger.info("Initialized OpenAI for meeting summarization")
        else:
            logger.warning("OpenAI API key not set. Using basic summarization.")

        # Summary settings
        self.summary_length = config.get('summarization.summary_length', 'medium')
        self.include_action_items = config.get('summarization.generate_action_items', True)
        self.include_timestamps = config.get('summarization.include_timestamps', True)

        logger.info("Initialized meeting summarizer")

    def summarize_transcript(self, transcript_lines):
        """
        Summarize a meeting transcript.

        Args:
            transcript_lines: List of transcript lines.

        Returns:
            Summary text.
        """
        if not transcript_lines:
            return "No transcript available to summarize."

        try:
            if self.use_openai:
                return self._summarize_with_openai(transcript_lines)
            else:
                return self._basic_summarize(transcript_lines)

        except Exception as e:
            logger.error(f"Error summarizing transcript: {e}")
            return f"Error generating summary: {e}"

    def _summarize_with_openai(self, transcript_lines):
        """
        Summarize transcript using OpenAI.

        Args:
            transcript_lines: List of transcript lines.

        Returns:
            Summary text.
        """
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI not available. Falling back to basic summarization.")
            return self._basic_summarize(transcript_lines)

        # Prepare transcript text
        transcript_text = "\\n".join(transcript_lines)

        # Determine max tokens based on summary length
        max_tokens = {
            'short': 150,
            'medium': 300,
            'long': 500
        }.get(self.summary_length, 300)

        # Prepare prompt
        prompt = f"Please summarize the following meeting transcript:\\n\\n{transcript_text}\\n\\n"

        if self.include_action_items:
            prompt += "Include a section for action items and key decisions. "

        if self.include_timestamps:
            prompt += "Reference important timestamps where relevant. "

        prompt += f"Provide a {self.summary_length} length summary."

        try:
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes meeting transcripts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.5
            )

            # Extract summary
            summary = response.choices[0].message.content.strip()

            return summary
        except Exception as e:
            logger.error(f"Error using OpenAI for summarization: {e}")
            return self._basic_summarize(transcript_lines)

    def _basic_summarize(self, transcript_lines):
        """
        Basic transcript summarization without external APIs.

        Args:
            transcript_lines: List of transcript lines.

        Returns:
            Summary text.
        """
        # Extract speakers and their messages
        speakers = {}
        for line in transcript_lines:
            # Parse line format: [timestamp] Speaker: Message
            match = re.match(r'\[(.*?)\] (.*?): (.*)', line)
            if match:
                timestamp, speaker, message = match.groups()
                if speaker not in speakers:
                    speakers[speaker] = []
                speakers[speaker].append((timestamp, message))

        # Generate summary
        summary = "Meeting Summary:\n\n"

        # Add participants
        summary += f"Participants: {', '.join(speakers.keys())}\n\n"

        # Add key points (just take the first few messages from each speaker)
        summary += "Key Points:\n"
        for speaker, messages in speakers.items():
            # Take up to 3 messages per speaker
            for timestamp, message in messages[:3]:
                if len(message) > 100:
                    message = message[:100] + "..."
                summary += f"- {speaker} ({timestamp}): {message}\n"

        # Add simple action items (look for phrases like "need to", "should", "will")
        action_items = []
        for line in transcript_lines:
            for phrase in ["need to", "should", "will", "action item", "todo", "to-do"]:
                if phrase in line.lower():
                    action_items.append(line)
                    break

        if action_items and self.include_action_items:
            summary += "\nPossible Action Items:\n"
            for item in action_items[:5]:  # Limit to 5 items
                summary += f"- {item}\n"

        return summary

    def generate_meeting_summary_file(self, transcript_file):
        """
        Generate a summary file from a transcript file.

        Args:
            transcript_file: Path to transcript file.

        Returns:
            Path to summary file.
        """
        try:
            # Read transcript file
            with open(transcript_file, 'r') as f:
                transcript_lines = f.readlines()

            # Generate summary
            summary = self.summarize_transcript(transcript_lines)

            # Create summary file
            summary_file = transcript_file.replace('transcript_', 'summary_')
            with open(summary_file, 'w') as f:
                f.write(summary)

            logger.info(f"Generated meeting summary: {summary_file}")
            return summary_file

        except Exception as e:
            logger.error(f"Error generating meeting summary file: {e}")
            return None
