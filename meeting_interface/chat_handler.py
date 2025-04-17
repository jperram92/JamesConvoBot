"""
Chat handler for Google Meet.
"""
import time
import threading
from selenium.webdriver.common.by import By
# No need for Keys import

from utils.logging_utils import logger

class ChatHandler:
    """Handle chat interactions in Google Meet."""

    def __init__(self, browser_automation=None):
        """
        Initialize the chat handler.

        Args:
            browser_automation: BrowserAutomation instance for browser interaction.
        """
        self.browser_automation = browser_automation
        self.is_monitoring = False
        self.monitoring_thread = None
        self.last_processed_messages = set()
        self.command_handlers = {}

        # Register default command handlers
        self._register_default_commands()

        logger.info("Initialized chat handler")

    def _register_default_commands(self):
        """Register default command handlers."""
        self.command_handlers = {
            "help": self._handle_help,
            "summarize": self._handle_summarize,
            "list participants": self._handle_list_participants,
            "status": self._handle_status,
            "leave": self._handle_leave,
        }

    def start_monitoring(self):
        """Start monitoring chat for commands."""
        if self.is_monitoring:
            logger.warning("Already monitoring chat")
            return

        self.is_monitoring = True

        # Start monitoring in a separate thread
        self.monitoring_thread = threading.Thread(target=self._monitor_chat)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

        logger.info("Started chat monitoring")

    def stop_monitoring(self):
        """Stop monitoring chat."""
        if not self.is_monitoring:
            logger.warning("Not monitoring chat")
            return

        self.is_monitoring = False

        # Wait for monitoring thread to finish
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)

        logger.info("Stopped chat monitoring")

    def _monitor_chat(self):
        """Monitor chat for commands."""
        try:
            while self.is_monitoring and self.browser_automation and self.browser_automation.driver:
                try:
                    # Check for new messages
                    self._check_for_commands()
                except Exception as e:
                    logger.warning(f"Error checking for commands: {e}")

                # Sleep for a short time
                time.sleep(2)

        except Exception as e:
            logger.error(f"Error in chat monitoring thread: {e}")
            self.is_monitoring = False

    def _check_for_commands(self):
        """Check for commands in the chat."""
        if not self.browser_automation or not self.browser_automation.driver:
            return

        try:
            # First, make sure the chat panel is open
            self._ensure_chat_panel_open()

            # Try to find chat messages with more specific Google Meet selectors
            chat_message_selectors = [
                # Google Meet specific selectors (2023-2025 versions)
                "//div[contains(@class, 'GDhqjd')]",  # Message container
                "//div[contains(@class, 'oIy2qc')]",  # Message text
                "//div[contains(@class, 'YTbUzc')]",  # Message container
                "//div[contains(@class, 'VfPpkd-fmcmS-yrriRe')]",  # Chat input
                "//div[contains(@jsname, 'r4nke')]",  # Chat message
                "//div[contains(@data-sender-name, 'James')]",  # Messages from specific sender

                # Generic selectors
                "//div[contains(@aria-label, 'Chat message')]",
                "//div[contains(@class, 'chat-message')]",
                "//div[contains(@class, 'message-container')]",
                "//div[contains(text(), 'Augment')]",  # Direct text match
                "//span[contains(text(), 'Augment')]/ancestor::div[1]",  # Text in span

                # Last resort - get all visible text elements in the chat area
                "//div[contains(@aria-label, 'Chat with')]/descendant::div"
            ]

            # Get all chat messages
            all_messages = []
            for selector in chat_message_selectors:
                try:
                    elements = self.browser_automation.driver.find_elements(By.XPATH, selector)
                    if elements:
                        for element in elements:
                            try:
                                # Get the message text
                                message_text = element.text.strip()

                                # Skip empty messages
                                if not message_text:
                                    continue

                                all_messages.append(message_text)
                            except Exception as e:
                                logger.debug(f"Error getting message text: {e}")
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {e}")

            # Process all found messages
            for message_text in all_messages:
                # Create a unique identifier for this message
                message_id = message_text

                # Skip if we've already processed this message
                if message_id in self.last_processed_messages:
                    continue

                # Add to processed messages
                self.last_processed_messages.add(message_id)

                # Log all messages for debugging
                logger.debug(f"Chat message: {message_text}")

                # Check if this is a command (case insensitive)
                if "augment" in message_text.lower():
                    logger.info(f"Detected command in chat: {message_text}")
                    # Try to respond directly in the chat
                    self._process_command(message_text)

            # Limit the size of processed messages set
            if len(self.last_processed_messages) > 100:
                # Keep only the most recent 50 messages
                self.last_processed_messages = set(list(self.last_processed_messages)[-50:])

        except Exception as e:
            logger.warning(f"Error checking for commands: {e}")

    def _ensure_chat_panel_open(self):
        """Make sure the chat panel is open."""
        try:
            # Check if chat panel is already open
            chat_input_selectors = [
                "//textarea[contains(@aria-label, 'Send a message')]",
                "//div[@role='textbox']",
                "//div[contains(@class, 'chat-input')]"
            ]

            for selector in chat_input_selectors:
                try:
                    chat_input = self.browser_automation.driver.find_element(By.XPATH, selector)
                    if chat_input and chat_input.is_displayed():
                        # Chat panel is already open
                        return True
                except Exception:
                    pass

            # Chat panel not open, try to open it
            chat_button_selectors = [
                "//button[@aria-label='Chat with everyone']",
                "//div[@aria-label='Chat with everyone']",
                "//button[contains(@aria-label, 'chat')]",
                "//div[contains(@aria-label, 'chat')]",
                "//span[contains(text(), 'Chat')]/parent::div",
                "//div[contains(@data-tooltip, 'Chat')]",
                "//button[contains(@data-tooltip, 'Chat')]"
            ]

            for selector in chat_button_selectors:
                try:
                    chat_button = self.browser_automation.driver.find_element(By.XPATH, selector)
                    if chat_button and chat_button.is_displayed():
                        chat_button.click()
                        logger.info(f"Opened chat panel using selector: {selector}")
                        time.sleep(1)  # Wait for chat panel to open
                        return True
                except Exception:
                    pass

            # Try JavaScript click as a last resort
            for selector in chat_button_selectors:
                try:
                    element = self.browser_automation.driver.find_element(By.XPATH, selector)
                    self.browser_automation.driver.execute_script("arguments[0].click();", element)
                    logger.info(f"Opened chat panel using JavaScript click on selector: {selector}")
                    time.sleep(1)  # Wait for chat panel to open
                    return True
                except Exception:
                    pass

            logger.warning("Could not open chat panel")
            return False

        except Exception as e:
            logger.warning(f"Error ensuring chat panel is open: {e}")
            return False



    def _process_command(self, message_text):
        """
        Process a command from chat.

        Args:
            message_text: The chat message text.
        """
        # Extract the command (after "augment")
        parts = message_text.lower().split("augment", 1)
        if len(parts) < 2:
            return

        command = parts[1].strip()

        # Find the appropriate handler
        handler = None
        for cmd, handler_func in self.command_handlers.items():
            if cmd in command:
                handler = handler_func
                break

        # If no specific handler found, use help
        if not handler:
            handler = self._handle_help

        # Execute the handler and get the response
        response = handler(command)

        # Send the response
        if response and self.browser_automation:
            self._send_chat_response(response)

    def _send_chat_response(self, response):
        """
        Send a response in the chat.

        Args:
            response: The response text to send.
        """
        if not self.browser_automation:
            return

        try:
            # Use the browser automation to send the message
            self.browser_automation._send_chat_message(response)
        except Exception as e:
            logger.error(f"Error sending chat response: {e}")

    def _handle_help(self, _):
        """Handle help command."""
        return (
            "Available commands:\n"
            "- Augment help: Show this help message\n"
            "- Augment summarize: Generate a summary of the meeting so far\n"
            "- Augment list participants: Show who's in the meeting\n"
            "- Augment status: Show the bot's current status\n"
            "- Augment leave: Make the bot leave the meeting"
        )

    def _handle_summarize(self, _):
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

    def _handle_list_participants(self, _):
        """Handle list participants command."""
        if not self.browser_automation:
            return "I can't list participants without browser automation."

        participants = self.browser_automation.get_participants()
        if not participants:
            return "I couldn't detect any participants."

        return f"Current participants: {', '.join(participants)}"

    def _handle_status(self, _):
        """Handle status command."""
        if not self.browser_automation:
            return "I can't check status without browser automation."

        status = "Current Status:\n"
        status += f"- In meeting: {self.browser_automation.is_in_meeting}\n"
        status += f"- Recording: {hasattr(self.browser_automation, 'audio_handler') and self.browser_automation.audio_handler.is_recording}\n"
        status += f"- Transcript lines: {len(self.browser_automation.meeting_transcript)}"

        return status

    def _handle_leave(self, _):
        """Handle leave command."""
        if not self.browser_automation:
            return "I can't leave without browser automation."

        # Schedule leaving after sending response
        def leave_after_delay():
            time.sleep(2)  # Wait for response to be sent
            self.browser_automation.leave_meeting()

        threading.Thread(target=leave_after_delay).start()

        return "I'll leave the meeting now. Goodbye!"
