import sys
import os
import keyboard
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon

from config import load_config, save_config
from overlay import Overlay
from config_window import ConfigWindow

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class Application:
    """Main application class to manage everything."""
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.config = load_config()
        self.pressed_hotkeys = set()
        self.action_map = {}
        self.config_win = None

        try:
            icon_path = resource_path("icon.png")
            self.app_icon = QIcon(icon_path)
        except:
            style = self.app.style()
            self.app_icon = style.standardIcon(style.SP_ComputerIcon)

        self.overlay = Overlay(self.config)
        self.setup_tray_icon()
        self.register_hotkeys()

    def register_hotkeys(self):
        keyboard.unhook_all()
        self.action_map = {hotkey: action for action, hotkey in self.config.get("hotkeys", {}).items()}
        keyboard.hook(self.keyboard_event_handler)

    def keyboard_event_handler(self, event: keyboard.KeyboardEvent):
        if event.event_type == keyboard.KEY_DOWN:
            for hotkey_str, action in self.action_map.items():
                try:
                    if keyboard.is_pressed(hotkey_str) and hotkey_str not in self.pressed_hotkeys:
                        self.pressed_hotkeys.add(hotkey_str)
                        self.overlay.key_action_triggered.emit(action)
                except Exception:
                    pass
        
        elif event.event_type == keyboard.KEY_UP:
            pressed_hotkeys_copy = self.pressed_hotkeys.copy()
            for hotkey_str in pressed_hotkeys_copy:
                if not keyboard.is_pressed(hotkey_str):
                    self.pressed_hotkeys.remove(hotkey_str)

    def setup_tray_icon(self):
        self.tray = QSystemTrayIcon(self.app_icon, self.app)
        self.tray.setToolTip("PoE Maven Memory Game Helper")
        self.tray.setVisible(True)

        self.tray.activated.connect(self.on_tray_icon_activated)

        menu = QMenu()
        toggle_action = QAction("Disable Overlay", self.app)
        toggle_action.triggered.connect(lambda: self.toggle_overlay(toggle_action))
        menu.addAction(toggle_action)

        config_action = QAction("Configure", self.app)
        config_action.triggered.connect(self.show_config_window)
        menu.addAction(config_action)
        
        menu.addSeparator()
        quit_action = QAction("Quit", self.app)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)

    def on_tray_icon_activated(self, reason):
        """
        Handles activation events on the system tray icon.
        """
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_config_window()

    def toggle_overlay(self, action):
        self.overlay.overlay_enabled = not self.overlay.overlay_enabled
        action.setText("Enable Overlay" if not self.overlay.overlay_enabled else "Disable Overlay")
        self.overlay.update_display()

    def show_config_window(self):
        """
        Shows the configuration window. If it's already open, it brings it to the front.
        """
        if self.config_win is None or not self.config_win.isVisible():
            keyboard.unhook_all()
            self.config_win = ConfigWindow(self.config, self.app_icon)
            self.config_win.config_saved.connect(self.on_config_saved)
            self.config_win.finished.connect(self.register_hotkeys)
            self.config_win.show()
        else:
            self.config_win.activateWindow()
            self.config_win.raise_()

    def on_config_saved(self, new_config):
        self.config = new_config
        save_config(self.config)
        self.overlay.update_config(self.config)

    def run(self):
        sys.exit(self.app.exec_())

    def quit(self):
        keyboard.unhook_all()
        self.app.quit()
