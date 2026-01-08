from PySide6.QtWidgets import QFrame, QVBoxLayout
from PySide6.QtCore import Qt

from qfluentwidgets import (
    PrimaryPushButton, FluentIcon as FIF, 
    TitleLabel, BodyLabel, CardWidget, IconWidget
)

class HomeAutomationTab(QFrame):
    """
    Placeholder tab for Home Automation integration.
    """
    def __init__(self):
        super().__init__()
        self.setObjectName("homeAutomationView")
        # Remove custom gradient, let Fluent window background show (or use transparent)
        self.setStyleSheet("background: transparent;")
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Container Card
        card = CardWidget()
        card.setFixedSize(500, 400)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(15)
        
        # Icon
        icon = IconWidget(FIF.HOME)
        icon.setFixedSize(64, 64)
        card_layout.addWidget(icon)
        
        # Title
        title = TitleLabel("Home Automation")
        card_layout.addWidget(title)
        
        # Description
        desc = BodyLabel("Connect your Home Assistant to control devices directly from Pocket AI.")
        desc.setStyleSheet("color: #8a8a8a;")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(desc)
        
        # Placeholder Button
        btn = PrimaryPushButton(FIF.LINK, "Connect Home Assistant")
        btn.setFixedWidth(200)
        card_layout.addWidget(btn)
        
        layout.addWidget(card)
