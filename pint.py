import tkinter as tk
from tkinter import ttk, filedialog
import threading
import os
import sys
import csv
from datetime import datetime
from scanner import scan
from mdns_scanner import scan_mdns, resolve_mdns_ips
from ip_info import get_ip_config, get_dhcp_options, FLAG_COLOURS
from session import SessionManager
from exporter import export_xlsx

class PiNTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PiNT - Network Tool")
        self.root.geometry("500x560")
        self.root.configure(bg="#1a1a2e")

        # ── Session manager ──────────────────────────────────
        self.session = SessionManager()
        self.session.register_listener(self._on_session_update)

        try:
            from PIL import Image, ImageTk
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(base_path, "logo.png")
            img = Image.open(logo_path)
            img = img.resize((80, 80))
            logo_img = ImageTk.PhotoImage(img)
            logo_label = tk.Label(root, image=logo_img, bg="#1a1a2e")
            logo_label.image = logo_img
            logo_label.pack(pady=5)
            root.iconphoto(True, logo_img)
        except Exception as e:
            print(f"Logo error: {e}")

        title = tk.Label(root, text="PiNT - Network Tool",
                        font=("Arial", 16, "bold"),
                        bg="#1a1a2e", fg="#00d4ff")
        title.pack(pady=5)

        about_btn = tk.Button(root, text="About",
                              command=self.show_about,
                              bg="#1a1a2e", fg="#888888",
                              font=("Arial", 8),
                              relief="flat",
                              highlightthickness=0,
                              borderwidth=0)
        about_btn.pack()

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background="#1a1a2e", borderwidth=0)
        style.configure("TNotebook.Tab",
                        background="#16213e", foreground="#888888",
                        padding=[12, 4], font=("Arial", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", "#1a1a2e")],
                  foreground=[("selected", "#00d4ff")])

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self.port_tab = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(self.port_tab, text="  Port ID  ")
        self.build_port_tab()

        self.mdns_tab = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(self.mdns_tab, text="  mDNS  ")
        self.build_mdns_tab()

        self.ip_tab = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(self.ip_tab, text="  IP Info  ")
        self.build_ip_tab()

        self.export_tab = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(self.export_tab, text="  Export  ")
        self.build_export_tab()

        self.device_data = {}

    def _tab_description(self, parent, text):
        """Renders a muted description line at the top of a tab."""
        tk.Label(parent, text=text,
                 bg="#1a1a2e", fg="#555555",
                 font=("Arial", 9, "italic"),
                 wraplength=460, justify="left").pack(
                     fill="x", padx=10, pady=(0, 4), anchor="w")

    def show_about(self):
        import webbrowser
        win = tk.Toplevel(self.root)
        win.title("About PiNT")
        win.configure(bg="#1a1a2e")
        win.resizable(False, False)
        win.grab_set()

        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 160
        win.geometry(f"400x320+{x}+{y}")

        tk.Label(win, text="🖧 PiNT - Port Identifier Network Tool",
                 bg="#1a1a2e", fg="#00d4ff",
                 font=("Arial", 13, "bold")).pack(pady=(20, 4))

        tk.Label(win, text="Version v0.5.3",
                 bg="#1a1a2e", fg="#888888",
                 font=("Arial", 10)).pack()

        tk.Frame(win, bg="#0f3460", height=1).pack(fill="x", padx=30, pady=14)

        tk.Label(win,
                 text="A lightweight tool for field technicians to identify\n"
                      "switch ports and discover mDNS devices on a network.",
                 bg="#1a1a2e", fg="#eee",
                 font=("Arial", 10), justify="center").pack(padx=20)

        tk.Frame(win, bg="#0f3460", height=1).pack(fill="x", padx=30, pady=14)

        tk.Label(win, text="Built by Reece Rainer",
                 bg="#1a1a2e", fg="#888888",
                 font=("Arial", 10)).pack()

        def _make_link(parent, text, url):
            lbl = tk.Label(parent, text=text,
                           bg="#1a1a2e", fg="#00d4ff",
                           font=("Arial", 10, "underline"),
                           cursor="hand2")
            lbl.pack(pady=2)
            lbl.bind("<Button-1>", lambda e: webbrowser.open(url))

        _make_link(win, "📧 reece@pinetworktools.com", "mailto:reece@pinetworktools.com")
        _make_link(win, "🔗 github.com/ReeceRRG12/PiNT-Portable", "https://github.com/ReeceRRG12/PiNT-Portable")

        tk.Label(win, text="Fully Open Source — Built with ❤️ for the networking community",
                 bg="#1a1a2e", fg="#555",
                 font=("Arial", 9), justify="center").pack(pady=(10, 0))

        tk.Button(win, text="Close",
                  command=win.destroy,
                  bg="#16213e", fg="#eee",
                  font=("Arial", 10),
                  padx=20, relief="flat",
                  highlightthickness=0, borderwidth=0).pack(pady=16)

    # ── Session listener ──────────────────────────────────────
    def _on_session_update(self):
        """Called automatically whenever the session changes."""
        self.root.after(0, self._refresh_export_tab)

    # ── Port ID Tab ──────────────────────────────────────────
    def build_port_tab(self):
        self._tab_description(
            self.port_tab,
            "Identifies which switch and port you are connected to by listening for "
            "LLDP and CDP packets broadcast by managed switches. Useful when tracing "
            "cables or auditing patch panels."
        )

        self.status = tk.Label(self.port_tab,
                               text="Press Scan to detect your switch port",
                               bg="#1a1a2e", fg="#888888")
        self.status.pack(pady=(4, 0))

        self.result_frame = tk.Frame(self.port_tab, bg="#16213e", padx=20, pady=20)
        self.result_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.result = tk.Label(self.result_frame, text="No data yet",
                               bg="#16213e", fg="#eee",
                               font=("Arial", 11), justify="left")
        self.result.pack()

        btn_frame = tk.Frame(self.port_tab, bg="#1a1a2e")
        btn_frame.pack(pady=5)

        self.scan_btn = tk.Button(btn_frame, text="Scan",
                                  command=self.start_scan,
                                  bg="#00d4ff", fg="#1a1a2e",
                                  font=("Arial", 11, "bold"),
                                  padx=20,
                                  relief="flat",
                                  highlightthickness=0,
                                  borderwidth=0)
        self.scan_btn.pack(side="left", padx=5)

        self.copy_btn = tk.Button(btn_frame, text="Copy to Clipboard",
                                  command=self.copy_to_clipboard,
                                  bg="#16213e", fg="#eee",
                                  padx=20,
                                  relief="flat",
                                  highlightthickness=0,
                                  borderwidth=0)
        self.copy_btn.pack(side="left", padx=5)

    def start_scan(self):
        self.scan_btn.config(state="disabled")
        self.status.config(text="Scanning for LLDP and CDP... (up to 30s)", fg="#ffaa00")
        self.result.config(text="Listening for switch...")
        self.device_data = {}
        thread = threading.Thread(target=self.run_scan, daemon=True)
        thread.start()

    def run_scan(self):
        scan(self.handle_result)

    def handle_result(self, device):
        self.root.after(0, self.update_ui, device)

    def update_ui(self, device):
        if device:
            protocol = device.get('protocol', 'Unknown')
            protocol_color = "#00d4ff" if protocol == "LLDP" else "#ff9500"
            text = (f"Switch:    {device.get('name', 'Unknown')}\n"
                    f"Port:      {device.get('port', 'Unknown')}\n"
                    f"Model:     {device.get('description', device.get('model', 'Unknown'))}\n"
                    f"IP:        {device.get('ip', 'Unknown')}\n"
                    f"VLAN:      {device.get('vlan', 'Unknown')}\n"
                    f"Protocol:  {protocol}")
            self.device_data = device
            self.result.config(text=text, fg="#00ff88")
            self.status.config(text=f"✅ Switch detected via {protocol}!", fg=protocol_color)
            self.session.add_port_scan(device)
        else:
            self.result.config(
                text="No switch detected.\nAre you plugged into a managed switch?",
                fg="#ff4757")
            self.status.config(text="Scan timed out", fg="#ff4757")
        self.scan_btn.config(state="normal")

    def copy_to_clipboard(self):
        if self.device_data:
            d = self.device_data
            text = (f"Switch: {d.get('name', 'Unknown')} | "
                    f"Port: {d.get('port', 'Unknown')} | "
                    f"Model: {d.get('description', d.get('model', 'Unknown'))} | "
                    f"IP: {d.get('ip', 'Unknown')} | "
                    f"Protocol: {d.get('protocol', 'Unknown')}")
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status.config(text="📋 Copied to clipboard!", fg="#00d4ff")

    # ── mDNS Tab ─────────────────────────────────────────────
    def build_mdns_tab(self):
        self._tab_description(
            self.mdns_tab,
            "Discovers devices on the local network that advertise services via mDNS "
            "(Bonjour). Commonly used to find printers, cameras, smart devices, and "
            "Apple services without needing access to the switch or DHCP server."
        )

        top_frame = tk.Frame(self.mdns_tab, bg="#1a1a2e")
        top_frame.pack(fill="x", padx=10, pady=(0, 5))

        self.mdns_status = tk.Label(top_frame,
                                    text="Press Scan to discover mDNS devices",
                                    bg="#1a1a2e", fg="#888888")
        self.mdns_status.pack(side="left")

        self.mdns_scan_btn = tk.Button(top_frame, text="Scan",
                                       command=self.start_mdns_scan,
                                       bg="#00d4ff", fg="#1a1a2e",
                                       font=("Arial", 10, "bold"),
                                       padx=15,
                                       relief="flat",
                                       highlightthickness=0,
                                       borderwidth=0)
        self.mdns_scan_btn.pack(side="right")

        self.mdns_view_mode = "simple"
        self.toggle_btn = tk.Button(top_frame, text="Full View",
                                    command=self.toggle_mdns_view,
                                    bg="#16213e", fg="#eee",
                                    font=("Arial", 10),
                                    padx=10,
                                    relief="flat",
                                    highlightthickness=0,
                                    borderwidth=0)
        self.toggle_btn.pack(side="right", padx=(0, 5))

        self.resolve_btn = tk.Button(top_frame, text="Resolve IPs",
                                     command=self.start_resolve,
                                     bg="#16213e", fg="#eee",
                                     font=("Arial", 10),
                                     padx=10,
                                     relief="flat",
                                     highlightthickness=0,
                                     borderwidth=0)
        self.resolve_btn.pack(side="right", padx=(0, 5))
        self.resolve_btn.config(state="disabled")

        search_frame = tk.Frame(self.mdns_tab, bg="#1a1a2e")
        search_frame.pack(fill="x", padx=10, pady=(0, 5))

        tk.Label(search_frame, text="Filter:", bg="#1a1a2e", fg="#888888").pack(side="left")
        self.mdns_filter_var = tk.StringVar()
        self.mdns_filter_var.trace_add("write", self.apply_mdns_filter)
        self.mdns_filter_entry = tk.Entry(search_frame,
                                          textvariable=self.mdns_filter_var,
                                          bg="#16213e", fg="#eee",
                                          insertbackground="#eee",
                                          relief="flat", font=("Arial", 10))
        self.mdns_filter_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))

        tree_frame = tk.Frame(self.mdns_tab, bg="#1a1a2e")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        style = ttk.Style()
        style.configure("Treeview",
                         background="#16213e",
                         foreground="#eee",
                         fieldbackground="#16213e",
                         rowheight=28,
                         font=("Arial", 10))
        style.configure("Treeview.Heading",
                         background="#0f3460",
                         foreground="#00d4ff",
                         font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#0f3460")])

        self.mdns_tree = ttk.Treeview(tree_frame,
                                       columns=("friendly", "type", "ip"),
                                       show="headings",
                                       selectmode="browse")
        self.mdns_tree.heading("friendly", text="Device Name")
        self.mdns_tree.heading("type", text="Service Type")
        self.mdns_tree.heading("ip", text="IP Address")
        self.mdns_tree.column("friendly", width=200)
        self.mdns_tree.column("type", width=160)
        self.mdns_tree.column("ip", width=110)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical",
                                   command=self.mdns_tree.yview)
        self.mdns_tree.configure(yscrollcommand=scrollbar.set)
        self.mdns_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        bottom_frame = tk.Frame(self.mdns_tab, bg="#1a1a2e")
        bottom_frame.pack(fill="x", padx=10, pady=(0, 5))

        self.mdns_detail = tk.Label(bottom_frame, text="",
                                     bg="#1a1a2e", fg="#888888",
                                     font=("Arial", 9), anchor="w")
        self.mdns_detail.pack(side="left", fill="x", expand=True)

        self.mdns_copy_btn = tk.Button(bottom_frame, text="Copy",
                                        command=self.mdns_copy_to_clipboard,
                                        bg="#16213e", fg="#eee",
                                        font=("Arial", 9),
                                        padx=8,
                                        relief="flat",
                                        highlightthickness=0,
                                        borderwidth=0,
                                        state="disabled")
        self.mdns_copy_btn.pack(side="right", padx=(5, 0))

        self.mdns_export_btn = tk.Button(bottom_frame, text="Export CSV",
                                          command=self.export_mdns_csv,
                                          bg="#16213e", fg="#eee",
                                          font=("Arial", 9),
                                          padx=8,
                                          relief="flat",
                                          highlightthickness=0,
                                          borderwidth=0,
                                          state="disabled")
        self.mdns_export_btn.pack(side="right", padx=(5, 0))

        self.mdns_tree.bind("<<TreeviewSelect>>", self.show_mdns_detail)
        self.mdns_results = []

    def start_mdns_scan(self):
        self.mdns_scan_btn.config(state="disabled")
        self.resolve_btn.config(state="disabled")
        self.mdns_export_btn.config(state="disabled")
        self.mdns_copy_btn.config(state="disabled")
        self.mdns_status.config(text="Scanning for mDNS devices... (30s)", fg="#ffaa00")
        for row in self.mdns_tree.get_children():
            self.mdns_tree.delete(row)
        self.mdns_results = []
        self.mdns_detail.config(text="")
        thread = threading.Thread(target=self.run_mdns_scan, daemon=True)
        thread.start()

    def run_mdns_scan(self):
        scan_mdns(self.handle_mdns_result)

    def handle_mdns_result(self, devices):
        self.root.after(0, self.update_mdns_ui, devices)

    def update_mdns_ui(self, devices):
        self.mdns_results = devices
        self.apply_mdns_filter()
        count = len(devices)
        self.mdns_status.config(
            text=f"✅ Found {count} mDNS device{'s' if count != 1 else ''}",
            fg="#00ff88" if count > 0 else "#ff4757"
        )
        self.mdns_scan_btn.config(state="normal")
        self.resolve_btn.config(state="normal")
        self.mdns_export_btn.config(state="normal")
        self.mdns_copy_btn.config(state="normal")
        if devices:
            self.session.add_mdns_scan(devices)

    def apply_mdns_filter(self, *args):
        query = self.mdns_filter_var.get().lower()
        for row in self.mdns_tree.get_children():
            self.mdns_tree.delete(row)
        for d in self.mdns_results:
            if self.mdns_view_mode == "simple" and not d.get("simple", False):
                continue
            friendly = d.get("friendly", "")
            stype = d.get("type", "")
            ip = d.get("ip", "")
            if query in friendly.lower() or query in stype.lower() or query in ip.lower():
                self.mdns_tree.insert("", "end",
                                       values=(friendly, stype, ip),
                                       tags=(d.get("raw", ""),))

    def show_mdns_detail(self, event):
        selected = self.mdns_tree.selection()
        if selected:
            tags = self.mdns_tree.item(selected[0], "tags")
            if tags:
                self.mdns_detail.config(text=f"Raw: {tags[0]}")

    def toggle_mdns_view(self):
        if self.mdns_view_mode == "simple":
            self.mdns_view_mode = "full"
            self.toggle_btn.config(text="Simple View")
        else:
            self.mdns_view_mode = "simple"
            self.toggle_btn.config(text="Full View")
        self.apply_mdns_filter()

    def start_resolve(self):
        self.resolve_btn.config(state="disabled")
        self.mdns_scan_btn.config(state="disabled")
        self.mdns_status.config(text="Sending IP resolve request... (45s)", fg="#ffaa00")
        thread = threading.Thread(
            target=lambda: resolve_mdns_ips(self.mdns_results, self.handle_resolve_result),
            daemon=True
        )
        thread.start()

    def handle_resolve_result(self, updated_devices):
        self.root.after(0, self.finish_resolve, updated_devices)

    def finish_resolve(self, updated_devices):
        self.mdns_results = updated_devices
        self.apply_mdns_filter()
        self.resolve_btn.config(state="normal")
        self.mdns_scan_btn.config(state="normal")
        self.mdns_status.config(text="✅ IP resolve complete", fg="#00ff88")

    def mdns_copy_to_clipboard(self):
        if not self.mdns_results:
            return
        lines = ["Device Name\tService Type\tIP Address"]
        for d in self.mdns_results:
            if self.mdns_view_mode == "simple" and not d.get("simple", False):
                continue
            lines.append(f"{d.get('friendly','')}\t{d.get('type','')}\t{d.get('ip','')}")
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(lines))
        self.mdns_status.config(text="📋 Copied to clipboard!", fg="#00d4ff")

    def export_mdns_csv(self):
        if not self.mdns_results:
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"pint_mdns_{timestamp}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=default_name,
            title="Export mDNS results"
        )
        if not filepath:
            return
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Device Name", "Service Type", "IP Address", "Raw"])
            for d in self.mdns_results:
                writer.writerow([
                    d.get("friendly", ""),
                    d.get("type", ""),
                    d.get("ip", ""),
                    d.get("raw", "")
                ])
        self.mdns_status.config(text=f"✅ Exported to {os.path.basename(filepath)}", fg="#00ff88")

    # ── IP Info Tab ───────────────────────────────────────────
    def build_ip_tab(self):
        self._tab_description(
            self.ip_tab,
            "Displays the IP configuration of your network adapter, including DHCP "
            "server details and scope options. Useful for understanding the network "
            "segment you are connected to without needing switch or router access."
        )

        top_frame = tk.Frame(self.ip_tab, bg="#1a1a2e")
        top_frame.pack(fill="x", padx=10, pady=(0, 5))

        self.ip_status = tk.Label(top_frame,
                                  text="Press Scan to load IP & DHCP information",
                                  bg="#1a1a2e", fg="#888888")
        self.ip_status.pack(side="left")

        self.ip_scan_btn = tk.Button(top_frame, text="Scan",
                                     command=self.start_ip_scan,
                                     bg="#00d4ff", fg="#1a1a2e",
                                     font=("Arial", 10, "bold"),
                                     padx=15,
                                     relief="flat",
                                     highlightthickness=0,
                                     borderwidth=0)
        self.ip_scan_btn.pack(side="right")

        canvas_frame = tk.Frame(self.ip_tab, bg="#1a1a2e")
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self.ip_canvas = tk.Canvas(canvas_frame, bg="#1a1a2e",
                                   highlightthickness=0)
        ip_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical",
                                     command=self.ip_canvas.yview)
        self.ip_canvas.configure(yscrollcommand=ip_scrollbar.set)
        ip_scrollbar.pack(side="right", fill="y")
        self.ip_canvas.pack(side="left", fill="both", expand=True)

        self.ip_inner = tk.Frame(self.ip_canvas, bg="#1a1a2e")
        self.ip_canvas_window = self.ip_canvas.create_window(
            (0, 0), window=self.ip_inner, anchor="nw"
        )
        self.ip_inner.bind("<Configure>", self._on_ip_inner_configure)
        self.ip_canvas.bind("<Configure>", self._on_ip_canvas_configure)

        self.ip_canvas.bind("<Enter>",
            lambda e: self.ip_canvas.bind_all("<MouseWheel>", self._on_ip_mousewheel))
        self.ip_canvas.bind("<Leave>",
            lambda e: self.ip_canvas.unbind_all("<MouseWheel>"))

    def _on_ip_inner_configure(self, event):
        self.ip_canvas.configure(scrollregion=self.ip_canvas.bbox("all"))

    def _on_ip_canvas_configure(self, event):
        self.ip_canvas.itemconfig(self.ip_canvas_window, width=event.width)

    def _on_ip_mousewheel(self, event):
        self.ip_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def start_ip_scan(self):
        self.ip_scan_btn.config(state="disabled")
        self.ip_status.config(text="Reading IP config and querying DHCP... (up to 15s)",
                               fg="#ffaa00")
        for widget in self.ip_inner.winfo_children():
            widget.destroy()
        thread = threading.Thread(target=self.run_ip_scan, daemon=True)
        thread.start()

    def run_ip_scan(self):
        ip_data = get_ip_config()
        dhcp_opts = get_dhcp_options(timeout=10) if ip_data.get("dhcp_enabled") else []
        self.root.after(0, self.update_ip_ui, ip_data, dhcp_opts)

    def update_ip_ui(self, ip_data, dhcp_opts):
        parent = self.ip_inner

        self._ip_section_header(parent, "IP Configuration")

        rows = [
            ("Adapter",       ip_data.get("adapter", "Unknown")),
            ("Hostname",      ip_data.get("hostname", "Unknown")),
            ("MAC Address",   ip_data.get("mac", "Unknown")),
            ("IP Address",    ip_data.get("ip", "Unknown")),
            ("Subnet Mask",   ip_data.get("subnet", "Unknown")),
            ("Gateway",       ip_data.get("gateway", "Unknown")),
            ("Domain",        ip_data.get("domain", "Unknown")),
        ]
        for i, dns in enumerate(ip_data.get("dns", [])):
            label = "DNS Server" if i == 0 else f"DNS Server {i+1}"
            rows.append((label, dns))

        for label, value in rows:
            self._ip_row(parent, label, value)

        self._ip_section_header(parent, "DHCP")

        dhcp_enabled = ip_data.get("dhcp_enabled", False)
        self._ip_row(parent, "DHCP Enabled",
                     "Yes" if dhcp_enabled else "No",
                     value_colour="#00ff88" if dhcp_enabled else "#ff4757")

        if dhcp_enabled:
            self._ip_row(parent, "DHCP Server",    ip_data.get("dhcp_server", "Unknown"))
            self._ip_row(parent, "Lease Obtained", ip_data.get("lease_obtained", "Unknown"))
            self._ip_row(parent, "Lease Expires",  ip_data.get("lease_expires",  "Unknown"))

            self._ip_section_header(parent, "DHCP Scope Options")

            if dhcp_opts:
                legend_frame = tk.Frame(parent, bg="#1a1a2e")
                legend_frame.pack(fill="x", padx=10, pady=(0, 6))
                for flag, colour in [("Standard", "#00ff88"),
                                     ("Notable",  "#ffaa00"),
                                     ("Unknown",  "#ff4757")]:
                    tk.Label(legend_frame, text="●", fg=colour,
                             bg="#1a1a2e", font=("Arial", 9)).pack(side="left")
                    tk.Label(legend_frame, text=f" {flag}   ",
                             fg="#888888", bg="#1a1a2e",
                             font=("Arial", 9)).pack(side="left")

                for opt_num, label, value, flag in dhcp_opts:
                    colour = FLAG_COLOURS.get(flag, "#eee")
                    self._ip_option_row(parent, opt_num, label, value, colour)
            else:
                tk.Label(parent,
                         text="No scope options returned by DHCP server.",
                         bg="#1a1a2e", fg="#888888",
                         font=("Arial", 10)).pack(padx=10, pady=4, anchor="w")
        else:
            tk.Label(parent,
                     text="DHCP is not enabled on this adapter.",
                     bg="#1a1a2e", fg="#888888",
                     font=("Arial", 10)).pack(padx=10, pady=4, anchor="w")

        self.session.add_ip_snapshot(ip_data, dhcp_opts)

        self.ip_status.config(text="✅ IP & DHCP information loaded", fg="#00ff88")
        self.ip_scan_btn.config(state="normal")

    def _ip_section_header(self, parent, text):
        frame = tk.Frame(parent, bg="#0f3460")
        frame.pack(fill="x", padx=0, pady=(10, 2))
        tk.Label(frame, text=text,
                 bg="#0f3460", fg="#00d4ff",
                 font=("Arial", 10, "bold"),
                 padx=10, pady=4).pack(anchor="w")

    def _ip_row(self, parent, label, value, value_colour="#eee"):
        frame = tk.Frame(parent, bg="#16213e")
        frame.pack(fill="x", padx=0, pady=1)
        tk.Label(frame, text=label,
                 bg="#16213e", fg="#888888",
                 font=("Arial", 10), width=18, anchor="w",
                 padx=10).pack(side="left")
        tk.Label(frame, text=value,
                 bg="#16213e", fg=value_colour,
                 font=("Arial", 10), anchor="w").pack(side="left", padx=(0, 10))

    def _ip_option_row(self, parent, opt_num, label, value, colour):
        frame = tk.Frame(parent, bg="#16213e")
        frame.pack(fill="x", padx=0, pady=1)
        tk.Label(frame, text="●", fg=colour,
                 bg="#16213e", font=("Arial", 9),
                 padx=6).pack(side="left")
        tk.Label(frame, text=f"{opt_num:>3}",
                 bg="#16213e", fg="#555",
                 font=("Arial", 9, "bold"),
                 width=3).pack(side="left")
        tk.Label(frame, text=label,
                 bg="#16213e", fg="#888888",
                 font=("Arial", 10), width=22, anchor="w").pack(side="left")
        tk.Label(frame, text=value,
                 bg="#16213e", fg=colour,
                 font=("Arial", 10), anchor="w").pack(side="left", padx=(0, 10))

    # ── Export Tab ────────────────────────────────────────────
    def build_export_tab(self):
        self._tab_description(
            self.export_tab,
            "Accumulates results from all tabs during your session and exports them "
            "to a formatted Excel file. Run scans across multiple ports to build up "
            "a full picture before exporting — ideal for switch audits."
        )

        header_frame = tk.Frame(self.export_tab, bg="#1a1a2e")
        header_frame.pack(fill="x", padx=10, pady=(0, 5))

        self.export_status = tk.Label(header_frame,
                                      text="No data in session yet",
                                      bg="#1a1a2e", fg="#888888")
        self.export_status.pack(side="left")

        clear_btn = tk.Button(header_frame, text="Clear Session",
                              command=self.clear_session,
                              bg="#16213e", fg="#ff4757",
                              font=("Arial", 9),
                              padx=10,
                              relief="flat",
                              highlightthickness=0,
                              borderwidth=0)
        clear_btn.pack(side="right")

        tree_frame = tk.Frame(self.export_tab, bg="#1a1a2e")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self.export_tree = ttk.Treeview(tree_frame,
                                         columns=("time", "type", "summary"),
                                         show="headings",
                                         selectmode="browse")
        self.export_tree.heading("time",    text="Timestamp")
        self.export_tree.heading("type",    text="Type")
        self.export_tree.heading("summary", text="Summary")
        self.export_tree.column("time",    width=140)
        self.export_tree.column("type",    width=90)
        self.export_tree.column("summary", width=230)

        exp_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical",
                                       command=self.export_tree.yview)
        self.export_tree.configure(yscrollcommand=exp_scrollbar.set)
        self.export_tree.pack(side="left", fill="both", expand=True)
        exp_scrollbar.pack(side="right", fill="y")

        btn_frame = tk.Frame(self.export_tab, bg="#1a1a2e")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.export_xlsx_btn = tk.Button(btn_frame, text="Export XLS",
                                          command=self.do_export_xlsx,
                                          bg="#00d4ff", fg="#1a1a2e",
                                          font=("Arial", 11, "bold"),
                                          padx=20,
                                          relief="flat",
                                          highlightthickness=0,
                                          borderwidth=0,
                                          state="disabled")
        self.export_xlsx_btn.pack(side="left", padx=(0, 5))

        self.export_result_label = tk.Label(btn_frame, text="",
                                             bg="#1a1a2e", fg="#00ff88",
                                             font=("Arial", 9))
        self.export_result_label.pack(side="left", padx=10)

    def _refresh_export_tab(self):
        for row in self.export_tree.get_children():
            self.export_tree.delete(row)

        for entry in self.session.port_scans:
            summary = f"{entry['switch']} — {entry['port']} ({entry['protocol']})"
            self.export_tree.insert("", "end",
                                     values=(entry["timestamp"], "Port Scan", summary))

        for entry in self.session.ip_snapshots:
            summary = (f"{entry['ip']} via {entry['dhcp_server']}"
                       if entry["dhcp_enabled"] else f"{entry['ip']} (static)")
            self.export_tree.insert("", "end",
                                     values=(entry["timestamp"], "IP Snapshot", summary))

        for entry in self.session.mdns_scans:
            count = len(entry["devices"])
            summary = f"{count} device{'s' if count != 1 else ''} discovered"
            self.export_tree.insert("", "end",
                                     values=(entry["timestamp"], "mDNS Scan", summary))

        total = self.session.total_entries()
        if total == 0:
            self.export_status.config(text="No data in session yet", fg="#888888")
            self.export_xlsx_btn.config(state="disabled")
        else:
            parts = []
            if self.session.port_scans:
                n = len(self.session.port_scans)
                parts.append(f"{n} port scan{'s' if n != 1 else ''}")
            if self.session.ip_snapshots:
                n = len(self.session.ip_snapshots)
                parts.append(f"{n} IP snapshot{'s' if n != 1 else ''}")
            if self.session.mdns_scans:
                n = len(self.session.mdns_scans)
                parts.append(f"{n} mDNS scan{'s' if n != 1 else ''}")
            self.export_status.config(
                text="Session: " + ", ".join(parts),
                fg="#00d4ff"
            )
            self.export_xlsx_btn.config(state="normal")

    def do_export_xlsx(self):
        if not self.session.has_data():
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
            export_xlsx(self.session, filepath)
            self.export_result_label.config(
                text=f"✅ Saved {os.path.basename(filepath)}", fg="#00ff88"
            )
        except Exception as e:
            self.export_result_label.config(text=f"❌ Export failed: {e}", fg="#ff4757")

    def clear_session(self):
        import tkinter.messagebox as mb
        if not self.session.has_data():
            return
        if mb.askyesno("Clear Session",
                        "This will remove all accumulated scan results.\n\nAre you sure?"):
            self.session.clear()
            self.export_result_label.config(text="")


# ── Npcap installer (Windows only) ───────────────────────────
def check_and_install_npcap():
    import subprocess
    import urllib.request
    import tkinter.messagebox as mb

    npcap_path = r"C:\Windows\System32\Npcap"
    if os.path.exists(npcap_path):
        return True

    result = mb.askyesno(
        "Npcap Required",
        "PiNT requires Npcap to capture network packets.\n\n"
        "Would you like to install it now? (Requires admin rights)"
    )
    if result:
        url = "https://npcap.com/dist/npcap-1.80.exe"
        installer = os.path.join(os.environ["TEMP"], "npcap_installer.exe")
        mb.showinfo("Installing", "Downloading Npcap, please wait...")
        urllib.request.urlretrieve(url, installer)
        subprocess.run([installer], check=True)
        mb.showinfo("Restart Required",
                    "Npcap has been installed!\n\nPlease restart your PC and run PiNT again.")
        sys.exit()
    return False


if __name__ == "__main__":
    if sys.platform == "win32":
        check_and_install_npcap()
    root = tk.Tk()
    app = PiNTApp(root)
    root.mainloop()