"""Main application window."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QStatusBar, QLabel
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QCloseEvent

from config import config
from ui.styles import GLOBAL_STYLE, HTB_GREEN, HTB_TEXT_DIM
from ui.top_nav import TopNav
from ui.pages import (
    DashboardPage, MachinesPage, MachineDetailPage,
    SeasonsPage, VPNPage, SettingsPage
)
from utils.debug import debug_log


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        debug_log("UI", "MainWindow initialized")

    def closeEvent(self, event: QCloseEvent):
        """Detener todos los hilos de trabajo antes de cerrar para evitar crash."""
        pages_with_threads = [
            self.dashboard,
            self.machines,
            self.machine_detail,
            self.seasons,
            self.vpn,
        ]
        for page in pages_with_threads:
            if hasattr(page, "stop_background_tasks"):
                page.stop_background_tasks()
        event.accept()
    
    def _setup_window(self):
        self.setWindowTitle("HackTheBox Client")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self.setStyleSheet(GLOBAL_STYLE)
    
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top navigation
        self.top_nav = TopNav()
        layout.addWidget(self.top_nav)
        
        # Content
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #101927;")
        layout.addWidget(self.stack)
        
        # Create pages
        self.dashboard = DashboardPage()
        self.machines = MachinesPage()
        self.machine_detail = MachineDetailPage()
        self.seasons = SeasonsPage()
        self.vpn = VPNPage()
        self.settings = SettingsPage()
        
        # Add to stack
        self.pages = {
            "dashboard": self.dashboard,
            "machines": self.machines,
            "machine_detail": self.machine_detail,
            "seasons": self.seasons,
            "vpn": self.vpn,
            "settings": self.settings,
        }
        
        for page in self.pages.values():
            self.stack.addWidget(page)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.connection_label = QLabel("🔴 Not connected")
        self.connection_label.setStyleSheet(f"color: {HTB_TEXT_DIM};")
        self.status_bar.addPermanentWidget(self.connection_label)
    
    def _connect_signals(self):
        self.top_nav.page_changed.connect(self._on_page_changed)
        
        # Machine selection
        self.machines.machine_selected.connect(self._on_machine_selected)
        self.seasons.machine_selected.connect(self._on_machine_selected)
        
        # Machine detail back button
        self.machine_detail.back_clicked.connect(
            lambda: self._on_page_changed("machines"))
        
        # Settings token changed
        self.settings.token_changed.connect(self._on_token_changed)
    
    @Slot(str)
    def _on_page_changed(self, page_id: str):
        debug_log("UI", f"Page changed: {page_id}")
        if page_id in self.pages:
            self.stack.setCurrentWidget(self.pages[page_id])
            self.top_nav.set_active(page_id)
    
    @Slot(object)
    def _on_machine_selected(self, machine):
        debug_log("UI", f"Machine selected: {machine.name}")
        self.machine_detail.set_machine(machine)
        self.stack.setCurrentWidget(self.machine_detail)
        self.top_nav.set_active("machines")
    
    @Slot()
    def _on_token_changed(self):
        debug_log("UI", "Token changed, refreshing...")
        
        if config.is_configured():
            self.connection_label.setText(f"🟢 Configured")
            self.connection_label.setStyleSheet(f"color: {HTB_GREEN};")
        
        # Refresh dashboard
        self.dashboard.load_data()
