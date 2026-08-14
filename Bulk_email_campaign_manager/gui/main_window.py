"""
gui/main_window.py
──────────────────
Professional SaaS-style app shell.
Dark sidebar + top header + view container.
All functionality is unchanged – only the visual layer was redesigned.
"""

import customtkinter as ctk

# Apply dark theme globally BEFORE any CTk widget is constructed.
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

from gui.views import (
    DashboardView, ContactsView, CampaignView,
    SchedulerView, LogsView, SettingsView,
)

# ─── Navigation definition ─────────────────────────────────────────────────────
#  (route_key, sidebar_icon, sidebar_label, header_title)
_NAV = [
    ("dashboard", "⊞",  "Dashboard",       "Dashboard"),
    ("contacts",  "◎",  "Contacts",         "Contacts Management"),
    ("campaign",  "✉",  "Create Campaign",  "Create Campaign"),
    ("scheduler", "⏰", "Scheduler",        "Campaign Scheduler"),
    ("logs",      "≡",  "Campaign Logs",    "Campaign Logs"),
    ("settings",  "⚙",  "Settings",         "Settings"),
]

# ─── Sidebar colour tokens ─────────────────────────────────────────────────────
_SB_BG   = "#13192A"   # sidebar background
_ACT_BG  = "#1A2D4A"   # active-item background
_ACT_FG  = "#5B8AF0"   # active-item text / accent
_INACT   = "#6B7A99"   # inactive item text
_DIVIDER = "#1E2840"   # divider lines
_APP_BG  = "#0F1117"   # main content background
_HDR_BG  = "#13192A"   # top header background


