import tkinter as tk
from tkinter import ttk, filedialog
import os
from datetime import datetime


class ExportTab:
    """
    Export tab — accumulates session results and exports them to XLS.
    Call refresh() whenever the session changes (wired up in pint.py).
    """

    def __init__(self, parent, root, app_state):
        self._root  = root
        self._state = app_state
        self._build(parent)

    def _build(self, parent):
        tk.Label(parent,
                 text="Accumulates results from all tabs during your session and exports them "
                      "to a formatted Excel file. Run scans across multiple ports to build up "
                      "a full picture before exporting — ideal for switch audits.",
                 bg="#1a1a2e", fg="#888888",
                 font=("Arial", 10),
                 wraplength=1050, justify="left").pack(
                     fill="x", padx=10, pady=(8, 6), anchor="w")

        header = tk.Frame(parent, bg="#1a1a2e")
        header.pack(fill="x", padx=10, pady=(0, 5))

        self._status = tk.Label(header, text="No data in session yet",
                                bg="#1a1a2e", fg="#888888")
        self._status.pack(side="left")

        tk.Button(header, text="Clear Session",
                  command=self._clear_session,
                  bg="#16213e", fg="#ff4757",
                  font=("Arial", 9), padx=10,
                  relief="flat", highlightthickness=0, borderwidth=0).pack(side="right")

        # ── Session tree ──────────────────────────────────────────────────────
        tree_frame = tk.Frame(parent, bg="#1a1a2e")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        style = ttk.Style()
        style.configure("Treeview",
                        background="#16213e", foreground="#eee",
                        fieldbackground="#16213e", bordercolor="#16213e",
                        rowheight=28, font=("Arial", 10))
        style.configure("Treeview.Heading",
                        background="#0f3460", foreground="#00d4ff",
                        bordercolor="#0f3460",
                        font=("Arial", 10, "bold"))
        style.map("Treeview",
                  background=[("selected", "#0f3460")],
                  foreground=[("selected", "#ffffff")])

        self._tree = ttk.Treeview(tree_frame,
                                   columns=("time", "type", "summary"),
                                   show="headings",
                                   selectmode="browse")
        self._tree.heading("time",    text="Timestamp")
        self._tree.heading("type",    text="Type")
        self._tree.heading("summary", text="Summary")
        self._tree.column("time",    width=140)
        self._tree.column("type",    width=90)
        self._tree.column("summary", width=230)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # ── Export buttons ────────────────────────────────────────────────────
        btn_frame = tk.Frame(parent, bg="#1a1a2e")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        self._export_btn = tk.Button(btn_frame, text="Export XLS",
                                      command=self._do_export,
                                      bg="#00d4ff", fg="#1a1a2e",
                                      font=("Arial", 11, "bold"),
                                      padx=20, relief="flat",
                                      highlightthickness=0, borderwidth=0,
                                      state="disabled")
        self._export_btn.pack(side="left", padx=(0, 5))

        self._result_label = tk.Label(btn_frame, text="",
                                       bg="#1a1a2e", fg="#00ff88",
                                       font=("Arial", 9))
        self._result_label.pack(side="left", padx=10)

    # ── Refresh (called by session listener) ──────────────────────────────────

    def refresh(self):
        session = self._state.session
        for row in self._tree.get_children():
            self._tree.delete(row)

        for entry in session.port_scans:
            summary = f"{entry['switch']} — {entry['port']} ({entry['protocol']})"
            self._tree.insert("", "end",
                               values=(entry["timestamp"], "Port Scan", summary))

        for entry in session.ip_snapshots:
            summary = (f"{entry['ip']} via {entry['dhcp_server']}"
                       if entry["dhcp_enabled"] else f"{entry['ip']} (static)")
            self._tree.insert("", "end",
                               values=(entry["timestamp"], "IP Snapshot", summary))

        for entry in session.mdns_scans:
            count   = len(entry["devices"])
            summary = f"{count} device{'s' if count != 1 else ''} discovered"
            self._tree.insert("", "end",
                               values=(entry["timestamp"], "mDNS Scan", summary))

        total = session.total_entries()
        if total == 0:
            self._status.config(text="No data in session yet", fg="#888888")
            self._export_btn.config(state="disabled")
        else:
            parts = []
            if session.port_scans:
                n = len(session.port_scans)
                parts.append(f"{n} port scan{'s' if n != 1 else ''}")
            if session.ip_snapshots:
                n = len(session.ip_snapshots)
                parts.append(f"{n} IP snapshot{'s' if n != 1 else ''}")
            if session.mdns_scans:
                n = len(session.mdns_scans)
                parts.append(f"{n} mDNS scan{'s' if n != 1 else ''}")
            self._status.config(text="Session: " + ", ".join(parts), fg="#00d4ff")
            self._export_btn.config(state="normal")

    # ── Export / clear ────────────────────────────────────────────────────────

    def _do_export(self):
        session = self._state.session
        if not session.has_data():
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=f"pint_session_{timestamp}.xlsx",
            title="Export session to XLS"
        )
        if not filepath:
            return
        try:
            from exporter import export_xlsx
            export_xlsx(session, filepath)
            self._result_label.config(
                text=f"✅ Saved {os.path.basename(filepath)}", fg="#00ff88")
        except Exception as e:
            self._result_label.config(text=f"❌ Export failed: {e}", fg="#ff4757")

    def _clear_session(self):
        import tkinter.messagebox as mb
        session = self._state.session
        if not session.has_data():
            return
        if mb.askyesno("Clear Session",
                        "This will remove all accumulated scan results.\n\nAre you sure?"):
            session.clear()
            self._result_label.config(text="")
