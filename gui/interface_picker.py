import tkinter as tk
from tkinter import ttk


def _enumerate_interfaces():
    """
    Return a list of dicts describing usable network interfaces,
    using scapy's conf.ifaces. Filters out loopback and unassigned.
    """
    interfaces = []
    try:
        from scapy.all import conf
        for name, iface in conf.ifaces.items():
            try:
                ip  = getattr(iface, 'ip',          '') or ''
                mac = getattr(iface, 'mac',         '') or ''
                desc = getattr(iface, 'description', '') or name

                if not ip or ip.startswith('127.') or ip == '0.0.0.0':
                    continue

                dl = desc.lower()
                is_wireless = any(w in dl for w in
                                  ['wi-fi', 'wifi', 'wireless', '802.11'])
                is_virtual  = any(w in dl for w in
                                  ['virtual', 'hyper-v', 'vmware', 'vpn',
                                   'tunnel', 'loopback', 'bluetooth',
                                   'npcap loopback', 'miniport'])
                is_apipa    = ip.startswith('169.254.')

                itype = ('Wireless' if is_wireless
                         else 'Virtual/VPN' if is_virtual
                         else 'Wired')
                recommended = not is_virtual and not is_wireless and not is_apipa

                interfaces.append({
                    'name':        name,
                    'description': desc,
                    'ip':          ip,
                    'mac':         mac,
                    'type':        itype,
                    'recommended': recommended,
                })
            except Exception:
                continue
    except Exception:
        pass
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
    """

    def __init__(self, parent):
        self.result = None
        self._interfaces = _enumerate_interfaces()

        if not self._interfaces:
            return  # nothing usable — let scapy auto-detect

        # One usable interface: silently auto-select it
        if len(self._interfaces) == 1:
            self.result = self._interfaces[0]['name']
            return

        # One clearly recommended interface amid virtual/wireless: auto-select
        recommended = [i for i in self._interfaces if i['recommended']]
        if len(recommended) == 1:
            self.result = recommended[0]['name']
            return

        # Multiple plausible interfaces: let the user choose
        self._build(parent)

    def _build(self, parent):
        win = tk.Toplevel(parent)
        win.title("Select Network Interface")
        win.configure(bg="#1a1a2e")
        win.resizable(False, False)
        win.grab_set()

        w, h = 640, 370
        parent.update_idletasks()
        px = parent.winfo_x() + max(0, (parent.winfo_width()  // 2) - w // 2)
        py = parent.winfo_y() + max(0, (parent.winfo_height() // 2) - h // 2)
        win.geometry(f"{w}x{h}+{px}+{py}")

        tk.Label(win, text="Select Network Interface",
                 bg="#1a1a2e", fg="#00d4ff",
                 font=("Arial", 14, "bold")).pack(pady=(16, 4))

        tk.Label(win,
                 text="Multiple network adapters detected. "
                      "Select the wired Ethernet interface connected to your managed switch.",
                 bg="#1a1a2e", fg="#888888",
                 font=("Arial", 9),
                 wraplength=600, justify="center").pack(pady=(0, 10))

        tree_frame = tk.Frame(win, bg="#1a1a2e")
        tree_frame.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        style = ttk.Style()
        style.configure("Picker.Treeview",
                         background="#16213e", foreground="#eee",
                         fieldbackground="#16213e",
                         rowheight=30, font=("Arial", 10))
        style.configure("Picker.Treeview.Heading",
                         background="#0f3460", foreground="#00d4ff",
                         font=("Arial", 10, "bold"))
        style.map("Picker.Treeview", background=[("selected", "#0f3460")])

        tree = ttk.Treeview(tree_frame,
                             columns=("desc", "ip", "mac", "type"),
                             show="headings",
                             style="Picker.Treeview",
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

        tree.tag_configure("rec",   foreground="#00ff88")
        tree.tag_configure("other", foreground="#888888")

        default = first_rec or (list(self._iface_map)[0] if self._iface_map else None)
        if default:
            tree.selection_set(default)
            tree.see(default)

        self._tree = tree

        legend = tk.Frame(win, bg="#1a1a2e")
        legend.pack(fill="x", padx=16, pady=(0, 6))
        tk.Label(legend, text="●  Recommended (wired, active)",
                 fg="#00ff88", bg="#1a1a2e", font=("Arial", 9)).pack(side="left")
        tk.Label(legend, text="    ●  Other",
                 fg="#888888", bg="#1a1a2e", font=("Arial", 9)).pack(side="left")

        def _confirm():
            sel = tree.selection()
            if sel:
                self.result = self._iface_map[sel[0]]["name"]
            win.destroy()

        btn_frame = tk.Frame(win, bg="#1a1a2e")
        btn_frame.pack(pady=(0, 14))

        tk.Button(btn_frame, text="Use Selected Interface",
                  command=_confirm,
                  bg="#00d4ff", fg="#1a1a2e",
                  font=("Arial", 11, "bold"),
                  padx=20, relief="flat",
                  highlightthickness=0, borderwidth=0).pack(side="left", padx=5)

        tk.Button(btn_frame, text="Auto-detect",
                  command=win.destroy,
                  bg="#16213e", fg="#888888",
                  font=("Arial", 10),
                  padx=12, relief="flat",
                  highlightthickness=0, borderwidth=0).pack(side="left", padx=5)

        win.protocol("WM_DELETE_WINDOW", _confirm)
        parent.wait_window(win)
