"""
Shared widget helpers — small factories for the patterns that repeat across
every tab (description label, primary/secondary buttons, scan progress bar,
results tree, copy-to-clipboard). Use these so tweaking the look or behaviour
of a common widget is a one-file edit.
"""

import tkinter as tk
from tkinter import ttk
import ipaddress
import re

import customtkinter as ctk
from gui import theme


def description(parent, text):
    """
    Left-aligned introduction that rewraps with the panel width.
    """
    label = tk.Label(parent, text=text.replace("\n\n", " "),
                     bg=theme.BG, fg=theme.FG_DIM,
                     font=theme.tk_font(13),
                     wraplength=600, justify="left", anchor="w")
    label.pack(fill="x", padx=20, pady=(16, 18))
    parent.bind("<Configure>",
                lambda e: label.configure(wraplength=max(100, e.width - 40)),
                add="+")
    return label


def status_label(parent, text):
    """Dim status label — typically the first thing in a tab's toolbar."""
    return ctk.CTkLabel(parent, text=text,
                        fg_color="transparent", text_color=theme.FG_DIM,
                        font=theme.font(12))


def primary_button(parent, text, command, **overrides):
    """
    Cyan accent button — the main Scan/Query action in each tab.
    Pass any CTkButton kwarg in **overrides to customise (e.g. width=120).
    """
    kwargs = dict(
        fg_color=theme.ACCENT, text_color=theme.BG,
        hover_color=theme.ACCENT_HOVER,
        font=theme.font(13, "bold"),
        corner_radius=8, border_width=0, width=88, height=36)
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
        font=theme.font(12),
        corner_radius=8, border_width=1, border_color=theme.DIVIDER,
        width=70, height=36)
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


def _sort_key(value):
    """Sort addresses numerically and mixed device names in natural order."""
    text = str(value).strip()
    try:
        address = ipaddress.ip_address(text)
        return (0, address.version, int(address))
    except ValueError:
        pass
    # Tagged pieces avoid comparing str with int for mixed text/numeric cells.
    return (1, tuple((0, int(part)) if part.isdigit() else (1, part.casefold())
                     for part in re.split(r"(\d+)", text) if part))


def _sort_tree(tree, column, descending=False):
    rows = sorted(tree.get_children(""),
                  key=lambda item: _sort_key(tree.set(item, column)),
                  reverse=descending)
    for index, item in enumerate(rows):
        tree.move(item, "", index)
    for key in tree["columns"]:
        title = tree.heading(key, "text").removesuffix("  ↑").removesuffix("  ↓")
        tree.heading(key, text=title + ("  ↓" if descending else "  ↑") if key == column else title,
                     command=lambda c=key, reverse=(not descending if key == column else False):
                         _sort_tree(tree, c, reverse))


def results_tree(parent, columns):
    """
    Sortable results with both scrollbars, inside their own frame.

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
        tree.heading(key, text=heading, command=lambda c=key: _sort_tree(tree, c))
        scaled_width = round(width * theme._scale())
        tree.column(key, width=scaled_width, minwidth=min(scaled_width, 130), anchor="w")

    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=sb.set, xscrollcommand=horizontal.set)
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    tree.grid(row=0, column=0, sticky="nsew")
    sb.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
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
