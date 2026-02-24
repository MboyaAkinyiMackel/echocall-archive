from flask import Flask, request, Response
import sqlite3
from datetime import datetime
import africastalking
import os

import requests

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("archive.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            recording_url TEXT,
            tags TEXT,
            summary TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

def generate_summary(tag):
    summaries = {
        "Folktale": "A traditional story preserving cultural heritage and moral lessons.",
        "History": "A historical account capturing important past events and community memory.",
        "Education": "An educational recording intended to share knowledge and learning."
    }

    return summaries.get(tag, "A valuable community contribution.")

@app.route("/")
def index():
    return """
    <html>
    <head>
        <title>EchoCall Archive Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                background: #f0f4f8;
                color: #333;
                margin: 0;
                padding: 0;
            }
            header {
                background: #6a0dad;
                color: white;
                padding: 20px 0;
            }
            h1 {
                margin: 0;
                font-size: 2.2em;
            }
            p {
                font-size: 1.1em;
            }
            .dashboard {
                margin: 30px auto;
                width: 90%;
                max-width: 600px;
            }
            button {
                background: #1e90ff;
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 1em;
                border-radius: 8px;
                cursor: pointer;
                transition: 0.3s;
            }
            button:hover {
                background: #0f70d1;
            }
            small {
                display: block;
                margin-top: 15px;
                color: #555;
            }
        </style>
    </head>
    <body>
        <header>
            <h1>EchoCall Archive</h1>
        </header>
        <div class="dashboard">
            <p>Welcome! Use the simulation to test the call flow without needing Africa's Talking live calls.</p>
            <form action="/simulate" method="post">
                <button type="submit">Run Simulation</button>
            </form>
            <small>Check the logs to see each step of the simulated call, including SMS summary and tagging.</small>
        </div>
    </body>
    </html>
    """

@app.route("/voice", methods=["POST"])
def voice():
    response = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say>Welcome to EchoCall Archive.</Say>
        <GetDigits action="/menu" method="POST" timeout="10">
            <Say>Press 1 to listen to archived stories. Press 2 to record your own story.</Say>
        </GetDigits>
    </Response>
    """
    return Response(response, mimetype="text/xml")


@app.route("/menu", methods=["POST"])
def menu():
    digits = request.form.get("dtmfDigits")

    if digits == "1":
        response = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>Here is a sample story from our archive.</Say>
            <Play>https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3</Play>
        </Response>
        """
    elif digits == "2":
        response = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say>Please record your story after the beep.</Say>
        <Record action="/tag-menu" method="POST" maxLength="60"/>
    </Response>
    """
    else:
        response = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>Invalid input. Goodbye.</Say>
        </Response>
        """

    return Response(response, mimetype="text/xml")

@app.route("/tag-menu", methods=["POST"])
def tag_menu():
    recording_url = request.form.get("recordingUrl")
    caller = request.form.get("callerNumber")

    # Temporarily store in session-like variables (simple version)
    response = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <GetDigits action="/save-recording?recording_url={recording_url}&caller={caller}" method="POST">
            <Say>Press 1 for Folktale. Press 2 for History. Press 3 for Education.</Say>
        </GetDigits>
    </Response>
    """
    return Response(response, mimetype="text/xml")

# Initialize AT
username = os.getenv("AT_USERNAME")
api_key = os.getenv("AT_API_KEY")

africastalking.initialize(username, api_key)
sms = africastalking.SMS


@app.route("/save-recording", methods=["POST"])
def save_recording():
    tag_digit = request.form.get("dtmfDigits")
    recording_url = request.args.get("recording_url")
    phone = request.args.get("caller")

    tag_map = {
        "1": "Folktale",
        "2": "History",
        "3": "Education"
    }

    selected_tag = tag_map.get(tag_digit, "Uncategorized")

    summary = generate_summary(selected_tag)

    conn = sqlite3.connect("archive.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO recordings (phone, recording_url, tags, summary, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (phone, recording_url, selected_tag, summary, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    # Send SMS
    try:
        sms.send(
            f"Your story was saved under {selected_tag}. Summary: {summary}",
            [phone]
        )
    except Exception as e:
        print("SMS failed:", e)

    response = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say>Thank you. Your story has been categorized and archived.</Say>
    </Response>
    """

    return Response(response, mimetype="text/xml")

@app.route("/simulate", methods=["POST"])
def simulate():
    """Run a full call flow simulation and show logs on-page."""
    logs = []

    try:
        # Simulated caller info
        caller = "+254700123456"
        fake_recording_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"

        # Step 1: /voice
        voice_resp = app.test_client().post("/voice")
        logs.append(f"/voice response: {voice_resp.data.decode()[:150]}...")

        # Step 2: /menu (simulate record)
        menu_resp = app.test_client().post("/menu", data={"dtmfDigits": "2"})
        logs.append(f"/menu response: {menu_resp.data.decode()[:150]}...")

        # Step 3: /tag-menu
        tag_resp = app.test_client().post("/tag-menu", data={
            "recordingUrl": fake_recording_url,
            "callerNumber": caller
        })
        logs.append(f"/tag-menu response: {tag_resp.data.decode()[:150]}...")

        # Step 4: /save-recording (choose History tag)
        save_resp = app.test_client().post("/save-recording",
                                           data={"dtmfDigits": "2"},
                                           query_string={"recording_url": fake_recording_url, "caller": caller})
        logs.append(f"/save-recording response: {save_resp.data.decode()[:150]}...")

        logs.append("Simulation complete ✅ Recording saved, tag applied, SMS summary sent (simulated).")

    except Exception as e:
        logs.append(f"Simulation failed ❌ Error: {e}")

    # Return logs on webpage
    logs_html = "<br>".join(logs)
    return f"""
    <html>
        <head>
            <title>Simulation Result</title>
        </head>
        <body style='font-family:Arial; text-align:center;'>
            <h1>EchoCall Archive Simulation Logs</h1>
            <div style='display:inline-block; text-align:left; font-family:monospace; background:#f5f5f5; padding:15px; border-radius:8px;'>
                {logs_html}
            </div>
            <p><a href="/">← Back to Dashboard</a></p>
        </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)