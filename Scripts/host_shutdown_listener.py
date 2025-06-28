# C:\Scripts\host_shutdown_listener.py
import time
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import subprocess

# Define the path to the signal file on your Windows C: drive.
# This must match the volume mount target from the Docker container.
SIGNAL_FILE = "C:\\shutdown_signal\\shutdown_signal.txt"

def shutdown_pc():
    """Executes the Windows shutdown command."""
    print("Received shutdown signal. Shutting down PC...")
    # /s for shutdown, /t 0 for immediate shutdown.
    os.system("shutdown /s /f /t 0")

def main():
    print(f"\nHost shutdown listener checking. Monitoring {SIGNAL_FILE}")

    est = ZoneInfo("America/New_York")
    current_time = datetime.now(est) + timedelta(minutes=1)
    print(f"\nCurrent Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

    #Get-ScheduledTaskInfo -TaskName "PC Shutdown Listener" | Select-Object -ExpandProperty NextRunTime

    task_name = "PC Shutdown Listener"
    command = f'powershell -Command "Get-ScheduledTaskInfo -TaskName \'{task_name}\' | Select-Object -ExpandProperty NextRunTime"'
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        #print("Next Run Time:", result.stdout.strip())
        pass
    else:
        print("Error:", result.stderr)

    formattimestamp = result.stdout.strip()
    # Parse the input string
    dt = datetime.strptime(formattimestamp, "%A, %B %d, %Y %I:%M:%S %p")
    # Format to desired output
    output_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    print("\nNext Scheduled Task Run Time:", output_str)


    # Ensure the signal directory exists
    signal_dir = os.path.dirname(SIGNAL_FILE)
    if not os.path.exists(signal_dir):
        os.makedirs(signal_dir)
        print(f"Created directory: {signal_dir}")

    # Create or initialize the signal file if it doesn't exist
    if not os.path.exists(SIGNAL_FILE):
        with open(SIGNAL_FILE, "w") as f:
            f.write("0") # '0' means no shutdown signal, '1' means initiate shutdown
        print(f"Initialized signal file: {SIGNAL_FILE}")

    last_signal_value = "0" # Keep track of the last read value to detect changes

    try:
        # Read the current signal value
        with open(SIGNAL_FILE, "r") as f:
            current_signal_value = f.read().strip()
            # Check if a shutdown signal ('1') has been received and it's a new signal
            if current_signal_value == "1" and last_signal_value != "1":
                shutdown_pc()
                # After initiating shutdown, reset the signal file to '0'
                # This prevents immediate re-shutdown if the script somehow restarts quickly.
                # Note: The script might terminate before this write completes if shutdown is too fast.
                with open(SIGNAL_FILE, "w") as f:
                    f.write("0")
            else:
                # Print static part of the message
                print(f"\nNo shutdown signal detected. Current signal value: {current_signal_value}. Exiting in: ", end='')

                # Countdown timer that only updates the seconds
                for i in range(1, 0, -1):
                    print(f"\rNo shutdown signal detected. Current signal value: {current_signal_value}. Exiting in: {i} seconds remaining... ", end='')
                    time.sleep(1)
            last_signal_value = current_signal_value
    except Exception as e:
            print(f"Error in host listener: {e}")
    #time.sleep(1) # Check the file every 10 seconds

if __name__ == "__main__":
    main()