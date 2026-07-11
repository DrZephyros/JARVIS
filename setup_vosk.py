import os
import urllib.request
import zipfile
import sys

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "vosk-model-small-en-us-0.15")
ZIP_PATH = os.path.join(MODEL_DIR, "vosk-model.zip")

def download_model():
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        
    if os.path.exists(MODEL_PATH):
        print(f"VOSK model already exists at {MODEL_PATH}")
        return True
        
    print(f"Downloading VOSK wake-word model (approx 40MB) from {MODEL_URL}...")
    try:
        def progress(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size)
            sys.stdout.write(f"\rDownloading... {percent}%")
            sys.stdout.flush()

        urllib.request.urlretrieve(MODEL_URL, ZIP_PATH, reporthook=progress)
        print("\nDownload complete. Extracting...")
        
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(MODEL_DIR)
            
        os.remove(ZIP_PATH)
        print("Model extracted successfully.")
        return True
    except Exception as e:
        print(f"\nError downloading model: {e}")
        return False

if __name__ == "__main__":
    download_model()
