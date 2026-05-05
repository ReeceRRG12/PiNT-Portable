import tkinter as tk
from tkinter import ttk
import threading


def _find_psutil_iface(selected_scapy_iface):
    """
    Map a scapy interface name to a psutil interface name by matching IP addresses.
    Falls back to the first non-loopback interface if no match is found.
    """
    import psutil

    target_ip = None
    if selected_scapy_iface:
        try:
            from scapy.all import conf
            iface_obj = conf.ifaces.get(selected_scapy_iface)
            if iface_obj:
                target_ip = getattr(iface_obj, 'ip', None)
        except Exception:
            pass

    addrs = psutil.net_if_addrs()

    if target_ip:
        for name, addr_list in addrs.items():
            for addr in addr_list:
                if addr.address == target_ip:
                    return name

    # Fallback: first adapter that has an IPv4 address and is up
    stats = psutil.net_if_stats()
    for name, addr_list in addrs.items():
        if not stats.get(name, None) or not stats[name].isup:
            continue
        for addr in addr_list:
            if '.' in addr.address and not addr.address.startswith('127.'):
                return name

    return None


def _get_link_stats(psutil_iface):
    """Return (speed_mbps, duplex_str, is_up) for a psutil interface name."""
    import psutil
    try:
        st = psutil.net_if_stats().get(psutil_iface)
        if not st:
            return 0, 'Unknown', False
        duplex_map = {
            psutil.NIC_DUPLEX_FULL:    'Full',
            psutil.NIC_DUPLEX_HALF:    'Half',
            psutil.NIC_DUPLEX_UNKNOWN: 'Unknown',
        }
        return st.speed, duplex_map.get(st.duplex, 'Unknown'), st.isup
    except Exception:
        return 0, 'Unknown', False


def _get_counters(psutil_iface):
    """Return (dropin, dropout, errin, errout) for a psutil interface name."""
    import psutil
    try:
        c = psutil.net_io_counters(pernic=True).get(psutil_iface)
        if not c:
            return 0, 0, 0, 0
        return c.dropin, c.dropout, c.errin, c.errout
    except Exception:
        return 0, 0, 0, 0


