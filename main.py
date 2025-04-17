"""
Main entry point for AI Meeting Assistant.
"""
import argparse
import os
import sys
import time
from typing import List, Optional

from meeting_interface.meet_client import MeetClient
from summarizer.summary_generator import SummaryGenerator
from utils.config import get_config
from utils.logging_utils import logger

# Get configuration
config = get_config()


def join_meeting(meeting_url: str) -> Optional[MeetClient]:
    """
    Join a Google Meet meeting.
    
    Args:
        meeting_url: URL of the meeting to join.
        
    Returns:
        MeetClient instance if joined successfully, None otherwise.
    """
    try:
        # Create client
        client = MeetClient()
        
        # Join meeting
        if client.join_meeting(meeting_url):
            logger.info(f"Successfully joined meeting: {meeting_url}")
            return client
        else:
            logger.error(f"Failed to join meeting: {meeting_url}")
            return None
    
    except Exception as e:
        logger.error(f"Error joining meeting: {e}")
        return None


def send_summary_email(client: MeetClient, recipients: List[str]) -> None:
    """
    Send a summary email.
    
    Args:
        client: MeetClient instance.
        recipients: List of email recipients.
    """
    try:
        # Send summary email
        result = client.send_summary_email(recipients)
        logger.info(f"Summary email result: {result}")
    
    except Exception as e:
        logger.error(f"Error sending summary email: {e}")


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="AI Meeting Assistant")
    parser.add_argument("--meeting-url", help="URL of the Google Meet meeting to join")
    parser.add_argument("--email", action="append", help="Email address to send summary to")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    
    # Load custom config if provided
    if args.config:
        config_path = args.config
        if os.path.exists(config_path):
            config.config_path = config_path
            config.config = config._load_config()
            config._override_with_env_vars()
            logger.info(f"Loaded configuration from {config_path}")
        else:
            logger.error(f"Configuration file not found: {config_path}")
            return 1
    
    # Check if meeting URL is provided
    meeting_url = args.meeting_url
    if not meeting_url:
        # Try to get from config
        meeting_url = config.get('google_meet.meeting_url')
        
        if not meeting_url:
            logger.error("Meeting URL not provided")
            parser.print_help()
            return 1
    
    # Join meeting
    client = join_meeting(meeting_url)
    
    if not client:
        return 1
    
    try:
        # Wait for meeting to end
        logger.info("Press Ctrl+C to leave the meeting")
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Leaving meeting...")
    
    finally:
        # Leave meeting
        client.leave_meeting()
        
        # Send summary email if recipients provided
        if args.email:
            send_summary_email(client, args.email)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
