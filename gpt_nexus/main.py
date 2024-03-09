import os
import subprocess


def run():
    # Determine the directory of the current file (e.g., the script this function is in)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    # Construct the path to streamlit_ui.py relative to this directory
    app_path = os.path.join(dir_path, "gpt_nexus", "streamlit_ui.py")

    command = ["streamlit", "run", app_path]
    process = subprocess.Popen(command)
    process.wait()
