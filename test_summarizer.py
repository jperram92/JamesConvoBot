"""
Test summarizer component.
"""
import yaml
from openai import OpenAI

def main():
    # Load API key from config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    api_key = config.get('api_keys', {}).get('openai', {}).get('api_key')
    
    if not api_key:
        print("OpenAI API key not found in config.yaml")
        return
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Sample transcript
    transcript = """
    [10:00:15] John: Good morning everyone, let's get started with our weekly meeting.
    [10:00:30] Sarah: Hi everyone, I have updates on the marketing campaign.
    [10:01:05] John: Great, please go ahead Sarah.
    [10:01:20] Sarah: We've seen a 15% increase in engagement since launching the new social media strategy.
    [10:02:10] Mike: That's impressive. What channels are performing best?
    [10:02:30] Sarah: Instagram and TikTok are our top performers, with Twitter showing moderate growth.
    [10:03:15] John: Excellent. Mike, what's the status on the product development?
    [10:03:30] Mike: We're on track to release version 2.0 next month. The team has completed 85% of the planned features.
    [10:04:10] John: Any blockers we should be aware of?
    [10:04:25] Mike: We need final approval on the UI designs by Friday to stay on schedule.
    [10:04:45] John: Noted. Sarah, can you review the designs with the marketing team and provide feedback by Thursday?
    [10:05:00] Sarah: Yes, I'll schedule that for tomorrow afternoon.
    [10:05:20] John: Perfect. Any other updates or concerns?
    [10:05:35] Mike: We should discuss the budget for Q3 at our next meeting.
    [10:05:50] John: Good point. I'll add that to the agenda. If there's nothing else, let's wrap up. Thanks everyone!
    """
    
    # Generate summary
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI meeting assistant. Summarize the following meeting transcript and extract action items."},
            {"role": "user", "content": f"Please summarize this meeting transcript and list any action items:\n\n{transcript}"}
        ]
    )
    
    print("Meeting Summary:")
    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()
