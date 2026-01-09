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

from gui.handlers import ChatHandlers
from core.model_manager import unload_all_models

from gui.styles import AURA_STYLESHEET 

from gui.tabs.dashboard import DashboardView
from gui.tabs.chat import ChatTab
from gui.tabs.planner import PlannerTab
from gui.tabs.briefing import BriefingView
from gui.tabs.home_automation import HomeAutomationTab
from gui.tabs.agent import AgentTab
from gui.components.system_monitor import SystemMonitor


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
        
        # Add system monitor to title bar
        self._init_system_monitor()
        
        self._init_window()
        self._connect_signals()
        self._init_background()
        
    def _init_window(self):
        # Create sub-interfaces
        self.dashboard_view = DashboardView()
        self.dashboard_view.setObjectName("dashboardInterface")

        self.chat_tab = ChatTab()
        self.chat_tab.setObjectName("chatInterface")
        
        self.planner_tab = PlannerTab()
        self.planner_tab.setObjectName("plannerInterface")
        
        self.briefing_view = BriefingView()
        self.briefing_view.setObjectName("briefingInterface")
        
        self.home_tab = HomeAutomationTab()
        self.home_tab.setObjectName("homeInterface")
        
        self.agent_tab = AgentTab()
        self.agent_tab.setObjectName("agentInterface")
        
        # Add interfaces to navigation
        self.addSubInterface(self.dashboard_view, FIF.HOME, "Dashboard")
        self.addSubInterface(self.chat_tab, FIF.CHAT, "Chat")
        self.addSubInterface(self.planner_tab, FIF.CALENDAR, "Planner")
        self.addSubInterface(self.briefing_view, FIF.DATE_TIME, "Briefing")
        self.addSubInterface(self.home_tab, FIF.LAYOUT, "Home Auto")
        self.addSubInterface(self.agent_tab, FIF.ROBOT, "Agent")
        
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
        
        # Tab change - unload models when switching
        self.stackedWidget.currentChanged.connect(self._on_tab_changed)

    def _on_send(self, text):
        """Forward send request to handlers."""
        self.handlers.send_message(text)
        
    def _on_session_clicked(self, session_id):
        """Load session."""
        self.handlers.load_session(session_id)
    
    def _init_background(self):
        """Initialize app without preloading models."""
        # Models are loaded on-demand when user interacts
        self.set_status("Ready")
        self.chat_tab.refresh_sidebar()
    
    def _init_system_monitor(self):
        """Add system monitor widget to the title bar."""
        self.system_monitor = SystemMonitor()
        # Add to the title bar (right side)
        self.titleBar.hBoxLayout.insertWidget(4, self.system_monitor, 1)
    
    def _on_tab_changed(self, index):
        """Called when user switches tabs. Unload models to free VRAM."""
        # Unload all models when switching away from AI tabs
        unload_all_models()
        self.set_status("Ready")
    
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
