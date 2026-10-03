import tkinter as tk
from tkinter import ttk
import sys

import customtkinter as ctk
from gui import theme


def _enumerate_interfaces():
    """
    Return a list of dicts describing usable network interfaces,
    using scapy's conf.ifaces. Layer-2 discovery also works without an IPv4 lease.
    """
    interfaces = []
    try:
        from scapy.all import conf
        import psutil
        stats = psutil.net_if_stats()
        details = {}
        if sys.platform == 'darwin':
            from network.platform_info import macos_interface_details
            details = macos_interface_details()
        for name, iface in conf.ifaces.items():
            try:
                ip  = getattr(iface, 'ip',          '') or ''
                mac = getattr(iface, 'mac',         '') or ''
                desc = getattr(iface, 'description', '') or name
                native = details.get(name, {})
                if native.get('description'):
                    desc = f"{native['description']} ({name})"

                if ip.startswith('127.') or desc.lower().startswith('loopback') or name == 'lo0':
                    continue

                dl = desc.lower()
                is_wireless = native.get('type') == 'Wireless' or any(w in dl for w in
                                  ['wi-fi', 'wifi', 'wireless', '802.11'])
                is_virtual  = native.get('type') == 'Virtual/VPN' or any(w in dl for w in
                                  ['virtual', 'hyper-v', 'vmware', 'vpn',
                                   'tunnel', 'loopback', 'bluetooth',
                                   'npcap loopback', 'miniport'])
                if sys.platform == 'darwin' and name.startswith(('bridge', 'utun', 'awdl', 'llw', 'anpi')):
                    is_virtual = True
                is_apipa    = ip.startswith('169.254.')
                has_ip = bool(ip and ip != '0.0.0.0')
                if not has_ip and (is_virtual or not mac or mac == '00:00:00:00:00:00'):
                    continue
                link = stats.get(name)
                if not has_ip and link is not None and not link.isup:
                    continue
                is_wired = (not is_wireless and not is_virtual and
                            (native.get('type') == 'Wired' or sys.platform == 'win32' or
                             any(w in dl for w in ('ethernet', 'wired', 'lan adapter'))))

                itype = ('Wireless' if is_wireless
                         else 'Virtual/VPN' if is_virtual
                         else 'Wired' if is_wired else 'Network')
                recommended = is_wired and has_ip and not is_apipa

                interfaces.append({
                    'name':        name,
                    'description': desc,
                    'ip':          ip if has_ip else 'No IPv4 address',
                    'mac':         mac,
                    'type':        itype,
                    'recommended': recommended,
                })
            except Exception:
                continue
    except Exception:
        pass
    interfaces.sort(key=lambda item: (not item['recommended'],
                                     item['ip'] == 'No IPv4 address',
                                     item['description'].casefold()))
    return interfaces


def get_iface_display(iface_name):
    """Return a short human-readable label for the given scapy interface name."""
    if not iface_name:
        return "Auto-detect"
    try:
        from scapy.all import conf
        iface = conf.ifaces.get(iface_name)
        if iface:
            desc = getattr(iface, 'description', '') or iface_name
            if sys.platform == 'darwin':
                from network.platform_info import macos_interface_details
                desc = macos_interface_details().get(iface_name, {}).get('description', desc)
            ip   = getattr(iface, 'ip', '') or ''
            label = desc[:32] + ('…' if len(desc) > 32 else '')
            return f"{label}  ({ip})" if ip else label
    except Exception:
        pass
    return iface_name


