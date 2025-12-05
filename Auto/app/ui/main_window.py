# Main Window for Orbita Multi-Profile Automation

import os
import subprocess
import time
import psutil
from typing import List, Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QSpinBox, QGroupBox, QMessageBox, QProgressBar,
    QHeaderView, QAbstractItemView, QCheckBox, QTextEdit, QTabWidget,
    QFrame, QListWidget, QFormLayout, QApplication, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor

from app.data.profile_repository import ProfileRepository
from app.data.profile_models import Profile
from app.core.profile_manager import ProfileManager
from app.core.fingerprint_generator import FingerprintGenerator
from app.core.browser_manager import BrowserManager
from app.core.session_manager import SessionManager
from app.core.backup_manager import BackupManager
from app.core.script_manager import ScriptManager
from app.core.automation_executor import AutomationExecutor
from app.ui.widgets import StatusBadge, StatsCard, ActionButton


class ProfileEditDialog(QDialog):
    """Dialog for editing profile information."""
    
    def __init__(self, profile=None, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.setWindowTitle("Edit Profile" if profile else "New Profile")
        self.setMinimumWidth(400)
        self._init_ui()
        if profile:
            self._load_profile_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        form = QFormLayout()
        form.setSpacing(10)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Profile name")
        form.addRow("Name:", self.name_edit)
        
        self.proxy_edit = QLineEdit()
        self.proxy_edit.setPlaceholderText("host:port:user:pass or host:port")
        form.addRow("Proxy:", self.proxy_edit)
        
        self.proxymode_combo = QComboBox()
        self.proxymode_combo.addItems(["none", "http", "socks5"])
        form.addRow("Proxy Mode:", self.proxymode_combo)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Facebook username")
        form.addRow("Username FB:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Facebook password")
        self.password_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Password FB:", self.password_edit)
        
        self.ma2fa_edit = QLineEdit()
        self.ma2fa_edit.setPlaceholderText("2FA secret key")
        form.addRow("2FA Key:", self.ma2fa_edit)
        
        self.group_edit = QLineEdit()
        self.group_edit.setPlaceholderText("Group name")
        form.addRow("Group:", self.group_edit)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Notes...")
        form.addRow("Notes:", self.notes_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _load_profile_data(self):
        if not self.profile:
            return
        data = self.profile.data
        self.name_edit.setText(data.name or "")
        self.proxy_edit.setText(data.proxy or "")
        self.proxymode_combo.setCurrentText(data.proxymode or "none")
        self.username_edit.setText(data.username_fb or "")
        self.password_edit.setText(data.password_fb or "")
        self.ma2fa_edit.setText(data.ma2fa or "")
        self.group_edit.setText(data.group_profile or "")
        self.notes_edit.setPlainText(data.notes or "")
    
    def get_data(self) -> dict:
        return {
            'name': self.name_edit.text().strip(),
            'proxy': self.proxy_edit.text().strip(),
            'proxymode': self.proxymode_combo.currentText(),
            'username_fb': self.username_edit.text().strip(),
            'password_fb': self.password_edit.text().strip(),
            'ma2fa': self.ma2fa_edit.text().strip(),
            'group_profile': self.group_edit.text().strip(),
            'notes': self.notes_edit.toPlainText().strip()
        }


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Orbita Multi-Profile Automation")
        self.setMinimumSize(1400, 800)
        
        self._init_managers()
        self._init_ui()
        self._load_profiles()
        self._start_system_monitor()
    
    def _init_managers(self):
        """Initialize all manager components."""
        self.repository = ProfileRepository(
            db_path="data/data.db",
            app_db_path="data/app_data.db",
            profile_dir="profile"
        )
        self.fingerprint_gen = FingerprintGenerator()
        self.profile_manager = ProfileManager(
            repository=self.repository,
            generator=self.fingerprint_gen,
            template_dir="temp"
        )
        self.browser_manager = BrowserManager(profile_manager=self.profile_manager)
        self.session_manager = SessionManager(
            browser_manager=self.browser_manager,
            max_concurrent=5
        )
        self.backup_manager = BackupManager(
            repository=self.repository,
            backup_dir="data/backup"
        )
        self.script_manager = ScriptManager()
        self.automation_executor = AutomationExecutor(self.script_manager)
        
        self.profiles: List[Profile] = []
        self.selected_profile: Optional[Profile] = None
        self.selected_script = None
        self.script_input_widgets = {}
    
    def _init_ui(self):
        """Initialize the user interface."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        self.automation_tab = self._create_automation_tab()
        self.tabs.addTab(self.automation_tab, "🤖  Automation")
        
        self.profiles_tab = self._create_profiles_tab()
        self.tabs.addTab(self.profiles_tab, "👤  Profiles")
        
        main_layout.addWidget(self.tabs)
        self.statusBar().showMessage("Ready")
    
    def _create_header(self) -> QFrame:
        """Create header with logo and system stats."""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(60)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel("🛡️ Orbita Multi-Profile")
        title.setObjectName("appTitle")
        layout.addWidget(title)
        layout.addStretch()
        
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setStyleSheet("color: #888;")
        stats_layout.addWidget(self.cpu_label)
        
        self.ram_label = QLabel("RAM: 0%")
        self.ram_label.setStyleSheet("color: #888;")
        stats_layout.addWidget(self.ram_label)
        
        self.running_label = QLabel("Running: 0")
        self.running_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        stats_layout.addWidget(self.running_label)
        
        layout.addLayout(stats_layout)
        
        theme_btn = QPushButton("🌙")
        theme_btn.setFixedSize(40, 40)
        theme_btn.setStyleSheet("border-radius: 20px;")
        layout.addWidget(theme_btn)
        
        return header

    # ==================== AUTOMATION TAB ====================
    
    def _create_automation_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        left_panel = self._create_scripts_panel()
        left_panel.setFixedWidth(320)
        layout.addWidget(left_panel)
        
        right_panel = self._create_automation_main_panel()
        layout.addWidget(right_panel)
        
        return tab
    
    def _create_scripts_panel(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 12px; }")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_label = QLabel("📜 Automation Scripts")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3; background: transparent;")
        layout.addWidget(header_label)
        
        # Scripts list from script manager
        self.scripts_list = QListWidget()
        self._load_scripts_list()
        self.scripts_list.currentRowChanged.connect(self._on_script_selected)
        layout.addWidget(self.scripts_list)
        
        # Script inputs container
        self.script_inputs_group = QGroupBox("Script Settings")
        self.script_inputs_layout = QFormLayout(self.script_inputs_group)
        self.script_inputs_layout.setSpacing(8)
        layout.addWidget(self.script_inputs_group)
        
        layout.addStretch()
        return panel
    
    def _load_scripts_list(self):
        """Load scripts from script manager."""
        self.scripts_list.clear()
        self.scripts_list.addItem("📘 No Script (Manual)")
        
        for script in self.script_manager.get_all_scripts():
            self.scripts_list.addItem(f"📗 {script.description}")
    
    def _on_script_selected(self, index: int):
        """Handle script selection."""
        # Clear previous inputs
        self._clear_script_inputs()
        
        if index == 0:
            # No script selected
            self.selected_script = None
            return
        
        # Get script (index - 1 because first item is "No Script")
        scripts = self.script_manager.get_all_scripts()
        if index - 1 < len(scripts):
            self.selected_script = scripts[index - 1]
            self._render_script_inputs(self.selected_script)
    
    def _clear_script_inputs(self):
        """Clear script input widgets."""
        while self.script_inputs_layout.count():
            item = self.script_inputs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.script_input_widgets = {}
    
    def _render_script_inputs(self, script):
        """Render input fields for a script."""
        inputs = self.script_manager.load_script_inputs(script)
        
        for inp in inputs:
            inp_type = inp.get('type', '')
            inp_name = inp.get('name', '')
            
            if inp_type == 'QLabel':
                label = QLabel(inp.get('text', ''))
                label.setWordWrap(True)
                label.setStyleSheet("color: #666; font-size: 11px;")
                self.script_inputs_layout.addRow(label)
                
            elif inp_type == 'QLineEdit':
                edit = QLineEdit()
                edit.setPlaceholderText(inp.get('placeholder', ''))
                edit.setText(inp.get('default_value', ''))
                self.script_inputs_layout.addRow(edit)
                self.script_input_widgets[inp_name] = edit
                
            elif inp_type == 'QCheckBox':
                checkbox = QCheckBox(inp.get('text', ''))
                checkbox.setChecked(inp.get('default_checked', False))
                self.script_inputs_layout.addRow(checkbox)
                self.script_input_widgets[inp_name] = checkbox
    
    def get_script_input_values(self) -> dict:
        """Get current values from script input widgets."""
        values = {}
        for name, widget in self.script_input_widgets.items():
            if isinstance(widget, QLineEdit):
                values[name] = widget.text()
            elif isinstance(widget, QCheckBox):
                values[name] = widget.isChecked()
        return values
    
    def _create_automation_main_panel(self) -> QFrame:
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.auto_platform_filter = QComboBox()
        self.auto_platform_filter.addItems(["All Platforms", "Facebook", "Instagram", "Telegram", "Zalo"])
        self.auto_platform_filter.setFixedWidth(140)
        toolbar.addWidget(self.auto_platform_filter)
        
        self.auto_status_filter = QComboBox()
        self.auto_status_filter.addItems(["All Status", "Ready", "Running", "Error", "Missing"])
        self.auto_status_filter.setFixedWidth(120)
        self.auto_status_filter.currentTextChanged.connect(self._apply_auto_filter)
        toolbar.addWidget(self.auto_status_filter)
        
        self.auto_search = QLineEdit()
        self.auto_search.setPlaceholderText("🔍 Search profiles...")
        self.auto_search.setFixedWidth(200)
        self.auto_search.textChanged.connect(self._search_auto_profiles)
        toolbar.addWidget(self.auto_search)
        toolbar.addStretch()
        
        select_all_btn = QPushButton("☑️ Select All")
        select_all_btn.clicked.connect(self._auto_select_all)
        toolbar.addWidget(select_all_btn)
        
        run_btn = QPushButton("▶️ Run Selected")
        run_btn.setObjectName("primaryBtn")
        run_btn.clicked.connect(self._run_selected_automation)
        toolbar.addWidget(run_btn)
        
        stop_btn = QPushButton("⏹️ Stop All")
        stop_btn.setObjectName("dangerBtn")
        stop_btn.clicked.connect(self._stop_all_automation)
        toolbar.addWidget(stop_btn)
        layout.addLayout(toolbar)
        
        # Stats cards
        stats_layout = QHBoxLayout()
        self.total_card = StatsCard("Total Profiles", "0")
        self.selected_card = StatsCard("Selected", "0")
        self.running_card = StatsCard("Running", "0")
        self.completed_card = StatsCard("Completed", "0")
        self.error_card = StatsCard("Errors", "0")
        for card in [self.total_card, self.selected_card, self.running_card, self.completed_card, self.error_card]:
            stats_layout.addWidget(card)
        layout.addLayout(stats_layout)
        
        # Table
        self.auto_table = QTableWidget()
        self.auto_table.setColumnCount(8)
        self.auto_table.setHorizontalHeaderLabels(["✓", "ID", "Name", "Platform", "Status", "Proxy", "Automation", "Actions"])
        self.auto_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.auto_table.setAlternatingRowColors(False)
        self.auto_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.auto_table.horizontalHeader().setStretchLastSection(True)
        self.auto_table.verticalHeader().setVisible(False)
        layout.addWidget(self.auto_table)
        
        # Footer
        footer = QHBoxLayout()
        self.auto_status_label = QLabel("Ready to run automation")
        self.auto_status_label.setStyleSheet("color: #888;")
        footer.addWidget(self.auto_status_label)
        footer.addStretch()
        self.auto_progress = QProgressBar()
        self.auto_progress.setFixedWidth(200)
        self.auto_progress.setVisible(False)
        footer.addWidget(self.auto_progress)
        layout.addLayout(footer)
        
        return panel

    # ==================== PROFILES TAB ====================
    
    def _create_profiles_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        left_panel = self._create_profiles_table_panel()
        layout.addWidget(left_panel, stretch=2)
        
        right_panel = self._create_profile_detail_panel()
        right_panel.setFixedWidth(400)
        layout.addWidget(right_panel)
        
        return tab
    
    def _create_profiles_table_panel(self) -> QFrame:
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        toolbar = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._load_profiles)
        toolbar.addWidget(refresh_btn)
        
        close_all_btn = QPushButton("❌ Close All Browsers")
        close_all_btn.setObjectName("dangerBtn")
        close_all_btn.clicked.connect(self._close_all_browsers)
        toolbar.addWidget(close_all_btn)
        
        toolbar.addStretch()
        
        self.profile_status_filter = QComboBox()
        self.profile_status_filter.addItems(["All Status", "Ready", "Running", "Error", "Missing"])
        self.profile_status_filter.currentTextChanged.connect(self._apply_profile_filter)
        toolbar.addWidget(self.profile_status_filter)
        
        self.profile_search = QLineEdit()
        self.profile_search.setPlaceholderText("🔍 Search...")
        self.profile_search.setFixedWidth(250)
        self.profile_search.textChanged.connect(self._search_profiles)
        toolbar.addWidget(self.profile_search)
        
        self.profile_count_label = QLabel("0 profiles")
        self.profile_count_label.setStyleSheet("color: #888;")
        toolbar.addWidget(self.profile_count_label)
        layout.addLayout(toolbar)
        
        self.profile_table = QTableWidget()
        self.profile_table.setColumnCount(8)
        self.profile_table.setHorizontalHeaderLabels(["ID", "Name", "Platform", "Status", "Username", "Last Run", "Proxy", "Actions"])
        self.profile_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.profile_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.profile_table.setAlternatingRowColors(False)
        self.profile_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.profile_table.horizontalHeader().setStretchLastSection(True)
        self.profile_table.verticalHeader().setVisible(False)
        self.profile_table.itemSelectionChanged.connect(self._on_profile_selected)
        layout.addWidget(self.profile_table)
        
        return panel
    
    def _create_profile_detail_panel(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 12px; }")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        self.detail_header = QLabel("Select a profile")
        self.detail_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3; background: transparent;")
        layout.addWidget(self.detail_header)
        
        self.detail_status = StatusBadge("idle")
        layout.addWidget(self.detail_status)
        
        actions_layout = QHBoxLayout()
        open_browser_btn = QPushButton("🌐 Open Browser")
        open_browser_btn.setObjectName("primaryBtn")
        open_browser_btn.clicked.connect(self._open_browser_manual)
        actions_layout.addWidget(open_browser_btn)
        
        open_folder_btn = QPushButton("📁 Folder")
        open_folder_btn.clicked.connect(self._open_profile_folder)
        actions_layout.addWidget(open_folder_btn)
        layout.addLayout(actions_layout)
        
        detail_tabs = QTabWidget()
        detail_tabs.setStyleSheet("QTabBar::tab { padding: 8px 16px; font-size: 12px; }")
        
        # Overview tab
        overview_tab = QWidget()
        overview_layout = QFormLayout(overview_tab)
        overview_layout.setSpacing(12)
        self.detail_id = QLabel("-")
        self.detail_id.setTextInteractionFlags(Qt.TextSelectableByMouse)
        overview_layout.addRow("Profile ID:", self.detail_id)
        self.detail_name = QLabel("-")
        overview_layout.addRow("Name:", self.detail_name)
        self.detail_platform = QLabel("-")
        overview_layout.addRow("Platform:", self.detail_platform)
        self.detail_username = QLabel("-")
        overview_layout.addRow("Username:", self.detail_username)
        self.detail_path = QLabel("-")
        self.detail_path.setWordWrap(True)
        self.detail_path.setStyleSheet("color: #888; font-size: 11px;")
        overview_layout.addRow("Path:", self.detail_path)
        self.detail_last_run = QLabel("-")
        overview_layout.addRow("Last Run:", self.detail_last_run)
        detail_tabs.addTab(overview_tab, "Overview")
        
        # Fingerprint tab
        fingerprint_tab = QWidget()
        fp_layout = QVBoxLayout(fingerprint_tab)
        self.fingerprint_text = QTextEdit()
        self.fingerprint_text.setReadOnly(True)
        self.fingerprint_text.setStyleSheet("font-family: 'Consolas', monospace; font-size: 11px;")
        fp_layout.addWidget(self.fingerprint_text)
        detail_tabs.addTab(fingerprint_tab, "Fingerprint")
        
        # Proxy tab
        proxy_tab = QWidget()
        proxy_layout = QFormLayout(proxy_tab)
        self.detail_proxy_host = QLabel("-")
        proxy_layout.addRow("Host:", self.detail_proxy_host)
        self.detail_proxy_port = QLabel("-")
        proxy_layout.addRow("Port:", self.detail_proxy_port)
        self.detail_proxy_status = StatusBadge("idle")
        proxy_layout.addRow("Status:", self.detail_proxy_status)
        
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("host:port:user:pass")
        proxy_layout.addRow("Set Proxy:", self.proxy_input)
        
        save_proxy_btn = QPushButton("💾 Save Proxy")
        save_proxy_btn.clicked.connect(self._save_proxy)
        proxy_layout.addRow("", save_proxy_btn)
        detail_tabs.addTab(proxy_tab, "Proxy")
        
        layout.addWidget(detail_tabs)
        layout.addStretch()
        
        return panel

    # ==================== DATA & EVENTS ====================
    
    def _load_profiles(self):
        self.statusBar().showMessage("Loading profiles...")
        try:
            self.profiles = self.profile_manager.load_all_profiles()
            self._populate_auto_table(self.profiles)
            self._populate_profile_table(self.profiles)
            self._update_stats()
            self.statusBar().showMessage(f"Loaded {len(self.profiles)} profiles")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load profiles: {e}")
    
    def _populate_auto_table(self, profiles: List[Profile]):
        self.auto_table.setRowCount(len(profiles))
        for row, profile in enumerate(profiles):
            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.auto_table.setCellWidget(row, 0, checkbox_widget)
            
            id_item = QTableWidgetItem(profile.profile_id[:12] + "...")
            id_item.setData(Qt.UserRole, profile.profile_id)
            id_item.setToolTip(profile.profile_id)
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.auto_table.setItem(row, 1, id_item)
            
            name_item = QTableWidgetItem(profile.data.name or "")
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.auto_table.setItem(row, 2, name_item)
            
            platform_item = QTableWidgetItem(self._detect_platform(profile))
            platform_item.setFlags(platform_item.flags() & ~Qt.ItemIsEditable)
            self.auto_table.setItem(row, 3, platform_item)
            self.auto_table.setCellWidget(row, 4, StatusBadge(profile.status))
            proxy = profile.data.proxy[:15] + "..." if profile.data.proxy and len(profile.data.proxy) > 15 else (profile.data.proxy or "None")
            proxy_item = QTableWidgetItem(proxy)
            proxy_item.setFlags(proxy_item.flags() & ~Qt.ItemIsEditable)
            self.auto_table.setItem(row, 5, proxy_item)
            self.auto_table.setCellWidget(row, 6, StatusBadge("idle"))
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)
            run_btn = ActionButton("▶", "Run automation", "run")
            run_btn.clicked.connect(lambda checked, pid=profile.profile_id: self._run_single_automation(pid))
            actions_layout.addWidget(run_btn)
            open_btn = ActionButton("🌐", "Open browser", "browser")
            open_btn.clicked.connect(lambda checked, pid=profile.profile_id: self._open_browser_for_profile(pid))
            actions_layout.addWidget(open_btn)
            self.auto_table.setCellWidget(row, 7, actions_widget)
    
    def _populate_profile_table(self, profiles: List[Profile]):
        self.profile_table.setRowCount(len(profiles))
        self.profile_count_label.setText(f"{len(profiles)} profiles")
        for row, profile in enumerate(profiles):
            id_item = QTableWidgetItem(profile.profile_id[:15] + "...")
            id_item.setData(Qt.UserRole, profile.profile_id)
            id_item.setToolTip(profile.profile_id)
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.profile_table.setItem(row, 0, id_item)
            
            name_item = QTableWidgetItem(profile.data.name or "")
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.profile_table.setItem(row, 1, name_item)
            
            platform_item = QTableWidgetItem(self._detect_platform(profile))
            platform_item.setFlags(platform_item.flags() & ~Qt.ItemIsEditable)
            self.profile_table.setItem(row, 2, platform_item)
            self.profile_table.setCellWidget(row, 3, StatusBadge(profile.status))
            username_item = QTableWidgetItem(profile.data.username_fb or "")
            username_item.setFlags(username_item.flags() & ~Qt.ItemIsEditable)
            self.profile_table.setItem(row, 4, username_item)
            
            lastrun_item = QTableWidgetItem(profile.data.last_run or "Never")
            lastrun_item.setFlags(lastrun_item.flags() & ~Qt.ItemIsEditable)
            self.profile_table.setItem(row, 5, lastrun_item)
            
            proxy = profile.data.proxy[:20] + "..." if profile.data.proxy and len(profile.data.proxy) > 20 else (profile.data.proxy or "None")
            proxy_item = QTableWidgetItem(proxy)
            proxy_item.setFlags(proxy_item.flags() & ~Qt.ItemIsEditable)
            self.profile_table.setItem(row, 6, proxy_item)
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)
            open_btn = ActionButton("🌐", "Open browser", "browser")
            open_btn.clicked.connect(lambda checked, pid=profile.profile_id: self._open_browser_for_profile(pid))
            actions_layout.addWidget(open_btn)
            folder_btn = ActionButton("📁", "Open folder", "folder")
            folder_btn.clicked.connect(lambda checked, pid=profile.profile_id: self._open_folder_for_profile(pid))
            actions_layout.addWidget(folder_btn)
            self.profile_table.setCellWidget(row, 7, actions_widget)
    
    def _detect_platform(self, profile: Profile) -> str:
        name = (profile.data.name or "").lower()
        if "facebook" in name or "fb" in name or profile.data.username_fb:
            return "📘 Facebook"
        elif "instagram" in name:
            return "📷 Instagram"
        elif "telegram" in name:
            return "✈️ Telegram"
        elif "zalo" in name:
            return "💬 Zalo"
        return "🌐 Other"
    
    def _update_stats(self):
        total = len(self.profiles)
        running = len([p for p in self.profiles if p.status == "running"])
        self.total_card.setValue(str(total))
        self.running_card.setValue(str(running))
        self.running_label.setText(f"Running: {running}")
    
    def _start_system_monitor(self):
        self.system_timer = QTimer()
        self.system_timer.timeout.connect(self._update_system_stats)
        self.system_timer.start(2000)
        
        # Timer to check browser status
        self.browser_check_timer = QTimer()
        self.browser_check_timer.timeout.connect(self._check_browser_status)
        self.browser_check_timer.start(3000)
    
    def _update_system_stats(self):
        try:
            self.cpu_label.setText(f"CPU: {psutil.cpu_percent():.0f}%")
            self.ram_label.setText(f"RAM: {psutil.virtual_memory().percent:.0f}%")
        except: pass
    
    def _check_browser_status(self):
        """Check if browsers are still running and update status."""
        try:
            closed_profiles = []
            
            # Check subprocess processes
            for profile_id, process in list(self.browser_manager.active_processes.items()):
                if process.poll() is not None:  # Process has terminated
                    closed_profiles.append(profile_id)
            
            # Update status for closed browsers
            for profile_id in closed_profiles:
                if profile_id in self.browser_manager.active_processes:
                    del self.browser_manager.active_processes[profile_id]
                self.profile_manager.update_profile_status(profile_id, "inactive")
            
            # Refresh UI if any browser was closed
            if closed_profiles:
                self._load_profiles()
        except Exception as e:
            pass
    
    def _on_profile_selected(self):
        selected = self.profile_table.selectedItems()
        if not selected: return
        id_item = self.profile_table.item(selected[0].row(), 0)
        if not id_item: return
        profile = self.profile_manager.get_profile(id_item.data(Qt.UserRole))
        if profile:
            self.selected_profile = profile
            self._update_detail_panel(profile)
    
    def _update_detail_panel(self, profile: Profile):
        self.detail_header.setText(profile.data.name or "Unnamed")
        self.detail_status.setStatus(profile.status)
        self.detail_id.setText(profile.profile_id)
        self.detail_name.setText(profile.data.name or "-")
        self.detail_platform.setText(self._detect_platform(profile))
        self.detail_username.setText(profile.data.username_fb or "-")
        self.detail_path.setText(profile.path)
        self.detail_last_run.setText(profile.data.last_run or "Never")
        if profile.data.proxy:
            parts = profile.data.proxy.split(":")
            self.detail_proxy_host.setText(parts[0] if parts else "-")
            self.detail_proxy_port.setText(parts[1] if len(parts) > 1 else "-")
            self.proxy_input.setText(profile.data.proxy)
        else:
            self.detail_proxy_host.setText("No proxy")
            self.detail_proxy_port.setText("-")
            self.proxy_input.setText("")

    # ==================== ACTIONS ====================
    
    def _get_auto_selected_ids(self) -> List[str]:
        selected = []
        for row in range(self.auto_table.rowCount()):
            checkbox_widget = self.auto_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    id_item = self.auto_table.item(row, 1)
                    if id_item:
                        selected.append(id_item.data(Qt.UserRole))
        return selected
    
    def _auto_select_all(self):
        for row in range(self.auto_table.rowCount()):
            checkbox_widget = self.auto_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)
        self.selected_card.setValue(str(len(self._get_auto_selected_ids())))
    
    def _apply_auto_filter(self, status: str):
        if status == "All Status":
            self._populate_auto_table(self.profiles)
        else:
            status_map = {"Ready": "inactive", "Running": "running", "Error": "error", "Missing": "missing"}
            filtered = [p for p in self.profiles if p.status == status_map.get(status, status.lower())]
            self._populate_auto_table(filtered)
    
    def _search_auto_profiles(self, text: str):
        if not text:
            self._populate_auto_table(self.profiles)
        else:
            filtered = [p for p in self.profiles if text.lower() in (p.data.name or "").lower() or text in p.profile_id]
            self._populate_auto_table(filtered)
    
    def _run_selected_automation(self):
        selected = self._get_auto_selected_ids()
        if not selected:
            QMessageBox.warning(self, "Warning", "No profiles selected")
            return
        
        # Check if script is selected
        if not self.selected_script:
            # No script - just open browsers
            self.auto_progress.setVisible(True)
            self.auto_progress.setMaximum(len(selected))
            for i, pid in enumerate(selected):
                self._open_browser_for_profile(pid)
                self.auto_progress.setValue(i + 1)
                QApplication.processEvents()
            self.auto_progress.setVisible(False)
            self._load_profiles()
            return
        
        # Run with script
        script_params = self.get_script_input_values()
        self.auto_progress.setVisible(True)
        self.auto_progress.setMaximum(len(selected))
        self.auto_status_label.setText(f"Running: {self.selected_script.description}")
        
        for i, pid in enumerate(selected):
            if not self.automation_executor.running or i == 0:
                # Launch browser with Selenium for automation
                result = self.browser_manager.launch_profile(pid, use_selenium=True)
                if result:
                    driver = self.browser_manager.get_driver(pid)
                    if driver:
                        self.automation_executor.execute_script(
                            driver,
                            self.selected_script.id,
                            script_params,
                            lambda cur, total: self._update_script_progress(cur, total)
                        )
            
            self.auto_progress.setValue(i + 1)
            QApplication.processEvents()
        
        self.auto_progress.setVisible(False)
        self.auto_status_label.setText("Automation completed")
        self._load_profiles()
    
    def _update_script_progress(self, current: int, total: int):
        """Update progress from script execution."""
        self.auto_status_label.setText(f"Progress: {current}/{total}")
        QApplication.processEvents()
    
    def _run_single_automation(self, profile_id: str):
        if self.selected_script:
            # Run with script
            result = self.browser_manager.launch_profile(profile_id, use_selenium=True)
            if result:
                driver = self.browser_manager.get_driver(profile_id)
                if driver:
                    script_params = self.get_script_input_values()
                    self.automation_executor.execute_script(
                        driver,
                        self.selected_script.id,
                        script_params
                    )
        else:
            self._open_browser_for_profile(profile_id)
        self._load_profiles()
    
    def _stop_all_automation(self):
        if QMessageBox.question(self, "Confirm", "Stop all browsers?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            # Stop automation executor
            self.automation_executor.stop()
            count = self.browser_manager.close_all_sessions()
            self._load_profiles()
            self.statusBar().showMessage(f"Stopped {count} browsers")
    
    def _apply_profile_filter(self, status: str):
        if status == "All Status":
            self._populate_profile_table(self.profiles)
        else:
            status_map = {"Ready": "inactive", "Running": "running", "Error": "error", "Missing": "missing"}
            filtered = [p for p in self.profiles if p.status == status_map.get(status, status.lower())]
            self._populate_profile_table(filtered)
    
    def _search_profiles(self, text: str):
        if not text:
            self._populate_profile_table(self.profiles)
        else:
            filtered = [p for p in self.profiles if text.lower() in (p.data.name or "").lower() or text in p.profile_id]
            self._populate_profile_table(filtered)
    
    def _open_browser_manual(self):
        if not self.selected_profile:
            QMessageBox.warning(self, "Warning", "No profile selected")
            return
        self._open_browser_for_profile(self.selected_profile.profile_id)
    
    def _close_all_browsers(self):
        """Close all running browser sessions."""
        count = self.browser_manager.get_session_count()
        if count == 0:
            QMessageBox.information(self, "Info", "No browsers are currently running")
            return
        
        reply = QMessageBox.question(
            self, "Confirm",
            f"Close all {count} running browser(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            closed = self.browser_manager.close_all_sessions()
            self.statusBar().showMessage(f"Closed {closed} browser(s)")
            self._load_profiles()
    
    def _open_browser_for_profile(self, profile_id: str):
        try:
            index = self.browser_manager.get_session_count()
            position = self.browser_manager.calculate_window_position(index)
            result = self.browser_manager.launch_profile(profile_id, window_position=position, use_selenium=False)
            if result:
                self.statusBar().showMessage(f"Opened browser for {profile_id[:15]}...")
                self._load_profiles()
            else:
                QMessageBox.warning(self, "Warning", "Failed to open browser")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {e}")
    
    def _open_profile_folder(self):
        if not self.selected_profile:
            QMessageBox.warning(self, "Warning", "No profile selected")
            return
        self._open_folder_for_profile(self.selected_profile.profile_id)
    
    def _open_folder_for_profile(self, profile_id: str):
        path = os.path.abspath(self.repository.get_profile_path(profile_id))
        if os.path.exists(path):
            subprocess.Popen(f'explorer "{path}"')
        else:
            QMessageBox.warning(self, "Warning", f"Folder not found: {path}")
    
    def _backup_selected_profile(self):
        if not self.selected_profile:
            QMessageBox.warning(self, "Warning", "No profile selected")
            return
        try:
            info = self.backup_manager.backup_profile(self.selected_profile.profile_id)
            if info:
                QMessageBox.information(self, "Success", f"Backup created:\n{info.backup_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Backup failed: {e}")
    
    def _create_new_profile(self):
        """Create a new profile."""
        dialog = ProfileEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            name = data.get('name') or f"Profile_{int(time.time())}"
            try:
                profile = self.profile_manager.create_profile(name=name)
                if profile:
                    # Update additional fields
                    profile.data.proxy = data.get('proxy', '')
                    profile.data.proxymode = data.get('proxymode', 'none')
                    profile.data.username_fb = data.get('username_fb', '')
                    profile.data.password_fb = data.get('password_fb', '')
                    profile.data.ma2fa = data.get('ma2fa', '')
                    profile.data.group_profile = data.get('group_profile', '')
                    profile.data.notes = data.get('notes', '')
                    self.repository.update_profile(profile.data)
                    self._load_profiles()
                    self.statusBar().showMessage(f"Created profile: {name}")
                else:
                    QMessageBox.warning(self, "Warning", "Failed to create profile")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create profile: {e}")
    
    def _edit_selected_profile(self):
        """Edit selected profile."""
        if not self.selected_profile:
            QMessageBox.warning(self, "Warning", "No profile selected")
            return
        
        dialog = ProfileEditDialog(profile=self.selected_profile, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                self.selected_profile.data.name = data.get('name', self.selected_profile.data.name)
                self.selected_profile.data.proxy = data.get('proxy', '')
                self.selected_profile.data.proxymode = data.get('proxymode', 'none')
                self.selected_profile.data.username_fb = data.get('username_fb', '')
                self.selected_profile.data.password_fb = data.get('password_fb', '')
                self.selected_profile.data.ma2fa = data.get('ma2fa', '')
                self.selected_profile.data.group_profile = data.get('group_profile', '')
                self.selected_profile.data.notes = data.get('notes', '')
                
                if self.repository.update_profile(self.selected_profile.data):
                    self._load_profiles()
                    self._update_detail_panel(self.selected_profile)
                    self.statusBar().showMessage("Profile updated")
                else:
                    QMessageBox.warning(self, "Warning", "Failed to update profile")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update profile: {e}")
    
    def _save_proxy(self):
        """Save proxy for selected profile."""
        if not self.selected_profile:
            QMessageBox.warning(self, "Warning", "No profile selected")
            return
        
        proxy = self.proxy_input.text().strip()
        try:
            self.selected_profile.data.proxy = proxy
            self.selected_profile.data.proxymode = "http" if proxy else "none"
            
            if self.repository.update_profile(self.selected_profile.data):
                self._update_detail_panel(self.selected_profile)
                self._load_profiles()
                self.statusBar().showMessage("Proxy saved")
            else:
                QMessageBox.warning(self, "Warning", "Failed to save proxy")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save proxy: {e}")
    
    def _delete_selected_profile(self):
        """Delete selected profile."""
        if not self.selected_profile:
            QMessageBox.warning(self, "Warning", "No profile selected")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete profile:\n{self.selected_profile.data.name}?\n\nThis will also delete all profile data files.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.profile_manager.delete_profile(self.selected_profile.profile_id, delete_files=True):
                    self.selected_profile = None
                    self.detail_header.setText("Select a profile")
                    self._load_profiles()
                    self.statusBar().showMessage("Profile deleted")
                else:
                    QMessageBox.warning(self, "Warning", "Failed to delete profile")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete profile: {e}")
    
    def closeEvent(self, event):
        try:
            self.browser_manager.close_all_sessions()
        except: pass
        event.accept()
