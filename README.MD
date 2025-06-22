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
    6.  **Program/script:** Browse to your Python executable (e.g., `C:\Users\<YourUser>\AppData\Local\Programs\Python\Python3X\python.exe`).
    7.  **Add arguments (optional):** Enter the full path to your script: `C:\Scripts\host_shutdown_listener.py`.
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

    ```python
    # D:\_MyLearnings\HomeProject\pc_shutdown\app.py
    from flask import Flask, render_template, request, jsonify
    from apscheduler.schedulers.background import BackgroundScheduler
    from datetime import datetime, timedelta
    import os
    import atexit
    import time

    app = Flask(__name__)
    scheduler = BackgroundScheduler()

    SIGNAL_FILE_CONTAINER_PATH = "/host_shared/shutdown_signal.txt"

    shutdown_job = None

    def trigger_host_shutdown():
        try:
            signal_dir_container = os.path.dirname(SIGNAL_FILE_CONTAINER_PATH)
            if not os.path.exists(signal_dir_container):
                os.makedirs(signal_dir_container)
                print(f"Created container-side directory for signal: {signal_dir_container}")

            with open(SIGNAL_FILE_CONTAINER_PATH, "w") as f:
                f.write("1")
            print("Shutdown signal sent to host.")
        except Exception as e:
            print(f"Error sending shutdown signal to host: {e}")

    def clear_current_job():
        global shutdown_job
        if shutdown_job:
            try:
                scheduler.remove_job(shutdown_job.id)
                print(f"Removed previous job: {shutdown_job.id}")
            except Exception as e:
                print(f"Error removing previous job {shutdown_job.id}: {e}")
            shutdown_job = None
        try:
            if os.path.exists(SIGNAL_FILE_CONTAINER_PATH):
                with open(SIGNAL_FILE_CONTAINER_PATH, "w") as f:
                    f.write("0")
                print("Shutdown signal reset on host.")
        except Exception as e:
            print(f"Error resetting shutdown signal: {e}")

    @app.route('/')
    def index():
        global shutdown_job
        current_signal = "0"
        try:
            if os.path.exists(SIGNAL_FILE_CONTAINER_PATH):
                with open(SIGNAL_FILE_CONTAINER_PATH, "r") as f:
                    current_signal = f.read().strip()
        except Exception as e:
            print(f"Could not read signal file for display in index: {e}")

        next_run_time_str = "N/A"
        if shutdown_job and shutdown_job.next_run_time:
            next_run_time_str = shutdown_job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")

        return render_template('index.html',
                               timer_active=(shutdown_job is not None),
                               next_run_time=next_run_time_str,
                               current_signal=current_signal)

    @app.route('/start_timer', methods=['POST'])
    def start_timer():
        global shutdown_job
        clear_current_job()

        try:
            minutes = int(request.form.get('minutes', 0))
            if minutes <= 0:
                return jsonify({"status": "error", "message": "Please enter a positive number of minutes."}), 400

            run_date = datetime.now() + timedelta(minutes=minutes)
            shutdown_job = scheduler.add_job(trigger_host_shutdown, 'date', run_date=run_date)

            return jsonify({"status": "success", "message": f"Shutdown scheduled in {minutes} minutes (at {run_date.strftime('%Y-%m-%d %H:%M:%S')})."})
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid minutes value."}), 400
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to schedule timer: {e}"}), 500

    @app.route('/schedule_specific_time', methods=['POST'])
    def schedule_specific_time():
        global shutdown_job
        clear_current_job()

        try:
            time_str = request.form.get('specific_time')
            if not time_str:
                return jsonify({"status": "error", "message": "Please select a specific time."}), 400

            hour, minute = map(int, time_str.split(':'))
            target_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)

            if target_time <= datetime.now():
                target_time += timedelta(days=1)
                print(f"Target time in past, scheduling for tomorrow: {target_time}")

            shutdown_job = scheduler.add_job(trigger_host_shutdown, 'date', run_date=target_time)

            return jsonify({"status": "success", "message": f"Shutdown scheduled for {target_time.strftime('%Y-%m-%d %H:%M:%S')}."})
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid time format."}), 400
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to schedule specific time shutdown: {e}"}), 500

    @app.route('/cancel_timer', methods=['POST'])
    def cancel_timer():
        global shutdown_job
        if shutdown_job:
            clear_current_job()
            return jsonify({"status": "success", "message": "Shutdown timer cancelled."})
        return jsonify({"status": "error", "message": "No active timer to cancel."}), 400

    @app.route('/shutdown_now', methods=['POST'])
    def shutdown_now():
        global shutdown_job
        clear_current_job()
        trigger_host_shutdown()
        return jsonify({"status": "success", "message": "Immediate shutdown signal sent."})

    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000, debug=True)
    ```

