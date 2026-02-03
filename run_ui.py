 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能台灯 - UI 启动入口

启动方式:
    python run_ui.py              # 正常启动 UI
    python run_ui.py --debug      # 调试模式
    python run_ui.py --no-backend # 仅启动 UI，不启动后端
"""

import sys
import argparse
import threading
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QFontDatabase


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='智能台灯 UI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--no-backend',
        action='store_true',
        help='仅启动 UI，不启动后端控制器'
    )
    
    return parser.parse_args()


def load_fonts(app: QApplication):
    """加载自定义字体"""
    import os
    
    font_dir = PROJECT_ROOT / "ui" / "fonts"
    font_files = [
        "Inter_18pt-Regular.ttf",
        "Inter_18pt-Medium.ttf",
        "Inter_18pt-Bold.ttf",
    ]
    
    font_db = QFontDatabase()
    loaded = []
    
    for font_file in font_files:
        font_path = font_dir / font_file
        if font_path.exists():
            font_id = font_db.addApplicationFont(str(font_path))
            if font_id != -1:
                families = font_db.applicationFontFamilies(font_id)
                loaded.extend(families)
                print(f"[OK] 字体加载成功: {font_file}")
    
    if loaded:
        app.setFont(QFont("Inter 18pt", 14))
        print(f"[OK] 已设置全局字体: Inter 18pt")
    else:
        app.setFont(QFont("Microsoft YaHei", 14))
        print(f"[INFO] 使用备用字体: Microsoft YaHei")


def main():
    """主函数"""
    args = parse_args()
    
    # --- 1. 优先解决 OpenCV 和 PyQt5 的环境冲突 ---
    # 必须在导入任何 cv2 或 PyQt5 相关大模块之前执行
    import os
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1" # 高分屏适配
    
    qt_plugin_path = os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH", "")
    if "cv2" in qt_plugin_path:
        print(f"[WARN] 检测到 OpenCV 覆盖了 Qt 插件路径: {qt_plugin_path}")
        print("[INFO] 正在尝试清除该环境变量以优先使用系统或 PyQt5 插件...")
        os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH")

    # --- 2. 初始化日志 ---
    from smart_lamp.utils.logger import setup_logger
    setup_logger(level="DEBUG" if args.debug else "INFO", debug=args.debug)
    
    print("=" * 50)
    print("智能台灯 UI - 启动中")
    print("=" * 50)

    # --- 3. 启动 Qt 应用 (主线程) ---
    # 必须在启动任何后台线程之前创建 QApplication
    app = QApplication(sys.argv)
    load_fonts(app)

    # --- 4. 启动后端控制器（可选，后台线程） ---
    controller = None
    if not args.no_backend:
        try:
            from smart_lamp.core.main_controller import MainController
            controller = MainController()
            
            # 在后台线程启动控制器
            def run_controller():
                try:
                    # 等待一点时间让 UI 先显示出来，避免启动竞争
                    import time
                    time.sleep(0.5) 
                    controller.start()
                    while controller.running:
                        controller.update()
                except Exception as e:
                    print(f"[ERROR] 控制器异常: {e}")
            
            backend_thread = threading.Thread(target=run_controller, daemon=True)
            backend_thread.start()
            print("[OK] 后端控制器线程已创建")
        except Exception as e:
            print(f"[WARN] 无法启动后端控制器: {e}")
            print("[INFO] 将以仅 UI 模式运行")

    # --- 5. 创建主窗口 ---
    from ui.main import RobotWindow
    window = RobotWindow(controller=controller)
    
    # 如果有控制器，注入到窗口(已在构造函数处理，这里保留兼容性)
    if controller and hasattr(window, 'set_controller'):
        window.set_controller(controller)
    
    # ORM: 确保窗口显示
    window.show()
    
    print("[OK] UI 已启动")
    print("=" * 50)
    
    # --- 6. 运行事件循环 ---
    exit_code = app.exec_()
    
    # 清理
    if controller:
        print("[INFO] 正在停止后端控制器...")
        controller.stop()
    
    print("[OK] 程序已退出")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
