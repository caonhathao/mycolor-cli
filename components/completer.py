import os

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

from functions.theme.theme_logic import THEMES


class DynamicCommandCompleter(Completer):
    def __init__(self):
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
                "--kill",
                "--run-new",
                "--d",
                "--e",
                "--help",
                "-h",
            ],
            "/copy": ["--last", "--export", "--help", "-h"],
            "/help": [],
            "/quit": [],
            "/clear": [],
        }
        self.themes = list(THEMES.keys())

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
                            self.commands[cmd] = ["--help", "-h"]
        except OSError:
            pass

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        text_stripped = text.lstrip()

        if not text_stripped:
            return

        if " " not in text_stripped:
            word = text_stripped
            if word.startswith("/"):
                word_lower = word.lower()
                for cmd in sorted(self.commands.keys()):
                    if cmd.startswith(word_lower):
                        yield Completion(cmd, start_position=-len(word))
            return

        parts = text_stripped.split()
        if not parts:
            return

        cmd = parts[0]
        if cmd not in self.commands:
            return

        current_word = parts[-1] if not text_stripped.endswith(" ") else ""

        if cmd == "/theme" and current_word in ["--style", "-s"]:
            prev_word = parts[-2] if len(parts) > 1 and not text_stripped.endswith(" ") else ""
            if prev_word == "--style" or prev_word == "-s":
                for theme in self.themes:
                    if current_word.lower() in theme.lower():
                        yield Completion(theme, start_position=-len(current_word))
                return

            if not current_word.startswith("-"):
                return

            for flag in self.commands[cmd]:
                if current_word in flag:
                    yield Completion(flag, start_position=-len(current_word))
            return

        if current_word.startswith("-"):
            flags = self.commands[cmd]
            for flag in flags:
                if current_word in flag:
                    yield Completion(flag, start_position=-len(current_word))
