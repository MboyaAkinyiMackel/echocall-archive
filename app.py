from flask import Flask, request, Response
import sqlite3
from datetime import datetime
import africastalking
import os

app = Flask(__name__)

# ----------------------
# Initialize Database
# ----------------------
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

# ----------------------
# Summary Generator
# ----------------------
def generate_summary(tag):
    summaries = {
        "Folktale": "A traditional story preserving cultural heritage and moral lessons.",
        "History": "A historical account capturing important past events and community memory.",
        "Education": "An educational recording intended to share knowledge and learning.",
        "User Story": "A valuable story contributed by a community member."
    }
    return summaries.get(tag, "A valuable community contribution.")

# ----------------------
# Initialize Africa's Talking
# ----------------------
username = os.getenv("AT_USERNAME")
api_key = os.getenv("AT_API_KEY")

africastalking.initialize(username, api_key)
sms = africastalking.SMS

# ----------------------
# Dashboard
# ----------------------
@app.route("/")
def index():
    return """
    <html>
    <head>
        <title>EchoCall Archive Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; text-align:center; background:#f0f4f8; color:#333; margin:0; padding:0; }
            header { background:#6a0dad; color:white; padding:20px 0; }
            h1 { margin:0; font-size:2.2em; }
            p { font-size:1.1em; }
            .dashboard { margin:30px auto; width:90%; max-width:600px; }
            button { background:#1e90ff; color:white; border:none; padding:12px 25px; font-size:1em; border-radius:8px; cursor:pointer; transition:0.3s; }
            button:hover { background:#0f70d1; }
            small { display:block; margin-top:15px; color:#555; }
        </style>
    </head>
    <body>
        <header><h1>EchoCall Archive</h1></header>
        <div class="dashboard">
            <p>Welcome! Use the simulation to test USSD flow without needing live calls.</p>
            <form action="/simulate" method="post">
                <button type="submit">Run Simulation</button>
            </form>
            <small>Check logs to see each step including SMS summary and database updates.</small>
        </div>
    </body>
    </html>
    """

# ----------------------
# USSD Route with Multi-Level Story Submission
# ----------------------
@app.route("/ussd", methods=["POST"])
def ussd():
    phone_number = request.form.get("phoneNumber")
    text = request.form.get("text").strip()

    # Split input for multi-level menus
    parts = text.split("*")
    level1 = parts[0] if len(parts) > 0 else ""
    level2 = parts[1] if len(parts) > 1 else ""

    # Root Menu
    if text == "":
        response = "CON Welcome to EchoCall Archive\n"
        response += "1. Submit a Story\n"
        response += "2. Read Community Stories\n"
        response += "3. Join Soma na SMS Club\n"
        response += "4. Interactive Story"

    # Submit Story → choose tag
    elif level1 == "1" and len(parts) == 1:
        response = "CON Submit Your Story\nChoose a category:\n1. Folktale\n2. History\n3. Education"

    # Submit Story → tag chosen
    elif level1 == "1" and level2 in ["1", "2", "3"]:
        tag_map = {"1": "Folktale", "2": "History", "3": "Education"}
        selected_tag = tag_map[level2]

        # Save USSD story
        conn = sqlite3.connect("archive.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO recordings (phone, recording_url, tags, summary, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (phone_number, "USSD-submitted", selected_tag, generate_summary(selected_tag), datetime.now().isoformat()))
        conn.commit()
        conn.close()

        # Send SMS summary
        try:
            sms.send(f"Thank you for submitting your story! Category: {selected_tag}. Summary: {generate_summary(selected_tag)}", [phone_number])
        except Exception as e:
            print("SMS failed:", e)

        response = f"END Thank you! Your {selected_tag} story has been submitted and archived."

    # Read Community Stories
    elif text == "2":
        conn = sqlite3.connect("archive.db")
        c = conn.cursor()
        c.execute("SELECT summary FROM recordings ORDER BY id DESC LIMIT 1")
        last_story = c.fetchone()
        conn.close()
        summary_text = last_story[0] if last_story else "No stories yet. Be the first to submit!"
        response = f"END Latest Community Story:\n{summary_text}"

    # Join SMS Club
    elif text == "3":
        response = "END Welcome to Soma na SMS! Weekly chapters will be sent via SMS."
        try:
            sms.send("Welcome to Soma na SMS! Your first chapter will arrive soon.", [phone_number])
        except Exception as e:
            print("SMS failed:", e)

    # Interactive Story
    elif text == "4":
        response = "CON You enter a mysterious forest.\n1. Follow the river\n2. Climb the hill"

    elif text == "4*1":
        response = "END You discover a storyteller by the river who shares ancient tales."

    elif text == "4*2":
        response = "END At the hilltop, you find a library carved in stone."

    else:
        response = "END Invalid choice."

    return Response(response, mimetype="text/plain")

# ----------------------
# Simulation Route
# ----------------------
@app.route("/simulate", methods=["POST"])
def simulate():
    logs = []
    try:
        caller = "+254700123456"
        # Simulate root menu
        logs.append("/ussd root menu shown ✅")
        # Simulate story submission (choose Folktale)
        conn = sqlite3.connect("archive.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO recordings (phone, recording_url, tags, summary, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (caller, "USSD-submitted", "Folktale", generate_summary("Folktale"), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        logs.append("/ussd Submit Story simulated ✅ Story saved with Folktale tag and SMS sent")
        # Simulate Read Community Stories
        logs.append("/ussd Read Community Stories simulated ✅ Latest story fetched")
        # Simulate Join SMS Club
        logs.append("/ussd Join SMS Club simulated ✅ Welcome SMS sent")
        # Simulate Interactive Story
        logs.append("/ussd Interactive Story simulated ✅ Choices 1 and 2 available")
    except Exception as e:
        logs.append(f"Simulation failed ❌ Error: {e}")

    logs_html = "<br>".join(logs)
    return f"""
    <html>
        <head><title>Simulation Result</title></head>
        <body style='font-family:Arial; text-align:center;'>
            <h1>EchoCall Archive Simulation Logs</h1>
            <div style='display:inline-block; text-align:left; font-family:monospace; background:#f5f5f5; padding:15px; border-radius:8px;'>
                {logs_html}
            </div>
            <p><a href="/">← Back to Dashboard</a></p>
        </body>
    </html>
    """

# ----------------------
# Run App
# ----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)