import tkinter as tk
from tkinter import ttk, filedialog
import os
from datetime import datetime

import customtkinter as ctk
from gui import theme


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
        _desc = tk.Label(parent,
                         text="Accumulates results from all tabs during your session and exports them "
                              "to a formatted Excel file.\n\n"
                              "Run scans across multiple ports to build up a full picture before "
                              "exporting — ideal for switch audits.",
                         bg=theme.BG, fg=theme.FG_DIM,
                         font=theme.tk_font(12),
                         wraplength=600, justify="center")
        _desc.pack(fill="x", padx=20, pady=(12, 8))
        parent.bind("<Configure>", lambda e: _desc.configure(wraplength=max(100, e.width - 40)), add="+")

        header = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        header.pack(fill="x", padx=10, pady=(0, 5))

        self._status = ctk.CTkLabel(header, text="No data in session yet",
                                    fg_color="transparent", text_color=theme.FG_DIM,
                                    font=theme.font(10))
        self._status.pack(side="left")

        ctk.CTkButton(header, text="Clear Session",
                      command=self._clear_session,
                      fg_color=theme.PANEL, text_color=theme.ERROR,
                      hover_color="#1f2d45",
                      font=theme.font(9),
                      corner_radius=6, border_width=0,
                      width=110).pack(side="right")

        # ── Session tree ──────────────────────────────────────────────────────
        tree_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        style = ttk.Style()
        theme.apply_treeview_style(style)

        self._tree = ttk.Treeview(tree_frame,
                                   columns=("time", "type", "summary"),
                                   show="headings",
                                   style="PiNT.Treeview",
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
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        self._export_btn = ctk.CTkButton(btn_frame, text="Export XLS",
                                          command=self._do_export,
                                          fg_color=theme.ACCENT, text_color=theme.BG,
                                          hover_color="#00b8d9",
                                          font=theme.font(11, "bold"),
                                          corner_radius=6, border_width=0,
                                          width=120, state="disabled")
        self._export_btn.pack(side="left", padx=(0, 5))

        self._result_label = ctk.CTkLabel(btn_frame, text="",
                                           fg_color="transparent",
                                           text_color=theme.SUCCESS,
                                           font=theme.font(9))
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
            self._status.configure(text="No data in session yet", text_color=theme.FG_DIM)
            self._export_btn.configure(state="disabled")
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
            self._status.configure(
                text="Session: " + ", ".join(parts), text_color=theme.ACCENT)
            self._export_btn.configure(state="normal")

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
            self._result_label.configure(
                text=f"✅ Saved {os.path.basename(filepath)}",
                text_color=theme.SUCCESS)
        except Exception as e:
            self._result_label.configure(
                text=f"❌ Export failed: {e}", text_color=theme.ERROR)

    def _clear_session(self):
        import tkinter.messagebox as mb
        session = self._state.session
        if not session.has_data():
            return
        if mb.askyesno("Clear Session",
                        "This will remove all accumulated scan results.\n\nAre you sure?"):
            session.clear()
            self._result_label.configure(text="")
