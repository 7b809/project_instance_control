from flask import Flask, request, jsonify, send_file
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_URL = os.getenv("API_URL")

app = Flask(__name__)


# -------------------------------
# 🏠 Serve HTML Page
# -------------------------------
@app.route("/", methods=["GET"])
def index():
    return send_file("templates/index.html")


# -------------------------------
# 🔁 Proxy API Request
# -------------------------------
@app.route("/api/control", methods=["POST"])
def control():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON received"}), 400

        action = data.get("action")

        if not action:
            return jsonify({"error": "Missing 'action'"}), 400

        # Forward request to external API
        response = requests.post(API_URL, json={"action": action})

        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------
# 🚀 Run Server
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)