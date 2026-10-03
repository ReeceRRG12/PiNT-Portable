import tkinter as tk
from tkinter import ttk
import os
import sys

import customtkinter as ctk

from session import SessionManager
from app_settings import AppSettings
from gui import theme
from gui.interface_picker import InterfacePicker, get_iface_display
from gui.port_tab     import PortTab
from gui.mdns_tab     import MdnsTab
from gui.ip_tab       import IpTab
from gui.export_tab   import ExportTab
from gui.monitor_tab  import MonitorTab
from gui.settings_tab import SettingsTab
from gui.arp_tab      import ArpTab
from gui.portscan_tab import PortScanTab
from gui.snmp_tab     import SnmpTab


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
        img  = Image.open(path).convert("RGBA")
        # Crop transparent padding
        bbox = img.split()[3].getbbox()
        if bbox:
            img = img.crop(bbox)
        # Resize maintaining aspect ratio, then center on a square canvas
        img.thumbnail((size, size), Image.LANCZOS)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        x = (size - img.width)  // 2
        y = (size - img.height) // 2
        canvas.paste(img, (x, y))
        _, _, _, a = canvas.split()
        tinted = Image.new("RGBA", (size, size), theme.FG_DIM)
        tinted.putalpha(a)
        return ctk.CTkImage(light_image=tinted, dark_image=tinted, size=(size, size))
    except Exception:
        return None


