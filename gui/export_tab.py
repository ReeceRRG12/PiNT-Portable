from tkinter import filedialog
import os
from datetime import datetime

import customtkinter as ctk
from gui import theme, widgets


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
        widgets.description(
            parent,
            "Accumulates results from all tabs during your session and exports them "
            "to a formatted Excel file.\n\n"
            "Run scans across multiple ports to build up a full picture before "
            "exporting — ideal for switch audits.")

        header = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        header.pack(fill="x", padx=10, pady=(0, 5))

        self._status = widgets.status_label(header, "No data in session yet")
        self._status.pack(side="left")

        widgets.secondary_button(
            header, "Clear Session", self._clear_session,
            width=110, text_color=theme.ERROR).pack(side="right")

        # ── Session tree ──────────────────────────────────────────────────────
        self._tree, tree_frame = widgets.results_tree(parent, [
            ("time",    "Timestamp", 140),
            ("type",    "Type",       90),
            ("summary", "Summary",   230),
        ])
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        # ── Export buttons ────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        self._export_btn = widgets.primary_button(
            btn_frame, "Export XLS", self._do_export,
            width=120, font=theme.font(11, "bold"), state="disabled")
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
