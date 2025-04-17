"""
Create a persistent Chrome profile with logged-in Google account.
This script opens a Chrome browser where you can manually log in to the Google account.
The login session will be saved to a profile directory that can be reused by the bot.
"""
import os
import time
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options

def main():
    print("Creating Chrome profile for bot...")
    
    # Create profile directory if it doesn't exist
    user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    os.makedirs(user_data_dir, exist_ok=True)
    
    # Set up Chrome options
    options = Options()
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Initialize driver
    print("Opening Chrome browser. Please log in to the Google account manually.")
    driver = uc.Chrome(options=options)
    
    # Navigate to Google sign-in page
    driver.get("https://accounts.google.com/signin")
    
    print("\nInstructions:")
    print("1. Log in to the Google account you created for the bot")
    print("2. Complete any security checks or CAPTCHA challenges")
    print("3. Make sure you're fully logged in (you should see the Google account dashboard)")
    print("4. Once logged in, this script will wait for 5 minutes to ensure all cookies are saved")
    print("5. After 5 minutes, the browser will close automatically")
    print("\nThe Chrome profile will be saved to:", user_data_dir)
    
    # Wait for 5 minutes to ensure login is complete and cookies are saved
    for i in range(300, 0, -1):
        mins, secs = divmod(i, 60)
        timer = f"{mins:02d}:{secs:02d}"
        print(f"Waiting for profile to be saved: {timer}", end="\r")
        time.sleep(1)
    
    # Close the browser
    driver.quit()
    
    print("\nChrome profile created successfully!")
    print("You can now run the bot with this profile to avoid CAPTCHA challenges.")

if __name__ == "__main__":
    main()
