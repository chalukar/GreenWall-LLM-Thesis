import socket
import os
import time
import json
import serial
import threading
import struct
import select
import subprocess 

# --- CONFIGURATION ---
SERVER_IP = '192.168.137.1' 
PORT = 5000
SERIAL_PORT = '/dev/ttyACM1' 
BAUD_RATE = 9600
PIR_COOLDOWN_SECONDS = 30

# Audio Settings
MIC_DEVICE = "plughw:1,0"   
# RECORD_CMD must include -N to block
RECORD_CMD = ["arecord", "-D", MIC_DEVICE, "-d", "8", "-f", "S16_LE", "-r", "16000", "-t", "wav", "-N", "input.wav"]
PLAY_CMD_LIST = ["mpg123", "-q", "response.mp3"] 

# Shared State
latest_pir_state = 0   
prev_pir_state = 1     
latest_soil_pct = 0 
is_in_session = False 
enter_key_pressed = False

def input_monitor():
    global enter_key_pressed
    print(">> Keyboard Ready. Press ENTER when asked.")
    while True:
        try:
            input() 
            if is_in_session:
                enter_key_pressed = True
                print(">> [DEBUG] Enter Captured")
        except: pass

def read_arduino():
    global latest_pir_state, latest_soil_pct
    print(">> [SENSOR] Starting Arduino Listener...")
    while True:
        try:
            if not os.path.exists(SERIAL_PORT):
                time.sleep(2)
                continue
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f">> [SENSOR] Connected to {SERIAL_PORT}")
            while True:
                if ser.in_waiting > 0:
                    try:
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        parts = line.split(';')
                        for part in parts:
                            if "PIR=" in part:
                                latest_pir_state = int(part.split('=')[1])
                            elif "SOIL_PCT=" in part:
                                latest_soil_pct = int(part.split('=')[1])
                    except: pass
        except:
            time.sleep(2)

def send_packet(sock, msg_type, file_path=None, payload=None):
    header = {"type": msg_type, "file_size": 0, "payload": payload or {}}
    if file_path and os.path.exists(file_path):
        header['file_size'] = os.path.getsize(file_path)
    try:
        header_bytes = json.dumps(header).encode('utf-8')
        sock.send(struct.pack('>I', len(header_bytes)))
        sock.send(header_bytes)
        if header['file_size'] > 0:
            with open(file_path, "rb") as f:
                sock.sendall(f.read())
    except: pass

def recvall(sock, n):
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk: return None
        data += chunk
    return data

def receive_packet(sock):
    try:
        len_bytes = recvall(sock, 4)
        if not len_bytes: return None
        header_len = struct.unpack('>I', len_bytes)[0]
        header_bytes = recvall(sock, header_len)
        if not header_bytes: return None
        header = json.loads(header_bytes.decode('utf-8'))
        
        if header.get('file_size', 0) > 0:
            file_data = recvall(sock, header['file_size'])
            if file_data:
                with open("response.mp3", "wb") as f:
                    f.write(file_data)
        return header
    except: return None

def main():
    global is_in_session, latest_pir_state, prev_pir_state, enter_key_pressed
    
    threading.Thread(target=read_arduino, daemon=True).start()
    threading.Thread(target=input_monitor, daemon=True).start()
    
    print(">> System Ready. Stabilizing Sensors...")
    time.sleep(2) 
    
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f"Connecting to {SERVER_IP}...")
            s.connect((SERVER_IP, PORT))
            print("Connected.")
            last_trigger_time = 0
            
            while True:
                ready, _, _ = select.select([s], [], [], 0.05)
                if ready:
                    msg = receive_packet(s)
                    if not msg: break 
                    cmd = msg['type']
                    print(f"[CMD] {cmd}")
                    
                    if cmd == "SPEAK_INTRO":
                        print(">> Playing Intro...")
                        subprocess.call(PLAY_CMD_LIST, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print(">> Waiting for user to press ENTER...")

                    elif cmd == "GET_SOIL":
                        print(f">> Sending Soil Data: {latest_soil_pct}%")
                        send_packet(s, "SOIL_DATA", payload={"soil": latest_soil_pct})

                    elif cmd == "SPEAK":
                        print(">> Playing audio...")
                        subprocess.call(PLAY_CMD_LIST, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        
                        # DELETE OLD FILE & RECORD NEW
                        if os.path.exists("input.wav"): os.remove("input.wav")
                        print(">> Recording 10 seconds...")
                        subprocess.call(RECORD_CMD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        
                        if os.path.exists("input.wav"):
                            print(">> Sending AUDIO...")
                            send_packet(s, "AUDIO", file_path="input.wav")
                        else:
                            print(">> Error: Mic failed to record.")

                    elif cmd == "END_SESSION":
                        print(">> Session Ended.")
                        is_in_session = False
                        prev_pir_state = 1
                        enter_key_pressed = False 

                if enter_key_pressed:
                    if is_in_session:
                        print(">> Sending USER_ENTER...")
                        send_packet(s, "USER_ENTER")
                    enter_key_pressed = False 

                current_time = time.time()
                if not is_in_session and (current_time - last_trigger_time > PIR_COOLDOWN_SECONDS):
                    if latest_pir_state == 1 and prev_pir_state == 0:
                        print(f"\n>> WAVE DETECTED!")
                        send_packet(s, "PIR_TRIGGER", payload={"soil": latest_soil_pct})
                        is_in_session = True
                        last_trigger_time = current_time
                        enter_key_pressed = False 
                    prev_pir_state = latest_pir_state

                time.sleep(0.05)
                        
        except Exception as e:
            print(f"Reconnecting... {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()