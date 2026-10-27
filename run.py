"""
DisasterShield — CLI Launcher
Quick runner script for launching DisasterShield development server.
"""

import sys
import webbrowser
from app import app

if __name__ == "__main__":
    port = 5000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"

    print("=" * 65)
    print("  DisasterShield — Disaster Management Guidance Chatbot")
    print("  Rule-Based Decision-Tree System for Emergency Guidance")
    print("=" * 65)
    print(f"[*] Server running at: {url}")
    print("[*] Verified Sources: NDMA, GSI, CWC, NDRF, Emergency 112")
    print("[*] Press Ctrl+C to terminate.")
    print("=" * 65)

    if "--open" in sys.argv:
        webbrowser.open(url)

    app.run(host=host, port=port, debug=False)
