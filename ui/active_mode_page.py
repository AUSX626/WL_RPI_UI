
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QCursor
import cv2

class ActiveModePage(QWidget):
    """
    Shows when a mode is active.
    Optionally shows camera feed.
    """
    def __init__(self, main_window, mode_name, has_camera=False):
        super().__init__()
        self.main_window = main_window
        self.mode_name = mode_name
        self.has_camera = has_camera
        self.is_camera_showing = False
        
        self.setup_ui()
        
        # Timer for camera update
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def setup_ui(self):
        # Dark background
        self.setStyleSheet("background-color: #1A1D24;")
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.setSpacing(30)

        # Title
        self.label_title = QLabel(f"正在运行: {self.mode_name}")
        self.label_title.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        self.label_title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.label_title)

        # Content Area (Stack for switching between options and camera)
        self.content_stack = QStackedLayout()
        
        # --- Page 1: Options Menu ---
        self.page_options = QWidget()
        options_layout = QVBoxLayout(self.page_options)
        options_layout.setAlignment(Qt.AlignCenter)
        options_layout.setSpacing(20)
        
        # Option 1: Exit to Eye Animation
        self.btn_exit = self.create_button("退出到眼睛动画", "#FF5252", "#FF1744")
        self.btn_exit.clicked.connect(self.on_exit_clicked)
        options_layout.addWidget(self.btn_exit)
        
        # Option 2: Show Camera (Only if has_camera)
        if self.has_camera:
            self.btn_show_camera = self.create_button("显示实时监控", "#448AFF", "#2979FF")
            self.btn_show_camera.clicked.connect(self.on_show_camera_clicked)
            options_layout.addWidget(self.btn_show_camera)
        
        self.content_stack.addWidget(self.page_options)
        
        # --- Page 2: Camera View ---
        self.page_camera = QWidget()
        camera_layout = QVBoxLayout(self.page_camera)
        camera_layout.setAlignment(Qt.AlignCenter)
        camera_layout.setSpacing(10)
        
        # Camera Frame
        self.label_camera = QLabel("正在连接摄像头...")
        self.label_camera.setAlignment(Qt.AlignCenter)
        self.label_camera.setMinimumSize(480, 320) # 4:3 Aspect Ratio
        self.label_camera.setStyleSheet("background-color: black; border: 2px solid #333; color: white; border-radius: 8px;")
        camera_layout.addWidget(self.label_camera)
        
        # Back Button
        self.btn_back = self.create_button("返回选项菜单", "#757575", "#616161")
        self.btn_back.setFixedSize(200, 50) # Smaller than main buttons
        self.btn_back.clicked.connect(self.on_back_clicked)
        camera_layout.addWidget(self.btn_back)
        
        self.content_stack.addWidget(self.page_camera)
        
        # Add stack to main layout
        self.main_layout.addLayout(self.content_stack)
        
        # Description Label
        self.label_footer = QLabel("点击退出将停止当前功能并返回待机状态")
        self.label_footer.setStyleSheet("color: #666666; font-size: 14px;")
        self.label_footer.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.label_footer)

    def create_button(self, text, color, hover_color):
        btn = QPushButton(text)
        btn.setFixedSize(300, 80)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 16px;
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
        return btn

    def on_exit_clicked(self):
        self.timer.stop()
        # Send command to enter standby
        self.main_window.command_service.execute_from_ui("enter_standby")
        # Navigate to Eye Animation (Face Page)
        if self.main_window.main_stack:
            self.main_window.main_stack.setCurrentIndex(0)

    def on_show_camera_clicked(self):
        self.content_stack.setCurrentWidget(self.page_camera)
        self.is_camera_showing = True
        self.timer.start(33) # ~30 FPS

    def on_back_clicked(self):
        self.timer.stop()
        self.is_camera_showing = False
        self.content_stack.setCurrentWidget(self.page_options)
        self.label_camera.clear()
        self.label_camera.setText("正在连接摄像头...")

    def update_frame(self):
        if not self.is_camera_showing:
            return
            
        # Get frame from controller
        if self.main_window.controller:
            frame = self.main_window.controller._get_frame()
            if frame is not None:
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                
                # Scale to label size (Keep Aspect Ratio)
                # Ensure we don't scale up too much if label is small
                target_size = self.label_camera.size()
                scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                    target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.label_camera.setPixmap(scaled_pixmap)
            else:
                self.label_camera.setText("等待摄像头画面...")
        else:
             self.label_camera.setText("控制器未连接")
