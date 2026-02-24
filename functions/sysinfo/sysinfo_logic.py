import psutil
import platform
import socket
import datetime
import locale
import subprocess

def run_powershell(command):
    """Executes a PowerShell command and returns a list of values."""
    try:
        # Run powershell command, suppress window creation on Windows
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Use -NoProfile to avoid loading profile scripts which might output text
        result = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True, startupinfo=startupinfo)
        lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return lines
    except Exception:
        return []

def get_general_info():
    bios = "Unknown"
    if platform.system() == "Windows":
        res = run_powershell("Get-CimInstance Win32_BIOS | Select-Object -ExpandProperty Version")
        if res: bios = res[0]
    
    lang = locale.getdefaultlocale()
    lang_str = f"{lang[0]} ({lang[1]})" if lang[0] else "Unknown"

    return {
        "Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Computer Name": socket.gethostname(),
        "OS": f"{platform.system()} {platform.release()} ({platform.version()})",
        "Language": lang_str,
        "BIOS": bios,
        "Processor": platform.processor()
    }

def get_cpu_info():
    freq = psutil.cpu_freq()
    current_freq = f"{freq.current:.2f} MHz" if freq else "Unknown"
    
    cpu_name = platform.processor()
    if platform.system() == "Windows":
        res = run_powershell("Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name")
        if res: cpu_name = res[0]

    return {
        "Processor": cpu_name,
        "Cores": psutil.cpu_count(logical=False),
        "Threads": psutil.cpu_count(logical=True),
        "Current Speed": current_freq
    }

def get_ram_info():
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    def sizeof_fmt(num, suffix="B"):
        for unit in ["", "Ki", "Mi", "Gi", "Ti"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f}{unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f}Pi{suffix}"

    return {
        "Total Memory": sizeof_fmt(vm.total),
        "Available": sizeof_fmt(vm.available),
        "Used": sizeof_fmt(vm.used),
        "Page File Used": sizeof_fmt(swap.used),
        "Page File Total": sizeof_fmt(swap.total)
    }

def get_disk_info():
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "Drive": part.device,
                "File System": part.fstype,
                "Total": f"{usage.total / (1024**3):.2f} GB",
                "Free": f"{usage.free / (1024**3):.2f} GB"
            })
        except PermissionError:
            continue
    return disks

def get_display_info():
    displays = []
    if platform.system() == "Windows":
        # Use powershell to get GPU info
        names = run_powershell("Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name")
        drivers = run_powershell("Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty DriverVersion")
        
        for i, name in enumerate(names):
            driver = drivers[i] if i < len(drivers) else "Unknown"
            displays.append({
                "Card Name": name,
                "Driver": driver
            })
    return displays

def get_input_info():
    inputs = []
    if platform.system() == "Windows":
        keyboards = run_powershell("Get-CimInstance Win32_Keyboard | Select-Object -ExpandProperty Description")
        mice = run_powershell("Get-CimInstance Win32_PointingDevice | Select-Object -ExpandProperty Description")
        for k in keyboards:
            inputs.append({"Type": "Keyboard", "Name": k})
        for m in mice:
            inputs.append({"Type": "Mouse", "Name": m})
    return inputs