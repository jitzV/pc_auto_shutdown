from win10toast import ToastNotifier
import time
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import subprocess

SIGNAL_FILE = "C:\\shutdown_signal\\shutdown_signal.txt"
toaster = ToastNotifier()

def shutdown_pc():
    toaster.show_toast("Shutdown Initiated", "Received shutdown signal. PC will shutdown now.", duration=10)
    os.system("shutdown /s /f /t 0")

def main():
    est = ZoneInfo("America/New_York")
    current_time = datetime.now(est) + timedelta(minutes=1)

    task_name = "PC Shutdown Listener"
    command = f'powershell -Command "Get-ScheduledTaskInfo -TaskName \'{task_name}\' | Select-Object -ExpandProperty NextRunTime"'
    result = subprocess.run(command, capture_output=True, text=True, shell=True)

    if result.returncode == 0:
        formattimestamp = result.stdout.strip()
        try:
            dt = datetime.strptime(formattimestamp, "%A, %B %d, %Y %I:%M:%S %p")
            output_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            output_str = "Unavailable"
    else:
        output_str = "Unavailable"

    if not os.path.exists(os.path.dirname(SIGNAL_FILE)):
        os.makedirs(os.path.dirname(SIGNAL_FILE))

    if not os.path.exists(SIGNAL_FILE):
        with open(SIGNAL_FILE, "w") as f:
            f.write("0")

    with open(SIGNAL_FILE, "r") as f:
        current_signal_value = f.read().strip()

    if current_signal_value == "1":
        shutdown_pc()
        with open(SIGNAL_FILE, "w") as f:
            f.write("0")
    else:
        toaster.show_toast("Shutdown Listener", f"No shutdown signal detected.\nNext Scheduled Run: {output_str}", duration=10)

if __name__ == "__main__":
    main()