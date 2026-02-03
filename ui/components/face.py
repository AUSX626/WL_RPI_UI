from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty, QEasingCurve, pyqtSignal, QParallelAnimationGroup
from PyQt5.QtGui import QPainter, QBrush, QColor, QRadialGradient

# --- 1. 独立的眼睛控件 (负责发光和绘制) ---
class EyeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 180) # 固定大小
        self._height = 176          # 当前高度
        
        # [关键 1] 给独立的眼睛加阴影 = 发光效果
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(80)  # 对应 React box-shadow 50px
        self.glow.setColor(QColor(79, 195, 247, 200)) # 50% 透明度的蓝
        self.glow.setOffset(0, 0)
        self.setGraphicsEffect(self.glow)
        
        # [关键 2] 背景透明，否则阴影是个黑框
        self.setAttribute(Qt.WA_TranslucentBackground)

    @pyqtProperty(int)
    def eyeHeight(self):
        return self._height

    @eyeHeight.setter
    def eyeHeight(self, val):
        self._height = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # [关键 3] 完美的 3D 渐变 (复刻 circle at 50% 30%)
        # 50% = width/2, 30% = height*0.3
        gradient = QRadialGradient(self.width()/2, self.height()*0.3, self.width()*0.8)
        gradient.setColorAt(0.0, QColor("#4FC3F7")) 
        gradient.setColorAt(0.2, QColor("#4FC3F7")) # <--- 新增这行，扩大高光区
        gradient.setColorAt(1.0, QColor("#0277BD")) 

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)

        # 始终居中绘制
        h = max(4, self._height)
        y = (self.height() - h) // 2
        
        # 绘制胶囊体
        painter.drawRoundedRect(0, y, self.width(), h, 30, 30)


# --- 2. 主面板 (负责布局和动画指挥) ---
class FaceWidget(QWidget):
    wake_up_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: black;") # 只有大背景是黑的
        
        # 布局
        self.setup_ui()
        
        # 动画组 (同时控制两只眼)
        self.anim_group = QParallelAnimationGroup(self)
        self.anim_left = QPropertyAnimation(self.left_eye, b"eyeHeight")
        self.anim_right = QPropertyAnimation(self.right_eye, b"eyeHeight")
        
        for anim in [self.anim_left, self.anim_right]:
            anim.setDuration(150)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            self.anim_group.addAnimation(anim)

        self.anim_group.finished.connect(self.check_blink_cycle)

        # 眨眼定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.start_blink)
        self.schedule_next_blink()

    def setup_ui(self):
        # 垂直布局：中间放眼睛，下面放字
        main_layout = QVBoxLayout(self)
        
        # 眼睛区域 (水平布局)
        eyes_layout = QHBoxLayout()
        eyes_layout.addStretch() # 左弹簧
        
        self.left_eye = EyeWidget()
        self.right_eye = EyeWidget()
        
        eyes_layout.addWidget(self.left_eye)
        eyes_layout.addSpacing(80) # [关键] React gap-20 ≈ 80px 间距
        eyes_layout.addWidget(self.right_eye)
        
        eyes_layout.addStretch() # 右弹簧

        main_layout.addStretch()
        main_layout.addLayout(eyes_layout)
        main_layout.addStretch()

        # 提示文字
        self.lbl_hint = QLabel("TOUCH TO WAKE")
        self.lbl_hint.setAlignment(Qt.AlignCenter)
        self.lbl_hint.setStyleSheet("color: rgba(255,255,255,0.6); font-family: 'Inter 18pt', 'Inter', 'Microsoft YaHei'; font-size: 18px; font-weight: medium; letter-spacing: 2px;")

        # 添加透明度特效
        self.opacity_effect = QGraphicsOpacityEffect(self.lbl_hint)
        self.opacity_effect.setOpacity(1.0)
        self.lbl_hint.setGraphicsEffect(self.opacity_effect)

        # 添加动画
        self.hint_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.hint_anim.setDuration(2000)
        self.hint_anim.setLoopCount(-1)
        self.hint_anim.setEasingCurve(QEasingCurve.InOutQuad)

        #设置关键帧
        self.hint_anim.setKeyValueAt(0, 1.0)
        self.hint_anim.setKeyValueAt(0.5, 0.5)
        self.hint_anim.setKeyValueAt(1, 1)

        self.hint_anim.start()

        main_layout.addWidget(self.lbl_hint)
        main_layout.addSpacing(32)

    # --- 动画控制逻辑 ---
    def schedule_next_blink(self):
        import random
        self.timer.start(random.randint(2000, 6000))

    def start_blink(self):
        self.timer.stop()
        # 闭眼
        self.anim_left.setStartValue(176)
        self.anim_left.setEndValue(10)
        self.anim_right.setStartValue(176)
        self.anim_right.setEndValue(10)
        self.anim_group.start()

    def check_blink_cycle(self):
        # 如果刚闭上(高度小)，马上睁开
        if self.left_eye.eyeHeight < 20:
            self.anim_left.setStartValue(10)
            self.anim_left.setEndValue(176)
            self.anim_right.setStartValue(10)
            self.anim_right.setEndValue(176)
            self.anim_group.start()
        else:
            self.schedule_next_blink()

    def mousePressEvent(self, event):
        self.wake_up_signal.emit()