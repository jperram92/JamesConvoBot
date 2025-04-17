"""
Test web search tool.
"""
import yaml
import requests

def main():
    # Load API key from config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    google_api_key = config.get('api_keys', {}).get('google', {}).get('api_key')
    google_cse_id = config.get('api_keys', {}).get('google', {}).get('cse_id')
    
    if not google_api_key or not google_cse_id:
        print("Google API key or CSE ID not found in config.yaml")
        # Use a mock response for testing
        print("\nUsing mock response for testing:")
        print_mock_search_results("latest AI news")
        return
    
    # Perform a Google search
    query = "latest AI news"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": google_api_key,
        "cx": google_cse_id,
        "q": query,
        "num": 5
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        results = response.json()
        
        if "items" not in results:
            print(f"No results found for query: {query}")
            return
        
        # Format the results
        print(f"Search results for '{query}':\n")
        
        for i, item in enumerate(results["items"][:5], 1):
            title = item.get("title", "No title")
            link = item.get("link", "No link")
            snippet = item.get("snippet", "No description")
            
            print(f"{i}. {title}")
            print(f"   URL: {link}")
            print(f"   Description: {snippet}\n")
    
    except Exception as e:
        print(f"Error performing search: {e}")
        # Use a mock response for testing
        print("\nUsing mock response for testing:")
        print_mock_search_results(query)

def print_mock_search_results(query):
    """Print mock search results for testing."""
    print(f"Search results for '{query}':\n")
    
    mock_results = [
        {
            "title": "Latest AI News and Breakthroughs - AI News",
            "link": "https://www.example.com/ai-news",
            "snippet": "Stay updated with the latest artificial intelligence news, breakthroughs, and research from around the world."
        },
        {
            "title": "OpenAI Releases GPT-5 with Enhanced Capabilities",
            "link": "https://www.example.com/openai-gpt5",
            "snippet": "OpenAI has announced the release of GPT-5, featuring improved reasoning, multimodal capabilities, and reduced hallucinations."
        },
        {
            "title": "AI Regulation: New Global Framework Proposed",
            "link": "https://www.example.com/ai-regulation",
            "snippet": "World leaders have proposed a new global framework for AI regulation, focusing on safety, transparency, and ethical considerations."
        }
    ]
    
    for i, item in enumerate(mock_results, 1):
        print(f"{i}. {item['title']}")
        print(f"   URL: {item['link']}")
        print(f"   Description: {item['snippet']}\n")

if __name__ == "__main__":
    main()
