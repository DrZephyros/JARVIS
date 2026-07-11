from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QFrame, QMenu
from PyQt6.QtGui import QAction, QFont, QColor
from PyQt6.QtCore import Qt, QPoint, QEvent, pyqtSignal
import sys

class StickyNote(QWidget):
    sign_in_requested = pyqtSignal()
    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                # Prevent minimization from "Show Desktop" gestures
                self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        super().changeEvent(event)

    def __init__(self, agenda_items=None, title="Morning Briefing", subtitle="TODAY'S SCHEDULE"):
        super().__init__()
        import os
        import json
        self.state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'todo_state.json')
        
        if agenda_items is not None:
            self.agenda_items = agenda_items
            self.title_text = title
            self.subtitle_text = subtitle
            if self.agenda_items:
                try:
                    self.agenda_items = sorted(self.agenda_items, key=lambda x: x.get('start', ''))
                except Exception:
                    pass
            self._save_state()
        else:
            self._load_state(title, subtitle)
            
        self.initUI()
        self.oldPos = self.pos()
        # self._pin_to_desktop() # Temporarily disabled because Win32 SetParent can cause windows to disappear on Windows 11

    def _save_state(self):
        import json
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    "agenda_items": self.agenda_items,
                    "title": self.title_text,
                    "subtitle": self.subtitle_text
                }, f)
        except Exception as e:
            print("Failed to save state:", e)
            
    def _load_state(self, def_title, def_subtitle):
        import json, os
        self.agenda_items = []
        self.title_text = def_title
        self.subtitle_text = def_subtitle
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.agenda_items = state.get("agenda_items", [])
                    self.title_text = state.get("title", def_title)
                    self.subtitle_text = state.get("subtitle", def_subtitle)
            except Exception as e:
                print("Failed to load state:", e)

    def delete_task(self, idx):
        if self.agenda_items and 0 <= idx < len(self.agenda_items):
            del self.agenda_items[idx]
            self._save_state()
            self._rebuild_list()

    def _pin_to_desktop(self):
        try:
            import win32gui
            import win32con
            
            hwnd = int(self.winId())
            progman = win32gui.FindWindow("Progman", None)
            win32gui.SendMessageTimeout(progman, 0x052C, 0, 0, win32con.SMTO_NORMAL, 1000)
            
            workerw = [None]
            def enum_windows(w, param):
                p = win32gui.FindWindowEx(w, 0, "SHELLDLL_DefView", None)
                if p != 0:
                    workerw[0] = win32gui.FindWindowEx(0, w, "WorkerW", None)
                return True
                
            win32gui.EnumWindows(enum_windows, None)
            
            if workerw[0]:
                win32gui.SetParent(hwnd, workerw[0])
            else:
                win32gui.SetParent(hwnd, progman)
        except Exception as e:
            print("Failed to pin to desktop:", e)

    def initUI(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowStaysOnBottomHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        width = 280
        height = 360
        self.resize(width, height)
        
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.width() - width - 20
        y = screen.top() + 20
        self.setGeometry(x, y, width, height)
        
        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QFrame#container {
                background-color: #212121;
                border-radius: 12px;
                border: 1px solid #424242;
            }
            QLabel#title {
                color: #ececec;
                font-size: 15px;
                font-family: "Inter", "Segoe UI", sans-serif;
                font-weight: 600;
            }
            QLabel#subtitle {
                color: #a0a0a0;
                font-size: 10px;
                font-family: "Inter", "Segoe UI", sans-serif;
                font-weight: bold;
                letter-spacing: 2px;
            }
            QLabel {
                color: #ececec;
                font-family: "Inter", "Segoe UI", sans-serif;
            }
        """)
        
        self.inner_layout = QVBoxLayout(self.container)
        self.inner_layout.setContentsMargins(16, 16, 16, 16)
        self.inner_layout.setSpacing(10)
        
        self.outer_layout.addWidget(self.container)
        self._rebuild_list()
        
    def _rebuild_list(self):
        from PyQt6.QtWidgets import QHBoxLayout, QPushButton
        
        for i in reversed(range(self.inner_layout.count())): 
            item = self.inner_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Note: nested layouts could be handled better, but deleting the widgets is usually enough
                pass

        subtitle = QLabel(self.subtitle_text)
        subtitle.setObjectName("subtitle")
        self.inner_layout.addWidget(subtitle)
        
        title = QLabel(self.title_text)
        title.setObjectName("title")
        self.inner_layout.addWidget(title)
        
        card_style = """
            QFrame {
                background-color: #2f2f2f;
                border-radius: 8px;
                border: 1px solid #424242;
            }
            QFrame:hover {
                background-color: #3d3d3d;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """
        
        if self.agenda_items is None:
            empty_card = QFrame()
            empty_card.setStyleSheet(card_style)
            ec_layout = QVBoxLayout(empty_card)
            lbl = QLabel("Please sign in to view agenda.\n\nSay 'Jarvis, sign in' to link account.")
            lbl.setWordWrap(True)
            ec_layout.addWidget(lbl)
            self.inner_layout.addWidget(empty_card)
        elif not self.agenda_items:
            empty_card = QFrame()
            empty_card.setStyleSheet(card_style)
            ec_layout = QVBoxLayout(empty_card)
            lbl = QLabel("No pending items.")
            lbl.setWordWrap(True)
            ec_layout.addWidget(lbl)
            self.inner_layout.addWidget(empty_card)
        else:
            for idx, item in enumerate(self.agenda_items):
                time_str = item.get('start', '')
                if time_str and 'T' in time_str:
                    time_str = time_str.split('T')[1][:5]
                
                card = QFrame()
                card.setStyleSheet(card_style)
                card_layout = QHBoxLayout(card)
                card_layout.setContentsMargins(10, 8, 10, 8)
                
                text_layout = QVBoxLayout()
                text_layout.setSpacing(2)
                
                if time_str:
                    time_lbl = QLabel(time_str)
                    time_lbl.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 11px;")
                    text_layout.addWidget(time_lbl)
                
                title_lbl = QLabel(item['summary'])
                title_lbl.setStyleSheet("color: #E0F7FA;")
                title_lbl.setWordWrap(True)
                text_layout.addWidget(title_lbl)
                
                card_layout.addLayout(text_layout)
                
                del_btn = QPushButton("✕")
                del_btn.setFixedSize(20, 20)
                del_btn.setStyleSheet("""
                    QPushButton { background: transparent; color: #a0a0a0; border: none; font-weight: bold; font-size: 14px;}
                    QPushButton:hover { color: #ff6b6b; }
                """)
                del_btn.clicked.connect(lambda checked, i=idx: self.delete_task(i))
                card_layout.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
                
                self.inner_layout.addWidget(card)
                
        self.inner_layout.addStretch()
        
    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(6, 16, 24, 255);
                color: #E0F7FA;
                border: 1px solid #00F0FF;
            }
            QMenu::item:selected {
                background-color: rgba(9, 50, 84, 255);
                color: #00F0FF;
            }
        """)
        
        sign_in_action = menu.addAction("Sign In")
        hide_action = menu.addAction("Hide Checklist")
        
        action = menu.exec(event.globalPos())
        if action == hide_action:
            self.hide()
        elif action == sign_in_action:
            self.sign_in_requested.emit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Test data
    test_agenda = [
        {"start": "2026-07-01T09:00:00", "summary": "Sync Meeting"},
        {"start": "2026-07-01T12:00:00", "summary": "Lunch with Client"},
        {"start": "2026-07-01T15:30:00", "summary": "Project Review"}
    ]
    
    note = StickyNote(test_agenda)
    note.show()
    sys.exit(app.exec())
