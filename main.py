import subprocess
import sys
import os

if __name__ == "__main__":
    # Get the absolute path to the app file
    app_path = os.path.join(os.path.dirname(__file__), "frontend", "app.py")
    
    # Run streamlit using subprocess
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])
