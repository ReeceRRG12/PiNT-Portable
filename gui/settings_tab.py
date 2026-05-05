import tkinter as tk


class SettingsTab:
    """Settings panel — configure scan timeouts and monitor poll interval."""

    def __init__(self, parent, root, app_state):
        self._root  = root
        self._state = app_state
        self._build(parent)

    def _build(self, parent):
        frame = tk.Frame(parent, bg="#1a1a2e")
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(frame, text="Settings",
                 bg="#1a1a2e", fg="#00d4ff",
                 font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 4))

        tk.Label(frame,
                 text="Changes take effect immediately on the next scan or monitor start.",
                 bg="#1a1a2e", fg="#555555",
                 font=("Arial", 9, "italic")).pack(anchor="w", pady=(0, 16))

        s = self._state.settings

        self._section(frame, "Scan Timeouts")
        self._port_var = self._setting_row(
            frame, "Port ID scan timeout", s.port_timeout, 5, 120, "seconds")
        self._mdns_var = self._setting_row(
            frame, "mDNS scan timeout", s.mdns_timeout, 5, 120, "seconds")

        self._section(frame, "Port Monitor")
        self._poll_var = self._setting_row(
            frame, "Poll interval", s.monitor_poll_ms // 1000, 1, 30, "seconds")

        tk.Button(frame, text="Apply Settings",
                  command=self._apply,
                  bg="#00d4ff", fg="#1a1a2e",
                  font=("Arial", 11, "bold"),
                  padx=20, relief="flat",
                  highlightthickness=0, borderwidth=0).pack(anchor="w", pady=(20, 4))

        self._feedback = tk.Label(frame, text="",
                                  bg="#1a1a2e", fg="#00ff88",
                                  font=("Arial", 9))
        self._feedback.pack(anchor="w")

    def _section(self, parent, title):
        tk.Frame(parent, bg="#0f3460", height=1).pack(fill="x", pady=(10, 8))
        tk.Label(parent, text=title,
                 bg="#1a1a2e", fg="#aaaaaa",
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 10))

    def _setting_row(self, parent, label, initial, from_, to, unit):
        row = tk.Frame(parent, bg="#1a1a2e")
        row.pack(fill="x", pady=6)

        tk.Label(row, text=label,
                 bg="#1a1a2e", fg="#eeeeee",
                 font=("Arial", 10), width=26, anchor="w").pack(side="left")

        var = tk.IntVar(value=initial)

        val_lbl = tk.Label(row, text=str(initial),
                           bg="#1a1a2e", fg="#00d4ff",
                           font=("Arial", 10, "bold"), width=4, anchor="e")
        val_lbl.pack(side="right")

        tk.Label(row, text=unit,
                 bg="#1a1a2e", fg="#555555",
                 font=("Arial", 9)).pack(side="right", padx=(0, 4))

        tk.Scale(row, from_=from_, to=to,
                 variable=var, orient="horizontal",
                 bg="#1a1a2e", fg="#888888",
                 troughcolor="#16213e",
                 highlightthickness=0,
                 showvalue=False, length=220,
                 command=lambda v, l=val_lbl: l.config(
                     text=str(int(float(v))))).pack(side="left", padx=(8, 0))

        return var

    def _apply(self):
        s = self._state.settings
        s.port_timeout    = self._port_var.get()
        s.mdns_timeout    = self._mdns_var.get()
        s.monitor_poll_ms = self._poll_var.get() * 1000
        self._feedback.config(text="✅ Settings applied")
        self._root.after(2500, lambda: self._feedback.config(text=""))
