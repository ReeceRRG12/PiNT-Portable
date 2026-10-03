import threading

import customtkinter as ctk
from gui import theme, widgets


class IpTab:
    """
    IP Info tab — shows adapter IP config, DHCP server details and scope options.
    """

    def __init__(self, parent, root, app_state):
        self._root  = root
        self._state = app_state
        self._build(parent)

    def _build(self, parent):
        widgets.description(
            parent,
            "Displays the IP configuration of your network adapter, including DHCP "
            "server details and scope options.\n\n"
            "Useful for understanding the network segment you are connected to "
            "without needing switch or router access.")

        top = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        top.pack(fill="x", padx=10, pady=(0, 5))

        self.status = widgets.status_label(top, "Press Scan to load IP & DHCP information")
        self.status.pack(side="left")

        self.scan_btn = widgets.primary_button(top, "Scan", self.start_scan)
        self.scan_btn.pack(side="right")

        # ── Scrollable content area ───────────────────────────────────────────
        self._inner = ctk.CTkScrollableFrame(parent, fg_color=theme.BG)
        self._inner.pack(fill="both", expand=True, padx=10, pady=(0, 5))

    # ── Scan ──────────────────────────────────────────────────────────────────

    def start_scan(self):
        self.scan_btn.configure(state="disabled")
        self.status.configure(
            text="Reading IP config and querying DHCP... (up to 15s)",
            text_color=theme.WARNING)
        for w in self._inner.winfo_children():
            w.destroy()
        # Capture selection now so adapter changes cannot mix two networks.
        threading.Thread(target=self._run_scan,
                         args=(self._state.selected_iface,), daemon=True).start()

    def _run_scan(self, iface):
        try:
            from network.ip_info import get_ip_config, get_dhcp_options
            ip_data = get_ip_config(iface)
            dhcp_opts = (get_dhcp_options(timeout=10, iface=ip_data.get("interface", iface))
                         if ip_data.get("dhcp_enabled") is True and not ip_data.get("error") else [])
        except Exception as exc:
            ip_data, dhcp_opts = {"error": str(exc)}, []
        self._root.after(0, self._update_ui, ip_data, dhcp_opts)

    def _update_ui(self, ip_data, dhcp_opts):
        from network.ip_info import FLAG_COLOURS
        parent = self._inner

        if ip_data.get("error"):
            self.status.configure(text=ip_data["error"], text_color=theme.ERROR)
            self.scan_btn.configure(state="normal")
            return

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

        enabled = ip_data.get("dhcp_enabled")
        self._row(parent, "DHCP Enabled",
                  "Yes" if enabled is True else "No" if enabled is False else "Unavailable",
                  value_colour=theme.SUCCESS if enabled is True else theme.FG_DIM)

        if enabled:
            self._row(parent, "DHCP Server",    ip_data.get("dhcp_server",    "Unknown"))
            self._row(parent, "Lease Obtained", ip_data.get("lease_obtained", "Unknown"))
            self._row(parent, "Lease Expires",  ip_data.get("lease_expires",  "Unknown"))

            self._section(parent, "DHCP Scope Options")

            if dhcp_opts:
                legend = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
                legend.pack(fill="x", padx=10, pady=(0, 6))
                for flag, colour in [("Standard", theme.SUCCESS),
                                     ("Notable",  theme.WARNING),
                                     ("Unknown",  theme.ERROR)]:
                    ctk.CTkLabel(legend, text="●", text_color=colour,
                                 fg_color="transparent",
                                 font=theme.font(9)).pack(side="left")
                    ctk.CTkLabel(legend, text=f" {flag}   ",
                                 text_color=theme.FG_DIM, fg_color="transparent",
                                 font=theme.font(9)).pack(side="left")

                for opt_num, label, value, flag in dhcp_opts:
                    colour = FLAG_COLOURS.get(flag, theme.FG)
                    self._option_row(parent, opt_num, label, value, colour)
            else:
                ctk.CTkLabel(parent,
                             text="No scope options returned by DHCP server.",
                             fg_color="transparent", text_color=theme.FG_DIM,
                             font=theme.font(10)).pack(padx=10, pady=4, anchor="w")
        elif enabled is False:
            ctk.CTkLabel(parent, text="DHCP is not enabled on this adapter.",
                         fg_color="transparent", text_color=theme.FG_DIM,
                         font=theme.font(10)).pack(padx=10, pady=4, anchor="w")

        self._state.session.add_ip_snapshot(ip_data, dhcp_opts)
        probe_error = next((value for number, label, value, flag in dhcp_opts
                            if number == 0 and label == "Error"), None)
        warning = ip_data.get("warning") or (
            f"IP information loaded; DHCP query failed: {probe_error}" if probe_error else None)
        self.status.configure(
            text=warning or "IP & DHCP information loaded",
            text_color=theme.WARNING if warning else theme.SUCCESS)
        self.scan_btn.configure(state="normal")

    # ── Widget helpers ────────────────────────────────────────────────────────

    def _section(self, parent, text):
        frame = ctk.CTkFrame(parent, fg_color=theme.DIVIDER, corner_radius=0)
        frame.pack(fill="x", padx=0, pady=(10, 2))
        ctk.CTkLabel(frame, text=text,
                     fg_color="transparent", text_color=theme.ACCENT,
                     font=theme.font(10, "bold"),
                     anchor="w").pack(anchor="w", padx=10, pady=4)

    def _row(self, parent, label, value, value_colour=None):
        if value_colour is None:
            value_colour = theme.FG
        frame = ctk.CTkFrame(parent, fg_color=theme.PANEL, corner_radius=0)
        frame.pack(fill="x", padx=0, pady=1)
        ctk.CTkLabel(frame, text=label,
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(10), width=150, anchor="w").pack(
                         side="left", padx=10)
        ctk.CTkLabel(frame, text=value,
                     fg_color="transparent", text_color=value_colour,
                     font=theme.font(10), anchor="w").pack(
                         side="left", padx=(0, 10))

    def _option_row(self, parent, opt_num, label, value, colour):
        frame = ctk.CTkFrame(parent, fg_color=theme.PANEL, corner_radius=0)
        frame.pack(fill="x", padx=0, pady=1)
        ctk.CTkLabel(frame, text="●", text_color=colour,
                     fg_color="transparent",
                     font=theme.font(9), width=20).pack(side="left", padx=6)
        ctk.CTkLabel(frame, text=f"{opt_num:>3}",
                     text_color=theme.FG_HINT, fg_color="transparent",
                     font=theme.font(9, "bold"), width=24).pack(side="left")
        ctk.CTkLabel(frame, text=label,
                     text_color=theme.FG_DIM, fg_color="transparent",
                     font=theme.font(10), width=176, anchor="w").pack(side="left")
        ctk.CTkLabel(frame, text=value,
                     text_color=colour, fg_color="transparent",
                     font=theme.font(10), anchor="w").pack(
                         side="left", padx=(0, 10))
