"""
AdForge AI — Ngrok Public Deployment Script
============================================
Run this in a SECOND terminal while app.py is already running.
It creates a secure public tunnel to your local Flask server
so anyone can access AdForge AI from any device or browser.

Usage:
    1. Terminal 1: python app.py          (keep this running)
    2. Terminal 2: python ngrok_start.py  (run this)

Requirements:
    pip install pyngrok
"""

import time
import sys

try:
    from pyngrok import ngrok, conf
except ImportError:
    print("\n❌ pyngrok is not installed.")
    print("   Run: pip install pyngrok")
    print("   Then try again.\n")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOCAL_PORT  = 5000          # Must match the port in app.py
REGION      = "us"          # Options: us, eu, ap, au, sa, jp, in

# Optional: Set your ngrok authtoken for a stable URL (free at ngrok.com)
# If left empty, a random URL is generated each time.
NGROK_AUTH_TOKEN = ""       # e.g. "2abc123XYZ_yourTokenHere"

# ---------------------------------------------------------------------------
# Start tunnel
# ---------------------------------------------------------------------------

def start_tunnel():
    print("\n" + "="*55)
    print("  AdForge AI — Ngrok Public Deployment")
    print("="*55)

    # Set authtoken if provided
    if NGROK_AUTH_TOKEN:
        conf.get_default().auth_token = NGROK_AUTH_TOKEN
        print(f"  ✅ Auth token configured")

    print(f"  🔌 Connecting to local server on port {LOCAL_PORT}...")

    try:
        # Open HTTP tunnel to local Flask server
        tunnel = ngrok.connect(LOCAL_PORT, "http")
        public_url = tunnel.public_url

        # Force HTTPS
        if public_url.startswith("http://"):
            public_url = public_url.replace("http://", "https://", 1)

        print("\n" + "="*55)
        print("  🚀 AdForge AI is now PUBLIC!")
        print("="*55)
        print(f"\n  🌐 Public URL:  {public_url}")
        print(f"  🏠 Local URL:   http://localhost:{LOCAL_PORT}")
        print("\n  Share the Public URL with anyone.")
        print("  They can access AdForge AI from any device.\n")
        print("  Pages available:")
        print(f"    {public_url}/             → Ad Generator")
        print(f"    {public_url}/how-it-works → How It Works")
        print(f"    {public_url}/about        → About")
        print("\n" + "="*55)
        print("  Press Ctrl+C to stop the tunnel")
        print("="*55 + "\n")

        # Keep the tunnel alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n  🛑 Stopping ngrok tunnel...")
            ngrok.kill()
            print("  ✅ Tunnel closed. App is no longer public.\n")

    except Exception as e:
        print(f"\n❌ Error starting ngrok: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure app.py is running in another terminal")
        print("  2. Check your internet connection")
        print("  3. Try: pip install --upgrade pyngrok\n")
        sys.exit(1)


if __name__ == "__main__":
    start_tunnel()
