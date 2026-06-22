import os
import signal

killed = False
for proc in os.listdir('/proc'):
    if proc.isdigit():
        try:
            with open(f'/proc/{proc}/cmdline', 'r') as f:
                cmd = f.read()
                if 'uvicorn' in cmd and '8005' in cmd:
                    print(f"Killing process {proc}: {cmd}")
                    os.kill(int(proc), signal.SIGKILL)
                    killed = True
        except Exception:
            pass

if not killed:
    print("No running uvicorn process on port 8005 found.")
