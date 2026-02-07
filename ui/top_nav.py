"""Top navigation bar - HTB style, sin sidebar."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor

from ui.styles import HTB_GREEN, HTB_TEXT_DIM, TOP_NAV_STYLE


class TopNav(QWidget):
    page_changed = Signal(str)

    PAGES = [
        ("dashboard", "Dashboard"),
        ("machines", "Machines"),
        ("seasons", "Seasons"),
        ("vpn", "VPN"),
        ("settings", "Settings"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("top_nav")
        self.setFixedHeight(56)
        self.setStyleSheet(TOP_NAV_STYLE)
        self._buttons = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(0)

        # Logo
        logo = QLabel("⬡ HACK THE BOX")
        logo.setObjectName("nav_logo")
        logo.setCursor(Qt.PointingHandCursor)
        logo.mousePressEvent = lambda e: self._on_click("dashboard") if e.button() == Qt.LeftButton else None
        layout.addWidget(logo)

        layout.addStretch()

        # Nav items
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        for page_id, label in self.PAGES:
            btn = QPushButton(label)
            btn.setObjectName("nav_item")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, p=page_id: self._on_click(p))
            self.button_group.addButton(btn)
            self._buttons[page_id] = btn
            layout.addWidget(btn)

    def _on_click(self, page_id: str):
        self.page_changed.emit(page_id)

    def set_active(self, page_id: str):
        if page_id in self._buttons:
            self._buttons[page_id].setChecked(True)
