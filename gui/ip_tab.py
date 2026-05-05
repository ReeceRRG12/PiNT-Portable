import tkinter as tk
from tkinter import ttk
import threading


class IpTab:
    """
    IP Info tab — shows adapter IP config, DHCP server details and scope options.
    """

    def __init__(self, parent, root, app_state):
        self._root  = root
        self._state = app_state
        self._build(parent)

    def _build(self, parent):
        tk.Label(parent,
                 text="Displays the IP configuration of your network adapter, including DHCP "
                      "server details and scope options. Useful for understanding the network "
                      "segment you are connected to without needing switch or router access.",
                 bg="#1a1a2e", fg="#888888",
                 font=("Arial", 10),
                 wraplength=1050, justify="left").pack(
                     fill="x", padx=10, pady=(8, 6), anchor="w")

        top = tk.Frame(parent, bg="#1a1a2e")
        top.pack(fill="x", padx=10, pady=(0, 5))

        self.status = tk.Label(top,
                               text="Press Scan to load IP & DHCP information",
                               bg="#1a1a2e", fg="#888888")
        self.status.pack(side="left")

        self.scan_btn = tk.Button(top, text="Scan",
                                  command=self.start_scan,
                                  bg="#00d4ff", fg="#1a1a2e",
                                  font=("Arial", 10, "bold"),
                                  padx=15, relief="flat",
                                  highlightthickness=0, borderwidth=0)
        self.scan_btn.pack(side="right")

        # ── Scrollable canvas ─────────────────────────────────────────────────
        canvas_frame = tk.Frame(parent, bg="#1a1a2e")
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self._canvas = tk.Canvas(canvas_frame, bg="#1a1a2e", highlightthickness=0)
        sb = ttk.Scrollbar(canvas_frame, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas, bg="#1a1a2e")
        self._win = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>",
                         lambda _: self._canvas.configure(
                             scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(self._win, width=e.width))

        self._canvas.bind("<Enter>",
                          lambda _: self._canvas.bind_all("<MouseWheel>", self._on_wheel))
        self._canvas.bind("<Leave>",
                          lambda _: self._canvas.unbind_all("<MouseWheel>"))

    def _on_wheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Scan ──────────────────────────────────────────────────────────────────

    def start_scan(self):
        self.scan_btn.config(state="disabled")
        self.status.config(
            text="Reading IP config and querying DHCP... (up to 15s)", fg="#ffaa00")
        for w in self._inner.winfo_children():
            w.destroy()
        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        from ip_info import get_ip_config, get_dhcp_options
        ip_data  = get_ip_config()
        dhcp_opts = (get_dhcp_options(timeout=10, iface=self._state.selected_iface)
                     if ip_data.get("dhcp_enabled") else [])
        self._root.after(0, self._update_ui, ip_data, dhcp_opts)

    def _update_ui(self, ip_data, dhcp_opts):
        from ip_info import FLAG_COLOURS
        parent = self._inner

        self._section(parent, "IP Configuration")

        rows = [
            ("Adapter",     ip_data.get("adapter",  "Unknown")),
            ("Hostname",    ip_data.get("hostname",  "Unknown")),
            ("MAC Address", ip_data.get("mac",       "Unknown")),
            ("IP Address",  ip_data.get("ip",        "Unknown")),
            ("Subnet Mask", ip_data.get("subnet",    "Unknown")),
            ("Gateway",     ip_data.get("gateway",   "Unknown")),
            ("Domain",      ip_data.get("domain",    "Unknown")),
        ]
        for i, dns in enumerate(ip_data.get("dns", [])):
            rows.append(("DNS Server" if i == 0 else f"DNS Server {i+1}", dns))

        for label, value in rows:
            self._row(parent, label, value)

        self._section(parent, "DHCP")

        enabled = ip_data.get("dhcp_enabled", False)
        self._row(parent, "DHCP Enabled",
                  "Yes" if enabled else "No",
                  value_colour="#00ff88" if enabled else "#ff4757")

        if enabled:
            self._row(parent, "DHCP Server",    ip_data.get("dhcp_server",    "Unknown"))
            self._row(parent, "Lease Obtained", ip_data.get("lease_obtained", "Unknown"))
            self._row(parent, "Lease Expires",  ip_data.get("lease_expires",  "Unknown"))

            self._section(parent, "DHCP Scope Options")

            if dhcp_opts:
                legend = tk.Frame(parent, bg="#1a1a2e")
                legend.pack(fill="x", padx=10, pady=(0, 6))
                for flag, colour in [("Standard", "#00ff88"),
                                     ("Notable",  "#ffaa00"),
                                     ("Unknown",  "#ff4757")]:
                    tk.Label(legend, text="●", fg=colour,
                             bg="#1a1a2e", font=("Arial", 9)).pack(side="left")
                    tk.Label(legend, text=f" {flag}   ",
                             fg="#888888", bg="#1a1a2e",
                             font=("Arial", 9)).pack(side="left")

                for opt_num, label, value, flag in dhcp_opts:
                    colour = FLAG_COLOURS.get(flag, "#eee")
                    self._option_row(parent, opt_num, label, value, colour)
            else:
                tk.Label(parent, text="No scope options returned by DHCP server.",
                         bg="#1a1a2e", fg="#888888",
                         font=("Arial", 10)).pack(padx=10, pady=4, anchor="w")
        else:
            tk.Label(parent, text="DHCP is not enabled on this adapter.",
                     bg="#1a1a2e", fg="#888888",
                     font=("Arial", 10)).pack(padx=10, pady=4, anchor="w")

        self._state.session.add_ip_snapshot(ip_data, dhcp_opts)
        self.status.config(text="✅ IP & DHCP information loaded", fg="#00ff88")
        self.scan_btn.config(state="normal")

    # ── Widget helpers ────────────────────────────────────────────────────────

    def _section(self, parent, text):
        frame = tk.Frame(parent, bg="#0f3460")
        frame.pack(fill="x", padx=0, pady=(10, 2))
        tk.Label(frame, text=text,
                 bg="#0f3460", fg="#00d4ff",
                 font=("Arial", 10, "bold"),
                 padx=10, pady=4).pack(anchor="w")

    def _row(self, parent, label, value, value_colour="#eee"):
        frame = tk.Frame(parent, bg="#16213e")
        frame.pack(fill="x", padx=0, pady=1)
        tk.Label(frame, text=label,
                 bg="#16213e", fg="#888888",
                 font=("Arial", 10), width=18, anchor="w",
                 padx=10).pack(side="left")
        tk.Label(frame, text=value,
                 bg="#16213e", fg=value_colour,
                 font=("Arial", 10), anchor="w").pack(side="left", padx=(0, 10))

    def _option_row(self, parent, opt_num, label, value, colour):
        frame = tk.Frame(parent, bg="#16213e")
        frame.pack(fill="x", padx=0, pady=1)
        tk.Label(frame, text="●", fg=colour,
                 bg="#16213e", font=("Arial", 9), padx=6).pack(side="left")
        tk.Label(frame, text=f"{opt_num:>3}",
                 bg="#16213e", fg="#555",
                 font=("Arial", 9, "bold"), width=3).pack(side="left")
        tk.Label(frame, text=label,
                 bg="#16213e", fg="#888888",
                 font=("Arial", 10), width=22, anchor="w").pack(side="left")
        tk.Label(frame, text=value,
                 bg="#16213e", fg=colour,
                 font=("Arial", 10), anchor="w").pack(side="left", padx=(0, 10))
