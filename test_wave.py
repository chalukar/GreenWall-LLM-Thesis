import serial
import time
import sys

# --- CONFIGURATION ---
# Try '/dev/ttyACM0' if ACM1 fails. Run "ls /dev/tty*" in terminal to check.
SERIAL_PORT = '/dev/ttyACM1' 
BAUD_RATE = 9600

def main():
    print(f"--- PIR SENSOR TEST MODE ---")
    print(f"Connecting to {SERIAL_PORT}...")

    try:
        # Open Serial Connection
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) # Wait for connection to settle
        print(">> CONNECTED. Reading sensor data...")
        print("------------------------------------------------")
        print("State:      | Raw Data:")
        print("------------------------------------------------")

        while True:
            if ser.in_waiting > 0:
                try:
                    # Read line from Arduino
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    # Check for PIR Status
                    if "PIR=1" in line:
                        print(f"MOTION   | {line}")
                    elif "PIR=0" in line:
                        print(f"NO MOVT  | {line}")
                    
                except Exception as e:
                    print(f"Error parsing: {e}")
                    
    except serial.SerialException:
        print(f"\n[ERROR] Could not open {SERIAL_PORT}.")
        print("1. Check if Arduino is plugged in.")
        print("2. Run 'ls /dev/tty*' to find the correct port (e.g., ttyACM0).")
    except KeyboardInterrupt:
        print("\nTest Finished.")

if __name__ == "__main__":
    main()