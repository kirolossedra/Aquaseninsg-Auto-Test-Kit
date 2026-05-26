"""
Gateway Addition Logs - Modern Azure SQL GUI

This application provides a modern CustomTkinter GUI for managing records in:
dbo.GatewayAdditionLogs

Features:
- Modern light-blue and white theme
- Password login screen with hidden password input
- Animated login card transition
- Azure SQL connection test
- Automatic table creation if missing
- Gateway addition form
- Insert new gateway log records
- Update selected gateway log records
- Search/view records window
- Load selected record into form
- Delete selected record
- Rounded panels/cards
- Modern buttons, dropdowns, and scrollable layouts
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
import pyodbc
import customtkinter as ctk


# ============================================================
# AZURE SQL CONFIGURATION
# ============================================================

AZURE_SQL_SERVER = "aquasenseserver2.database.windows.net"
AZURE_SQL_DATABASE = "aquadb"
AZURE_SQL_USERNAME = "aquasense123"

TABLE_SCHEMA = "dbo"
TABLE_NAME = "GatewayAdditionLogs"


# ============================================================
# THEME CONFIGURATION
# ============================================================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COLOR_BACKGROUND = "#EAF7FF"
COLOR_CARD = "#FFFFFF"
COLOR_PRIMARY = "#5BBCE4"
COLOR_PRIMARY_DARK = "#2697C7"
COLOR_PRIMARY_LIGHT = "#DFF5FF"
COLOR_TEXT = "#143447"
COLOR_MUTED = "#5F7D8C"
COLOR_BORDER = "#B9E6F7"
COLOR_SUCCESS = "#2A9D8F"
COLOR_WARNING = "#F4A261"
COLOR_DANGER = "#D9534F"
COLOR_DANGER_DARK = "#B83C38"
COLOR_DARK_BLUE = "#315D75"


# ============================================================
# DATABASE MANAGER
# ============================================================

class DatabaseManager:
    def __init__(self, password):
        self.password = password
        self.connection = None

    def connect(self):
        connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={AZURE_SQL_SERVER};"
            f"DATABASE={AZURE_SQL_DATABASE};"
            f"UID={AZURE_SQL_USERNAME};"
            f"PWD={self.password};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )

        self.connection = pyodbc.connect(connection_string)
        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_commit(self, query, params=None):
        if params is None:
            params = []

        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        cursor.close()

    def execute_fetchall(self, query, params=None):
        if params is None:
            params = []

        cursor = self.connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def create_table_if_missing(self):
        query = f"""
        IF NOT EXISTS (
            SELECT 1
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{TABLE_SCHEMA}'
              AND TABLE_NAME = '{TABLE_NAME}'
        )
        BEGIN
            CREATE TABLE {TABLE_SCHEMA}.{TABLE_NAME}
            (
                LogId INT IDENTITY(1,1) PRIMARY KEY,

                GatewayId NVARCHAR(100) NOT NULL,

                ProgrammedByName NVARCHAR(150) NOT NULL,

                ICCID NVARCHAR(50) NULL,

                BLEBuildMode NVARCHAR(20) NULL
                    CHECK (BLEBuildMode IN ('Debug', 'Release')),

                LTEFirmwareStatus NVARCHAR(20) NULL
                    CHECK (LTEFirmwareStatus IN ('Old', 'New')),

                PassedAllQualityChecks BIT NOT NULL DEFAULT 0,

                LTEModemFirmwareVersion NVARCHAR(100) NULL,

                SIMProvider NVARCHAR(20) NULL
                    CHECK (SIMProvider IN ('Bell', 'Hologram')),

                DataLimitEnforced BIT NOT NULL DEFAULT 0,

                InForceDate DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),

                Purpose NVARCHAR(20) NULL
                    CHECK (Purpose IN ('Deployment', 'Testing')),

                UsageScope NVARCHAR(20) NULL
                    CHECK (UsageScope IN ('Internal', 'External')),

                IntendedUser NVARCHAR(200) NULL,

                CreatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

                UpdatedAt DATETIME2 NULL
            );
        END
        """
        self.execute_commit(query)

    def insert_gateway_log(self, data):
        query = f"""
        INSERT INTO {TABLE_SCHEMA}.{TABLE_NAME}
        (
            GatewayId,
            ProgrammedByName,
            ICCID,
            BLEBuildMode,
            LTEFirmwareStatus,
            PassedAllQualityChecks,
            LTEModemFirmwareVersion,
            SIMProvider,
            DataLimitEnforced,
            InForceDate,
            Purpose,
            UsageScope,
            IntendedUser
        )
        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        params = [
            data["GatewayId"],
            data["ProgrammedByName"],
            data["ICCID"],
            data["BLEBuildMode"],
            data["LTEFirmwareStatus"],
            data["PassedAllQualityChecks"],
            data["LTEModemFirmwareVersion"],
            data["SIMProvider"],
            data["DataLimitEnforced"],
            data["InForceDate"],
            data["Purpose"],
            data["UsageScope"],
            data["IntendedUser"],
        ]

        self.execute_commit(query, params)

    def update_gateway_log(self, log_id, data):
        query = f"""
        UPDATE {TABLE_SCHEMA}.{TABLE_NAME}
        SET
            GatewayId = ?,
            ProgrammedByName = ?,
            ICCID = ?,
            BLEBuildMode = ?,
            LTEFirmwareStatus = ?,
            PassedAllQualityChecks = ?,
            LTEModemFirmwareVersion = ?,
            SIMProvider = ?,
            DataLimitEnforced = ?,
            InForceDate = ?,
            Purpose = ?,
            UsageScope = ?,
            IntendedUser = ?,
            UpdatedAt = SYSDATETIME()
        WHERE LogId = ?;
        """

        params = [
            data["GatewayId"],
            data["ProgrammedByName"],
            data["ICCID"],
            data["BLEBuildMode"],
            data["LTEFirmwareStatus"],
            data["PassedAllQualityChecks"],
            data["LTEModemFirmwareVersion"],
            data["SIMProvider"],
            data["DataLimitEnforced"],
            data["InForceDate"],
            data["Purpose"],
            data["UsageScope"],
            data["IntendedUser"],
            log_id,
        ]

        self.execute_commit(query, params)

    def delete_gateway_log(self, log_id):
        query = f"""
        DELETE FROM {TABLE_SCHEMA}.{TABLE_NAME}
        WHERE LogId = ?;
        """
        self.execute_commit(query, [log_id])

    def search_gateway_logs(self, search_text=""):
        search_text = search_text.strip()

        if not search_text:
            query = f"""
            SELECT TOP 300
                LogId,
                GatewayId,
                ProgrammedByName,
                ICCID,
                BLEBuildMode,
                LTEFirmwareStatus,
                PassedAllQualityChecks,
                LTEModemFirmwareVersion,
                SIMProvider,
                DataLimitEnforced,
                InForceDate,
                Purpose,
                UsageScope,
                IntendedUser,
                CreatedAt,
                UpdatedAt
            FROM {TABLE_SCHEMA}.{TABLE_NAME}
            ORDER BY CreatedAt DESC;
            """
            return self.execute_fetchall(query)

        query = f"""
        SELECT TOP 300
            LogId,
            GatewayId,
            ProgrammedByName,
            ICCID,
            BLEBuildMode,
            LTEFirmwareStatus,
            PassedAllQualityChecks,
            LTEModemFirmwareVersion,
            SIMProvider,
            DataLimitEnforced,
            InForceDate,
            Purpose,
            UsageScope,
            IntendedUser,
            CreatedAt,
            UpdatedAt
        FROM {TABLE_SCHEMA}.{TABLE_NAME}
        WHERE
            GatewayId LIKE ?
            OR ProgrammedByName LIKE ?
            OR ICCID LIKE ?
            OR BLEBuildMode LIKE ?
            OR LTEFirmwareStatus LIKE ?
            OR LTEModemFirmwareVersion LIKE ?
            OR SIMProvider LIKE ?
            OR Purpose LIKE ?
            OR UsageScope LIKE ?
            OR IntendedUser LIKE ?
        ORDER BY CreatedAt DESC;
        """

        pattern = f"%{search_text}%"
        params = [pattern] * 10
        return self.execute_fetchall(query, params)


