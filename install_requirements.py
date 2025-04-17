"""
Install required packages for the AI Meeting Assistant.
"""
import subprocess
import sys

def main():
    """Install required packages."""
    print("Installing required packages...")

    # List of required packages
    required_packages = [
        "pyaudio",             # For audio recording
        "numpy",               # For audio processing
        "wave",                # For saving audio files
        "requests",            # For HTTP requests
        "python-dotenv",       # For environment variables
    ]

    # Optional packages
    optional_packages = [
        "SpeechRecognition",   # For speech recognition
        "pocketsphinx",        # For offline speech recognition
        "openai",              # For summarization
        "google-cloud-speech", # For Google Cloud Speech-to-Text
    ]

    # Install required packages
    print("\nInstalling required packages...")
    for package in required_packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}")
            return 1

    # Install optional packages
    print("\nInstalling optional packages (some may fail, that's OK)...")
    for package in optional_packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError:
            print(f"Failed to install {package} - this is OK, the bot will still work with reduced functionality")

    print("All packages installed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
