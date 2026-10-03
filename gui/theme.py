import customtkinter as ctk
import sys
import tkinter as tk
from tkinter import ttk


def _scale() -> float:
    root = tk._default_root
    if root is not None and hasattr(root, "_get_widget_scaling"):
        return root._get_widget_scaling()
    from gui.scale_manager import current_scale
    return current_scale()


# ── Colours ───────────────────────────────────────────────────────────────────
# Base palette
BG      = "#101722"
SIDEBAR = "#131D2A"
ACCENT  = "#62D6C7"
PANEL   = "#192635"
DIVIDER = "#2A3B4E"
FG      = "#EDF3FA"
FG_DIM  = "#A7B6C8"
FG_HINT = "#98A9BE"
FG_MUTED = "#BBC8D7"
FG_LABEL = "#A7B6C8"
WARNING = "#F3BD69"
SUCCESS = "#7BDCB5"
ERROR   = "#FF929B"

# Interaction states
ACCENT_HOVER = "#80E2D5"
PANEL_HOVER  = "#25384B"
NAV_BG       = SIDEBAR
NAV_ACTIVE   = "#233D46"
SELECT       = "#2B4957"

# Accent as an RGB tuple (for PIL image tinting where we can't pass a hex string)
ACCENT_RGB = (98, 214, 199)

NAV_W = 212
FONT_FAMILY = "Helvetica Neue" if sys.platform == "darwin" else "Segoe UI" if sys.platform == "win32" else "DejaVu Sans"


# ── Fonts ─────────────────────────────────────────────────────────────────────

def font(size: int, weight: str = "normal") -> ctk.CTkFont:
    """CTkFont for CTk widgets — size is scaled automatically by CTk's widget scaling."""
    return ctk.CTkFont(
        family=FONT_FAMILY,
        size=max(12, size),
        weight="bold" if weight == "bold" else "normal",
        slant="italic" if weight == "italic" else "roman",
    )


def tk_font(size: int, weight: str = "normal") -> tuple:
    """Font tuple for ttk/tk widgets (Treeview, Entry, etc.) — manually scaled."""
    # Negative sizes are pixels, matching CTkFont; positive Tk sizes are points.
    scaled = -max(10, round(max(12, size) * _scale()))
    if weight == "bold":
        return (FONT_FAMILY, scaled, "bold")
    if weight == "italic":
        return (FONT_FAMILY, scaled, "italic")
    return (FONT_FAMILY, scaled)


# ── Treeview ──────────────────────────────────────────────────────────────────

def apply_treeview_style(style: ttk.Style) -> None:
    """Dark PiNT styling for all ttk.Treeview widgets via the PiNT.Treeview style."""
    row_h = max(26, round(34 * _scale()))
    style.configure("PiNT.Treeview",
                    background=PANEL,
                    foreground=FG,
                    fieldbackground=PANEL,
                    borderwidth=0,
                    relief="flat",
                    lightcolor=PANEL,
                    darkcolor=PANEL,
                    bordercolor=PANEL,
                    rowheight=row_h,
                    font=tk_font(13))
    style.configure("PiNT.Treeview.Heading",
                    background=SIDEBAR,
                    foreground=FG_MUTED,
                    borderwidth=0,
                    padding=(10, 10),
                    relief="flat",
                    font=tk_font(12, "bold"))
    style.map("PiNT.Treeview",
              background=[("selected", SELECT)],
              foreground=[("selected", FG)])
    style.map("PiNT.Treeview.Heading",
              background=[("active", PANEL_HOVER)])


def apply_progressbar_style(style: ttk.Style) -> None:
    """Cyan scan progress bar style — used by every tab's Scan.Horizontal.TProgressbar."""
    style.configure("Scan.Horizontal.TProgressbar",
                    troughcolor=PANEL, background=ACCENT,
                    bordercolor=PANEL, lightcolor=ACCENT,
                    darkcolor=ACCENT, thickness=3)


def apply_scrollbar_style(style: ttk.Style) -> None:
    """Dark styling for ttk.Scrollbar widgets (best-effort on Windows)."""
    for orient in ("Vertical", "Horizontal"):
        name = f"{orient}.TScrollbar"
        style.configure(name,
                        background=PANEL,
                        troughcolor=BG,
                        bordercolor=BG,
                        arrowcolor=FG_DIM,
                        darkcolor=PANEL,
                        lightcolor=PANEL,
                        gripcount=0,
                        arrowsize=13,
                        relief="flat",
                        borderwidth=0)
        style.map(name,
                  background=[("active", DIVIDER), ("pressed", ACCENT), ("!active", PANEL)],
                  troughcolor=[("active", BG), ("!active", BG)],
                  arrowcolor=[("active", FG), ("!active", FG_DIM)])
