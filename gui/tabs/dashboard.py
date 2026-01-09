from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QGridLayout, QPushButton
)
from PySide6.QtCore import Qt, QTimer, QDate, QTime, QSize, Signal, QThread
from PySide6.QtGui import QFont, QColor

from qfluentwidgets import (
    CardWidget, TitleLabel, BodyLabel, StrongBodyLabel, 
    FluentIcon as FIF, IconWidget, TransparentToolButton,
    SimpleCardWidget, ImageLabel, PillToolButton
)

from core.news import news_manager
from core.tasks import task_manager
from core.calendar import calendar_manager
from datetime import datetime

# --- Components ---

from core.weather import weather_manager

class GreetingsHeader(QWidget):
    """
    Header showing "Good [Morning/Afternoon/Evening]" and Bubbles (Time | Weather).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 20)
        self.layout.setSpacing(15)
        
        # Text Block
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        self.sub_label = BodyLabel("Welcome back, User")
        self.sub_label.setStyleSheet("color: #8b9bb4;")
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 42px; font-weight: bold; color: #33b5e5; font-family: 'Segoe UI', sans-serif;")
        
        self.date_label = BodyLabel()
        self.date_label.setStyleSheet("color: #8b9bb4; font-size: 14px;")
        
        text_layout.addWidget(self.sub_label)
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.date_label)
        
        self.layout.addLayout(text_layout)
        self.layout.addStretch()
        
        # --- Bubbles Container ---
        # We use a container to hold the two bubbles side-by-side or grouped
        bubbles_layout = QHBoxLayout()
        bubbles_layout.setSpacing(15)
        
        # 1. Time Bubble
        self.time_bubble = QFrame()
        self.time_bubble.setFixedSize(160, 100)
        self.time_bubble.setStyleSheet("""
            QFrame {
                background-color: #0f1524;
                border: 1px solid #1a2236;
                border-radius: 20px;
            }
        """)
        tb_layout = QVBoxLayout(self.time_bubble)
        tb_layout.setAlignment(Qt.AlignCenter)
        
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet("color: #e8eaed; font-size: 28px; font-weight: bold;")
        tb_layout.addWidget(self.clock_label)
        
        bubbles_layout.addWidget(self.time_bubble)
        
        # 2. Weather Bubble
        self.weather_bubble = QFrame()
        self.weather_bubble.setFixedSize(160, 100)
        self.weather_bubble.setStyleSheet("""
            QFrame {
                background-color: #0f1524;
                border: 1px solid #1a2236;
                border-radius: 20px;
            }
        """)
        wb_layout = QVBoxLayout(self.weather_bubble)
        wb_layout.setAlignment(Qt.AlignCenter)
        wb_layout.setSpacing(5)
        
        # Icon Area
        # Using a label for emoji or IconWidget
        self.w_icon_label = QLabel("☁️") # Default emoji
        self.w_icon_label.setStyleSheet("font-size: 24px; background: transparent;")
        self.w_icon_label.setAlignment(Qt.AlignCenter)
        
        self.temp_label = QLabel("--°F")
        self.temp_label.setStyleSheet("color: #e8eaed; font-size: 18px; font-weight: bold;")
        
        self.cond_label = QLabel("Loading...")
        self.cond_label.setStyleSheet("color: #8b9bb4; font-size: 12px;")
        
        wb_layout.addWidget(self.w_icon_label)
        wb_layout.addWidget(self.temp_label)
        wb_layout.addWidget(self.cond_label)
        
        bubbles_layout.addWidget(self.weather_bubble)
        
        self.layout.addLayout(bubbles_layout)
        
        # Timer
        self._update_time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000) 
        
        # Weather update (async would be better, but simple timer fits pattern)
        # Fetch immediately then every 15 mins
        self._fetch_weather()
        self.w_timer = QTimer(self)
        self.w_timer.timeout.connect(self._fetch_weather)
        self.w_timer.start(900000) 

    def _update_time(self):
        now = datetime.now()
        hour = now.hour
        
        if 5 <= hour < 12:
            greeting = "Good Morning"
        elif 12 <= hour < 18:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"
            
        self.title_label.setText(greeting)
        self.date_label.setText("📅 " + QDate.currentDate().toString("dddd, MMMM d"))
        self.clock_label.setText(QTime.currentTime().toString("h:mm AP"))

    def _fetch_weather(self):
        # Run in thread to avoid freeze
        self._thread = QThread()
        self._worker = WeatherWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_weather_loaded)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_weather_loaded(self, data):
        if not data:
            self.cond_label.setText("Offline")
            return
            
        temp = data['temp']
        code = data['code']
        
        self.temp_label.setText(f"{int(temp)}°F")
        
        # Mapping Code to Emoji/Text
        # 0: Clear (☀️), 1-3: Cloud (☁️), 45+: Cloud/Fog, 51+: Rain (🌧️), 71+: Snow (❄️), 95+: Storm (⚡)
        if code == 0:
            icon, text = "☀️", "Clear"
        elif code in [1, 2, 3]:
            icon, text = "⛅", "Cloudy"
        elif code in [45, 48]:
            icon, text = "🌫️", "Foggy"
        elif code in [51, 53, 55, 61, 63, 65]:
            icon, text = "🌧️", "Rain"
        elif code in [71, 73, 75, 85, 86]:
            icon, text = "❄️", "Snow"
        elif code >= 95:
             icon, text = "⚡", "Storm"
        else:
             icon, text = "🌡️", "Unknown"
             
        self.w_icon_label.setText(icon)
        self.cond_label.setText(text)

class WeatherWorker(QThread):
    finished = Signal(dict)
    def run(self):
        data = weather_manager.get_weather()
        self.finished.emit(data or {})


class StatCard(CardWidget):
    """
    Square/Rectangular card for quick stats (Agenda, Devices, etc).
    """
    def __init__(self, icon: FIF, title: str, count: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 110)
        self.setBorderRadius(16)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 25, 20)
        
        # Left Side: Icon + Title
        left = QVBoxLayout()
        left.setSpacing(15)
        
        # Icon bubble
        icon_bubble = QLabel()
        icon_bubble.setFixedSize(40, 40)
        icon_bubble.setAlignment(Qt.AlignCenter)
        # Using a QFrame approach or just styling the label
        # Since I can't easily embed FluentIcon in stylesheet, use IconWidget in a container
        
        ib_container = QFrame()
        ib_container.setFixedSize(40, 40)
        ib_container.setStyleSheet("background-color: #1a2236; border-radius: 12px;")
        ib_layout = QVBoxLayout(ib_container)
        ib_layout.setContentsMargins(0,0,0,0)
        ib_layout.setAlignment(Qt.AlignCenter)
        
        iw = IconWidget(icon)
        iw.setFixedSize(20, 20)
        # Tint icon
        # iw.setStyleSheet("color: #33b5e5;") # IconWidget doesn't style this way easily
        ib_layout.addWidget(iw)
        
        left.addWidget(ib_container)
        
        lbl = BodyLabel(title)
        lbl.setStyleSheet("color: #8b9bb4; font-size: 13px; font-weight: 500;")
        left.addWidget(lbl)
        
        layout.addLayout(left)
        layout.addStretch()
        
        # Right Side: Big Number
        num = QLabel(str(count))
        num.setStyleSheet("font-size: 28px; font-weight: bold; color: #e8eaed;")
        num.setAlignment(Qt.AlignRight | Qt.AlignTop)
        layout.addWidget(num)

    def set_count(self, count):
        # find the label and update (simple version: rebuild or keep ref)
        # Keeping it simple for static init, dynamic update would require saving ref
        pass

class HomeScenesCard(CardWidget):
    """
    Card with Home Scene buttons.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 160)
        self.setBorderRadius(16)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        t1 = StrongBodyLabel("Home Scenes")
        t2 = BodyLabel("Instant environmental adjustments.")
        t2.setStyleSheet("color: #6e7a8e; font-size: 12px;")
        
        layout.addWidget(t1)
        layout.addWidget(t2)
        
        # Buttons
        btns = QHBoxLayout()
        b1 = QPushButton("Focus Mode")
        b1.setStyleSheet("""
            QPushButton {
                background-color: #1a2236; color: #e8eaed; border: 1px solid #1a2236; 
                border-radius: 8px; padding: 8px; font-weight: bold;
            }
            QPushButton:hover { background-color: #232d45; }
        """)
        
        b2 = QPushButton("Relax")
        b2.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #e8eaed; border: 1px solid #1a2236; 
                border-radius: 8px; padding: 8px; font-weight: bold;
            }
            QPushButton:hover { background-color: #1a2236; }
        """)
        
        btns.addWidget(b1)
        btns.addWidget(b2)
        layout.addLayout(btns)


class IntelligenceItem(QFrame):
    """
    Single row in the Intelligence Feed.
    """
    def __init__(self, icon: FIF, title: str, description: str, time_str: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(15)
        
        # Icon
        ic_bg = QFrame()
        ic_bg.setFixedSize(36, 36)
        ic_bg.setStyleSheet("background-color: #141c2f; border-radius: 10px;")
        icl = QVBoxLayout(ic_bg)
        icl.setContentsMargins(0,0,0,0)
        icl.setAlignment(Qt.AlignCenter)
        icl.addWidget(IconWidget(icon))
        
        layout.addWidget(ic_bg)
        
        # Content
        col = QVBoxLayout()
        col.setSpacing(4)
        
        top_line = QHBoxLayout()
        t_lbl = StrongBodyLabel(title)
        time_lbl = BodyLabel(time_str)
        time_lbl.setStyleSheet("color: #6e7a8e; font-size: 11px;")
        
        top_line.addWidget(t_lbl)
        top_line.addStretch()
        top_line.addWidget(time_lbl)
        
        desc_lbl = BodyLabel(description)
        desc_lbl.setStyleSheet("color: #8b9bb4; font-size: 12px;")
        desc_lbl.setWordWrap(True)
        
        col.addLayout(top_line)
        col.addWidget(desc_lbl)
        
        layout.addLayout(col)

class IntelligenceFeed(CardWidget):
    """
    Main content area: System Intelligence.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBorderRadius(20)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 25, 30, 30)
        self.layout.setSpacing(20)
        
        # Header
        h_layout = QHBoxLayout()
        h = TitleLabel("System Intelligence", self)
        h.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        live_tag = QLabel("Live Updates")
        live_tag.setStyleSheet("""
            background-color: #1a2236; color: #8b9bb4; 
            padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: bold;
        """)
        
        h_layout.addWidget(h)
        h_layout.addStretch()
        h_layout.addWidget(live_tag)
        
        self.layout.addLayout(h_layout)
        
        # Mock Items + Real News
        # Using real data where possible
        
        # 1. Daily Focus (Mock logic for now)
        self.layout.addWidget(IntelligenceItem(
            FIF.TILES, # Fallback safe icon
            "Daily Focus",
            "You have a clear window between 2 PM and 4 PM. Suggested for 'Product Strategy'.",
            "5M AGO"
        ))
        
        # Separator
        sep1 = QFrame()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet("background-color: #1a2236;")
        self.layout.addWidget(sep1)
        
        # 2. News (Real)
        news = news_manager.get_briefing()
        if news:
            top = news[0]
            self.layout.addWidget(IntelligenceItem(
                FIF.WIFI, # News icon
                "Intel Alert", # Source
                top['title'],
                "12M AGO"
            ))
        else:
             self.layout.addWidget(IntelligenceItem(
                FIF.WIFI, 
                "Intel Alert",
                "No active intelligence streams detected.",
                "NOW"
            ))
            
        # Separator
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background-color: #1a2236;")
        self.layout.addWidget(sep2)
        
        # 3. Energy Saving (Mock)
        self.layout.addWidget(IntelligenceItem(
                FIF.SPEED_HIGH, 
                "Energy Saving",
                "Living Room lights dimmed to 40% based on ambient sunlight.",
                "1H AGO"
        ))
        
        self.layout.addStretch()
        
        # Upcoming Priority Card (Embedded at bottom)
        self.priority = PriorityCard()
        self.layout.addWidget(self.priority)

