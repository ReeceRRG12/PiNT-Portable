import customtkinter as ctk
from tkinter import ttk


def _scale() -> float:
    from gui.scale_manager import current_scale
    return current_scale()


# ── Colours ───────────────────────────────────────────────────────────────────
BG      = "#1a1a2e"
SIDEBAR = "#16213e"
ACCENT  = "#00d4ff"
PANEL   = "#16213e"
DIVIDER = "#0f3460"
FG      = "#eeeeee"
FG_DIM  = "#888888"
FG_HINT = "#555555"
WARNING = "#ffaa00"
SUCCESS = "#00ff88"
ERROR   = "#ff4757"

NAV_W = 210  # sidebar width at scale 1.0


# ── Fonts ─────────────────────────────────────────────────────────────────────

def font(size: int, weight: str = "normal") -> ctk.CTkFont:
    """CTkFont for CTk widgets — size is scaled automatically by CTk's widget scaling."""
    return ctk.CTkFont(
        family="Arial",
        size=size,
        weight="bold" if weight == "bold" else "normal",
        slant="italic" if weight == "italic" else "roman",
    )


def tk_font(size: int, weight: str = "normal") -> tuple:
    """Font tuple for ttk/tk widgets (Treeview, Entry, etc.) — manually scaled."""
    scaled = max(8, round(size * _scale()))
    if weight == "bold":
        return ("Arial", scaled, "bold")
    if weight == "italic":
        return ("Arial", scaled, "italic")
    return ("Arial", scaled)


# ── Treeview ──────────────────────────────────────────────────────────────────

def apply_treeview_style(style: ttk.Style) -> None:
    """Dark PiNT styling for all ttk.Treeview widgets via the PiNT.Treeview style."""
    row_h = max(22, round(26 * _scale()))
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
                    font=tk_font(10))
    style.configure("PiNT.Treeview.Heading",
                    background=DIVIDER,
                    foreground=ACCENT,
                    borderwidth=0,
                    font=tk_font(10, "bold"))
    style.map("PiNT.Treeview",
              background=[("selected", "#1f3a5c")],
              foreground=[("selected", FG)])
    style.map("PiNT.Treeview.Heading",
              background=[("active", "#1f2d45")])


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
