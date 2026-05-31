"""Main application window."""

import re

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QStatusBar,
    QLabel, QSizeGrip, QApplication, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QSize, QPoint, QTimer, QThread, QObject, Signal
from PySide6.QtGui import QCloseEvent, QColor, QPalette

from config import config
from api.endpoints import HTBApi
from ui.styles import GLOBAL_STYLE, HTB_GREEN, HTB_TEXT_MUTED, HTB_BG_DARKEST
from ui.top_nav import TopNav
from ui.widgets.title_bar import TitleBar
from ui.pages import (
    DashboardPage, MachinesPage, MachineDetailPage,
    SeasonsPage, ToolkitPage, VPNPage, SettingsPage
)
from ui.widgets.fade_stack import FadeStackWidget
from utils.debug import debug_log


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.drag_pos = None
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._setup_clipboard_monitor()
        debug_log("UI", "MainWindow initialized")

    def closeEvent(self, event: QCloseEvent):
        """Stop threads before closing."""
        self._clipboard_timer.stop()
        self._cleanup_flag_thread()
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
        # Frameless Window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(GLOBAL_STYLE)

    def _setup_ui(self):
        # We need a central widget that acts as the real window background
        # because the main window is transparent to allow for rounded corners if desired
        central = QWidget()
        central.setObjectName("CentralWidget")
        central.setStyleSheet(f"""
            QWidget#CentralWidget {{
                background-color: {HTB_BG_DARKEST};
                border: 1px solid #333;
                border-radius: 10px;
            }}
        """)
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Custom Title Bar
        self.title_bar = TitleBar(self)
        layout.addWidget(self.title_bar)

        # Top navigation
        self.top_nav = TopNav()
        layout.addWidget(self.top_nav)

        # Content Area
        self.stack = FadeStackWidget()
        layout.addWidget(self.stack)

        # Create pages
        self.dashboard = DashboardPage()

        # Initialize other pages (placeholders for now to match imports)
        self.machines = MachinesPage()
        self.machine_detail = MachineDetailPage()
        self.seasons = SeasonsPage()
        self.toolkit = ToolkitPage()
        self.vpn = VPNPage()
        self.settings = SettingsPage()

        # Add to stack
        self.pages = {
            "dashboard": self.dashboard,
            "machines": self.machines,
            "machine_detail": self.machine_detail,
            "seasons": self.seasons,
            "toolkit": self.toolkit,
            "vpn": self.vpn,
            "settings": self.settings,
        }

        for page in self.pages.values():
            self.stack.addWidget(page)

        # Status bar implementation (custom at bottom of central widget)
        self.status_bar = QWidget()
        self.status_bar.setFixedHeight(24)
        self.status_bar.setStyleSheet(f"background-color: {HTB_BG_DARKEST}; border-top: 1px solid #222;")
        sb_layout = QHBoxLayout(self.status_bar)
        sb_layout.setContentsMargins(10, 0, 10, 0)

        self.connection_label = QLabel("🔴 Not connected")
        self.connection_label.setStyleSheet(f"color: {HTB_TEXT_MUTED}; font-size: 11px;")
        sb_layout.addStretch()
        sb_layout.addWidget(self.connection_label)

        # Size Grip for resizing
        self.size_grip = QSizeGrip(self.status_bar)
        sb_layout.addWidget(self.size_grip, 0, Qt.AlignBottom | Qt.AlignRight)

        layout.addWidget(self.status_bar)

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
            self.connection_label.setStyleSheet(f"color: {HTB_GREEN}; font-size: 11px;")

        # Refresh dashboard
        self.dashboard.load_data()

    # =================================================================
    # GLOBAL FLAG WATCHER
    # Surveille le presse-papier dans toute l'application. On utilise un
    # polling par QTimer (et non le signal dataChanged) pour que la
    # surveillance fonctionne aussi quand la fenetre n'a pas le focus.
    # =================================================================

    _FLAG_PATTERN = re.compile(r'^[a-fA-F0-9]{32}$')

    def _setup_clipboard_monitor(self):
        """Monitor clipboard for potential flags (works in background on X11)."""
        self.clipboard = QApplication.clipboard()
        self._last_clipboard_text = ""
        self._flag_thread = None
        self._flag_worker = None

        self._clipboard_timer = QTimer(self)
        self._clipboard_timer.setInterval(1500)
        self._clipboard_timer.timeout.connect(self._check_clipboard)
        self._clipboard_timer.start()

    @Slot()
    def _check_clipboard(self):
        text = self.clipboard.text().strip()
        if not text or text == self._last_clipboard_text:
            return
        self._last_clipboard_text = text

        # Check if text looks like a flag (32 chars hex / MD5)
        if self._FLAG_PATTERN.match(text):
            debug_log("CLIPBOARD", f"Potential flag detected: {text}")
            self._submit_flag(text)

    def _submit_flag(self, flag: str):
        if self._flag_thread and self._flag_thread.isRunning():
            return  # Busy with previous flag

        self._flag_thread = QThread()
        self._flag_worker = FlagSubmitter(flag)
        self._flag_worker.moveToThread(self._flag_thread)
        self._flag_thread.started.connect(self._flag_worker.run)
        self._flag_worker.finished.connect(self._on_flag_submitted)
        self._flag_worker.error.connect(self._on_flag_error)
        self._flag_thread.start()

    @Slot(dict)
    def _on_flag_submitted(self, result: dict):
        self._cleanup_flag_thread()
        if result.get("success"):
            machine_name = result.get("machine_name", "Machine")
            msg = result.get("message", "Flag accepted!")
            self.connection_label.setText(f"🎉 Correct flag for {machine_name}!")
            self.connection_label.setStyleSheet(f"color: {HTB_GREEN}; font-size: 11px;")
            QMessageBox.information(self, "🎉 Flag Accepted!", f"{msg}\n\nMachine: {machine_name}")

            # Refresh current page if it's the dashboard
            if self.stack.currentWidget() == self.dashboard:
                self.dashboard.load_data()

    @Slot(str)
    def _on_flag_error(self, error: str):
        self._cleanup_flag_thread()
        # Only log error, don't annoy user if they just copied some other 32 char string
        debug_log("CLIPBOARD", f"Auto-submit failed: {error}")

    def _cleanup_flag_thread(self):
        if self._flag_thread:
            if self._flag_thread.isRunning():
                self._flag_thread.quit()
                self._flag_thread.wait()
            self._flag_thread = None
            self._flag_worker = None


class FlagSubmitter(QObject):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, flag: str):
        super().__init__()
        self.flag = flag

    def run(self):
        try:
            # 1. Get active machine
            success, result = HTBApi.get_active_machine()
            if not success or not result:
                self.error.emit("No active machine found")
                return

            from models.connection import ActiveMachine
            active = ActiveMachine.from_api(result)
            if not active:
                self.error.emit("No active machine parsed")
                return

            # 2. Submit flag
            success, result = HTBApi.submit_flag(active.id, self.flag)
            if success:
                # HTB sometimes returns 200 OK even for a wrong flag, with a message
                msg = result.get("message", "") if isinstance(result, dict) else ""
                is_correct = "incorrect" not in msg.lower() and "wrong" not in msg.lower()

                if is_correct:
                    self.finished.emit({
                        "success": True,
                        "message": msg or "Flag accepted!",
                        "machine_name": active.name
                    })
                else:
                    self.error.emit(msg)
            else:
                self.error.emit(str(result))

        except Exception as e:
            self.error.emit(str(e))
