import serial
import time
import sys

# Try '/dev/ttyACM0' if ACM1 fails
SERIAL_PORT = '/dev/ttyACM0' 
BAUD_RATE = 9600

print(f"--- SENSOR TEST MODE ---")
print(f"Attempting to connect to {SERIAL_PORT}...")

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) # Give connection time to settle
    print("Connected! waving hand in front of sensor...")
    print("Press Ctrl+C to exit.\n")

    while True:
        if ser.in_waiting > 0:
            try:
                # Read the raw line from Arduino
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                # Check for PIR keyword
                if "PIR=1" in line:
                    print(f"✅ MOTION DETECTED  | Raw: {line}")
                elif "PIR=0" in line:
                    print(f"❌ NO MOTION       | Raw: {line}")
                else:
                    print(f"⚠️  UNKNOWN DATA    | Raw: {line}")
                    
            except Exception as e:
                print(f"Read Error: {e}")
                
except serial.SerialException:
    print(f"\n[ERROR] Could not open {SERIAL_PORT}.")
    print("1. Check if Arduino is plugged in.")
    print("2. Try changing port to '/dev/ttyACM0' or '/dev/ttyUSB0'.")
    print("3. Make sure no other script is running (like client.py).")
except KeyboardInterrupt:
    print("\nTest finished.")