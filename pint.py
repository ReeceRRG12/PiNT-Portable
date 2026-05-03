import tkinter as tk
from tkinter import ttk
import threading
import os
import sys
import csv
from datetime import datetime
from scanner import scan
from mdns_scanner import scan_mdns, resolve_mdns_ips

class PiNTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PiNT - Network Tool")
        self.root.geometry("500x480")
        self.root.configure(bg="#1a1a2e")

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

        self.device_data = {}

    # ── Port ID Tab ──────────────────────────────────────────
    def build_port_tab(self):
        self.status = tk.Label(self.port_tab,
                               text="Press Scan to detect your switch port",
                               bg="#1a1a2e", fg="#888888")
        self.status.pack(pady=(10, 0))

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
        top_frame = tk.Frame(self.mdns_tab, bg="#1a1a2e")
        top_frame.pack(fill="x", padx=10, pady=(10, 5))

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
        from tkinter import filedialog
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