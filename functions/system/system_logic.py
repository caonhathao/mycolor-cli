import os
import subprocess
import sys

import psutil

try:
    import winreg
except ImportError:
    winreg = None

def get_processes():
    """Returns a list of processes sorted by CPU usage."""
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
        try:
            p_info = p.info
            # Ensure values are not None
            if p_info['cpu_percent'] is None:
                p_info['cpu_percent'] = 0.0
            if p_info['memory_percent'] is None:
                p_info['memory_percent'] = 0.0
            procs.append(p_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return sorted(procs, key=lambda p: p['cpu_percent'], reverse=True)

def terminate_process(pid):
    """Terminates a process by PID."""
    try:
        p = psutil.Process(pid)
        p.terminate()
        return True, f"Process {pid} terminated."
    except psutil.Error as e:
        return False, str(e)

def run_new_task(cmd):
    """Runs a new command/task."""
    try:
        subprocess.Popen(cmd, shell=True)
        return True, f"Started: {cmd}"
    except (subprocess.SubprocessError, OSError) as e:
        return False, str(e)

# Registry paths
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APPROVED_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"

def get_startup_apps():
    """Returns a dictionary of startup apps and their status."""
    apps = {}
    if not winreg:
        return apps

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    apps[name] = {"cmd": value, "enabled": True}
                    i += 1
                except OSError:
                    break
        
        # Check StartupApproved for disabled status
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, APPROVED_KEY, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        if name in apps and isinstance(value, bytes) and len(value) > 0:
                            # 0x02 is enabled, odd numbers usually disabled (0x03)
                            if value[0] % 2 != 0:
                                apps[name]["enabled"] = False
                        i += 1
                    except OSError:
                        break
        except OSError:
            pass # StartupApproved key might not exist
            
    except OSError:
        pass # Run key might not exist
    return apps

def set_startup_state(name, enable):
    """Enables or disables a startup app using StartupApproved key."""
    if not winreg:
        return False, "Registry access not available."
    
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, APPROVED_KEY) as key:
            # The value is a 12-byte array. The first byte determines the state.
            # 0x02 = enabled, 0x03 = disabled. The other bytes are typically zero.
            new_byte = 0x02 if enable else 0x03
            new_val = bytes([new_byte]) + b'\x00' * 11
            winreg.SetValueEx(key, name, 0, winreg.REG_BINARY, new_val)
            return True, f"Startup app '{name}' {'enabled' if enable else 'disabled'}."
    except OSError as e:
        return False, str(e)

def launch_taskmgr_window():
    """Launches the Task Manager in a new terminal window."""
    try:
        python_exe = sys.executable
        script_path = os.path.abspath("myworld.py")
        work_dir = os.getcwd()
        
        command = f'start "MYCOLOR - Task Manager" "{python_exe}" "{script_path}" --mode taskmgr'
        
        subprocess.Popen(command, shell=True, cwd=work_dir)
        return True, "Task Manager launched in a new window."
    except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
        return False, str(e)