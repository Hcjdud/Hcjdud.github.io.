from flask import Flask, request
import requests
import json
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8514511524:AAH9_bCmQYOaB29ajeFn_vlad3BSVpcUUIA"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_msg(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)

@app.route('/')
def home():
    return "✅ Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        
        if text == "/start":
            send_msg(chat_id, "🌟 Привет! Я VPN бот")
        else:
            send_msg(chat_id, f"Вы написали: {text}")
    
    return "OK", 200

if __name__ == '__main__':
    app.run()
