import tkinter as tk
from tkinter import ttk
import threading

import customtkinter as ctk
from gui import theme
from port_scanner import PRESET_LABELS, PRESET_PORTS


class PortScanTab:
    """Port scanner tab — TCP connect scan with presets or a custom range."""

    def __init__(self, parent, root, app_state):
        self._root    = root
        self._state   = app_state
        self._results = []
        self._build(parent)

    def _build(self, parent):
        _desc = tk.Label(
            parent,
            text="TCP connect-scan a host to discover open ports.\n\n"
                 "Choose a preset or enter a custom port range. "
                 "Results show each open port and its common service name.",
            bg=theme.BG, fg=theme.FG_DIM,
            font=theme.tk_font(12),
            wraplength=600, justify="center")
        _desc.pack(fill="x", padx=20, pady=(12, 8))
        parent.bind("<Configure>",
                    lambda e: _desc.configure(wraplength=max(100, e.width - 40)),
                    add="+")

        # ── Toolbar ───────────────────────────────────────────────────────────
        top = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        top.pack(fill="x", padx=10, pady=(0, 2))

        self._status = ctk.CTkLabel(
            top, text="Enter a host and press Scan",
            fg_color="transparent", text_color=theme.FG_DIM,
            font=theme.font(10))
        self._status.pack(side="left")

        self._scan_btn = ctk.CTkButton(
            top, text="Scan",
            command=self._start_scan,
            fg_color=theme.ACCENT, text_color=theme.BG,
            hover_color="#00b8d9",
            font=theme.font(10, "bold"),
            corner_radius=6, border_width=0, width=80)
        self._scan_btn.pack(side="right")

        # ── Options row ───────────────────────────────────────────────────────
        opts = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        opts.pack(fill="x", padx=10, pady=(0, 4))

        ctk.CTkLabel(opts, text="Host:",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left")

        self._host_var = tk.StringVar()
        ctk.CTkEntry(opts,
                     textvariable=self._host_var,
                     placeholder_text="192.168.1.1",
                     fg_color=theme.PANEL, text_color=theme.FG,
                     border_color=theme.DIVIDER, border_width=1,
                     font=theme.font(10), width=160).pack(side="left", padx=(5, 14))

        ctk.CTkLabel(opts, text="Ports:",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left")

        self._preset_var = tk.StringVar(value="Top 20")
        self._preset_menu = ctk.CTkOptionMenu(
            opts,
            values=PRESET_LABELS,
            variable=self._preset_var,
            command=self._on_preset_change,
            fg_color=theme.PANEL, text_color=theme.FG,
            button_color=theme.DIVIDER, button_hover_color="#1f2d45",
            dropdown_fg_color=theme.PANEL, dropdown_text_color=theme.FG,
            dropdown_hover_color="#1f2d45",
            font=theme.font(10), width=110)
        self._preset_menu.pack(side="left", padx=(5, 10))

        # Custom range fields (hidden unless preset == Custom)
        self._custom_frame = ctk.CTkFrame(opts, fg_color="transparent",
                                           corner_radius=0)
        ctk.CTkLabel(self._custom_frame, text="From:",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left")
        self._port_from = tk.StringVar(value="1")
        ctk.CTkEntry(self._custom_frame,
                     textvariable=self._port_from,
                     fg_color=theme.PANEL, text_color=theme.FG,
                     border_color=theme.DIVIDER, border_width=1,
                     font=theme.font(10), width=60).pack(side="left", padx=(4, 8))
        ctk.CTkLabel(self._custom_frame, text="To:",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left")
        self._port_to = tk.StringVar(value="1024")
        ctk.CTkEntry(self._custom_frame,
                     textvariable=self._port_to,
                     fg_color=theme.PANEL, text_color=theme.FG,
                     border_color=theme.DIVIDER, border_width=1,
                     font=theme.font(10), width=60).pack(side="left", padx=(4, 0))

        ctk.CTkLabel(opts, text="Timeout (s):",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left", padx=(10, 0))
        self._timeout_var = tk.StringVar(value="1")
        ctk.CTkEntry(opts,
                     textvariable=self._timeout_var,
                     fg_color=theme.PANEL, text_color=theme.FG,
                     border_color=theme.DIVIDER, border_width=1,
                     font=theme.font(10), width=44).pack(side="left", padx=5)

        # ── Progress bar (determinate) ────────────────────────────────────────
        style = ttk.Style()
        style.configure("Scan.Horizontal.TProgressbar",
                        troughcolor=theme.PANEL, background=theme.ACCENT,
                        bordercolor=theme.PANEL, lightcolor=theme.ACCENT,
                        darkcolor=theme.ACCENT, thickness=6)
        self._progress = ttk.Progressbar(parent, mode="determinate",
                                          style="Scan.Horizontal.TProgressbar",
                                          maximum=100)
        self._progress.pack(fill="x", padx=10, pady=(0, 4))

        # ── Results tree ──────────────────────────────────────────────────────
        tree_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        theme.apply_treeview_style(style)

        self._tree = ttk.Treeview(
            tree_frame,
            columns=("port", "service"),
            show="headings",
            style="PiNT.Treeview",
            selectmode="browse")
        self._tree.heading("port",    text="Port")
        self._tree.heading("service", text="Service")
        self._tree.column("port",    width=100)
        self._tree.column("service", width=220)

        sb = ttk.Scrollbar(tree_frame, orient="vertical",
                           command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # ── Bottom bar ────────────────────────────────────────────────────────
        bottom = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        bottom.pack(fill="x", padx=10, pady=(0, 5))

        self._detail = ctk.CTkLabel(
            bottom, text="",
            fg_color="transparent", text_color=theme.FG_DIM,
            font=theme.font(9), anchor="w")
        self._detail.pack(side="left", fill="x", expand=True)

        self._copy_btn = ctk.CTkButton(
            bottom, text="Copy",
            command=self._copy,
            fg_color=theme.PANEL, text_color=theme.FG,
            hover_color="#1f2d45",
            font=theme.font(9),
            corner_radius=6, border_width=0,
            width=60, state="disabled")
        self._copy_btn.pack(side="right", padx=(5, 0))

    # ── Preset toggle ─────────────────────────────────────────────────────────

    def _on_preset_change(self, value):
        if value == "Custom":
            self._custom_frame.pack(side="left")
        else:
            self._custom_frame.pack_forget()

    # ── Scan ──────────────────────────────────────────────────────────────────

    def _start_scan(self):
        host = self._host_var.get().strip()
        if not host:
            self._status.configure(text="Enter a host to scan",
                                   text_color=theme.ERROR)
            return

        preset = self._preset_var.get()
        if preset == "Custom":
            try:
                p_from = int(self._port_from.get())
                p_to   = int(self._port_to.get())
                if p_from < 1 or p_to > 65535 or p_from > p_to:
                    raise ValueError
                ports = list(range(p_from, p_to + 1))
            except ValueError:
                self._status.configure(text="Invalid port range (1–65535)",
                                       text_color=theme.ERROR)
                return
        else:
            ports = PRESET_PORTS[preset]

        try:
            timeout = max(0.1, float(self._timeout_var.get()))
        except ValueError:
            timeout = 1.0

        self._scan_btn.configure(state="disabled")
        self._copy_btn.configure(state="disabled")
        self._progress["value"] = 0
        self._status.configure(
            text=f"Scanning {host} — {len(ports)} port{'s' if len(ports) != 1 else ''}...",
            text_color=theme.WARNING)
        for row in self._tree.get_children():
            self._tree.delete(row)
        self._results = []
        self._detail.configure(text="")

        threading.Thread(
            target=self._run_scan,
            args=(host, ports, timeout),
            daemon=True).start()

    def _run_scan(self, host, ports, timeout):
        from port_scanner import scan_ports

        def _progress(completed, total):
            pct = int(completed / total * 100) if total else 100
            self._root.after(0, self._set_progress, pct)

        scan_ports(host, ports, timeout=timeout,
                   progress_callback=_progress,
                   done_callback=lambda r: self._root.after(0, self._update_ui, r))

    def _set_progress(self, pct):
        self._progress["value"] = pct

    def _update_ui(self, results):
        self._progress["value"] = 100
        self._results = results
        for d in results:
            label = f"{d['port']}/tcp"
            self._tree.insert("", "end", values=(label, d["service"]))
        open_count = len(results)
        host = self._host_var.get().strip()
        self._status.configure(
            text=f"✅ {open_count} open port{'s' if open_count != 1 else ''} on {host}",
            text_color=theme.SUCCESS if open_count > 0 else theme.FG_DIM)
        self._scan_btn.configure(state="normal")
        if results:
            self._copy_btn.configure(state="normal")

    # ── Copy ──────────────────────────────────────────────────────────────────

    def _copy(self):
        if not self._results:
            return
        host = self._host_var.get().strip()
        lines = [f"Port scan — {host}", "Port\tService"]
        for d in self._results:
            lines.append(f"{d['port']}/tcp\t{d['service']}")
        self._root.clipboard_clear()
        self._root.clipboard_append("\n".join(lines))
        self._status.configure(text="📋 Copied to clipboard!", text_color=theme.ACCENT)
