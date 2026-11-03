import os
import ssl
import certifi
from pathlib import Path
import time

# --- עקיפת SSL (השאירי רק אם בלעדיה מתקבלת שגיאת חיבור, אחרת אפשר למחוק) ---
os.environ['SSL_CERT_FILE'] = certifi.where()
ssl._create_default_https_context = ssl._create_unverified_context

import httpx
original_init = httpx.Client.__init__
def new_init(self, *args, **kwargs):
    kwargs['verify'] = False
    original_init(self, *args, **kwargs)
httpx.Client.__init__ = new_init
# -----------------------------------------------------------------------------

import gradio as gr
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL = "gemini-3.8-flash"  
PROMPTS_DIR = Path(__file__).parent / "prompts"

client = genai.Client()


def load_prompt(version: str) -> str:
    return (PROMPTS_DIR / f"{version}.txt").read_text(encoding="utf-8")


def generate_cli_command(user_instruction: str, version: str) -> str:
    if not user_instruction.strip():
        return ""
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=user_instruction,
            config=types.GenerateContentConfig(
                system_instruction=load_prompt(version),
                temperature=0,
            ),
        )
        return response.text.strip()
    except Exception as e:
        return f"Error: {e}"


versions = sorted(p.stem for p in PROMPTS_DIR.glob("v*.txt"))

demo = gr.Interface(
    fn=generate_cli_command,
    inputs=[
        gr.Textbox(label="הוראה בשפה טבעית", lines=3),
        gr.Dropdown(versions, value=versions[-1], label="גרסת פרומפט"),
    ],
    outputs=gr.Textbox(label="פקודת CLI"),
    title="NL → CLI",
)

if __name__ == "__main__":
    demo.launch()