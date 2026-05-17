import tkinter as tk

import customtkinter as ctk
from gui import theme


class SettingsTab:
    """Settings panel — configure scan timeouts and monitor poll interval."""

    def __init__(self, parent, root, app_state):
        self._root  = root
        self._state = app_state
        self._build(parent)

    def _build(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(frame, text="Settings",
                     fg_color="transparent", text_color=theme.ACCENT,
                     font=theme.font(14, "bold")).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(frame,
                     text="Changes take effect immediately on the next scan or monitor start.",
                     fg_color="transparent", text_color=theme.FG_HINT,
                     font=theme.font(9, "italic")).pack(anchor="w", pady=(0, 16))

        s = self._state.settings

        self._section(frame, "Scan Timeouts")
        self._port_var = self._setting_row(
            frame, "Port ID scan timeout", s.port_timeout, 5, 120, "seconds")
        self._mdns_var = self._setting_row(
            frame, "mDNS scan timeout", s.mdns_timeout, 5, 120, "seconds")

        self._section(frame, "Port Monitor")
        self._poll_var = self._setting_row(
            frame, "Poll interval", s.monitor_poll_ms // 1000, 1, 30, "seconds")

        ctk.CTkButton(frame, text="Apply Settings",
                      command=self._apply,
                      fg_color=theme.ACCENT, text_color=theme.BG,
                      hover_color=theme.ACCENT_HOVER,
                      font=theme.font(11, "bold"),
                      corner_radius=6, border_width=0,
                      width=150).pack(anchor="w", pady=(20, 4))

        self._feedback = ctk.CTkLabel(frame, text="",
                                      fg_color="transparent", text_color=theme.SUCCESS,
                                      font=theme.font(9))
        self._feedback.pack(anchor="w")

    def _section(self, parent, title):
        ctk.CTkFrame(parent, fg_color=theme.DIVIDER,
                     height=2, corner_radius=0).pack(fill="x", pady=(10, 8))
        ctk.CTkLabel(parent, text=title,
                     fg_color="transparent", text_color=theme.FG_MUTED,
                     font=theme.font(10, "bold")).pack(anchor="w", pady=(0, 10))

    def _setting_row(self, parent, label, initial, from_, to, unit):
        row = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        row.pack(fill="x", pady=6)

        ctk.CTkLabel(row, text=label,
                     fg_color="transparent", text_color=theme.FG,
                     font=theme.font(10), width=210, anchor="w").pack(side="left")

        var = tk.IntVar(value=initial)

        val_lbl = ctk.CTkLabel(row, text=str(initial),
                               fg_color="transparent", text_color=theme.ACCENT,
                               font=theme.font(10, "bold"), width=32, anchor="e")
        val_lbl.pack(side="right")

        ctk.CTkLabel(row, text=unit,
                     fg_color="transparent", text_color=theme.FG_HINT,
                     font=theme.font(9)).pack(side="right", padx=(0, 4))

        ctk.CTkSlider(row,
                      from_=from_, to=to,
                      variable=var,
                      number_of_steps=int(to - from_),
                      fg_color=theme.PANEL,
                      progress_color=theme.ACCENT,
                      button_color=theme.ACCENT,
                      button_hover_color=theme.ACCENT_HOVER,
                      width=220,
                      command=lambda v, l=val_lbl: l.configure(
                          text=str(round(float(v))))).pack(side="left", padx=(8, 0))

        return var

    def _apply(self):
        s = self._state.settings
        s.port_timeout    = self._port_var.get()
        s.mdns_timeout    = self._mdns_var.get()
        s.monitor_poll_ms = self._poll_var.get() * 1000
        self._feedback.configure(text="✅ Settings applied")
        self._root.after(2500, lambda: self._feedback.configure(text=""))
