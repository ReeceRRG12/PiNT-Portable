"""
Shared widget helpers — small factories for the patterns that repeat across
every tab (description label, primary/secondary buttons, scan progress bar,
results tree, copy-to-clipboard). Use these so tweaking the look or behaviour
of a common widget is a one-file edit.
"""

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk
from gui import theme


def description(parent, text):
    """
    Centered grey description label at the top of a tab. Auto-rewraps when
    the window resizes. Uses tk.Label (not CTk) because tk_font is manually
    scaled and the auto-wrap behaviour is more reliable here.
    """
    label = tk.Label(parent, text=text,
                     bg=theme.BG, fg=theme.FG_DIM,
                     font=theme.tk_font(12),
                     wraplength=600, justify="center")
    label.pack(fill="x", padx=20, pady=(12, 8))
    parent.bind("<Configure>",
                lambda e: label.configure(wraplength=max(100, e.width - 40)),
                add="+")
    return label


def status_label(parent, text):
    """Dim status label — typically the first thing in a tab's toolbar."""
    return ctk.CTkLabel(parent, text=text,
                        fg_color="transparent", text_color=theme.FG_DIM,
                        font=theme.font(10))


def primary_button(parent, text, command, **overrides):
    """
    Cyan accent button — the main Scan/Query action in each tab.
    Pass any CTkButton kwarg in **overrides to customise (e.g. width=120).
    """
    kwargs = dict(
        fg_color=theme.ACCENT, text_color=theme.BG,
        hover_color=theme.ACCENT_HOVER,
        font=theme.font(10, "bold"),
        corner_radius=6, border_width=0, width=80)
    kwargs.update(overrides)
    return ctk.CTkButton(parent, text=text, command=command, **kwargs)


def secondary_button(parent, text, command, **overrides):
    """
    Subtle panel-coloured button — for Copy, Export, Clear, etc.
    Pass any CTkButton kwarg in **overrides to customise.
    """
    kwargs = dict(
        fg_color=theme.PANEL, text_color=theme.FG,
        hover_color=theme.PANEL_HOVER,
        font=theme.font(9),
        corner_radius=6, border_width=0, width=60)
    kwargs.update(overrides)
    return ctk.CTkButton(parent, text=text, command=command, **kwargs)


def scan_progressbar(parent, mode="indeterminate", maximum=None, **pack_kwargs):
    """
    Cyan scan progress bar. Already packed using **pack_kwargs (so callers
    don't need to call .pack() themselves). Returns the Progressbar.
    """
    style = ttk.Style()
    theme.apply_progressbar_style(style)
    kwargs = {"mode": mode, "style": "Scan.Horizontal.TProgressbar"}
    if maximum is not None:
        kwargs["maximum"] = maximum
    bar = ttk.Progressbar(parent, **kwargs)
    bar.pack(**pack_kwargs)
    return bar


def results_tree(parent, columns):
    """
    Dark-themed Treeview with a vertical scrollbar, inside its own frame.

    columns: list of (key, heading, width) tuples.

    Returns (tree, frame). The caller is responsible for packing `frame`
    so the layout (padding, expand=True, etc.) stays in the tab where you
    can see it.
    """
    frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
    style = ttk.Style()
    theme.apply_treeview_style(style)

    tree = ttk.Treeview(frame,
                        columns=[c[0] for c in columns],
                        show="headings",
                        style="PiNT.Treeview",
                        selectmode="browse")
    for key, heading, width in columns:
        tree.heading(key, text=heading)
        tree.column(key, width=width)

    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return tree, frame


def copy_to_clipboard(root, text, status_label=None):
    """
    Copy text to the system clipboard. If a status_label is given, flash
    the standard "Copied to clipboard!" confirmation on it.
    """
    root.clipboard_clear()
    root.clipboard_append(text)
    if status_label is not None:
        status_label.configure(text="📋 Copied to clipboard!",
                               text_color=theme.ACCENT)
