import threading

import customtkinter as ctk
from gui import theme, widgets


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

    _POLL_MS = 2000

    def __init__(self, parent, root, app_state):
        self._root         = root
        self._state        = app_state
        self._psutil_iface = None
        self._baseline     = None
        self._running      = False
        self._after_id     = None
        self._build(parent)

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self, parent):
        widgets.description(
            parent,
            "Monitors your network interface for link speed, duplex negotiation "
            "and packet drops.\n\n"
            "Useful as a basic cable test — drops or half-duplex negotiation "
            "often indicate a cable or switch port problem.")

        # ── Link info panel ───────────────────────────────────────────────────
        link_frame = ctk.CTkFrame(parent, fg_color=theme.PANEL, corner_radius=8)
        link_frame.pack(fill="x", padx=40, pady=(0, 10))

        ctk.CTkLabel(link_frame, text="Link Status",
                     fg_color=theme.DIVIDER, text_color=theme.ACCENT,
                     font=theme.font(11, "bold"),
                     corner_radius=0, anchor="center").pack(fill="x", padx=0, pady=0, ipady=8)

        self._link_status_dot = ctk.CTkLabel(link_frame, text="●  —",
                                              fg_color="transparent",
                                              text_color=theme.FG_HINT,
                                              font=theme.font(13))
        self._link_status_dot.pack(pady=(8, 4))

        info_row = ctk.CTkFrame(link_frame, fg_color="transparent", corner_radius=0)
        info_row.pack(pady=(0, 14))

        self._speed_val  = self._stat_cell(info_row, "Speed",   "—")
        self._duplex_val = self._stat_cell(info_row, "Duplex",  "—")
        self._iface_val  = self._stat_cell(info_row, "Adapter", "—")

        # ── Drop/error counter panel ──────────────────────────────────────────
        drop_frame = ctk.CTkFrame(parent, fg_color=theme.PANEL, corner_radius=8)
        drop_frame.pack(fill="x", padx=40, pady=(0, 10))

        ctk.CTkLabel(drop_frame,
                     text="Packet Drops & Errors  (since monitor started)",
                     fg_color=theme.DIVIDER, text_color=theme.ACCENT,
                     font=theme.font(11, "bold"),
                     corner_radius=0, anchor="center").pack(fill="x", padx=0, pady=0, ipady=8)

        counter_row = ctk.CTkFrame(drop_frame, fg_color="transparent", corner_radius=0)
        counter_row.pack(pady=14)

        self._dropin_val  = self._counter_cell(counter_row, "RX Drops")
        self._dropout_val = self._counter_cell(counter_row, "TX Drops")
        self._errin_val   = self._counter_cell(counter_row, "RX Errors")
        self._errout_val  = self._counter_cell(counter_row, "TX Errors")

        # ── Status / buttons ──────────────────────────────────────────────────
        # Status font is 11 here (not the toolbar-standard 10), so built inline.
        self._status = ctk.CTkLabel(parent,
                                    text="Press Start Monitor to begin",
                                    fg_color="transparent", text_color=theme.FG_DIM,
                                    font=theme.font(11))
        self._status.pack(pady=(0, 6))

        btn_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        btn_frame.pack()

        self._start_btn = widgets.primary_button(
            btn_frame, "Start Monitor", self._start,
            width=140, font=theme.font(11, "bold"))
        self._start_btn.pack(side="left", padx=5)

        self._stop_btn = widgets.secondary_button(
            btn_frame, "Stop", self._stop,
            width=80, font=theme.font(11),
            text_color=theme.ERROR, state="disabled")
        self._stop_btn.pack(side="left", padx=5)

        self._reset_btn = widgets.secondary_button(
            btn_frame, "Reset Counters", self._reset_counters,
            width=130, font=theme.font(10), state="disabled")
        self._reset_btn.pack(side="left", padx=5)

    def _stat_cell(self, parent, label, initial):
        """Return the value CTkLabel for a two-line (label / value) stat cell."""
        cell = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        cell.pack(side="left", padx=20)
        ctk.CTkLabel(cell, text=label,
                     fg_color="transparent", text_color=theme.FG_HINT,
                     font=theme.font(11)).pack(anchor="w")
        val = ctk.CTkLabel(cell, text=initial,
                           fg_color="transparent", text_color=theme.FG,
                           font=theme.font(13, "bold"))
        val.pack(anchor="w")
        return val

    def _counter_cell(self, parent, label):
        """Return the value CTkLabel for a drop/error counter cell."""
        cell = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        cell.pack(side="left", padx=24)
        ctk.CTkLabel(cell, text=label,
                     fg_color="transparent", text_color=theme.FG_HINT,
                     font=theme.font(11)).pack(anchor="w")
        val = ctk.CTkLabel(cell, text="0",
                           fg_color="transparent", text_color=theme.SUCCESS,
                           font=theme.font(18, "bold"))
        val.pack(anchor="w")
        return val

    # ── Monitor logic ─────────────────────────────────────────────────────────

    def _start(self):
        self._psutil_iface = _find_psutil_iface(self._state.selected_iface)
        if not self._psutil_iface:
            self._status.configure(
                text="Could not find a matching network adapter via psutil.",
                text_color=theme.ERROR)
            return

        self._baseline = _get_counters(self._psutil_iface)
        self._running  = True
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._reset_btn.configure(state="normal")
        poll_s = self._state.settings.monitor_poll_ms // 1000
        self._status.configure(
            text=f"Monitoring {self._psutil_iface} — updates every {poll_s}s",
            text_color=theme.ACCENT)
        self._poll()

    def _stop(self):
        self._running = False
        if self._after_id:
            self._root.after_cancel(self._after_id)
            self._after_id = None
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._reset_btn.configure(state="disabled")
        self._status.configure(text="Monitor stopped", text_color=theme.FG_DIM)

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

        if is_up:
            self._link_status_dot.configure(text="●  Up", text_color=theme.SUCCESS)
        else:
            self._link_status_dot.configure(text="●  Down", text_color=theme.ERROR)

        self._speed_val.configure(
            text=f"{speed} Mbps" if speed else "Unknown",
            text_color=theme.ACCENT if speed >= 1000 else theme.WARNING if speed > 0 else theme.FG_DIM)

        self._duplex_val.configure(
            text=duplex,
            text_color=theme.SUCCESS if duplex == "Full" else theme.ERROR if duplex == "Half" else theme.FG_DIM)

        self._iface_val.configure(text=self._psutil_iface, text_color=theme.FG_DIM)

        if self._baseline:
            bi, bo, ei, eo = self._baseline
            ci, co, cei, ceo = current
            self._update_counter_display(ci - bi, co - bo, cei - ei, ceo - eo)

        self._after_id = self._root.after(self._state.settings.monitor_poll_ms, self._poll)

    def _update_counter_display(self, dropin, dropout, errin, errout):
        def _colour(n):
            return theme.SUCCESS if n == 0 else theme.ERROR

        self._dropin_val.configure( text=str(dropin),  text_color=_colour(dropin))
        self._dropout_val.configure(text=str(dropout), text_color=_colour(dropout))
        self._errin_val.configure(  text=str(errin),   text_color=_colour(errin))
        self._errout_val.configure( text=str(errout),  text_color=_colour(errout))
