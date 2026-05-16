import tkinter as tk
from tkinter import ttk
import threading

import customtkinter as ctk
from gui import theme
from snmp_query import COMMON_OIDS


class SnmpTab:
    """SNMP query tab — GET or WALK against a v1/v2c device."""

    def __init__(self, parent, root, app_state):
        self._root    = root
        self._state   = app_state
        self._results = []
        self._build(parent)

    def _build(self, parent):
        _desc = tk.Label(
            parent,
            text="Query SNMP-enabled devices (switches, routers, APs) using community-string authentication.\n\n"
                 "GET retrieves a single OID value. WALK traverses an OID subtree and returns all values beneath it.",
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
            top, text="Enter host details and press Query",
            fg_color="transparent", text_color=theme.FG_DIM,
            font=theme.font(10))
        self._status.pack(side="left")

        self._query_btn = ctk.CTkButton(
            top, text="Query",
            command=self._start_query,
            fg_color=theme.ACCENT, text_color=theme.BG,
            hover_color="#00b8d9",
            font=theme.font(10, "bold"),
            corner_radius=6, border_width=0, width=80)
        self._query_btn.pack(side="right")

        # ── Connection row ────────────────────────────────────────────────────
        row1 = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        row1.pack(fill="x", padx=10, pady=(0, 4))

        ctk.CTkLabel(row1, text="Host:",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left")
        self._host_var = tk.StringVar()
        ctk.CTkEntry(row1,
                     textvariable=self._host_var,
                     placeholder_text="192.168.1.1",
                     fg_color=theme.PANEL, text_color=theme.FG,
                     border_color=theme.DIVIDER, border_width=1,
                     font=theme.font(10), width=150).pack(side="left", padx=(5, 14))

        ctk.CTkLabel(row1, text="Community:",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left")
        self._community_var = tk.StringVar(value="public")
        ctk.CTkEntry(row1,
                     textvariable=self._community_var,
                     fg_color=theme.PANEL, text_color=theme.FG,
                     border_color=theme.DIVIDER, border_width=1,
                     font=theme.font(10), width=100).pack(side="left", padx=(5, 14))

        ctk.CTkLabel(row1, text="Port:",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left")
        self._port_var = tk.StringVar(value="161")
        ctk.CTkEntry(row1,
                     textvariable=self._port_var,
                     fg_color=theme.PANEL, text_color=theme.FG,
                     border_color=theme.DIVIDER, border_width=1,
                     font=theme.font(10), width=55).pack(side="left", padx=(5, 14))

        ctk.CTkLabel(row1, text="Version:",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left")
        self._version_var = tk.StringVar(value="v2c")
        ctk.CTkOptionMenu(
            row1,
            values=["v2c", "v1"],
            variable=self._version_var,
            fg_color=theme.PANEL, text_color=theme.FG,
            button_color=theme.DIVIDER, button_hover_color="#1f2d45",
            dropdown_fg_color=theme.PANEL, dropdown_text_color=theme.FG,
            dropdown_hover_color="#1f2d45",
            font=theme.font(10), width=70).pack(side="left", padx=5)

        # ── OID row ───────────────────────────────────────────────────────────
        row2 = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        row2.pack(fill="x", padx=10, pady=(0, 4))

        ctk.CTkLabel(row2, text="OID:",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left")

        self._oid_var = tk.StringVar(value=COMMON_OIDS["System Description"])
        ctk.CTkEntry(row2,
                     textvariable=self._oid_var,
                     fg_color=theme.PANEL, text_color=theme.FG,
                     border_color=theme.DIVIDER, border_width=1,
                     font=theme.font(10), width=260).pack(side="left", padx=(5, 10))

        ctk.CTkLabel(row2, text="Preset:",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left")
        self._oid_preset_var = tk.StringVar(value="System Description")
        ctk.CTkOptionMenu(
            row2,
            values=list(COMMON_OIDS.keys()),
            variable=self._oid_preset_var,
            command=self._on_oid_preset,
            fg_color=theme.PANEL, text_color=theme.FG,
            button_color=theme.DIVIDER, button_hover_color="#1f2d45",
            dropdown_fg_color=theme.PANEL, dropdown_text_color=theme.FG,
            dropdown_hover_color="#1f2d45",
            font=theme.font(10), width=180).pack(side="left", padx=(5, 14))

        ctk.CTkLabel(row2, text="Operation:",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10)).pack(side="left")
        self._op_var = tk.StringVar(value="GET")
        ctk.CTkOptionMenu(
            row2,
            values=["GET", "WALK"],
            variable=self._op_var,
            fg_color=theme.PANEL, text_color=theme.FG,
            button_color=theme.DIVIDER, button_hover_color="#1f2d45",
            dropdown_fg_color=theme.PANEL, dropdown_text_color=theme.FG,
            dropdown_hover_color="#1f2d45",
            font=theme.font(10), width=75).pack(side="left", padx=5)

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
            columns=("oid", "value"),
            show="headings",
            style="PiNT.Treeview",
            selectmode="browse")
        self._tree.heading("oid",   text="OID")
        self._tree.heading("value", text="Value")
        self._tree.column("oid",   width=300)
        self._tree.column("value", width=380)

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

    # ── OID preset ────────────────────────────────────────────────────────────

    def _on_oid_preset(self, label):
        self._oid_var.set(COMMON_OIDS.get(label, ""))

    # ── Query ─────────────────────────────────────────────────────────────────

    def _start_query(self):
        host      = self._host_var.get().strip()
        community = self._community_var.get().strip()
        oid       = self._oid_var.get().strip()

        if not host:
            self._status.configure(text="Enter a host", text_color=theme.ERROR)
            return
        if not oid:
            self._status.configure(text="Enter an OID", text_color=theme.ERROR)
            return

        try:
            port = int(self._port_var.get())
        except ValueError:
            port = 161

        version = 1 if self._version_var.get() == "v2c" else 0
        op      = self._op_var.get()

        self._query_btn.configure(state="disabled")
        self._copy_btn.configure(state="disabled")
        self._status.configure(
            text=f"{op} {oid} on {host}...", text_color=theme.WARNING)
        for row in self._tree.get_children():
            self._tree.delete(row)
        self._results = []
        self._detail.configure(text="")
        self._progress.start(10)

        threading.Thread(
            target=self._run_query,
            args=(host, community, oid, port, version, op),
            daemon=True).start()

    def _run_query(self, host, community, oid, port, version, op):
        from snmp_query import snmp_get, snmp_walk

        if op == "GET":
            value, err = snmp_get(host, community, oid, port=port, version=version)
            if err:
                self._root.after(0, self._finish_error, err)
            else:
                self._root.after(0, self._update_ui, [(oid, value)])
        else:
            rows = []
            errors = []

            def _row(o, v, e):
                if e:
                    errors.append(e)
                elif o is not None:
                    rows.append((o, v))

            snmp_walk(host, community, oid, port=port, version=version,
                      row_callback=_row)

            if errors and not rows:
                self._root.after(0, self._finish_error, errors[0])
            else:
                self._root.after(0, self._update_ui, rows)

    def _update_ui(self, rows):
        self._progress.stop()
        self._results = rows
        for oid, value in rows:
            self._tree.insert("", "end", values=(oid, value))
        count = len(rows)
        self._status.configure(
            text=f"✅ {count} result{'s' if count != 1 else ''}",
            text_color=theme.SUCCESS if count > 0 else theme.FG_DIM)
        self._query_btn.configure(state="normal")
        if rows:
            self._copy_btn.configure(state="normal")

    def _finish_error(self, msg):
        self._progress.stop()
        self._status.configure(text=f"Error: {msg}", text_color=theme.ERROR)
        self._query_btn.configure(state="normal")

    # ── Events ────────────────────────────────────────────────────────────────

    def _on_select(self, _event):
        sel = self._tree.selection()
        if sel:
            vals = self._tree.item(sel[0], "values")
            if vals:
                self._detail.configure(text=f"  {vals[1]}")

    def _copy(self):
        if not self._results:
            return
        lines = ["OID\tValue"]
        for oid, value in self._results:
            lines.append(f"{oid}\t{value}")
        self._root.clipboard_clear()
        self._root.clipboard_append("\n".join(lines))
        self._status.configure(text="📋 Copied to clipboard!", text_color=theme.ACCENT)
