import win32gui
import win32con
from PyQt5.QtWidgets import QWidget, QLabel, QApplication
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QFont

class Overlay(QWidget):
    """A transparent, always-on-top window to display text."""
    key_action_triggered = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.sequence = []
        self.overlay_enabled = True
        self._is_win32_style_set = False
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.label = QLabel(self)
        self.label.setTextFormat(Qt.RichText)
        
        self.update_config(config)
        
        self.key_action_triggered.connect(self.handle_key_event)
        self.update_display()

    def update_config(self, config):
        """Updates all configuration settings for the overlay."""
        self.config = config
        style_config = self.config.get("style", {})
        bg_color = style_config.get('background_color', 'black')
        font_size = style_config.get('font_size', 24)
        self.pos_x = style_config.get('x', 'center')
        self.pos_y = style_config.get('y', 20)
        self.separator = style_config.get('separator', ' -> ')
        
        self.label.setFont(QFont("Arial", font_size, QFont.Bold))
        self.label.setStyleSheet(f"background-color: {bg_color}; padding: 10px; border-radius: 5px;")
        self.update_display()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._is_win32_style_set:
            hwnd = self.winId()
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_NOACTIVATE)
            self._is_win32_style_set = True

    def update_display(self):
        if self.sequence and self.overlay_enabled:
            html_parts = []
            sequence_actions = self.config.get("sequence_actions", {})
            font_colors = self.config.get("style", {}).get("font_colors", {})

            for action_name in self.sequence:
                text = sequence_actions.get(action_name, "?")
                color = font_colors.get(action_name, "#ffffff")
                html_parts.append(f"<font color='{color}'>{text}</font>")
            
            separator_html = f"<font color='white'>{self.separator}</font>"
            display_text = separator_html.join(html_parts)
            
            self.label.setText(display_text)
            self.label.adjustSize()
            self.resize(self.label.size())
            self.show()
            self.reposition_overlay()
        else:
            self.hide()

    def reposition_overlay(self):
        """Positions the overlay, treating the stored X as a center point."""
        screen_geometry = QApplication.desktop().screenGeometry()
        if self.pos_x == 'center':
            center_x = screen_geometry.width() // 2
        else:
            center_x = self.pos_x
            
        top_left_x = center_x - (self.width() // 2)
        top_left_y = self.pos_y
        self.move(QPoint(top_left_x, top_left_y))

    def handle_key_event(self, action):
        sequence_actions = self.config.get("sequence_actions", {})
        if action == 'Toggle Overlay':
            self.overlay_enabled = not self.overlay_enabled
        elif self.overlay_enabled:
            if action in sequence_actions:
                self.sequence.append(action)
            elif action == 'Clear Sequence':
                self.sequence.clear()
        self.update_display()
