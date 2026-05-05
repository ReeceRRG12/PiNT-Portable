import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import webbrowser
import os
import shutil


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
    Shows quick-launch buttons (SSH, Telnet, HTTP, HTTPS) once a management IP
    is detected.
    """

    def __init__(self, parent, root, app_state):
        self._root   = root
        self._state  = app_state
        self._device = {}
        self._build(parent)

    def _build(self, parent):
        tk.Label(parent,
                 text="Identifies which switch and port you are connected to by listening for "
                      "LLDP and CDP packets broadcast by managed switches. Useful when tracing "
                      "cables or auditing patch panels.",
                 bg="#1a1a2e", fg="#888888",
                 font=("Arial", 10),
                 wraplength=1050, justify="left").pack(
                     fill="x", padx=10, pady=(8, 6), anchor="w")

        self.status = tk.Label(parent,
                               text="Press Scan to detect your switch port",
                               bg="#1a1a2e", fg="#888888")
        self.status.pack(pady=(4, 2))

        style = ttk.Style()
        style.configure("Scan.Horizontal.TProgressbar",
                        troughcolor="#16213e", background="#00d4ff",
                        bordercolor="#16213e", lightcolor="#00d4ff", darkcolor="#00d4ff",
                        thickness=6)
        self._progress = ttk.Progressbar(parent, mode="indeterminate",
                                          style="Scan.Horizontal.TProgressbar")
        self._progress.pack(fill="x", padx=20, pady=(0, 4))

        self.result_frame = tk.Frame(parent, bg="#16213e", padx=20, pady=20)
        self.result_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.result = tk.Label(self.result_frame, text="No data yet",
                               bg="#16213e", fg="#eee",
                               font=("Arial", 11), justify="left")
        self.result.pack()

        # ── Quick-launch bar (hidden until a management IP is found) ──────────
        self._ql_frame = tk.Frame(parent, bg="#1a1a2e")

        tk.Label(self._ql_frame, text="Quick Launch →",
                 bg="#1a1a2e", fg="#555555",
                 font=("Arial", 8, "italic")).pack(side="left", padx=(12, 6))

        for label, cmd, colour in [
            ("SSH (PuTTY)",    self._launch_ssh,    "#00d4ff"),
            ("Telnet (PuTTY)", self._launch_telnet, "#ffaa00"),
            ("HTTP",           self._open_http,     "#eee"),
            ("HTTPS",          self._open_https,    "#eee"),
        ]:
            tk.Button(self._ql_frame, text=label, command=cmd,
                      bg="#16213e", fg=colour,
                      font=("Arial", 9, "bold"),
                      padx=10, pady=2,
                      relief="flat", highlightthickness=0, borderwidth=0,
                      cursor="hand2").pack(side="left", padx=3)

        # ── Main action buttons ───────────────────────────────────────────────
        self._btn_frame = tk.Frame(parent, bg="#1a1a2e")
        self._btn_frame.pack(pady=5)

        self.scan_btn = tk.Button(self._btn_frame, text="Scan",
                                  command=self.start_scan,
                                  bg="#00d4ff", fg="#1a1a2e",
                                  font=("Arial", 11, "bold"),
                                  padx=20, relief="flat",
                                  highlightthickness=0, borderwidth=0)
        self.scan_btn.pack(side="left", padx=5)

        self.copy_btn = tk.Button(self._btn_frame, text="Copy to Clipboard",
                                  command=self.copy_to_clipboard,
                                  bg="#16213e", fg="#eee",
                                  padx=20, relief="flat",
                                  highlightthickness=0, borderwidth=0)
        self.copy_btn.pack(side="left", padx=5)

    # ── Scan logic ────────────────────────────────────────────────────────────

    def start_scan(self):
        timeout = self._state.settings.port_timeout
        self.scan_btn.config(state="disabled")
        self.status.config(
            text=f"Scanning for LLDP and CDP... (up to {timeout}s)", fg="#ffaa00")
        self.result.config(text="Listening for switch...")
        self._device = {}
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
            proto_colour = "#00d4ff" if protocol == "LLDP" else "#ff9500"
            text = (f"Switch:    {device.get('name',        'Unknown')}\n"
                    f"Port:      {device.get('port',        'Unknown')}\n"
                    f"Model:     {device.get('description', device.get('model', 'Unknown'))}\n"
                    f"IP:        {device.get('ip',          'Unknown')}\n"
                    f"VLAN:      {device.get('vlan',        'Unknown')}\n"
                    f"Protocol:  {protocol}")
            self._device = device
            self.result.config(text=text, fg="#00ff88")
            self.status.config(text=f"✅ Switch detected via {protocol}!", fg=proto_colour)
            self._state.session.add_port_scan(device)

            mgmt_ip = device.get('ip', '')
            if mgmt_ip and mgmt_ip != 'Unknown':
                self._ql_frame.pack(before=self._btn_frame, pady=(0, 4))
        else:
            self.result.config(
                text="No switch detected.\nAre you plugged into a managed switch?",
                fg="#ff4757")
            self.status.config(text="Scan timed out", fg="#ff4757")
            self._ql_frame.pack_forget()

        self.scan_btn.config(state="normal")

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
        self.status.config(text="📋 Copied to clipboard!", fg="#00d4ff")

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
            self.status.config(
                text="PuTTY not found — download from putty.org", fg="#ff4757")

    def _launch_telnet(self):
        ip = self._mgmt_ip()
        if not ip:
            return
        putty = _find_putty()
        if putty:
            subprocess.Popen([putty, "-telnet", ip])
        else:
            self.status.config(
                text="PuTTY not found — download from putty.org", fg="#ff4757")

    def _open_http(self):
        ip = self._mgmt_ip()
        if ip:
            webbrowser.open(f"http://{ip}")

    def _open_https(self):
        ip = self._mgmt_ip()
        if ip:
            webbrowser.open(f"https://{ip}")
