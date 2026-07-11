# J.A.R.V.I.S. (Just A Rather Very Intelligent System)

An autonomous, multimodal AI assistant built to act as a replica of Iron Man's JARVIS. It features a voice-activated Dual-LLM architecture that allows it to hold natural conversations, manage your emails, and visually interact with your computer's screen to navigate applications autonomously.

## 🌟 Core Features
- **Wake Word Detection & Speech-to-Text**: Utilizes lightweight offline VOSK models for lightning-fast wake word recognition ("Jarvis"), coupled with Google STT for highly accurate command transcription.
- **Dual-LLM Planner/Actor Architecture**: Powered by Google Gemini Pro (Strategic Planner) and Gemini Flash (Vision Actor). JARVIS parses your intent, formulates a step-by-step strategy, and executes it efficiently to save API tokens.
- **Autonomous Vision UI Navigation**: Uses an advanced Computer Vision pipeline (OpenCV + Set-of-Mark OCR Prompting) to dynamically identify, read, and click buttons on your screen. It can skip ads, maximize videos, and navigate GUIs just like a human.
- **Dynamic User Interface**: Features a beautiful front-end displaying current AI states (Listening, Thinking, Speaking) with overlapping modal support and smooth Z-index management.
- **Premium Voice (Text-to-Speech)**: Integrated with ElevenLabs for a responsive, cinematic voice profile with intelligent background muting to prevent audio deadlocks.
- **Google Workspace & Microsoft Office Integration**: Automatically fetches and reads unanswered emails via secure local OAuth authentication protocols for both Google and Microsoft (Azure) accounts.

---

## 🛠️ Step-by-Step Setup Guide (For Beginners)
Don't worry if you aren't a programmer! Just follow these steps closely to get JARVIS running on your computer.

### Step 1: Install Python and Git
1. **Download Python**: Go to [python.org](https://www.python.org/downloads/) and download Python (Version 3.10 or newer).
   - **CRITICAL**: During the installation, make sure you check the box that says **"Add Python to PATH"** at the very bottom before clicking Install. If you miss this, JARVIS won't know how to run!
2. **Download Git**: Go to [git-scm.com](https://git-scm.com/downloads) and install Git for Windows. You can just click "Next" on all the default settings.

### Step 2: Download the JARVIS Code
1. Open your computer's **Command Prompt** (press the Windows key, type `cmd`, and hit Enter).
2. Type the following command to download the code to your computer and hit Enter:
   ```bash
   git clone https://github.com/DrZephyros/JARVIS.git
   ```
3. Move into the JARVIS folder you just downloaded by typing this and hitting Enter:
   ```bash
   cd JARVIS
   ```

### Step 3: Install Required Libraries
JARVIS needs a few extra software packages to run. While still in the Command Prompt (inside the JARVIS folder), run this command:
```bash
pip install -r requirements.txt
```
*Wait for the progress bars to finish downloading everything.*

### Step 4: Get Your AI Brain Keys (API Keys)
JARVIS needs to connect to Google Gemini (for his brain) and ElevenLabs (for his voice). These keys act like personal passwords so JARVIS can use their services.
1. Find the `.env.example` file in your JARVIS folder and rename it to exactly `.env` (make sure it doesn't accidentally become `.env.txt`).
2. Open the `.env` file using Notepad.
3. **Get a Gemini API Key**: Go to [Google AI Studio](https://aistudio.google.com/), sign in, and click "Create API Key". Paste this key next to `GEMINI_API_KEY=` in your `.env` file.
4. **Get an ElevenLabs API Key**: Go to [ElevenLabs](https://elevenlabs.io/), create a free account, click on your profile in the bottom left -> "Profile + API key", and copy the key. Paste it next to `ELEVENLABS_API_KEY=` in your `.env` file.
5. Save and close the `.env` file.

### Step 5: Email Integration (Optional but Highly Recommended)
To allow JARVIS to read your emails safely, you need to tell Google or Microsoft to trust JARVIS.

**For Gmail / Google Accounts**:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new Project, and go to "APIs & Services" -> "Credentials".
3. Click "Create Credentials" -> "OAuth client ID" (Choose "Desktop app").
4. Click the download icon to save the JSON file to your computer.
5. Rename the downloaded file to exactly `google_client_secrets.json` and drag it into your JARVIS folder.

**For Outlook / Microsoft Accounts**:
1. Go to the [Microsoft Entra ID (Azure) Portal](https://entra.microsoft.com/).
2. Go to "Applications" -> "App registrations" and click "New registration".
3. Name it "JARVIS" and set the redirect URI to "Public client/native (mobile & desktop)".
4. Once created, copy the "Application (client) ID" (it looks like a long string of letters and numbers).
5. Create a new text file in your JARVIS folder named exactly `azure_client_id.txt` and paste the ID inside.

### Step 6: Download JARVIS's Ears (Wake Word Models)
JARVIS relies on a local offline model to continuously listen for his name ("Jarvis") without burning cloud API credits or invading your privacy.
Run this simple script to download his "ears":
1. In your Command Prompt (still inside the JARVIS folder), type:
   ```bash
   python setup_vosk.py
   ```
   *Wait for the download to finish.*

---

## 🚀 How to Start JARVIS!

You are all set! You can launch JARVIS in two ways:

**Method 1: Terminal (For Developers)**
Open your Command Prompt in the JARVIS folder and type:
```bash
python main.py
```

**Method 2: The Easy Desktop Shortcut (For Everyone Else)**
1. Go to your JARVIS folder and find the file named `Create_Shortcut.ps1`.
2. Right-click on it and select **"Run with PowerShell"**.
3. A beautiful **JARVIS** icon will appear on your computer's desktop!
4. From now on, you can just double-click that icon on your desktop to wake him up! No terminal required.
