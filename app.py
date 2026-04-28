import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL")
API_SECRET = os.getenv("API_SECRET")
ALLOWED_CHAT_ID = str(os.getenv("TELEGRAM_CHAT_ID"))

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


# 🔹 Send message safely
def send_message(chat_id, text, reply_markup=None):
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)

        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print("Telegram send error:", str(e))


# 🔹 Call EC2 API
def call_ec2(action):
    try:
        response = requests.post(
            API_URL,
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_SECRET
            },
            json={"action": action},
            timeout=10
        )
        return response.text
    except Exception as e:
        return f"❌ API Error: {str(e)}"


# 🔹 Main handler
def handler(request):
    # Health check
    if request.method == "GET":
        return {
            "statusCode": 200,
            "body": "✅ Bot is running"
        }

    try:
        body = json.loads(request.body)

        # 🔹 MESSAGE HANDLING
        if "message" in body:
            chat_id = str(body["message"]["chat"]["id"])
            text = body["message"].get("text", "")

            # 🔐 Restrict access
            if chat_id != ALLOWED_CHAT_ID:
                return {"statusCode": 403, "body": "Unauthorized"}

            if text == "/start":
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "🚀 Start Server", "callback_data": "start"},
                            {"text": "🛑 Stop Server", "callback_data": "stop"}
                        ]
                    ]
                }

                send_message(chat_id, "Choose an action:", keyboard)

        # 🔹 BUTTON CLICK HANDLING
        elif "callback_query" in body:
            query = body["callback_query"]
            chat_id = str(query["message"]["chat"]["id"])
            action = query["data"]

            # 🔐 Restrict access
            if chat_id != ALLOWED_CHAT_ID:
                return {"statusCode": 403, "body": "Unauthorized"}

            send_message(chat_id, f"⏳ Processing: {action}...")

            result = call_ec2(action)

            send_message(chat_id, f"✅ Action: {action}\n{result}")

        return {
            "statusCode": 200,
            "body": "ok"
        }

    except Exception as e:
        error_msg = f"❌ Bot Error:\n{str(e)}"
        print(error_msg)

        # Try sending error to Telegram (if possible)
        try:
            if ALLOWED_CHAT_ID:
                send_message(ALLOWED_CHAT_ID, error_msg)
        except:
            pass

        return {
            "statusCode": 500,
            "body": "Internal Server Error"
        }