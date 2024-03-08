import subprocess


def run():
    # Define the command to run your Streamlit app.
    command = ["streamlit", "run", "gpt_nexus/streamlit_ui.py"]

    # Start the Streamlit app as a subprocess.
    process = subprocess.Popen(command)

    process.wait()
