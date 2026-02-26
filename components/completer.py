import os
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from functions.theme.theme_logic import THEMES


class DynamicCommandCompleter(Completer):
    def __init__(self):
        # Base commands and their flags
        self.commands = {
            "/theme": ["--style", "--list", "--help", "-h"],
            "/sysinfo": [
                "--g",
                "--cpu",
                "--ram",
                "--disk",
                "--display",
                "--input",
                "--help",
                "-h",
            ],
            "/system": [
                "--taskmgr",
                "--end-task",
                "--run-new",
                "--d",
                "--e",
                "--help",
                "--h",
            ],
            "/copy": ["--last", "--export", "--help", "-h"],
            "/help": [],
            "/quit": [],
            "/clear": [],
        }
        self.themes = list(THEMES.keys())

        # Dynamic Scan of functions directory for new commands
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            functions_dir = os.path.join(project_root, "functions")

            if os.path.exists(functions_dir):
                for item in os.listdir(functions_dir):
                    item_path = os.path.join(functions_dir, item)
                    if os.path.isdir(item_path) and not item.startswith("__"):
                        cmd = f"/{item}"
                        if cmd not in self.commands:
                            self.commands[cmd] = [
                                "--help"
                            ]  # Default flag for discovered commands
        except Exception:
            pass

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor

        # 1. Command Completion (start of line)
        if " " not in text.lstrip():
            word = text.lstrip()
            if word.startswith("/"):
                for cmd in self.commands:
                    if word in cmd:  # Fuzzy/Substring match
                        yield Completion(cmd, start_position=-len(word))
            return

        # 2. Flag/Argument Completion
        parts = text.lstrip().split()
        if not parts:
            return

        cmd = parts[0]
        if cmd in self.commands:
            current_word = parts[-1] if not text.endswith(" ") else ""

            # Context: /theme --style [theme_name]
            prev_word = (
                parts[-1]
                if text.endswith(" ")
                else (parts[-2] if len(parts) > 1 else "")
            )
            if cmd == "/theme" and prev_word == "--style":
                for theme in self.themes:
                    if current_word.lower() in theme.lower():
                        yield Completion(theme, start_position=-len(current_word))
                return

            # Suggest Flags
            if current_word.startswith("-"):
                flags = self.commands[cmd]
                for flag in flags:
                    if current_word in flag:
                        yield Completion(flag, start_position=-len(current_word))
