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


# ✅ THIS is what Vercel needs
def app(environ, start_response):
    try:
        method = environ.get("REQUEST_METHOD")

        # 🌐 Health check
        if method == "GET":
            response_body = "✅ Bot is running"
            start_response("200 OK", [("Content-Type", "text/plain")])
            return [response_body.encode()]

        # 📥 Read request body
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
        except:
            content_length = 0

        body = environ["wsgi.input"].read(content_length)
        data = json.loads(body.decode("utf-8") or "{}")

        # 🔹 MESSAGE
        if "message" in data:
            chat_id = str(data["message"]["chat"]["id"])
            text = data["message"].get("text", "")

            if chat_id != ALLOWED_CHAT_ID:
                start_response("403 Forbidden", [])
                return [b"Unauthorized"]

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

        # 🔹 CALLBACK
        elif "callback_query" in data:
            query = data["callback_query"]
            chat_id = str(query["message"]["chat"]["id"])
            action = query["data"]

            if chat_id != ALLOWED_CHAT_ID:
                start_response("403 Forbidden", [])
                return [b"Unauthorized"]

            send_message(chat_id, f"⏳ Processing: {action}...")

            result = call_ec2(action)

            send_message(chat_id, f"✅ Action: {action}\n{result}")

        start_response("200 OK", [("Content-Type", "application/json")])
        return [b'{"status":"ok"}']

    except Exception as e:
        error_msg = f"❌ Bot Error:\n{str(e)}"
        print(error_msg)

        try:
            if ALLOWED_CHAT_ID:
                send_message(ALLOWED_CHAT_ID, error_msg)
        except:
            pass

        start_response("500 Internal Server Error", [])
        return [b"Internal Server Error"]