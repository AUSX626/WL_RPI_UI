import sys
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QStackedWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QSize, QEvent
from PyQt5.QtGui import QIcon, QPixmap, QFontDatabase, QFont, QScreen
from PyQt5 import uic

from ui.components.face import FaceWidget
from ui.active_mode_page import ActiveModePage
from smart_lamp.services.service_manager import ServiceManager
from smart_lamp.services.command_service import CommandServiceIntegration
from smart_lamp.utils.logger import setup_logger

# 路径辅助函数：处理不同系统的路径分隔符
def resource_path(relative_path):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

UI_PATH = resource_path("mainwindow.ui")

def load_fonts():
    """动态加载本地 fonts/ 下的 Inter 字体，避免目标机未安装字体导致样式变形。"""
    font_files = [
        "fonts/Inter_18pt-Regular.ttf",
        "fonts/Inter_18pt-Medium.ttf",
        "fonts/Inter_18pt-Bold.ttf",
    ]
    font_db = QFontDatabase()
    loaded = []
    for f in font_files:
        font_path = resource_path(f)
        if os.path.exists(font_path):
            font_id = font_db.addApplicationFont(font_path)
            if font_id != -1:
                families = font_db.applicationFontFamilies(font_id)
                loaded.extend(families)
                print(f"[OK] 字体加载成功: {font_path}")
                print(f"     -> 字体家族: {families}")
            else:
                print(f"[WARN] 字体加载失败: {font_path}")
        else:
            print(f"[WARN] 未找到字体文件: {font_path}")
    if loaded:
        print(f"[OK] 已加载字体家族: {loaded}")
        print(f"[INFO] 可用的字体名称: {list(set(loaded))}")
    else:
        print("[WARN] 未加载到任何字体，界面可能使用系统默认字体")
    return loaded

