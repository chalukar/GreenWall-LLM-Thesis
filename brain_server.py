import socket
import json
import os
import struct
import time
import re
import speech_recognition as sr
import ollama 
from gtts import gTTS

# --- CONFIGURATION ---
HOST_IP = '10.32.38.101'
PORT = 5000

# --- TEXT TEMPLATES ---
BASE_INTRO = "Welcome. I am a Vertical Living Green Wall. "
PROMPT_TEXT = "Would you like to speak with me? Please press the Enter key to start."
REMINDER_TEXT = "I am still waiting. Press Enter if you wish to speak."
EXIT_TEXT = "I understand. Have a peaceful day."

# --- HELPER FUNCTIONS ---

def generate_tts(text, filename="reply.mp3"):
    # --- CLEAN THE TEXT FIRST ---
    clean_text = clean_text_for_audio(text)
    
    print(f"[TTS] Original: {text[:30]}...")
    print(f"[TTS] Speaking: {clean_text[:30]}...")
    
    try:
        # Generate audio from the CLEAN text
        tts = gTTS(text=clean_text, lang='en')
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

def transcribe_audio(file_path):
    print(">> Transcribing...")
    r = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            audio = r.record(source)
            return r.recognize_google(audio)
    except: return ""

def send_packet(conn, msg_type, file_path=None, payload=None):
    header = {"type": msg_type, "file_size": 0, "payload": payload or {}}
    if file_path and os.path.exists(file_path):
        header['file_size'] = os.path.getsize(file_path)
    
    try:
        header_bytes = json.dumps(header).encode('utf-8')
        conn.send(struct.pack('>I', len(header_bytes)))
        conn.send(header_bytes)
        if header['file_size'] > 0:
            with open(file_path, "rb") as f:
                conn.sendall(f.read())
    except Exception as e:
        print(f"Send Error: {e}")

