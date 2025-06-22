import cv2
import json
import os
import time
from pygrabber.dshow_graph import FilterGraph
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QTimer

def get_camera_device_list():
    graph = FilterGraph()
    return [(name, idx) for idx, name in enumerate(graph.get_input_devices())]


class CameraController:
    def __init__(self):
        self.settings_path = "settings.json"
        self.cap = None
        self.cam_index = 0
        self.show_fps = False
        self.last_time = None
        self.load_settings()

    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                data = json.load(f)
                self.cam_index = data.get("cam_index", 0)
                self.show_fps = data.get("show_fps", False)
                self.shortcut_key = data.get("shortcut_key", "F10")
        except FileNotFoundError:
            self.cam_index = 0
            self.show_fps = False
            self.shortcut_key = "F10"


    def save_settings(self):
        data = {
            "cam_index": self.cam_index,
            "show_fps": self.show_fps,
            "shortcut_key": self.shortcut_key
        }
        with open("settings.json", "w") as f:
            json.dump(data, f, indent=2)


    def start_camera(self, index):
        if self.cap:
            self.cap.release()
        self.cam_index = index
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            return True
        return False

    def get_frame(self):
        if not self.cap or not self.cap.isOpened():
            return None, None
        ret, frame = self.cap.read()
        if not ret:
            return None, None
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        fps = None
        if self.show_fps:
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            if not fps or fps < 1:
                fps = "Missing Fps"

        return rgb, fps

    
    def trigger_flash(self, parent_label):
        flash = QLabel(parent_label.parent())
        flash.setStyleSheet("background-color: white;")
        flash.setGeometry(parent_label.geometry())
        flash.show()
        QTimer.singleShot(100, flash.hide)

    def save_screenshot(self):
        frame, _ = self.get_frame()
        if frame is None:
            return
        os.makedirs("screenshots", exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = os.path.join("screenshots", f"screenshot_{timestamp}.png")
        cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        print(f"Screenshot saved as {filename}")


    def release(self):
        if self.cap:
            self.cap.release()
