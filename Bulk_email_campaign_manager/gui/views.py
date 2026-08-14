"""
gui/views.py
────────────
Modern professional SaaS-style views for Campaign Manager Pro.

Visual layer completely redesigned.  All backend logic methods are
preserved verbatim – only __init__ layouts were changed.
"""

import customtkinter as ctk
import tkinter as tk
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import shutil
from tkinter import messagebox, filedialog
import threading
import schedule
import dotenv
import webbrowser
import tempfile
import os

from config import settings, CONTACTS_FILE, TEMPLATE_FILE, LOG_FILE, MAX_EMAILS_PER_HOUR
from email_sender import EmailSender, send_campaign
from utils import ContactLoader, render_template
from scheduler import run_daily, run_every_hours, run_scheduler

# Optional HTML renderer (not used inline; kept for future use)
try:
    from tkinterweb import HtmlFrame
    _TKINTERWEB_AVAILABLE = True
except ImportError:
    _TKINTERWEB_AVAILABLE = False

# ─── Scheduler daemon thread ──────────────────────────────────────────────────
_scheduler_thread = None

def _start_scheduler_thread():
    global _scheduler_thread
    if _scheduler_thread is None or not _scheduler_thread.is_alive():
        _scheduler_thread = threading.Thread(
            target=lambda: run_scheduler(poll_interval=10), daemon=True)
        _scheduler_thread.start()

# ─── File paths ───────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent.parent
CONTACTS_PATH = BASE_DIR / CONTACTS_FILE
LOGS_PATH     = BASE_DIR / LOG_FILE

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
C_APP    = "#0F1117"   # app / page background
C_CARD   = "#1A2236"   # card surface
C_CARD2  = "#141C2E"   # slightly darker surface (inputs, nested panels)
C_BORDER = "#252D40"   # card / input border
C_ROW    = "#1C2640"   # table row background
C_ROW_A  = "#18203A"   # alternate row

C_ACCENT = "#5B8AF0"   # primary blue
C_ADARK  = "#3D6FD9"   # accent hover
C_GREEN  = "#34D399"   # success
C_GDARK  = "#22A876"   # green hover
C_RED    = "#FC6C6C"   # error / danger
C_RDARK  = "#D44D4D"   # red hover
C_AMBER  = "#FBBF24"   # warning
C_PURPLE = "#A78BFA"   # info / misc

C_T1 = "#E2E8F0"   # primary text
C_T2 = "#8B9CB8"   # secondary text
C_T3 = "#4A5E7A"   # muted / placeholder

# ── Widget factories ──────────────────────────────────────────────────────────

def _card(parent, **kw) -> ctk.CTkFrame:
    defaults = dict(fg_color=C_CARD, corner_radius=12,
                    border_width=1, border_color=C_BORDER)
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


def _card_title(card: ctk.CTkFrame, text: str, row: int = None, col_span: int = 2):
    f = ctk.CTkFrame(card, fg_color="transparent")
    ctk.CTkLabel(f, text=text,
                 font=ctk.CTkFont(size=13, weight="bold"),
                 text_color=C_T2).pack(anchor="w", padx=16, pady=(14, 0))
    ctk.CTkFrame(f, height=1, fg_color=C_BORDER).pack(
        fill="x", padx=16, pady=(8, 0))
    if row is not None:
        f.grid(row=row, column=0, columnspan=col_span, sticky="ew")
    else:
        f.pack(fill="x")


def _lbl(parent, text="", size=13, weight="normal", color=C_T1, **kw):
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont(size=size, weight=weight),
                        text_color=color, **kw)


def _btn_primary(parent, text, cmd, **kw):
    d = dict(fg_color=C_ACCENT, hover_color=C_ADARK, text_color="white",
             corner_radius=8, height=36, font=ctk.CTkFont(size=13, weight="bold"))
    d.update(kw)
    return ctk.CTkButton(parent, text=text, command=cmd, **d)


def _btn_danger(parent, text, cmd, **kw):
    d = dict(fg_color=C_RED, hover_color=C_RDARK, text_color="white",
             corner_radius=8, height=36, font=ctk.CTkFont(size=13, weight="bold"))
    d.update(kw)
    return ctk.CTkButton(parent, text=text, command=cmd, **d)


def _btn_success(parent, text, cmd, **kw):
    d = dict(fg_color=C_GREEN, hover_color=C_GDARK, text_color="white",
             corner_radius=8, height=36, font=ctk.CTkFont(size=13, weight="bold"))
    d.update(kw)
    return ctk.CTkButton(parent, text=text, command=cmd, **d)


def _btn_ghost(parent, text, cmd, **kw):
    d = dict(fg_color=C_CARD2, hover_color=C_ROW, text_color=C_T2,
             border_width=1, border_color=C_BORDER,
             corner_radius=8, height=36, font=ctk.CTkFont(size=13))
    d.update(kw)
    return ctk.CTkButton(parent, text=text, command=cmd, **d)


def _entry(parent, placeholder="", **kw):
    d = dict(fg_color=C_CARD2, border_color=C_BORDER, border_width=1,
             text_color=C_T1, placeholder_text_color=C_T3,
             corner_radius=8, height=38, font=ctk.CTkFont(size=13),
             placeholder_text=placeholder)
    d.update(kw)
    return ctk.CTkEntry(parent, **d)


def _chip(parent, text, color):
    """Inline stat chip label."""
    f = ctk.CTkFrame(parent, fg_color=C_CARD2, corner_radius=6,
                     border_width=1, border_color=color)
    f.pack(side="left", padx=5)
    lbl = ctk.CTkLabel(f, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                       text_color=color)
    lbl.pack(padx=10, pady=4)
    return lbl


def _section_title(parent, text, row, col, **kw):
    _lbl(parent, text=text, size=12, color=C_T3).grid(
        row=row, column=col, sticky="w", pady=(12, 4), **kw)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD VIEW
