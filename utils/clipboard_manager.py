from prompt_toolkit.application.current import get_app
from prompt_toolkit.clipboard import ClipboardData

try:
    import pyperclip  # type: ignore
except ImportError:
    pyperclip = None

def copy_to_clipboard(text: str) -> None:
    """Copies the provided text to the system clipboard using pyperclip or prompt_toolkit."""
    if not text:
        return

    # Priority 1: Pyperclip (System Clipboard)
    if pyperclip:
        try:
            pyperclip.copy(text)
            return
        except Exception:
            pass

    # Priority 2: Prompt Toolkit Internal Clipboard
    try:
        app = get_app()
        app.clipboard.set_data(ClipboardData(text))
    except Exception:
        pass