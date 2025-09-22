#!/usr/bin/env python3
"""
AirIQ Startup Script
Simple launcher that detects platform and runs appropriate version
"""

import os
import sys
import subprocess
import platform

def detect_raspberry_pi():
    """Detect if running on Raspberry Pi"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            return 'Raspberry Pi' in f.read()
    except FileNotFoundError:
        return False

def main():
    """Main startup function"""
    print("🔍 AirIQ Smart Launcher")
    print("=" * 30)
    
    # Detect platform
    is_raspberry_pi = detect_raspberry_pi()
    is_windows = platform.system() == 'Windows'
    
    print(f"Platform: {platform.system()}")
    print(f"Raspberry Pi: {'Yes' if is_raspberry_pi else 'No'}")
    
    # Choose appropriate script
    if is_raspberry_pi:
        script = "AirIQ.py"
        print("\n🎯 Running full AirIQ Monitor (Raspberry Pi mode)")
    else:
        script = "AirIQ_demo.py"
        print("\n🎮 Running AirIQ Demo (Simulation mode)")
    
    # Check if script exists
    if not os.path.exists(script):
        print(f"❌ Error: {script} not found!")
        return 1
    
    try:
        # Launch the appropriate script
        print(f"🚀 Launching {script}...")
        subprocess.run([sys.executable, script])
    except KeyboardInterrupt:
        print("\n👋 AirIQ Launcher stopped")
    except Exception as e:
        print(f"❌ Error launching {script}: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())