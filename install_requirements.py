"""
Install required packages for the AI Meeting Assistant.
"""
import subprocess
import sys

def main():
    """Install required packages."""
    print("Installing required packages...")
    
    # List of required packages
    packages = [
        "pyaudio",  # For audio recording
        "numpy",    # For audio processing
        "wave",     # For saving audio files
    ]
    
    # Install each package
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}")
            return 1
    
    print("All packages installed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