# ============================================================
# MODERN LOGIN WINDOW
# ============================================================

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gateway Addition Logs - Login")
        self.geometry("820x540")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BACKGROUND)

        self.db_manager = None
        self.card_x_position = -500

        self.build_login_ui()
        self.animate_login_card()

    def build_login_ui(self):
        self.background_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_BACKGROUND,
            corner_radius=0
        )
        self.background_frame.pack(fill="both", expand=True)

        self.left_art_panel = ctk.CTkFrame(
            self.background_frame,
            width=260,
            height=540,
            fg_color=COLOR_PRIMARY,
            corner_radius=0
        )
        self.left_art_panel.place(x=0, y=0)

        ctk.CTkLabel(
            self.left_art_panel,
            text="AQS",
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=36, weight="bold")
        ).place(x=42, y=58)

        ctk.CTkLabel(
            self.left_art_panel,
            text="Gateway\nProgramming\nControl",
            text_color="white",
            justify="left",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold")
        ).place(x=42, y=140)

        ctk.CTkLabel(
            self.left_art_panel,
            text="Azure SQL linked internal tool",
            text_color="#EAF7FF",
            font=ctk.CTkFont(family="Segoe UI", size=12)
        ).place(x=42, y=430)

        self.decor_circle_1 = ctk.CTkFrame(
            self.left_art_panel,
            width=120,
            height=120,
            fg_color="#8BD8F3",
            corner_radius=60
        )
        self.decor_circle_1.place(x=160, y=300)

        self.decor_circle_2 = ctk.CTkFrame(
            self.left_art_panel,
            width=70,
            height=70,
            fg_color="#C8F1FF",
            corner_radius=35
        )
        self.decor_circle_2.place(x=32, y=330)

        self.login_card = ctk.CTkFrame(
            self.background_frame,
            width=470,
            height=420,
            fg_color=COLOR_CARD,
            border_color=COLOR_BORDER,
            border_width=2,
            corner_radius=28
        )
        self.login_card.place(x=self.card_x_position, y=60)

        ctk.CTkLabel(
            self.login_card,
            text="Secure Login",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold")
        ).place(x=42, y=38)

        ctk.CTkLabel(
            self.login_card,
            text="Enter the Azure SQL password to access the gateway log system.",
            text_color=COLOR_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=13)
        ).place(x=42, y=78)

        self.info_box = ctk.CTkFrame(
            self.login_card,
            width=385,
            height=112,
            fg_color=COLOR_PRIMARY_LIGHT,
            corner_radius=18
        )
        self.info_box.place(x=42, y=120)

        ctk.CTkLabel(
            self.info_box,
            text="Server",
            text_color=COLOR_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        ).place(x=18, y=14)

        ctk.CTkLabel(
            self.info_box,
            text=AZURE_SQL_SERVER,
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=12)
        ).place(x=115, y=14)

        ctk.CTkLabel(
            self.info_box,
            text="Database",
            text_color=COLOR_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        ).place(x=18, y=46)

        ctk.CTkLabel(
            self.info_box,
            text=AZURE_SQL_DATABASE,
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=12)
        ).place(x=115, y=46)

        ctk.CTkLabel(
            self.info_box,
            text="Username",
            text_color=COLOR_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        ).place(x=18, y=78)

        ctk.CTkLabel(
            self.info_box,
            text=AZURE_SQL_USERNAME,
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=12)
        ).place(x=115, y=78)

        self.password_var = tk.StringVar()

        ctk.CTkLabel(
            self.login_card,
            text="SQL Password",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        ).place(x=42, y=258)

        self.password_entry = ctk.CTkEntry(
            self.login_card,
            textvariable=self.password_var,
            width=385,
            height=44,
            show="*",
            corner_radius=14,
            border_color=COLOR_BORDER,
            fg_color="#FFFFFF",
            text_color=COLOR_TEXT,
            placeholder_text="Enter password",
            placeholder_text_color="#8AA5B2",
            font=ctk.CTkFont(family="Segoe UI", size=13)
        )
        self.password_entry.place(x=42, y=286)
        self.password_entry.focus()

        self.show_password_var = tk.BooleanVar(value=False)

        self.show_password_checkbox = ctk.CTkCheckBox(
            self.login_card,
            text="Show password",
            variable=self.show_password_var,
            command=self.toggle_password_visibility,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_DARK,
            text_color=COLOR_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.show_password_checkbox.place(x=42, y=340)

        self.connect_button = ctk.CTkButton(
            self.login_card,
            text="Connect",
            width=160,
            height=44,
            corner_radius=16,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_DARK,
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.connect
        )
        self.connect_button.place(x=267, y=338)

        self.status_label = ctk.CTkLabel(
            self.login_card,
            text="Ready.",
            text_color=COLOR_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.status_label.place(x=42, y=388)

        self.bind("<Return>", lambda event: self.connect())

    def animate_login_card(self):
        target_x = 310

        if self.card_x_position < target_x:
            self.card_x_position += 24
            if self.card_x_position > target_x:
                self.card_x_position = target_x

            self.login_card.place(x=self.card_x_position, y=60)
            self.after(12, self.animate_login_card)

    def toggle_password_visibility(self):
        if self.show_password_var.get():
            self.password_entry.configure(show="")
        else:
            self.password_entry.configure(show="*")

    def pulse_button(self, state):
        if state:
            self.connect_button.configure(text="Connecting...", fg_color=COLOR_DARK_BLUE)
            self.status_label.configure(text="Connecting to Azure SQL...", text_color=COLOR_PRIMARY_DARK)
        else:
            self.connect_button.configure(text="Connect", fg_color=COLOR_PRIMARY)

    def connect(self):
        password = self.password_var.get().strip()

        if not password:
            messagebox.showwarning("Missing Password", "Enter the Azure SQL password.")
            return

        try:
            self.pulse_button(True)
            self.update_idletasks()

            self.db_manager = DatabaseManager(password)
            self.db_manager.connect()
            self.db_manager.create_table_if_missing()

            self.status_label.configure(text="Connection successful. Opening dashboard...", text_color=COLOR_SUCCESS)
            self.after(650, self.open_main_window)

        except Exception as e:
            self.pulse_button(False)
            self.status_label.configure(text="Connection failed.", text_color=COLOR_DANGER)
            messagebox.showerror(
                "Connection Failed",
                f"Could not connect to Azure SQL.\n\nError:\n{e}"
            )

    def open_main_window(self):
        self.destroy()
        app = GatewayAdditionLogsApp(self.db_manager)
        app.mainloop()


# ============================================================
# MAIN APPLICATION WINDOW
# ============================================================

class GatewayAdditionLogsApp(ctk.CTk):
    def __init__(self, db_manager):
        super().__init__()

        self.db = db_manager
        self.selected_log_id = None

        self.title("Gateway Addition Logs Manager")
        self.geometry("1320x850")
        self.minsize(1180, 760)
        self.configure(fg_color=COLOR_BACKGROUND)

        self.sidebar_visible = True
        self.sidebar_width = 250

        self.configure_treeview_style()
        self.build_ui()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def configure_treeview_style(self):
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            background="#FFFFFF",
            foreground=COLOR_TEXT,
            rowheight=32,
            fieldbackground="#FFFFFF",
            font=("Segoe UI", 9)
        )

        style.configure(
            "Treeview.Heading",
            background=COLOR_PRIMARY_LIGHT,
            foreground=COLOR_TEXT,
            font=("Segoe UI", 9, "bold")
        )

        style.map(
            "Treeview",
            background=[("selected", COLOR_PRIMARY)],
            foreground=[("selected", "#FFFFFF")]
        )

    def build_ui(self):
        self.build_sidebar()
        self.build_main_area()

    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=self.sidebar_width,
            corner_radius=0,
            fg_color=COLOR_PRIMARY
        )
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(
            self.sidebar,
            text="AQS",
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold")
        ).pack(anchor="w", padx=28, pady=(35, 4))

        ctk.CTkLabel(
            self.sidebar,
            text="Gateway Log Console",
            text_color="#EAF7FF",
            font=ctk.CTkFont(family="Segoe UI", size=13)
        ).pack(anchor="w", padx=28, pady=(0, 32))

        self.sidebar_status_card = ctk.CTkFrame(
            self.sidebar,
            width=200,
            height=110,
            fg_color="#8BD8F3",
            corner_radius=20
        )
        self.sidebar_status_card.pack(padx=24, pady=(0, 25))

        ctk.CTkLabel(
            self.sidebar_status_card,
            text="Connected",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
        ).place(x=20, y=20)

        ctk.CTkLabel(
            self.sidebar_status_card,
            text=AZURE_SQL_DATABASE,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=12)
        ).place(x=20, y=56)

        self.nav_form_button = ctk.CTkButton(
            self.sidebar,
            text="Gateway Form",
            width=200,
            height=44,
            corner_radius=14,
            fg_color="#FFFFFF",
            hover_color=COLOR_PRIMARY_LIGHT,
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.focus_form
        )
        self.nav_form_button.pack(padx=24, pady=8)

        self.nav_search_button = ctk.CTkButton(
            self.sidebar,
            text="Search Records",
            width=200,
            height=44,
            corner_radius=14,
            fg_color="#FFFFFF",
            hover_color=COLOR_PRIMARY_LIGHT,
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.open_search_window
        )
        self.nav_search_button.pack(padx=24, pady=8)

        self.nav_clear_button = ctk.CTkButton(
            self.sidebar,
            text="Clear Form",
            width=200,
            height=44,
            corner_radius=14,
            fg_color="#FFFFFF",
            hover_color=COLOR_PRIMARY_LIGHT,
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.clear_form
        )
        self.nav_clear_button.pack(padx=24, pady=8)

        self.hide_sidebar_button = ctk.CTkButton(
            self.sidebar,
            text="Collapse Panel",
            width=200,
            height=38,
            corner_radius=14,
            fg_color=COLOR_PRIMARY_DARK,
            hover_color=COLOR_DARK_BLUE,
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.animate_sidebar_toggle
        )
        self.hide_sidebar_button.pack(side="bottom", padx=24, pady=28)

    def animate_sidebar_toggle(self):
        if self.sidebar_visible:
            self.animate_sidebar_collapse()
        else:
            self.animate_sidebar_expand()

    def animate_sidebar_collapse(self):
        current_width = self.sidebar.winfo_width()

        if current_width > 70:
            current_width -= 18
            if current_width < 70:
                current_width = 70

            self.sidebar.configure(width=current_width)
            self.sidebar.pack_propagate(False)
            self.after(10, self.animate_sidebar_collapse)
        else:
            self.sidebar_visible = False
            self.hide_sidebar_button.configure(text="Expand")
            self.nav_form_button.configure(text="Form", width=54)
            self.nav_search_button.configure(text="Search", width=54)
            self.nav_clear_button.configure(text="Clear", width=54)

    def animate_sidebar_expand(self):
        current_width = self.sidebar.winfo_width()

        if current_width < self.sidebar_width:
            current_width += 18
            if current_width > self.sidebar_width:
                current_width = self.sidebar_width

            self.sidebar.configure(width=current_width)
            self.sidebar.pack_propagate(False)
            self.after(10, self.animate_sidebar_expand)
        else:
            self.sidebar_visible = True
            self.hide_sidebar_button.configure(text="Collapse Panel")
            self.nav_form_button.configure(text="Gateway Form", width=200)
            self.nav_search_button.configure(text="Search Records", width=200)
            self.nav_clear_button.configure(text="Clear Form", width=200)

    def build_main_area(self):
        self.main_area = ctk.CTkFrame(
            self,
            fg_color=COLOR_BACKGROUND,
            corner_radius=0
        )
        self.main_area.pack(side="left", fill="both", expand=True)

        self.header_frame = ctk.CTkFrame(
            self.main_area,
            fg_color=COLOR_BACKGROUND,
            corner_radius=0
        )
        self.header_frame.pack(fill="x", padx=30, pady=(25, 12))

        ctk.CTkLabel(
            self.header_frame,
            text="Gateway Addition Logs",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            self.header_frame,
            text="Record gateway programming, SIM status, firmware state, deployment purpose, and intended user.",
            text_color=COLOR_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=14)
        ).pack(anchor="w", pady=(4, 0))

        self.build_stats_strip()
        self.build_form_card()
        self.build_action_bar()

    def build_stats_strip(self):
        self.stats_strip = ctk.CTkFrame(
            self.main_area,
            fg_color=COLOR_BACKGROUND,
            corner_radius=0
        )
        self.stats_strip.pack(fill="x", padx=30, pady=(0, 12))

        self.selected_card = ctk.CTkFrame(
            self.stats_strip,
            width=260,
            height=82,
            fg_color=COLOR_CARD,
            border_color=COLOR_BORDER,
            border_width=2,
            corner_radius=22
        )
        self.selected_card.pack(side="left", padx=(0, 14))
        self.selected_card.pack_propagate(False)

        ctk.CTkLabel(
            self.selected_card,
            text="Current Mode",
            text_color=COLOR_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        ).pack(anchor="w", padx=22, pady=(14, 0))

        self.selected_record_label = ctk.CTkLabel(
            self.selected_card,
            text="New Record",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
        )
        self.selected_record_label.pack(anchor="w", padx=22, pady=(2, 0))

        self.database_card = ctk.CTkFrame(
            self.stats_strip,
            width=330,
            height=82,
            fg_color=COLOR_CARD,
            border_color=COLOR_BORDER,
            border_width=2,
            corner_radius=22
        )
        self.database_card.pack(side="left", padx=(0, 14))
        self.database_card.pack_propagate(False)

        ctk.CTkLabel(
            self.database_card,
            text="Database",
            text_color=COLOR_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        ).pack(anchor="w", padx=22, pady=(14, 0))

        ctk.CTkLabel(
            self.database_card,
            text=f"{AZURE_SQL_SERVER} / {AZURE_SQL_DATABASE}",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        ).pack(anchor="w", padx=22, pady=(5, 0))

    def build_form_card(self):
        self.form_card = ctk.CTkFrame(
            self.main_area,
            fg_color=COLOR_CARD,
            border_color=COLOR_BORDER,
            border_width=2,
            corner_radius=28
        )
        self.form_card.pack(fill="both", expand=True, padx=30, pady=(0, 12))

        self.form_scroll = ctk.CTkScrollableFrame(
            self.form_card,
            fg_color=COLOR_CARD,
            corner_radius=24
        )
        self.form_scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            self.form_scroll,
            text="Gateway Programming Form",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold")
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=8, pady=(4, 18))

        self.gateway_id_var = tk.StringVar()
        self.programmed_by_var = tk.StringVar()
        self.iccid_var = tk.StringVar()
        self.ble_mode_var = tk.StringVar(value="Release")
        self.lte_firmware_status_var = tk.StringVar(value="New")
        self.quality_check_var = tk.StringVar(value="Yes")
        self.modem_firmware_version_var = tk.StringVar()
        self.sim_provider_var = tk.StringVar(value="Bell")
        self.data_limit_var = tk.StringVar(value="Yes")
        self.in_force_date_var = tk.StringVar(value=str(date.today()))
        self.purpose_var = tk.StringVar(value="Deployment")
        self.usage_scope_var = tk.StringVar(value="External")
        self.intended_user_var = tk.StringVar()

        fields = [
            {
                "label": "Gateway ID",
                "var": self.gateway_id_var,
                "type": "entry",
                "placeholder": "Example: aqsdevice97",
                "required": True
            },
            {
                "label": "Programmed by (Name)",
                "var": self.programmed_by_var,
                "type": "entry",
                "placeholder": "Example: Kirolos Sedra",
                "required": True
            },
            {
                "label": "ICCID",
                "var": self.iccid_var,
                "type": "entry",
                "placeholder": "SIM ICCID",
                "required": False
            },
            {
                "label": "BLE in Debug or Release?",
                "var": self.ble_mode_var,
                "type": "combo",
                "values": ["Debug", "Release"],
                "required": True
            },
            {
                "label": "LTE firmware version? Old or New?",
                "var": self.lte_firmware_status_var,
                "type": "combo",
                "values": ["Old", "New"],
                "required": True
            },
            {
                "label": "Passed all quality checks?",
                "var": self.quality_check_var,
                "type": "combo",
                "values": ["Yes", "No"],
                "required": True
            },
            {
                "label": "LTE modem firmware version",
                "var": self.modem_firmware_version_var,
                "type": "entry",
                "placeholder": "Example: RM502QAEAAR13A03M4G",
                "required": False
            },
            {
                "label": "Bell or Hologram?",
                "var": self.sim_provider_var,
                "type": "combo",
                "values": ["Bell", "Hologram"],
                "required": True
            },
            {
                "label": "Data limit enforced or not?",
                "var": self.data_limit_var,
                "type": "combo",
                "values": ["Yes", "No"],
                "required": True
            },
            {
                "label": "In Force Date / Day of Programming",
                "var": self.in_force_date_var,
                "type": "date",
                "placeholder": "YYYY-MM-DD",
                "required": True
            },
            {
                "label": "Deployment or Testing?",
                "var": self.purpose_var,
                "type": "combo",
                "values": ["Deployment", "Testing"],
                "required": True
            },
            {
                "label": "Internal or External?",
                "var": self.usage_scope_var,
                "type": "combo",
                "values": ["Internal", "External"],
                "required": True
            },
            {
                "label": "Intended User",
                "var": self.intended_user_var,
                "type": "entry",
                "placeholder": "External: company name | Internal: person's name",
                "required": True
            }
        ]

        left_fields = fields[:7]
        right_fields = fields[7:]

        self.create_field_column(self.form_scroll, left_fields, start_col=0, start_row=1)
        self.create_field_column(self.form_scroll, right_fields, start_col=2, start_row=1)

        self.note_box = ctk.CTkFrame(
            self.form_scroll,
            fg_color=COLOR_PRIMARY_LIGHT,
            corner_radius=18
        )
        self.note_box.grid(row=9, column=0, columnspan=4, sticky="ew", padx=8, pady=(18, 8))

        ctk.CTkLabel(
            self.note_box,
            text="Rule: External means the intended user is a company name. Internal means the intended user is the internal person using the gateway.",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=13)
        ).pack(anchor="w", padx=18, pady=14)

        self.form_scroll.grid_columnconfigure(1, weight=1)
        self.form_scroll.grid_columnconfigure(3, weight=1)

    def create_field_column(self, parent, fields, start_col, start_row):
        for index, field in enumerate(fields):
            row = start_row + index

            label_text = field["label"]
            if field.get("required"):
                label_text += " *"

            ctk.CTkLabel(
                parent,
                text=label_text,
                text_color=COLOR_TEXT,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
            ).grid(row=row, column=start_col, sticky="w", padx=8, pady=(8, 4))

            if field["type"] == "entry":
                widget = ctk.CTkEntry(
                    parent,
                    textvariable=field["var"],
                    placeholder_text=field.get("placeholder", ""),
                    width=310,
                    height=42,
                    corner_radius=14,
                    border_color=COLOR_BORDER,
                    fg_color="#FFFFFF",
                    text_color=COLOR_TEXT,
                    placeholder_text_color="#8AA5B2",
                    font=ctk.CTkFont(family="Segoe UI", size=13)
                )
                widget.grid(row=row, column=start_col + 1, sticky="ew", padx=(8, 26), pady=(8, 4))

            elif field["type"] == "combo":
                widget = ctk.CTkComboBox(
                    parent,
                    variable=field["var"],
                    values=field["values"],
                    width=310,
                    height=42,
                    corner_radius=14,
                    border_color=COLOR_BORDER,
                    fg_color="#FFFFFF",
                    button_color=COLOR_PRIMARY,
                    button_hover_color=COLOR_PRIMARY_DARK,
                    dropdown_fg_color="#FFFFFF",
                    dropdown_hover_color=COLOR_PRIMARY_LIGHT,
                    text_color=COLOR_TEXT,
                    font=ctk.CTkFont(family="Segoe UI", size=13)
                )
                widget.grid(row=row, column=start_col + 1, sticky="ew", padx=(8, 26), pady=(8, 4))

            elif field["type"] == "date":
                date_frame = ctk.CTkFrame(
                    parent,
                    fg_color=COLOR_CARD,
                    corner_radius=0
                )
                date_frame.grid(row=row, column=start_col + 1, sticky="ew", padx=(8, 26), pady=(8, 4))

                widget = ctk.CTkEntry(
                    date_frame,
                    textvariable=field["var"],
                    placeholder_text=field.get("placeholder", ""),
                    width=195,
                    height=42,
                    corner_radius=14,
                    border_color=COLOR_BORDER,
                    fg_color="#FFFFFF",
                    text_color=COLOR_TEXT,
                    placeholder_text_color="#8AA5B2",
                    font=ctk.CTkFont(family="Segoe UI", size=13)
                )
                widget.pack(side="left", fill="x", expand=True)

                today_button = ctk.CTkButton(
                    date_frame,
                    text="Today",
                    width=90,
                    height=42,
                    corner_radius=14,
                    fg_color=COLOR_PRIMARY_LIGHT,
                    hover_color="#C6EDFA",
                    text_color=COLOR_TEXT,
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                    command=lambda var=field["var"]: var.set(str(date.today()))
                )
                today_button.pack(side="left", padx=(8, 0))

    def build_action_bar(self):
        self.action_bar = ctk.CTkFrame(
            self.main_area,
            fg_color=COLOR_BACKGROUND,
            corner_radius=0
        )
        self.action_bar.pack(fill="x", padx=30, pady=(0, 25))

        self.save_button = ctk.CTkButton(
            self.action_bar,
            text="Save New Record",
            width=175,
            height=46,
            corner_radius=16,
            fg_color=COLOR_SUCCESS,
            hover_color="#21867A",
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.save_new_record
        )
        self.save_button.pack(side="left", padx=(0, 10))

        self.update_button = ctk.CTkButton(
            self.action_bar,
            text="Update Selected",
            width=175,
            height=46,
            corner_radius=16,
            fg_color=COLOR_WARNING,
            hover_color="#E78B38",
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.update_selected_record
        )
        self.update_button.pack(side="left", padx=(0, 10))

        self.clear_button = ctk.CTkButton(
            self.action_bar,
            text="Clear Form",
            width=150,
            height=46,
            corner_radius=16,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_DARK,
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.clear_form
        )
        self.clear_button.pack(side="left", padx=(0, 10))

        self.search_button = ctk.CTkButton(
            self.action_bar,
            text="Search / View Records",
            width=210,
            height=46,
            corner_radius=16,
            fg_color=COLOR_DARK_BLUE,
            hover_color="#254B61",
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.open_search_window
        )
        self.search_button.pack(side="right")

    def focus_form(self):
        self.form_card.focus_set()

    def collect_form_data(self):
        gateway_id = self.gateway_id_var.get().strip()
        programmed_by = self.programmed_by_var.get().strip()
        iccid = self.iccid_var.get().strip()
        ble_mode = self.ble_mode_var.get().strip()
        lte_firmware_status = self.lte_firmware_status_var.get().strip()
        quality_check = self.quality_check_var.get().strip()
        modem_firmware_version = self.modem_firmware_version_var.get().strip()
        sim_provider = self.sim_provider_var.get().strip()
        data_limit = self.data_limit_var.get().strip()
        in_force_date = self.in_force_date_var.get().strip()
        purpose = self.purpose_var.get().strip()
        usage_scope = self.usage_scope_var.get().strip()
        intended_user = self.intended_user_var.get().strip()

        required_fields = {
            "Gateway ID": gateway_id,
            "Programmed by": programmed_by,
            "BLE build mode": ble_mode,
            "LTE firmware status": lte_firmware_status,
            "Quality check result": quality_check,
            "SIM provider": sim_provider,
            "Data limit enforced": data_limit,
            "In Force Date": in_force_date,
            "Purpose": purpose,
            "Usage scope": usage_scope,
            "Intended user": intended_user
        }

        missing = [name for name, value in required_fields.items() if not value]

        if missing:
            raise ValueError("Missing required fields:\n\n" + "\n".join(missing))

        try:
            parsed_date = datetime.strptime(in_force_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("In Force Date must use this format: YYYY-MM-DD")

        if ble_mode not in ["Debug", "Release"]:
            raise ValueError("BLE build mode must be Debug or Release.")

        if lte_firmware_status not in ["Old", "New"]:
            raise ValueError("LTE firmware status must be Old or New.")

        if quality_check not in ["Yes", "No"]:
            raise ValueError("Passed all quality checks must be Yes or No.")

        if sim_provider not in ["Bell", "Hologram"]:
            raise ValueError("SIM provider must be Bell or Hologram.")

        if data_limit not in ["Yes", "No"]:
            raise ValueError("Data limit enforced must be Yes or No.")

        if purpose not in ["Deployment", "Testing"]:
            raise ValueError("Purpose must be Deployment or Testing.")

        if usage_scope not in ["Internal", "External"]:
            raise ValueError("Usage scope must be Internal or External.")

        return {
            "GatewayId": gateway_id,
            "ProgrammedByName": programmed_by,
            "ICCID": iccid if iccid else None,
            "BLEBuildMode": ble_mode,
            "LTEFirmwareStatus": lte_firmware_status,
            "PassedAllQualityChecks": 1 if quality_check == "Yes" else 0,
            "LTEModemFirmwareVersion": modem_firmware_version if modem_firmware_version else None,
            "SIMProvider": sim_provider,
            "DataLimitEnforced": 1 if data_limit == "Yes" else 0,
            "InForceDate": parsed_date,
            "Purpose": purpose,
            "UsageScope": usage_scope,
            "IntendedUser": intended_user
        }

    def animate_save_button_success(self):
        original_text = self.save_button.cget("text")
        original_color = self.save_button.cget("fg_color")

        self.save_button.configure(text="Saved ✓", fg_color=COLOR_PRIMARY_DARK)
        self.after(
            850,
            lambda: self.save_button.configure(text=original_text, fg_color=original_color)
        )

    def animate_update_button_success(self):
        original_text = self.update_button.cget("text")
        original_color = self.update_button.cget("fg_color")

        self.update_button.configure(text="Updated ✓", fg_color=COLOR_SUCCESS)
        self.after(
            850,
            lambda: self.update_button.configure(text=original_text, fg_color=original_color)
        )

    def save_new_record(self):
        try:
            data = self.collect_form_data()
            self.db.insert_gateway_log(data)

            self.animate_save_button_success()
            messagebox.showinfo("Saved", "Gateway addition log saved successfully.")
            self.clear_form()

        except Exception as e:
            messagebox.showerror("Save Failed", str(e))

    def update_selected_record(self):
        if self.selected_log_id is None:
            messagebox.showwarning(
                "No Record Selected",
                "Load a record from the search window before updating."
            )
            return

        try:
            data = self.collect_form_data()
            self.db.update_gateway_log(self.selected_log_id, data)

            self.animate_update_button_success()
            messagebox.showinfo("Updated", "Selected gateway addition log updated successfully.")
            self.clear_form()

        except Exception as e:
            messagebox.showerror("Update Failed", str(e))

    def clear_form(self):
        self.selected_log_id = None

        self.gateway_id_var.set("")
        self.programmed_by_var.set("")
        self.iccid_var.set("")
        self.ble_mode_var.set("Release")
        self.lte_firmware_status_var.set("New")
        self.quality_check_var.set("Yes")
        self.modem_firmware_version_var.set("")
        self.sim_provider_var.set("Bell")
        self.data_limit_var.set("Yes")
        self.in_force_date_var.set(str(date.today()))
        self.purpose_var.set("Deployment")
        self.usage_scope_var.set("External")
        self.intended_user_var.set("")

        self.selected_record_label.configure(text="New Record", text_color=COLOR_TEXT)

    def load_record_into_form(self, row):
        self.selected_log_id = row.LogId

        self.gateway_id_var.set(row.GatewayId if row.GatewayId is not None else "")
        self.programmed_by_var.set(row.ProgrammedByName if row.ProgrammedByName is not None else "")
        self.iccid_var.set(row.ICCID if row.ICCID is not None else "")
        self.ble_mode_var.set(row.BLEBuildMode if row.BLEBuildMode is not None else "Release")
        self.lte_firmware_status_var.set(row.LTEFirmwareStatus if row.LTEFirmwareStatus is not None else "New")
        self.quality_check_var.set("Yes" if row.PassedAllQualityChecks else "No")
        self.modem_firmware_version_var.set(row.LTEModemFirmwareVersion if row.LTEModemFirmwareVersion is not None else "")
        self.sim_provider_var.set(row.SIMProvider if row.SIMProvider is not None else "Bell")
        self.data_limit_var.set("Yes" if row.DataLimitEnforced else "No")
        self.in_force_date_var.set(str(row.InForceDate) if row.InForceDate is not None else str(date.today()))
        self.purpose_var.set(row.Purpose if row.Purpose is not None else "Deployment")
        self.usage_scope_var.set(row.UsageScope if row.UsageScope is not None else "External")
        self.intended_user_var.set(row.IntendedUser if row.IntendedUser is not None else "")

        self.selected_record_label.configure(
            text=f"Editing LogId {self.selected_log_id}",
            text_color="#8A5A00"
        )

    def open_search_window(self):
        SearchWindow(self, self.db, self.load_record_into_form)

    def on_close(self):
        try:
            self.db.close()
        except Exception:
            pass

        self.destroy()


# ============================================================
# MODERN SEARCH WINDOW
# ============================================================

class SearchWindow(ctk.CTkToplevel):
    def __init__(self, parent, db_manager, load_callback):
        super().__init__(parent)

        self.parent = parent
        self.db = db_manager
        self.load_callback = load_callback
        self.rows_cache = []

        self.title("Search Gateway Addition Logs")
        self.geometry("1540x760")
        self.minsize(1250, 620)
        self.configure(fg_color=COLOR_BACKGROUND)

        self.window_y_position = -760

        self.configure_treeview_style()
        self.build_ui()
        self.refresh_records()
        self.animate_window_drop()

        self.grab_set()

    def animate_window_drop(self):
        target_y = 60

        if self.window_y_position < target_y:
            self.window_y_position += 35
            if self.window_y_position > target_y:
                self.window_y_position = target_y

            try:
                self.geometry(f"1540x760+120+{self.window_y_position}")
            except tk.TclError:
                return

            self.after(10, self.animate_window_drop)

    def configure_treeview_style(self):
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Modern.Treeview",
            background="#FFFFFF",
            foreground=COLOR_TEXT,
            rowheight=34,
            fieldbackground="#FFFFFF",
            borderwidth=0,
            font=("Segoe UI", 9)
        )

        style.configure(
            "Modern.Treeview.Heading",
            background=COLOR_PRIMARY_LIGHT,
            foreground=COLOR_TEXT,
            relief="flat",
            font=("Segoe UI", 9, "bold")
        )

        style.map(
            "Modern.Treeview",
            background=[("selected", COLOR_PRIMARY)],
            foreground=[("selected", "#FFFFFF")]
        )

    def build_ui(self):
        self.header = ctk.CTkFrame(
            self,
            fg_color=COLOR_BACKGROUND,
            corner_radius=0
        )
        self.header.pack(fill="x", padx=26, pady=(24, 10))

        ctk.CTkLabel(
            self.header,
            text="Search / View Gateway Records",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            self.header,
            text="Search by gateway ID, ICCID, programmer name, SIM provider, purpose, scope, or intended user.",
            text_color=COLOR_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=13)
        ).pack(anchor="w", pady=(3, 0))

        self.search_card = ctk.CTkFrame(
            self,
            fg_color=COLOR_CARD,
            border_color=COLOR_BORDER,
            border_width=2,
            corner_radius=24
        )
        self.search_card.pack(fill="x", padx=26, pady=10)

        self.search_var = tk.StringVar()

        self.search_entry = ctk.CTkEntry(
            self.search_card,
            textvariable=self.search_var,
            width=520,
            height=44,
            corner_radius=16,
            border_color=COLOR_BORDER,
            fg_color="#FFFFFF",
            text_color=COLOR_TEXT,
            placeholder_text="Search records...",
            placeholder_text_color="#8AA5B2",
            font=ctk.CTkFont(family="Segoe UI", size=13)
        )
        self.search_entry.pack(side="left", padx=(20, 10), pady=16)
        self.search_entry.bind("<Return>", lambda event: self.refresh_records())

        self.search_button = ctk.CTkButton(
            self.search_card,
            text="Search",
            width=130,
            height=44,
            corner_radius=16,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_DARK,
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.refresh_records
        )
        self.search_button.pack(side="left", padx=8, pady=16)

        self.show_all_button = ctk.CTkButton(
            self.search_card,
            text="Show All",
            width=130,
            height=44,
            corner_radius=16,
            fg_color=COLOR_DARK_BLUE,
            hover_color="#254B61",
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.show_all
        )
        self.show_all_button.pack(side="left", padx=8, pady=16)

        self.status_label = ctk.CTkLabel(
            self.search_card,
            text="",
            text_color=COLOR_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=13)
        )
        self.status_label.pack(side="right", padx=22)

        self.table_card = ctk.CTkFrame(
            self,
            fg_color=COLOR_CARD,
            border_color=COLOR_BORDER,
            border_width=2,
            corner_radius=24
        )
        self.table_card.pack(fill="both", expand=True, padx=26, pady=(4, 12))

        self.table_container = tk.Frame(
            self.table_card,
            bg="#FFFFFF"
        )
        self.table_container.pack(fill="both", expand=True, padx=16, pady=16)

        columns = [
            "LogId",
            "GatewayId",
            "ProgrammedByName",
            "ICCID",
            "BLEBuildMode",
            "LTEFirmwareStatus",
            "PassedAllQualityChecks",
            "LTEModemFirmwareVersion",
            "SIMProvider",
            "DataLimitEnforced",
            "InForceDate",
            "Purpose",
            "UsageScope",
            "IntendedUser",
            "CreatedAt",
            "UpdatedAt"
        ]

        self.tree = ttk.Treeview(
            self.table_container,
            columns=columns,
            show="headings",
            style="Modern.Treeview"
        )

        readable_headers = {
            "LogId": "Log ID",
            "GatewayId": "Gateway ID",
            "ProgrammedByName": "Programmed By",
            "ICCID": "ICCID",
            "BLEBuildMode": "BLE Mode",
            "LTEFirmwareStatus": "LTE FW Status",
            "PassedAllQualityChecks": "Passed QC",
            "LTEModemFirmwareVersion": "LTE Modem FW",
            "SIMProvider": "SIM Provider",
            "DataLimitEnforced": "Data Limit",
            "InForceDate": "In Force Date",
            "Purpose": "Purpose",
            "UsageScope": "Scope",
            "IntendedUser": "Intended User",
            "CreatedAt": "Created At",
            "UpdatedAt": "Updated At"
        }

        column_widths = {
            "LogId": 70,
            "GatewayId": 130,
            "ProgrammedByName": 160,
            "ICCID": 190,
            "BLEBuildMode": 115,
            "LTEFirmwareStatus": 130,
            "PassedAllQualityChecks": 120,
            "LTEModemFirmwareVersion": 180,
            "SIMProvider": 120,
            "DataLimitEnforced": 120,
            "InForceDate": 130,
            "Purpose": 120,
            "UsageScope": 120,
            "IntendedUser": 190,
            "CreatedAt": 190,
            "UpdatedAt": 190
        }

        for col in columns:
            self.tree.heading(col, text=readable_headers[col])
            self.tree.column(col, width=column_widths[col], anchor="w")

        y_scroll = ttk.Scrollbar(self.table_container, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(self.table_container, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        self.table_container.grid_rowconfigure(0, weight=1)
        self.table_container.grid_columnconfigure(0, weight=1)

        self.action_bar = ctk.CTkFrame(
            self,
            fg_color=COLOR_BACKGROUND,
            corner_radius=0
        )
        self.action_bar.pack(fill="x", padx=26, pady=(0, 20))

        self.load_button = ctk.CTkButton(
            self.action_bar,
            text="Load Selected Into Form",
            width=220,
            height=44,
            corner_radius=16,
            fg_color=COLOR_SUCCESS,
            hover_color="#21867A",
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.load_selected
        )
        self.load_button.pack(side="left", padx=(0, 10))

        self.delete_button = ctk.CTkButton(
            self.action_bar,
            text="Delete Selected",
            width=160,
            height=44,
            corner_radius=16,
            fg_color=COLOR_DANGER,
            hover_color=COLOR_DANGER_DARK,
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.delete_selected
        )
        self.delete_button.pack(side="left", padx=(0, 10))

        self.refresh_button = ctk.CTkButton(
            self.action_bar,
            text="Refresh",
            width=130,
            height=44,
            corner_radius=16,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_DARK,
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.refresh_records
        )
        self.refresh_button.pack(side="left", padx=(0, 10))

        self.close_button = ctk.CTkButton(
            self.action_bar,
            text="Close",
            width=130,
            height=44,
            corner_radius=16,
            fg_color=COLOR_DARK_BLUE,
            hover_color="#254B61",
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.destroy
        )
        self.close_button.pack(side="right")

    def show_all(self):
        self.search_var.set("")
        self.refresh_records()

    def refresh_records(self):
        try:
            search_text = self.search_var.get().strip()
            rows = self.db.search_gateway_logs(search_text)
            self.rows_cache = rows

            for item in self.tree.get_children():
                self.tree.delete(item)

            for index, row in enumerate(rows):
                values = [
                    row.LogId,
                    row.GatewayId,
                    row.ProgrammedByName,
                    row.ICCID,
                    row.BLEBuildMode,
                    row.LTEFirmwareStatus,
                    "Yes" if row.PassedAllQualityChecks else "No",
                    row.LTEModemFirmwareVersion,
                    row.SIMProvider,
                    "Yes" if row.DataLimitEnforced else "No",
                    str(row.InForceDate) if row.InForceDate is not None else "",
                    row.Purpose,
                    row.UsageScope,
                    row.IntendedUser,
                    str(row.CreatedAt) if row.CreatedAt is not None else "",
                    str(row.UpdatedAt) if row.UpdatedAt is not None else ""
                ]

                tag_name = "evenrow" if index % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=values, tags=(tag_name,))

            self.tree.tag_configure("evenrow", background="#FFFFFF")
            self.tree.tag_configure("oddrow", background="#F3FBFF")

            self.status_label.configure(text=f"{len(rows)} record(s) shown")

        except Exception as e:
            messagebox.showerror("Search Failed", str(e))

    def get_selected_log_id(self):
        selected_items = self.tree.selection()

        if not selected_items:
            messagebox.showwarning("No Selection", "Select a record first.")
            return None

        selected_item = selected_items[0]
        values = self.tree.item(selected_item, "values")

        if not values:
            messagebox.showwarning("Invalid Selection", "Selected row has no data.")
            return None

        return int(values[0])

    def get_selected_row_object(self):
        selected_log_id = self.get_selected_log_id()

        if selected_log_id is None:
            return None

        for row in self.rows_cache:
            if int(row.LogId) == selected_log_id:
                return row

        messagebox.showerror("Record Not Found", "Selected record was not found in the loaded cache.")
        return None

    def load_selected(self):
        row = self.get_selected_row_object()

        if row is None:
            return

        self.load_callback(row)
        self.destroy()

    def delete_selected(self):
        selected_log_id = self.get_selected_log_id()

        if selected_log_id is None:
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete LogId {selected_log_id}?\n\nThis cannot be undone."
        )

        if not confirm:
            return

        try:
            self.db.delete_gateway_log(selected_log_id)
            messagebox.showinfo("Deleted", f"LogId {selected_log_id} deleted successfully.")
            self.refresh_records()

        except Exception as e:
            messagebox.showerror("Delete Failed", str(e))


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def main():
    app = LoginWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
