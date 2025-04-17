"""
Test the AI Meeting Assistant with direct chat command handling.
This script focuses specifically on testing chat commands.
"""
import argparse
import os
import sys
import time

from meeting_interface.browser_automation import BrowserAutomation

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test AI Meeting Assistant Direct Chat Commands")
    parser.add_argument("--meeting-url", required=True, help="URL of the Google Meet meeting to join")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()
    
    # Check if Chrome profile exists
    chrome_profile_dir = os.path.join(os.getcwd(), "chrome_profile")
    if not os.path.exists(chrome_profile_dir) or not os.listdir(chrome_profile_dir):
        print("ERROR: Chrome profile not found or empty")
        print("Please run create_chrome_profile.py first to set up a logged-in profile:")
        print("  python create_chrome_profile.py")
        return 1
    
    # Initialize browser automation
    browser = BrowserAutomation()
    
    # Override headless setting if specified
    if args.headless is not None:
        browser.headless = args.headless
    
    # Disable features that might interfere with chat testing
    browser.is_transcribing = False
    
    try:
        print(f"Initializing Chrome driver...")
        browser.initialize_driver()
        
        print("Using persistent Chrome profile with logged-in Google account")
        
        print(f"Joining meeting: {args.meeting_url}")
        if browser.join_meeting(args.meeting_url):
            print("Successfully joined meeting")
            
            # Send initial message
            browser._send_chat_message("Hello! I'm the AI Meeting Assistant. I'm here to assist with the meeting.")
            browser._send_chat_message("Type 'Augment help' to see available commands.")
            
            print("\n=== CHAT COMMAND TEST MODE ===")
            print("The bot is now monitoring the chat for commands.")
            print("Available commands:")
            print("- Augment help")
            print("- Augment list participants")
            print("- Augment status")
            print("- Augment summarize")
            print("- Augment leave")
            print("\nPress Ctrl+C to exit the test.")
            
            # Stay in the meeting and focus on chat commands
            while True:
                time.sleep(1)
                
                # Check if still in meeting
                if not browser.driver or "Meet" not in browser.driver.title:
                    print("No longer in meeting")
                    break
        else:
            print("Failed to join meeting")
            return 1
    
    except KeyboardInterrupt:
        print("\nLeaving meeting...")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    finally:
        # Leave meeting
        browser.leave_meeting()
        print("Left meeting")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
