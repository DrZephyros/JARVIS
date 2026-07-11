import os
import sys

sys.path.append(os.getcwd())
from vision_system import TwoTierVision

def main():
    print("Testing TwoTierVision initialization...")
    vision = TwoTierVision()
    
    if not vision.reader_available:
        print("WARN: WinRT OCR reader failed to initialize.")
    else:
        print("SUCCESS: WinRT OCR reader initialized.")
        
    print("TwoTierVision loaded successfully.")
    print("Testing find_text...")
    coords = vision.find_text("Liked")
    if coords:
        print(f"Found 'Liked' at {coords}")
    else:
        print("Could not find 'Liked' on screen.")

if __name__ == "__main__":
    main()
