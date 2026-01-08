"""
Main PySide6 application setup and layout.
"""

import threading
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QScrollArea, QLineEdit, QPushButton, QLabel, QFrame,
    QListWidget, QListWidgetItem, QSizePolicy, QCheckBox, QMenu,
    QStackedWidget, QTabBar, QInputDialog
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QIcon

from core.llm import preload_models
from core.tts import tts
from core.history import history_manager
from core.tasks import task_manager
from gui.handlers import ChatHandlers
from gui.components import MessageBubble, ThinkingExpander, ToggleSwitch
from gui.components.schedule import ScheduleComponent
from gui.components.timer import TimerComponent
from gui.components.schedule import ScheduleComponent
from gui.components.timer import TimerComponent
from gui.components.schedule import ScheduleComponent
from gui.components.timer import TimerComponent
from gui.components.alarm import AlarmComponent
from gui.views.briefing_view import BriefingView


# Global stylesheet for the entire application
STYLESHEET = """
/* Main Window */
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #121212, stop:1 #1e1e24);
}

/* Sidebar */
QFrame#sidebar {
    background-color: rgba(30, 30, 35, 180);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

QLabel#sidebarTitle {
    color: #4F8EF7;
    font-size: 20px;
    font-weight: bold;
    padding: 15px;
    letter-spacing: 3px;
}

QPushButton#newChatBtn {
    background-color: rgba(255, 255, 255, 0.05);
    color: #e8eaed;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 12px 15px;
    font-size: 14px;
    font-weight: 500;
    text-align: left;
}

QPushButton#newChatBtn:hover {
    background-color: rgba(255, 255, 255, 0.1);
    border: 1px solid #4F8EF7;
    color: white;
}

QPushButton#newChatBtn:pressed {
    background-color: rgba(255, 255, 255, 0.15);
}

QListWidget#sessionList {
    background-color: transparent;
    border: none;
    outline: none;
    padding: 5px 10px;
}

QListWidget#sessionList::item {
    background-color: transparent;
    color: #9e9e9e;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 0;
    min-height: 36px;
}

QListWidget#sessionList::item:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: #e8eaed;
}

QListWidget#sessionList::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(79, 142, 247, 0.2), stop:1 rgba(79, 142, 247, 0.05));
    color: white;
    border-left: 2px solid #4F8EF7;
}

/* Chat Panel */
QFrame#chatPanel {
    background-color: transparent;
}

QFrame#chatHeader {
    background-color: rgba(30, 30, 35, 180);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

QLabel#headerTitle {
    color: #e8eaed;
    font-size: 16px;
    font-weight: 500;
}

QLabel#statusLabel {
    color: #6e6e6e;
    font-size: 12px;
}

/* Scroll Area */
QScrollArea#chatScroll {
    background-color: transparent;
    border: none;
}

QScrollArea#chatScroll > QWidget > QWidget {
    background-color: transparent;
}

QScrollBar:vertical {
    background: transparent;
    width: 6px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.3);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* Input Area */
QFrame#inputBar {
    background-color: rgba(30, 30, 35, 180);
    border-top: 1px solid rgba(255, 255, 255, 0.08);
}

QLineEdit#userInput {
    background-color: rgba(255, 255, 255, 0.05);
    color: #e8eaed;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 12px 20px;
    font-size: 14px;
}

QLineEdit#userInput:focus {
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid #4F8EF7;
}

QPushButton#sendBtn, QPushButton#stopBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4F8EF7, stop:1 #bd93f9);
    border: none;
    border-radius: 22px; /* Half of 44px */
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
    font-size: 16px;
}

QPushButton#sendBtn {
    color: white;
}

QPushButton#stopBtn {
    background-color: #ef5350; /* Keep red for stop */
    background: #ef5350;
    color: white;
}

QPushButton#sendBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3d7be5, stop:1 #a87df0);
}

QPushButton#sendBtn:pressed {
    background: #333;
}

/* TTS Toggle Switch */
QCheckBox#ttsToggle {
    color: #9e9e9e;
    font-size: 12px;
    spacing: 8px;
}

QCheckBox#ttsToggle::indicator {
    width: 44px;
    height: 24px;
    border-radius: 12px;
    background-color: #3d3d3d;
    border: 2px solid #3d3d3d;
}

QCheckBox#ttsToggle::indicator:checked {
    background-color: #4F8EF7;
    border: 2px solid #4F8EF7;
    image: none;
}

/* Delete button in session list */
QPushButton#deleteBtn {
    background-color: transparent;
    color: #6e6e6e;
    border: none;
    font-size: 14px;
    padding: 5px;
}

QPushButton#deleteBtn:hover {
    color: #ef5350;
}

/* Top Tab Bar */
QTabBar#topTabBar {
    background: transparent;
    border: none;
}

QTabBar#topTabBar::tab {
    background: transparent;
    color: #9e9e9e;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 500;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 8px;
}

QTabBar#topTabBar::tab:hover {
    color: #e8eaed;
    background: #2b2d31;
}

QTabBar#topTabBar::tab:selected {
    color: #4F8EF7;
    border-bottom: 2px solid #4F8EF7;
}

/* Planner Panel */
QFrame#plannerPanel {
    background-color: #1a1c1e;
}

QLineEdit#taskInput {
    background-color: #2b2d31;
    color: #e8eaed;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
}

QLineEdit#taskInput:focus {
    background-color: #33363b;
}

QPushButton#addTaskBtn {
    background-color: #4F8EF7;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: 500;
}

QPushButton#addTaskBtn:hover {
    background-color: #3d7be5;
}

QListWidget#taskList {
    background-color: transparent;
    border: none;
    outline: none;
    padding: 10px;
}

QListWidget#taskList::item {
    background-color: #2b2d31;
    color: #e8eaed;
    border-radius: 8px;
    padding: 0px;
    margin: 6px 10px;
    min-height: 48px;
}

QListWidget#taskList::item:hover {
    background-color: #33363b;
}

QListWidget#taskList::item:selected {
    background-color: #343541;
    border: 1px solid #4F8EF7;
}

QCheckBox#taskCheckbox {
    color: #e8eaed;
    font-size: 14px;
    spacing: 10px;
}

QCheckBox#taskCheckbox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    background-color: #3d3d3d;
    border: 1px solid #5d5d5d;
}

QCheckBox#taskCheckbox::indicator:checked {
    background-color: #4F8EF7;
    border: 1px solid #4F8EF7;
}

QCheckBox#taskCheckbox::indicator:hover {
    border: 1px solid #4F8EF7;
}
"""


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A.D.A")
        self.setMinimumSize(1000, 700)
        self.resize(1000, 700)
        
        # Apply global stylesheet
        self.setStyleSheet(STYLESHEET)
        
        # Initialize handlers
        self.handlers = ChatHandlers(self)
        
        self._setup_ui()
        self._connect_signals()
        self._init_background()
        self._load_tasks()
        
    def _load_tasks(self):
        """Load tasks from persistent storage."""
        tasks = task_manager.get_tasks()
        for task in tasks:
            self._create_task_item(task)
            
        self._update_task_counter()
        
    def _setup_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Top Tab Bar (persistent across all views) ---
        tab_bar_container = QFrame()
        tab_bar_container.setObjectName("chatPanel")
        tab_bar_layout = QVBoxLayout(tab_bar_container)
        tab_bar_layout.setContentsMargins(0, 0, 0, 0)
        tab_bar_layout.setSpacing(0)
        
        self.top_tab_bar = QTabBar()
        self.top_tab_bar.setObjectName("topTabBar")
        self.top_tab_bar.addTab("💬  Chat")
        self.top_tab_bar.addTab("📋  Planner")
        self.top_tab_bar.addTab("📰  Briefing")
        self.top_tab_bar.setExpanding(False)
        self.top_tab_bar.currentChanged.connect(self._on_tab_changed)
        tab_bar_layout.addWidget(self.top_tab_bar)
        
        # Tab bar divider
        tab_divider = QFrame()
        tab_divider.setFixedHeight(1)
        tab_divider.setStyleSheet("background-color: #3d3d3d;")
        tab_bar_layout.addWidget(tab_divider)
        
        main_layout.addWidget(tab_bar_container)
        
        # --- Stacked Widget for tab content ---
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        # --- Chat Page (Page 0) - Contains Sidebar + Chat Area ---
        chat_page = QWidget()
        chat_page_layout = QHBoxLayout(chat_page)
        chat_page_layout.setContentsMargins(0, 0, 0, 0)
        chat_page_layout.setSpacing(0)
        
        # --- Sidebar (inside Chat tab) ---
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Title
        title_label = QLabel("A.D.A")
        title_label.setObjectName("sidebarTitle")
        sidebar_layout.addWidget(title_label)
        
        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #3d3d3d;")
        sidebar_layout.addWidget(divider)
        
        # New Chat Button
        new_chat_container = QWidget()
        new_chat_layout = QHBoxLayout(new_chat_container)
        new_chat_layout.setContentsMargins(10, 10, 10, 5)
        
        self.new_chat_btn = QPushButton("➕  New Chat")
        self.new_chat_btn.setObjectName("newChatBtn")
        new_chat_layout.addWidget(self.new_chat_btn)
        sidebar_layout.addWidget(new_chat_container)
        
        # Session List
        self.session_list = QListWidget()
        self.session_list.setObjectName("sessionList")
        self.session_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.session_list.customContextMenuRequested.connect(self._show_session_context_menu)
        sidebar_layout.addWidget(self.session_list)
        
        chat_page_layout.addWidget(self.sidebar)
        
        # --- Chat Content Area ---
        chat_content = QFrame()
        chat_content.setObjectName("chatPanel")
        chat_layout = QVBoxLayout(chat_content)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setObjectName("chatHeader")
        header.setFixedHeight(50)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        header_title = QLabel("Chat")
        header_title.setObjectName("headerTitle")
        header_layout.addWidget(header_title)
        
        header_layout.addStretch()
        
        # TTS Toggle
        tts_label = QLabel("Voice")
        tts_label.setStyleSheet("color: #9e9e9e; font-size: 12px;")
        header_layout.addWidget(tts_label)
        
        self.tts_toggle = ToggleSwitch(checked=False)
        header_layout.addWidget(self.tts_toggle)
        
        chat_layout.addWidget(header)
        
        # Status
        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setContentsMargins(20, 5, 20, 5)
        chat_layout.addWidget(self.status_label)
        
        # Divider
        divider2 = QFrame()
        divider2.setFixedHeight(1)
        divider2.setStyleSheet("background-color: #3d3d3d;")
        chat_layout.addWidget(divider2)
        
        # Chat Scroll Area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setObjectName("chatScroll")
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_layout.setSpacing(15)
        self.chat_layout.addStretch()
        
        self.chat_scroll.setWidget(self.chat_container)
        chat_layout.addWidget(self.chat_scroll)
        
        # Input Bar
        input_bar = QFrame()
        input_bar.setObjectName("inputBar")
        input_bar.setFixedHeight(76)
        input_layout = QHBoxLayout(input_bar)
        input_layout.setContentsMargins(15, 16, 15, 16)
        input_layout.setSpacing(12)
        input_layout.setAlignment(Qt.AlignVCenter)
        
        self.user_input = QLineEdit()
        self.user_input.setObjectName("userInput")
        self.user_input.setPlaceholderText("Ask something...")
        input_layout.addWidget(self.user_input)
        
        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setVisible(False)
        self.stop_btn.setToolTip("Stop Generation")
        input_layout.addWidget(self.stop_btn)
        
        self.send_btn = QPushButton("➤")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setToolTip("Send")
        input_layout.addWidget(self.send_btn)
        
        chat_layout.addWidget(input_bar)
        
        chat_page_layout.addWidget(chat_content)
        
        self.content_stack.addWidget(chat_page)
        
        # --- Planner Panel (Page 1) ---
        # --- Planner Panel (Page 1) ---
        planner_page = QFrame()
        planner_page.setObjectName("plannerPanel")
        planner_page.setStyleSheet("""
            QFrame#plannerPanel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #121212, stop:1 #1e1e24);
            }
        """)
        planner_layout = QHBoxLayout(planner_page)
        planner_layout.setContentsMargins(30, 30, 30, 30)
        planner_layout.setSpacing(25)
        
        # --- Column 1: Focus Tasks ---
        tasks_col = QFrame()
        tasks_col.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 35, 200);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        tasks_layout = QVBoxLayout(tasks_col)
        tasks_layout.setContentsMargins(20, 25, 20, 25)
        tasks_layout.setSpacing(15)
        
        # Task Header
        t_title = QLabel("FOCUS TASKS")
        t_title.setStyleSheet("color: #e8eaed; font-size: 14px; font-weight: bold; letter-spacing: 1px; background: transparent; border: none;")
        tasks_layout.addWidget(t_title)
        
        # New Task Input (Top)
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Add a new task...")
        self.task_input.returnPressed.connect(self._add_task) # Reusing legacy add_task which uses self.task_input
        self.task_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: white;
                padding: 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #bd93f9;
                background: rgba(189, 147, 249, 0.05);
            }
        """)
        tasks_layout.addWidget(self.task_input)
        
        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); border: none;")
        tasks_layout.addWidget(div)
        
        # Task Lists (Active)
        self.task_list = QListWidget()
        self.task_list.setObjectName("taskList")
        self.task_list.setStyleSheet("background: transparent; border: none;") # Override global style
        tasks_layout.addWidget(self.task_list, 1) # Stretch to fill
        
        # Completed Section
        self.completed_header = QPushButton("▼  Completed  0")
        self.completed_header.setObjectName("completedHeader")
        self.completed_header.setCursor(Qt.PointingHandCursor)
        self.completed_header.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #6e6e6e;
                font-size: 12px;
                font-weight: 500;
                border: none;
                text-align: left;
                padding: 10px 0;
            }
            QPushButton:hover { color: #e8eaed; }
        """)
        self.completed_header.clicked.connect(self._toggle_completed_section)
        tasks_layout.addWidget(self.completed_header)
        
        self.completed_list = QListWidget()
        self.completed_list.setObjectName("taskList")
        self.completed_list.setStyleSheet("background: transparent; border: none;")
        self.completed_list.setVisible(False)
        self.completed_expanded = False
        tasks_layout.addWidget(self.completed_list)
        

        
        # Task Counter (Hidden/Small)
        self.task_counter = QLabel("0 tasks")
        self.task_counter.setStyleSheet("color: #6e6e6e; font-size: 11px; margin-top: 5px;")
        self.task_counter.setAlignment(Qt.AlignCenter)
        tasks_layout.addWidget(self.task_counter)
        
        planner_layout.addWidget(tasks_col, 1)
        
        # --- Column 2: Today's Schedule ---
        schedule_col = QFrame()
        schedule_col.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 35, 200);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        schedule_col.setLayout(QVBoxLayout())
        schedule_col.layout().setContentsMargins(20, 25, 20, 25)
        
        self.schedule_component = ScheduleComponent()
        schedule_col.layout().addWidget(self.schedule_component)
        
        planner_layout.addWidget(schedule_col, 1)
        
        # --- Column 3: Flow State ---
        flow_col = QFrame()
        flow_col.setFixedWidth(320)
        flow_col.setStyleSheet("background: transparent; border: none;") # Wrapper is transparent
        flow_layout = QVBoxLayout(flow_col)
        flow_layout.setContentsMargins(0, 0, 0, 0)
        flow_layout.setSpacing(25)
        
        self.timer_component = TimerComponent()
        flow_layout.addWidget(self.timer_component)
        
        self.alarm_component = AlarmComponent()
        flow_layout.addWidget(self.alarm_component)
        
        planner_layout.addWidget(flow_col)
        
        self.content_stack.addWidget(planner_page)

        # --- Briefing Panel (Page 2) ---
        self.briefing_view = BriefingView()
        self.content_stack.addWidget(self.briefing_view)
        

    
    def _on_tab_changed(self, index: int):
        """Handle tab bar selection changes."""
        self.content_stack.setCurrentIndex(index)
        
    def _add_task_dialog(self):
        """Show a dialog/popup to add a task (cleaner UI)."""
        text, ok = QInputDialog.getText(self, "Add Task", "Enter task:", QLineEdit.Normal)
        if ok and text:
            self._add_task_from_text(text)

    def _add_task(self):
        """(Legacy) Add a new task from the old input field."""
        if hasattr(self, 'task_input'):
            task_text = self.task_input.text().strip()
            if task_text:
                self._add_task_from_text(task_text)
                self.task_input.clear()
    
    def _add_task_from_text(self, task_text):
        """Internal helper to add task."""
        # Save to DB
        new_task = task_manager.add_task(task_text)
        if new_task:
            self._create_task_item(new_task)
        self._update_task_counter()
    
    def _on_task_checked(self, state: int, item: QListWidgetItem, source_list: QListWidget):
        """Handle task checkbox state change - move between lists."""
        widget = source_list.itemWidget(item)
        if not widget:
            return
            
        # Get task ID from data
        task_id = item.data(Qt.UserRole)
        
        # Get task text from label
        label = widget.findChild(QLabel)
        if not label:
            return
        
        task_text = label.text()
        row = source_list.row(item)
        is_completed = (state == Qt.Checked.value)
        
        # Update persistence
        task_manager.toggle_task(task_id, is_completed)
        
        # Start transition
        source_list.takeItem(row)
        
        # Re-create in correct list
        task_data = {"id": task_id, "text": task_text, "completed": is_completed}
        self._create_task_item(task_data)
        
        self._update_task_counter()
    
    def _create_task_item(self, task_data: dict):
        """Create a task item widget and add to appropriate list."""
        completed = task_data.get('completed', False)
        text = task_data.get('text', '')
        task_id = task_data.get('id')
        
        target_list = self.completed_list if completed else self.task_list
        
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, 56))
        item.setData(Qt.UserRole, task_id)  # Store ID
        
        task_widget = QWidget()
        task_widget.setMinimumHeight(48)
        task_layout = QHBoxLayout(task_widget)
        task_layout.setContentsMargins(16, 12, 16, 12)
        task_layout.setSpacing(12)
        
        # Checkbox
        checkbox = QCheckBox()
        checkbox.setObjectName("taskCheckbox")
        checkbox.setChecked(completed)
        checkbox.stateChanged.connect(lambda state, i=item, l=target_list: self._on_task_checked(state, i, l))
        task_layout.addWidget(checkbox)
        
        # Task label
        task_label = QLabel(text)
        if completed:
            task_label.setStyleSheet("color: #6e6e6e; font-size: 14px; padding: 2px 0; text-decoration: line-through;")
        else:
            task_label.setStyleSheet("color: #e8eaed; font-size: 14px; padding: 2px 0;")
        task_label.setWordWrap(False)
        task_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        task_layout.addWidget(task_label, 1)
        
        # Delete button
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(32, 32)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #6e6e6e;
                font-size: 14px;
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover {
                background: #3d3d3d;
                color: #ef5350;
            }
        """)
        delete_btn.clicked.connect(lambda: self._delete_task(item, target_list))
        task_layout.addWidget(delete_btn)
        
        target_list.addItem(item)
        target_list.setItemWidget(item, task_widget)
    
    def _delete_task(self, item: QListWidgetItem, source_list: QListWidget = None):
        """Delete a task from the list."""
        if source_list is None:
            source_list = self.task_list
            
        task_id = item.data(Qt.UserRole)
        task_manager.delete_task(task_id)
        
        row = source_list.row(item)
        if row >= 0:
            source_list.takeItem(row)
            self._update_task_counter()
    
    def _toggle_completed_section(self):
        """Toggle the completed tasks section visibility."""
        self.completed_expanded = not self.completed_expanded
        self.completed_list.setVisible(self.completed_expanded)
        
        # Update header arrow
        count = self.completed_list.count()
        arrow = "▼" if self.completed_expanded else "▶"
        self.completed_header.setText(f"{arrow}  Completed  {count}")
    
    def _update_task_counter(self):
        """Update the task counter label and completed header."""
        active_count = self.task_list.count()
        completed_count = self.completed_list.count()
        
        self.task_counter.setText(f"{active_count} active task{'s' if active_count != 1 else ''}")
        
        # Update completed header
        arrow = "▼" if self.completed_expanded else "▶"
        self.completed_header.setText(f"{arrow}  Completed  {completed_count}")
        
    def _connect_signals(self):
        self.new_chat_btn.clicked.connect(self.handlers.clear_chat)
        self.send_btn.clicked.connect(self._on_send)
        self.stop_btn.clicked.connect(self.handlers.stop_generation)
        self.user_input.returnPressed.connect(self._on_send)
        self.tts_toggle.toggled.connect(self.handlers.toggle_tts)
        self.session_list.itemClicked.connect(self._on_session_clicked)
        
    def _on_send(self):
        text = self.user_input.text()
        self.handlers.send_message(text)
        
    def _on_session_clicked(self, item: QListWidgetItem):
        session_id = item.data(Qt.UserRole)
        if session_id:
            self.handlers.load_session(session_id)
    
    def _init_background(self):
        """Initialize models in background."""
        def preload_background():
            self.set_status("Warming up models...")
            preload_models()
            if tts.toggle(True):
                self.set_status("Ready | TTS Active")
            else:
                self.set_status("Ready | TTS Failed")
        
        threading.Thread(target=preload_background, daemon=True).start()
        self.handlers.refresh_sidebar()
    
    # --- Public Methods for Handlers ---
    
    def set_status(self, text: str):
        """Update status label (thread-safe via QTimer)."""
        QTimer.singleShot(0, lambda: self.status_label.setText(text))
    
    def clear_input(self):
        """Clear the input field."""
        self.user_input.clear()
    
    def set_generating_state(self, is_generating: bool):
        """Switch between generating and idle UI state."""
        self.send_btn.setVisible(not is_generating)
        self.stop_btn.setVisible(is_generating)
        self.user_input.setEnabled(not is_generating)
        if not is_generating:
            self.user_input.setFocus()
    
    def add_message_bubble(self, role: str, text: str, is_thinking: bool = False):
        """Add a message bubble to the chat."""
        bubble = MessageBubble(role, text, is_thinking)
        
        # Create wrapper for alignment
        wrapper = QWidget()
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        
        if role == "user":
            wrapper_layout.addStretch()
            wrapper_layout.addWidget(bubble)
        else:
            wrapper_layout.addWidget(bubble)
            wrapper_layout.addStretch()
        
        # Insert before the stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, wrapper)
        
        # Scroll to bottom
        QTimer.singleShot(50, self.scroll_to_bottom)
    
    def add_streaming_widgets(self, thinking_ui: ThinkingExpander, response_bubble: MessageBubble):
        """Add streaming UI widgets (thinking expander + response bubble)."""
        # Create wrapper for assistant alignment
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(8)
        
        # Add thinking UI
        wrapper_layout.addWidget(thinking_ui)
        
        # Add response bubble wrapper
        bubble_wrapper = QWidget()
        bubble_layout = QHBoxLayout(bubble_wrapper)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.addWidget(response_bubble)
        bubble_layout.addStretch()
        wrapper_layout.addWidget(bubble_wrapper)
        
        # Insert before the stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, wrapper)
        
        # Scroll to bottom
        QTimer.singleShot(50, self.scroll_to_bottom)
    
    def clear_chat_display(self):
        """Clear all messages from the chat display."""
        # Remove all widgets except the final stretch
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def refresh_sidebar(self, current_session_id: str = None):
        """Refresh the session list in the sidebar."""
        self.session_list.clear()
        sessions = history_manager.get_sessions()
        
        for sess in sessions:
            title = sess['title']
            sid = sess['id']
            is_pinned = sess.get('pinned', False)
            is_current = sid == current_session_id
            
            # Create custom widget for list item
            item_widget = QWidget()
            item_widget.setFixedHeight(40)  # Match list item height
            item_widget.setStyleSheet("background-color: transparent;")
            # Make widget transparent to mouse events so clicks pass through to list item
            item_widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(8, 0, 8, 0)
            item_layout.setSpacing(8)
            
            # Icon (pin or chat)
            icon = "📌" if is_pinned else "💬"
            icon_label = QLabel(icon)
            icon_label.setFixedWidth(20)
            icon_label.setStyleSheet("color: #9e9e9e;")
            item_layout.addWidget(icon_label)
            
            # Title - truncate if too long
            display_title = title[:35] + "..." if len(title) > 35 else title
            title_label = QLabel(display_title)
            title_label.setStyleSheet(f"color: {'white' if is_current else '#9e9e9e'}; font-size: 13px;")
            title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            item_layout.addWidget(title_label)
            
            # 3-dot menu button - container to handle mouse events
            menu_container = QWidget()
            menu_container.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # Menu receives clicks
            menu_layout = QHBoxLayout(menu_container)
            menu_layout.setContentsMargins(0, 0, 0, 0)
            
            menu_btn = QPushButton("⋮")
            menu_btn.setFixedSize(24, 24)
            menu_btn.setCursor(Qt.PointingHandCursor)
            menu_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #6e6e6e;
                    font-size: 16px;
                    font-weight: bold;
                    border: none;
                    border-radius: 12px;
                }
                QPushButton:hover {
                    background: #3d3d3d;
                    color: #e8eaed;
                }
            """)
            menu_btn.clicked.connect(lambda checked, s=sid, w=item_widget, p=is_pinned: self._show_item_menu(s, w, p))
            menu_layout.addWidget(menu_btn)
            item_layout.addWidget(menu_container)
            
            # Create list item
            item = QListWidgetItem()
            item.setData(Qt.UserRole, sid)
            item.setSizeHint(QSize(280, 48))  # Fixed height for consistent display
            
            if is_current:
                item.setSelected(True)
            
            self.session_list.addItem(item)
            self.session_list.setItemWidget(item, item_widget)

        
        # Show empty state if no sessions
        if not sessions:
            empty_item = QListWidgetItem("No conversations yet")
            empty_item.setFlags(Qt.NoItemFlags)
            self.session_list.addItem(empty_item)
    
    def _show_item_menu(self, session_id: str, widget: QWidget, is_pinned: bool):
        """Show context menu for a session item."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2d31;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                color: #e8eaed;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
            QMenu::separator {
                height: 1px;
                background: #3d3d3d;
                margin: 5px 10px;
            }
        """)
        
        pin_text = "📌  Unpin" if is_pinned else "📌  Pin"
        pin_action = menu.addAction(pin_text)
        pin_action.triggered.connect(lambda: self.handlers.pin_session(session_id))
        
        rename_action = menu.addAction("✏️  Rename")
        rename_action.triggered.connect(lambda: self._rename_session_dialog(session_id))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️  Delete")
        delete_action.triggered.connect(lambda: self.handlers.delete_session(session_id))
        
        # Position menu near the widget
        menu.exec(widget.mapToGlobal(widget.rect().topRight()))
    
    def _rename_session_dialog(self, session_id: str):
        """Show rename dialog for a session."""
        from PySide6.QtWidgets import QInputDialog
        
        new_title, ok = QInputDialog.getText(
            self, "Rename Chat", "Enter new name:"
        )
        
        if ok and new_title.strip():
            self.handlers.rename_session(session_id, new_title.strip())
    
    def _show_session_context_menu(self, position):
        """Show context menu for session list items."""
        item = self.session_list.itemAt(position)
        if not item:
            return
        
        session_id = item.data(Qt.UserRole)
        if not session_id:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2d31;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                color: #e8eaed;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
        """)
        
        pin_action = menu.addAction("📌  Pin")
        pin_action.triggered.connect(lambda: self.handlers.pin_session(session_id))
        
        rename_action = menu.addAction("✏️  Rename")
        rename_action.triggered.connect(lambda: self._rename_session(session_id, item))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️  Delete")
        delete_action.triggered.connect(lambda: self.handlers.delete_session(session_id))
        
        menu.exec(self.session_list.mapToGlobal(position))
    
    def _rename_session(self, session_id: str, item: QListWidgetItem):
        """Show rename dialog for a session."""
        from PySide6.QtWidgets import QInputDialog
        
        current_title = item.text().replace("💬  ", "").replace("📌  ", "")
        new_title, ok = QInputDialog.getText(
            self, "Rename Chat", "Enter new name:",
            text=current_title
        )
        
        if ok and new_title.strip():
            self.handlers.rename_session(session_id, new_title.strip())
    
    def scroll_to_bottom(self):
        """Scroll chat to bottom."""
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def create_app():
    """Create and return the main window."""
    return MainWindow()