e.  **Create `templates` Directory and `index.html`:**
    In your project directory (`D:\_MyLearnings\HomeProject\pc_shutdown`), create a sub-folder named `templates`. Inside `templates`, create `index.html`.

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PC Shutdown Timer</title>
        <style>
            body { font-family: sans-serif; margin: 50px; text-align: center; background-color: #f4f4f4; }
            .container { max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); background-color: white; }
            h1, h2 { color: #333; }
            hr { border: 0; height: 1px; background-color: #eee; margin: 20px 0; }
            input[type="number"], input[type="time"] { padding: 10px; margin: 10px 0; width: 120px; border: 1px solid #ccc; border-radius: 4px; }
            button { padding: 10px 20px; margin: 8px; cursor: pointer; background-color: #007bff; color: white; border: none; border-radius: 5px; font-size: 1em; transition: background-color 0.2s ease; }
            button.cancel { background-color: #dc3545; }
            button:hover { opacity: 0.9; background-color: #0056b3; }
            button.cancel:hover { background-color: #c82333; }
            #status { margin-top: 20px; padding: 15px; background-color: #e9ecef; border-radius: 5px; }
            #status p { margin: 5px 0; color: #333; }
            .current-signal { font-size: 0.9em; color: #666; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>PC Shutdown Timer</h1>

            <div id="status">
                {% if timer_active %}
                    <p><strong>Timer is active.</strong> PC will shut down at: <strong>{{ next_run_time }}</strong></p>
                    <button class="cancel" onclick="cancelTimer()">Cancel Timer</button>
                {% else %}
                    <p>No timer active.</p>
                {% endif %}
                <div class="current-signal">Internal signal status: {{ current_signal }}</div>
            </div>

            <hr>

            <h2>Schedule Shutdown in Minutes</h2>
            <form id="startTimerForm">
                <label for="minutes">Shut down in (minutes):</label>
                <input type="number" id="minutes" name="minutes" min="1" value="60">
                <br>
                <button type="submit">Start Timer</button>
            </form>

            <hr>

            <h2>Schedule Shutdown at Specific Time</h2>
            <form id="startSpecificTimeForm">
                <label for="specific_time">Shut down at:</label>
                <input type="time" id="specific_time" name="specific_time">
                <br>
                <button type="submit">Schedule Time</button>
            </form>

            <hr>

            <h2>Immediate Shutdown</h2>
            <button onclick="shutdownNow()">Shut Down Now</button>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', (event) => {
                const now = new Date();
                now.setHours(now.getHours() + 1);
                now.setMinutes(now.getMinutes());
                now.setSeconds(0);
                now.setMilliseconds(0);
                const defaultTime = now.toTimeString().split(' ')[0].substring(0, 5);
                document.getElementById('specific_time').value = defaultTime;
            });

            async function startTimer() {
                const minutes = document.getElementById('minutes').value;
                if (minutes < 1) {
                    alert("Please enter a positive number of minutes.");
                    return;
                }
                const response = await fetch('/start_timer', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({ minutes: minutes }),
                });
                const data = await response.json();
                alert(data.message);
                if (data.status === 'success') { location.reload(); }
            }

            async function startSpecificTimeTimer() {
                const specificTime = document.getElementById('specific_time').value;
                if (!specificTime) {
                    alert("Please select a specific time.");
                    return;
                }
                const response = await fetch('/schedule_specific_time', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({ specific_time: specificTime }),
                });
                const data = await response.json();
                alert(data.message);
                if (data.status === 'success') { location.reload(); }
            }

            async function cancelTimer() {
                const response = await fetch('/cancel_timer', { method: 'POST' });
                const data = await response.json();
                alert(data.message);
                if (data.status === 'success') { location.reload(); }
            }

            async function shutdownNow() {
                if (confirm("Are you sure you want to shut down your PC immediately? This cannot be undone once started.")) {
                    const response = await fetch('/shutdown_now', { method: 'POST' });
                    const data = await response.json();
                    alert(data.message);
                }
            }

            document.getElementById('startTimerForm').addEventListener('submit', function(event) {
                event.preventDefault();
                startTimer();
            });

            document.getElementById('startSpecificTimeForm').addEventListener('submit', function(event) {
                event.preventDefault();
                startSpecificTimeTimer();
            });
        </script>
    </body>
    </html>
    ```

f.  **Create `docker-compose.yml`:**
    Save this file in your project directory (`D:\_MyLearnings\HomeProject\pc_shutdown`).

    ```yaml
    # D:\_MyLearnings\HomeProject\pc_shutdown\docker-compose.yml
    version: '3.8'

    services:
      pc_shutdown_web:
        build: .
        ports:
          - "5000:5000"
        volumes:
          - C:/shutdown_signal:/host_shared # Mounts Windows path to container path
        container_name: pc-shutdown-app
        restart: unless-stopped
    ```

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