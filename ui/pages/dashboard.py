"""Dashboard Page - con máquina activa, acciones y activity."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
    QPushButton, QLineEdit, QScrollArea, QMessageBox, QApplication,
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QObject, QUrl, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from typing import Optional, List

from api.endpoints import HTBApi
from models.user import User
from models.connection import ActiveMachine, Connection
from ui.styles import (
    HTB_GREEN, HTB_BG_CARD, HTB_TEXT_DIM, HTB_BG_CARD_ELEVATED,
    BTN_PRIMARY, BTN_DANGER, BTN_DEFAULT
)
from ui.widgets.activity_item import ActivityItem
from utils.debug import debug_log


class DashboardWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    
    def run(self):
        debug_log("DASHBOARD", "Loading data...")
        data = {}
        try:
            success, result = HTBApi.get_user_info()
            if success and isinstance(result, dict):
                data["user"] = User.from_api(result)
            
            success, result = HTBApi.get_active_machine()
            if success and isinstance(result, dict):
                data["active_machine"] = ActiveMachine.from_api(result)
            
            success, result = HTBApi.get_connection_status()
            if success and isinstance(result, list) and len(result) > 0:
                data["connection"] = Connection.from_api(result[0])
            
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class DashboardActionWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, action: str, machine_id: int, flag: str = ""):
        super().__init__()
        self.action = action
        self.machine_id = machine_id
        self.flag = flag
    
    def run(self):
        try:
            if self.action == "terminate":
                success, result = HTBApi.terminate_machine(self.machine_id)
            elif self.action == "reset":
                success, result = HTBApi.reset_machine(self.machine_id)
            elif self.action == "flag":
                success, result = HTBApi.submit_flag(self.machine_id, self.flag)
            else:
                self.error.emit("Unknown action")
                return
            if success:
                self.finished.emit({"action": self.action, "result": result})
            else:
                self.error.emit(str(result))
        except Exception as e:
            self.error.emit(str(e))


class DashboardActivityWorker(QObject):
    finished = Signal(list)
    error = Signal(str)
    
    def __init__(self, machine_id: int):
        super().__init__()
        self.machine_id = machine_id
    
    def run(self):
        try:
            success, result = HTBApi.get_machine_activity(self.machine_id)
            if success and isinstance(result, dict):
                info = result.get("info", {})
                self.finished.emit(info.get("activity", []))
            else:
                self.error.emit(str(result) if not success else "Invalid response")
        except Exception as e:
            self.error.emit(str(e))


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._worker = None
        self._loading = False
        self._active_machine_id: Optional[int] = None
        self._active_machine_avatar: str = ""
        self._network_manager = QNetworkAccessManager(self)
        self._network_manager.finished.connect(self._on_avatar_loaded)
        self._activity_network = QNetworkAccessManager(self)
        self._activity_network.finished.connect(self._on_activity_avatar_loaded)
        self._machine_avatar_network = QNetworkAccessManager(self)
        self._machine_avatar_network.finished.connect(self._on_machine_avatar_loaded)
        self._activity_thread = None
        self._activity_worker = None
        self._action_thread = None
        self._action_worker = None
        self._activity_timer = QTimer(self)
        self._activity_timer.setInterval(15000)
        self._activity_timer.timeout.connect(self._load_activity)
        self._activity_countdown = QTimer(self)
        self._activity_countdown.setInterval(1000)
        self._activity_countdown.timeout.connect(self._update_activity_countdown)
        self._activity_seconds_left = 15
        self._activity_items: List[ActivityItem] = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(22)
        
        # Welcome
        self.welcome_label = QLabel("Welcome back!")
        self.welcome_label.setStyleSheet("font-size: 28px; font-weight: 700; letter-spacing: -0.5px;")
        self.welcome_label.setWordWrap(True)
        layout.addWidget(self.welcome_label)
        
        # Stats row
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(16)
        
        # User card con avatar
        self.user_card = self._create_user_card_with_avatar()
        self.sub_card = self._create_stat_card("👑", "Subscription", "-")
        self.rank_card = self._create_stat_card("📊", "Server", "-")
        
        stats_layout.addWidget(self.user_card)
        stats_layout.addWidget(self.sub_card)
        stats_layout.addWidget(self.rank_card)
        stats_layout.addStretch()
        
        layout.addWidget(stats_widget)
        
        # Active Machine
        section1 = QLabel("ACTIVE MACHINE")
        section1.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        layout.addWidget(section1)
        
        self.machine_frame = QFrame()
        self.machine_frame.setStyleSheet(f"background-color: {HTB_BG_CARD}; border-radius: 12px;")
        self.machine_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        machine_layout = QVBoxLayout(self.machine_frame)
        machine_layout.setContentsMargins(24, 20, 24, 20)
        machine_layout.setSpacing(8)
        
        # Header row con avatar + nombre
        machine_header = QHBoxLayout()
        machine_header.setSpacing(14)
        
        self.machine_avatar = QLabel()
        self.machine_avatar.setFixedSize(48, 48)
        self.machine_avatar.setStyleSheet("background-color: #1a2638; border-radius: 8px;")
        self.machine_avatar.setAlignment(Qt.AlignCenter)
        self.machine_avatar.setVisible(False)
        machine_header.addWidget(self.machine_avatar)
        
        machine_info_col = QVBoxLayout()
        machine_info_col.setSpacing(4)
        
        self.machine_name = QLabel("No active machine")
        self.machine_name.setStyleSheet("font-size: 18px; font-weight: 600; background: transparent; border: none;")
        self.machine_name.setWordWrap(True)
        machine_info_col.addWidget(self.machine_name)
        
        self.machine_info = QLabel("Spawn a machine from the Machines page to start hacking")
        self.machine_info.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 14px; background: transparent; border: none;")
        self.machine_info.setWordWrap(True)
        machine_info_col.addWidget(self.machine_info)
        
        machine_header.addLayout(machine_info_col)
        machine_header.addStretch()
        machine_layout.addLayout(machine_header)
        
        ip_row = QHBoxLayout()
        ip_row.setSpacing(10)
        self.machine_ip = QLabel("")
        self.machine_ip.setStyleSheet(f"color: {HTB_GREEN}; font-size: 16px; font-weight: 600; font-family: monospace; background: transparent; border: none;")
        ip_row.addWidget(self.machine_ip)
        self.copy_ip_btn = QPushButton("📋 Copy IP")
        self.copy_ip_btn.setStyleSheet(BTN_DEFAULT)
        self.copy_ip_btn.setToolTip("Copy IP to clipboard")
        self.copy_ip_btn.setCursor(Qt.PointingHandCursor)
        self.copy_ip_btn.clicked.connect(self._copy_ip_to_clipboard)
        self.copy_ip_btn.setVisible(False)
        ip_row.addWidget(self.copy_ip_btn)
        ip_row.addStretch()
        machine_layout.addLayout(ip_row)
        
        # Acciones: Stop, Reset, Submit flag (misma estética que machine detail)
        self.actions_widget = QWidget()
        actions_layout = QVBoxLayout(self.actions_widget)
        actions_layout.setContentsMargins(0, 14, 0, 0)
        actions_layout.setSpacing(12)
        btns_row = QHBoxLayout()
        btns_row.setSpacing(12)
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setStyleSheet(BTN_DANGER)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        btns_row.addWidget(self.stop_btn)
        self.reset_btn = QPushButton("🔄 Reset")
        self.reset_btn.setStyleSheet(BTN_DEFAULT)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        btns_row.addWidget(self.reset_btn)
        btns_row.addStretch()
        actions_layout.addLayout(btns_row)
        flag_row = QHBoxLayout()
        flag_row.setSpacing(12)
        self.flag_input = QLineEdit()
        self.flag_input.setObjectName("flag_input")
        self.flag_input.setPlaceholderText("Enter the flag")
        self.flag_input.setMinimumHeight(42)
        self.flag_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        flag_row.addWidget(self.flag_input)
        self.submit_flag_btn = QPushButton("🚩 Submit Flag")
        self.submit_flag_btn.setStyleSheet(BTN_PRIMARY)
        self.submit_flag_btn.setCursor(Qt.PointingHandCursor)
        flag_row.addWidget(self.submit_flag_btn)
        actions_layout.addLayout(flag_row)
        actions_layout.setContentsMargins(0, 14, 0, 20)  # Add bottom margin for spacing
        machine_layout.addWidget(self.actions_widget)
        self.actions_widget.setVisible(False)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        self.submit_flag_btn.clicked.connect(self._on_submit_flag_clicked)
        
        layout.addWidget(self.machine_frame)
        
        # Activity (solo visible si hay máquina activa)
        activity_title_row = QHBoxLayout()
        self.activity_header = QLabel("ACTIVITY")
        self.activity_header.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        activity_title_row.addWidget(self.activity_header)
        activity_title_row.addStretch()
        self.activity_refresh_label = QLabel("Refreshing in 15s")
        self.activity_refresh_label.setStyleSheet(f"color: {HTB_GREEN}; font-size: 11px; font-weight: 500;")
        activity_title_row.addWidget(self.activity_refresh_label)
        layout.addLayout(activity_title_row)
        self.activity_scroll = QScrollArea()
        self.activity_scroll.setWidgetResizable(True)
        self.activity_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.activity_scroll.setStyleSheet("background: transparent; border: none;")
        self.activity_scroll.setFrameShape(QFrame.NoFrame)
        self._activity_container = QWidget()
        self._activity_layout = QVBoxLayout(self._activity_container)
        self._activity_layout.setContentsMargins(0, 0, 8, 0)
        self._activity_layout.setSpacing(8)
        self._activity_layout.setAlignment(Qt.AlignTop)
        self.activity_scroll.setWidget(self._activity_container)
        self.activity_scroll.setMinimumHeight(180)
        self.activity_scroll.setMaximumHeight(240)
        layout.addWidget(self.activity_scroll)
        self.activity_header.setVisible(False)
        self.activity_refresh_label.setVisible(False)
        self.activity_scroll.setVisible(False)
        
        # VPN
        section2 = QLabel("VPN STATUS")
        section2.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px;")
        layout.addWidget(section2)
        
        self.vpn_frame = QFrame()
        self.vpn_frame.setStyleSheet(f"background-color: {HTB_BG_CARD}; border-radius: 12px;")
        self.vpn_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        vpn_layout = QHBoxLayout(self.vpn_frame)
        vpn_layout.setContentsMargins(24, 20, 24, 20)
        
        self.vpn_status = QLabel("🔴 Disconnected")
        self.vpn_status.setStyleSheet("font-size: 16px; font-weight: 500;")
        vpn_layout.addWidget(self.vpn_status)
        
        vpn_layout.addStretch()
        
        self.vpn_details = QLabel("Connect via VPN to access machines")
        self.vpn_details.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 14px;")
        self.vpn_details.setWordWrap(True)
        vpn_layout.addWidget(self.vpn_details)
        
        layout.addWidget(self.vpn_frame)
        layout.addStretch()
    
    def _create_stat_card(self, icon: str, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        card.setStyleSheet(f"background-color: {HTB_BG_CARD}; border-radius: 12px;")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)
        
        header = QLabel(f"{icon} {title}")
        header.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 12px; font-weight: 500;")
        layout.addWidget(header)
        
        value_lbl = QLabel(value)
        value_lbl.setObjectName("value")
        value_lbl.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {HTB_GREEN};")
        value_lbl.setWordWrap(True)
        layout.addWidget(value_lbl)
        
        return card
    
    def _create_user_card_with_avatar(self) -> QFrame:
        """Crear tarjeta de usuario con avatar."""
        card = QFrame()
        card.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        card.setStyleSheet(f"background-color: {HTB_BG_CARD}; border-radius: 12px;")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)
        
        header = QLabel("👤 Username")
        header.setStyleSheet(f"color: {HTB_TEXT_DIM}; font-size: 12px; font-weight: 500;")
        layout.addWidget(header)
        
        # Contenedor horizontal para avatar + nombre
        user_row = QWidget()
        user_layout = QHBoxLayout(user_row)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(10)
        
        # Avatar (placeholder si no hay URL; se rellena con imagen o inicial)
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(40, 40)
        self.avatar_label.setStyleSheet(
            "background-color: #1a2638; border-radius: 20px; "
            "color: #9fef00; font-weight: 700; font-size: 16px;"
        )
        self.avatar_label.setAlignment(Qt.AlignCenter)
        user_layout.addWidget(self.avatar_label)
        
        # Username
        self.username_label = QLabel("-")
        self.username_label.setObjectName("value")
        self.username_label.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {HTB_GREEN};")
        self.username_label.setWordWrap(True)
        user_layout.addWidget(self.username_label)
        user_layout.addStretch()
        
        layout.addWidget(user_row)
        
        return card
    
    def _load_avatar(self, avatar_url: str):
        """Descargar avatar desde URL."""
        if not avatar_url:
            return
        request = QNetworkRequest(QUrl(avatar_url))
        self._network_manager.get(request)
    
    def _set_avatar_placeholder(self, username: str):
        """Mostrar inicial del usuario cuando no hay avatar."""
        initial = (username.strip() or "?")[0].upper()
        self.avatar_label.setText(initial)
        self.avatar_label.setPixmap(QPixmap())
        self.avatar_label.setStyleSheet(
            "background-color: #1a2638; border-radius: 20px; "
            "color: #9fef00; font-weight: 700; font-size: 16px;"
        )

    @Slot(QNetworkReply)
    def _on_avatar_loaded(self, reply: QNetworkReply):
        """Callback cuando el avatar se descarga."""
        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                scaled = pixmap.scaled(40, 40, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.avatar_label.setPixmap(scaled)
                self.avatar_label.setText("")
                self.avatar_label.setStyleSheet("border-radius: 20px; background: transparent;")
        reply.deleteLater()
    
    def _update_card(self, card: QFrame, value: str):
        lbl = card.findChild(QLabel, "value")
        if lbl:
            lbl.setText(value)
    
    def load_data(self):
        if self._loading:
            return
        self._loading = True
        self._cleanup_thread()
        
        self._thread = QThread()
        self._worker = DashboardWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_loaded)
        self._worker.error.connect(self._on_error)
        self._thread.start()
    
    def _cleanup_thread(self):
        if self._thread:
            if self._thread.isRunning():
                self._thread.quit()
                if not self._thread.wait(3000):
                    self._thread.terminate()
                    self._thread.wait(500)
            self._thread = None
            self._worker = None

    def stop_background_tasks(self):
        self._loading = False
        self._activity_timer.stop()
        self._activity_countdown.stop()
        self._cleanup_thread()
        self._cleanup_activity_thread()
        self._cleanup_action_thread()

    def _cleanup_activity_thread(self):
        if self._activity_thread:
            if self._activity_thread.isRunning():
                self._activity_thread.quit()
                if not self._activity_thread.wait(3000):
                    self._activity_thread.terminate()
                    self._activity_thread.wait(500)
            self._activity_thread = None
            self._activity_worker = None

    def _cleanup_action_thread(self):
        if self._action_thread:
            if self._action_thread.isRunning():
                self._action_thread.quit()
                if not self._action_thread.wait(3000):
                    self._action_thread.terminate()
                    self._action_thread.wait(500)
            self._action_thread = None
            self._action_worker = None

    def _copy_ip_to_clipboard(self):
        ip = self.machine_ip.text().strip()
        if ip and not ip.startswith("⏳") and not ip.startswith("❌"):
            cb = QApplication.clipboard()
            if cb:
                cb.setText(ip)
                QMessageBox.information(self, "Copied", f"IP copied: {ip}")
        else:
            QMessageBox.information(self, "Copy IP", "No IP available yet. Wait for the machine to start.")

    def _update_activity_countdown(self):
        self._activity_seconds_left -= 1
        if self._activity_seconds_left <= 0:
            self._activity_seconds_left = 15
        self.activity_refresh_label.setText(f"Refreshing in {self._activity_seconds_left}s")

    def _load_activity(self):
        if not self._active_machine_id:
            return
        self._cleanup_activity_thread()
        self._activity_seconds_left = 15
        self.activity_refresh_label.setText("Refreshing in 15s")
        self._activity_thread = QThread()
        self._activity_worker = DashboardActivityWorker(self._active_machine_id)
        self._activity_worker.moveToThread(self._activity_thread)
        self._activity_thread.started.connect(self._activity_worker.run)
        self._activity_worker.finished.connect(self._on_activity_loaded)
        self._activity_worker.error.connect(lambda e: self._cleanup_activity_thread())
        self._activity_thread.start()

    @Slot(list)
    def _on_activity_loaded(self, activity: List[dict]):
        self._cleanup_activity_thread()
        self._activity_seconds_left = 15
        self.activity_refresh_label.setText("Refreshing in 15s")
        for w in self._activity_items:
            w.deleteLater()
        self._activity_items.clear()
        while self._activity_layout.count():
            item = self._activity_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, entry in enumerate(activity[:15]):
            date_diff = entry.get("date_diff", "")
            user_name = entry.get("user_name", "")
            entry_type = entry.get("type", "")  # "blood", "user", or "root"
            blood_type = entry.get("blood_type", "")  # "user" or "root" when type=="blood"
            avatar_url = entry.get("user_avatar", "") or entry.get("avatar", "")
            if avatar_url and not avatar_url.startswith("http"):
                avatar_url = f"https://labs.hackthebox.com{avatar_url}"
            row = ActivityItem(date_diff, user_name, entry_type, blood_type, avatar_url)
            self._activity_layout.addWidget(row)
            self._activity_items.append(row)
            if avatar_url:
                req = QNetworkRequest(QUrl(avatar_url))
                reply = self._activity_network.get(req)
                reply.setProperty("index", i)

    @Slot(QNetworkReply)
    def _on_activity_avatar_loaded(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NoError:
            reply.deleteLater()
            return
        idx = reply.property("index")
        if idx is not None and 0 <= idx < len(self._activity_items):
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                self._activity_items[idx].set_avatar_pixmap(pixmap)
        reply.deleteLater()

    @Slot(QNetworkReply)
    def _on_machine_avatar_loaded(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NoError:
            reply.deleteLater()
            return
        data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        if not pixmap.isNull():
            # Escalar y redondear esquinas
            from PySide6.QtGui import QPainter, QPainterPath
            scaled = pixmap.scaled(48, 48, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            rounded = QPixmap(48, 48)
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 48, 48, 8, 8)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, 48, 48, scaled)
            painter.end()
            self.machine_avatar.setPixmap(rounded)
            self.machine_avatar.setStyleSheet("border-radius: 8px; background: transparent;")
        reply.deleteLater()

    def _on_stop_clicked(self):
        if not self._active_machine_id:
            return
        r = QMessageBox.question(
            self, "Confirm", "Stop this machine?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if r != QMessageBox.Yes:
            return
        self._run_action("terminate")

    def _on_reset_clicked(self):
        if not self._active_machine_id:
            return
        r = QMessageBox.question(
            self, "Confirm", "Reset this machine?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if r != QMessageBox.Yes:
            return
        self._run_action("reset")

    def _on_submit_flag_clicked(self):
        if not self._active_machine_id:
            return
        flag = self.flag_input.text().strip()
        if not flag:
            QMessageBox.warning(self, "Flag", "Enter a flag.")
            return
        self._run_action("flag", flag)

    def _run_action(self, action: str, flag: str = ""):
        self._cleanup_action_thread()
        self._action_thread = QThread()
        self._action_worker = DashboardActionWorker(action, self._active_machine_id, flag)
        self._action_worker.moveToThread(self._action_thread)
        self._action_thread.started.connect(self._action_worker.run)
        self._action_worker.finished.connect(self._on_action_done)
        self._action_worker.error.connect(self._on_action_error)
        self._action_thread.start()

    @Slot(dict)
    def _on_action_done(self, data: dict):
        self._cleanup_action_thread()
        action = data.get("action", "")
        msg = data.get("result", {}).get("message", "Done.")
        if action == "terminate":
            self._active_machine_id = None
            self.machine_name.setText("No active machine")
            self.machine_info.setText("Spawn a machine from the Machines page to start hacking")
            self.machine_ip.setText("")
            self.copy_ip_btn.setVisible(False)
            self.actions_widget.setVisible(False)
            self.activity_header.setVisible(False)
            self.activity_refresh_label.setVisible(False)
            self.activity_scroll.setVisible(False)
            self._activity_timer.stop()
            self._activity_countdown.stop()
        if action == "flag":
            self.flag_input.clear()
        QMessageBox.information(self, "Success", msg)

    @Slot(str)
    def _on_action_error(self, error: str):
        self._cleanup_action_thread()
        QMessageBox.warning(self, "Error", error)
    
    @Slot(dict)
    def _on_loaded(self, data: dict):
        self._loading = False
        self._cleanup_thread()
        
        if "user" in data:
            u = data["user"]
            self.welcome_label.setText(f"Welcome back, {u.name}!")
            self.username_label.setText(u.name)
            self._update_card(self.sub_card, u.subscription_display)
            self._update_card(self.rank_card, f"Server {u.server_id}")
            if u.avatar_url:
                self._load_avatar(u.avatar_url)
            else:
                self._set_avatar_placeholder(u.name)
        
        if "active_machine" in data and data["active_machine"]:
            m = data["active_machine"]
            self._active_machine_id = m.id
            self.machine_name.setText(f"🖥️ {m.name}")
            self.machine_info.setText(m.status_text)
            ip_text = m.ip if m.ip else "Starting..."
            self.machine_ip.setText(ip_text)
            self.copy_ip_btn.setVisible(bool(m.ip))
            self.actions_widget.setVisible(True)
            self.activity_header.setVisible(True)
            self.activity_refresh_label.setVisible(True)
            self.activity_scroll.setVisible(True)
            self._activity_seconds_left = 15
            self.activity_refresh_label.setText("Refreshing in 15s")
            self._load_activity()
            self._activity_timer.start()
            self._activity_countdown.start()
            # Cargar avatar de la máquina
            if m.avatar:
                self._active_machine_avatar = m.avatar
                self.machine_avatar.setVisible(True)
                req = QNetworkRequest(QUrl(m.avatar))
                self._machine_avatar_network.get(req)
            else:
                self.machine_avatar.setVisible(False)
        else:
            self._active_machine_id = None
            self._active_machine_avatar = ""
            self.machine_name.setText("No active machine")
            self.machine_info.setText("Spawn a machine from the Machines page to start hacking")
            self.machine_ip.setText("")
            self.copy_ip_btn.setVisible(False)
            self.actions_widget.setVisible(False)
            self.activity_header.setVisible(False)
            self.activity_refresh_label.setVisible(False)
            self.activity_scroll.setVisible(False)
            self.machine_avatar.setVisible(False)
            self._activity_timer.stop()
            self._activity_countdown.stop()
        
        if "connection" in data and data["connection"]:
            c = data["connection"]
            self.vpn_status.setText(f"🟢 {c.server_friendly_name}")
            self.vpn_details.setText(c.ip_display)
        else:
            self.vpn_status.setText("🔴 Disconnected")
            self.vpn_details.setText("Connect via VPN to access machines")
    
    @Slot(str)
    def _on_error(self, error: str):
        self._loading = False
        self._cleanup_thread()
        debug_log("DASHBOARD", f"Error: {error}")
    
    def showEvent(self, event):
        super().showEvent(event)
        self.load_data()
    
    def hideEvent(self, event):
        super().hideEvent(event)
        self._activity_timer.stop()
        self._activity_countdown.stop()
        self._cleanup_thread()
        self._cleanup_activity_thread()
        self._cleanup_action_thread()
