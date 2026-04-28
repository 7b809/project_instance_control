from flask import Flask, request, jsonify, send_file
import requests
import os
import threading
from dotenv import load_dotenv

# -----------------------------------
# 🔐 Load environment variables
# -----------------------------------
load_dotenv()

API_URL = os.getenv("API_URL")
SEND_LOGS_URL = os.getenv("SEND_LOGS_URL")

app = Flask(__name__)


# -----------------------------------
# 🏠 Serve HTML Page
# -----------------------------------
@app.route("/", methods=["GET"])
def index():
    return send_file("templates/index.html")


# -----------------------------------
# 🚀 ASYNC LOG TRIGGER (FAST ⚡)
# -----------------------------------
def trigger_logs():
    try:
        if SEND_LOGS_URL:
            requests.get(SEND_LOGS_URL, timeout=5)
    except Exception as e:
        print("[LOG ERROR]", e)


# -----------------------------------
# 🔁 Proxy API Request
# -----------------------------------
@app.route("/api/control", methods=["POST"])
def control():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON received"}), 400

        action = data.get("action")

        if not action:
            return jsonify({"error": "Missing 'action'"}), 400

        # -----------------------------------
        # 🔁 Forward request to external API
        # -----------------------------------
        response = requests.post(API_URL, json={"action": action})

        try:
            result = response.json()
        except:
            result = {"message": response.text}

        # -----------------------------------
        # 🚨 IF STOP → TRIGGER LOGS
        # -----------------------------------
        if action.lower() == "stop":
            if SEND_LOGS_URL:
                threading.Thread(target=trigger_logs).start()

                result["logs_triggered"] = True
                result["logs_mode"] = "async"
            else:
                result["logs_triggered"] = False
                result["logs_error"] = "SEND_LOGS_URL not set"

        return jsonify(result), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------
# ❤️ Health Check
# -----------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# -----------------------------------
# 🚀 Run Server
# -----------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)