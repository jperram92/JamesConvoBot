"""
Command recognition for the AI Meeting Assistant.
"""
import re
import threading
import time
# No need for datetime import

from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()

class CommandRecognizer:
    """Recognize and handle commands during meetings."""

    def __init__(self, browser_automation=None):
        """
        Initialize the command recognizer.

        Args:
            browser_automation: BrowserAutomation instance for executing commands.
        """
        self.browser_automation = browser_automation
        self.is_monitoring = False
        self.monitoring_thread = None
        self.trigger_word = config.get('agent.trigger_word', 'Augment')
        self.last_processed_message = None

        # Command patterns
        self.commands = {
            r'(?i)summarize': self._handle_summarize,
            r'(?i)take\s+notes': self._handle_take_notes,
            r'(?i)list\s+participants': self._handle_list_participants,
            r'(?i)help': self._handle_help,
            r'(?i)status': self._handle_status,
            r'(?i)leave': self._handle_leave,
            r'(?i)mute': self._handle_mute,
            r'(?i)unmute': self._handle_unmute,
            r'(?i)record': self._handle_record,
            r'(?i)stop\s+recording': self._handle_stop_recording,
            r'(?i)transcribe': self._handle_transcribe,
            r'(?i)stop\s+transcribing': self._handle_stop_transcribing,
        }

        logger.info("Initialized command recognizer")

    def start_monitoring(self):
        """Start monitoring for commands."""
        if self.is_monitoring:
            logger.warning("Already monitoring for commands")
            return

        self.is_monitoring = True

        # Start monitoring in a separate thread
        self.monitoring_thread = threading.Thread(target=self._monitor_chat)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

        logger.info("Started monitoring for commands")

    def stop_monitoring(self):
        """Stop monitoring for commands."""
        if not self.is_monitoring:
            logger.warning("Not monitoring for commands")
            return

        self.is_monitoring = False

        # Wait for monitoring thread to finish
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)

        logger.info("Stopped monitoring for commands")

    def process_transcript_line(self, line):
        """
        Process a transcript line for commands.

        Args:
            line: Transcript line to process.
        """
        if not self.is_monitoring or not line:
            return

        # Check if line contains trigger word
        if self.trigger_word.lower() in line.lower():
            # Extract command part (after trigger word)
            trigger_index = line.lower().find(self.trigger_word.lower())
            command_text = line[trigger_index + len(self.trigger_word):].strip()

            if command_text and command_text != self.last_processed_message:
                self.last_processed_message = command_text
                self._process_command(command_text)

    def _monitor_chat(self):
        """Monitor chat for commands."""
        try:
            last_processed_messages = set()

            while self.is_monitoring and self.browser_automation:
                # Check for new chat messages every few seconds
                time.sleep(3)

                # Get chat messages
                if hasattr(self.browser_automation, 'get_chat_messages'):
                    try:
                        chat_messages = self.browser_automation.get_chat_messages()

                        # Process new messages
                        for message in chat_messages:
                            # Create a unique identifier for this message
                            message_id = f"{message.get('sender', 'Unknown')}:{message.get('text', '')}"

                            # Skip if we've already processed this message
                            if message_id in last_processed_messages:
                                continue

                            # Add to processed messages
                            last_processed_messages.add(message_id)

                            # Process the message
                            self.process_chat_message(
                                message.get('text', ''),
                                message.get('sender', 'Unknown')
                            )

                        # Limit the size of processed messages set
                        if len(last_processed_messages) > 100:
                            # Keep only the most recent 50 messages
                            last_processed_messages = set(list(last_processed_messages)[-50:])

                    except Exception as e:
                        logger.warning(f"Error processing chat messages: {e}")

        except Exception as e:
            logger.error(f"Error in command monitoring thread: {e}")
            self.is_monitoring = False

    def process_chat_message(self, message, sender):
        """Process a chat message for commands.

        Args:
            message: The chat message text.
            sender: The sender of the message.
        """
        if not self.is_monitoring or not message:
            return

        # Only process messages from others, not from the bot itself
        if sender == "AI Assistant" or sender == self.browser_automation.google_email:
            return

        # Check if message contains trigger word
        if self.trigger_word.lower() in message.lower():
            logger.info(f"Received command in chat from {sender}: {message}")
            self._process_command(message)

    def _process_command(self, command_text):
        """
        Process a command.

        Args:
            command_text: Command text to process.
        """
        logger.info(f"Processing command: {command_text}")

        # Check each command pattern
        for pattern, handler in self.commands.items():
            if re.search(pattern, command_text):
                response = handler(command_text)

                if response and self.browser_automation:
                    # Send response in chat
                    self.browser_automation._send_chat_message(response)

                return

        # No matching command
        if self.browser_automation:
            self.browser_automation._send_chat_message(
                f"I'm sorry, I don't understand that command. Try saying '{self.trigger_word} help' for a list of commands."
            )

    def _handle_summarize(self, command_text):
        """Handle summarize command."""
        if not self.browser_automation:
            return "I can't summarize without browser automation."

        # Generate a quick summary of the meeting so far
        transcript = self.browser_automation.meeting_transcript
        if not transcript:
            return "There's no transcript to summarize yet."

        # For now, just return a simple summary
        # In a real implementation, you would use the summarization module
        return "Here's a quick summary of the meeting so far: This is a placeholder summary. In a real implementation, I would generate a proper summary of the meeting content."

    def _handle_take_notes(self, command_text):
        """Handle take notes command."""
        return "I'm already taking notes of this meeting. I'll provide a summary at the end."

    def _handle_list_participants(self, command_text):
        """Handle list participants command."""
        if not self.browser_automation:
            return "I can't list participants without browser automation."

        participants = self.browser_automation.get_participants()
        if not participants:
            return "I couldn't detect any participants."

        return f"Current participants: {', '.join(participants)}"

    def _handle_help(self, command_text):
        """Handle help command."""
        help_text = f"Here are the commands you can use (prefix with '{self.trigger_word}'):\\n"
        help_text += "- summarize: Generate a summary of the meeting so far\\n"
        help_text += "- take notes: Confirm that I'm taking notes\\n"
        help_text += "- list participants: Show who's in the meeting\\n"
        help_text += "- status: Show my current status\\n"
        help_text += "- mute/unmute: Control my microphone\\n"
        help_text += "- record/stop recording: Control audio recording\\n"
        help_text += "- transcribe/stop transcribing: Control transcription\\n"
        help_text += "- leave: Leave the meeting"

        return help_text

    def _handle_status(self, command_text):
        """Handle status command."""
        if not self.browser_automation:
            return "I can't check status without browser automation."

        status = "Current Status:\\n"
        status += f"- In meeting: {self.browser_automation.is_in_meeting}\\n"
        status += f"- Recording: {hasattr(self.browser_automation, 'audio_handler') and self.browser_automation.audio_handler.is_recording}\\n"
        status += f"- Transcript lines: {len(self.browser_automation.meeting_transcript)}"

        return status

    def _handle_leave(self, command_text):
        """Handle leave command."""
        if not self.browser_automation:
            return "I can't leave without browser automation."

        # Schedule leaving after sending response
        def leave_after_delay():
            time.sleep(2)  # Wait for response to be sent
            self.browser_automation.leave_meeting()

        threading.Thread(target=leave_after_delay).start()

        return "I'll leave the meeting now. Goodbye!"

    def _handle_mute(self, command_text):
        """Handle mute command."""
        # This would require browser_automation to have a method to mute
        return "I've muted my microphone."

    def _handle_unmute(self, command_text):
        """Handle unmute command."""
        # This would require browser_automation to have a method to unmute
        return "I've unmuted my microphone."

    def _handle_record(self, command_text):
        """Handle record command."""
        if not self.browser_automation or not hasattr(self.browser_automation, 'audio_handler'):
            return "I can't control recording without audio handler."

        if not self.browser_automation.audio_handler.is_recording:
            self.browser_automation.audio_handler.start_recording()
            return "I've started recording the meeting."
        else:
            return "I'm already recording the meeting."

    def _handle_stop_recording(self, command_text):
        """Handle stop recording command."""
        if not self.browser_automation or not hasattr(self.browser_automation, 'audio_handler'):
            return "I can't control recording without audio handler."

        if self.browser_automation.audio_handler.is_recording:
            recording_file = self.browser_automation.audio_handler.stop_recording()
            return f"I've stopped recording the meeting. Recording saved to {recording_file}"
        else:
            return "I'm not currently recording the meeting."

    def _handle_transcribe(self, command_text):
        """Handle transcribe command."""
        # This would require browser_automation to have a speech recognizer
        return "I've started transcribing the meeting."

    def _handle_stop_transcribing(self, command_text):
        """Handle stop transcribing command."""
        # This would require browser_automation to have a speech recognizer
        return "I've stopped transcribing the meeting."
