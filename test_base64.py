from interpreter import interpreter
import os
from dotenv import load_dotenv
import pyscreeze
import base64

load_dotenv()
interpreter.llm.api_key = os.getenv("GEMINI_API_KEY")
interpreter.llm.model = "gpt-4o"
interpreter.auto_run = True

pyscreeze.screenshot("temp_screenshot.png")
with open("temp_screenshot.png", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

# Open Interpreter uses OpenAI format internally
msg = {
    "role": "user",
    "type": "message",
    "content": [
        {"type": "text", "text": "What is on my screen? I have attached it here."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_string}"}}
    ]
}

print(interpreter.chat([msg]))
