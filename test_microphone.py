#!/usr/bin/env python3
"""
Microphone Test Script for Raspberry Pi
This script helps you test if your microphone is properly configured.
"""

import os
import subprocess
import time

# Audio Settings (same as in pi_greenwall_client.py)
MIC_DEVICE = "plughw:2,0"
TEST_DURATION = 3  # seconds

print("=" * 50)
print("MICROPHONE TEST SCRIPT")
print("=" * 50)

# Step 1: List available audio devices
print("\n[1] Listing available audio devices...")
print("-" * 50)
os.system("arecord -l")

# Step 2: Test recording
print(f"\n[2] Testing microphone: {MIC_DEVICE}")
print(f"Recording for {TEST_DURATION} seconds...")
print("Please speak into the microphone!")
print("-" * 50)

record_cmd = f"arecord -D {MIC_DEVICE} -d {TEST_DURATION} -f S16_LE -r 16000 -t wav test_recording.wav"
result = os.system(record_cmd)

if result == 0:
    print("\n✓ Recording completed successfully!")
    
    # Check if file was created
    if os.path.exists("test_recording.wav"):
        file_size = os.path.getsize("test_recording.wav")
        print(f"✓ File created: test_recording.wav ({file_size} bytes)")
        
        if file_size > 1000:  # At least 1KB
            print("✓ File size looks good!")
            
            # Step 3: Play back the recording
            print("\n[3] Playing back your recording...")
            print("(If you have speakers/headphones connected)")
            print("-" * 50)
            playback_cmd = "aplay test_recording.wav"
            os.system(playback_cmd)
            
            print("\n" + "=" * 50)
            print("TEST COMPLETE!")
            print("=" * 50)
            print("\nDid you hear your voice played back?")
            print("  YES → Microphone is working! ✓")
            print("  NO  → Check speaker/audio output settings")
        else:
            print("✗ File is too small - microphone may not be recording")
            print("  Try a different device (check 'arecord -l' output above)")
    else:
        print("✗ Recording file was not created")
        print("  The microphone device may be incorrect")
else:
    print("\n✗ Recording failed!")
    print(f"  Error code: {result}")
    print("\nTroubleshooting:")
    print("1. Check if the microphone is connected")
    print("2. Try a different device from the list above")
    print("3. Update MIC_DEVICE in pi_greenwall_client.py")
    print("\nExample devices:")
    print("  - plughw:0,0  (first device)")
    print("  - plughw:1,0  (second device)")
    print("  - plughw:2,0  (third device)")

print("\n" + "=" * 50)