class MonitorTab:
    """
    Port Monitor tab — shows negotiated link speed and duplex, and tracks
    dropped/errored packets since monitoring started.  Useful as a basic
    cable-test: drops or half-duplex negotiation often point to a bad cable
    or a mis-configured switch port.
    """

    _POLL_MS = 2000  # refresh interval in milliseconds

    def __init__(self, parent, root, app_state):
        self._root      = root
        self._state     = app_state
        self._psutil_iface = None   # resolved on each monitor start
        self._baseline  = None      # (dropin, dropout, errin, errout) at start
        self._running   = False
        self._after_id  = None
        self._build(parent)

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self, parent):
        tk.Label(parent,
                 text="Monitors your network interface for link speed, duplex negotiation "
                      "and packet drops. Useful as a basic cable test — drops or half-duplex "
                      "negotiation often indicate a cable or switch port problem.",
                 bg="#1a1a2e", fg="#555555",
                 font=("Arial", 9, "italic"),
                 wraplength=460, justify="left").pack(
                     fill="x", padx=10, pady=(0, 6), anchor="w")

        # ── Link info panel ───────────────────────────────────────────────────
        link_frame = tk.Frame(parent, bg="#16213e")
        link_frame.pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(link_frame, text="Link Status",
                 bg="#0f3460", fg="#00d4ff",
                 font=("Arial", 10, "bold"),
                 padx=10, pady=4).pack(fill="x")

        self._link_status_dot = tk.Label(link_frame, text="●  —",
                                          bg="#16213e", fg="#555555",
                                          font=("Arial", 12), padx=14, pady=6)
        self._link_status_dot.pack(anchor="w")

        info_row = tk.Frame(link_frame, bg="#16213e")
        info_row.pack(fill="x", padx=14, pady=(0, 10))

        self._speed_val  = self._stat_cell(info_row, "Speed",  "—")
        self._duplex_val = self._stat_cell(info_row, "Duplex", "—")
        self._iface_val  = self._stat_cell(info_row, "Adapter", "—")

        # ── Drop/error counter panel ──────────────────────────────────────────
        drop_frame = tk.Frame(parent, bg="#16213e")
        drop_frame.pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(drop_frame, text="Packet Drops & Errors  (since monitor started)",
                 bg="#0f3460", fg="#00d4ff",
                 font=("Arial", 10, "bold"),
                 padx=10, pady=4).pack(fill="x")

        counter_row = tk.Frame(drop_frame, bg="#16213e")
        counter_row.pack(fill="x", padx=14, pady=10)

        self._dropin_val  = self._counter_cell(counter_row, "RX Drops")
        self._dropout_val = self._counter_cell(counter_row, "TX Drops")
        self._errin_val   = self._counter_cell(counter_row, "RX Errors")
        self._errout_val  = self._counter_cell(counter_row, "TX Errors")

        # ── Status / buttons ──────────────────────────────────────────────────
        self._status = tk.Label(parent,
                                text="Press Start Monitor to begin",
                                bg="#1a1a2e", fg="#888888",
                                font=("Arial", 9))
        self._status.pack(pady=(0, 6))

        btn_frame = tk.Frame(parent, bg="#1a1a2e")
        btn_frame.pack()

        self._start_btn = tk.Button(btn_frame, text="Start Monitor",
                                    command=self._start,
                                    bg="#00d4ff", fg="#1a1a2e",
                                    font=("Arial", 11, "bold"),
                                    padx=20, relief="flat",
                                    highlightthickness=0, borderwidth=0)
        self._start_btn.pack(side="left", padx=5)

        self._stop_btn = tk.Button(btn_frame, text="Stop",
                                   command=self._stop,
                                   bg="#16213e", fg="#ff4757",
                                   font=("Arial", 11),
                                   padx=20, relief="flat",
                                   highlightthickness=0, borderwidth=0,
                                   state="disabled")
        self._stop_btn.pack(side="left", padx=5)

        self._reset_btn = tk.Button(btn_frame, text="Reset Counters",
                                    command=self._reset_counters,
                                    bg="#16213e", fg="#eee",
                                    font=("Arial", 10),
                                    padx=12, relief="flat",
                                    highlightthickness=0, borderwidth=0,
                                    state="disabled")
        self._reset_btn.pack(side="left", padx=5)

    def _stat_cell(self, parent, label, initial):
        """Return the value Label for a two-line (label / value) stat cell."""
        cell = tk.Frame(parent, bg="#16213e", padx=16)
        cell.pack(side="left")
        tk.Label(cell, text=label, bg="#16213e", fg="#555555",
                 font=("Arial", 8)).pack(anchor="w")
        val = tk.Label(cell, text=initial, bg="#16213e", fg="#eee",
                       font=("Arial", 13, "bold"))
        val.pack(anchor="w")
        return val

    def _counter_cell(self, parent, label):
        """Return the value Label for a drop/error counter cell."""
        cell = tk.Frame(parent, bg="#16213e", padx=20)
        cell.pack(side="left")
        tk.Label(cell, text=label, bg="#16213e", fg="#555555",
                 font=("Arial", 8)).pack(anchor="w")
        val = tk.Label(cell, text="0", bg="#16213e", fg="#00ff88",
                       font=("Arial", 18, "bold"))
        val.pack(anchor="w")
        return val

    # ── Monitor logic ─────────────────────────────────────────────────────────

    def _start(self):
        self._psutil_iface = _find_psutil_iface(self._state.selected_iface)
        if not self._psutil_iface:
            self._status.config(
                text="Could not find a matching network adapter via psutil.",
                fg="#ff4757")
            return

        self._baseline = _get_counters(self._psutil_iface)
        self._running  = True
        self._start_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        self._reset_btn.config(state="normal")
        self._status.config(text=f"Monitoring {self._psutil_iface} — updates every 2s",
                            fg="#00d4ff")
        self._poll()

    def _stop(self):
        self._running = False
        if self._after_id:
            self._root.after_cancel(self._after_id)
            self._after_id = None
        self._start_btn.config(state="normal")
        self._stop_btn.config(state="disabled")
        self._reset_btn.config(state="disabled")
        self._status.config(text="Monitor stopped", fg="#888888")

    def _reset_counters(self):
        if self._psutil_iface:
            self._baseline = _get_counters(self._psutil_iface)
            self._update_counter_display(0, 0, 0, 0)

    def _poll(self):
        if not self._running:
            return
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        if not self._psutil_iface:
            return
        speed, duplex, is_up = _get_link_stats(self._psutil_iface)
        current = _get_counters(self._psutil_iface)
        self._root.after(0, self._refresh_ui, speed, duplex, is_up, current)

    def _refresh_ui(self, speed, duplex, is_up, current):
        if not self._running:
            return

        # Link status row
        if is_up:
            self._link_status_dot.config(text="●  Up", fg="#00ff88")
        else:
            self._link_status_dot.config(text="●  Down", fg="#ff4757")

        self._speed_val.config(
            text=f"{speed} Mbps" if speed else "Unknown",
            fg="#00d4ff" if speed >= 1000 else "#ffaa00" if speed > 0 else "#888888")

        self._duplex_val.config(
            text=duplex,
            fg="#00ff88" if duplex == "Full" else "#ff4757" if duplex == "Half" else "#888888")

        self._iface_val.config(text=self._psutil_iface, fg="#888888")

        # Drop/error deltas
        if self._baseline:
            bi, bo, ei, eo = self._baseline
            ci, co, cei, ceo = current
            self._update_counter_display(ci - bi, co - bo, cei - ei, ceo - eo)

        # Schedule next poll
        self._after_id = self._root.after(self._POLL_MS, self._poll)

    def _update_counter_display(self, dropin, dropout, errin, errout):
        def _colour(n):
            return "#00ff88" if n == 0 else "#ff4757"

        self._dropin_val.config( text=str(dropin),  fg=_colour(dropin))
        self._dropout_val.config(text=str(dropout), fg=_colour(dropout))
        self._errin_val.config(  text=str(errin),   fg=_colour(errin))
        self._errout_val.config( text=str(errout),  fg=_colour(errout))
