"""
Test OpenAI integration.
"""
import os
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
    
    # Test chat completion
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ]
    )
    
    print("Response:", response.choices[0].message.content)

if __name__ == "__main__":
    main()
