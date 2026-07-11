# J.A.R.V.I.S. (Just A Rather Very Intelligent System)

An autonomous, multimodal AI assistant built to act as a replica of Iron Man's JARVIS. It features a voice-activated Dual-LLM architecture that allows it to hold natural conversations, manage your emails, and visually interact with your computer's screen to navigate applications autonomously.

## 🌟 Core Features

- **Wake Word Detection & Speech-to-Text**: Utilizes lightweight offline VOSK models for lightning-fast wake word recognition ("Jarvis"), coupled with Google STT for highly accurate command transcription.
- **Dual-LLM Planner/Actor Architecture**: Powered by Google Gemini Pro (Strategic Planner) and Gemini Flash (Vision Actor). JARVIS parses your intent, formulates a step-by-step strategy, and executes it efficiently to save API tokens.
- **Autonomous Vision UI Navigation**: Uses an advanced Computer Vision pipeline (OpenCV + Set-of-Mark OCR Prompting) to dynamically identify, read, and click buttons on your screen. It can skip ads, maximize videos, and navigate GUIs just like a human.
- **Dynamic User Interface**: Features a beautiful front-end displaying current AI states (Listening, Thinking, Speaking) with overlapping modal support and smooth Z-index management.
- **Premium Voice (Text-to-Speech)**: Integrated with ElevenLabs for a responsive, cinematic voice profile with intelligent background muting to prevent audio deadlocks.
- **Google Workspace Integration**: Automatically fetches and reads unanswered emails via secure local OAuth authentication protocols.

---

## 🛠️ Setup Instructions

### 1. Prerequisites
- **Python 3.10+**: Ensure Python is installed and added to your system PATH.
- **Git**: To clone the repository.

### 2. Installation
Clone the repository and install the required dependencies:
```bash
git clone https://github.com/DrZephyros/JARVIS.git
cd JARVIS
pip install -r requirements.txt
```

### 3. API Keys & Environment Setup
You will need API keys for the LLM and TTS engines.
1. Rename the `.env.example` file to `.env`.
2. Open `.env` and paste in your respective keys:
   - `GEMINI_API_KEY`
   - `ELEVENLABS_API_KEY`
   - (Other keys if requested).

### 4. Google Authentication (For Email Integration)
To allow JARVIS to read your emails, you must configure a Google Cloud Console project.
1. Create OAuth 2.0 Credentials (Desktop App) in Google Cloud.
2. Download the JSON file and rename it exactly to `google_client_secrets.json`.
3. Place this file in the root JARVIS directory.

### 5. Download Offline Wake Word Models
JARVIS relies on a local VOSK model to continuously listen for his name without burning cloud API credits.
Run the included setup script to download and extract the required models:
```bash
python setup_vosk.py
```

---

## 🚀 Running JARVIS

You can launch JARVIS through the terminal by simply running:
```bash
python main.py
```

### Create a Desktop Shortcut
If you prefer a seamless, double-click experience to launch JARVIS in the background (with his proper icon), run the included PowerShell script to generate a desktop shortcut automatically:

1. Right-click `Create_Shortcut.ps1` in your folder.
2. Select **Run with PowerShell**.
3. A `JARVIS` icon will appear on your desktop. Double-click it anytime to boot up the system!
