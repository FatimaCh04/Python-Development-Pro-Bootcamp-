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

from config import settings, CONTACTS_FILE, TEMPLATE_FILE, LOG_FILE, MAX_EMAILS_PER_HOUR
from email_sender import EmailSender, send_campaign
from utils import ContactLoader, render_template
from scheduler import run_daily, run_every_hours, run_scheduler

# Optional HTML renderer
try:
    from tkinterweb import HtmlFrame
    _TKINTERWEB_AVAILABLE = True
except ImportError:
    _TKINTERWEB_AVAILABLE = False

# Global tracker for the background scheduler loop thread
_scheduler_thread = None

def _start_scheduler_thread():
    global _scheduler_thread
    if _scheduler_thread is None or not _scheduler_thread.is_alive():
        _scheduler_thread = threading.Thread(target=lambda: run_scheduler(poll_interval=10), daemon=True)
        _scheduler_thread.start()

# Setup paths (gui is inside the main directory, so parent is BASE_DIR)
BASE_DIR = Path(__file__).parent.parent
CONTACTS_PATH = BASE_DIR / CONTACTS_FILE
LOGS_PATH = BASE_DIR / LOG_FILE

class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        
        # --- Top Section: Header & Refresh ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        self.title_lbl = ctk.CTkLabel(self.header_frame, text="Campaign Overview", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_lbl.grid(row=0, column=0, sticky="w")
        
        self.refresh_btn = ctk.CTkButton(self.header_frame, text="Refresh Data", width=120, command=self.refresh_data)
        self.refresh_btn.grid(row=0, column=1, sticky="e")
        
        # --- Metrics Cards ---
        self.metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.metrics_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        self.metrics_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Contacts Card
        self.card_contacts = self._create_card(self.metrics_frame, "Contacts", 0, 0)
        self.lbl_total_contacts = ctk.CTkLabel(self.card_contacts, text="Total: 0")
        self.lbl_total_contacts.pack(anchor="w", padx=15, pady=(5,0))
        self.lbl_valid_contacts = ctk.CTkLabel(self.card_contacts, text="Valid: 0", text_color="green")
        self.lbl_valid_contacts.pack(anchor="w", padx=15)
        self.lbl_invalid_contacts = ctk.CTkLabel(self.card_contacts, text="Invalid: 0", text_color="red")
        self.lbl_invalid_contacts.pack(anchor="w", padx=15, pady=(0,10))
        
        # Emails Card
        self.card_emails = self._create_card(self.metrics_frame, "Emails Sent", 0, 1)
        self.lbl_sent_emails = ctk.CTkLabel(self.card_emails, text="Sent: 0", text_color="green")
        self.lbl_sent_emails.pack(anchor="w", padx=15, pady=(5,0))
        self.lbl_failed_emails = ctk.CTkLabel(self.card_emails, text="Failed: 0", text_color="red")
        self.lbl_failed_emails.pack(anchor="w", padx=15)
        self.lbl_remaining_emails = ctk.CTkLabel(self.card_emails, text="Remaining: 0")
        self.lbl_remaining_emails.pack(anchor="w", padx=15, pady=(0,10))
        
        # Rate Limit Card
        self.card_rate = self._create_card(self.metrics_frame, "Rate Limit", 0, 2)
        self.lbl_hourly_limit = ctk.CTkLabel(self.card_rate, text=f"Hourly Limit: {MAX_EMAILS_PER_HOUR}")
        self.lbl_hourly_limit.pack(anchor="w", padx=15, pady=(5,0))
        self.lbl_sent_this_hour = ctk.CTkLabel(self.card_rate, text="Sent This Hour: 0")
        self.lbl_sent_this_hour.pack(anchor="w", padx=15)
        self.lbl_rate_warning = ctk.CTkLabel(self.card_rate, text="", text_color="orange", font=ctk.CTkFont(weight="bold"))
        self.lbl_rate_warning.pack(anchor="w", padx=15, pady=(0,10))
        
        # --- Campaign Status ---
        self.status_frame = self._create_card(self, "Campaign Status", 2, 0, sticky="ew", padx=20, pady=10)
        self.lbl_campaign_status = ctk.CTkLabel(self.status_frame, text="Current Status: Idle", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_campaign_status.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(self.status_frame)
        self.progress_bar.pack(fill="x", padx=15, pady=5)
        self.progress_bar.set(0)
        
        self.lbl_progress_text = ctk.CTkLabel(self.status_frame, text="0%")
        self.lbl_progress_text.pack(anchor="e", padx=15, pady=(0, 10))
        
        # --- Bottom Split (Activity & Quick Actions) ---
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        self.bottom_frame.grid_columnconfigure(0, weight=3)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        
        # Recent Activity
        self.activity_card = self._create_card(self.bottom_frame, "Recent Campaign Activity", 0, 0, sticky="nsew", padx=(0,10))
        self.activity_list_frame = ctk.CTkFrame(self.activity_card, fg_color="transparent")
        self.activity_list_frame.pack(fill="both", expand=True, padx=15, pady=(0,15))
        
        # Quick Actions
        self.actions_card = self._create_card(self.bottom_frame, "Quick Actions", 0, 1, sticky="nsew")
        
        btn_contacts = ctk.CTkButton(self.actions_card, text="Import Contacts", command=lambda: self.winfo_toplevel().select_view("contacts"))
        btn_contacts.pack(fill="x", padx=15, pady=(5,10))
        
        btn_create = ctk.CTkButton(self.actions_card, text="Create Campaign", command=lambda: self.winfo_toplevel().select_view("campaign"))
        btn_create.pack(fill="x", padx=15, pady=10)
        
        btn_schedule = ctk.CTkButton(self.actions_card, text="Schedule Campaign", command=lambda: self.winfo_toplevel().select_view("scheduler"))
        btn_schedule.pack(fill="x", padx=15, pady=10)
        
        btn_logs = ctk.CTkButton(self.actions_card, text="View Logs", command=lambda: self.winfo_toplevel().select_view("logs"))
        btn_logs.pack(fill="x", padx=15, pady=(10,15))
        
        # Load initial data
        self.refresh_data()
        
    def _create_card(self, parent, title, row, col, sticky="nsew", padx=5, pady=5):
        card = ctk.CTkFrame(parent, corner_radius=8)
        card.grid(row=row, column=col, sticky=sticky, padx=padx, pady=pady)
        title_lbl = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        title_lbl.pack(anchor="w", padx=15, pady=(15, 5))
        return card

    def refresh_data(self):
        # 1. Contacts Data
        total_contacts = 0
        valid_contacts = 0
        invalid_contacts = 0
        
        if CONTACTS_PATH.exists():
            try:
                loader = ContactLoader(CONTACTS_PATH)
                res = loader.load()
                total_contacts = res.total_raw
                valid_contacts = res.total_valid
                invalid_contacts = res.total_invalid
            except Exception:
                pass
                
        self.lbl_total_contacts.configure(text=f"Total: {total_contacts}")
        self.lbl_valid_contacts.configure(text=f"Valid: {valid_contacts}")
        self.lbl_invalid_contacts.configure(text=f"Invalid: {invalid_contacts}")
        
        # 2. Logs Data
        total_sent = 0
        total_failed = 0
        sent_this_hour = 0
        
        # Clear recent activity
        for widget in self.activity_list_frame.winfo_children():
            widget.destroy()
            
        if LOGS_PATH.exists():
            try:
                df = pd.read_csv(LOGS_PATH)
                # Ensure column exists
                if "status" in df.columns:
                    total_sent = len(df[df["status"] == "Sent"])
                    total_failed = len(df[df["status"] == "Failed"])
                
                if "timestamp" in df.columns:
                    # Convert to datetime and calculate sent this hour
                    df["timestamp_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
                    one_hour_ago = datetime.now() - timedelta(hours=1)
                    
                    # Filter for last hour and sent status
                    recent_df = df[(df["timestamp_dt"] >= one_hour_ago) & (df["status"] == "Sent")]
                    sent_this_hour = len(recent_df)
                    
                # Recent activity
                recent_activity = df.tail(10).iloc[::-1]  # Get last 10, reversed
                
                if recent_activity.empty:
                    ctk.CTkLabel(self.activity_list_frame, text="No campaign activity yet.").pack(anchor="w")
                else:
                    # Table headers
                    header_frame = ctk.CTkFrame(self.activity_list_frame, fg_color="transparent")
                    header_frame.pack(fill="x", pady=(0, 5))
                    ctk.CTkLabel(header_frame, text="Time", width=150, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
                    ctk.CTkLabel(header_frame, text="Recipient", width=150, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
                    ctk.CTkLabel(header_frame, text="Subject", width=200, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5, fill="x", expand=True)
                    ctk.CTkLabel(header_frame, text="Status", width=80, font=ctk.CTkFont(weight="bold")).pack(side="right", padx=5)

                    for _, row in recent_activity.iterrows():
                        frame = ctk.CTkFrame(self.activity_list_frame, fg_color="transparent")
                        frame.pack(fill="x", pady=2)
                        
                        time_str = str(row.get("timestamp", ""))[:19]
                        name = str(row.get("name", row.get("email", "")))
                        subj = str(row.get("subject", ""))
                        status = str(row.get("status", ""))
                        
                        color = "green" if status == "Sent" else ("red" if status == "Failed" else "gray")
                        
                        ctk.CTkLabel(frame, text=time_str, width=150, anchor="w").pack(side="left", padx=5)
                        ctk.CTkLabel(frame, text=name[:20], width=150, anchor="w").pack(side="left", padx=5)
                        ctk.CTkLabel(frame, text=subj[:30], width=200, anchor="w").pack(side="left", padx=5, fill="x", expand=True)
                        ctk.CTkLabel(frame, text=status, width=80, text_color=color).pack(side="right", padx=5)
                        
            except Exception as e:
                ctk.CTkLabel(self.activity_list_frame, text=f"Could not load logs: {e}").pack(anchor="w")
        else:
            ctk.CTkLabel(self.activity_list_frame, text="No campaign activity yet (log file missing).").pack(anchor="w")

        # 3. Update Labels
        self.lbl_sent_emails.configure(text=f"Sent: {total_sent}")
        self.lbl_failed_emails.configure(text=f"Failed: {total_failed}")
        
        remaining_emails = max(0, valid_contacts - total_sent)
        self.lbl_remaining_emails.configure(text=f"Remaining: {remaining_emails}")
        
        self.lbl_sent_this_hour.configure(text=f"Sent This Hour: {sent_this_hour}")
        remaining_hourly = max(0, MAX_EMAILS_PER_HOUR - sent_this_hour)
        
        if remaining_hourly == 0:
            self.lbl_rate_warning.configure(text="Hourly sending limit reached")
        else:
            self.lbl_rate_warning.configure(text=f"Remaining (Hour): {remaining_hourly}")
            
        # 4. Progress Bar
        progress_val = 0.0
        if valid_contacts > 0:
            progress_val = min(1.0, total_sent / valid_contacts)
            
        self.progress_bar.set(progress_val)
        self.lbl_progress_text.configure(text=f"{int(progress_val * 100)}%")
        
        # Keep status as Idle for now
        self.lbl_campaign_status.configure(text="Current Status: Idle")



class ContactsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.all_contacts_data = [] # List of dicts with 'name', 'email', 'status', 'selected'
        
        # --- Top Section: Action Bar & Statistics ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.top_frame.grid_columnconfigure(1, weight=1)
        
        # Actions
        self.actions_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.actions_frame.grid(row=0, column=0, sticky="w")
        
        ctk.CTkButton(self.actions_frame, text="Import Contacts CSV", command=self.import_csv).pack(side="left", padx=(0,10))
        ctk.CTkButton(self.actions_frame, text="Reload Contacts", command=self.load_contacts).pack(side="left", padx=10)
        ctk.CTkButton(self.actions_frame, text="Delete Selected", command=self.delete_selected, fg_color="#8B0000", hover_color="darkred").pack(side="left", padx=10)
        ctk.CTkButton(self.actions_frame, text="Clear Contacts", command=self.clear_contacts, fg_color="red", hover_color="darkred").pack(side="left", padx=10)
        
        # Stats Cards
        self.stats_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.stats_frame.grid(row=0, column=1, sticky="e")
        
        self.lbl_stat_total = self._create_stat_label(self.stats_frame, "Total: 0")
        self.lbl_stat_valid = self._create_stat_label(self.stats_frame, "Valid: 0", "green")
        self.lbl_stat_invalid = self._create_stat_label(self.stats_frame, "Invalid: 0", "red")
        self.lbl_stat_dup = self._create_stat_label(self.stats_frame, "Duplicates: 0", "orange")
        
        # --- Middle Section: Search & Filter ---
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        self.filter_frame.grid_columnconfigure(0, weight=1)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_table())
        
        self.search_entry = ctk.CTkEntry(self.filter_frame, placeholder_text="Search contacts by name or email...", textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0,20))
        
        self.filter_var = ctk.StringVar(value="All")
        self.filter_menu = ctk.CTkOptionMenu(self.filter_frame, values=["All", "Valid", "Invalid", "Duplicate"], variable=self.filter_var, command=lambda _: self.refresh_table())
        self.filter_menu.pack(side="left")
        
        self.lbl_selected_count = ctk.CTkLabel(self.filter_frame, text="0 selected")
        self.lbl_selected_count.pack(side="right", padx=20)
        
        # --- Bottom Section: Table Headers & Scrollable Table ---
        self.table_container = ctk.CTkFrame(self, fg_color="transparent")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0,20))
        self.table_container.grid_columnconfigure(0, weight=1)
        self.table_container.grid_rowconfigure(1, weight=1)
        
        # Headers
        self.header_frame = ctk.CTkFrame(self.table_container)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        ctk.CTkLabel(self.header_frame, text="#", width=40, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(self.header_frame, text="Name", width=200, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(self.header_frame, text="Email", width=250, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkLabel(self.header_frame, text="Status", width=80, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(self.header_frame, text="Actions", width=140, font=ctk.CTkFont(weight="bold")).pack(side="right", padx=5)
        
        self.table_frame = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.table_frame.grid(row=1, column=0, sticky="nsew", pady=(5,0))
        
        # Load contacts immediately
        self.load_contacts()
        
    def _create_stat_label(self, parent, text, color=None):
        lbl = ctk.CTkLabel(parent, text=text, text_color=color, font=ctk.CTkFont(weight="bold"))
        lbl.pack(side="left", padx=10)
        return lbl
        
    def import_csv(self):
        file_path = filedialog.askopenfilename(title="Select Contacts CSV", filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                shutil.copy(file_path, CONTACTS_PATH)
                self.load_contacts()
                messagebox.showinfo("Success", "Contacts imported successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import contacts:\n{e}")
                
    def clear_contacts(self):
        if CONTACTS_PATH.exists():
            if messagebox.askyesno("Confirm", "Are you sure you want to clear all imported contacts?"):
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
                
                # Combine valid
                for c in res.valid:
                    self.all_contacts_data.append({"name": str(c.get("name","")), "email": str(c.get("email","")), "status": "Valid", "selected": False})
                
                # Combine invalid
                for c in res.invalid:
                    self.all_contacts_data.append({"name": str(c.get("name","")), "email": str(c.get("email","")), "status": "Invalid", "selected": False})
                    
                # Combine duplicates
                for c in res.duplicates:
                    self.all_contacts_data.append({"name": str(c.get("name","")), "email": str(c.get("email","")), "status": "Duplicate", "selected": False})
                    
                total = len(self.all_contacts_data)
                valid = res.total_valid
                invalid = res.total_invalid
                dups = res.total_duplicates
                
            except Exception as e:
                messagebox.showerror("Load Error", f"An error occurred loading contacts:\n{e}")
                
        self.lbl_stat_total.configure(text=f"Total: {total}")
        self.lbl_stat_valid.configure(text=f"Valid: {valid}")
        self.lbl_stat_invalid.configure(text=f"Invalid: {invalid}")
        self.lbl_stat_dup.configure(text=f"Duplicates: {dups}")
        
        self.refresh_table()
        self.update_dashboard()
        
    def save_contacts_to_csv(self):
        """Persist the current in-memory contact list back to contacts.csv."""
        rows = [{"name": c["name"], "email": c["email"]} for c in self.all_contacts_data]
        df = pd.DataFrame(rows)
        df.to_csv(CONTACTS_PATH, index=False)

    def delete_contact(self, contact):
        if messagebox.askyesno("Confirm Delete", f"Delete '{contact['name']}' ({contact['email']})?" ):
            self.all_contacts_data.remove(contact)
            self.save_contacts_to_csv()
            self.load_contacts()

    def delete_selected(self):
        selected = [c for c in self.all_contacts_data if c["selected"]]
        if not selected:
            messagebox.showinfo("No Selection", "Please tick the checkboxes next to the contacts you want to delete.")
            return
        if messagebox.askyesno("Confirm Delete", f"Delete {len(selected)} selected contact(s)?"):
            for c in selected:
                self.all_contacts_data.remove(c)
            self.save_contacts_to_csv()
            self.load_contacts()

    def edit_contact(self, contact):
        """Open a small dialog to edit name and email of a contact."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Contact")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.grab_set()  # Modal

        ctk.CTkLabel(dialog, text="Name:").grid(row=0, column=0, padx=20, pady=(20,5), sticky="w")
        entry_name = ctk.CTkEntry(dialog, width=250)
        entry_name.grid(row=0, column=1, padx=10, pady=(20,5))
        entry_name.insert(0, contact["name"])

        ctk.CTkLabel(dialog, text="Email:").grid(row=1, column=0, padx=20, pady=5, sticky="w")
        entry_email = ctk.CTkEntry(dialog, width=250)
        entry_email.grid(row=1, column=1, padx=10, pady=5)
        entry_email.insert(0, contact["email"])

        def save():
            new_name = entry_name.get().strip()
            new_email = entry_email.get().strip()
            if not new_email:
                messagebox.showerror("Error", "Email cannot be empty.", parent=dialog)
                return
            contact["name"] = new_name
            contact["email"] = new_email
            self.save_contacts_to_csv()
            dialog.destroy()
            self.load_contacts()

        ctk.CTkButton(dialog, text="Save", fg_color="green", hover_color="darkgreen", command=save).grid(row=2, column=0, columnspan=2, pady=20)

    def refresh_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()
            
        search_term = self.search_var.get().lower()
        filter_status = self.filter_var.get()
        
        filtered = []
        for c in self.all_contacts_data:
            if filter_status != "All" and c["status"] != filter_status:
                continue
            if search_term and search_term not in c["name"].lower() and search_term not in c["email"].lower():
                continue
            filtered.append(c)
            
        if not filtered:
            msg = "No contacts found matching your filters." if self.all_contacts_data else "No contacts imported yet.\nClick 'Import Contacts CSV' to get started."
            lbl = ctk.CTkLabel(self.table_frame, text=msg, text_color="gray", font=ctk.CTkFont(size=14))
            lbl.pack(pady=40)
            self.lbl_selected_count.configure(text="0 selected")
            return
            
        for i, c in enumerate(filtered, 1):
            row_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            
            chk_var = ctk.BooleanVar(value=c["selected"])
            def on_check(contact=c, var=chk_var):
                contact["selected"] = var.get()
                self._update_selected_count()
                
            chk = ctk.CTkCheckBox(row_frame, text=str(i), width=40, variable=chk_var, command=on_check)
            chk.pack(side="left", padx=5)
            
            ctk.CTkLabel(row_frame, text=c["name"][:30], width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row_frame, text=c["email"][:40], width=250, anchor="w").pack(side="left", padx=5, fill="x", expand=True)
            
            color = "green" if c["status"] == "Valid" else ("red" if c["status"] == "Invalid" else "orange")
            ctk.CTkLabel(row_frame, text=c["status"], width=80, text_color=color).pack(side="left", padx=5)

            # Edit & Delete buttons
            btn_del = ctk.CTkButton(row_frame, text="Delete", width=60, fg_color="red", hover_color="darkred", command=lambda contact=c: self.delete_contact(contact))
            btn_del.pack(side="right", padx=(2, 5))
            btn_edit = ctk.CTkButton(row_frame, text="Edit", width=60, command=lambda contact=c: self.edit_contact(contact))
            btn_edit.pack(side="right", padx=2)
            
        self._update_selected_count()
        
    def _update_selected_count(self):
        count = sum(1 for c in self.all_contacts_data if c["selected"])
        self.lbl_selected_count.configure(text=f"{count} selected")


class CampaignView(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        self.template_path = BASE_DIR / "email_template.html"
        
        # --- Config Section ---
        self.config_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.config_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.config_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.config_frame, text="Campaign Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_name = ctk.CTkEntry(self.config_frame, placeholder_text="My Awesome Campaign")
        self.entry_name.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        
        ctk.CTkLabel(self.config_frame, text="Email Subject:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_subject = ctk.CTkEntry(self.config_frame, placeholder_text="Hello {name}, check this out!")
        self.entry_subject.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.entry_subject.insert(0, settings.default_subject)
        
        ctk.CTkLabel(self.config_frame, text="Template:").grid(row=2, column=0, sticky="w", pady=5)
        self.template_btn_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.template_btn_frame.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        ctk.CTkButton(self.template_btn_frame, text="Select HTML", width=100, command=self.pick_template).pack(side="left")
        self.lbl_template = ctk.CTkLabel(self.template_btn_frame, text=self.template_path.name)
        self.lbl_template.pack(side="left", padx=10)
        
        # --- Preview Section ---
        self.preview_frame = ctk.CTkFrame(self)
        self.preview_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(1, weight=1)
        
        header_frame = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(header_frame, text="Live Preview (First Contact)", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(header_frame, text="Refresh Preview", width=120, command=self.refresh_preview).pack(side="right")
        
        if _TKINTERWEB_AVAILABLE:
            # Wrap in a standard tk.Frame so HtmlFrame embeds correctly
            self._html_container = tk.Frame(
                self.preview_frame, height=380, bg="white", relief="flat"
            )
            self._html_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
            self._html_container.pack_propagate(False)  # keep fixed height
            self.html_preview = HtmlFrame(
                self._html_container,
                messages_enabled=False,
                vertical_scrollbar=True,
            )
            self.html_preview.pack(fill="both", expand=True)
            self.preview_box = None
        else:
            self._html_container = None
            self.html_preview = None
            self.preview_box = ctk.CTkTextbox(self.preview_frame, height=380, state="disabled")
            self.preview_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # --- Actions & Progress ---
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        self.action_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_test = ctk.CTkButton(self.action_frame, text="Send Test Email", fg_color="gray", hover_color="darkgray", command=self.send_test)
        self.btn_test.grid(row=0, column=0, sticky="w")
        
        self.btn_start = ctk.CTkButton(self.action_frame, text="▶ Start Campaign", fg_color="green", hover_color="darkgreen", command=self.start_campaign)
        self.btn_start.grid(row=0, column=2, sticky="e")
        
        self.lbl_recipients = ctk.CTkLabel(self.action_frame, text="Recipients ready: 0", text_color="orange")
        self.lbl_recipients.grid(row=0, column=1, padx=20)
        
        # --- Live Log ---
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(10,20))
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_progress = ctk.CTkLabel(self.log_frame, text="Idle", font=ctk.CTkFont(weight="bold"))
        self.lbl_progress.pack(anchor="w", padx=10, pady=(10,5))
        
        self.progress_bar = ctk.CTkProgressBar(self.log_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        self.log_box = ctk.CTkTextbox(self.log_frame, height=150, state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.is_running = False
        
        # Initial updates
        self.update_recipient_count()
        self.refresh_preview()

    def update_recipient_count(self):
        try:
            views = self.winfo_toplevel().views
            if "contacts" in views:
                contacts_view = views["contacts"]
                selected = [c for c in contacts_view.all_contacts_data if c.get("selected")]
                if selected:
                    self.lbl_recipients.configure(text=f"Recipients ready: {len(selected)} (Selected)")
                    return
        except Exception:
            pass
            
        # Fallback to all valid
        try:
            loader = ContactLoader(CONTACTS_PATH)
            res = loader.load()
            self.lbl_recipients.configure(text=f"Recipients ready: {res.total_valid} (All Valid)")
        except Exception:
            self.lbl_recipients.configure(text="Recipients ready: 0")

    def pick_template(self):
        path = filedialog.askopenfilename(title="Select HTML Template", filetypes=[("HTML Files", "*.html")])
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

        html = ""
        try:
            if not self.template_path.exists():
                html = "<p style='color:red;font-family:sans-serif'>Template file not found.</p>"
            else:
                html = render_template(self.template_path, contact)
        except Exception as e:
            html = f"<p style='color:red;font-family:sans-serif'>Error rendering template: {e}</p>"

        if _TKINTERWEB_AVAILABLE and self.html_preview is not None:
            self.html_preview.load_html(html)
        else:
            # Fallback: show raw HTML in textbox
            self.preview_box.configure(state="normal")
            self.preview_box.delete("1.0", "end")
            self.preview_box.insert("1.0", html)
            self.preview_box.configure(state="disabled")

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
            html = render_template(self.template_path, {"name": "Test User", "email": test_email})
            
            self.log_msg(f"Sending test email to {test_email}...")
            
            def send_t():
                try:
                    with EmailSender() as sender:
                        sender.send_email(test_email, "Test User", subject, html)
                    self.after(0, lambda: messagebox.showinfo("Success", "Test email sent successfully!"))
                    self.after(0, lambda: self.log_msg("Test email sent!"))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Error", f"Failed to send test email:\n{e}"))
                    self.after(0, lambda: self.log_msg(f"Test email failed: {e}"))
            
            threading.Thread(target=send_t, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def start_campaign(self):
        if self.is_running:
            return
            
        if not CONTACTS_PATH.exists():
            messagebox.showerror("Error", "No contacts loaded. Please go to the Contacts tab first.")
            return
            
        if not self.template_path.exists():
            messagebox.showerror("Error", "Template file not found.")
            return
            
        if not messagebox.askyesno("Start Campaign", "Are you sure you want to start sending emails now?"):
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
            msg = f"[{index}/{total}] {name} -> {status}"
            self.after(0, lambda: self.progress_bar.set(pct))
            self.after(0, lambda: self.lbl_progress.configure(text=f"Sending {int(pct*100)}% ({index}/{total})"))
            self.after(0, lambda: self.log_msg(msg))
            
        def run_camp():
            try:
                self.after(0, lambda: self.log_msg("Starting campaign engine..."))
                send_campaign(
                    CONTACTS_PATH,
                    self.template_path,
                    subject=subject,
                    progress_callback=progress_cb
                )
                self.after(0, lambda: messagebox.showinfo("Done", "Campaign finished!"))
                self.after(0, lambda: self.lbl_progress.configure(text="Finished"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Campaign crashed:\n{e}"))
                self.after(0, lambda: self.lbl_progress.configure(text="Error"))
            finally:
                self.after(0, self.finish_campaign)
                
        threading.Thread(target=run_camp, daemon=True).start()
        
    def finish_campaign(self):
        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_test.configure(state="normal")
        try:
            self.winfo_toplevel().views["dashboard"].refresh_data()
        except:
            pass


class SchedulerView(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        
        # Make sure the background scheduler loop is running
        _start_scheduler_thread()
        
        # --- Config Section ---
        self.config_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.config_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.config_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.config_frame, text="Campaign Subject:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_subject = ctk.CTkEntry(self.config_frame, placeholder_text="Subject...")
        self.entry_subject.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        self.entry_subject.insert(0, settings.default_subject)
        
        ctk.CTkLabel(self.config_frame, text="Frequency:").grid(row=1, column=0, sticky="w", pady=5)
        self.freq_var = ctk.StringVar(value="Daily")
        self.freq_menu = ctk.CTkOptionMenu(self.config_frame, values=["Daily", "Every N Hours"], variable=self.freq_var, command=self._on_freq_change)
        self.freq_menu.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        self.lbl_time_val = ctk.CTkLabel(self.config_frame, text="Time (HH:MM):")
        self.lbl_time_val.grid(row=2, column=0, sticky="w", pady=5)
        self.entry_time_val = ctk.CTkEntry(self.config_frame, placeholder_text="08:00")
        self.entry_time_val.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        self.entry_time_val.insert(0, "08:00")
        
        # --- Action Section ---
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        ctk.CTkButton(self.action_frame, text="Schedule Campaign", fg_color="green", hover_color="darkgreen", command=self.schedule_job).pack(side="left")
        ctk.CTkButton(self.action_frame, text="Refresh Table", command=self.refresh_table).pack(side="right")
        
        # --- Table Section ---
        self.table_container = ctk.CTkFrame(self, fg_color="transparent")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10,20))
        self.table_container.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.table_container, text="Scheduled Campaigns", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", pady=(0,5))
        
        # Headers
        self.header_frame = ctk.CTkFrame(self.table_container)
        self.header_frame.grid(row=1, column=0, sticky="ew")
        
        ctk.CTkLabel(self.header_frame, text="Frequency", width=150, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(self.header_frame, text="Next Run", width=150, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(self.header_frame, text="Action", width=100, font=ctk.CTkFont(weight="bold")).pack(side="right", padx=15)
        
        self.table_frame = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent", height=200)
        self.table_frame.grid(row=2, column=0, sticky="nsew", pady=(5,0))
        
        self.refresh_table()
        
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
            messagebox.showerror("Error", "No contacts loaded. Please go to the Contacts tab first.")
            return
            
        subject = self.entry_subject.get()
        freq = self.freq_var.get()
        val = self.entry_time_val.get()
        
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
            lbl = ctk.CTkLabel(self.table_frame, text="No campaigns scheduled.", text_color="gray")
            lbl.pack(pady=20)
            return
            
        for job in jobs:
            row_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            
            # Reconstruct a friendly description from the job properties
            if hasattr(job, 'at_time') and job.at_time:
                freq_str = f"Daily at {job.at_time}"
            elif job.interval > 1:
                freq_str = f"Every {job.interval} {job.unit}"
            else:
                freq_str = f"Every {job.unit[:-1]}"
                
            next_run = job.next_run.strftime("%Y-%m-%d %H:%M:%S") if job.next_run else "Unknown"
            
            ctk.CTkLabel(row_frame, text=freq_str, width=150, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row_frame, text=next_run, width=150, anchor="w").pack(side="left", padx=5)
            
            btn_cancel = ctk.CTkButton(row_frame, text="Cancel", width=80, fg_color="red", hover_color="darkred", command=lambda j=job: self.cancel_job_ui(j))
            btn_cancel.pack(side="right", padx=15)


class LogsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.all_logs_data = [] # List of dicts
        
        # --- Top Section: Action Bar & Statistics ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.top_frame.grid_columnconfigure(1, weight=1)
        
        # Actions
        self.actions_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.actions_frame.grid(row=0, column=0, sticky="w")
        
        ctk.CTkButton(self.actions_frame, text="Refresh Logs", command=self.load_logs).pack(side="left", padx=(0,10))
        
        # Stats Cards
        self.stats_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.stats_frame.grid(row=0, column=1, sticky="e")
        
        self.lbl_stat_total = self._create_stat_label(self.stats_frame, "Total: 0")
        self.lbl_stat_sent = self._create_stat_label(self.stats_frame, "Sent: 0", "green")
        self.lbl_stat_failed = self._create_stat_label(self.stats_frame, "Failed: 0", "red")
        self.lbl_stat_skipped = self._create_stat_label(self.stats_frame, "Skipped: 0", "orange")
        
        # --- Middle Section: Search & Filter ---
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        self.filter_frame.grid_columnconfigure(0, weight=1)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_table())
        
        self.search_entry = ctk.CTkEntry(self.filter_frame, placeholder_text="Search logs by name, email, or subject...", textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0,20))
        
        self.filter_var = ctk.StringVar(value="All")
        self.filter_menu = ctk.CTkOptionMenu(self.filter_frame, values=["All", "Sent", "Failed", "Skipped"], variable=self.filter_var, command=lambda _: self.refresh_table())
        self.filter_menu.pack(side="left")
        
        # --- Bottom Section: Table Headers & Scrollable Table ---
        self.table_container = ctk.CTkFrame(self, fg_color="transparent")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0,20))
        self.table_container.grid_columnconfigure(0, weight=1)
        self.table_container.grid_rowconfigure(1, weight=1)
        
        # Headers
        self.header_frame = ctk.CTkFrame(self.table_container)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        ctk.CTkLabel(self.header_frame, text="Time", width=150, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(self.header_frame, text="Recipient", width=200, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(self.header_frame, text="Subject", width=250, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkLabel(self.header_frame, text="Status", width=80, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(self.header_frame, text="Error", width=150, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="right", padx=15)
        
        self.table_frame = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.table_frame.grid(row=1, column=0, sticky="nsew", pady=(5,0))
        
        # Load logs immediately
        self.load_logs()
        
    def _create_stat_label(self, parent, text, color=None):
        lbl = ctk.CTkLabel(parent, text=text, text_color=color, font=ctk.CTkFont(weight="bold"))
        lbl.pack(side="left", padx=10)
        return lbl
        
    def load_logs(self):
        self.all_logs_data.clear()
        
        total = sent = failed = skipped = 0
        
        if LOGS_PATH.exists():
            try:
                df = pd.read_csv(LOGS_PATH)
                df = df.fillna("")
                
                # Newest first
                df = df.iloc[::-1]
                
                for _, row in df.iterrows():
                    rec = {
                        "timestamp": str(row.get("timestamp", "")),
                        "email": str(row.get("email", "")),
                        "name": str(row.get("name", "")),
                        "subject": str(row.get("subject", "")),
                        "status": str(row.get("status", "")),
                        "error": str(row.get("error", ""))
                    }
                    self.all_logs_data.append(rec)
                    
                    st = rec["status"].lower()
                    if st == "sent":
                        sent += 1
                    elif st == "failed":
                        failed += 1
                    elif st == "skipped":
                        skipped += 1
                        
                total = len(self.all_logs_data)
            except pd.errors.EmptyDataError:
                pass
            except Exception as e:
                messagebox.showerror("Load Error", f"An error occurred loading logs:\n{e}")
                
        self.lbl_stat_total.configure(text=f"Total: {total}")
        self.lbl_stat_sent.configure(text=f"Sent: {sent}")
        self.lbl_stat_failed.configure(text=f"Failed: {failed}")
        self.lbl_stat_skipped.configure(text=f"Skipped: {skipped}")
        
        self.refresh_table()
        
    def refresh_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()
            
        search_term = self.search_var.get().lower()
        filter_status = self.filter_var.get()
        
        filtered = []
        for r in self.all_logs_data:
            if filter_status != "All" and r["status"] != filter_status:
                continue
            if search_term:
                if search_term not in r["name"].lower() and \
                   search_term not in r["email"].lower() and \
                   search_term not in r["subject"].lower():
                    continue
            filtered.append(r)
            
        if not filtered:
            msg = "No logs match your filters." if self.all_logs_data else "No campaign logs found."
            lbl = ctk.CTkLabel(self.table_frame, text=msg, text_color="gray", font=ctk.CTkFont(size=14))
            lbl.pack(pady=40)
            return
            
        # Optimization: Only render top 200 logs to prevent lag
        max_render = 200
        for i, r in enumerate(filtered):
            if i >= max_render:
                lbl = ctk.CTkLabel(self.table_frame, text=f"... and {len(filtered)-max_render} more rows hidden to maintain performance.", text_color="gray")
                lbl.pack(pady=10)
                break
                
            row_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            
            time_str = r["timestamp"][:19]
            recipient = f"{r['name'][:15]} <{r['email'][:20]}>" if r['name'] else r['email'][:35]
            
            ctk.CTkLabel(row_frame, text=time_str, width=150, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row_frame, text=recipient, width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row_frame, text=r["subject"][:40], width=250, anchor="w").pack(side="left", padx=5, fill="x", expand=True)
            
            status = r["status"]
            color = "green" if status == "Sent" else ("red" if status == "Failed" else "orange")
            ctk.CTkLabel(row_frame, text=status, width=80, text_color=color).pack(side="left", padx=5)
            
            err_text = r["error"][:30] + "..." if len(r["error"]) > 30 else r["error"]
            ctk.CTkLabel(row_frame, text=err_text, width=150, anchor="w", text_color="gray").pack(side="right", padx=15)


class SettingsView(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        
        # --- Authentication Status Card ---
        self.auth_frame = ctk.CTkFrame(self)
        self.auth_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.auth_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.auth_frame, text="Authentication Settings", font=ctk.CTkFont(weight="bold", size=16)).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10), columnspan=2)
        
        ctk.CTkLabel(self.auth_frame, text="Gmail Account:").grid(row=1, column=0, sticky="w", padx=15, pady=5)
        account = settings.email_address if settings.email_address else "Not Configured"
        ctk.CTkLabel(self.auth_frame, text=account).grid(row=1, column=1, sticky="w", padx=15, pady=5)
        
        ctk.CTkLabel(self.auth_frame, text="Password:").grid(row=2, column=0, sticky="w", padx=15, pady=5)
        pwd_disp = "********" if settings.email_password else "Not Configured"
        ctk.CTkLabel(self.auth_frame, text=pwd_disp).grid(row=2, column=1, sticky="w", padx=15, pady=5)
        
        ctk.CTkLabel(self.auth_frame, text="Credential Status:").grid(row=3, column=0, sticky="w", padx=15, pady=(5, 15))
        if settings.email_address and settings.email_password:
            lbl_status = ctk.CTkLabel(self.auth_frame, text="Configured", text_color="green", font=ctk.CTkFont(weight="bold"))
        else:
            lbl_status = ctk.CTkLabel(self.auth_frame, text="Missing Credentials", text_color="red", font=ctk.CTkFont(weight="bold"))
        lbl_status.grid(row=3, column=1, sticky="w", padx=15, pady=(5, 15))
        
        # --- SMTP Configuration Card ---
        self.smtp_frame = ctk.CTkFrame(self)
        self.smtp_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        self.smtp_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.smtp_frame, text="SMTP Configuration", font=ctk.CTkFont(weight="bold", size=16)).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10), columnspan=2)
        
        ctk.CTkLabel(self.smtp_frame, text="SMTP Server:").grid(row=1, column=0, sticky="w", padx=15, pady=5)
        ctk.CTkLabel(self.smtp_frame, text=settings.smtp_host).grid(row=1, column=1, sticky="w", padx=15, pady=5)
        
        ctk.CTkLabel(self.smtp_frame, text="SMTP Port:").grid(row=2, column=0, sticky="w", padx=15, pady=5)
        ctk.CTkLabel(self.smtp_frame, text=str(settings.smtp_port)).grid(row=2, column=1, sticky="w", padx=15, pady=5)
        
        self.btn_test_smtp = ctk.CTkButton(self.smtp_frame, text="Test SMTP Connection", command=self.test_smtp)
        self.btn_test_smtp.grid(row=3, column=0, sticky="w", padx=15, pady=(10, 15), columnspan=2)
        
        # --- Application Settings Card ---
        self.app_frame = ctk.CTkFrame(self)
        self.app_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        self.app_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.app_frame, text="Application Settings", font=ctk.CTkFont(weight="bold", size=16)).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 10), columnspan=2)
        
        ctk.CTkLabel(self.app_frame, text="Max Emails Per Hour:").grid(row=1, column=0, sticky="w", padx=15, pady=5)
        self.entry_max_emails = ctk.CTkEntry(self.app_frame, width=100)
        self.entry_max_emails.grid(row=1, column=1, sticky="w", padx=15, pady=5)
        self.entry_max_emails.insert(0, str(settings.max_emails_per_hour))
        
        ctk.CTkLabel(self.app_frame, text="Contacts File:").grid(row=2, column=0, sticky="w", padx=15, pady=5)
        ctk.CTkLabel(self.app_frame, text=CONTACTS_FILE).grid(row=2, column=1, sticky="w", padx=15, pady=5)
        
        ctk.CTkLabel(self.app_frame, text="Template File:").grid(row=3, column=0, sticky="w", padx=15, pady=5)
        ctk.CTkLabel(self.app_frame, text=TEMPLATE_FILE).grid(row=3, column=1, sticky="w", padx=15, pady=5)
        
        ctk.CTkLabel(self.app_frame, text="Log File:").grid(row=4, column=0, sticky="w", padx=15, pady=(5, 15))
        ctk.CTkLabel(self.app_frame, text=LOG_FILE).grid(row=4, column=1, sticky="w", padx=15, pady=(5, 15))
        
        # --- Action Section ---
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 20))
        
        self.btn_save = ctk.CTkButton(self.action_frame, text="Save Settings", fg_color="green", hover_color="darkgreen", command=self.save_settings)
        self.btn_save.pack(side="right")
        
    def test_smtp(self):
        self.btn_test_smtp.configure(state="disabled", text="Testing...")
        
        def run_test():
            try:
                # Use context manager just to verify login
                with EmailSender() as sender:
                    pass
                self.after(0, lambda: messagebox.showinfo("Success", "SMTP connection authenticated successfully!"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"SMTP Connection Failed:\n{e}"))
            finally:
                self.after(0, lambda: self.btn_test_smtp.configure(state="normal", text="Test SMTP Connection"))
                
        threading.Thread(target=run_test, daemon=True).start()
        
    def save_settings(self):
        new_limit = self.entry_max_emails.get()
        if not new_limit.isdigit() or int(new_limit) <= 0:
            messagebox.showerror("Error", "Max Emails Per Hour must be a positive integer.")
            return
            
        try:
            env_path = BASE_DIR / ".env"
            if not env_path.exists():
                env_path.touch()
                
            dotenv.set_key(env_path, "MAX_EMAILS_PER_HOUR", new_limit)
            settings.max_emails_per_hour = int(new_limit)
            
            messagebox.showinfo("Success", "Settings saved successfully!\nMax Emails Per Hour updated.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings to .env:\n{e}")
