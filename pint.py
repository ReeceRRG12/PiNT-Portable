import tkinter as tk
from tkinter import ttk
import os
import sys

import customtkinter as ctk

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
        from PIL import Image
        path = os.path.join(_base_path(), "icons", filename)
        img = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
        return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    except Exception:
        return None


class PiNTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PiNT — Pi Network Tools")
        from gui.scale_manager import current_scale
        _s = current_scale()
        self.root.geometry(f"{round(1380 * _s)}x{round(960 * _s)}")
        self.root.configure(fg_color=_BG)
        self.root.resizable(True, True)
        self.root.minsize(900, 640)

        _style = ttk.Style()
        _style.theme_use("clam")
        from gui.theme import apply_scrollbar_style
        apply_scrollbar_style(_style)

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
        sidebar = ctk.CTkFrame(self.root, fg_color=_SIDEBAR, width=_NAV_W, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Frame(sidebar, bg=_SIDEBAR, height=10).pack(fill="x")
        self._build_sidebar_header(sidebar)
        ctk.CTkFrame(sidebar, fg_color="#0f3460", height=2, corner_radius=0).pack(fill="x", padx=12, pady=(4, 8))

        for key, icon_key, label in [
            ("port",    "port",    "Port ID"),
            ("mdns",    "mdns",    "mDNS"),
            ("ip",      "ip",      "IP Info"),
            ("monitor", "monitor", "Monitor"),
            ("export",  "export",  "Export"),
        ]:
            self._nav_btn(sidebar, key, self._icons[icon_key], label)

        # Push Settings / About to bottom
        ctk.CTkFrame(sidebar, fg_color=_SIDEBAR, corner_radius=0).pack(fill="both", expand=True)
        ctk.CTkFrame(sidebar, fg_color="#0f3460", height=2, corner_radius=0).pack(fill="x", padx=12, pady=6)
        self._nav_btn(sidebar, "settings", self._icons["settings"], "Settings")
        self._nav_btn(sidebar, "about",    self._icons["about"],    "About")

        ctk.CTkFrame(sidebar, fg_color="#0f3460", height=2, corner_radius=0).pack(fill="x", padx=12, pady=(6, 2))
        self._build_adapter_bar(sidebar)

    def _build_sidebar_header(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=_SIDEBAR, corner_radius=0)
        frame.pack(fill="x")

        try:
            from PIL import Image, ImageTk

            # In-app logo: leave side margins by using a narrower width
            app_logo = Image.open(os.path.join(_base_path(), "PiNT_InAppLogo.png"))
            w = _NAV_W - 24
            h = int(app_logo.height * (w / app_logo.width))
            self._app_logo_img = ctk.CTkImage(
                light_image=app_logo, dark_image=app_logo, size=(w, h))
            lbl = ctk.CTkLabel(frame, image=self._app_logo_img,
                               text="", fg_color="transparent")
            lbl.pack(padx=12, pady=(0, 8))

            # Taskbar / window icon — iconphoto() requires a PhotoImage, not CTkImage
            icon = Image.open(os.path.join(_base_path(), "logo.png")).resize(
                (32, 32), Image.LANCZOS)
            self._taskbar_icon = ImageTk.PhotoImage(icon)
            self.root.iconphoto(True, self._taskbar_icon)
        except Exception:
            ctk.CTkLabel(frame, text="Pi Network\nTools",
                         fg_color="transparent", text_color=_ACCENT,
                         font=ctk.CTkFont("Arial", 10, weight="bold"),
                         justify="center").pack(pady=14)

    def _build_adapter_bar(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=_SIDEBAR, corner_radius=0)
        frame.pack(fill="x", padx=8, pady=(0, 10))

        ctk.CTkLabel(frame, text="Adapter",
                     fg_color="transparent", text_color="#666666",
                     font=ctk.CTkFont("Arial", 11, weight="bold"),
                     anchor="w").pack(anchor="w", fill="x")

        self._iface_label = ctk.CTkLabel(
            frame,
            text=get_iface_display(self._state.selected_iface),
            fg_color="transparent", text_color="#888888",
            font=ctk.CTkFont("Arial", 10),
            wraplength=190, justify="left", anchor="w")
        self._iface_label.pack(anchor="w")

        ctk.CTkButton(frame, text="Change adapter",
                      command=self._change_interface,
                      fg_color="transparent", text_color=_ACCENT,
                      hover_color="#1f2d45",
                      font=ctk.CTkFont("Arial", 11, underline=True),
                      anchor="w", height=24, corner_radius=0,
                      border_width=0).pack(anchor="w", pady=(2, 0))

    def _nav_btn(self, parent, key, icon_img, label):
        btn = ctk.CTkButton(
            parent,
            text=f"  {label}",
            image=icon_img,
            compound="left",
            anchor="w",
            fg_color="#111d2e",
            text_color="#888888",
            hover_color="#1f2d45",
            font=ctk.CTkFont("Arial", 11, weight="bold"),
            height=42,
            corner_radius=6,
            border_width=0,
            cursor="hand2",
            command=lambda k=key: self._navigate(k),
        )
        btn.pack(fill="x", padx=6, pady=2)
        self._nav_buttons[key] = btn

    # ── Content area ──────────────────────────────────────────────────────────

    def _build_content(self):
        content = ctk.CTkFrame(self.root, fg_color=_BG, corner_radius=0)
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

        frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        frame.place(relx=0.5, rely=0.46, anchor="center")

        try:
            from PIL import Image
            about_logo = Image.open(os.path.join(_base_path(), "PiNT_InAppLogo.png"))
            w = 260
            h = int(about_logo.height * (w / about_logo.width))
            about_img = ctk.CTkImage(light_image=about_logo, dark_image=about_logo,
                                     size=(w, h))
            ctk.CTkLabel(frame, image=about_img, text="",
                         fg_color="transparent").pack(pady=(0, 10))
        except Exception:
            pass

        ctk.CTkLabel(frame, text="PiNT — Port Identifier Network Tool",
                     fg_color="transparent", text_color=_ACCENT,
                     font=ctk.CTkFont("Arial", 16, weight="bold")).pack()

        ctk.CTkLabel(frame, text="Version v1.1",
                     fg_color="transparent", text_color="#888888",
                     font=ctk.CTkFont("Arial", 12)).pack(pady=(3, 0))

        ctk.CTkFrame(frame, fg_color="#0f3460", height=2,
                     corner_radius=0).pack(fill="x", padx=20, pady=14)

        ctk.CTkLabel(frame,
                     text="A lightweight tool for field technicians to identify\n"
                          "switch ports and discover mDNS devices on a network.",
                     fg_color="transparent", text_color="#eeeeee",
                     font=ctk.CTkFont("Arial", 13), justify="center").pack()

        ctk.CTkFrame(frame, fg_color="#0f3460", height=2,
                     corner_radius=0).pack(fill="x", padx=20, pady=14)

        ctk.CTkLabel(frame, text="Built by Reece Rainer",
                     fg_color="transparent", text_color="#888888",
                     font=ctk.CTkFont("Arial", 12)).pack()

        for text, url in [
            ("reece@pinetworktools.com",            "mailto:reece@pinetworktools.com"),
            ("github.com/ReeceRRG12/PiNT-Portable", "https://github.com/ReeceRRG12/PiNT-Portable"),
        ]:
            lbl = ctk.CTkLabel(frame, text=text,
                               fg_color="transparent", text_color=_ACCENT,
                               font=ctk.CTkFont("Arial", 12, underline=True),
                               cursor="hand2")
            lbl.pack(pady=3)
            lbl.bind("<Button-1>", lambda _, u=url: webbrowser.open(u))

        ctk.CTkLabel(frame,
                     text="Fully Open Source — Built with ❤️ for the networking community",
                     fg_color="transparent", text_color="#555555",
                     font=ctk.CTkFont("Arial", 11)).pack(pady=(14, 0))

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate(self, key):
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(text_color=_ACCENT, fg_color="#1a3050")
            else:
                btn.configure(text_color="#888888", fg_color="#111d2e")
        self._active_panel = key
        self._panels[key].tkraise()

    def _change_interface(self):
        picker = InterfacePicker(self.root, force=True)
        if picker.result is not None:
            self._state.selected_iface = picker.result
        self._iface_label.configure(text=get_iface_display(self._state.selected_iface))


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
    from gui.scale_manager import detect_scale, apply_scale

    if sys.platform == "win32":
        check_and_install_npcap()

    # Scale must be applied before ctk.CTk() is created
    ctk.set_appearance_mode("dark")
    apply_scale(detect_scale())
    root = ctk.CTk()
    app = PiNTApp(root)
    root.mainloop()
