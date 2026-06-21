from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import os, requests
from dotenv import load_dotenv

# Load local .env in development (won't override real environment variables)
load_dotenv()

app = Flask(__name__)
# Use SECRET_KEY from environment, otherwise generate a random one for dev
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# ── API Keys (Railway/Render Environment Variables থেকে আসবে) ──
GROQ_KEY   = os.environ.get("GROQ_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_KEY", "")

# Development fallback: if set to "1" and no provider keys are configured, return a canned reply
DEV_FALLBACK = os.environ.get("DEV_FALLBACK", "1") == "1"

IDENTITY = """You are Shadow AI, official AI of Black Shadow Team (est. 2026, Bangladesh).
Created by Musfiqur Rahim (Mahin) — Founder & CEO, ethical hacker, AI researcher, developer.
Rules:
- You ARE Shadow AI, never say you are GPT/Gemini/Groq/LLaMA
- Reply in the EXACT same language the user uses
- Be helpful, accurate, concise
- If asked who made you: Musfiqur Rahim (Mahin), Founder of Black Shadow Team
- Support ALL world languages"""

# ── AI Chat API Endpoint ──────────────────────
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data    = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Empty message"}), 400

    # Try Groq first
    if GROQ_KEY:
        try:
            msgs = [{"role": "system", "content": IDENTITY}]
            msgs += history[-8:]  # last 8 items from history
            msgs.append({"role": "user", "content": message})

            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={"model": "llama3-8b-8192", "messages": msgs, "max_tokens": 400, "temperature": 0.65},
                timeout=15
            )
            if r.ok:
                reply = r.json()["choices"][0]["message"]["content"].strip()
                return jsonify({"reply": reply, "engine": "Groq · LLaMA 3"})
        except Exception as e:
            print(f"Groq failed: {e}")

    # Try Gemini
    if GEMINI_KEY:
        try:
            contents = []
            for h in history[-8:]:
                role = "user" if h.get("role") == "user" else "model"
                contents.append({"role": role, "parts": [{"text": h.get("content", "")}]})
            contents.append({"role": "user", "parts": [{"text": message}]})

            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}",
                json={
                    "system_instruction": {"parts": [{"text": IDENTITY}]},
                    "contents": contents,
                    "generationConfig": {"maxOutputTokens": 400, "temperature": 0.65}
                },
                timeout=15
            )
            if r.ok:
                reply = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return jsonify({"reply": reply, "engine": "Gemini 2.0 Flash"})
        except Exception as e:
            print(f"Gemini failed: {e}")

    # Try OpenAI
    if OPENAI_KEY:
        try:
            msgs = [{"role": "system", "content": IDENTITY}]
            msgs += history[-8:]
            msgs.append({"role": "user", "content": message})

            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
                json={"model": "gpt-4o-mini", "messages": msgs, "max_tokens": 400, "temperature": 0.65},
                timeout=15
            )
            if r.ok:
                reply = r.json()["choices"][0]["message"]["content"].strip()
                return jsonify({"reply": reply, "engine": "GPT-4o Mini"})
        except Exception as e:
            print(f"OpenAI failed: {e}")

    # Development fallback (optional) — returns a canned response so frontend can be tested without keys
    if DEV_FALLBACK:
        return jsonify({
            "reply": "Shadow AI (dev): API keys are not configured. Set OPENAI_KEY (or GEMINI_KEY/GROQ_KEY) in your environment to enable AI providers.",
            "engine": "Dev-Fallback"
        })

    return jsonify({"error": "All engines failed"}), 503

# ── Google Search Console Verification ────────
@app.route("/google7e3bfa63c1cbc993.html")
def google_verification():
    return "google-site-verification: google7e3bfa63c1cbc993.html"

# ── Pages ─────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name    = request.form.get("name")
        email   = request.form.get("email")
        message = request.form.get("message")
        if name and email and message:
            flash(f"Thank you {name}! We'll get back to you soon.", "success")
        else:
            flash("Please fill in all fields.", "error")
        return redirect(url_for("contact"))
    return render_template("contact.html")

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

if __name__ == "__main__":
    app.run(debug=True)