# Robust Receiver (prevents JSON errors)
def recvall(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet: return None
        data += packet
    return data

def receive_packet(conn):
    try:
        len_bytes = recvall(conn, 4)
        if not len_bytes: return None
        header_len = struct.unpack('>I', len_bytes)[0]
        
        header_bytes = recvall(conn, header_len)
        if not header_bytes: return None
        
        header = json.loads(header_bytes.decode('utf-8'))
        
        if header.get('file_size', 0) > 0:
            print(f">> Receiving file {header['file_size']} bytes...")
            file_data = recvall(conn, header['file_size'])
            if file_data:
                with open("input.wav", "wb") as f:
                    f.write(file_data)
        return header
    except socket.timeout:
        return "TIMEOUT"
    except Exception as e:
        print(f"Receive Error: {e}")
        return None

# --- LOGIC ---

def wait_for_user_enter(conn):
    """Waits for USER_ENTER packet from Client"""
    print(">> [SERVER] Waiting for Client to press Enter...")
    
    # INCREASED TIMEOUT to 40s (Allows user to listen to long intro)
    conn.settimeout(40.0) 

    # Attempt 1
    try:
        start_time = time.time()
        while time.time() - start_time < 40:
            msg = receive_packet(conn)
            if msg == "TIMEOUT": continue
            if msg and msg.get('type') == 'USER_ENTER':
                print(">> [SERVER] User pressed Enter! Starting chat.")
                return True
    except: pass
    
    # Reminder (Using SPEAK_INTRO so client DOES NOT record)
    print(">> Timeout 1. Sending Reminder.")
    f = generate_tts(REMINDER_TEXT)
    send_packet(conn, "SPEAK_INTRO", file_path=f)
    
    # Attempt 2
    try:
        start_time = time.time()
        while time.time() - start_time < 30:
            msg = receive_packet(conn)
            if msg == "TIMEOUT": continue
            if msg and msg.get('type') == 'USER_ENTER':
                print(">> [SERVER] User pressed Enter! Starting chat.")
                return True
    except: pass

    return False

def chat_mode(conn, custom_intro=None):
    print(">> --- CHAT LOOP STARTED ---")
    system_prompt = ("You are a sentient Vertical Green Wall and you are a living, "
    "breathing plant and you are chatting with a human via voice. " 
    "Keep your responses concise and friendly. " 
    "also you can mention your need for water if your soil is dry." 
    "you can refer to yourself as a plant wall or green wall.")
    
    history = [{'role': 'system', 'content': system_prompt}]
    
    conn.settimeout(60.0) # Long timeout for conversation

    if custom_intro:
        greeting = custom_intro + " I am listening."
    else:
        greeting = "Hello! I am listening. Please speak now."

    print(f"Wall: {greeting}")
    f = generate_tts(greeting)
    send_packet(conn, "SPEAK", file_path=f) 
    history.append({'role': 'assistant', 'content': greeting})

    while True:
        print(">> Waiting for AUDIO from client...")
        msg = receive_packet(conn)
        
        if not msg: break
        if msg == "TIMEOUT":
            print(">> Timeout waiting for audio")
            break

        if msg.get('type') == 'AUDIO':
            user_text = transcribe_audio("input.wav")
            print(f"User: {user_text}")

            if not user_text:
                f = generate_tts("I didn't hear anything. Please try again.")
                send_packet(conn, "SPEAK", file_path=f)
                continue

            if any(w in user_text.lower() for w in ["bye", "stop", "exit"]):
                f = generate_tts(EXIT_TEXT)
                send_packet(conn, "SPEAK", file_path=f)
                break
            
            # Real-time Soil Check during Chat
            if any(w in user_text.lower() for w in ["soil", "moisture", "water", "status"]):
                print(">> [Logic] Checking fresh sensors...")
                send_packet(conn, "GET_SOIL")
                conn.settimeout(5.0)
                dmsg = receive_packet(conn)
                conn.settimeout(60.0)
                if dmsg and dmsg.get('type') == 'SOIL_DATA':
                    val = dmsg['payload'].get('soil', 0)
                    history.append({'role': 'system', 'content': f"SYSTEM NOTE: Current Soil Moisture is {val}%."})

            history.append({'role': 'user', 'content': user_text})
            
            try:
                response = ollama.chat(model='gemma2:2b', messages=history)
                ai_text = response['message']['content']
            except: ai_text = "I am having trouble thinking."

            print(f"Wall: {ai_text}")
            history.append({'role': 'assistant', 'content': ai_text})
            
            f = generate_tts(ai_text)
            send_packet(conn, "SPEAK", file_path=f)

def run_session(conn, initial_soil_level):
    try: current_soil = int(initial_soil_level)
    except: current_soil = 0

    is_dry = current_soil < 30
    intro_audio_text = BASE_INTRO

    # --- STEP 1: INITIAL ANALYSIS ---
    if is_dry:
        print(f">> [Logic] Soil is DRY ({current_soil}%). Asking for water.")
        intro_audio_text += f"My soil moisture is low at {current_soil} percent. It is dry. Could you please help water me? "
        intro_audio_text += PROMPT_TEXT 
    else:
        print(f">> [Logic] Soil is WET ({current_soil}%). Ready to chat.")
        intro_audio_text += f"My soil moisture is a healthy {current_soil} percent. I do not need water. "
        intro_audio_text += PROMPT_TEXT

    f = generate_tts(intro_audio_text)
    send_packet(conn, "SPEAK_INTRO", file_path=f)

    # --- STEP 2: WAIT FOR ENTER ---
    if not wait_for_user_enter(conn):
        f = generate_tts(EXIT_TEXT)
        send_packet(conn, "SPEAK_INTRO", file_path=f)
        send_packet(conn, "END_SESSION")
        return

    # --- STEP 3: RE-CHECK LOGIC ---
    custom_start_msg = ""
    
    if is_dry:
        print(">> [Logic] User pressed enter. RE-CHECKING soil status...")
        send_packet(conn, "GET_SOIL")
        
        conn.settimeout(5.0)
        new_packet = receive_packet(conn)
        conn.settimeout(60.0) 
        
        new_soil = current_soil 
        if new_packet and new_packet.get('type') == 'SOIL_DATA':
            new_soil = int(new_packet['payload'].get('soil', 0))
            print(f">> [Logic] Fresh Soil Data: {new_soil}%")
        
        if new_soil < 30:
            custom_start_msg = f"I see my soil is still dry at {new_soil} percent. Perhaps the water needs time to soak in. We can talk anyway."
        else:
            custom_start_msg = f"Thank you! I sense the water. My moisture is now {new_soil} percent. I feel much better."
    else:
        custom_start_msg = "Great. I am ready."

    # --- STEP 4: START CHAT ---
    chat_mode(conn, custom_intro=custom_start_msg)
    send_packet(conn, "END_SESSION")

def clean_text_for_audio(text):
    # 1. Remove Asterisks (often used for *actions*)
    text = text.replace("*", "")
    
    # 2. Remove Emojis and special symbols using Regex
    # This pattern keeps: Letters (a-z), Numbers (0-9), Spaces, and Punctuation (.,!?'"-)
    # It removes everything else (emojis, complex symbols).
    clean_text = re.sub(r'[^a-zA-Z0-9\s.,!("\')?-]', '', text)
    
    # 3. Remove extra whitespace
    return " ".join(clean_text.split())

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST_IP, PORT))
    server.listen(1)
    print(f"Green Wall Brain Ready on {PORT}")
    
    while True:
        try:
            conn, addr = server.accept()
            print(f"Connected: {addr}")
            while True:
                conn.settimeout(None)
                msg = receive_packet(conn)
                if not msg: break
                
                if msg != "TIMEOUT" and msg['type'] == "PIR_TRIGGER":
                    print("\n--- MOTION DETECTED ---")
                    soil_val = msg.get('payload', {}).get('soil', 0)
                    run_session(conn, soil_val)
                    print("--- END INTERACTION ---\n")
        except Exception as e:
            print(f"Connection Error: {e}")

if __name__ == "__main__":
    start_server()