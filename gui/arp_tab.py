import tkinter as tk
from tkinter import ttk
import threading

import customtkinter as ctk
from gui import theme


class ArpTab:
    """ARP scanner tab — sweeps the local subnet and lists IP/MAC/hostname."""

    def __init__(self, parent, root, app_state):
        self._root    = root
        self._state   = app_state
        self._results = []
        self._build(parent)

    def _build(self, parent):
        _desc = tk.Label(
            parent,
            text="Sends ARP requests across the local subnet to discover all active devices.\n\n"
                 "Results show each device's IP address, MAC address, and hostname (if resolvable).",
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
            top, text="Press Scan to discover devices on the subnet",
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

        # ── Subnet field ──────────────────────────────────────────────────────
        opts = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        opts.pack(fill="x", padx=10, pady=(0, 4))

        ctk.CTkLabel(opts, text="Subnet:",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left")

        self._subnet_var = tk.StringVar(value=self._detect_subnet())
        ctk.CTkEntry(opts,
                     textvariable=self._subnet_var,
                     fg_color=theme.PANEL, text_color=theme.FG,
                     border_color=theme.DIVIDER, border_width=1,
                     font=theme.font(10), width=180).pack(side="left", padx=(5, 12))

        ctk.CTkLabel(opts, text="Timeout (s):",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left")

        self._timeout_var = tk.StringVar(value="3")
        ctk.CTkEntry(opts,
                     textvariable=self._timeout_var,
                     fg_color=theme.PANEL, text_color=theme.FG,
                     border_color=theme.DIVIDER, border_width=1,
                     font=theme.font(10), width=50).pack(side="left", padx=5)

        # ── Progress bar ──────────────────────────────────────────────────────
        style = ttk.Style()
        style.configure("Scan.Horizontal.TProgressbar",
                        troughcolor=theme.PANEL, background=theme.ACCENT,
                        bordercolor=theme.PANEL, lightcolor=theme.ACCENT,
                        darkcolor=theme.ACCENT, thickness=6)
        self._progress = ttk.Progressbar(parent, mode="indeterminate",
                                          style="Scan.Horizontal.TProgressbar")
        self._progress.pack(fill="x", padx=10, pady=(0, 4))

        # ── Results tree ──────────────────────────────────────────────────────
        tree_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        theme.apply_treeview_style(style)

        self._tree = ttk.Treeview(
            tree_frame,
            columns=("ip", "mac", "hostname"),
            show="headings",
            style="PiNT.Treeview",
            selectmode="browse")
        self._tree.heading("ip",       text="IP Address")
        self._tree.heading("mac",      text="MAC Address")
        self._tree.heading("hostname", text="Hostname")
        self._tree.column("ip",       width=130)
        self._tree.column("mac",      width=160)
        self._tree.column("hostname", width=260)

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

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _detect_subnet(self):
        try:
            from arp_scanner import get_subnet_for_iface
            subnet = get_subnet_for_iface(self._state.selected_iface)
            return subnet or ""
        except Exception:
            return ""

    # ── Scan ──────────────────────────────────────────────────────────────────

    def _start_scan(self):
        network = self._subnet_var.get().strip()
        if not network:
            self._status.configure(
                text="Enter a subnet (e.g. 192.168.1.0/24)", text_color=theme.ERROR)
            return

        try:
            timeout = max(1, int(self._timeout_var.get()))
        except ValueError:
            timeout = 3

        self._scan_btn.configure(state="disabled")
        self._copy_btn.configure(state="disabled")
        self._status.configure(
            text=f"Scanning {network}...", text_color=theme.WARNING)
        for row in self._tree.get_children():
            self._tree.delete(row)
        self._results = []
        self._detail.configure(text="")
        self._progress.start(10)

        threading.Thread(
            target=self._run_scan,
            args=(network, timeout),
            daemon=True).start()

    def _run_scan(self, network, timeout):
        from arp_scanner import scan_arp
        scan_arp(network,
                 iface=self._state.selected_iface,
                 timeout=timeout,
                 callback=lambda r: self._root.after(0, self._update_ui, r))

    def _update_ui(self, results):
        self._progress.stop()
        self._results = results
        for d in results:
            self._tree.insert("", "end",
                               values=(d["ip"], d["mac"], d["hostname"]))
        count = len(results)
        self._status.configure(
            text=f"✅ Found {count} device{'s' if count != 1 else ''}",
            text_color=theme.SUCCESS if count > 0 else theme.ERROR)
        self._scan_btn.configure(state="normal")
        if results:
            self._copy_btn.configure(state="normal")

    # ── Events ────────────────────────────────────────────────────────────────

    def _on_select(self, _event):
        sel = self._tree.selection()
        if sel:
            vals = self._tree.item(sel[0], "values")
            if vals:
                self._detail.configure(text=f"  {vals[0]}  |  {vals[1]}")

    def _copy(self):
        if not self._results:
            return
        lines = ["IP Address\tMAC Address\tHostname"]
        for d in self._results:
            lines.append(f"{d['ip']}\t{d['mac']}\t{d['hostname']}")
        self._root.clipboard_clear()
        self._root.clipboard_append("\n".join(lines))
        self._status.configure(text="📋 Copied to clipboard!", text_color=theme.ACCENT)
