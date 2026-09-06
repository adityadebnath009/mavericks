import requests
import json

payload = {
    "query": "Is it safe to fish here and are there any potential fishing zones?",
    "latitude": 15.0,
    "longitude": 73.0
}

print("👨‍💻 HUMAN: Typing question to Navik Advisor...")
try:
    res = requests.post("http://127.0.0.1:8000/api/chat", json=payload, timeout=20)
    print(f"Status Code: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print("\n✅ CHATBOT RESPONSE (RAW JSON):")
        print(json.dumps(data, indent=2))
    else:
        print(res.text)
except Exception as e:
    print(f"Error: {e}")
