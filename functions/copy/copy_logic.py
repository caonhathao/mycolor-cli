import os
import json
import datetime
from utils.clipboard_manager import copy_to_clipboard
from modules.tracker.history_tracker import get_history_tracker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

DEFAULT_LOG_PATH = os.path.join(os.path.expanduser("~"), "Documents", "mycolor", "log")


def get_default_log_path():
    """Returns the default log path from config or default."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config.get("log_export_path", DEFAULT_LOG_PATH)
    except Exception:
        pass
    return DEFAULT_LOG_PATH


def save_log_path_to_config(path):
    """Saves the log export path to config.json."""
    try:
        config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
        
        config["log_export_path"] = path
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception:
        return False


def ensure_log_directory(path):
    """Ensures the log directory exists, creates it if missing."""
    try:
        os.makedirs(path, exist_ok=True)
        return True, path
    except Exception as e:
        return False, str(e)


def format_pairs_for_clipboard(pairs):
    """Formats command-result pairs into a readable string for clipboard."""
    if not pairs:
        return ""
    
    parts = []
    for cmd, result in pairs:
        parts.append(f"> {cmd}\n{result}\n----------------------------------------")
    
    return "\n".join(parts)


def copy_last_n_pairs(n):
    """Copies the last n command-result pairs to clipboard.
    Returns (success, message).
    """
    entries = get_history_tracker().get_entries()
    
    if not entries:
        return False, "No commands found in history."

    # Pull the last N entries
    last_n_entries = entries[-n:]
    pairs = [(entry["command"], entry["result"]) for entry in last_n_entries]
    
    if not pairs:
        return False, "No commands found in buffer."
    
    formatted = format_pairs_for_clipboard(pairs)
    
    if not formatted:
        return False, "No content to copy."
    
    try:
        copy_to_clipboard(formatted)
        return True, "Copied successfully"
    except Exception as e:
        return False, f"Failed to copy to clipboard: {e}"


def export_history_to_file(custom_path=None):
    """Exports the entire history to a file.
    Returns (success, message, file_path).
    """
    target_path = custom_path if custom_path and custom_path.strip() else get_default_log_path()
    target_path = os.path.abspath(target_path)
    
    entries = get_history_tracker().get_entries()
    success, result = ensure_log_directory(target_path)
    if not success:
        return False, f"Failed to create log directory: {result}", None
    
    # Determine directory
    if os.path.splitext(target_path)[1]: # If it looks like a file path
        target_dir = os.path.dirname(target_path)
    else:
        target_dir = target_path
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    
    # Generate unique timestamped filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    full_path = os.path.join(target_dir, f"session_log_{timestamp}.txt")
    
    try:
        # Use the same formatting logic for file export
        pairs = [(entry["command"], entry["result"]) for entry in entries]
        content = format_pairs_for_clipboard(pairs)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        if custom_path and custom_path != get_default_log_path():
            save_log_path_to_config(custom_path)
        
        return True, f"History exported successfully to: {full_path}", full_path
    except Exception as e:
        return False, f"Failed to export history: {e}", None
