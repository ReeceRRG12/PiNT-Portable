import tkinter as tk
from tkinter import ttk, filedialog
import threading
import csv
import os
from datetime import datetime

import customtkinter as ctk
from gui import theme


class MdnsTab:
    """
    mDNS tab — discovers Bonjour/mDNS services on the local network.
    """

    def __init__(self, parent, root, app_state):
        self._root      = root
        self._state     = app_state
        self._results   = []
        self._view_mode = "simple"
        self._build(parent)

    def _build(self, parent):
        _desc = tk.Label(parent,
                         text="Discovers devices on the local network that advertise services via mDNS (Bonjour).\n\n"
                              "Commonly used to find printers, cameras, smart devices, and Apple services "
                              "without needing access to the switch or DHCP server.",
                         bg=theme.BG, fg=theme.FG_DIM,
                         font=theme.tk_font(12),
                         wraplength=600, justify="center")
        _desc.pack(fill="x", padx=20, pady=(12, 8))
        parent.bind("<Configure>", lambda e: _desc.configure(wraplength=max(100, e.width - 40)), add="+")

        # ── Top toolbar ───────────────────────────────────────────────────────
        top = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        top.pack(fill="x", padx=10, pady=(0, 2))

        self.status = ctk.CTkLabel(top, text="Press Scan to discover mDNS devices",
                                   fg_color="transparent", text_color=theme.FG_DIM,
                                   font=theme.font(10))
        self.status.pack(side="left")

        self.scan_btn = ctk.CTkButton(top, text="Scan",
                                      command=self.start_scan,
                                      fg_color=theme.ACCENT, text_color=theme.BG,
                                      hover_color="#00b8d9",
                                      font=theme.font(10, "bold"),
                                      corner_radius=6, border_width=0,
                                      width=80)
        self.scan_btn.pack(side="right")

        self.toggle_btn = ctk.CTkButton(top, text="Full View",
                                        command=self._toggle_view,
                                        fg_color=theme.PANEL, text_color=theme.FG,
                                        hover_color="#1f2d45",
                                        font=theme.font(10),
                                        corner_radius=6, border_width=0,
                                        width=90)
        self.toggle_btn.pack(side="right", padx=(0, 5))

        self.resolve_btn = ctk.CTkButton(top, text="Resolve IPs",
                                         command=self._start_resolve,
                                         fg_color=theme.PANEL, text_color=theme.FG,
                                         hover_color="#1f2d45",
                                         font=theme.font(10),
                                         corner_radius=6, border_width=0,
                                         width=100, state="disabled")
        self.resolve_btn.pack(side="right", padx=(0, 5))

        # ── Progress bar ──────────────────────────────────────────────────────
        style = ttk.Style()
        style.configure("Scan.Horizontal.TProgressbar",
                        troughcolor=theme.PANEL, background=theme.ACCENT,
                        bordercolor=theme.PANEL, lightcolor=theme.ACCENT,
                        darkcolor=theme.ACCENT, thickness=6)
        self._progress = ttk.Progressbar(parent, mode="indeterminate",
                                          style="Scan.Horizontal.TProgressbar")
        self._progress.pack(fill="x", padx=10, pady=(0, 4))

        # ── Filter bar ────────────────────────────────────────────────────────
        search = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        search.pack(fill="x", padx=10, pady=(0, 5))

        ctk.CTkLabel(search, text="Filter:",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left")

        self._filter_var = tk.StringVar()
        self._filter_var.trace_add("write", self._apply_filter)
        ctk.CTkEntry(search,
                     textvariable=self._filter_var,
                     fg_color=theme.PANEL, text_color=theme.FG,
                     border_color=theme.DIVIDER, border_width=1,
                     font=theme.font(10)).pack(
                         side="left", fill="x", expand=True, padx=(5, 0))

        # ── Results tree ──────────────────────────────────────────────────────
        tree_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        theme.apply_treeview_style(style)

        self._tree = ttk.Treeview(tree_frame,
                                   columns=("friendly", "type", "ip"),
                                   show="headings",
                                   style="PiNT.Treeview",
                                   selectmode="browse")
        self._tree.heading("friendly", text="Device Name")
        self._tree.heading("type",     text="Service Type")
        self._tree.heading("ip",       text="IP Address")
        self._tree.column("friendly", width=200)
        self._tree.column("type",     width=160)
        self._tree.column("ip",       width=110)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # ── Bottom bar ────────────────────────────────────────────────────────
        bottom = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        bottom.pack(fill="x", padx=10, pady=(0, 5))

        self._detail = ctk.CTkLabel(bottom, text="",
                                    fg_color="transparent", text_color=theme.FG_DIM,
                                    font=theme.font(9), anchor="w")
        self._detail.pack(side="left", fill="x", expand=True)

        self.export_btn = ctk.CTkButton(bottom, text="Export CSV",
                                        command=self._export_csv,
                                        fg_color=theme.PANEL, text_color=theme.FG,
                                        hover_color="#1f2d45",
                                        font=theme.font(9),
                                        corner_radius=6, border_width=0,
                                        width=90, state="disabled")
        self.export_btn.pack(side="right", padx=(5, 0))

        self.copy_btn = ctk.CTkButton(bottom, text="Copy",
                                      command=self._copy,
                                      fg_color=theme.PANEL, text_color=theme.FG,
                                      hover_color="#1f2d45",
                                      font=theme.font(9),
                                      corner_radius=6, border_width=0,
                                      width=60, state="disabled")
        self.copy_btn.pack(side="right", padx=(5, 0))

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

    # ── Scan ──────────────────────────────────────────────────────────────────

    def start_scan(self):
        timeout = self._state.settings.mdns_timeout
        self.scan_btn.configure(state="disabled")
        self.resolve_btn.configure(state="disabled")
        self.export_btn.configure(state="disabled")
        self.copy_btn.configure(state="disabled")
        self.status.configure(
            text=f"Scanning for mDNS devices... ({timeout}s)",
            text_color=theme.WARNING)
        for row in self._tree.get_children():
            self._tree.delete(row)
        self._results = []
        self._detail.configure(text="")
        self._progress.start(10)
        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        from mdns_scanner import scan_mdns
        scan_mdns(self._handle_result,
                  timeout=self._state.settings.mdns_timeout,
                  iface=self._state.selected_iface)

    def _handle_result(self, devices):
        self._root.after(0, self._update_ui, devices)

    def _update_ui(self, devices):
        self._progress.stop()
        self._results = devices
        self._apply_filter()
        count = len(devices)
        self.status.configure(
            text=f"✅ Found {count} mDNS device{'s' if count != 1 else ''}",
            text_color=theme.SUCCESS if count > 0 else theme.ERROR)
        self.scan_btn.configure(state="normal")
        self.resolve_btn.configure(state="normal")
        self.export_btn.configure(state="normal")
        self.copy_btn.configure(state="normal")
        if devices:
            self._state.session.add_mdns_scan(devices)

    # ── Filter / view ─────────────────────────────────────────────────────────

    def _apply_filter(self, *_):
        query = self._filter_var.get().lower()
        for row in self._tree.get_children():
            self._tree.delete(row)
        for d in self._results:
            if self._view_mode == "simple" and not d.get("simple", False):
                continue
            friendly = d.get("friendly", "")
            stype    = d.get("type",     "")
            ip       = d.get("ip",       "")
            if query in friendly.lower() or query in stype.lower() or query in ip.lower():
                self._tree.insert("", "end",
                                   values=(friendly, stype, ip),
                                   tags=(d.get("raw", ""),))

    def _toggle_view(self):
        if self._view_mode == "simple":
            self._view_mode = "full"
            self.toggle_btn.configure(text="Simple View")
        else:
            self._view_mode = "simple"
            self.toggle_btn.configure(text="Full View")
        self._apply_filter()

    def _on_select(self, _event):
        sel = self._tree.selection()
        if sel:
            tags = self._tree.item(sel[0], "tags")
            if tags:
                self._detail.configure(text=f"Raw: {tags[0]}")

    # ── IP resolve ────────────────────────────────────────────────────────────

    def _start_resolve(self):
        self.resolve_btn.configure(state="disabled")
        self.scan_btn.configure(state="disabled")
        self.status.configure(
            text="Sending IP resolve request... (45s)", text_color=theme.WARNING)
        threading.Thread(target=self._run_resolve, daemon=True).start()

    def _run_resolve(self):
        from mdns_scanner import resolve_mdns_ips
        resolve_mdns_ips(self._results, self._handle_resolve)

    def _handle_resolve(self, updated):
        self._root.after(0, self._finish_resolve, updated)

    def _finish_resolve(self, updated):
        self._results = updated
        self._apply_filter()
        self.resolve_btn.configure(state="normal")
        self.scan_btn.configure(state="normal")
        self.status.configure(text="✅ IP resolve complete", text_color=theme.SUCCESS)

    # ── Copy / export ─────────────────────────────────────────────────────────

    def _copy(self):
        if not self._results:
            return
        lines = ["Device Name\tService Type\tIP Address"]
        for d in self._results:
            if self._view_mode == "simple" and not d.get("simple", False):
                continue
            lines.append(f"{d.get('friendly','')}\t{d.get('type','')}\t{d.get('ip','')}")
        self._root.clipboard_clear()
        self._root.clipboard_append("\n".join(lines))
        self.status.configure(text="📋 Copied to clipboard!", text_color=theme.ACCENT)

    def _export_csv(self):
        if not self._results:
            return
        timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"pint_mdns_{timestamp}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=default_name,
            title="Export mDNS results"
        )
        if not filepath:
            return
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Device Name", "Service Type", "IP Address", "Raw"])
            for d in self._results:
                writer.writerow([d.get("friendly",""), d.get("type",""),
                                  d.get("ip",""),      d.get("raw","")])
        self.status.configure(
            text=f"✅ Exported to {os.path.basename(filepath)}",
            text_color=theme.SUCCESS)
