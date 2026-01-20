import sys
import os

if __name__ == "__main__":
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(base_path, "backend", "app.py")

    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.headless=true",
    ]
    raise SystemExit(stcli.main())
