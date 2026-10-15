import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    print("\n" + "="*60)
    print("  🌱 AQUASENSE AI — SMART IRRIGATION SYSTEM")
    print(f"  🚀 Server running at http://127.0.0.1:{port}")
    print(f"  🌐 Open index.html or visit http://127.0.0.1:{port}")
    print("="*60 + "\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
