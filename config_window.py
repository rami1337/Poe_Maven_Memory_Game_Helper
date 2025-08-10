from PyQt5.QtWidgets import (QLabel, QVBoxLayout, QPushButton, 
                             QFormLayout, QLineEdit, QDialog, QHBoxLayout, QColorDialog, QFrame)
from PyQt5.QtGui import QKeySequence, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QPoint

class HotkeyLineEdit(QLineEdit):
    """A custom QLineEdit that captures a single hotkey combination."""
    def __init__(self, hotkey_text, parent=None):
        super().__init__(hotkey_text, parent)
        self.setReadOnly(True)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta, Qt.Key_unknown):
            return

        sequence = QKeySequence(event.key() | int(event.modifiers()))
        hotkey_str = sequence.toString(QKeySequence.PortableText).lower()
        hotkey_str = hotkey_str.replace('control', 'ctrl')
        
        parts = hotkey_str.split('+')
        modifiers = {'ctrl', 'shift', 'alt'}
        pressed_modifiers = sorted([p for p in parts if p in modifiers])
        pressed_key = [p for p in parts if p not in modifiers]
        
        if len(pressed_key) != 1: return
        final_hotkey = '+'.join(pressed_modifiers + pressed_key)
        self.setText(final_hotkey)

class ColorPickerButton(QPushButton):
    """A button that displays a color and opens a color dialog on click."""
    color_changed = pyqtSignal()

    def __init__(self, initial_color='white', parent=None):
        super().__init__(parent)
        self._color = QColor(initial_color)
        self.setText(self._color.name())
        self.update_stylesheet()
        self.clicked.connect(self.open_color_dialog)

    def open_color_dialog(self):
        """Creates a color dialog as a new top-level window to prevent style inheritance."""
        dialog = QColorDialog()
        dialog.setCurrentColor(self._color)
        dialog.setOption(QColorDialog.DontUseNativeDialog)
        dialog.setStyleSheet("")
        
        if dialog.exec_():
            new_color = dialog.selectedColor()
            if new_color.isValid():
                self.set_color(new_color)

    def set_color(self, color):
        if isinstance(color, str): self._color = QColor(color)
        else: self._color = color
        self.setText(self._color.name())
        self.update_stylesheet()
        self.color_changed.emit()

    def update_stylesheet(self):
        self.setStyleSheet(f"background-color: {self._color.name()}; color: {self.get_contrasting_text_color()};")

    def get_contrasting_text_color(self):
        return "white" if self._color.lightness() < 128 else "black"

    def color_name(self):
        return self._color.name()

class PositioningWindow(QDialog):
    """A draggable, frameless dialog to set the position."""
    position_set = pyqtSignal(int, int)

    def __init__(self, style_config, icon, parent=None):
        super().__init__(parent)
        self.setWindowIcon(icon)
            
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.drag_position = None
        layout = QVBoxLayout(self)
        
        self.preview_label = QLabel("Drag me to position, then click OK")
        font_color = style_config.get('font_color', '#ffffff')
        bg_color = style_config.get('background_color', 'black')
        self.preview_label.setStyleSheet(f"color: {font_color}; background-color: {bg_color}; padding: 10px; border-radius: 5px;")
        self.preview_label.setFont(QFont("Arial", style_config.get('font_size', 24), QFont.Bold))
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept_position)
        
        layout.addWidget(self.preview_label)
        layout.addWidget(ok_button)
        self.adjustSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def accept_position(self):
        final_geom = self.frameGeometry()
        center_x = final_geom.center().x()
        top_y = final_geom.top()
        self.position_set.emit(center_x, top_y)
        self.close()

