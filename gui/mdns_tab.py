import tkinter as tk
from tkinter import filedialog
import threading
import csv
import os
from datetime import datetime

import customtkinter as ctk
from gui import theme, widgets


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
        widgets.description(
            parent,
            "Discovers devices on the local network that advertise services via mDNS (Bonjour).\n\n"
            "Commonly used to find printers, cameras, smart devices, and Apple services "
            "without needing access to the switch or DHCP server.")

        # ── Top toolbar ───────────────────────────────────────────────────────
        top = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        top.pack(fill="x", padx=10, pady=(0, 2))

        self.status = widgets.status_label(top, "Press Scan to discover mDNS devices")
        self.status.pack(side="left")

        self.scan_btn = widgets.primary_button(top, "Scan", self.start_scan)
        self.scan_btn.pack(side="right")

        self.toggle_btn = widgets.secondary_button(
            top, "Full View", self._toggle_view,
            width=90, font=theme.font(10))
        self.toggle_btn.pack(side="right", padx=(0, 5))

        self.resolve_btn = widgets.secondary_button(
            top, "Resolve IPs", self._start_resolve,
            width=100, font=theme.font(10), state="disabled")
        self.resolve_btn.pack(side="right", padx=(0, 5))

        # ── Progress bar ──────────────────────────────────────────────────────
        self._progress = widgets.scan_progressbar(
            parent, fill="x", padx=10, pady=(0, 4))

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
        self._tree, tree_frame = widgets.results_tree(parent, [
            ("friendly", "Device Name",  200),
            ("type",     "Service Type", 160),
            ("ip",       "IP Address",   110),
        ])
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        # ── Bottom bar ────────────────────────────────────────────────────────
        bottom = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        bottom.pack(fill="x", padx=10, pady=(0, 5))

        self._detail = ctk.CTkLabel(bottom, text="",
                                    fg_color="transparent", text_color=theme.FG_DIM,
                                    font=theme.font(9), anchor="w")
        self._detail.pack(side="left", fill="x", expand=True)

        self.export_btn = widgets.secondary_button(
            bottom, "Export CSV", self._export_csv,
            width=90, state="disabled")
        self.export_btn.pack(side="right", padx=(5, 0))

        self.copy_btn = widgets.secondary_button(
            bottom, "Copy", self._copy, state="disabled")
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
        from network.mdns_scanner import scan_mdns
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
        from network.mdns_scanner import resolve_mdns_ips
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
        widgets.copy_to_clipboard(self._root, "\n".join(lines), self.status)

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
