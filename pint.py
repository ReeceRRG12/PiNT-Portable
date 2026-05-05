import tkinter as tk
from tkinter import ttk
import os
import sys

from session import SessionManager
from gui.interface_picker import InterfacePicker, get_iface_display
from gui.port_tab    import PortTab
from gui.mdns_tab    import MdnsTab
from gui.ip_tab      import IpTab
from gui.export_tab  import ExportTab
from gui.monitor_tab import MonitorTab


class AppState:
    """Lightweight container for state shared across all tabs."""
    def __init__(self, selected_iface, session):
        self.selected_iface = selected_iface  # scapy interface name or None
        self.session        = session


class PiNTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PiNT - Network Tool")
        self.root.geometry("500x580")
        self.root.configure(bg="#1a1a2e")

        self._build_logo()
        self._build_title()

        # ── Interface picker (shows as modal if multiple adapters detected) ───
        picker = InterfacePicker(root)
        session = SessionManager()
        self._state = AppState(selected_iface=picker.result, session=session)

        self._build_adapter_bar()
        self._build_notebook()

        # Wire session changes → export tab refresh
        self._state.session.register_listener(
            lambda: root.after(0, self._export_tab.refresh))

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_logo(self):
        try:
            from PIL import Image, ImageTk
            base = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(
                os.path.abspath(__file__))
            img = Image.open(os.path.join(base, "logo.png")).resize((80, 80))
            logo_img = ImageTk.PhotoImage(img)
            lbl = tk.Label(self.root, image=logo_img, bg="#1a1a2e")
            lbl.image = logo_img
            lbl.pack(pady=5)
            self.root.iconphoto(True, logo_img)
        except Exception as e:
            print(f"Logo error: {e}")

    def _build_title(self):
        tk.Label(self.root, text="PiNT - Network Tool",
                 font=("Arial", 16, "bold"),
                 bg="#1a1a2e", fg="#00d4ff").pack(pady=5)

        tk.Button(self.root, text="About",
                  command=self._show_about,
                  bg="#1a1a2e", fg="#888888",
                  font=("Arial", 8),
                  relief="flat", highlightthickness=0, borderwidth=0).pack()

    def _build_adapter_bar(self):
        """Small bar showing the selected adapter with a Change button."""
        bar = tk.Frame(self.root, bg="#1a1a2e")
        bar.pack(fill="x", padx=14, pady=(2, 0))

        tk.Label(bar, text="Adapter:",
                 bg="#1a1a2e", fg="#555555",
                 font=("Arial", 8)).pack(side="left")

        self._iface_label = tk.Label(
            bar,
            text=get_iface_display(self._state.selected_iface),
            bg="#1a1a2e", fg="#888888",
            font=("Arial", 8))
        self._iface_label.pack(side="left", padx=(4, 8))

        tk.Button(bar, text="Change",
                  command=self._change_interface,
                  bg="#1a1a2e", fg="#00d4ff",
                  font=("Arial", 8, "underline"),
                  relief="flat", highlightthickness=0, borderwidth=0,
                  cursor="hand2").pack(side="left")

    def _change_interface(self):
        picker = InterfacePicker(self.root, force=True)
        if picker.result is not None:
            self._state.selected_iface = picker.result
        self._iface_label.config(text=get_iface_display(self._state.selected_iface))

    # ── Notebook ──────────────────────────────────────────────────────────────

    def _build_notebook(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background="#1a1a2e", borderwidth=0)
        style.configure("TNotebook.Tab",
                        background="#16213e", foreground="#888888",
                        padding=[12, 4], font=("Arial", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", "#1a1a2e")],
                  foreground=[("selected", "#00d4ff")])

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=10, pady=5)

        def _frame():
            f = tk.Frame(nb, bg="#1a1a2e")
            return f

        port_frame = _frame(); nb.add(port_frame, text="  Port ID  ")
        PortTab(port_frame, self.root, self._state)

        mdns_frame = _frame(); nb.add(mdns_frame, text="  mDNS  ")
        MdnsTab(mdns_frame, self.root, self._state)

        ip_frame = _frame(); nb.add(ip_frame, text="  IP Info  ")
        IpTab(ip_frame, self.root, self._state)

        monitor_frame = _frame(); nb.add(monitor_frame, text="  Monitor  ")
        MonitorTab(monitor_frame, self.root, self._state)

        export_frame = _frame(); nb.add(export_frame, text="  Export  ")
        self._export_tab = ExportTab(export_frame, self.root, self._state)

    # ── About dialog ──────────────────────────────────────────────────────────

    def _show_about(self):
        import webbrowser
        win = tk.Toplevel(self.root)
        win.title("About PiNT")
        win.configure(bg="#1a1a2e")
        win.resizable(False, False)
        win.grab_set()

        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()  // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 160
        win.geometry(f"400x320+{x}+{y}")

        tk.Label(win, text="🖧 PiNT - Port Identifier Network Tool",
                 bg="#1a1a2e", fg="#00d4ff",
                 font=("Arial", 13, "bold")).pack(pady=(20, 4))

        tk.Label(win, text="Version v0.7",
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

        def _link(text, url):
            lbl = tk.Label(win, text=text,
                           bg="#1a1a2e", fg="#00d4ff",
                           font=("Arial", 10, "underline"),
                           cursor="hand2")
            lbl.pack(pady=2)
            lbl.bind("<Button-1>", lambda _: webbrowser.open(url))

        _link("📧 reece@pinetworktools.com", "mailto:reece@pinetworktools.com")
        _link("🔗 github.com/ReeceRRG12/PiNT-Portable",
              "https://github.com/ReeceRRG12/PiNT-Portable")

        tk.Label(win, text="Fully Open Source — Built with ❤️ for the networking community",
                 bg="#1a1a2e", fg="#555",
                 font=("Arial", 9), justify="center").pack(pady=(10, 0))

        tk.Button(win, text="Close",
                  command=win.destroy,
                  bg="#16213e", fg="#eee",
                  font=("Arial", 10), padx=20,
                  relief="flat", highlightthickness=0, borderwidth=0).pack(pady=16)


# ── Npcap check (Windows) ─────────────────────────────────────────────────────

def check_and_install_npcap():
    import subprocess, urllib.request
    import tkinter.messagebox as mb

    if os.path.exists(r"C:\Windows\System32\Npcap"):
        return True

    if not mb.askyesno("Npcap Required",
                        "PiNT requires Npcap to capture network packets.\n\n"
                        "Would you like to install it now? (Requires admin rights)"):
        return False

    url       = "https://npcap.com/dist/npcap-1.80.exe"
    installer = os.path.join(os.environ["TEMP"], "npcap_installer.exe")
    mb.showinfo("Installing", "Downloading Npcap, please wait...")
    urllib.request.urlretrieve(url, installer)
    subprocess.run([installer], check=True)
    mb.showinfo("Restart Required",
                "Npcap has been installed!\n\nPlease restart your PC and run PiNT again.")
    sys.exit()


if __name__ == "__main__":
    if sys.platform == "win32":
        check_and_install_npcap()
    root = tk.Tk()
    app  = PiNTApp(root)
    root.mainloop()
