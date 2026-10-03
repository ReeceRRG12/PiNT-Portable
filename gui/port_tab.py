import threading
import webbrowser

import customtkinter as ctk
from gui import theme, widgets
from gui.desktop import launch_terminal, management_address


class PortTab:
    """
    Port ID tab — listens for LLDP/CDP to identify the connected switch port.
    Shows a card grid of fields that populate once a switch is detected.
    Shows quick-launch buttons (SSH, Telnet, HTTP, HTTPS) once a management IP
    is detected.
    """

    def __init__(self, parent, root, app_state):
        self._root   = root
        self._state  = app_state
        self._device = {}
        self._build(parent)

    def _build(self, parent):
        widgets.description(parent,
            "Identify the switch and port behind your Ethernet connection. "
            "Listen for LLDP and CDP announcements from the connected switch.")

        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(6, 16))
        self.status = widgets.status_label(toolbar, "Ready to identify your connection")
        self.status.pack(side="left", fill="x", expand=True)
        self.scan_btn = widgets.primary_button(
            toolbar, "Identify port", self.start_scan, width=130)
        self.scan_btn.pack(side="right", padx=(12, 0))
        self._progress = widgets.scan_progressbar(
            parent, fill="x", padx=20, pady=(0, 16))

        grid = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        grid.pack(fill="x", padx=14, pady=(0, 12))
        grid.columnconfigure((0, 1, 2), weight=1, uniform="col")
        self._switch_val   = self._card(grid, "CONNECTED SWITCH", 0, 0, primary=True)
        self._port_val     = self._card(grid, "SWITCH PORT",      1, 0, primary=True)
        self._protocol_val = self._card(grid, "PROTOCOL",         2, 0)
        self._model_val    = self._card(grid, "Model",            0, 1)
        self._ip_val       = self._card(grid, "Management IP",    1, 1)
        self._vlan_val     = self._card(grid, "VLAN",             2, 1)

        self._ql_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        for label, cmd in [("SSH", self._launch_ssh), ("Telnet", self._launch_telnet),
                           ("HTTP", self._open_http), ("HTTPS", self._open_https)]:
            widgets.secondary_button(self._ql_frame, label, cmd, width=95).pack(
                side="left", padx=4)

        self._btn_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        self._btn_frame.pack(fill="x", padx=20, pady=8)
        self.copy_btn = widgets.secondary_button(
            self._btn_frame, "Copy connection details", self.copy_to_clipboard,
            width=180, state="disabled")
        self.copy_btn.pack(side="left")
        self._help = ctk.CTkLabel(
            parent, text="Connect to a managed switch, choose your adapter, then identify the port.",
            text_color=theme.FG_DIM, font=theme.font(11), anchor="w", justify="left",
            wraplength=650)
        self._help.pack(fill="x", padx=20, pady=(12, 8))
        parent.bind("<Configure>", lambda e: self._help.configure(
            wraplength=max(250, e.width - 40)), add="+")

    def _card(self, parent, label, col, row, primary=False):
        card = ctk.CTkFrame(parent, fg_color=theme.PANEL, corner_radius=10,
                            border_width=1, border_color=theme.DIVIDER)
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        ctk.CTkLabel(card, text=label, fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(11), anchor="w").pack(
                         anchor="w", padx=18, pady=(18, 8))
        val = ctk.CTkLabel(card, text="—", fg_color="transparent",
                           text_color=theme.FG_DIM,
                           font=theme.font(24 if primary else 15, "bold"),
                           anchor="w", wraplength=180, justify="left")
        val.pack(anchor="w", fill="x", padx=18, pady=(0, 18))
        card.bind("<Configure>", lambda e: val.configure(
            wraplength=max(100, e.width / val._get_widget_scaling() - 36)), add="+")
        return val

    def _reset_cards(self, colour=None):
        for v in (self._switch_val, self._port_val, self._protocol_val,
                  self._model_val,  self._ip_val,   self._vlan_val):
            v.configure(text="—", text_color=colour or theme.FG_DIM)

    # ── Scan logic ────────────────────────────────────────────────────────────

    def start_scan(self):
        timeout = self._state.settings.port_timeout
        self.scan_btn.configure(state="disabled")
        self.status.configure(
            text=f"Scanning for LLDP and CDP... (up to {timeout}s)",
            text_color=theme.WARNING)
        self._device = {}
        self.copy_btn.configure(state="disabled")
        self._help.configure(text="Listening for switch announcements…", text_color=theme.FG_DIM)
        self._reset_cards()
        self._ql_frame.pack_forget()
        self._progress.start(10)
        threading.Thread(target=self._run_scan,
                         args=(timeout, self._state.selected_iface), daemon=True).start()

    def _run_scan(self, timeout, iface):
        try:
            from network.scanner import scan
            scan(self._handle_result, timeout=timeout, iface=iface,
                 error_callback=lambda e: self._root.after(0, self._scan_error, e))
        except Exception as exc:
            self._root.after(0, self._scan_error, str(exc))

    def _scan_error(self, message):
        self._progress.stop()
        self.status.configure(text="Could not capture switch announcements", text_color=theme.ERROR)
        self._help.configure(text=message, text_color=theme.ERROR)
        self.scan_btn.configure(state="normal")

    def _handle_result(self, device):
        self._root.after(0, self._update_ui, device)

    def _update_ui(self, device):
        self._progress.stop()

        if device:
            protocol     = device.get('protocol', 'Unknown')
            proto_colour = theme.ACCENT if protocol == "LLDP" else theme.WARNING

            self._switch_val.configure(
                text=device.get('name', '—'), text_color=theme.FG)
            self._port_val.configure(
                text=device.get('port', '—'), text_color=theme.FG)
            self._protocol_val.configure(
                text=protocol, text_color=proto_colour)
            self._model_val.configure(
                text=device.get('description', device.get('model', '—')),
                text_color=theme.FG)
            self._ip_val.configure(
                text=device.get('ip', '—'), text_color=theme.ACCENT)
            self._vlan_val.configure(
                text=str(device.get('vlan', '—')), text_color=theme.FG)

            self._device = device
            self.copy_btn.configure(state="normal")
            self._help.configure(text="Connection saved to this session. Open Export to save your findings.", text_color=theme.FG_DIM)
            self.status.configure(
                text=f"✅ Switch detected via {protocol}!", text_color=proto_colour)
            self._state.session.add_port_scan(device)

            if self._mgmt_ip():
                self._ql_frame.pack(before=self._btn_frame, pady=(0, 4))
        else:
            self._reset_cards(theme.ERROR)
            self.status.configure(
                text="No switch detected. Are you plugged into a managed switch?",
                text_color=theme.ERROR)
            self._ql_frame.pack_forget()
            self._help.configure(text="Check the selected Ethernet adapter. The switch must advertise LLDP or CDP.", text_color=theme.FG_DIM)

        self.scan_btn.configure(state="normal")

    # ── Clipboard ─────────────────────────────────────────────────────────────

    def copy_to_clipboard(self):
        if not self._device:
            return
        d = self._device
        text = (f"Switch: {d.get('name', 'Unknown')} | "
                f"Port: {d.get('port', 'Unknown')} | "
                f"Model: {d.get('description', d.get('model', 'Unknown'))} | "
                f"IP: {d.get('ip', 'Unknown')} | "
                f"Protocol: {d.get('protocol', 'Unknown')}")
        widgets.copy_to_clipboard(self._root, text, self.status)

    # ── Quick-launch helpers ──────────────────────────────────────────────────

    def _mgmt_ip(self):
        try:
            return management_address(self._device.get("ip", ""))
        except ValueError:
            return ""

    def _launch(self, protocol):
        ip = self._mgmt_ip()
        if not ip:
            return
        try:
            launch_terminal(protocol, ip)
        except Exception as exc:
            self._help.configure(text=str(exc), text_color=theme.ERROR)

    def _launch_ssh(self):
        self._launch("ssh")

    def _launch_telnet(self):
        self._launch("telnet")

    def _open_web(self, protocol):
        ip = self._mgmt_ip()
        if ip:
            host = f"[{ip}]" if ":" in ip else ip
            webbrowser.open(f"{protocol}://{host}")

    def _open_http(self):
        self._open_web("http")

    def _open_https(self):
        self._open_web("https")