class PiNTApp:
    PAGE_TITLES = {
        "port": "Identify switch port", "mdns": "Discover services",
        "arp": "Find network devices", "ip": "IP & DHCP details",
        "monitor": "Monitor connection", "portscan": "Scan TCP ports",
        "snmp": "Query SNMP", "export": "Session & export",
        "settings": "Settings", "about": "About PiNT",
    }

    def __init__(self, root):
        self.root = root
        self.root.title("PiNT — Network Tools")
        from gui.scale_manager import window_size
        width, height = window_size(root.winfo_screenwidth(), root.winfo_screenheight(),
                                    root._get_window_scaling())
        self.root.geometry(f"{width}x{height}")
        self.root.configure(fg_color=theme.BG)
        self.root.resizable(True, True)
        self.root.minsize(min(1000, width), min(640, height))

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
            "arp":      _load_icon("ARP.png"),
            "portscan": _load_icon("PortScanner.png"),
            "snmp":     _load_icon("SNMP.png"),
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
        sidebar = ctk.CTkFrame(self.root, fg_color=theme.SIDEBAR, width=theme.NAV_W, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        self._build_sidebar_header(sidebar)
        footer = ctk.CTkFrame(sidebar, fg_color="transparent", corner_radius=0)
        footer.pack(side="bottom", fill="x", padx=10, pady=(8, 12))
        ctk.CTkFrame(footer, fg_color=theme.DIVIDER, height=1, corner_radius=0).pack(fill="x", pady=(0, 10))
        self._nav_btn(footer, "settings", self._icons["settings"], "Settings")
        self._nav_btn(footer, "about", self._icons["about"], "About")
        ctk.CTkLabel(footer, text="PiNT Desktop  /  v1.5", text_color=theme.FG_HINT,
                     font=theme.font(12), anchor="w").pack(fill="x", padx=12, pady=(10, 0))

        # Navigation remains reachable on shorter laptop screens.
        nav = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", corner_radius=0,
                                     scrollbar_button_color=theme.SIDEBAR,
                                     scrollbar_button_hover_color=theme.DIVIDER)
        nav.pack(fill="both", expand=True, padx=(8, 0))
        groups = [
            ("DISCOVER", [("port", "Port ID"), ("mdns", "mDNS / Bonjour"), ("arp", "ARP Scanner")]),
            ("DIAGNOSE", [("ip", "IP & DHCP"), ("monitor", "Monitor"),
                          ("portscan", "Port Scanner"), ("snmp", "SNMP Query")]),
            ("SESSION", [("export", "Export results")]),
        ]
        for heading, entries in groups:
            ctk.CTkLabel(nav, text=heading, font=theme.font(12, "bold"),
                         text_color=theme.FG_HINT, anchor="w").pack(fill="x", padx=12, pady=(16, 5))
            for key, label in entries:
                self._nav_btn(nav, key, self._icons[key], label)

    def _build_sidebar_header(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=theme.SIDEBAR, corner_radius=0)
        frame.pack(fill="x", padx=24, pady=(24, 6))
        ctk.CTkLabel(frame, text="PiNT", text_color=theme.FG,
                     font=theme.font(34, "bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(frame, text="NETWORK TOOLS", text_color=theme.ACCENT,
                     font=theme.font(12, "bold"), anchor="w").pack(fill="x", pady=(0, 10))
        self.root.after(100, self._set_window_icon)

    def _set_window_icon(self):
        """Use platform-supported icons; macOS takes its Dock icon from the bundle."""
        try:
            if sys.platform == "win32":
                self.root.iconbitmap(os.path.join(_base_path(), "logo.ico"))
            elif sys.platform != "darwin":
                from PIL import Image, ImageTk
                self._window_icon = ImageTk.PhotoImage(Image.open(os.path.join(_base_path(), "logo.png")))
                self.root.iconphoto(True, self._window_icon)
        except (OSError, tk.TclError):
            pass

    def _build_adapter_bar(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=theme.PANEL, corner_radius=10,
                             border_width=1, border_color=theme.DIVIDER)
        frame.pack(side="right", padx=(24, 0))
        details = ctk.CTkFrame(frame, fg_color="transparent")
        details.pack(side="left", padx=(14, 8), pady=8)

        ctk.CTkLabel(details, text="NETWORK ADAPTER",
                     fg_color="transparent", text_color=theme.FG_LABEL,
                     font=theme.font(12, "bold"), height=20,
                     anchor="w").pack(anchor="w", fill="x")

        self._iface_label = ctk.CTkLabel(
            details,
            text=get_iface_display(self._state.selected_iface),
            fg_color="transparent", text_color=theme.FG,
            font=theme.font(12),
            wraplength=235, justify="left", anchor="w", height=22)
        self._iface_label.pack(anchor="w")

        ctk.CTkButton(frame, text="Change",
                      command=self._change_interface,
                      fg_color="transparent", text_color=theme.ACCENT,
                      hover_color=theme.PANEL_HOVER,
                      font=theme.font(12, "bold"),
                      height=32, width=68, corner_radius=6,
                      border_width=0).pack(side="right", padx=(0, 8))

    def _nav_btn(self, parent, key, icon_img, label):
        btn = ctk.CTkButton(
            parent,
            text=f"  {label}",
            image=icon_img,
            compound="left",
            anchor="w",
            fg_color=theme.NAV_BG,
            text_color=theme.FG_DIM,
            hover_color=theme.PANEL_HOVER,
            font=theme.font(13),
            height=40,
            corner_radius=8,
            border_width=0,
            cursor="hand2",
            command=lambda k=key: self._navigate(k),
        )
        btn.pack(fill="x", padx=2, pady=2)
        self._nav_buttons[key] = btn

    # ── Content area ──────────────────────────────────────────────────────────

    def _build_content(self):
        content = ctk.CTkFrame(self.root, fg_color=theme.BG, corner_radius=0)
        content.pack(side="left", fill="both", expand=True)

        header = ctk.CTkFrame(content, fg_color="transparent", corner_radius=0)
        header.pack(fill="x", padx=24, pady=(22, 18))
        self._build_adapter_bar(header)
        title = ctk.CTkFrame(header, fg_color="transparent")
        title.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(title, text="NETWORK WORKSPACE", text_color=theme.FG_HINT,
                     font=theme.font(12, "bold"), anchor="w", height=20).pack(fill="x")
        self._page_title = ctk.CTkLabel(title, text="", text_color=theme.FG,
                                       font=theme.font(26, "bold"), anchor="w")
        self._page_title.pack(fill="x", pady=(4, 0))
        ctk.CTkFrame(content, fg_color=theme.DIVIDER, height=1, corner_radius=0).pack(fill="x", padx=24)
        body = tk.Frame(content, bg=theme.BG)
        body.pack(fill="both", expand=True, padx=6, pady=(0, 12))

        def _panel(key):
            f = tk.Frame(body, bg=theme.BG)
            f.place(relwidth=1, relheight=1)
            self._panels[key] = f
            return f

        PortTab(_panel("port"), self.root, self._state)
        MdnsTab(_panel("mdns"), self.root, self._state)
        IpTab(_panel("ip"), self.root, self._state)
        MonitorTab(_panel("monitor"), self.root, self._state)
        ArpTab(_panel("arp"), self.root, self._state)
        PortScanTab(_panel("portscan"), self.root, self._state)
        SnmpTab(_panel("snmp"), self.root, self._state)
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
                     fg_color="transparent", text_color=theme.ACCENT,
                     font=ctk.CTkFont("Arial", 16, weight="bold")).pack()

        ctk.CTkLabel(frame, text="Version v1.5",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=ctk.CTkFont("Arial", 12)).pack(pady=(3, 0))

        ctk.CTkFrame(frame, fg_color=theme.DIVIDER, height=2,
                     corner_radius=0).pack(fill="x", padx=20, pady=14)

        ctk.CTkLabel(frame,
                     text="A lightweight tool for field technicians to identify\n"
                          "switch ports and discover mDNS devices on a network.",
                     fg_color="transparent", text_color=theme.FG,
                     font=ctk.CTkFont("Arial", 13), justify="center").pack()

        ctk.CTkFrame(frame, fg_color=theme.DIVIDER, height=2,
                     corner_radius=0).pack(fill="x", padx=20, pady=14)

        ctk.CTkLabel(frame, text="Built by Reece Rainer",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=ctk.CTkFont("Arial", 12)).pack()

        for text, url in [
            ("reece@pinetworktools.com",            "mailto:reece@pinetworktools.com"),
            ("github.com/ReeceRRG12/PiNT-Portable", "https://github.com/ReeceRRG12/PiNT-Portable"),
        ]:
            lbl = ctk.CTkLabel(frame, text=text,
                               fg_color="transparent", text_color=theme.ACCENT,
                               font=ctk.CTkFont("Arial", 12, underline=True),
                               cursor="hand2")
            lbl.pack(pady=3)
            lbl.bind("<Button-1>", lambda _, u=url: webbrowser.open(u))

        ctk.CTkLabel(frame,
                     text="Fully Open Source — Built with ❤️ for the networking community",
                     fg_color="transparent", text_color=theme.FG_HINT,
                     font=ctk.CTkFont("Arial", 11)).pack(pady=(14, 0))

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate(self, key):
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(text_color=theme.ACCENT, fg_color=theme.NAV_ACTIVE)
            else:
                btn.configure(text_color=theme.FG_DIM, fg_color=theme.NAV_BG)
        self._active_panel = key
        self._page_title.configure(text=self.PAGE_TITLES[key])
        self.root.title(f"PiNT — {self.PAGE_TITLES[key]}")
        self._panels[key].tkraise()

    def _change_interface(self):
        picker = InterfacePicker(self.root, force=True)
        if picker.result is not None:
            self._state.selected_iface = picker.result
        self._iface_label.configure(text=get_iface_display(self._state.selected_iface))


# ── Npcap check (Windows) ─────────────────────────────────────────────────────

def check_npcap(parent):
    import tkinter.messagebox as mb
    import webbrowser

    windows = os.environ.get("SystemRoot", r"C:\Windows")
    if os.path.isdir(os.path.join(windows, "System32", "Npcap")):
        return True
    if mb.askyesno("Packet capture setup", parent=parent,
                    message="Port ID, ARP and mDNS capture need Npcap. "
                            "You can still use TCP and SNMP tools without it.\n\n"
                            "Open the official Npcap download page? "
                            "Restart PiNT after installing it."):
        webbrowser.open("https://npcap.com/#download")
    return False


if __name__ == "__main__":
    from gui.scale_manager import detect_scale, apply_scale

    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    apply_scale(detect_scale(root))
    if sys.platform == "win32":
        check_npcap(root)
    app = PiNTApp(root)
    root.mainloop()
