# PC Shutdown Timer (Dockerized Web App for Windows)

This project provides a local web-based timer and control panel for shutting down your Windows 11 PC. The web application runs in a Docker container, communicating with a small Python script on your host machine to safely initiate the shutdown.

## ⚠️ **Security Warning**

This project grants a Docker container the ability to trigger a shutdown of your host PC. While designed with an intermediary script for enhanced security (avoiding `--privileged` mode for the web app itself), it still involves a powerful operation.

* **Only use this project on a machine you control and trust.**
* **Do NOT expose the web interface to the internet** unless you implement robust authentication and security measures.
* The host-side script is configured to run with "highest privileges" to execute the shutdown command. Ensure its integrity.

## ✨ Features

* **Schedule Shutdown in X Minutes:** Set a timer for your PC to shut down after a specified number of minutes.
* **Schedule Shutdown at Specific Time:** Choose an exact time of day for your PC to shut down.
* **Immediate Shutdown:** Trigger an instant shutdown of your PC with a single button click.
* **Cancel Active Timer:** Stop any running shutdown schedule.
* **Web-based Interface:** Access controls conveniently from your browser.
* **Dockerized Application:** Easy deployment and isolation for the web application.

## 🚀 Prerequisites

Before you begin, ensure you have the following installed on your Windows 11 machine:

