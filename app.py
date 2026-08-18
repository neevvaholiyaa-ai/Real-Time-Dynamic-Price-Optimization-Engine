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
    import webbrowser

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    url = f"http://localhost:{port}"

    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    print(f"\n" + "=" * 60)
    print(f" AuraPrice Dynamic Price Optimization Engine")
    print(f" Server running at: {url}")
    print(f" Launching application in default browser...")
    print(f"=" * 60 + "\n")

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
