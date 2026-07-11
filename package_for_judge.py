import os
import shutil
import json

def create_submission_package():
    # Source directory (where this script is located)
    source_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Destination directory (on Desktop)
    desktop_dir = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    dest_dir = os.path.join(desktop_dir, 'JARVIS_Submission')
    
    print(f"Packaging JARVIS for submission...\nSource: {source_dir}\nDestination: {dest_dir}\n")
    
    # Remove destination if it already exists to start fresh
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
        
    os.makedirs(dest_dir)
    
    # Files and folders to EXCLUDE from the copy
    exclude = {
        '.git', 
        '__pycache__', 
        '.env', 
        'Secrets.txt', 
        'memory.json', 
        'protocols.json',
        'package_for_judge.py',
        'tts_cache'
    }
    
    # Copy everything over except the exclusions
    for item in os.listdir(source_dir):
        if item in exclude:
            continue
            
        s = os.path.join(source_dir, item)
        d = os.path.join(dest_dir, item)
        
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
            
    print("✓ Core files copied safely (personal files ignored).")
    
    # Create a fresh, empty memory.json
    with open(os.path.join(dest_dir, 'memory.json'), 'w') as f:
        json.dump({}, f, indent=4)
    print("✓ Created clean memory.json.")
        
    # Create the demo protocols.json for the judge
    demo_protocols = {
        "morning routine": {
            "commands": [
                "Open Chrome and search YouTube for morning news",
                "Open Spotify and play some jazz music",
                "Open Notepad"
            ],
            "password": None
        },
        "secure vault": {
            "commands": [
                "Open Chrome and go to github.com"
            ],
            "password": "judge"
        }
    }
    
    with open(os.path.join(dest_dir, 'protocols.json'), 'w') as f:
        json.dump(demo_protocols, f, indent=4)
    print("✓ Created demo protocols.json.")
    
    print(f"\n✅ Packaging Complete!\nA clean, safe copy of JARVIS has been created at: {dest_dir}")
    print("You can safely ZIP that folder and send it to the judge.")

if __name__ == "__main__":
    create_submission_package()