1.  **Docker Desktop:** This is essential for running Docker containers on Windows. Download from [Docker's official website](https://www.docker.com/products/docker-desktop/).
2.  **Python 3.x:** For the host-side listener script. Download from [python.org](https://www.python.org/downloads/windows/). Ensure it's added to your PATH during installation.
3.  **Git (Optional but Recommended):** For cloning this repository. Download from [git-scm.com](https://git-scm.com/download/win).

## ⚙️ Project Setup

Follow these steps to set up the project on your Windows 11 PC.

### 1. Host-Side Setup (Windows 11)

This script will run directly on your Windows PC and execute the shutdown command when signaled.

a.  **Create a Signal Directory:**
    Create a new folder on your `C:` drive:
    ```powershell
    mkdir C:\shutdown_signal
    ```

b.  **Create the Host Shutdown Listener Script:**
    Create a folder for your scripts (e.g., `C:\Scripts`) if you don't have one, and save the following Python code as `host_shutdown_listener.py` inside it.

    ```python
    # C:\Scripts\host_shutdown_listener.py
    import time
    import os
    import sys

    SIGNAL_FILE = "C:\\shutdown_signal\\shutdown_signal.txt"

    def shutdown_pc():
        print("Received shutdown signal. Shutting down PC...")
        os.system("shutdown /s /t 0")

    def main():
        print(f"Host shutdown listener started. Monitoring {SIGNAL_FILE}")
        signal_dir = os.path.dirname(SIGNAL_FILE)
        if not os.path.exists(signal_dir):
            os.makedirs(signal_dir)
            print(f"Created directory: {signal_dir}")

        if not os.path.exists(SIGNAL_FILE):
            with open(SIGNAL_FILE, "w") as f:
                f.write("0")
            print(f"Initialized signal file: {SIGNAL_FILE}")

        last_signal_value = "0"

        while True:
            try:
                with open(SIGNAL_FILE, "r") as f:
                    current_signal_value = f.read().strip()

                if current_signal_value == "1" and last_signal_value != "1":
                    shutdown_pc()
                    with open(SIGNAL_FILE, "w") as f:
                        f.write("0")
                    break
                last_signal_value = current_signal_value
            except Exception as e:
                print(f"Error in host listener: {e}")
            time.sleep(5)

    if __name__ == "__main__":
        main()
    ```

c.  **Configure Task Scheduler to Run at Startup:**
    This ensures the listener script starts automatically when your PC boots up.

    1.  Search for "Task Scheduler" in the Windows search bar and open it.
    2.  In the right-hand "Actions" pane, click **"Create Basic Task..."**.
    3.  **Name:** `PC Shutdown Listener`.
    4.  **Trigger:** Select **"When the computer starts"**.
    5.  **Action:** Select **"Start a program"**.
    6.  **Program/script:** Browse to your Python executable (e.g., `C:\Users\<YourUser>\AppData\Local\Programs\Python\Python3X\pythonw.exe`).
    7.  **Add arguments (optional):** Enter the full path to your script: `C:\Scripts\host_shutdown_listener_v1.py`.
    8.  Click **"Next"** and then **"Finish"**.
    9.  **Important: Configure Elevated Privileges.** Find your new task in the "Task Scheduler Library" (left pane). Right-click it and select "Properties."
        * On the "General" tab:
            * Select **"Run whether user is logged on or not"**.
            * Check **"Run with highest privileges"**.
            * You may be prompted for your administrator password. This is crucial for the script to execute the `shutdown` command.

### 2. Docker Application Setup

This is your web application that will run inside a Docker container.

a.  **Create Project Directory:**
    Create a main folder for your project, e.g., `D:\_MyLearnings\HomeProject\pc_shutdown`.

b.  **Create `Dockerfile`:**
    In your project directory (`D:\_MyLearnings\HomeProject\pc_shutdown`), create a file named `Dockerfile` (no extension). **Note the Python version has been updated to 3.10 to ensure compatibility with `click` library.**

    ```dockerfile
    # D:\_MyLearnings\HomeProject\pc_shutdown\Dockerfile
    FROM python:3.10-slim-buster # Updated to Python 3.10 for compatibility

    WORKDIR /app

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY . .

    EXPOSE 5000

    CMD ["python", "app.py"]
    ```

c.  **Generate `requirements.txt`:**
    In your project directory (`D:\_MyLearnings\HomeProject\pc_shutdown`), ensure you have a Python virtual environment activated (or Python globally installed) and then run:

    ```bash
    pip install Flask APScheduler # Ensure these are installed in your environment
    pip freeze > requirements.txt
    ```
    This will create the `requirements.txt` file listing your dependencies (Flask, APScheduler, and their sub-dependencies).

d.  **Create `app.py`:**
    Save the following Python code as `app.py` in your project directory.


e.  **Create `templates` Directory and `index.html`:**
    In your project directory (`D:\_MyLearnings\HomeProject\pc_shutdown`), create a sub-folder named `templates`. Inside `templates`, create `index.html`.

 

f.  **Create `docker-compose.yml`:**
    Save this file in your project directory (`D:\_MyLearnings\HomeProject\pc_shutdown`).



## 🚀 Deployment

1.  **Open PowerShell or Command Prompt:** Navigate to your project directory:
    ```powershell
    cd D:\_MyLearnings\HomeProject\pc_shutdown
    ```

2.  **Build and Run with Docker Compose:**
    This command will build your Docker image (if not already built or if Dockerfile changed) and start the container. The `--build` flag ensures a fresh build.

    ```powershell
    docker compose up -d --build
    ```

3.  **Verify Status:**
    Check that your container is running:
    ```powershell
    docker compose ps
    ```
    You should see `pc-shutdown-app` listed with an `Up` status.

## 💡 Usage

1.  **Access the Web Interface:** Open your web browser and go to `http://localhost:5000`.
2.  **Schedule a Timer:**
    * **In Minutes:** Enter the desired number of minutes in the "Shut down in (minutes)" field and click "Start Timer".
    * **At Specific Time:** Select a time using the time picker in the "Shut down at:" field and click "Schedule Time". The system will automatically schedule for today or tomorrow if the time has passed.
3.  **Immediate Shutdown:** Click the "Shut Down Now" button. You will receive a confirmation prompt.
4.  **Cancel Timer:** If a timer is active, a "Cancel Timer" button will appear under the status. Click it to stop the scheduled shutdown.

##  troubleshooting Common Issues

* **`failed to read dockerfile: open Dockerfile: no such file or directory`**: Ensure your `Dockerfile` is named exactly `Dockerfile` (no extension) and is in the same directory as `docker-compose.yml`.
* **`ERROR: No matching distribution found for click==X.Y.Z`**: This indicates a Python version mismatch. Ensure your `Dockerfile`'s `FROM` line (`FROM python:3.10-slim-buster`) matches the Python version compatible with your `requirements.txt` dependencies. Rebuild with `docker compose up -d --build`.
* **Website not accessible (e.g., `localhost:5000` is blank/error)**:
    * Verify Docker Desktop is running.
    * Check container logs: `docker compose logs -f pc_shutdown_web`. Look for Flask errors.
    * Ensure no other application is using port 5000 on your host.
* **PC doesn't shut down after signal**:
    * Verify `host_shutdown_listener.py` is running: Check Task Manager (Processes or Details tabs for `python.exe`).
    * Check Task Scheduler history for the "PC Shutdown Listener" task for errors.
    * Ensure the Task Scheduler task is configured to "Run with highest privileges".
    * Check the `C:\shutdown_signal\shutdown_signal.txt` file's content after triggering from the web app. It should change to `'1'`.
    * Verify the path `C:\shutdown_signal` is correct and accessible by both Docker and your Python host script.

## ⚙️ Future Enhancements (Ideas)

* **User Authentication:** Add login capabilities if multiple users might access the web interface.
* **Scheduled Reboot:** Add an option to reboot the PC instead of just shutting it down.
* **Confirmation Dialogs:** More explicit confirmations for shutdown actions.
* **Graceful Shutdown Messages:** Display a message on the host before shutdown.
* **Configuration File:** Allow configuring the signal file path, port, etc., via a configuration file.
* **More Robust Logging:** Implement proper logging for both the Flask app and the host script.

---


echo "# pc_auto_shutdown" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/jitzV/pc_auto_shutdown.git
git push -u origin main
…or push an existing repository from the command line
git remote add origin https://github.com/jitzV/pc_auto_shutdown.git
git branch -M main
git push -u origin main