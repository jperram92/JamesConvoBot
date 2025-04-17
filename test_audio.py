"""
Test audio processing and OpenAI integration.
"""
import argparse
import sys
import time
import yaml
from openai import OpenAI

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Audio Processing")
    parser.add_argument("--duration", type=int, default=60, help="Duration to run the test in seconds")
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
    
    print("Starting audio processing test...")
    print("This test will simulate a meeting assistant that listens and responds to queries.")
    print(f"The test will run for {args.duration} seconds.")
    print("Press Ctrl+C to stop the test early.")
    
    # Simulate a meeting transcript
    transcript = [
        {"speaker": "John", "text": "Good morning everyone, let's get started with our weekly meeting."},
        {"speaker": "Sarah", "text": "Hi everyone, I have updates on the marketing campaign."},
        {"speaker": "John", "text": "Great, please go ahead Sarah."},
        {"speaker": "Sarah", "text": "We've seen a 15% increase in engagement since launching the new social media strategy."},
        {"speaker": "Mike", "text": "That's impressive. What channels are performing best?"},
        {"speaker": "Sarah", "text": "Instagram and TikTok are our top performers, with Twitter showing moderate growth."},
        {"speaker": "John", "text": "Excellent. Mike, what's the status on the product development?"},
        {"speaker": "Mike", "text": "We're on track to release version 2.0 next month. The team has completed 85% of the planned features."},
        {"speaker": "John", "text": "Any blockers we should be aware of?"},
        {"speaker": "Mike", "text": "We need final approval on the UI designs by Friday to stay on schedule."},
        {"speaker": "John", "text": "Noted. Sarah, can you review the designs with the marketing team and provide feedback by Thursday?"},
        {"speaker": "Sarah", "text": "Yes, I'll schedule that for tomorrow afternoon."},
        {"speaker": "John", "text": "Perfect. Any other updates or concerns?"},
        {"speaker": "Mike", "text": "We should discuss the budget for Q3 at our next meeting."},
        {"speaker": "John", "text": "Good point. I'll add that to the agenda. If there's nothing else, let's wrap up. Thanks everyone!"},
        {"speaker": "User", "text": "Augment, can you summarize the key points from this meeting?"}
    ]
    
    try:
        start_time = time.time()
        
        # Process each transcript entry
        for entry in transcript:
            # Print the transcript entry
            print(f"\n{entry['speaker']}: {entry['text']}")
            
            # If this is a query for Augment, generate a response
            if "Augment" in entry['text']:
                print("\nProcessing query...")
                
                # Generate a response using OpenAI
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are Augment, an AI meeting assistant. You help with meeting transcription, answering questions, and providing summaries."},
                        {"role": "user", "content": "\n".join([f"{e['speaker']}: {e['text']}" for e in transcript[:-1]])},
                        {"role": "user", "content": entry['text']}
                    ]
                )
                
                # Print the response
                print(f"\nAugment: {response.choices[0].message.content}")
            
            # Pause between entries
            time.sleep(2)
            
            # Check if we've exceeded the duration
            if time.time() - start_time > args.duration:
                print("\nTest duration exceeded. Stopping test.")
                break
        
        # Generate a meeting summary
        print("\n\nGenerating meeting summary...")
        
        summary_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI meeting assistant. Summarize the following meeting transcript and extract action items."},
                {"role": "user", "content": f"Please summarize this meeting transcript and list any action items:\n\n{chr(10).join([f'{e['speaker']}: {e['text']}' for e in transcript[:-1]])}"}
            ]
        )
        
        print("\nMeeting Summary:")
        print(summary_response.choices[0].message.content)
    
    except KeyboardInterrupt:
        print("\nTest stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
    
    print("\nTest completed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
