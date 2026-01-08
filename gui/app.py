"""
Main PySide6 application setup and layout using Fluent Widgets.
"""

import threading
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon as FIF,
    SplashScreen
)

from core.llm import preload_models
from core.tts import tts
from gui.handlers import ChatHandlers

from gui.styles import AURA_STYLESHEET 

from gui.tabs.chat import ChatTab
from gui.tabs.planner import PlannerTab
from gui.tabs.briefing import BriefingView
from gui.tabs.home_automation import HomeAutomationTab


class MainWindow(FluentWindow):
    """Main application window using Fluent Design."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A.D.A")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)
        
        
        # Center on screen
        # Disable Mica to allow our Deep Navy background to show through
        # self.windowEffect.setMicaEffect(self.winId())
        self.setStyleSheet(AURA_STYLESHEET)
        
        # Initialize handlers
        self.handlers = ChatHandlers(self)
        
        self._init_window()
        self._connect_signals()
        self._init_background()
        
    def _init_window(self):
        # Create sub-interfaces
        self.chat_tab = ChatTab()
        self.chat_tab.setObjectName("chatInterface")
        
        self.planner_tab = PlannerTab()
        self.planner_tab.setObjectName("plannerInterface")
        
        self.briefing_view = BriefingView()
        self.briefing_view.setObjectName("briefingInterface")
        
        self.home_tab = HomeAutomationTab()
        self.home_tab.setObjectName("homeInterface")
        
        # Add interfaces to navigation
        self.addSubInterface(self.chat_tab, FIF.CHAT, "Chat")
        self.addSubInterface(self.planner_tab, FIF.CALENDAR, "Planner")
        self.addSubInterface(self.briefing_view, FIF.DATE_TIME, "Briefing")
        self.addSubInterface(self.home_tab, FIF.HOME, "Home Auto")
        
    def _connect_signals(self):
        """Connect signals between UI components and logic."""
        # Chat Logic Connections
        self.chat_tab.new_chat_requested.connect(self.handlers.clear_chat)
        self.chat_tab.send_message_requested.connect(self._on_send)
        self.chat_tab.stop_generation_requested.connect(self.handlers.stop_generation)
        self.chat_tab.tts_toggled.connect(self.handlers.toggle_tts)
        self.chat_tab.session_selected.connect(self._on_session_clicked)
        
        # Session Management
        self.chat_tab.session_pin_requested.connect(self.handlers.pin_session)
        self.chat_tab.session_rename_requested.connect(self.handlers.rename_session)
        self.chat_tab.session_delete_requested.connect(self.handlers.delete_session)

    def _on_send(self, text):
        """Forward send request to handlers."""
        self.handlers.send_message(text)
        
    def _on_session_clicked(self, session_id):
        """Load session."""
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
        self.chat_tab.refresh_sidebar()
    
    # --- Public Methods for Handlers (Facade Pattern) ---
    
    def set_status(self, text: str):
        self.chat_tab.set_status(text)
    
    def clear_input(self):
        self.chat_tab.clear_input()
    
    def set_generating_state(self, is_generating: bool):
        self.chat_tab.set_generating_state(is_generating)
    
    def add_message_bubble(self, role: str, text: str, is_thinking: bool = False):
        self.chat_tab.add_message_bubble(role, text, is_thinking)
    
    def add_streaming_widgets(self, thinking_ui, response_bubble):
        self.chat_tab.add_streaming_widgets(thinking_ui, response_bubble)
    
    def clear_chat_display(self):
        self.chat_tab.clear_chat_display()
    
    def refresh_sidebar(self, current_session_id: str = None):
        self.chat_tab.refresh_sidebar(current_session_id)
    
    def scroll_to_bottom(self):
        self.chat_tab.scroll_to_bottom()


def create_app():
    """Create and return the main window."""
    return MainWindow()