class ConfigWindow(QDialog):
    """Configuration window for setting hotkeys and styles."""
    config_saved = pyqtSignal(dict)

    def __init__(self, current_config, icon, parent=None):
        super().__init__(parent)
        from config import DEFAULT_CONFIG 
        self.setWindowTitle("Configure")
        self.app_icon = icon
        self.setWindowIcon(self.app_icon)

        flags = self.windowFlags()
        flags &= ~Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)

        self.current_config = current_config
        self.inputs = {}
        self.new_pos_x = self.current_config['style'].get('x')
        self.new_pos_y = self.current_config['style'].get('y')
        self.pos_win = None

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        hotkeys = self.current_config.get("hotkeys", {})
        seq_actions = self.current_config.get("sequence_actions", {})
        font_colors = self.current_config.get("style", {}).get("font_colors", {})

        for action, hotkey in hotkeys.items():
            self.inputs[f"hotkey_{action}"] = HotkeyLineEdit(hotkey)
            form_layout.addRow(QLabel(f"Hotkey ({action}):"), self.inputs[f"hotkey_{action}"])
            
            if action in seq_actions:
                self.inputs[f"text_{action}"] = QLineEdit(seq_actions.get(action))
                self.inputs[f"color_{action}"] = ColorPickerButton(font_colors.get(action))
                form_layout.addRow(QLabel(f"  Text:"), self.inputs[f"text_{action}"])
                form_layout.addRow(QLabel(f"  Color:"), self.inputs[f"color_{action}"])

        self.inputs['background_color'] = ColorPickerButton(self.current_config['style'].get('background_color'))
        form_layout.addRow(QLabel("Background Color:"), self.inputs['background_color'])
        
        set_position_button = QPushButton("Set Position")
        set_position_button.clicked.connect(self.open_positioning_mode)
        form_layout.addRow(set_position_button)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        form_layout.addRow(separator)

        self.preview_label = QLabel("Preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFont(QFont("Arial", 16, QFont.Bold))
        form_layout.addRow(self.preview_label)
        
        for key, field in self.inputs.items():
            if isinstance(field, ColorPickerButton):
                field.color_changed.connect(self.update_preview)
            elif isinstance(field, QLineEdit):
                field.textChanged.connect(self.update_preview)
        
        self.update_preview()

        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        revert_button = QPushButton("Revert to Defaults")
        cancel_button = QPushButton("Cancel")
        save_button.clicked.connect(self.save_config)
        revert_button.clicked.connect(lambda: self.revert_defaults(DEFAULT_CONFIG))
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(revert_button)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        
        self.setFixedSize(self.sizeHint())

    def open_positioning_mode(self):
        self.hide() 
        temp_style_config = {
            'font_color': '#ffffff',
            'background_color': self.inputs['background_color'].color_name(),
            'font_size': self.current_config['style'].get('font_size')
        }
        self.pos_win = PositioningWindow(temp_style_config, self.app_icon)
        self.pos_win.setWindowModality(Qt.ApplicationModal)
        self.pos_win.position_set.connect(self.on_position_set)
        self.pos_win.finished.connect(self.show)
        self.pos_win.show()

    def on_position_set(self, x, y):
        self.new_pos_x = x
        self.new_pos_y = y

    def update_preview(self):
        html_parts = []
        for i in range(1, 4):
            action = f"Sequence {i}"
            text_widget = self.inputs.get(f"text_{action}")
            color_widget = self.inputs.get(f"color_{action}")
            if text_widget and color_widget:
                text = text_widget.text()
                color = color_widget.color_name()
                html_parts.append(f"<font color='{color}'>{text}</font>")
        
        separator_html = f"<font color='white'> -> </font>"
        preview_text = separator_html.join(html_parts)
        
        bg_color_widget = self.inputs.get('background_color')
        if bg_color_widget:
            bg_color = bg_color_widget.color_name()
            self.preview_label.setText(preview_text)
            self.preview_label.setStyleSheet(f"background-color: {bg_color}; padding: 10px; border-radius: 5px;")

    def save_config(self):
        new_config = { "hotkeys": {}, "sequence_actions": {}, "style": {"font_colors": {}} }
        
        for key, field in self.inputs.items():
            if key.startswith("hotkey_"):
                action = key.replace("hotkey_", "")
                new_config["hotkeys"][action] = field.text()
            elif key.startswith("text_"):
                action = key.replace("text_", "")
                new_config["sequence_actions"][action] = field.text()
            elif key.startswith("color_"):
                action = key.replace("color_", "")
                new_config["style"]["font_colors"][action] = field.color_name()
            elif key == "background_color":
                new_config["style"]["background_color"] = field.color_name()
        
        new_config['style']['x'] = self.new_pos_x
        new_config['style']['y'] = self.new_pos_y
        new_config['style']['font_size'] = self.current_config['style'].get('font_size')
        new_config['style']['separator'] = self.current_config['style'].get('separator')

        self.config_saved.emit(new_config)
        self.accept()

    def revert_defaults(self, defaults):
        """Resets all fields in the config window to their default values."""
        for widget in self.inputs.values():
            widget.blockSignals(True)
        
        try:
            for action, hotkey in defaults.get('hotkeys', {}).items():
                widget = self.inputs.get(f"hotkey_{action}")
                if widget:
                    widget.setText(hotkey)
            
            for action, text in defaults.get('sequence_actions', {}).items():
                text_widget = self.inputs.get(f"text_{action}")
                if text_widget:
                    text_widget.setText(text)
                
                color_widget = self.inputs.get(f"color_{action}")
                default_color = defaults.get('style', {}).get('font_colors', {}).get(action)
                if color_widget and default_color:
                    color_widget.set_color(default_color)
            
            bg_color_widget = self.inputs.get('background_color')
            default_bg_color = defaults.get('style', {}).get('background_color')
            if bg_color_widget and default_bg_color:
                bg_color_widget.set_color(default_bg_color)
            
            self.new_pos_x = defaults.get('style', {}).get('x', 'center')
            self.new_pos_y = defaults.get('style', {}).get('y', 20)
        
        finally:
            for widget in self.inputs.values():
                widget.blockSignals(False)
        
        self.update_preview()