class RobotWindow(QMainWindow):
    def __init__(self, controller=None):
        super().__init__()
        
        # --- 1. 调试：检查文件是否存在 ---
        if not os.path.exists(UI_PATH):
            print(f"[ERROR] 严重错误: 找不到文件 {UI_PATH}")
            print("请确认 mainwindow.ui 和 main.py 在同一个文件夹里！")
            return
            
        # --- 2. 加载界面 ---
        try:
            uic.loadUi(UI_PATH, self)
            print("[OK] UI 文件加载成功！")
        except Exception as e:
            print(f"[ERROR] 加载 UI 失败: {e}")
            return

        # --- 3. 初始化服务层和命令服务 ---
        if controller:
            print("[INFO] 使用后端控制器提供的服务层")
            self.services = controller.services
            self.controller = controller
        else:
            print("[INFO] 独立运行模式，创建本地服务层")
            # 使用项目根目录的 data 目录
            services_data_dir = str(PROJECT_ROOT / "data")
            self.services = ServiceManager(data_dir=services_data_dir)
            self.controller = None

        self.command_service = self.services.command
        self.command_integration = CommandServiceIntegration(
            self.command_service,
            controller=self.controller,
            services=self.services,
        )

        # --- 4. 窗口设置 ---
        # 去掉标题栏和所有窗口装饰（包括关闭按钮）
        # 使用 Window 作为基础，然后添加 FramelessWindowHint 来移除所有装饰
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        
        # 自动检测屏幕分辨率并调整窗口大小（铺满屏幕）
        self.adjust_window_to_screen()
        
        # 【调试模式】先注释掉下面这行，确保你能看到窗口！
        # 等你看到黑框了，再把下面这行取消注释，恢复圆角透明效果
        self.setAttribute(Qt.WA_TranslucentBackground) 

        # --- 5. 初始化 ---
        self.apply_styles()
        self.setup_icons() # 加载图标
        self.setup_logic()
        self.setup_face_page() #加载人脸识别页面 

        # ---6.玻璃质感 ---
        # 直接为功能按钮设置样式，确保样式一定被应用
        self.setup_motion_button_styles()
    
    def adjust_window_to_screen(self):
        """
        自动检测屏幕分辨率并调整窗口大小（铺满整个屏幕，排除顶部状态栏）
        """
        app = QApplication.instance()
        if not app:
            # 如果还没有QApplication实例，使用默认值
            print("[WARN] 无法获取屏幕信息，使用默认窗口大小 640x480")
            self.setMaximumSize(640, 480)
            self.resize(640, 480)
            return
        
        # 获取主屏幕（当前窗口所在的屏幕）
        screen = app.primaryScreen()
        if not screen:
            print("[WARN] 无法获取屏幕信息，使用默认窗口大小 640x480")
            self.setMaximumSize(640, 480)
            self.resize(640, 480)
            return
        
        # 获取完整屏幕尺寸和可用区域
        full_geometry = screen.geometry()
        available_geometry = screen.availableGeometry()
        
        # 计算顶部状态栏高度（如果 availableGeometry 没有正确排除，则手动减去16px）
        top_bar_height = full_geometry.y() - available_geometry.y()
        if top_bar_height == 0:
            # 如果系统没有正确排除顶部状态栏，手动设置16px
            top_bar_height = 16
        
        # 计算窗口尺寸：从顶部状态栏下方开始，铺满剩余区域
        screen_width = full_geometry.width()
        screen_height = full_geometry.height() - top_bar_height
        
        print(f"[INFO] 检测到屏幕分辨率: {full_geometry.width()}x{full_geometry.height()}")
        print(f"[INFO] 顶部状态栏高度: {top_bar_height}px")
        print(f"[INFO] 窗口尺寸: {screen_width}x{screen_height}")
        
        # 窗口铺满整个可用区域
        self.setMinimumSize(screen_width, screen_height)
        self.setMaximumSize(screen_width, screen_height)
        self.resize(screen_width, screen_height)
        
        # 移动到顶部状态栏下方（从状态栏高度开始）
        self.move(0, top_bar_height)
        
        print(f"[OK] 窗口已铺满屏幕（排除顶部状态栏）: {screen_width}x{screen_height}, 位置: (0, {top_bar_height})")
    
    def showEvent(self, event):
        """
        窗口显示事件
        确保窗口显示时铺满屏幕（排除顶部状态栏）
        """
        super().showEvent(event)
        # 在窗口显示时再次确保铺满屏幕
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                full_geometry = screen.geometry()
                available_geometry = screen.availableGeometry()
                
                # 计算顶部状态栏高度
                top_bar_height = full_geometry.y() - available_geometry.y()
                if top_bar_height == 0:
                    top_bar_height = 16  # 手动设置16px
                
                screen_width = full_geometry.width()
                screen_height = full_geometry.height() - top_bar_height
                
                self.setGeometry(0, top_bar_height, screen_width, screen_height)
    
    def setup_face_page(self):
        """初始化人脸识别页面（FaceWidget）"""
        # 找到 page_face 页面
        page_face = self.findChild(QWidget, "page_face")
        if not page_face:
            print("[WARN] 警告: 找不到 page_face 页面")
            return
        
        # 创建 FaceWidget 实例
        self.face_widget = FaceWidget(page_face)
        
        # 为 page_face 创建布局并添加 FaceWidget
        layout = QVBoxLayout(page_face)
        layout.setContentsMargins(0, 0, 0, 0)  # 去掉边距，让 FaceWidget 填满整个页面
        layout.setSpacing(0)
        layout.addWidget(self.face_widget)
        
        # 连接唤醒信号：点击 FaceWidget 时切换到主页面
        self.face_widget.wake_up_signal.connect(self.wake_up_from_face)
        
        print("[OK] FaceWidget 已加载到 page_face")
    
    def wake_up_from_face(self):
        """从人脸页面唤醒，切换到主页面"""
        if self.main_stack:
            self.main_stack.setCurrentIndex(1)  # 切换到 page_main（索引1）
            print("[OK] 已唤醒，切换到主页面")
        
        # 同步按钮选中状态：根据当前显示的页面，设置对应按钮为选中
        if hasattr(self, 'page_stack') and hasattr(self, 'page_to_button'):
            current_page = self.page_stack.currentWidget()
            if current_page and current_page in self.page_to_button:
                btn = self.page_to_button[current_page]
                btn.setChecked(True)
                print(f"[OK] 已同步按钮状态: {btn.objectName()}")

    def close_application(self):
        """关闭应用程序"""
        print("[INFO] 收到关闭指令，正在退出应用程序...")
        # 关闭窗口，这会触发 QApplication 退出
        self.close()
        # 或者直接退出应用程序
        QApplication.instance().quit()

    def setup_icons(self):
        """ 为侧边栏按钮和功能按钮加载图标 """
        # 侧边栏按钮图标映射
        sidebar_icon_map = {
            # objectName: (normal_png, checked_png)
            "pushButton_5": ("book-open-text.png", "book-open-text (2).png"),   # Mode 模式
            "pushButton": ("gamepad.png", "gamepad (2).png"),                   # Light Control 灯光控制
            "pushButton_2": ("chart-column-big.png", "chart-column-big (2).png"), # Pet Interaction 宠物互动
            "pushButton_3": ("cpu.png", "cpu (2).png"),                         # Learning 学习
            "pushButton_4": ("power.png", "power (2).png"),                     # 底部：Sleep 休眠
            "pushButton_6": ("sun.png", "sun (2).png"),                         # Reminders 提醒
            "pushButton_7": ("square.png", "square (2).png"),                   # System 系统
        }

        # 功能按钮图标映射（Page_Mode 中的6个按钮）
        motion_icon_map = {
            "pushButton_standby": "square.png",      # standby - 待机模式
            "pushButton_handfollow": "play.png",      # hand-follow - 手势跟随
            "pushButton_petmode": "gamepad.png",   # pet-mode - 宠物模式
            "pushButton_studymode": "bolt.png",      # study-mode - 学习模式
            "pushButton_settings": "rotate-ccw.png", # settings - 设置
            "pushButton_switchmode": "zap.png",        # switch-mode - 模式切换
        }
        
        # 灯光控制按钮图标映射（Page_LightControl 中的5个按钮）
        light_icon_map = {
            "pushButton_turnon": "sun.png",          # turn_on - 开灯
            "pushButton_turnoff": "power.png",       # turn_off - 关灯
            "pushButton_brightup": "bolt.png",       # brightness_up - 亮度增加
            "pushButton_brightdown": "zap.png",      # brightness_down - 亮度降低
            "pushButton_setbrightness": "cpu.png",   # set_brightness - 设置亮度
        }
        
        # 宠物互动按钮图标映射（Page_PetInteraction 中的4个按钮）
        pet_icon_map = {
            "pushButton_petinteract": "gamepad.png",  # pet_interact - 宠物互动
            "pushButton_petfeed": "chart-column-big.png",  # pet_feed - 喂食
            "pushButton_petplay": "play.png",         # pet_play - 玩耍
            "pushButton_pettalk": "book-open-text.png",  # pet_talk - 聊天
        }
        
        # 学习相关按钮图标映射（Page_Learning 中的5个按钮）
        learning_icon_map = {
            "pushButton_startstudy": "play.png",          # start_study - 开始学习
            "pushButton_endstudy": "square.png",          # end_study - 结束学习
            "pushButton_startpomodoro": "bolt.png",       # start_pomodoro - 开始番茄钟
            "pushButton_pausepomodoro": "zap.png",        # pause_pomodoro - 暂停番茄钟
            "pushButton_skipbreak": "rotate-ccw.png",     # skip_break - 跳过休息
        }
        
        # 日程提醒按钮图标映射（Page_Reminders 中的3个按钮）
        reminders_icon_map = {
            "pushButton_addreminder": "sun.png",          # add_reminder - 添加提醒
            "pushButton_listreminders": "book-open-text.png",  # list_reminders - 查看提醒
            "pushButton_deletereminder": "chart-column-big.png",  # delete_reminder - 删除提醒
        }
        
        # 系统按钮图标映射（Page_System 中的4个按钮）
        system_icon_map = {
            "pushButton_shutdown": "power.png",           # shutdown - 关机
            "pushButton_restart": "rotate-ccw.png",       # restart - 重启
            "pushButton_systemsleep": "cpu.png",          # sleep - 休眠
            "pushButton_wakeup": "sun.png",               # wake_up - 唤醒
        }

        def set_btn_icon(btn: QPushButton, filename: str):
            icon_path = resource_path(os.path.join("icons", filename))
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(32, 32))
            else:
                print(f"[WARN] 警告: 找不到图标 {icon_path}")

        # 设置侧边栏按钮（可选中，有常态/选中态图标）
        for btn_name, (normal_icon, checked_icon) in sidebar_icon_map.items():
            btn = self.findChild(QPushButton, btn_name)
            if not btn:
                continue

            # 可选中 + 互斥
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            # 禁用焦点，避免出现焦点边框（黑色细线）
            btn.setFocusPolicy(Qt.NoFocus)

            # 初始设置常态图标
            set_btn_icon(btn, normal_icon)

            # 根据选中状态切换图标
            btn.toggled.connect(lambda checked, b=btn, n=normal_icon, c=checked_icon: set_btn_icon(b, c if checked else n))

        # 设置功能按钮（Page_Mode 中的按钮，不可选中，只有单一图标）
        for btn_name, icon_file in motion_icon_map.items():
            btn = self.findChild(QPushButton, btn_name)
            if btn:
                set_btn_icon(btn, icon_file)
                print(f"[OK] 已为 {btn_name} 设置图标: {icon_file}")
            else:
                print(f"[WARN] 警告: 找不到按钮 {btn_name}")
        
        # 设置灯光控制按钮（Page_LightControl 中的按钮）
        for btn_name, icon_file in light_icon_map.items():
            btn = self.findChild(QPushButton, btn_name)
            if btn:
                set_btn_icon(btn, icon_file)
                print(f"[OK] 已为 {btn_name} 设置图标: {icon_file}")
            else:
                print(f"[WARN] 警告: 找不到按钮 {btn_name}")
        
        # 设置宠物互动按钮（Page_PetInteraction 中的按钮）
        for btn_name, icon_file in pet_icon_map.items():
            btn = self.findChild(QPushButton, btn_name)
            if btn:
                set_btn_icon(btn, icon_file)
                print(f"[OK] 已为 {btn_name} 设置图标: {icon_file}")
            else:
                print(f"[WARN] 警告: 找不到按钮 {btn_name}")
        
        # 设置学习相关按钮（Page_Learning 中的按钮）
        for btn_name, icon_file in learning_icon_map.items():
            btn = self.findChild(QPushButton, btn_name)
            if btn:
                set_btn_icon(btn, icon_file)
                print(f"[OK] 已为 {btn_name} 设置图标: {icon_file}")
            else:
                print(f"[WARN] 警告: 找不到按钮 {btn_name}")
        
        # 设置日程提醒按钮（Page_Reminders 中的按钮）
        for btn_name, icon_file in reminders_icon_map.items():
            btn = self.findChild(QPushButton, btn_name)
            if btn:
                set_btn_icon(btn, icon_file)
                print(f"[OK] 已为 {btn_name} 设置图标: {icon_file}")
            else:
                print(f"[WARN] 警告: 找不到按钮 {btn_name}")
        
        # 设置系统按钮（Page_System 中的按钮）
        for btn_name, icon_file in system_icon_map.items():
            btn = self.findChild(QPushButton, btn_name)
            if btn:
                set_btn_icon(btn, icon_file)
                print(f"[OK] 已为 {btn_name} 设置图标: {icon_file}")
            else:
                print(f"[WARN] 警告: 找不到按钮 {btn_name}")
    
    def setup_motion_button_styles(self):
        """直接为功能按钮设置玻璃质感样式"""
        glass_button_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 16px;
                color: rgba(255, 255, 255, 0.9);
                font-family: "Inter 18pt", "Inter", "Microsoft YaHei";
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
                margin: 0px;
                text-align: center;
                qproperty-iconSize: 32px 32px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(79, 195, 247, 0.5);
                color: rgba(255, 255, 255, 1.0);
            }
            QPushButton:pressed {
                background-color: rgba(79, 195, 247, 0.2);
                border: 1px solid #4FC3F7;
                color: rgba(255, 255, 255, 1.0);
            }
        """
        
        # 找到所有功能按钮并直接设置样式
        motion_button_names = [
            "pushButton_standby",
            "pushButton_handfollow", 
            "pushButton_petmode",
            "pushButton_studymode",
            "pushButton_settings",
            "pushButton_switchmode"
        ]
        
        # 灯光控制按钮列表
        light_button_names = [
            "pushButton_turnon",
            "pushButton_turnoff",
            "pushButton_brightup",
            "pushButton_brightdown",
            "pushButton_setbrightness"
        ]
        
        # 宠物互动按钮列表
        pet_button_names = [
            "pushButton_petinteract",
            "pushButton_petfeed",
            "pushButton_petplay",
            "pushButton_pettalk"
        ]
        
        # 学习相关按钮列表
        learning_button_names = [
            "pushButton_startstudy",
            "pushButton_endstudy",
            "pushButton_startpomodoro",
            "pushButton_pausepomodoro",
            "pushButton_skipbreak"
        ]
        
        # 日程提醒按钮列表
        reminders_button_names = [
            "pushButton_addreminder",
            "pushButton_listreminders",
            "pushButton_deletereminder"
        ]
        
        # 系统按钮列表
        system_button_names = [
            "pushButton_shutdown",
            "pushButton_restart",
            "pushButton_systemsleep",
            "pushButton_wakeup"
        ]
        
        # 应用样式到所有功能按钮
        all_function_buttons = (motion_button_names + light_button_names + 
                               pet_button_names + learning_button_names + 
                               reminders_button_names + system_button_names)
        for btn_name in all_function_buttons:
            btn = self.findChild(QPushButton, btn_name)
            if btn:
                btn.setStyleSheet(glass_button_style)
                print(f"[OK] 已为 {btn_name} 应用玻璃质感样式")
            else:
                print(f"[WARN] 警告: 找不到按钮 {btn_name}，无法应用样式")
        
        # ========== 将六个功能按钮与六个模式指令关联（用于测试） ==========
        # 你可以按需要调整下面的映射关系
        mode_button_map = {
            "pushButton_standby": "enter_standby",       # standby → 进入待机
            "pushButton_handfollow": "enter_hand_follow", # hand-follow → 手势跟随
            "pushButton_petmode": "enter_pet_mode",      # pet-mode → 宠物模式
            "pushButton_studymode": "enter_study_mode",  # study-mode → 学习模式
            "pushButton_settings": "enter_settings",     # settings → 设置
            "pushButton_switchmode": "switch_mode",      # switch-mode → 通用切换（需要 params 指定）
        }
        
        # ========== 将五个灯光控制按钮与亮度控制指令关联 ==========
        light_button_map = {
            "pushButton_turnon": "turn_on",              # Turn On → 开灯
            "pushButton_turnoff": "turn_off",            # Turn Off → 关灯
            "pushButton_brightup": "brightness_up",      # Brightness + → 亮度增加
            "pushButton_brightdown": "brightness_down",  # Brightness - → 亮度降低
            "pushButton_setbrightness": "set_brightness", # Set Brightness → 设置亮度
        }

        # 绑定模式按钮
        for btn_name, cmd_name in mode_button_map.items():
            btn = self.findChild(QPushButton, btn_name)
            if not btn:
                print(f"[WARN] 警告: 找不到模式按钮 {btn_name}，无法绑定指令 {cmd_name}")
                continue

            if not hasattr(self, "command_service") or self.command_service is None:
                print("[WARN] 警告: command_service 未初始化，按钮无法发送指令")
                break

            # 确定该模式是否需要显示 ActiveModePage 以及是否有摄像头
            has_camera = False
            mode_display_name = cmd_name
            should_switch_page = False
            
            # 手势跟随：有摄像头
            if cmd_name == "enter_hand_follow":
                has_camera = True
                should_switch_page = True
                mode_display_name = "Hand Follow Mode"
            # 宠物模式：有摄像头（用于互动）
            elif cmd_name == "enter_pet_mode":
                has_camera = True
                should_switch_page = True
                mode_display_name = "Pet Mode"
            # 学习模式：有摄像头（用于监测）
            elif cmd_name == "enter_study_mode" or (cmd_name == "switch_mode" and btn_name == "pushButton_studymode"):
                # 注意：switch_mode 也要处理
                has_camera = True
                should_switch_page = True
                mode_display_name = "Study Mode"
            elif cmd_name == "switch_mode":
                # 对于通用的 switch_mode，我们假设只有 study 会用到这里
                # 如果未来有其他，需要判断 params
                 pass
            
            # 待机：不切换到 ActivePage，而是直接去 FacePage
            if cmd_name == "enter_standby":
                btn.clicked.connect(self.go_to_sleep_mode)
                continue

            # 绑定点击事件
            # 使用闭包捕获变量
            if should_switch_page:
                if cmd_name == "switch_mode":
                     # 特殊处理 study mode 的 switch_mode
                     btn.clicked.connect(
                        lambda _=False, cs=self.command_service, name="Study Mode", cam=True: 
                        self.activate_mode_page("switch_mode", {"mode": "study"}, name, cam)
                    )
                else:
                    btn.clicked.connect(
                        lambda _=False, cs=self.command_service, c=cmd_name, name=mode_display_name, cam=has_camera: 
                        self.activate_mode_page(c, {}, name, cam)
                    )
            else:
                # 不需要切换页面的模式（如设置），保持原样
                if cmd_name == "switch_mode":
                    # 示例：跳跃按钮作为"切换到学习模式"的测试
                    # 由于上面已经处理了 study，这里可能是漏网之鱼，或者是原来的逻辑
                    # 暂时保留原来的逻辑，或者统一走 command
                    pass
                else:
                    btn.clicked.connect(
                        lambda _=False, cs=self.command_service, name=cmd_name: cs.execute_from_ui(
                            name
                        )
                    )

    def activate_mode_page(self, cmd_name, params, display_name, has_camera):
        """激活模式页面"""
        print(f"[UI] 激活模式页面: {display_name}, 摄像头: {has_camera}")
        
        # 1. 发送指令
        self.command_service.execute_from_ui(cmd_name, params)
        
        # 2. 创建并显示 ActiveModePage
        active_page = ActiveModePage(self, display_name, has_camera=has_camera)
        
        # 将新页面添加到 main_stack (与 page_face, page_main 同级)
        # 假设 main_stack 只有两个页面 (0: face, 1: main)
        # 我们添加第三个，用完后移除
        
        if self.main_stack:
            # 先移除旧的临时页面（如果有）
            while self.main_stack.count() > 2:
                widget = self.main_stack.widget(2)
                self.main_stack.removeWidget(widget)
                widget.deleteLater()
            
            self.main_stack.addWidget(active_page)
            self.main_stack.setCurrentWidget(active_page)

    def setup_light_buttons(self, light_button_map):
        # 绑定灯光控制按钮 (重构函数以使得逻辑清晰，虽然直接写在 __init__ 也可以)
        pass # 这里保留之前的逻辑即可，不需要改动
        
        # 绑定灯光控制按钮
        for btn_name, cmd_name in light_button_map.items():
            btn = self.findChild(QPushButton, btn_name)
            if not btn:
                print(f"[WARN] 警告: 找不到灯光控制按钮 {btn_name}，无法绑定指令 {cmd_name}")
                continue

            if not hasattr(self, "command_service") or self.command_service is None:
                print("[WARN] 警告: command_service 未初始化，按钮无法发送指令")
                break

            # set_brightness 需要参数，这里默认设为 50%
            if cmd_name == "set_brightness":
                btn.clicked.connect(
                    lambda _=False, cs=self.command_service: cs.execute_from_ui(
                        "set_brightness", {"value": 0.5}
                    )
                )
            else:
                btn.clicked.connect(
                    lambda _=False, cs=self.command_service, name=cmd_name: cs.execute_from_ui(
                        name
                    )
                )
        
        # ========== 将四个宠物互动按钮与宠物指令关联 ==========
        pet_button_map = {
            "pushButton_petinteract": "pet_interact",  # Pet Interact → 宠物互动
            "pushButton_petfeed": "pet_feed",          # Feed → 喂食
            "pushButton_petplay": "pet_play",          # Play → 玩耍
            "pushButton_pettalk": "pet_talk",          # Talk → 聊天
        }
        
        # 绑定宠物互动按钮
        for btn_name, cmd_name in pet_button_map.items():
            btn = self.findChild(QPushButton, btn_name)
            if not btn:
                print(f"[WARN] 警告: 找不到宠物互动按钮 {btn_name}，无法绑定指令 {cmd_name}")
                continue

            if not hasattr(self, "command_service") or self.command_service is None:
                print("[WARN] 警告: command_service 未初始化，按钮无法发送指令")
                break

            # pet_interact 需要传 action 参数
            if cmd_name == "pet_interact":
                btn.clicked.connect(
                    lambda _=False, cs=self.command_service: cs.execute_from_ui(
                        "pet_interact", {"action": "pet"}
                    )
                )
            elif cmd_name == "pet_feed":
                btn.clicked.connect(
                    lambda _=False, cs=self.command_service: cs.execute_from_ui(
                        "pet_interact", {"action": "feed"}
                    )
                )
            elif cmd_name == "pet_play":
                btn.clicked.connect(
                    lambda _=False, cs=self.command_service: cs.execute_from_ui(
                        "pet_interact", {"action": "play"}
                    )
                )
            elif cmd_name == "pet_talk":
                btn.clicked.connect(
                    lambda _=False, cs=self.command_service: cs.execute_from_ui(
                        "pet_interact", {"action": "talk"}
                    )
                )
            else:
                btn.clicked.connect(
                    lambda _=False, cs=self.command_service, name=cmd_name: cs.execute_from_ui(
                        name
                    )
                )
        
        # ========== 将五个学习相关按钮与学习指令关联 ==========
        learning_button_map = {
            "pushButton_startstudy": "start_study",          # Start Study → 开始学习
            "pushButton_endstudy": "end_study",              # End Study → 结束学习
            "pushButton_startpomodoro": "start_pomodoro",    # Start Pomodoro → 开始番茄钟
            "pushButton_pausepomodoro": "pause_pomodoro",    # Pause Pomodoro → 暂停番茄钟
            "pushButton_skipbreak": "skip_break",            # Skip Break → 跳过休息
        }
        
        # 绑定学习相关按钮
        for btn_name, cmd_name in learning_button_map.items():
            btn = self.findChild(QPushButton, btn_name)
            if not btn:
                print(f"[WARN] 警告: 找不到学习按钮 {btn_name}，无法绑定指令 {cmd_name}")
                continue

            if not hasattr(self, "command_service") or self.command_service is None:
                print("[WARN] 警告: command_service 未初始化，按钮无法发送指令")
                break

            btn.clicked.connect(
                lambda _=False, cs=self.command_service, name=cmd_name: cs.execute_from_ui(
                    name
                )
            )
        
        # ========== 将三个日程提醒按钮与提醒指令关联 ==========
        reminders_button_map = {
            "pushButton_addreminder": "add_reminder",        # Add Reminder → 添加提醒
            "pushButton_listreminders": "list_reminders",    # List Reminders → 查看提醒
            "pushButton_deletereminder": "delete_reminder",  # Delete Reminder → 删除提醒
        }
        
        # 绑定日程提醒按钮
        for btn_name, cmd_name in reminders_button_map.items():
            btn = self.findChild(QPushButton, btn_name)
            if not btn:
                print(f"[WARN] 警告: 找不到提醒按钮 {btn_name}，无法绑定指令 {cmd_name}")
                continue

            if not hasattr(self, "command_service") or self.command_service is None:
                print("[WARN] 警告: command_service 未初始化，按钮无法发送指令")
                break

            # add_reminder 需要参数，这里示例添加一个测试提醒
            if cmd_name == "add_reminder":
                btn.clicked.connect(
                    lambda _=False, cs=self.command_service: cs.execute_from_ui(
                        "add_reminder", {"content": "测试提醒", "minutes": 5}
                    )
                )
            else:
                btn.clicked.connect(
                    lambda _=False, cs=self.command_service, name=cmd_name: cs.execute_from_ui(
                        name
                    )
                )
        
        # ========== 将四个系统按钮与系统指令关联 ==========
        system_button_map = {
            "pushButton_shutdown": "shutdown",        # Shutdown → 关闭应用程序
            "pushButton_restart": "restart",          # Restart → 重启
            "pushButton_systemsleep": "sleep",        # Sleep → 休眠
            "pushButton_wakeup": "wake_up",           # Wake Up → 唤醒
        }
        
        # 绑定系统按钮
        for btn_name, cmd_name in system_button_map.items():
            btn = self.findChild(QPushButton, btn_name)
            if not btn:
                print(f"[WARN] 警告: 找不到系统按钮 {btn_name}，无法绑定指令 {cmd_name}")
                continue

            # shutdown 按钮特殊处理：直接关闭应用程序
            if btn_name == "pushButton_shutdown":
                btn.clicked.connect(lambda: self.close_application())
                print(f"[OK] shutdown 按钮已绑定：关闭应用程序")
                continue

            if not hasattr(self, "command_service") or self.command_service is None:
                print("[WARN] 警告: command_service 未初始化，按钮无法发送指令")
                break

            btn.clicked.connect(
                lambda _=False, cs=self.command_service, name=cmd_name: cs.execute_from_ui(
                    name
                )
            )

    def setup_logic(self):
        """ 按钮点击逻辑 """
        self.main_stack = self.findChild(object, "rootStack") # 注意：请确认你在Designer里改名了吗？没改名可能是 stackedWidget
        if not self.main_stack:
            # 尝试找默认名字
            self.main_stack = self.findChild(object, "stackedWidget")

        # 默认显示主页
        if self.main_stack:
            self.main_stack.setCurrentIndex(0) # 跳过 Face，显示 App

        # ---- 子页面：motion / console / status / settings / reminders / system 切换 ----
        # 中间的内容区 stackedWidget_2
        self.page_stack = self.findChild(QStackedWidget, "stackedWidget_2")

        # 侧边栏按钮（按 .ui 中的实际标签）
        btn_motion   = self.findChild(QPushButton, "pushButton_5")  # Mode → Page_Mode
        btn_console  = self.findChild(QPushButton, "pushButton")    # Light Control → Page_LightControl
        btn_status   = self.findChild(QPushButton, "pushButton_2")  # Pet Interaction → Page_PetInteraction
        btn_settings = self.findChild(QPushButton, "pushButton_3")  # Learning → Page_Learning
        # 可选：提醒 & 系统（按 .ui 名称匹配）
        btn_reminders = self.findChild(QPushButton, "pushButton_6")  # Reminders → Page_Reminders
        btn_system    = self.findChild(QPushButton, "pushButton_7")  # System → Page_System
        
        # 统一侧边栏按钮尺寸，避免新增按钮后整体被拉伸
        sidebar_buttons = [
            btn_motion, btn_console, btn_status, btn_settings, btn_reminders, btn_system
        ]
        for btn in sidebar_buttons:
            if btn:
                btn.setFixedHeight(54)

        if self.page_stack:
            # 找到所有页面对象（按 .ui 中的实际名称）
            page_motion     = self.findChild(QWidget, "Page_Mode")
            page_console    = self.findChild(QWidget, "Page_LightControl")
            page_status     = self.findChild(QWidget, "Page_PetInteraction")
            page_settings   = self.findChild(QWidget, "Page_Learning")
            page_reminders  = self.findChild(QWidget, "Page_Reminders")
            page_system     = self.findChild(QWidget, "Page_System")

            # 保存页面到按钮的映射关系，用于唤醒时同步按钮状态
            self.page_to_button = {}
            if page_motion and btn_motion:
                self.page_to_button[page_motion] = btn_motion
            if page_console and btn_console:
                self.page_to_button[page_console] = btn_console
            if page_status and btn_status:
                self.page_to_button[page_status] = btn_status
            if page_settings and btn_settings:
                self.page_to_button[page_settings] = btn_settings
            if page_reminders and btn_reminders:
                self.page_to_button[page_reminders] = btn_reminders
            if page_system and btn_system:
                self.page_to_button[page_system] = btn_system

            # 绑定按钮点击事件到对应页面
            if btn_motion and page_motion:
                btn_motion.clicked.connect(lambda: self.page_stack.setCurrentWidget(page_motion))
            if btn_console and page_console:
                btn_console.clicked.connect(lambda: self.page_stack.setCurrentWidget(page_console))
            if btn_status and page_status:
                btn_status.clicked.connect(lambda: self.page_stack.setCurrentWidget(page_status))
            if btn_settings and page_settings:
                btn_settings.clicked.connect(lambda: self.page_stack.setCurrentWidget(page_settings))
            if btn_reminders and page_reminders:
                btn_reminders.clicked.connect(lambda: self.page_stack.setCurrentWidget(page_reminders))
            if btn_system and page_system:
                btn_system.clicked.connect(lambda: self.page_stack.setCurrentWidget(page_system))

            # 初始页面：button5 + page_motion
            self.page_stack.setCurrentWidget(page_motion)
            if btn_motion:
                btn_motion.setChecked(True)

        # 退出按钮逻辑 (方便你关闭无边框窗口)
        # 既然没有 X，我们暂时用 Sleep 按钮关闭程序，或者按 Alt+F4
        # 修改：Sleep 按钮现在返回眼睛动画（待机）
        btn_sleep = self.findChild(object, "pushButton_4")
        if btn_sleep:
            btn_sleep.clicked.disconnect() if btn_sleep.receivers(btn_sleep.clicked) > 0 else None
            # 点击 Sleep -> 发送 standby 命令 -> 切换到 main_stack[0] (FacePage)
            btn_sleep.clicked.connect(self.go_to_sleep_mode)

    def go_to_sleep_mode(self):
        """进入休眠(待机)模式，显示眼睛动画"""
        print("[UI] 点击休眠按钮，返回眼睛动画")
        # 发送待机命令
        if self.command_service:
            self.command_service.execute_from_ui("enter_standby")
        # 切换页面
        if self.main_stack:
            self.main_stack.setCurrentIndex(0)

    def apply_styles(self):
        # 颜色定义
        COLOR_BG_DARK = "#1A1D24"
        COLOR_TEXT_GRAY = "#B0B0B0"
        COLOR_TEXT_WHITE = "#FFFFFF"
        COLOR_ACCENT = "#4FC3F7"

        # 修复可见性：针对 centralwidget 设置背景，而不是 QMainWindow
        styles = f"""
        /* 修复幽灵窗口的关键：给中心部件上色 */
        QWidget#centralwidget {{
            background-color: black;
            border-radius: 0px;
        }}
        
        /* 侧边栏 */
        QFrame#sidebarFrame {{
            background-color: {COLOR_BG_DARK};
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            border-top-left-radius: 16px;
            border-bottom-left-radius: 16px;
        }}
        
        /* 侧边栏按钮样式（只应用于侧边栏内的按钮） */
        QFrame#sidebarFrame QPushButton {{
            background-color: transparent;            /*透明背景*/
            color: {COLOR_TEXT_GRAY};                 /*灰色字体*/
            border: none;                             /*无边框*/
            text-align: left;                         /*文字左对齐*/
            padding-left: 2px;                       /*图标和文字左侧留白*/
            font-family: "Inter 18pt", "Inter", "Microsoft YaHei"; /* 兼容字体 */
            font-size: 18px;                          /*字体大小*/
            height: 64px;                             /*加大高度，方便触摸*/
            border-radius: 0px;                       /*直角，无圆角*/
            margin: 4px 10px;                         /*按钮间距*/
        }}

        /* 侧边栏按钮鼠标悬停效果 */
        QFrame#sidebarFrame QPushButton:hover {{
            color: {COLOR_TEXT_WHITE};
            font-weight: bold;
            border: none;                             /*移除边框*/
            border-radius: 12px;
        }}

        /* 侧边栏按钮选中（checked）样式 */
        QFrame#sidebarFrame QPushButton:checked {{
            color: #1A1D24;
            background-color: #4FC3F7;
            border: none;                             /*移除边框，避免出现黑色细线*/
            outline: none;                            /*移除焦点轮廓*/
            font-family: "Inter 18pt", "Inter", "Microsoft YaHei";
            font-size: 18px;
            font-weight: bold;
            border-radius: 12px;
        }}
        
        /* 侧边栏按钮焦点状态 - 移除焦点边框 */
        QFrame#sidebarFrame QPushButton:focus {{
            border: none;
            outline: none;
        }}
        
        /* 侧边栏按钮选中且获得焦点时的样式 */
        QFrame#sidebarFrame QPushButton:checked:focus {{
            border: none;
            outline: none;
        }}
        """
        self.setStyleSheet(styles)


if __name__ == "__main__":
    # 高分屏适配
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    # 初始化日志，使 SERVICE 中的日志输出到当前终端
    setup_logger(level="INFO", debug=True)

    app = QApplication(sys.argv)
    # 动态加载字体，避免目标机缺字
    loaded_fonts = load_fonts()
    
    # 设置全局字体（14pt 高分屏适配，可按需调节）
    # 确保使用正确的字体家族名
    if loaded_fonts:
        # Inter 18pt 的字体家族名实际上就是 "Inter 18pt"
        app.setFont(QFont("Inter 18pt", 14))
        print(f"[OK] 全局字体已设置为: Inter 18pt")
    else:
        app.setFont(QFont("Inter", 14))
        print(f"[INFO] 使用备用字体: Inter")
    
    window = RobotWindow()
    window.show()
    sys.exit(app.exec_())