class InterfacePicker:
    """
    Modal dialog for selecting a network interface.

    After instantiation check self.result for the chosen scapy interface
    name (str) or None if the user dismissed or only one option existed.

    Pass force=True to always show the dialog (used when the user clicks
    the Change button rather than on first launch).
    """

    def __init__(self, parent, force=False):
        self.result = None
        self._interfaces = _enumerate_interfaces()

        if not self._interfaces:
            return

        if not force:
            if len(self._interfaces) == 1:
                self.result = self._interfaces[0]['name']
                return

        self._build(parent)

    def _build(self, parent):
        win = ctk.CTkToplevel(parent)
        win.title("Select Network Interface")
        win.configure(fg_color=theme.BG)
        win.resizable(False, False)
        win.grab_set()

        w, h = 640, 440
        parent.update_idletasks()
        px = parent.winfo_x() + max(0, (parent.winfo_width()  // 2) - w // 2)
        py = parent.winfo_y() + max(0, (parent.winfo_height() // 2) - h // 2)
        win.geometry(f"{w}x{h}+{px}+{py}")

        ctk.CTkLabel(win, text="Select Network Interface",
                     fg_color="transparent", text_color=theme.ACCENT,
                     font=theme.font(14, "bold")).pack(pady=(16, 4))

        ctk.CTkLabel(win,
                     text="Multiple network adapters detected. "
                          "Select the wired Ethernet interface connected to your managed switch.",
                     fg_color="transparent", text_color=theme.FG_DIM,
                     font=theme.font(9),
                     wraplength=600, justify="center").pack(pady=(0, 10))

        tree_frame = ctk.CTkFrame(win, fg_color="transparent", corner_radius=0)
        tree_frame.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        style = ttk.Style()
        theme.apply_treeview_style(style)

        tree = ttk.Treeview(tree_frame,
                             columns=("desc", "ip", "mac", "type"),
                             show="headings",
                             style="PiNT.Treeview",
                             selectmode="browse",
                             height=7)
        tree.heading("desc", text="Interface Name")
        tree.heading("ip",   text="IP Address")
        tree.heading("mac",  text="MAC Address")
        tree.heading("type", text="Type")
        tree.column("desc", width=250)
        tree.column("ip",   width=120)
        tree.column("mac",  width=140)
        tree.column("type", width=90)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._iface_map = {}
        first_rec = None

        for iface in self._interfaces:
            tag = "rec" if iface["recommended"] else "other"
            iid = tree.insert("", "end",
                               values=(iface["description"], iface["ip"],
                                       iface["mac"],         iface["type"]),
                               tags=(tag,))
            self._iface_map[iid] = iface
            if iface["recommended"] and first_rec is None:
                first_rec = iid

        tree.tag_configure("rec",   foreground=theme.SUCCESS)
        tree.tag_configure("other", foreground=theme.FG_DIM)

        default = first_rec or (list(self._iface_map)[0] if self._iface_map else None)
        if default:
            tree.selection_set(default)
            tree.see(default)

        self._tree = tree

        legend = ctk.CTkFrame(win, fg_color="transparent", corner_radius=0)
        legend.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(legend, text="●  Recommended (wired, active)",
                     text_color=theme.SUCCESS, fg_color="transparent",
                     font=theme.font(9)).pack(side="left")
        ctk.CTkLabel(legend, text="    ●  Other",
                     text_color=theme.FG_DIM, fg_color="transparent",
                     font=theme.font(9)).pack(side="left")

        def _confirm():
            sel = tree.selection()
            if sel:
                self.result = self._iface_map[sel[0]]["name"]
            win.destroy()

        btn_frame = ctk.CTkFrame(win, fg_color="transparent", corner_radius=0)
        btn_frame.pack(pady=(0, 14))

        ctk.CTkButton(btn_frame, text="Use Selected Interface",
                      command=_confirm,
                      fg_color=theme.ACCENT, text_color=theme.BG,
                      hover_color=theme.ACCENT_HOVER,
                      font=theme.font(11, "bold"),
                      corner_radius=6, border_width=0,
                      width=200).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="Auto-detect",
                      command=win.destroy,
                      fg_color=theme.PANEL, text_color=theme.FG_DIM,
                      hover_color=theme.PANEL_HOVER,
                      font=theme.font(10),
                      corner_radius=6, border_width=0,
                      width=110).pack(side="left", padx=5)

        win.protocol("WM_DELETE_WINDOW", _confirm)
        parent.wait_window(win)
