import tkinter as tk
import threading
import os
from datetime import datetime
from tkinter import filedialog

import customtkinter as ctk
from gui import theme, widgets


class ArpTab:
    """ARP scanner tab — sweeps the local subnet and lists IP/MAC/hostname."""

    def __init__(self, parent, root, app_state):
        self._root    = root
        self._state   = app_state
        self._results = []
        self._build(parent)

    def _build(self, parent):
        widgets.description(
            parent,
            "Sends ARP requests across the local subnet to discover all active devices.\n\n"
            "Results show each device's IP address, MAC address, and hostname (if resolvable).")

        # ── Toolbar ───────────────────────────────────────────────────────────
        top = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        top.pack(fill="x", padx=10, pady=(0, 2))

        self._status = widgets.status_label(
            top, "Press Scan to discover devices on the subnet")
        self._status.pack(side="left")

        self._scan_btn = widgets.primary_button(top, "Scan", self._start_scan)
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
        self._progress = widgets.scan_progressbar(
            parent, fill="x", padx=10, pady=(0, 4))

        # ── Results tree ──────────────────────────────────────────────────────
        self._tree, tree_frame = widgets.results_tree(parent, [
            ("ip",       "IP Address",  130),
            ("mac",      "MAC Address", 160),
            ("hostname", "Hostname",    260),
        ])
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        # ── Bottom bar ────────────────────────────────────────────────────────
        bottom = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        bottom.pack(fill="x", padx=10, pady=(0, 5))

        self._detail = ctk.CTkLabel(
            bottom, text="",
            fg_color="transparent", text_color=theme.FG_DIM,
            font=theme.font(9), anchor="w")
        self._detail.pack(side="left", fill="x", expand=True)

        self._copy_btn = widgets.secondary_button(
            bottom, "Copy", self._copy, state="disabled")
        self._copy_btn.pack(side="right", padx=(5, 0))

        self._export_btn = widgets.secondary_button(
            bottom, "Export XLSX", self._export, width=90, state="disabled")
        self._export_btn.pack(side="right", padx=(5, 0))

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _detect_subnet(self):
        try:
            from network.arp_scanner import get_subnet_for_iface
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
        self._export_btn.configure(state="disabled")
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
        from network.arp_scanner import scan_arp
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
            self._export_btn.configure(state="normal")
        else:
            self._export_btn.configure(state="disabled")

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
        widgets.copy_to_clipboard(self._root, "\n".join(lines), self._status)

    def _export(self):
        if not self._results:
            return

        # Derive a filename-safe "<site>" hint from the subnet so the user
        # gets a meaningful default they can rename in the save dialog.
        subnet = self._subnet_var.get().strip()
        site = "".join(c if c.isalnum() else "_" for c in subnet).strip("_") or "scan"
        date = datetime.now().strftime("%Y%m%d")
        default_name = f"arp_export_{site}_{date}.xlsx"

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=default_name,
            title="Export ARP table to XLSX",
        )
        if not filepath:
            return

        try:
            from exporter import export_arp_xlsx
            export_arp_xlsx(self._results, filepath)
            self._status.configure(
                text=f"✅ Saved {os.path.basename(filepath)}",
                text_color=theme.SUCCESS)
        except Exception as e:
            self._status.configure(
                text=f"❌ Export failed: {e}", text_color=theme.ERROR)
