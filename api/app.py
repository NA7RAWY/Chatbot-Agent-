from flask import Flask, render_template, request, jsonify, send_from_directory
import google.generativeai as genai
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.chat_compression import compress_chat
from markupsafe import Markup
import json
import pdfplumber
from dotenv import load_dotenv


load_dotenv()

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
#os.makedirs(UPLOAD_FOLDER, exist_ok=True)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("models/gemini-2.5-flash")

chat_history = []

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json["message"]
    compressed = compress_chat(chat_history)

    instruction = """
You are a helpful assistant.
- Do NOT use Markdown.
- Never include triple backticks.
- Return clean HTML wrapped in <div class='bot-reply'>...</div>.
"""

    prompt = instruction + "\n\n" + compressed + f"\nUser: {user_input}\nBot:"

    try:
        response = model.generate_content(prompt, generation_config={"temperature": 0.7})
        bot_reply = response.parts[0].text.strip()
    except Exception as e:
        bot_reply = f"⚠️ Error: {str(e)}"

    chat_history.append({"user": user_input, "bot": bot_reply})

    return jsonify({"response": Markup(f"<div class='bot-reply'>{bot_reply}</div>")})

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    if not file or not file.filename.endswith(".pdf"):
        return jsonify({"error": "Please upload a valid PDF file."}), 400

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    try:
        with pdfplumber.open(filepath) as pdf:
            content = "\n".join(page.extract_text() or '' for page in pdf.pages)
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/clear", methods=["POST"])
def clear_chat():
    global chat_history
    chat_history = []
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    app.run(debug=True)

app = app
