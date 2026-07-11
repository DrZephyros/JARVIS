import os
import io
import time
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

# Setup ElevenLabs client
api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    print("No ELEVENLABS_API_KEY found.")
    exit(1)

client = ElevenLabs(api_key=api_key)
JARVIS_VOICE_ID = os.getenv("JARVIS_VOICE_ID", "15FdLT5xRvbE88aexehv")

PRESETS = {
    "abort": [
        "Autonomous tasks have been aborted, Sir.",
        "I have terminated the current operation, Sir.",
        "As you wish, Sir. Task aborted.",
        "Halting operations immediately, Sir."
    ],
    "complete": [
        "Task complete, Sir.",
        "I have finished the assigned task, Sir.",
        "Operation successful, Sir.",
        "All done, Sir. Is there anything else?"
    ],
    "error": [
        "I encountered a slight complication with that, Sir.",
        "I'm afraid I ran into an error, Sir.",
        "Apologies, Sir, but it seems I've hit a snag.",
        "Something went wrong during execution, Sir."
    ],
    "startup": [
        "JARVIS systems are now online sir."
    ]
}

cache_dir = "tts_presets"
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

print("Generating JARVIS TTS presets...")

for category, phrases in PRESETS.items():
    for i, text in enumerate(phrases):
        filename = f"{category}_{i}.mp3"
        filepath = os.path.join(cache_dir, filename)
        
        if os.path.exists(filepath):
            print(f"Skipping {filename} (already exists)")
            continue
            
        print(f"Generating: {filename} -> '{text}'")
        try:
            audio_gen = client.text_to_speech.convert(
                text=text,
                voice_id=JARVIS_VOICE_ID,
                model_id="eleven_flash_v2_5",
                output_format="mp3_44100_128",
            )
            chunks = [chunk for chunk in audio_gen]
            audio_bytes = b"".join(chunks)
            
            with open(filepath, "wb") as f:
                f.write(audio_bytes)
            
            # Small delay to respect rate limits
            time.sleep(0.5)
        except Exception as e:
            print(f"Failed to generate {filename}: {e}")

print("Done generating TTS presets!")
