import tkinter as tk
from tkinter import ttk
import os
import sys

from session import SessionManager
from gui.interface_picker import InterfacePicker, get_iface_display
from gui.port_tab     import PortTab
from gui.mdns_tab     import MdnsTab
from gui.ip_tab       import IpTab
from gui.export_tab   import ExportTab
from gui.monitor_tab  import MonitorTab
from gui.settings_tab import SettingsTab


_BG      = "#1a1a2e"
_SIDEBAR = "#16213e"
_ACCENT  = "#00d4ff"
_NAV_W   = 210


class AppSettings:
    def __init__(self):
        self.port_timeout    = 30    # seconds
        self.mdns_timeout    = 30    # seconds
        self.monitor_poll_ms = 2000  # milliseconds


class AppState:
    def __init__(self, selected_iface, session):
        self.selected_iface = selected_iface
        self.session        = session
        self.settings       = AppSettings()


def _base_path():
    return (sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.dirname(os.path.abspath(__file__)))


def _load_icon(filename, size=20):
    try:
        from PIL import Image, ImageTk
        path = os.path.join(_base_path(), "icons", filename)
        img = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


class PiNTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PiNT — Pi Network Tools")
        self.root.geometry("1380x960")
        self.root.configure(bg=_BG)
        self.root.resizable(False, False)

        ttk.Style().theme_use("clam")

        picker      = InterfacePicker(root)
        session     = SessionManager()
        self._state = AppState(selected_iface=picker.result, session=session)

        self._icons = {
            "port":     _load_icon("PortID.png"),
            "mdns":     _load_icon("mDNS.png"),
            "ip":       _load_icon("IP_Info.png"),
            "monitor":  _load_icon("Monitor.png"),
            "export":   _load_icon("Export.png"),
            "settings": _load_icon("settings.png"),
            "about":    _load_icon("About.png"),
        }

        self._nav_buttons  = {}
        self._active_panel = None
        self._panels       = {}

        self._build_sidebar()
        self._build_content()

        self._state.session.register_listener(
            lambda: root.after(0, self._export_tab.refresh))

        self._navigate("port")

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sidebar = tk.Frame(self.root, bg=_SIDEBAR, width=_NAV_W)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        self._build_sidebar_header(sidebar)
        tk.Frame(sidebar, bg="#0f3460", height=1).pack(fill="x", padx=12, pady=(4, 8))

        for key, icon_key, label in [
            ("port",    "port",    "Port ID"),
            ("mdns",    "mdns",    "mDNS"),
            ("ip",      "ip",      "IP Info"),
            ("monitor", "monitor", "Monitor"),
            ("export",  "export",  "Export"),
        ]:
            self._nav_btn(sidebar, key, self._icons[icon_key], label)

        # Push Settings / About to bottom
        tk.Frame(sidebar, bg=_SIDEBAR).pack(fill="both", expand=True)
        tk.Frame(sidebar, bg="#0f3460", height=1).pack(fill="x", padx=12, pady=6)
        self._nav_btn(sidebar, "settings", self._icons["settings"], "Settings")
        self._nav_btn(sidebar, "about",    self._icons["about"],    "About")

        tk.Frame(sidebar, bg="#0f3460", height=1).pack(fill="x", padx=12, pady=(6, 2))
        self._build_adapter_bar(sidebar)

    def _build_sidebar_header(self, parent):
        frame = tk.Frame(parent, bg=_SIDEBAR)
        frame.pack(fill="x")

        try:
            from PIL import Image, ImageTk

            # In-app logo: fill sidebar width, preserve aspect ratio
            app_logo = Image.open(os.path.join(_base_path(), "PiNT_InAppLogo.png"))
            w = _NAV_W
            h = int(app_logo.height * (w / app_logo.width))
            app_logo = app_logo.resize((w, h), Image.LANCZOS)
            self._app_logo_img = ImageTk.PhotoImage(app_logo)
            lbl = tk.Label(frame, image=self._app_logo_img, bg=_SIDEBAR)
            lbl.image = self._app_logo_img
            lbl.pack()

            # Taskbar / window icon: keep the original logo.png
            icon = Image.open(os.path.join(_base_path(), "logo.png")).resize(
                (32, 32), Image.LANCZOS)
            self._taskbar_icon = ImageTk.PhotoImage(icon)
            self.root.iconphoto(True, self._taskbar_icon)
        except Exception:
            tk.Label(frame, text="Pi Network\nTools",
                     bg=_SIDEBAR, fg=_ACCENT,
                     font=("Arial", 10, "bold"),
                     justify="center").pack(pady=14)

    def _build_adapter_bar(self, parent):
        frame = tk.Frame(parent, bg=_SIDEBAR)
        frame.pack(fill="x", padx=8, pady=(0, 10))

        tk.Label(frame, text="Adapter",
                 bg=_SIDEBAR, fg="#666666",
                 font=("Arial", 9, "bold")).pack(anchor="w")

        self._iface_label = tk.Label(
            frame,
            text=get_iface_display(self._state.selected_iface),
            bg=_SIDEBAR, fg="#888888",
            font=("Arial", 9),
            wraplength=190, justify="left")
        self._iface_label.pack(anchor="w")

        tk.Button(frame, text="Change adapter",
                  command=self._change_interface,
                  bg=_SIDEBAR, fg=_ACCENT,
                  font=("Arial", 9, "underline"),
                  relief="flat", highlightthickness=0, borderwidth=0,
                  cursor="hand2").pack(anchor="w", pady=(2, 0))

    def _nav_btn(self, parent, key, icon_img, label):
        btn = tk.Button(
            parent,
            text=f"  {label}",
            image=icon_img,
            compound="left" if icon_img else "none",
            anchor="w",
            bg=_SIDEBAR, fg="#888888",
            activebackground="#1f2d45", activeforeground=_ACCENT,
            font=("Arial", 10),
            relief="flat", highlightthickness=0, borderwidth=0,
            padx=8, pady=9,
            cursor="hand2",
            command=lambda k=key: self._navigate(k),
        )
        btn.pack(fill="x")

        def _enter(b=btn, k=key):
            if k != self._active_panel:
                b.config(fg="#cccccc")

        def _leave(b=btn, k=key):
            if k != self._active_panel:
                b.config(fg="#888888")

        btn.bind("<Enter>", lambda _: _enter())
        btn.bind("<Leave>", lambda _: _leave())
        self._nav_buttons[key] = btn

    # ── Content area ──────────────────────────────────────────────────────────

    def _build_content(self):
        content = tk.Frame(self.root, bg=_BG)
        content.pack(side="left", fill="both", expand=True)

        def _panel(key):
            f = tk.Frame(content, bg=_BG)
            f.place(relwidth=1, relheight=1)
            self._panels[key] = f
            return f

        PortTab(_panel("port"), self.root, self._state)
        MdnsTab(_panel("mdns"), self.root, self._state)
        IpTab(_panel("ip"), self.root, self._state)
        MonitorTab(_panel("monitor"), self.root, self._state)
        self._export_tab = ExportTab(_panel("export"), self.root, self._state)
        SettingsTab(_panel("settings"), self.root, self._state)
        self._build_about_panel(_panel("about"))

    def _build_about_panel(self, parent):
        import webbrowser

        frame = tk.Frame(parent, bg=_BG)
        frame.place(relx=0.5, rely=0.46, anchor="center")

        try:
            from PIL import Image, ImageTk
            about_logo = Image.open(os.path.join(_base_path(), "PiNT_InAppLogo.png"))
            w = 200
            h = int(about_logo.height * (w / about_logo.width))
            about_logo = about_logo.resize((w, h), Image.LANCZOS)
            about_img = ImageTk.PhotoImage(about_logo)
            lbl = tk.Label(frame, image=about_img, bg=_BG)
            lbl.image = about_img
            lbl.pack(pady=(0, 8))
        except Exception:
            pass

        tk.Label(frame, text="PiNT — Port Identifier Network Tool",
                 bg=_BG, fg=_ACCENT,
                 font=("Arial", 13, "bold")).pack()

        tk.Label(frame, text="Version v1.0",
                 bg=_BG, fg="#888888",
                 font=("Arial", 10)).pack(pady=(2, 0))

        tk.Frame(frame, bg="#0f3460", height=1).pack(fill="x", padx=20, pady=12)

        tk.Label(frame,
                 text="A lightweight tool for field technicians to identify\n"
                      "switch ports and discover mDNS devices on a network.",
                 bg=_BG, fg="#eeeeee",
                 font=("Arial", 10), justify="center").pack()

        tk.Frame(frame, bg="#0f3460", height=1).pack(fill="x", padx=20, pady=12)

        tk.Label(frame, text="Built by Reece Rainer",
                 bg=_BG, fg="#888888",
                 font=("Arial", 10)).pack()

        for text, url in [
            ("reece@pinetworktools.com",           "mailto:reece@pinetworktools.com"),
            ("github.com/ReeceRRG12/PiNT-Portable", "https://github.com/ReeceRRG12/PiNT-Portable"),
        ]:
            lbl = tk.Label(frame, text=text,
                           bg=_BG, fg=_ACCENT,
                           font=("Arial", 10, "underline"),
                           cursor="hand2")
            lbl.pack(pady=2)
            lbl.bind("<Button-1>", lambda _, u=url: webbrowser.open(u))

        tk.Label(frame,
                 text="Fully Open Source — Built with ❤️ for the networking community",
                 bg=_BG, fg="#555555",
                 font=("Arial", 9)).pack(pady=(12, 0))

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate(self, key):
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.config(fg=_ACCENT, bg="#1f2d45")
            else:
                btn.config(fg="#888888", bg=_SIDEBAR)
        self._active_panel = key
        self._panels[key].tkraise()

    def _change_interface(self):
        picker = InterfacePicker(self.root, force=True)
        if picker.result is not None:
            self._state.selected_iface = picker.result
        self._iface_label.config(text=get_iface_display(self._state.selected_iface))


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
