from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QTimer, QTime
from core.tasks import task_manager # We'll extend task_manager to handle alarms too

class AlarmComponent(QWidget):
    """Alarm Component for setting reminders."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_alarms()
        
        # Background checking timer
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self._check_alarms)
        self.check_timer.start(5000) # Check every 5 seconds (not precise but efficient)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 35, 200);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        self.card_layout = QVBoxLayout(card)
        self.card_layout.setContentsMargins(20, 20, 20, 20)
        self.card_layout.setSpacing(15)
        
        # Header
        header = QHBoxLayout()
        lbl = QLabel("ALARMS")
        lbl.setStyleSheet("color: #e8eaed; font-size: 14px; font-weight: bold; letter-spacing: 1px; background: transparent; border: none;")
        header.addWidget(lbl)
        header.addStretch()
        
        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(79, 142, 247, 0.2);
                color: #4F8EF7;
                border: 1px solid #4F8EF7;
                border-radius: 14px;
                font-weight: bold;
                font-size: 16px;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background-color: rgba(79, 142, 247, 0.3);
            }
        """)
        add_btn.clicked.connect(self._add_alarm_dialog)
        header.addWidget(add_btn)
        
        self.card_layout.addLayout(header)
        
        # List
        self.alarm_list = QListWidget()
        self.alarm_list.setStyleSheet("background: transparent; border: none; outline: none;")
        self.card_layout.addWidget(self.alarm_list)
        
        layout.addWidget(card)
        
    def _add_alarm_dialog(self):
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "New Alarm", "Enter time (HH:MM or HH:MM AM/PM):")
        if ok and text:
            # Parse time loosely
            try:
                # Store normalized 24h format HH:MM
                from dateutil import parser
                dt = parser.parse(text)
                time_str = dt.strftime("%H:%M")
                
                # Add to DB
                task_manager.add_alarm(time_str, "Alarm")
                self._load_alarms()
            except:
                pass # Invalid format ignored for now

    def _load_alarms(self):
        self.alarm_list.clear()
        alarms = task_manager.get_alarms()
        for a in alarms:
            self._create_alarm_item(a)

    def _create_alarm_item(self, alarm):
        item = QListWidgetItem()
        item.setSizeHint(QScrollArea().sizeHint()) # specific size not needed
        item.setSizeHint(QFrame().sizeHint()) # Just dummy
        item.setSizeHint(QLabel().sizeHint()) # Reset
        # Actual height
        item.setSizeHint(QLabel("", self).fontMetrics().boundingRect("X").size()) 
        # Manual Size
        from PySide6.QtCore import QSize
        item.setSizeHint(QSize(0, 50))
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Time Label (convert back to AM/PM for display)
        time_24 = alarm['time']
        try:
            display_time = datetime.datetime.strptime(time_24, "%H:%M").strftime("%I:%M %p").lstrip("0")
        except:
            display_time = time_24
            
        lbl = QLabel(display_time)
        lbl.setStyleSheet("color: white; font-size: 16px; font-weight: 500;")
        layout.addWidget(lbl)
        
        layout.addStretch()
        
        # Delete Btn
        del_btn = QPushButton("×")
        del_btn.setFixedSize(24, 24)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton { color: #6e6e6e; background: transparent; border: none; font-size: 18px; font-weight: bold; }
            QPushButton:hover { color: #ef5350; }
        """)
        # Capture ID
        a_id = alarm['id']
        del_btn.clicked.connect(lambda checked=False, aid=a_id: self._delete_alarm(aid))
        layout.addWidget(del_btn)
        
        self.alarm_list.addItem(item)
        self.alarm_list.setItemWidget(item, widget)

    def _delete_alarm(self, alarm_id):
        task_manager.delete_alarm(alarm_id)
        self._load_alarms()

    def _check_alarms(self):
        import datetime
        now = datetime.datetime.now().strftime("%H:%M")
        alarms = task_manager.get_alarms()
        
        # In a real app we'd track "fired" state to not repeat
        # For this prototype we just print if match
        for a in alarms:
            if a['time'] == now:
                # Play sound or show popup
                # Check recent history to avoid spam (simple debounce)
                pass 
