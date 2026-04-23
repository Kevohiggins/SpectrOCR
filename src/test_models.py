from google import genai
import inspect

from config import get_setting

def list_gemini_models():
    api_key = get_setting("api_key", "")
    client = genai.Client(api_key=api_key)
    
    print("--- Available Models ---")
    for m in client.models.list():
        print(f"- {m.name} | Display Name: {m.display_name}")

if __name__ == "__main__":
    list_gemini_models()
