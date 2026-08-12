import customtkinter as ctk

from gui.views import (
    DashboardView,
    ContactsView,
    CampaignView,
    SchedulerView,
    LogsView,
    SettingsView
)

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Automated Bulk Email Campaign Manager")
        self.geometry("1100x700")
        self.minsize(900, 600)
        
        # Configure grid layout (1 row, 2 columns)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Campaign\nManager", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))
        
        # Sidebar buttons
        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Dashboard", anchor="w", command=lambda: self.select_view("dashboard"))
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_contacts = ctk.CTkButton(self.sidebar_frame, text="Contacts", anchor="w", command=lambda: self.select_view("contacts"))
        self.btn_contacts.grid(row=2, column=0, padx=20, pady=10)
        
        self.btn_campaign = ctk.CTkButton(self.sidebar_frame, text="Create Campaign", anchor="w", command=lambda: self.select_view("campaign"))
        self.btn_campaign.grid(row=3, column=0, padx=20, pady=10)
        
        self.btn_scheduler = ctk.CTkButton(self.sidebar_frame, text="Scheduler", anchor="w", command=lambda: self.select_view("scheduler"))
        self.btn_scheduler.grid(row=4, column=0, padx=20, pady=10)
        
        self.btn_logs = ctk.CTkButton(self.sidebar_frame, text="Campaign Logs", anchor="w", command=lambda: self.select_view("logs"))
        self.btn_logs.grid(row=5, column=0, padx=20, pady=10)
        
        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="Settings", anchor="w", command=lambda: self.select_view("settings"))
        self.btn_settings.grid(row=6, column=0, padx=20, pady=10)
        
        # Appearance mode toggle
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionmenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionmenu.grid(row=9, column=0, padx=20, pady=(10, 20))
        self.appearance_mode_optionmenu.set("System")
        
        # --- Main Content Area ---
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_content_frame.grid_rowconfigure(1, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        self.header_label = ctk.CTkLabel(self.main_content_frame, text="Dashboard", font=ctk.CTkFont(size=24, weight="bold"))
        self.header_label.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Dictionary to store view instances
        self.views = {}
        
        # Initialize views
        self.views["dashboard"] = DashboardView(self.main_content_frame)
        self.views["contacts"] = ContactsView(self.main_content_frame)
        self.views["campaign"] = CampaignView(self.main_content_frame)
        self.views["scheduler"] = SchedulerView(self.main_content_frame)
        self.views["logs"] = LogsView(self.main_content_frame)
        self.views["settings"] = SettingsView(self.main_content_frame)
        
        # Start on dashboard
        self.current_view = None
        self.select_view("dashboard")
        
    def select_view(self, name):
        # Hide current view
        if self.current_view:
            self.views[self.current_view].grid_forget()
            
        # Update header
        titles = {
            "dashboard": "Dashboard",
            "contacts": "Contacts Management",
            "campaign": "Create Campaign",
            "scheduler": "Scheduler",
            "logs": "Campaign Logs",
            "settings": "Settings"
        }
        self.header_label.configure(text=titles.get(name, name.capitalize()))
        
        # Show new view
        self.current_view = name
        self.views[name].grid(row=1, column=0, sticky="nsew")
        
        # Update button highlights
        buttons = {
            "dashboard": self.btn_dashboard,
            "contacts": self.btn_contacts,
            "campaign": self.btn_campaign,
            "scheduler": self.btn_scheduler,
            "logs": self.btn_logs,
            "settings": self.btn_settings
        }
        
        for btn_name, btn in buttons.items():
            if btn_name == name:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
