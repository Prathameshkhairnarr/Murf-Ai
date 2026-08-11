import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

# Your Vapi Private API Key (starts with 'sk-')
VAPI_API_KEY = os.environ.get("VAPI_API_KEY", "")

# The phone number you want to call (your personal mobile)
TO_NUMBER = "+918421922328"  # Must include country code

# Your Vapi purchased phone number (you must buy one in Vapi dashboard to make outbound calls)
# If Vapi allows calling without a purchased number (using a default routing number), leave this blank.
FROM_NUMBER = ""

def make_vapi_call():
    if not VAPI_API_KEY:
        print("ERROR: VAPI_API_KEY is not set in .env.local")
        return

    print(f"Initiating outbound call to {TO_NUMBER} via Vapi.ai...")

    url = "https://api.vapi.ai/call/phone"
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "phoneNumberId": "3282c930-65b1-4ddb-8f06-03f9c2000ae1",
        "customer": {
            "number": TO_NUMBER
        },
        "assistant": {
            "name": "Rakshika NDRF Assistant",
            "model": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Rakshika, a female assistant from NDRF (National Disaster Response Force). "
                            "You are calling to alert the user about a heavy rainfall and flood warning in their district. "
                            "Speak strictly in Hindi using Devanagari script. Be polite, urgent, and professional. "
                            "Start by saying: 'नमस्ते। मैं रक्षिका हूँ, NDRF की तरफ से। आपके जिले में भारी बारिश और बाढ़ का अलर्ट जारी किया गया है। कृपया सुरक्षित स्थान पर जाएँ।'"
                        )
                    }
                ]
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "EXAVITQu4vr4xnSDxMaL", # Bella - good multilingual voice on ElevenLabs
                "model": "eleven_multilingual_v2"
            }
        }
    }
    
    # Placed the call

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print("Success! Vapi call initiated.")
        print("Response:", response.json())
    except requests.exceptions.HTTPError as e:
        print(f"Failed to place call: {e}")
        try:
            print("Error details:", response.json())
        except:
            print("Raw response:", response.text)

if __name__ == "__main__":
    make_vapi_call()