class MainWindow(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("Campaign Manager Pro")
        self.geometry("1300x820")
        self.minsize(1060, 650)
        self.configure(fg_color=_APP_BG)

        # Two-column root grid: sidebar | content
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_main_area()

        # ── Instantiate all views ────────────────────────────────────────────
        _CLS = {
            "dashboard": DashboardView,
            "contacts":  ContactsView,
            "campaign":  CampaignView,
            "scheduler": SchedulerView,
            "logs":      LogsView,
            "settings":  SettingsView,
        }
        self.views: dict[str, ctk.CTkBaseClass] = {
            k: _CLS[k](self._vc) for k in _CLS
        }
        self.current_view: str | None = None
        self.select_view("dashboard")

    # ── Private builders ──────────────────────────────────────────────────────

    def _build_sidebar(self) -> None:
        """Build the left navigation sidebar."""
        sb = ctk.CTkFrame(self, width=225, corner_radius=0, fg_color=_SB_BG)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_columnconfigure(0, weight=1)

        # Row layout:
        #  0 = brand     1 = divider   2 = "MENU" label
        #  3–8 = nav buttons            9 = spacer (weight=1)
        # 10 = divider  11 = theme row
        sb.grid_rowconfigure(9, weight=1)

        # ── Brand ────────────────────────────────────────────────────────────
        brand = ctk.CTkFrame(sb, fg_color="transparent")
        brand.grid(row=0, column=0, padx=18, pady=(26, 18), sticky="ew")

        ctk.CTkLabel(
            brand, text="◉", font=ctk.CTkFont(size=30), text_color=_ACT_FG
        ).pack(side="left", padx=(0, 10))

        btext = ctk.CTkFrame(brand, fg_color="transparent")
        btext.pack(side="left")
        ctk.CTkLabel(
            btext, text="Campaign",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#E2E8F0"
        ).pack(anchor="w")
        ctk.CTkLabel(
            btext, text="Manager Pro",
            font=ctk.CTkFont(size=10), text_color=_ACT_FG
        ).pack(anchor="w")

        # ── Top divider ──────────────────────────────────────────────────────
        ctk.CTkFrame(sb, height=1, fg_color=_DIVIDER).grid(
            row=1, column=0, sticky="ew", padx=14, pady=(0, 8))

        # ── Menu label ───────────────────────────────────────────────────────
        ctk.CTkLabel(
            sb, text="MAIN MENU",
            font=ctk.CTkFont(size=9, weight="bold"), text_color="#2E3D58"
        ).grid(row=2, column=0, sticky="w", padx=22, pady=(4, 6))

        # ── Nav buttons ──────────────────────────────────────────────────────
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for i, (key, icon, label, _title) in enumerate(_NAV):
            btn = ctk.CTkButton(
                sb,
                text=f"  {icon}   {label}",
                anchor="w",
                height=44,
                corner_radius=9,
                fg_color="transparent",
                hover_color="#182340",
                text_color=_INACT,
                font=ctk.CTkFont(size=13),
                command=lambda k=key: self.select_view(k),
            )
            btn.grid(row=3 + i, column=0, padx=10, pady=2, sticky="ew")
            self._nav_btns[key] = btn

        # ── Bottom divider ───────────────────────────────────────────────────
        ctk.CTkFrame(sb, height=1, fg_color=_DIVIDER).grid(
            row=10, column=0, sticky="ew", padx=14, pady=(8, 8))

        # ── Theme row ────────────────────────────────────────────────────────
        bot = ctk.CTkFrame(sb, fg_color="transparent")
        bot.grid(row=11, column=0, padx=12, pady=(0, 18), sticky="ew")
        bot.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            bot, text="🌙", text_color=_INACT, font=ctk.CTkFont(size=14)
        ).grid(row=0, column=0, padx=(4, 8))

        tm = ctk.CTkOptionMenu(
            bot,
            values=["Dark", "Light", "System"],
            command=lambda v: ctk.set_appearance_mode(v),
            fg_color="#1E2840",
            button_color="#252E45",
            button_hover_color="#2D3A58",
            text_color="#8B9CB8",
            font=ctk.CTkFont(size=12),
            height=32,
        )
        tm.grid(row=0, column=1, sticky="ew")
        tm.set("Dark")

    def _build_main_area(self) -> None:
        """Build the right-hand content column (header + view container)."""
        area = ctk.CTkFrame(self, fg_color=_APP_BG, corner_radius=0)
        area.grid(row=0, column=1, sticky="nsew")
        area.grid_rowconfigure(1, weight=1)
        area.grid_columnconfigure(0, weight=1)

        # ── Top header bar ───────────────────────────────────────────────────
        hdr = ctk.CTkFrame(area, height=62, corner_radius=0, fg_color=_HDR_BG)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(0, weight=1)

        self.header_title = ctk.CTkLabel(
            hdr, text="Dashboard",
            font=ctk.CTkFont(size=21, weight="bold"),
            text_color="#E2E8F0",
        )
        self.header_title.grid(row=0, column=0, padx=28, sticky="w")

        rhs = ctk.CTkFrame(hdr, fg_color="transparent")
        rhs.grid(row=0, column=1, padx=24, sticky="e")
        ctk.CTkLabel(
            rhs, text="●", text_color="#34D399", font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(
            rhs, text="SMTP Ready", font=ctk.CTkFont(size=12), text_color="#6B7A99"
        ).pack(side="left")

        # ── View container ───────────────────────────────────────────────────
        self._vc = ctk.CTkFrame(area, fg_color="transparent")
        self._vc.grid(row=1, column=0, sticky="nsew")
        self._vc.grid_rowconfigure(0, weight=1)
        self._vc.grid_columnconfigure(0, weight=1)

    # ── Public API ────────────────────────────────────────────────────────────

    def select_view(self, name: str) -> None:
        """Switch the visible view and update the active nav button."""
        if self.current_view:
            self.views[self.current_view].grid_forget()

        title = next((t for k, _i, _l, t in _NAV if k == name), name.title())
        self.header_title.configure(text=title)

        self.current_view = name
        self.views[name].grid(row=0, column=0, sticky="nsew")

        for k, btn in self._nav_btns.items():
            active = k == name
            btn.configure(
                fg_color=_ACT_BG  if active else "transparent",
                text_color=_ACT_FG if active else _INACT,
            )

    # Kept for backward-compat with any code that calls this method
    def change_appearance_mode_event(self, mode: str) -> None:
        ctk.set_appearance_mode(mode)
