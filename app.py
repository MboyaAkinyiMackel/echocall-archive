from flask import Flask, request, Response
import sqlite3
from datetime import datetime
import africastalking

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
username = "sandbox"  # change later
api_key = "YOUR_API_KEY"

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)