class PriorityCard(QFrame):
    """
    Blue gradient card for next priority.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #33b5e5, stop:1 #4a68af);
                border-radius: 16px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 0, 25, 0)
        
        # Text
        txt = QVBoxLayout()
        txt.setAlignment(Qt.AlignVCenter)
        txt.setSpacing(5)
        
        l1 = QLabel("Upcoming Priority")
        l1.setStyleSheet("color: white; font-weight: bold; font-size: 16px; background: transparent;")
        
        # Fetch next event
        next_event = self._get_next_event()
        l2 = QLabel(next_event['title'])
        l2.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 14px; background: transparent;")
        
        l3 = QLabel(f"Starts in {next_event['starts_in']}")
        l3.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px; background: transparent;")
        
        txt.addWidget(l1)
        txt.addWidget(l2)
        txt.addWidget(l3)
        
        layout.addLayout(txt)
        layout.addStretch()
        
        # Button
        btn = QPushButton("Details")
        btn.setFixedSize(80, 32)
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.2);
                color: white;
                border-radius: 8px;
                border: 1px solid rgba(255,255,255,0.3);
                font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.3); }
        """)
        layout.addWidget(btn)

    def _get_next_event(self):
        # Mock logic or real fetch
        # For now return mock if no events
        return {
            "title": "Market Strategy Review",
            "starts_in": "45 minutes"
        }

