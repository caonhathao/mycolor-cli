class HistoryTracker:
    """Stores command-result pairs in structured format, separate from UI rendering."""
    
    def __init__(self):
        self.history = []  # List of dicts: [{"command": str, "result": str}]
        self.is_capturing = False
    
    def start_new_entry(self, command_text):
        """Called when a user presses Enter in the input area."""
        """Pre-filter /copy commands and prepare for result stream."""
        clean_cmd = command_text.strip()
        if clean_cmd.startswith('/copy'):
            self.is_capturing = False
            return
        
        self.is_capturing = True
        # Ensure we always have a clean string to append to
        self.history.append({"command": clean_cmd, "result": ""})
        # Limit history to 10 entries for memory efficiency
        if len(self.history) > 10:
            self.history.pop(0)
    
    def append_result(self, text):
        """Crucial: Ensure text is appended with its original newlines."""
        if self.is_capturing and self.history:
            # Append raw text exactly as received from the system stream
            self.history[-1]["result"] += text

    def get_entries(self):
        return self.history


# Global instance
_history_tracker = HistoryTracker()


def get_history_tracker():
    """Return the global HistoryTracker instance."""
    return _history_tracker
