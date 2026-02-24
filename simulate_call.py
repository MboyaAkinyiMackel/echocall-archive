import requests

# Base URL of your Flask app (local or Render)
BASE_URL = "https://echocall-archive.onrender.com"  # change if local e.g., http://127.0.0.1:5000

# Simulated caller number
CALLER = "+254700123456"

def simulate_call():
    print("=== Simulating call to /voice ===")
    voice_resp = requests.post(f"{BASE_URL}/voice")
    print(voice_resp.text)
    
    # Choose menu option (1 = listen, 2 = record)
    menu_choice = input("Choose menu option (1=listen, 2=record): ")
    print(f"=== Sending choice {menu_choice} to /menu ===")
    menu_resp = requests.post(f"{BASE_URL}/menu", data={"dtmfDigits": menu_choice})
    print(menu_resp.text)
    
    if menu_choice == "2":
        # Simulate recording (we use a placeholder URL)
        fake_recording_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
        print(f"=== Sending recording to /tag-menu ===")
        tag_resp = requests.post(f"{BASE_URL}/tag-menu", data={
            "recordingUrl": fake_recording_url,
            "callerNumber": CALLER
        })
        print(tag_resp.text)
        
        # Choose tag
        tag_choice = input("Choose tag (1=Folktale, 2=History, 3=Education): ")
        print(f"=== Sending tag {tag_choice} to /save-recording ===")
        save_resp = requests.post(f"{BASE_URL}/save-recording", data={"dtmfDigits": tag_choice}, 
                                  params={"recording_url": fake_recording_url, "caller": CALLER})
        print(save_resp.text)
        print("=== Simulation complete! Check DB and logs for SMS summary ===")
    else:
        print("=== Listen path chosen. Simulation complete. ===")

if __name__ == "__main__":
    simulate_call()