import sys
import time
import cv2
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QSizePolicy, QDialog, QComboBox, QCheckBox, QLineEdit
)
from PyQt5.QtGui import QImage, QPixmap, QIcon, QKeySequence
from PyQt5.QtCore import QTimer, Qt
import os
from PyQt5.QtWidgets import QShortcut
from capture_viewer_core import CameraController, get_camera_device_list


class SettingsDialog(QDialog):
    def __init__(self, current_index, show_fps, current_key="F10"):
        super().__init__()
        self.setWindowTitle("Select Camera")

        self.combo = QComboBox()
        self.populate()
        self.combo.setCurrentIndex(current_index)

        self.fps_checkbox = QCheckBox("Toggle FPS")
        self.fps_checkbox.setChecked(show_fps)

        self.key_label = QLabel("Shortcut for Screenshot:")
        self.key_input = QLineEdit()
        self.key_input.setText(current_key)

        btn = QPushButton("Save")
        btn.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(self.combo)
        layout.addWidget(self.fps_checkbox)
        layout.addWidget(self.key_label)
        layout.addWidget(self.key_input)
        layout.addWidget(btn)
        self.setLayout(layout)

    def populate(self):
        self.combo.clear()
        for name, idx in get_camera_device_list():
            self.combo.addItem(f"{name} (Index {idx})", idx)

    def selected_index(self):
        return self.combo.currentIndex()

    def fps_enabled(self):
        return self.fps_checkbox.isChecked()

    
    def shortcut_key(self):
        return self.key_input.text().strip()


def resource_path(relative_path):
    import sys
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class CaptureViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Capture Viewer")

        self.controller = CameraController()
        self.shortcut_keybind = self.controller.shortcut_key

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setScaledContents(True)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setStyleSheet("background-color: black;")

        self.button = QPushButton()
        self.button.setIcon(QIcon(resource_path("assets/settings.png")))
        self.button.setFixedSize(32, 32)
        self.button.setStyleSheet("border: none;")
        self.button.clicked.connect(self.open_settings)

        self.screenshot_button = QPushButton()
        self.screenshot_button.setIcon(QIcon(resource_path("assets/screenshot.png")))
        self.screenshot_button.setFixedSize(32, 32)
        self.screenshot_button.setStyleSheet("border: none;")
        self.screenshot_button.clicked.connect(self.controller.save_screenshot)

        self.fps_label = QLabel("")
        self.fps_label.setStyleSheet("color: white; font-size: 10pt; padding: 5px;")
        self.fps_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.shortcut = QShortcut(QKeySequence(self.shortcut_keybind), self)
        self.shortcut.activated.connect(self.handle_screenshot_shortcut)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.label)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        button_layout.addWidget(self.fps_label)
        button_layout.addStretch()
        button_layout.addWidget(self.screenshot_button)
        button_layout.addWidget(self.button)

        footer = QWidget()
        footer.setLayout(button_layout)
        footer.setStyleSheet("background-color: black;")
        layout.addWidget(footer)

        self.resize(800, 600)
        if self.controller.start_camera(self.controller.cam_index):
            self.timer.start(10)

    def open_settings(self):
        dialog = SettingsDialog(self.controller.cam_index, self.controller.show_fps, self.controller.shortcut_key)
        if dialog.exec_():
            self.controller.cam_index = dialog.selected_index()
            self.controller.show_fps = dialog.fps_enabled()
            self.controller.shortcut_key = dialog.shortcut_key()
            self.shortcut.setKey(QKeySequence(self.controller.shortcut_key))
            self.controller.save_settings()
            if self.controller.start_camera(self.controller.cam_index):
                self.timer.start(10)
                

    def update_frame(self):
        frame, fps = self.controller.get_frame()
        if frame is None:
            return

        h, w, ch = frame.shape
        img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(img))

        if self.controller.show_fps and fps is not None:
            if isinstance(fps, str):
                self.fps_label.setText(f"{fps}")
            else:
                self.fps_label.setText(f"{fps:.1f} FPS")
        else:
            self.fps_label.setText("")


    def handle_screenshot_shortcut(self):
        self.controller.save_screenshot()
        self.controller.trigger_flash(self.label)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_frame()

    

    def closeEvent(self, event):
        self.controller.save_settings()
        self.controller.release()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("icon.ico")))
    viewer = CaptureViewer()
    viewer.show()
    sys.exit(app.exec_())
