# app.py
from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import atexit
import time

app = Flask(__name__)
scheduler = BackgroundScheduler()

# Define the path to the signal file *within the container*.
SIGNAL_FILE_CONTAINER_PATH = "/host_shared/shutdown_signal.txt"

shutdown_job = None # This will hold the currently active APScheduler job

def trigger_host_shutdown():
    """Writes to the shared file to signal the host listener to shut down."""
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

# Helper function to clear existing job before scheduling a new one
def clear_current_job():
    global shutdown_job
    if shutdown_job:
        try:
            scheduler.remove_job(shutdown_job.id)
            print(f"Removed previous job: {shutdown_job.id}")
        except Exception as e:
            print(f"Error removing previous job {shutdown_job.id}: {e}")
        shutdown_job = None
    # Always reset the signal file when a new job is set or cancelled
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
    clear_current_job() # Clear any existing job

    try:
        est = ZoneInfo("America/New_York")
        minutes = int(request.form.get('minutes', 0))
        if minutes <= 0:
            return jsonify({"status": "error", "message": "Please enter a positive number of minutes."}), 400

        run_date = datetime.now(est) + timedelta(minutes=minutes)
        shutdown_job = scheduler.add_job(trigger_host_shutdown, 'date', run_date=run_date)

        return jsonify({"status": "success", "message": f"Shutdown scheduled in {minutes} minutes (at {run_date.strftime('%Y-%m-%d %H:%M:%S')})."})
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid minutes value."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to schedule timer: {e}"}), 500

@app.route('/schedule_specific_time', methods=['POST'])
def schedule_specific_time():
    global shutdown_job
    clear_current_job() # Clear any existing job

    try:
        est = ZoneInfo("America/New_York")
        time_str = request.form.get('specific_time') # e.g., "14:30"
        if not time_str:
            return jsonify({"status": "error", "message": "Please select a specific time."}), 400

        # Parse hour and minute from the time string
        hour, minute = map(int, time_str.split(':'))

        # Create a datetime object for the target time today
        target_time = datetime.now(est).replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If the target time is in the past for today, schedule it for tomorrow
        if target_time <= datetime.now(est):
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
        clear_current_job() # This function already resets signal file
        return jsonify({"status": "success", "message": "Shutdown timer cancelled."})
    return jsonify({"status": "error", "message": "No active timer to cancel."}), 400

@app.route('/shutdown_now', methods=['POST'])
def shutdown_now():
    global shutdown_job
    clear_current_job() # Clear any active timer and reset signal file
    trigger_host_shutdown() # Trigger immediate shutdown
    return jsonify({"status": "success", "message": "Immediate shutdown signal sent."})


# Start the APScheduler when the Flask app starts
scheduler.start()

# Register a cleanup function to stop the scheduler when the app exits
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

est = ZoneInfo("America/New_York")
shutdown_time = datetime.now(est) + timedelta(minutes=1)
print(f"PC will shut down at: {shutdown_time.strftime('%Y-%m-%d %H:%M:%S')}")