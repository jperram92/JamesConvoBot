"""
Simplified test for Google Meet client.
"""
import argparse
import sys
import time
import yaml
from openai import OpenAI

from meeting_interface.browser_automation import BrowserAutomation

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Google Meet Client")
    parser.add_argument("--meeting-url", required=True, help="URL of the Google Meet meeting to join")
    args = parser.parse_args()
    
    # Load API key from config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    api_key = config.get('api_keys', {}).get('openai', {}).get('api_key')
    
    if not api_key:
        print("OpenAI API key not found in config.yaml")
        return 1
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Initialize browser automation
    browser = BrowserAutomation()
    
    try:
        print(f"Joining meeting: {args.meeting_url}")
        
        # Join meeting
        if not browser.join_meeting(args.meeting_url):
            print("Failed to join meeting")
            return 1
        
        print("Successfully joined meeting")
        print("You can now speak in the meeting")
        print("The assistant will listen and respond to queries that start with 'Augment'")
        print("Press Ctrl+C to leave the meeting")
        
        # Simple simulation of listening and responding
        while True:
            # In a real implementation, this would be replaced with actual audio processing
            # For now, we'll just simulate a response every 30 seconds
            time.sleep(30)
            
            # Simulate a response
            print("\nSimulating a response to a query...")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are Augment, an AI meeting assistant."},
                    {"role": "user", "content": "What's the weather today?"}
                ]
            )
            
            print(f"Assistant would say: {response.choices[0].message.content}")
    
    except KeyboardInterrupt:
        print("\nLeaving meeting...")
    
    finally:
        # Leave meeting
        browser.leave_meeting()
        print("Left meeting")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
