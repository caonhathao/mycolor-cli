import datetime
import os

from modules.tracker.history_tracker import get_history_tracker
from utils.clipboard_manager import copy_to_clipboard

DEFAULT_LOG_PATH = os.path.join(os.path.expanduser("~"), "Documents", "mycolor", "log")


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
    target_path_str = custom_path if custom_path and custom_path.strip() else DEFAULT_LOG_PATH
    target_path = os.path.abspath(target_path_str)

    # Check if the provided path is a directory or a file path
    if os.path.splitext(target_path)[1]:  # It's a file path
        full_path = target_path
        target_dir = os.path.dirname(full_path)
    else:  # It's a directory path
        target_dir = target_path
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        full_path = os.path.join(target_dir, f"session_log_{timestamp}.txt")

    success, result = ensure_log_directory(target_dir)
    if not success:
        return False, f"Failed to create log directory: {result}", None

    entries = get_history_tracker().get_entries()

    try:
        pairs = [(entry["command"], entry["result"]) for entry in entries]
        content = format_pairs_for_clipboard(pairs)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True, f"History exported successfully to: {full_path}", full_path
    except Exception as e:
        return False, f"Failed to export history: {e}", None
