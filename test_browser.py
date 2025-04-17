"""
Test browser automation for Google Meet.
"""
import argparse
import sys
import time

from meeting_interface.browser_automation import BrowserAutomation

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Browser Automation")
    parser.add_argument("--meeting-url", required=True, help="URL of the Google Meet meeting to join")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()
    
    # Initialize browser automation
    browser = BrowserAutomation()
    
    # Override headless setting if specified
    if args.headless is not None:
        browser.headless = args.headless
    
    try:
        print(f"Initializing Chrome driver...")
        browser.initialize_driver()
        
        print(f"Joining meeting: {args.meeting_url}")
        if browser.join_meeting(args.meeting_url):
            print("Successfully joined meeting")
            
            # Get participants
            participants = browser.get_participants()
            print(f"Participants: {participants}")
            
            print("Press Ctrl+C to leave the meeting")
            
            # Stay in the meeting for a while
            while True:
                time.sleep(5)
                
                # Check if still in meeting
                if not browser.driver or "Meet" not in browser.driver.title:
                    print("No longer in meeting")
                    break
        else:
            print("Failed to join meeting")
    
    except KeyboardInterrupt:
        print("\nLeaving meeting...")
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Leave meeting
        browser.leave_meeting()
        print("Left meeting")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
