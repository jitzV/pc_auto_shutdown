import subprocess

#Get-ScheduledTaskInfo -TaskName "PC Shutdown Listener" | Select-Object -ExpandProperty NextRunTime

task_name = "PC Shutdown Listener"
command = f'powershell -Command "Get-ScheduledTaskInfo -TaskName \'{task_name}\' | Select-Object -ExpandProperty NextRunTime"'

result = subprocess.run(command, capture_output=True, text=True, shell=True)

if result.returncode == 0:
    formattimestamp = result.stdout.strip()
    print("Formatted Time:", formattimestamp)
    print("Next Run Time:", result.stdout.strip())
else:
    print("Error:", result.stderr)
