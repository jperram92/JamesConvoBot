"""
Test the AI Meeting Assistant with improved chat command handling.
"""
import argparse
import os
import sys
import time

from meeting_interface.browser_automation import BrowserAutomation

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test AI Meeting Assistant Chat Commands")
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
    
    try:
        print(f"Initializing Chrome driver...")
        browser.initialize_driver()
        
        print("Using persistent Chrome profile with logged-in Google account")
        
        print(f"Joining meeting: {args.meeting_url}")
        if browser.join_meeting(args.meeting_url):
            print("Successfully joined meeting")
            
            # Get participants
            participants = browser.get_participants()
            print(f"Participants: {participants}")
            
            print("Bot is now in the meeting. Press Ctrl+C to leave.")
            print("If the bot is in the waiting room, please admit it from the Google Meet interface.")
            print("\nChat Command Test:")
            print("- Type 'Augment help' in the chat to see available commands")
            print("- Type 'Augment list participants' to see who's in the meeting")
            print("- Type 'Augment status' to see the bot's status")
            print("- Type 'Augment summarize' to get a meeting summary")
            print("- Type 'Augment leave' to make the bot leave the meeting")
            
            # Stay in the meeting for a while
            meeting_duration = 0
            while True:
                time.sleep(5)
                meeting_duration += 5
                
                # Check if still in meeting
                if not browser.driver or "Meet" not in browser.driver.title:
                    print("No longer in meeting")
                    break
                
                # Every minute, get participants and print them
                if meeting_duration % 60 == 0:
                    participants = browser.get_participants()
                    if participants:
                        print(f"\nCurrent participants ({len(participants)}):")
                        for participant in participants:
                            print(f"- {participant}")
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
