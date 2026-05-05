import tkinter as tk
from tkinter import ttk, filedialog
import threading
import csv
import os
from datetime import datetime


class MdnsTab:
    """
    mDNS tab — discovers Bonjour/mDNS services on the local network.
    """

    def __init__(self, parent, root, app_state):
        self._root  = root
        self._state = app_state
        self._results   = []
        self._view_mode = "simple"
        self._build(parent)

    def _build(self, parent):
        tk.Label(parent,
                 text="Discovers devices on the local network that advertise services via mDNS "
                      "(Bonjour). Commonly used to find printers, cameras, smart devices, and "
                      "Apple services without needing access to the switch or DHCP server.",
                 bg="#1a1a2e", fg="#555555",
                 font=("Arial", 9, "italic"),
                 wraplength=460, justify="left").pack(
                     fill="x", padx=10, pady=(0, 4), anchor="w")

        # ── Top toolbar ───────────────────────────────────────────────────────
        top = tk.Frame(parent, bg="#1a1a2e")
        top.pack(fill="x", padx=10, pady=(0, 5))

        self.status = tk.Label(top, text="Press Scan to discover mDNS devices",
                               bg="#1a1a2e", fg="#888888")
        self.status.pack(side="left")

        self.scan_btn = tk.Button(top, text="Scan",
                                  command=self.start_scan,
                                  bg="#00d4ff", fg="#1a1a2e",
                                  font=("Arial", 10, "bold"),
                                  padx=15, relief="flat",
                                  highlightthickness=0, borderwidth=0)
        self.scan_btn.pack(side="right")

        self.toggle_btn = tk.Button(top, text="Full View",
                                    command=self._toggle_view,
                                    bg="#16213e", fg="#eee",
                                    font=("Arial", 10),
                                    padx=10, relief="flat",
                                    highlightthickness=0, borderwidth=0)
        self.toggle_btn.pack(side="right", padx=(0, 5))

        self.resolve_btn = tk.Button(top, text="Resolve IPs",
                                     command=self._start_resolve,
                                     bg="#16213e", fg="#eee",
                                     font=("Arial", 10),
                                     padx=10, relief="flat",
                                     highlightthickness=0, borderwidth=0,
                                     state="disabled")
        self.resolve_btn.pack(side="right", padx=(0, 5))

        # ── Filter bar ────────────────────────────────────────────────────────
        search = tk.Frame(parent, bg="#1a1a2e")
        search.pack(fill="x", padx=10, pady=(0, 5))

        tk.Label(search, text="Filter:", bg="#1a1a2e", fg="#888888").pack(side="left")
        self._filter_var = tk.StringVar()
        self._filter_var.trace_add("write", self._apply_filter)
        tk.Entry(search,
                 textvariable=self._filter_var,
                 bg="#16213e", fg="#eee",
                 insertbackground="#eee",
                 relief="flat", font=("Arial", 10)).pack(
                     side="left", fill="x", expand=True, padx=(5, 0))

        # ── Results tree ──────────────────────────────────────────────────────
        tree_frame = tk.Frame(parent, bg="#1a1a2e")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        style = ttk.Style()
        style.configure("Treeview",
                         background="#16213e", foreground="#eee",
                         fieldbackground="#16213e",
                         rowheight=28, font=("Arial", 10))
        style.configure("Treeview.Heading",
                         background="#0f3460", foreground="#00d4ff",
                         font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#0f3460")])

        self._tree = ttk.Treeview(tree_frame,
                                   columns=("friendly", "type", "ip"),
                                   show="headings",
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
        bottom = tk.Frame(parent, bg="#1a1a2e")
        bottom.pack(fill="x", padx=10, pady=(0, 5))

        self._detail = tk.Label(bottom, text="",
                                bg="#1a1a2e", fg="#888888",
                                font=("Arial", 9), anchor="w")
        self._detail.pack(side="left", fill="x", expand=True)

        self.export_btn = tk.Button(bottom, text="Export CSV",
                                    command=self._export_csv,
                                    bg="#16213e", fg="#eee",
                                    font=("Arial", 9), padx=8,
                                    relief="flat", highlightthickness=0, borderwidth=0,
                                    state="disabled")
        self.export_btn.pack(side="right", padx=(5, 0))

        self.copy_btn = tk.Button(bottom, text="Copy",
                                  command=self._copy,
                                  bg="#16213e", fg="#eee",
                                  font=("Arial", 9), padx=8,
                                  relief="flat", highlightthickness=0, borderwidth=0,
                                  state="disabled")
        self.copy_btn.pack(side="right", padx=(5, 0))

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

    # ── Scan ──────────────────────────────────────────────────────────────────

    def start_scan(self):
        self.scan_btn.config(state="disabled")
        self.resolve_btn.config(state="disabled")
        self.export_btn.config(state="disabled")
        self.copy_btn.config(state="disabled")
        self.status.config(text="Scanning for mDNS devices... (30s)", fg="#ffaa00")
        for row in self._tree.get_children():
            self._tree.delete(row)
        self._results = []
        self._detail.config(text="")
        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        from mdns_scanner import scan_mdns
        scan_mdns(self._handle_result, iface=self._state.selected_iface)

    def _handle_result(self, devices):
        self._root.after(0, self._update_ui, devices)

    def _update_ui(self, devices):
        self._results = devices
        self._apply_filter()
        count = len(devices)
        self.status.config(
            text=f"✅ Found {count} mDNS device{'s' if count != 1 else ''}",
            fg="#00ff88" if count > 0 else "#ff4757")
        self.scan_btn.config(state="normal")
        self.resolve_btn.config(state="normal")
        self.export_btn.config(state="normal")
        self.copy_btn.config(state="normal")
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
            self.toggle_btn.config(text="Simple View")
        else:
            self._view_mode = "simple"
            self.toggle_btn.config(text="Full View")
        self._apply_filter()

    def _on_select(self, _event):
        sel = self._tree.selection()
        if sel:
            tags = self._tree.item(sel[0], "tags")
            if tags:
                self._detail.config(text=f"Raw: {tags[0]}")

    # ── IP resolve ────────────────────────────────────────────────────────────

    def _start_resolve(self):
        self.resolve_btn.config(state="disabled")
        self.scan_btn.config(state="disabled")
        self.status.config(text="Sending IP resolve request... (45s)", fg="#ffaa00")
        threading.Thread(
            target=lambda: self._run_resolve(),
            daemon=True
        ).start()

    def _run_resolve(self):
        from mdns_scanner import resolve_mdns_ips
        resolve_mdns_ips(self._results, self._handle_resolve)

    def _handle_resolve(self, updated):
        self._root.after(0, self._finish_resolve, updated)

    def _finish_resolve(self, updated):
        self._results = updated
        self._apply_filter()
        self.resolve_btn.config(state="normal")
        self.scan_btn.config(state="normal")
        self.status.config(text="✅ IP resolve complete", fg="#00ff88")

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
        self.status.config(text="📋 Copied to clipboard!", fg="#00d4ff")

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
        self.status.config(
            text=f"✅ Exported to {os.path.basename(filepath)}", fg="#00ff88")
