import customtkinter as ctk

_scale: float = 1.0


def window_size(screen_width: int, screen_height: int, dpi_scale: float = 1.0) -> tuple:
    """Return logical CTk dimensions that leave room for system bars and borders.

    CTk applies the OS DPI factor to geometry itself. Scaling these dimensions
    again would make a window too large on high-DPI Windows laptops.
    """
    dpi_scale = max(0.1, dpi_scale)
    width = max(1, int((screen_width - 64) / dpi_scale))
    height = max(1, int((screen_height - 112) / dpi_scale))
    return min(1240, width), min(820, height)


def detect_scale(root) -> float:
    """Compact controls on smaller logical screens; keep native DPI scaling."""
    width, height = window_size(root.winfo_screenwidth(), root.winfo_screenheight(),
                                root._get_window_scaling())
    return 0.9 if width < 1120 or height < 720 else 1.0


def apply_scale(scale: float) -> None:
    """Apply a control density before building widgets, in addition to OS DPI."""
    global _scale
    _scale = scale
    ctk.set_widget_scaling(scale)


def current_scale() -> float:
    return _scale
