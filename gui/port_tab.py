import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import webbrowser
import os
import shutil

import customtkinter as ctk
from gui import theme


def _find_putty():
    """Locate PuTTY on Windows. Returns executable path or None."""
    if shutil.which("putty"):
        return "putty"
    candidates = [
        r"C:\Program Files\PuTTY\putty.exe",
        r"C:\Program Files (x86)\PuTTY\putty.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\PuTTY\putty.exe"),
        os.path.join(os.environ.get("APPDATA",      ""), r"PuTTY\putty.exe"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


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
        _desc = tk.Label(parent,
                         text="Identifies which switch and port you are connected to by listening for "
                              "LLDP and CDP packets broadcast by managed switches.\n\n"
                              "Useful when tracing cables or auditing patch panels.",
                         bg=theme.BG, fg=theme.FG_DIM,
                         font=theme.tk_font(12),
                         wraplength=600, justify="center")
        _desc.pack(fill="x", padx=20, pady=(12, 8))
        parent.bind("<Configure>", lambda e: _desc.configure(wraplength=max(100, e.width - 40)), add="+")

        self.status = ctk.CTkLabel(parent,
                                   text="Press Scan to detect your switch port",
                                   fg_color="transparent", text_color=theme.FG_DIM,
                                   font=theme.font(10))
        self.status.pack(pady=(4, 2))

        style = ttk.Style()
        style.configure("Scan.Horizontal.TProgressbar",
                        troughcolor=theme.PANEL, background=theme.ACCENT,
                        bordercolor=theme.PANEL, lightcolor=theme.ACCENT,
                        darkcolor=theme.ACCENT, thickness=6)
        self._progress = ttk.Progressbar(parent, mode="indeterminate",
                                          style="Scan.Horizontal.TProgressbar")
        self._progress.pack(fill="x", padx=20, pady=(0, 10))

        # ── Card grid ─────────────────────────────────────────────────────────
        grid = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        grid.pack(fill="x", padx=20, pady=(0, 6))
        grid.columnconfigure((0, 1, 2), weight=1, uniform="col")

        self._switch_val   = self._card(grid, "Switch",     0, 0)
        self._port_val     = self._card(grid, "Port",        1, 0)
        self._protocol_val = self._card(grid, "Protocol",   2, 0)
        self._model_val    = self._card(grid, "Model",       0, 1)
        self._ip_val       = self._card(grid, "IP Address",  1, 1)
        self._vlan_val     = self._card(grid, "VLAN",        2, 1)

        # ── Quick-launch bar (hidden until a management IP is found) ──────────
        self._ql_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)

        ctk.CTkLabel(self._ql_frame, text="Quick Launch →",
                     fg_color="transparent", text_color=theme.FG_HINT,
                     font=theme.font(11, "italic")).pack(side="left", padx=(12, 6))

        for label, cmd, colour in [
            ("SSH (PuTTY)",    self._launch_ssh,    theme.ACCENT),
            ("Telnet (PuTTY)", self._launch_telnet, theme.WARNING),
            ("HTTP",           self._open_http,     theme.FG),
            ("HTTPS",          self._open_https,    theme.FG),
        ]:
            ctk.CTkButton(self._ql_frame, text=label, command=cmd,
                          fg_color=theme.PANEL, text_color=colour,
                          hover_color="#1f2d45",
                          font=theme.font(11, "bold"),
                          corner_radius=6, border_width=0,
                          height=32).pack(side="left", padx=3)

        # ── Main action buttons ───────────────────────────────────────────────
        self._btn_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        self._btn_frame.pack(pady=8)

        self.scan_btn = ctk.CTkButton(self._btn_frame, text="Scan",
                                      command=self.start_scan,
                                      fg_color=theme.ACCENT, text_color=theme.BG,
                                      hover_color="#00b8d9",
                                      font=theme.font(11, "bold"),
                                      corner_radius=6, border_width=0,
                                      width=100)
        self.scan_btn.pack(side="left", padx=5)

        self.copy_btn = ctk.CTkButton(self._btn_frame, text="Copy to Clipboard",
                                      command=self.copy_to_clipboard,
                                      fg_color=theme.PANEL, text_color=theme.FG,
                                      hover_color="#1f2d45",
                                      font=theme.font(10),
                                      corner_radius=6, border_width=0)
        self.copy_btn.pack(side="left", padx=5)

    def _card(self, parent, label, col, row):
        """Create a labeled info card. Returns the value CTkLabel."""
        card = ctk.CTkFrame(parent, fg_color=theme.PANEL, corner_radius=8)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(card, text=label,
                     fg_color="transparent", text_color=theme.FG_HINT,
                     font=theme.font(13, "bold"),
                     anchor="w").pack(anchor="w", padx=14, pady=(12, 2))
        val = ctk.CTkLabel(card, text="—",
                           fg_color="transparent", text_color=theme.FG_DIM,
                           font=theme.font(14, "bold"),
                           anchor="w", wraplength=180, justify="left")
        val.pack(anchor="w", padx=14, pady=(0, 12))
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
        self._reset_cards()
        self._ql_frame.pack_forget()
        self._progress.start(10)
        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        from scanner import scan
        scan(self._handle_result,
             timeout=self._state.settings.port_timeout,
             iface=self._state.selected_iface)

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
            self.status.configure(
                text=f"✅ Switch detected via {protocol}!", text_color=proto_colour)
            self._state.session.add_port_scan(device)

            mgmt_ip = device.get('ip', '')
            if mgmt_ip and mgmt_ip != 'Unknown':
                self._ql_frame.pack(before=self._btn_frame, pady=(0, 4))
        else:
            self._reset_cards(theme.ERROR)
            self.status.configure(
                text="No switch detected. Are you plugged into a managed switch?",
                text_color=theme.ERROR)
            self._ql_frame.pack_forget()

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
        self._root.clipboard_clear()
        self._root.clipboard_append(text)
        self.status.configure(text="📋 Copied to clipboard!", text_color=theme.ACCENT)

    # ── Quick-launch helpers ──────────────────────────────────────────────────

    def _mgmt_ip(self):
        ip = self._device.get('ip', '')
        return ip if ip and ip != 'Unknown' else ''

    def _launch_ssh(self):
        ip = self._mgmt_ip()
        if not ip:
            return
        putty = _find_putty()
        if putty:
            subprocess.Popen([putty, "-ssh", ip])
        else:
            self.status.configure(
                text="PuTTY not found — download from putty.org",
                text_color=theme.ERROR)

    def _launch_telnet(self):
        ip = self._mgmt_ip()
        if not ip:
            return
        putty = _find_putty()
        if putty:
            subprocess.Popen([putty, "-telnet", ip])
        else:
            self.status.configure(
                text="PuTTY not found — download from putty.org",
                text_color=theme.ERROR)

    def _open_http(self):
        ip = self._mgmt_ip()
        if ip:
            webbrowser.open(f"http://{ip}")

    def _open_https(self):
        ip = self._mgmt_ip()
        if ip:
            webbrowser.open(f"https://{ip}")
