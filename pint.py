import tkinter as tk
import threading
import os
import sys
from scanner import scan

class PiNTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PiNT - Network Tool")
        self.root.geometry("500x340")
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

        title = tk.Label(root, text="PiNT - Port Identifier",
                        font=("Arial", 16, "bold"),
                        bg="#1a1a2e", fg="#00d4ff")
        title.pack(pady=5)

        self.status = tk.Label(root, text="Press Scan to detect your switch port",
                              bg="#1a1a2e", fg="#888888")
        self.status.pack()

        self.result_frame = tk.Frame(root, bg="#16213e", padx=20, pady=20)
        self.result_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.result = tk.Label(self.result_frame, text="No data yet",
                              bg="#16213e", fg="#eee",
                              font=("Arial", 11), justify="left")
        self.result.pack()

        btn_frame = tk.Frame(root, bg="#1a1a2e")
        btn_frame.pack(pady=5)

        self.scan_btn = tk.Button(btn_frame, text="Scan",
                                 command=self.start_scan,
                                 bg="#00d4ff", fg="#1a1a2e",
                                 font=("Arial", 11, "bold"),
                                 padx=20)
        self.scan_btn.pack(side="left", padx=5)

        self.copy_btn = tk.Button(btn_frame, text="Copy to Clipboard",
                                 command=self.copy_to_clipboard,
                                 bg="#16213e", fg="#eee",
                                 padx=20)
        self.copy_btn.pack(side="left", padx=5)

        self.device_data = {}

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
            self.status.config(
                text=f"✅ Switch detected via {protocol}!",
                fg=protocol_color
            )
        else:
            self.result.config(
                text="No switch detected.\nAre you plugged into a managed switch?",
                fg="#ff4757"
            )
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

def check_and_install_npcap():
    import os
    import sys
    import subprocess
    import urllib.request

    npcap_path = r"C:\Windows\System32\Npcap"
    if os.path.exists(npcap_path):
        return True

    import tkinter.messagebox as mb
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
        mb.showinfo(
            "Restart Required",
            "Npcap has been installed!\n\n"
            "Please restart your PC and run PiNT again."
        )
        sys.exit()

    return False

if __name__ == "__main__":
    if sys.platform == "win32":
        check_and_install_npcap()
    root = tk.Tk()
    app = PiNTApp(root)
    root.mainloop()