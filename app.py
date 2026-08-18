"""
Application Entry Point forwarding to backend.main:app.
Enables running either `uvicorn app:app` or `uvicorn backend.main:app`.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.main import app

if __name__ == "__main__":
    import uvicorn
    import threading
    import time
    import urllib.request
    import webbrowser

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    url = f"http://localhost:{port}"

    def wait_and_open_browser():
        health_url = f"http://127.0.0.1:{port}/health"
        max_attempts = 30
        for _ in range(max_attempts):
            try:
                with urllib.request.urlopen(health_url, timeout=1) as response:
                    if response.status == 200:
                        break
            except Exception:
                time.sleep(0.5)
        time.sleep(0.2)
        try:
            print(f"[AuraPrice] Opening browser at {url}...")
            webbrowser.open(url)
        except Exception as e:
            print(f"[AuraPrice] Could not launch browser automatically: {e}")

    print(f"\n" + "=" * 60)
    print(f"  AuraPrice Dynamic Price Optimization Engine")
    print(f"  Server URL: {url}")
    print(f"  API Docs:   {url}/docs")
    print(f"  Health:     {url}/health")
    print(f"  Launching application in default browser once ready...")
    print(f"=" * 60 + "\n")

    threading.Thread(target=wait_and_open_browser, daemon=True).start()
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)

