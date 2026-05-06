import customtkinter as ctk

_scale: float = 1.0


def detect_scale() -> float:
    """Pick a scale factor based on the primary screen width."""
    import tkinter as _tk
    tmp = _tk.Tk()
    tmp.withdraw()
    sw = tmp.winfo_screenwidth()
    tmp.destroy()
    if sw <= 1366:
        return 0.85
    if sw <= 1920:
        return 1.0
    return 1.15


def apply_scale(scale: float) -> None:
    """Apply scale globally — call once before any CTk widgets are created."""
    global _scale
    _scale = scale
    ctk.set_widget_scaling(scale)
    ctk.set_window_scaling(scale)


def current_scale() -> float:
    return _scale