class DashboardView(QWidget):
    """
    The main 'System Intelligence' Dashboard.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardView")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # 1. Greeting Header
        self.header = GreetingsHeader()
        main_layout.addWidget(self.header)
        
        # 2. Main Content Area (2 Columns)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(25)
        
        # --- Left Column (Stats) ---
        left_col = QVBoxLayout()
        left_col.setSpacing(20)
        
        # Stat 1: Planner
        tasks_count = len([t for t in task_manager.get_tasks() if not t.get('completed')])
        left_col.addWidget(StatCard(FIF.CALENDAR, "Planner Agenda", str(tasks_count)))
        
        # Stat 2: Devices (Mock)
        left_col.addWidget(StatCard(FIF.CODE, "Active Devices", "3"))
        
        # Stat 3: Unread News
        # Count available news
        news_count = len(news_manager.get_briefing())
        left_col.addWidget(StatCard(FIF.TILES, "Unread News", str(news_count)))
        
        # Home Scenes
        left_col.addWidget(HomeScenesCard())
        
        left_col.addStretch()
        content_layout.addLayout(left_col)
        
        # --- Right Column (Feed) ---
        self.feed = IntelligenceFeed()
        # Feed card should expand
        content_layout.addWidget(self.feed, 1)
        
        main_layout.addLayout(content_layout)
