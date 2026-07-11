from interpreter import interpreter
import os
from dotenv import load_dotenv

load_dotenv()
interpreter.llm.api_key = os.getenv("GEMINI_API_KEY")
interpreter.llm.model = "gpt-4o"
interpreter.auto_run = True

# Take a screenshot
import pyscreeze
pyscreeze.screenshot("temp_screenshot.png")

# Pass it to interpreter
resp = interpreter.chat("What is on my screen? I have attached it here: temp_screenshot.png")
print("RESPONSE:", resp)