# ══════════════════════════════════════════════════════════════════════════════
class DashboardView(ctk.CTkScrollableFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=C_APP, **kwargs)
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # ── Row 0 : 4 KPI stat cards ─────────────────────────────────────────
        self._build_stat_cards()

        # ── Row 1 : Progress card (left) + Quick Actions (right) ─────────────
        self._build_mid_row()

        # ── Row 2 : Recent activity ───────────────────────────────────────────
        self._build_activity()

        # Top action bar (refresh)
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.grid(row=3, column=0, columnspan=4, sticky="e", padx=20, pady=(0, 14))
        _btn_ghost(ctrl, "↻  Refresh", self.refresh_data, width=110).pack()

        self.refresh_data()

    # ── Layout helpers ────────────────────────────────────────────────────────

    def _draw_circle(self, canvas, percentage, color):
        canvas.delete("all")
        # Draw background circle
        canvas.create_arc(4, 4, 60, 60, start=0, extent=359.99, 
                          style="arc", outline=C_CARD2, width=6)
        # Draw foreground arc (extent is negative to draw clockwise)
        extent = - (percentage * 359.99)
        if extent == 0:
            return
        canvas.create_arc(4, 4, 60, 60, start=90, extent=extent, 
                          style="arc", outline=color, width=6)

    def _build_stat_cards(self):
        pad = dict(padx=8, pady=(20, 8), sticky="nsew")

        # Card 1 – Contacts
        c1 = _card(self)
        c1.grid(row=0, column=0, **pad)
        _lbl(c1, "📋  Audience", size=14, weight="bold", color=C_T2).pack(anchor="w", padx=16, pady=(14, 4))
        self.lbl_total_contacts = _lbl(c1, "0", size=32, weight="bold", color=C_T1)
        self.lbl_total_contacts.pack(anchor="w", padx=16, pady=(4, 0))
        _lbl(c1, "Total Contacts", size=12, color=C_T3).pack(anchor="w", padx=16, pady=(0, 8))
        
        f1 = ctk.CTkFrame(c1, fg_color="transparent")
        f1.pack(fill="x", padx=16, pady=(0, 14))
        self.lbl_valid_contacts = _lbl(f1, "Valid: 0", size=12, color=C_GREEN)
        self.lbl_valid_contacts.pack(side="left")
        self.lbl_invalid_contacts = _lbl(f1, "Invalid: 0", size=12, color=C_RED)
        self.lbl_invalid_contacts.pack(side="right")

        # Card 2 – Sent
        c2 = _card(self)
        c2.grid(row=0, column=1, **pad)
        _lbl(c2, "✉  Deliveries", size=14, weight="bold", color=C_T2).pack(anchor="w", padx=16, pady=(14, 4))
        self.lbl_sent_emails = _lbl(c2, "0", size=32, weight="bold", color=C_GREEN)
        self.lbl_sent_emails.pack(anchor="w", padx=16, pady=(4, 0))
        _lbl(c2, "Emails Sent", size=12, color=C_T3).pack(anchor="w", padx=16, pady=(0, 8))
        
        f2 = ctk.CTkFrame(c2, fg_color="transparent")
        f2.pack(fill="x", padx=16, pady=(0, 14))
        self.lbl_failed_emails = _lbl(f2, "Failed: 0", size=12, color=C_RED)
        self.lbl_failed_emails.pack(side="left")
        self.lbl_remaining_emails = _lbl(f2, "Remaining: 0", size=12, color=C_T2)
        self.lbl_remaining_emails.pack(side="right")

        # Card 3 – Rate limit
        c3 = _card(self)
        c3.grid(row=0, column=2, **pad)
        _lbl(c3, "⏱  Hourly Rate Limit", size=14, weight="bold", color=C_T2).pack(anchor="w", padx=16, pady=(14, 4))
        
        import tkinter as tk
        self.rate_canvas = tk.Canvas(c3, width=64, height=64, bg=C_CARD, highlightthickness=0)
        self.rate_canvas.pack(pady=(4, 4))
        self._draw_circle(self.rate_canvas, 0, C_AMBER)
        
        self.lbl_sent_this_hour = _lbl(c3, "0 / 50 sent", size=13, weight="bold", color=C_T1)
        self.lbl_sent_this_hour.pack(pady=(2, 2))
        self.lbl_rate_warning = _lbl(c3, "", size=11, color=C_AMBER)
        self.lbl_rate_warning.pack(pady=(0, 8))

        # Card 4 – Overall progress
        c4 = _card(self)
        c4.grid(row=0, column=3, **pad)
        _lbl(c4, "📈  Campaign Progress", size=14, weight="bold", color=C_T2).pack(anchor="w", padx=16, pady=(14, 4))
        
        self.lbl_progress_text = _lbl(c4, "0%", size=36, weight="bold", color=C_ACCENT)
        self.lbl_progress_text.pack(pady=(2, 0))
        
        self.progress_bar = ctk.CTkProgressBar(c4, progress_color=C_ACCENT, fg_color=C_CARD2, height=6)
        self.progress_bar.pack(fill="x", padx=24, pady=(8, 6))
        self.progress_bar.set(0)
        
        self.lbl_campaign_status = _lbl(c4, "Status: Idle", size=12, color=C_T3)
        self.lbl_campaign_status.pack(pady=(0, 10))

    def _build_mid_row(self):
        acts = ctk.CTkFrame(self, fg_color="transparent")
        acts.grid(row=1, column=0, columnspan=4, padx=8, pady=(0, 8), sticky="ew")
        
        _btn_primary(acts, "➕  Import Contacts",
                     lambda: self.winfo_toplevel().select_view("contacts"),
                     width=160).pack(side="left", padx=(0, 10))
        _btn_ghost(acts, "✉  Create Campaign",
                   lambda: self.winfo_toplevel().select_view("campaign"),
                   width=160).pack(side="left", padx=10)
        _btn_ghost(acts, "⏰  Scheduler",
                   lambda: self.winfo_toplevel().select_view("scheduler"),
                   width=160).pack(side="left", padx=10)
        _btn_ghost(acts, "≡  View Logs",
                   lambda: self.winfo_toplevel().select_view("logs"),
                   width=160).pack(side="left", padx=10)

    def _build_activity(self):
        act = _card(self)
        act.grid(row=2, column=0, columnspan=4,
                 padx=8, pady=(0, 20), sticky="nsew")
        _card_title(act, "🕐  Recent Campaign Activity", row=None)

        self.activity_list_frame = ctk.CTkFrame(act, fg_color="transparent")
        self.activity_list_frame.pack(fill="both", expand=True,
                                      padx=16, pady=(10, 16))

    # ── Backend-connected logic (UNCHANGED) ───────────────────────────────────

    def refresh_data(self):
        total_contacts = valid_contacts = invalid_contacts = 0

        if CONTACTS_PATH.exists():
            try:
                loader = ContactLoader(CONTACTS_PATH)
                res = loader.load()
                total_contacts = res.total_raw
                valid_contacts = res.total_valid
                invalid_contacts = res.total_invalid
            except Exception:
                pass

        self.lbl_total_contacts.configure(text=f"{total_contacts}")
        self.lbl_valid_contacts.configure(text=f"Valid: {valid_contacts}")
        self.lbl_invalid_contacts.configure(text=f"Invalid: {invalid_contacts}")

        total_sent = total_failed = sent_this_hour = 0

        for w in self.activity_list_frame.winfo_children():
            w.destroy()

        if LOGS_PATH.exists():
            try:
                df = pd.read_csv(LOGS_PATH)
                if "status" in df.columns:
                    total_sent   = len(df[df["status"] == "Sent"])
                    total_failed = len(df[df["status"] == "Failed"])

                if "timestamp" in df.columns:
                    df["ts_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
                    one_ago = datetime.now() - timedelta(hours=1)
                    sent_this_hour = len(
                        df[(df["ts_dt"] >= one_ago) & (df["status"] == "Sent")]
                    )

                recent = df.tail(10).iloc[::-1]

                if recent.empty:
                    _lbl(self.activity_list_frame,
                         "No campaign activity yet.", color=C_T3).pack(anchor="w")
                else:
                    # Header row
                    hf = ctk.CTkFrame(self.activity_list_frame,
                                      fg_color=C_CARD2, corner_radius=6)
                    hf.pack(fill="x", pady=(0, 4))
                    for txt, w in [("Timestamp", 160), ("Recipient", 160),
                                   ("Subject", 0), ("Status", 80)]:
                        kw = dict(width=w, anchor="w") if w else dict(anchor="w")
                        _lbl(hf, txt, size=11, weight="bold", color=C_T3,
                             **kw).pack(
                            side="left", padx=8, pady=6,
                            **({"fill": "x", "expand": True} if not w else {}))

                    for idx, row in enumerate(recent.itertuples()):
                        bg = C_ROW if idx % 2 == 0 else C_ROW_A
                        rf = ctk.CTkFrame(self.activity_list_frame,
                                          fg_color=bg, corner_radius=6)
                        rf.pack(fill="x", pady=2)

                        time_s = str(getattr(row, "timestamp", ""))[:19]
                        name   = str(getattr(row, "name", getattr(row, "email", "")))
                        subj   = str(getattr(row, "subject", ""))
                        status = str(getattr(row, "status", ""))
                        col    = C_GREEN if status == "Sent" else (
                                  C_RED if status == "Failed" else C_T2)

                        _lbl(rf, time_s[:19], size=12,
                             width=160, anchor="w").pack(side="left", padx=8, pady=6)
                        _lbl(rf, name[:22], size=12,
                             width=160, anchor="w").pack(side="left", padx=8)
                        _lbl(rf, subj[:38], size=12,
                             anchor="w").pack(side="left", padx=8,
                                              fill="x", expand=True)
                        _lbl(rf, status, size=12, weight="bold",
                             color=col, width=80).pack(side="right", padx=8)

            except Exception as e:
                _lbl(self.activity_list_frame,
                     f"Could not load logs: {e}", color=C_RED).pack(anchor="w")
        else:
            _lbl(self.activity_list_frame,
                 "No campaign activity yet (log file missing).",
                 color=C_T3).pack(anchor="w")

        self.lbl_sent_emails.configure(text=f"{total_sent}")
        self.lbl_failed_emails.configure(text=f"Failed: {total_failed}")
        remaining = max(0, valid_contacts - total_sent)
        self.lbl_remaining_emails.configure(text=f"Remaining: {remaining}")
        
        self.lbl_sent_this_hour.configure(text=f"{sent_this_hour} / {MAX_EMAILS_PER_HOUR} sent")
        rem_hourly = max(0, MAX_EMAILS_PER_HOUR - sent_this_hour)
        if rem_hourly == 0:
            self.lbl_rate_warning.configure(text="⚠ Hourly limit reached!", text_color=C_RED)
        else:
            self.lbl_rate_warning.configure(text="")
        
        pct_hourly = min(1.0, sent_this_hour / MAX_EMAILS_PER_HOUR) if MAX_EMAILS_PER_HOUR > 0 else 0
        self._draw_circle(self.rate_canvas, pct_hourly, C_AMBER if pct_hourly < 0.9 else C_RED)

        progress_val = min(1.0, total_sent / valid_contacts) if valid_contacts > 0 else 0.0
        self.progress_bar.set(progress_val)
        self.lbl_progress_text.configure(text=f"{int(progress_val * 100)}%")
        
        if progress_val >= 1.0 and valid_contacts > 0:
            self.lbl_campaign_status.configure(text="Status: Completed", text_color=C_GREEN)
        elif progress_val > 0:
            self.lbl_campaign_status.configure(text="Status: In Progress", text_color=C_ACCENT)
        else:
            self.lbl_campaign_status.configure(text="Status: Idle", text_color=C_T3)


# ══════════════════════════════════════════════════════════════════════════════
# CONTACTS VIEW
# ══════════════════════════════════════════════════════════════════════════════
class ContactsView(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=C_APP, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.all_contacts_data: list[dict] = []

        # ── Action bar ────────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        top.grid_columnconfigure(1, weight=1)

        acts = ctk.CTkFrame(top, fg_color="transparent")
        acts.grid(row=0, column=0, sticky="w")

        _btn_primary(acts, "⬆  Import CSV", self.import_csv, width=130).pack(
            side="left", padx=(0, 8))
        _btn_ghost(acts, "↻  Reload", self.load_contacts, width=90).pack(
            side="left", padx=4)
        _btn_danger(acts, "Delete Selected", self.delete_selected, width=130).pack(
            side="left", padx=4)
        _btn_danger(acts, "Clear All", self.clear_contacts,
                    fg_color="#6B1C1C", hover_color="#4A1010",
                    width=90).pack(side="left", padx=4)

        # Stat chips
        chips = ctk.CTkFrame(top, fg_color="transparent")
        chips.grid(row=0, column=1, sticky="e")

        self.lbl_stat_total   = _chip(chips, "Total: 0",      C_T2)
        self.lbl_stat_valid   = _chip(chips, "Valid: 0",      C_GREEN)
        self.lbl_stat_invalid = _chip(chips, "Invalid: 0",    C_RED)
        self.lbl_stat_dup     = _chip(chips, "Duplicates: 0", C_AMBER)

        # ── Search / filter bar ───────────────────────────────────────────────
        fbar = ctk.CTkFrame(self, fg_color="transparent")
        fbar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))
        fbar.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh_table())

        self.search_entry = _entry(fbar,
                                   placeholder="Search contacts by name or email…")
        self.search_entry.configure(textvariable=self.search_var)
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.filter_var = ctk.StringVar(value="All")
        self.filter_menu = ctk.CTkOptionMenu(
            fbar, values=["All", "Valid", "Invalid", "Duplicate"],
            variable=self.filter_var, command=lambda _: self.refresh_table(),
            fg_color=C_CARD2, button_color=C_CARD, button_hover_color=C_ROW,
            text_color=C_T1, font=ctk.CTkFont(size=13),
            corner_radius=8, height=38, width=120,
        )
        self.filter_menu.grid(row=0, column=1)

        self.lbl_selected_count = _lbl(fbar, "0 selected", size=12, color=C_T3)
        self.lbl_selected_count.grid(row=0, column=2, padx=(10, 0))

        # ── Table ─────────────────────────────────────────────────────────────
        tbl = ctk.CTkFrame(self, fg_color="transparent")
        tbl.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        tbl.grid_columnconfigure(0, weight=1)
        tbl.grid_rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(tbl, fg_color=C_CARD2, corner_radius=8,
                           border_width=1, border_color=C_BORDER)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        for txt, w, kw in [
            ("#",       44,  {}),
            ("Name",   200, {"fill": "x", "expand": False}),
            ("Email",  250, {"fill": "x", "expand": True}),
            ("Status",  80, {}),
            ("Actions", 130, {}),
        ]:
            _lbl(hdr, txt, size=12, weight="bold", color=C_T3,
                 width=w, anchor="w").pack(side="left", padx=8, pady=8, **kw)

        self.table_frame = ctk.CTkScrollableFrame(
            tbl, fg_color="transparent",
            scrollbar_button_color=C_CARD2,
            scrollbar_button_hover_color=C_BORDER,
        )
        self.table_frame.grid(row=1, column=0, sticky="nsew")

        self.load_contacts()

    # ── Backend logic (UNCHANGED) ─────────────────────────────────────────────

    def import_csv(self):
        file_path = filedialog.askopenfilename(
            title="Select Contacts CSV", filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                shutil.copy(file_path, CONTACTS_PATH)
                self.load_contacts()
                messagebox.showinfo("Success", "Contacts imported successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import contacts:\n{e}")

    def clear_contacts(self):
        if CONTACTS_PATH.exists():
            if messagebox.askyesno("Confirm",
                                   "Are you sure you want to clear all imported contacts?"):
                try:
                    CONTACTS_PATH.unlink()
                    self.load_contacts()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to clear contacts:\n{e}")

    def update_dashboard(self):
        try:
            self.winfo_toplevel().views["dashboard"].refresh_data()
        except Exception:
            pass

    def load_contacts(self):
        self.all_contacts_data.clear()
        total = valid = invalid = dups = 0

        if CONTACTS_PATH.exists():
            try:
                loader = ContactLoader(CONTACTS_PATH)
                res = loader.load()
                for c in res.valid:
                    self.all_contacts_data.append({
                        "name": str(c.get("name", "")),
                        "email": str(c.get("email", "")),
                        "status": "Valid", "selected": False})
                for c in res.invalid:
                    self.all_contacts_data.append({
                        "name": str(c.get("name", "")),
                        "email": str(c.get("email", "")),
                        "status": "Invalid", "selected": False})
                for c in res.duplicates:
                    self.all_contacts_data.append({
                        "name": str(c.get("name", "")),
                        "email": str(c.get("email", "")),
                        "status": "Duplicate", "selected": False})
                total   = len(self.all_contacts_data)
                valid   = res.total_valid
                invalid = res.total_invalid
                dups    = res.total_duplicates
            except Exception as e:
                messagebox.showerror("Load Error",
                                     f"An error occurred loading contacts:\n{e}")

        self.lbl_stat_total.configure(text=f"Total: {total}")
        self.lbl_stat_valid.configure(text=f"Valid: {valid}")
        self.lbl_stat_invalid.configure(text=f"Invalid: {invalid}")
        self.lbl_stat_dup.configure(text=f"Duplicates: {dups}")
        self.refresh_table()
        self.update_dashboard()

    def save_contacts_to_csv(self):
        rows = [{"name": c["name"], "email": c["email"]}
                for c in self.all_contacts_data]
        pd.DataFrame(rows).to_csv(CONTACTS_PATH, index=False)

    def delete_contact(self, contact):
        if messagebox.askyesno(
                "Confirm Delete",
                f"Delete '{contact['name']}' ({contact['email']})?"):
            self.all_contacts_data.remove(contact)
            self.save_contacts_to_csv()
            self.load_contacts()

    def delete_selected(self):
        selected = [c for c in self.all_contacts_data if c["selected"]]
        if not selected:
            messagebox.showinfo("No Selection",
                                "Tick the checkboxes next to contacts you want to delete.")
            return
        if messagebox.askyesno("Confirm Delete",
                               f"Delete {len(selected)} selected contact(s)?"):
            for c in selected:
                self.all_contacts_data.remove(c)
            self.save_contacts_to_csv()
            self.load_contacts()

    def edit_contact(self, contact):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Contact")
        dialog.geometry("420x210")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.configure(fg_color=C_APP)

        ctk.CTkFrame(dialog, fg_color=C_CARD, corner_radius=0).place(relx=0, rely=0,
                                                                       relwidth=1, relheight=1)
        for r, (lbl_t, attr) in enumerate([("Name", "name"), ("Email", "email")]):
            _lbl(dialog, lbl_t + ":", size=13, color=C_T2).grid(
                row=r, column=0, padx=24, pady=(24 if r == 0 else 10, 0), sticky="w")
            e = _entry(dialog, width=260)
            e.grid(row=r, column=1, padx=12, pady=(24 if r == 0 else 10, 0))
            e.insert(0, contact[attr])
            if attr == "name":
                entry_name = e
            else:
                entry_email = e

        def save():
            nn = entry_name.get().strip()
            ne = entry_email.get().strip()
            if not ne:
                messagebox.showerror("Error", "Email cannot be empty.", parent=dialog)
                return
            contact["name"] = nn
            contact["email"] = ne
            self.save_contacts_to_csv()
            dialog.destroy()
            self.load_contacts()

        _btn_success(dialog, "Save Changes", save, width=160).grid(
            row=2, column=0, columnspan=2, pady=20)

    def refresh_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()

        search = self.search_var.get().lower()
        f_status = self.filter_var.get()

        filtered = [
            c for c in self.all_contacts_data
            if (f_status == "All" or c["status"] == f_status)
            and (not search or search in c["name"].lower()
                 or search in c["email"].lower())
        ]

        if not filtered:
            msg = ("No contacts match your filters."
                   if self.all_contacts_data
                   else "No contacts imported yet.\nClick 'Import CSV' to get started.")
            _lbl(self.table_frame, msg, color=C_T3, size=14).pack(pady=50)
            self.lbl_selected_count.configure(text="0 selected")
            return

        for i, c in enumerate(filtered, 1):
            bg = C_ROW if i % 2 == 0 else C_ROW_A
            rf = ctk.CTkFrame(self.table_frame, fg_color=bg, corner_radius=6)
            rf.pack(fill="x", pady=2)

            chk_var = ctk.BooleanVar(value=c["selected"])

            def on_check(contact=c, var=chk_var):
                contact["selected"] = var.get()
                self._update_selected_count()

            ctk.CTkCheckBox(rf, text=str(i), width=44, variable=chk_var,
                            command=on_check,
                            fg_color=C_ACCENT, hover_color=C_ADARK,
                            checkmark_color="white", border_color=C_BORDER,
                            font=ctk.CTkFont(size=12)).pack(
                side="left", padx=8, pady=8)

            _lbl(rf, c["name"][:30],  size=13, width=200, anchor="w").pack(
                side="left", padx=4)
            _lbl(rf, c["email"][:40], size=13, width=250, anchor="w").pack(
                side="left", padx=4, fill="x", expand=True)

            s_color = (C_GREEN if c["status"] == "Valid"
                       else C_RED if c["status"] == "Invalid" else C_AMBER)
            sf = ctk.CTkFrame(rf, fg_color=C_CARD2, corner_radius=5,
                              border_width=1, border_color=s_color)
            sf.pack(side="left", padx=6, pady=6)
            _lbl(sf, c["status"], size=11, weight="bold", color=s_color).pack(
                padx=8, pady=3)

            _btn_danger(rf, "Del", lambda contact=c: self.delete_contact(contact),
                        width=50, height=30, font=ctk.CTkFont(size=11)).pack(
                side="right", padx=(2, 8), pady=6)
            _btn_ghost(rf, "Edit", lambda contact=c: self.edit_contact(contact),
                       width=52, height=30, font=ctk.CTkFont(size=11)).pack(
                side="right", padx=2)

        self._update_selected_count()

    def _update_selected_count(self):
        count = sum(1 for c in self.all_contacts_data if c["selected"])
        self.lbl_selected_count.configure(text=f"{count} selected")


# ══════════════════════════════════════════════════════════════════════════════
# CAMPAIGN VIEW
# ══════════════════════════════════════════════════════════════════════════════
class CampaignView(ctk.CTkScrollableFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=C_APP, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.template_path = BASE_DIR / "email_template.html"
        self._preview_temp_file = None
        self.preview_box  = None
        self.html_preview = None
        self.is_running   = False

        # ── Campaign config card ───────────────────────────────────────────────
        cfg = _card(self)
        cfg.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        cfg.grid_columnconfigure(1, weight=1)
        _card_title(cfg, "⚙  Campaign Configuration", row=0)

        fields = [
            ("Campaign Name:",  "entry_name",    "Q4 Newsletter"),
            ("Email Subject:",  "entry_subject",  "Hello {name}, check this out!"),
        ]
        for r, (lbl_t, attr, ph) in enumerate(fields):
            _lbl(cfg, lbl_t, size=13, color=C_T2).grid(
                row=r + 1, column=0, sticky="w", padx=16,
                pady=(14 if r == 0 else 8, 0))
            e = _entry(cfg, placeholder=ph)
            e.grid(row=r + 1, column=1, sticky="ew", padx=(8, 16),
                   pady=(14 if r == 0 else 8, 0))
            setattr(self, attr, e)
        self.entry_subject.insert(0, settings.default_subject)

        _lbl(cfg, "Template:", size=13, color=C_T2).grid(
            row=3, column=0, sticky="w", padx=16, pady=8)
        tpl_row = ctk.CTkFrame(cfg, fg_color="transparent")
        tpl_row.grid(row=3, column=1, sticky="ew", padx=(8, 16), pady=8)
        _btn_ghost(tpl_row, "Select HTML", self.pick_template, width=110).pack(
            side="left")
        self.lbl_template = _lbl(tpl_row, self.template_path.name,
                                  size=12, color=C_T2)
        self.lbl_template.pack(side="left", padx=12)
        ctk.CTkFrame(cfg, fg_color="transparent", height=8).grid(row=4, column=0)

        # ── Preview card ──────────────────────────────────────────────────────
        prev = _card(self)
        prev.grid(row=1, column=0, sticky="ew", padx=20, pady=8)
        prev.grid_columnconfigure(0, weight=1)

        ph = ctk.CTkFrame(prev, fg_color="transparent")
        ph.pack(fill="x", padx=16, pady=(14, 0))
        _lbl(ph, "📧  Live Preview (First Contact)", size=13,
             weight="bold", color=C_T2).pack(side="left")
        _btn_ghost(ph, "↻  Refresh Preview", self.refresh_preview,
                   width=140, height=32).pack(side="right")

        ctk.CTkFrame(prev, height=1, fg_color=C_BORDER).pack(
            fill="x", padx=16, pady=(8, 0))

        pinner = ctk.CTkFrame(prev, fg_color="transparent")
        pinner.pack(fill="both", expand=True, padx=16, pady=16)

        _lbl(pinner, "◉", size=40, color=C_ACCENT).pack(pady=(10, 6))
        self.lbl_preview_status = _lbl(
            pinner,
            'Click "Refresh Preview" to render the email design',
            size=13, color=C_T3)
        self.lbl_preview_status.pack(pady=4)
        self.lbl_preview_contact = _lbl(pinner, "", size=12, color=C_ACCENT)
        self.lbl_preview_contact.pack()

        ctk.CTkButton(
            pinner,
            text="🌐  Open Preview in Browser",
            command=self.refresh_preview,
            fg_color=C_ACCENT, hover_color=C_ADARK,
            text_color="white", corner_radius=20,
            height=38, font=ctk.CTkFont(size=13, weight="bold"),
            width=230,
        ).pack(pady=16)

        _lbl(pinner,
             "Opens in your default browser — identical to what recipients see.",
             size=11, color=C_T3).pack(pady=(0, 10))

        # ── Actions row ───────────────────────────────────────────────────────
        arow = ctk.CTkFrame(self, fg_color="transparent")
        arow.grid(row=2, column=0, sticky="ew", padx=20, pady=8)
        arow.grid_columnconfigure(1, weight=1)

        self.btn_test = _btn_ghost(arow, "✉  Send Test Email",
                                   self.send_test, width=155)
        self.btn_test.grid(row=0, column=0, sticky="w")

        self.lbl_recipients = _lbl(arow, "Recipients ready: 0",
                                   size=13, color=C_AMBER)
        self.lbl_recipients.grid(row=0, column=1, padx=20)

        self.btn_start = ctk.CTkButton(
            arow, text="▶  Start Campaign",
            command=self.start_campaign,
            fg_color=C_GREEN, hover_color=C_GDARK,
            text_color="white", corner_radius=8,
            height=38, font=ctk.CTkFont(size=14, weight="bold"),
            width=170,
        )
        self.btn_start.grid(row=0, column=2, sticky="e")

        # ── Progress / log card ───────────────────────────────────────────────
        log_card = _card(self)
        log_card.grid(row=3, column=0, sticky="ew", padx=20, pady=(8, 20))
        log_card.grid_columnconfigure(0, weight=1)
        _card_title(log_card, "📡  Sending Progress")

        prow = ctk.CTkFrame(log_card, fg_color="transparent")
        prow.pack(fill="x", padx=16, pady=(10, 4))
        prow.grid_columnconfigure(0, weight=1)
        self.lbl_progress = _lbl(prow, "Idle", size=13, weight="bold")
        self.lbl_progress.grid(row=0, column=0, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(
            log_card, progress_color=C_ACCENT, fg_color=C_CARD2)
        self.progress_bar.pack(fill="x", padx=16, pady=(0, 8))
        self.progress_bar.set(0)

        self.log_box = ctk.CTkTextbox(
            log_card, height=130, state="disabled",
            fg_color=C_CARD2, text_color=C_T2,
            border_width=1, border_color=C_BORDER,
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=8,
        )
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.update_recipient_count()
        self.refresh_preview()

    # ── Backend logic (UNCHANGED) ─────────────────────────────────────────────

    def update_recipient_count(self):
        try:
            views = self.winfo_toplevel().views
            if "contacts" in views:
                sel = [c for c in views["contacts"].all_contacts_data
                       if c.get("selected")]
                if sel:
                    self.lbl_recipients.configure(
                        text=f"Recipients ready: {len(sel)} (Selected)")
                    return
        except Exception:
            pass
        try:
            loader = ContactLoader(CONTACTS_PATH)
            res = loader.load()
            self.lbl_recipients.configure(
                text=f"Recipients ready: {res.total_valid} (All Valid)")
        except Exception:
            self.lbl_recipients.configure(text="Recipients ready: 0")

    def pick_template(self):
        path = filedialog.askopenfilename(
            title="Select HTML Template", filetypes=[("HTML Files", "*.html")])
        if path:
            self.template_path = Path(path)
            self.lbl_template.configure(text=self.template_path.name)
            self.refresh_preview()

    def refresh_preview(self):
        contact = {"name": "Jane Doe", "email": "jane@example.com"}
        try:
            loader = ContactLoader(CONTACTS_PATH)
            res = loader.load()
            if res.valid:
                contact = res.valid[0]
        except Exception:
            pass

        try:
            if not self.template_path.exists():
                messagebox.showerror("Preview Error",
                                     f"Template not found:\n{self.template_path}")
                return
            html = render_template(self.template_path, contact)
        except Exception as e:
            messagebox.showerror("Preview Error",
                                 f"Failed to render template:\n{e}")
            return

        try:
            if (self._preview_temp_file is None
                    or not os.path.exists(self._preview_temp_file)):
                fd, self._preview_temp_file = tempfile.mkstemp(
                    suffix=".html", prefix="campaign_preview_")
                os.close(fd)
            with open(self._preview_temp_file, "w", encoding="utf-8") as f:
                f.write(html)
            webbrowser.open(
                f"file:///{self._preview_temp_file.replace(os.sep, '/')}")
            name  = contact.get("name", "Sample Contact")
            email = contact.get("email", "")
            self.lbl_preview_status.configure(
                text="✅  Preview opened in your browser!", text_color=C_GREEN)
            self.lbl_preview_contact.configure(
                text=f"Rendered for: {name} <{email}>")
        except Exception as e:
            messagebox.showerror("Preview Error",
                                 f"Could not open preview:\n{e}")

    def log_msg(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def send_test(self):
        if self.is_running:
            return
        dialog = ctk.CTkInputDialog(text="Enter test email address:", title="Test Email")
        test_email = dialog.get_input()
        if not test_email:
            return
        subject = self.entry_subject.get() or "Test Subject"
        try:
            html = render_template(self.template_path,
                                   {"name": "Test User", "email": test_email})
            self.log_msg(f"Sending test email to {test_email}…")

            def send_t():
                try:
                    with EmailSender() as sender:
                        sender.send_email(test_email, "Test User", subject, html)
                    self.after(0, lambda: messagebox.showinfo(
                        "Success", "Test email sent successfully!"))
                    self.after(0, lambda: self.log_msg("✅ Test email sent!"))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror(
                        "Error", f"Failed to send test email:\n{e}"))
                    self.after(0, lambda: self.log_msg(f"❌ Test failed: {e}"))

            threading.Thread(target=send_t, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def start_campaign(self):
        if self.is_running:
            return
        if not CONTACTS_PATH.exists():
            messagebox.showerror("Error",
                                 "No contacts loaded. Go to the Contacts tab first.")
            return
        if not self.template_path.exists():
            messagebox.showerror("Error", "Template file not found.")
            return
        if not messagebox.askyesno("Start Campaign",
                                   "Are you sure you want to start sending emails now?"):
            return

        self.is_running = True
        self.btn_start.configure(state="disabled")
        self.btn_test.configure(state="disabled")
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

        subject = self.entry_subject.get()

        def progress_cb(index, total, name, status):
            pct = index / total
            msg = f"[{index}/{total}] {name} → {status}"
            self.after(0, lambda: self.progress_bar.set(pct))
            self.after(0, lambda: self.lbl_progress.configure(
                text=f"Sending {int(pct * 100)}% ({index}/{total})"))
            self.after(0, lambda: self.log_msg(msg))

        def run_camp():
            try:
                self.after(0, lambda: self.log_msg("🚀 Starting campaign engine…"))
                send_campaign(CONTACTS_PATH, self.template_path,
                              subject=subject, progress_callback=progress_cb)
                self.after(0, lambda: messagebox.showinfo("Done", "Campaign finished!"))
                self.after(0, lambda: self.lbl_progress.configure(text="✅ Finished"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(
                    "Error", f"Campaign crashed:\n{e}"))
                self.after(0, lambda: self.lbl_progress.configure(text="❌ Error"))
            finally:
                self.after(0, self.finish_campaign)

        threading.Thread(target=run_camp, daemon=True).start()

    def finish_campaign(self):
        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_test.configure(state="normal")
        try:
            self.winfo_toplevel().views["dashboard"].refresh_data()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# SCHEDULER VIEW
# ══════════════════════════════════════════════════════════════════════════════
class SchedulerView(ctk.CTkScrollableFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=C_APP, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        _start_scheduler_thread()

        # ── Config card ───────────────────────────────────────────────────────
        cfg = _card(self)
        cfg.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        cfg.grid_columnconfigure(1, weight=1)
        _card_title(cfg, "⏰  Schedule a Campaign", row=0)

        _lbl(cfg, "Campaign Subject:", size=13, color=C_T2).grid(
            row=1, column=0, sticky="w", padx=16, pady=(14, 8))
        self.entry_subject = _entry(cfg, placeholder="Subject line…")
        self.entry_subject.grid(row=1, column=1, sticky="ew",
                                padx=(8, 16), pady=(14, 8))
        self.entry_subject.insert(0, settings.default_subject)

        _lbl(cfg, "Frequency:", size=13, color=C_T2).grid(
            row=2, column=0, sticky="w", padx=16, pady=8)
        self.freq_var = ctk.StringVar(value="Daily")
        self.freq_menu = ctk.CTkOptionMenu(
            cfg, values=["Daily", "Every N Hours"],
            variable=self.freq_var, command=self._on_freq_change,
            fg_color=C_CARD2, button_color=C_CARD,
            button_hover_color=C_ROW, text_color=C_T1,
            font=ctk.CTkFont(size=13), corner_radius=8,
            height=38, width=180,
        )
        self.freq_menu.grid(row=2, column=1, sticky="w",
                            padx=(8, 16), pady=8)

        self.lbl_time_val = _lbl(cfg, "Time (HH:MM):", size=13, color=C_T2)
        self.lbl_time_val.grid(row=3, column=0, sticky="w", padx=16, pady=(8, 18))
        self.entry_time_val = _entry(cfg, placeholder="08:00", width=120)
        self.entry_time_val.grid(row=3, column=1, sticky="w",
                                 padx=(8, 16), pady=(8, 18))
        self.entry_time_val.insert(0, "08:00")

        # ── Action row ────────────────────────────────────────────────────────
        arow = ctk.CTkFrame(self, fg_color="transparent")
        arow.grid(row=1, column=0, sticky="ew", padx=20, pady=8)
        _btn_success(arow, "📅  Schedule Campaign",
                     self.schedule_job, width=180).pack(side="left")
        _btn_ghost(arow, "↻  Refresh Table",
                   self.refresh_table, width=130).pack(side="right")

        # ── Jobs card ─────────────────────────────────────────────────────────
        jobs_card = _card(self)
        jobs_card.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        jobs_card.grid_columnconfigure(0, weight=1)
        _card_title(jobs_card, "📋  Scheduled Campaigns")

        # Table header
        hdr = ctk.CTkFrame(jobs_card, fg_color=C_CARD2, corner_radius=6)
        hdr.pack(fill="x", padx=16, pady=(10, 4))
        for txt, w in [("Frequency", 180), ("Next Run", 200), ("", 0)]:
            kw = dict(fill="x", expand=True) if not w else {}
            _lbl(hdr, txt, size=12, weight="bold", color=C_T3,
                 width=w, anchor="w").pack(
                side="left", padx=10, pady=8, **kw)

        self.table_frame = ctk.CTkScrollableFrame(
            jobs_card, fg_color="transparent", height=220,
            scrollbar_button_color=C_CARD2,
        )
        self.table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.refresh_table()

    # ── Backend logic (UNCHANGED) ─────────────────────────────────────────────

    def _on_freq_change(self, choice):
        if choice == "Daily":
            self.lbl_time_val.configure(text="Time (HH:MM):")
            self.entry_time_val.delete(0, "end")
            self.entry_time_val.insert(0, "08:00")
        else:
            self.lbl_time_val.configure(text="Hours (e.g. 6):")
            self.entry_time_val.delete(0, "end")
            self.entry_time_val.insert(0, "6")

    def schedule_job(self):
        if not CONTACTS_PATH.exists():
            messagebox.showerror("Error",
                                 "No contacts loaded. Go to the Contacts tab first.")
            return
        subject = self.entry_subject.get()
        freq    = self.freq_var.get()
        val     = self.entry_time_val.get()
        try:
            if freq == "Daily":
                import re
                if not re.match(r"^([01][0-9]|2[0-3]):([0-5][0-9])$", val):
                    raise ValueError("Time must be in HH:MM format.")
                run_daily(at_time=val, subject=subject)
            else:
                hours = int(val)
                if hours <= 0:
                    raise ValueError("Hours must be positive.")
                run_every_hours(hours=hours, subject=subject)
            messagebox.showinfo("Success", "Campaign scheduled successfully!")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to schedule:\n{e}")

    def cancel_job_ui(self, job):
        try:
            schedule.cancel_job(job)
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to cancel job:\n{e}")

    def refresh_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()

        jobs = schedule.get_jobs()
        if not jobs:
            _lbl(self.table_frame,
                 "No campaigns scheduled yet.", color=C_T3, size=13).pack(pady=30)
            return

        for i, job in enumerate(jobs):
            if hasattr(job, "at_time") and job.at_time:
                freq_str = f"Daily at {job.at_time}"
            elif job.interval > 1:
                freq_str = f"Every {job.interval} {job.unit}"
            else:
                freq_str = f"Every {job.unit[:-1]}"

            next_run = (job.next_run.strftime("%Y-%m-%d  %H:%M:%S")
                        if job.next_run else "Unknown")

            bg = C_ROW if i % 2 == 0 else C_ROW_A
            rf = ctk.CTkFrame(self.table_frame, fg_color=bg, corner_radius=6)
            rf.pack(fill="x", pady=2)

            _lbl(rf, freq_str,  size=13, width=180, anchor="w").pack(
                side="left", padx=10, pady=8)
            _lbl(rf, next_run, size=12, color=C_T2, width=200, anchor="w").pack(
                side="left", padx=10)
            _btn_danger(rf, "Cancel", lambda j=job: self.cancel_job_ui(j),
                        width=80, height=28, font=ctk.CTkFont(size=11)).pack(
                side="right", padx=10, pady=8)


# ══════════════════════════════════════════════════════════════════════════════
# LOGS VIEW
# ══════════════════════════════════════════════════════════════════════════════
class LogsView(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=C_APP, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.all_logs_data: list[dict] = []

        # ── Top bar ───────────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        top.grid_columnconfigure(1, weight=1)

        acts = ctk.CTkFrame(top, fg_color="transparent")
        acts.grid(row=0, column=0, sticky="w")
        _btn_primary(acts, "↻  Refresh Logs", self.load_logs, width=130).pack(
            side="left")

        chips = ctk.CTkFrame(top, fg_color="transparent")
        chips.grid(row=0, column=1, sticky="e")
        self.lbl_stat_total   = _chip(chips, "Total: 0",   C_T2)
        self.lbl_stat_sent    = _chip(chips, "Sent: 0",    C_GREEN)
        self.lbl_stat_failed  = _chip(chips, "Failed: 0",  C_RED)
        self.lbl_stat_skipped = _chip(chips, "Skipped: 0", C_AMBER)

        # ── Search / filter bar ───────────────────────────────────────────────
        fbar = ctk.CTkFrame(self, fg_color="transparent")
        fbar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))
        fbar.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh_table())
        se = _entry(fbar, placeholder="Search by name, email or subject…")
        se.configure(textvariable=self.search_var)
        se.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.filter_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            fbar, values=["All", "Sent", "Failed", "Skipped"],
            variable=self.filter_var, command=lambda _: self.refresh_table(),
            fg_color=C_CARD2, button_color=C_CARD,
            button_hover_color=C_ROW, text_color=C_T1,
            font=ctk.CTkFont(size=13), corner_radius=8,
            height=38, width=120,
        ).grid(row=0, column=1)

        # ── Table ─────────────────────────────────────────────────────────────
        tbl = ctk.CTkFrame(self, fg_color="transparent")
        tbl.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        tbl.grid_columnconfigure(0, weight=1)
        tbl.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(tbl, fg_color=C_CARD2, corner_radius=8,
                           border_width=1, border_color=C_BORDER)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        for txt, w, expand in [
            ("Timestamp",  155, False),
            ("Recipient",  200, False),
            ("Subject",      0, True),
            ("Status",      80, False),
            ("Error",      160, False),
        ]:
            kw = dict(fill="x", expand=True) if expand else {}
            _lbl(hdr, txt, size=12, weight="bold", color=C_T3,
                 width=w, anchor="w").pack(side="left", padx=8, pady=8, **kw)

        self.table_frame = ctk.CTkScrollableFrame(
            tbl, fg_color="transparent",
            scrollbar_button_color=C_CARD2,
        )
        self.table_frame.grid(row=1, column=0, sticky="nsew")

        self.load_logs()

    # ── Backend logic (UNCHANGED) ─────────────────────────────────────────────

    def load_logs(self):
        self.all_logs_data.clear()
        total = sent = failed = skipped = 0

        if LOGS_PATH.exists():
            try:
                df = pd.read_csv(LOGS_PATH)
                df = df.fillna("")
                df = df.iloc[::-1]
                for _, row in df.iterrows():
                    rec = {k: str(row.get(k, "")) for k in
                           ["timestamp", "email", "name", "subject", "status", "error"]}
                    self.all_logs_data.append(rec)
                    st = rec["status"].lower()
                    if   st == "sent":    sent    += 1
                    elif st == "failed":  failed  += 1
                    elif st == "skipped": skipped += 1
                total = len(self.all_logs_data)
            except pd.errors.EmptyDataError:
                pass
            except Exception as e:
                messagebox.showerror("Load Error",
                                     f"An error occurred loading logs:\n{e}")

        self.lbl_stat_total.configure(text=f"Total: {total}")
        self.lbl_stat_sent.configure(text=f"Sent: {sent}")
        self.lbl_stat_failed.configure(text=f"Failed: {failed}")
        self.lbl_stat_skipped.configure(text=f"Skipped: {skipped}")
        self.refresh_table()

    def refresh_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()

        search     = self.search_var.get().lower()
        f_status   = self.filter_var.get()

        filtered = [
            r for r in self.all_logs_data
            if (f_status == "All" or r["status"] == f_status)
            and (not search or any(search in r[k].lower()
                                   for k in ["name", "email", "subject"]))
        ]

        if not filtered:
            _lbl(self.table_frame,
                 "No logs match your filters." if self.all_logs_data
                 else "No campaign logs found.", color=C_T3, size=14).pack(pady=50)
            return

        max_render = 200
        for i, r in enumerate(filtered):
            if i >= max_render:
                _lbl(self.table_frame,
                     f"… and {len(filtered) - max_render} more rows "
                     f"hidden to maintain performance.",
                     color=C_T3, size=12).pack(pady=8)
                break

            bg = C_ROW if i % 2 == 0 else C_ROW_A
            rf = ctk.CTkFrame(self.table_frame, fg_color=bg, corner_radius=6)
            rf.pack(fill="x", pady=2)

            recipient = (f"{r['name'][:14]} <{r['email'][:18]}>"
                         if r["name"] else r["email"][:35])
            status    = r["status"]
            s_color   = (C_GREEN  if status == "Sent"
                         else C_RED if status == "Failed" else C_AMBER)
            err = r["error"][:28] + "…" if len(r["error"]) > 28 else r["error"]

            _lbl(rf, r["timestamp"][:19], size=12,
                 width=155, anchor="w").pack(side="left", padx=8, pady=7)
            _lbl(rf, recipient, size=12,
                 width=200, anchor="w").pack(side="left", padx=4)
            _lbl(rf, r["subject"][:42], size=12,
                 anchor="w").pack(side="left", padx=4, fill="x", expand=True)

            sf = ctk.CTkFrame(rf, fg_color=C_CARD2, corner_radius=5,
                              border_width=1, border_color=s_color)
            sf.pack(side="left", padx=6, pady=6)
            _lbl(sf, status, size=11, weight="bold",
                 color=s_color).pack(padx=8, pady=3)

            _lbl(rf, err, size=11, color=C_T3,
                 width=160, anchor="w").pack(side="right", padx=8)


# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS VIEW
# ══════════════════════════════════════════════════════════════════════════════
class SettingsView(ctk.CTkScrollableFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=C_APP, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        # ── Auth card ─────────────────────────────────────────────────────────
        auth = _card(self)
        auth.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        auth.grid_columnconfigure(1, weight=1)
        _card_title(auth, "🔐  Authentication", row=0)

        rows = [
            ("Gmail Account:",    settings.email_address or "Not Configured",  C_T1),
            ("App Password:",     "••••••••••••••••" if settings.email_password
                                  else "Not Configured",                        C_T2),
        ]
        for r, (lbl_t, val, col) in enumerate(rows):
            _lbl(auth, lbl_t, size=13, color=C_T3).grid(
                row=r + 1, column=0, sticky="w", padx=16,
                pady=(14 if r == 0 else 8, 0))
            _lbl(auth, val, size=13, color=col).grid(
                row=r + 1, column=1, sticky="w", padx=12,
                pady=(14 if r == 0 else 8, 0))

        _lbl(auth, "Status:", size=13, color=C_T3).grid(
            row=3, column=0, sticky="w", padx=16, pady=(8, 16))
        if settings.email_address and settings.email_password:
            sf = ctk.CTkFrame(auth, fg_color=C_CARD2, corner_radius=6,
                              border_width=1, border_color=C_GREEN)
            sf.grid(row=3, column=1, sticky="w", padx=12, pady=(8, 16))
            _lbl(sf, "✓  Configured", size=12, weight="bold",
                 color=C_GREEN).pack(padx=10, pady=4)
        else:
            sf = ctk.CTkFrame(auth, fg_color=C_CARD2, corner_radius=6,
                              border_width=1, border_color=C_RED)
            sf.grid(row=3, column=1, sticky="w", padx=12, pady=(8, 16))
            _lbl(sf, "✗  Missing Credentials", size=12, weight="bold",
                 color=C_RED).pack(padx=10, pady=4)

        # ── SMTP card ─────────────────────────────────────────────────────────
        smtp = _card(self)
        smtp.grid(row=1, column=0, sticky="ew", padx=20, pady=8)
        smtp.grid_columnconfigure(1, weight=1)
        _card_title(smtp, "📡  SMTP Configuration", row=0)

        for r, (lbl_t, val) in enumerate([
            ("SMTP Server:", settings.smtp_host),
            ("SMTP Port:",   str(settings.smtp_port)),
        ]):
            _lbl(smtp, lbl_t, size=13, color=C_T3).grid(
                row=r + 1, column=0, sticky="w", padx=16,
                pady=(14 if r == 0 else 8, 0))
            _lbl(smtp, val, size=13).grid(
                row=r + 1, column=1, sticky="w", padx=12,
                pady=(14 if r == 0 else 8, 0))

        self.btn_test_smtp = _btn_ghost(
            smtp, "⚡  Test SMTP Connection", self.test_smtp, width=195)
        self.btn_test_smtp.grid(row=3, column=0, sticky="w",
                                padx=16, pady=(14, 16), columnspan=2)

        # ── App settings card ─────────────────────────────────────────────────
        app = _card(self)
        app.grid(row=2, column=0, sticky="ew", padx=20, pady=8)
        app.grid_columnconfigure(1, weight=1)
        _card_title(app, "⚙  Application Settings", row=0)

        _lbl(app, "Max Emails / Hour:", size=13, color=C_T3).grid(
            row=1, column=0, sticky="w", padx=16, pady=(14, 8))
        self.entry_max_emails = _entry(app, width=100)
        self.entry_max_emails.grid(row=1, column=1, sticky="w",
                                   padx=12, pady=(14, 8))
        self.entry_max_emails.insert(0, str(settings.max_emails_per_hour))

        for r, (lbl_t, val) in enumerate([
            ("Contacts File:", CONTACTS_FILE),
            ("Template File:", TEMPLATE_FILE),
            ("Log File:",      LOG_FILE),
        ], start=2):
            _lbl(app, lbl_t, size=13, color=C_T3).grid(
                row=r, column=0, sticky="w", padx=16, pady=6)
            _lbl(app, val, size=13, color=C_T2).grid(
                row=r, column=1, sticky="w", padx=12, pady=6)
        ctk.CTkFrame(app, height=8, fg_color="transparent").grid(row=5, column=0)

        # ── Action row ────────────────────────────────────────────────────────
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.grid(row=3, column=0, sticky="ew", padx=20, pady=(8, 24))
        _btn_success(bot, "💾  Save Settings", self.save_settings, width=160).pack(
            side="right")

    # ── Backend logic (UNCHANGED) ─────────────────────────────────────────────

    def test_smtp(self):
        self.btn_test_smtp.configure(state="disabled", text="Testing…")

        def run_test():
            try:
                with EmailSender() as _:
                    pass
                self.after(0, lambda: messagebox.showinfo(
                    "Success", "SMTP connection authenticated successfully!"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(
                    "Error", f"SMTP Connection Failed:\n{e}"))
            finally:
                self.after(0, lambda: self.btn_test_smtp.configure(
                    state="normal", text="⚡  Test SMTP Connection"))

        threading.Thread(target=run_test, daemon=True).start()

    def save_settings(self):
        new_limit = self.entry_max_emails.get()
        if not new_limit.isdigit() or int(new_limit) <= 0:
            messagebox.showerror("Error",
                                 "Max Emails Per Hour must be a positive integer.")
            return
        try:
            env_path = BASE_DIR / ".env"
            if not env_path.exists():
                env_path.touch()
            dotenv.set_key(env_path, "MAX_EMAILS_PER_HOUR", new_limit)
            messagebox.showinfo("Saved",
                                "Settings saved!\nMax Emails Per Hour updated.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")
