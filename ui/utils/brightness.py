"""
树莓派屏幕亮度控制

通过 /sys/class/backlight/ 控制屏幕背光亮度
"""

import subprocess
from pathlib import Path
from typing import Optional


class ScreenBrightness:
    """
    树莓派屏幕亮度控制
    
    通过 /sys/class/backlight/ 接口控制屏幕背光
    
    使用方法:
        brightness = ScreenBrightness()
        
        # 获取当前亮度 (0-100)
        current = brightness.get_brightness()
        
        # 设置亮度 (0-100)
        brightness.set_brightness(80)
        
        # 调整亮度
        brightness.adjust(10)   # 增加 10%
        brightness.adjust(-10)  # 降低 10%
    """
    
    # 常见的背光控制路径
    BACKLIGHT_PATHS = [
        "/sys/class/backlight/rpi_backlight/brightness",
        "/sys/class/backlight/10-0045/brightness",
        "/sys/class/backlight/backlight/brightness",
    ]
    
    def __init__(self):
        """初始化亮度控制"""
        self._path: Optional[str] = self._find_backlight_path()
        self._max_brightness: int = self._get_max_brightness()
        
        if self._path:
            print(f"[OK] 找到背光控制: {self._path}")
            print(f"[OK] 最大亮度值: {self._max_brightness}")
        else:
            print("[WARN] 未找到背光控制路径，亮度控制不可用")
    
    def _find_backlight_path(self) -> Optional[str]:
        """查找可用的背光控制路径"""
        for path in self.BACKLIGHT_PATHS:
            if Path(path).exists():
                return path
        
        # 尝试自动发现
        backlight_dir = Path("/sys/class/backlight")
        if backlight_dir.exists():
            for device in backlight_dir.iterdir():
                brightness_path = device / "brightness"
                if brightness_path.exists():
                    return str(brightness_path)
        
        return None
    
    def _get_max_brightness(self) -> int:
        """获取最大亮度值"""
        if not self._path:
            return 255  # 默认值
        
        max_path = self._path.replace("brightness", "max_brightness")
        try:
            with open(max_path, 'r') as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError, PermissionError):
            return 255  # 默认值
    
    @property
    def available(self) -> bool:
        """是否可用"""
        return self._path is not None
    
    def get_brightness(self) -> int:
        """
        获取当前亮度
        
        Returns:
            当前亮度值 (0-100)
        """
        if not self._path:
            return 100
        
        try:
            with open(self._path, 'r') as f:
                actual = int(f.read().strip())
                # 转换为 0-100 范围
                return int(actual / self._max_brightness * 100)
        except (FileNotFoundError, ValueError, PermissionError):
            return 100
    
    def set_brightness(self, value: int) -> bool:
        """
        设置亮度
        
        Args:
            value: 亮度值 (0-100)
            
        Returns:
            是否成功
        """
        if not self._path:
            print("[WARN] 背光控制不可用")
            return False
        
        # 限制范围并转换
        value = max(5, min(100, value))  # 最低 5%，避免完全黑屏
        actual = int(value / 100 * self._max_brightness)
        actual = max(1, actual)  # 至少为 1
        
        try:
            # 尝试直接写入
            with open(self._path, 'w') as f:
                f.write(str(actual))
            return True
        except PermissionError:
            # 需要 sudo 权限
            try:
                subprocess.run(
                    ['sudo', 'sh', '-c', f'echo {actual} > {self._path}'],
                    check=True,
                    capture_output=True
                )
                return True
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] 设置亮度失败: {e}")
                return False
    
    def adjust(self, delta: int) -> int:
        """
        调整亮度
        
        Args:
            delta: 变化量 (正数增加，负数减少)
            
        Returns:
            调整后的亮度值
        """
        current = self.get_brightness()
        new_value = current + delta
        new_value = max(5, min(100, new_value))
        self.set_brightness(new_value)
        return new_value
    
    def turn_on(self) -> bool:
        """开启屏幕（设为最大亮度）"""
        return self.set_brightness(100)
    
    def turn_off(self) -> bool:
        """关闭屏幕（设为最低亮度）"""
        return self.set_brightness(5)


# ==================== 独立测试 ====================
def test_screen_brightness():
    """
    独立测试屏幕亮度控制
    
    在树莓派上运行以测试背光控制
    """
    import time
    
    print("=" * 50)
    print("屏幕亮度控制 - 独立测试")
    print("=" * 50)
    print()
    
    # 创建控制器
    brightness = ScreenBrightness()
    
    if not brightness.available:
        print("[WARN] 背光控制不可用")
        print("可能原因:")
        print("  1. 不是树莓派设备")
        print("  2. 未连接官方触摸屏")
        print("  3. 权限不足")
        print()
        print("--- 模拟测试模式 ---")
        _test_mock_brightness()
        return
    
    # 真实测试
    print(f"背光路径: {brightness._path}")
    print(f"最大亮度: {brightness._max_brightness}")
    print()
    
    # 获取当前亮度
    current = brightness.get_brightness()
    print(f"当前亮度: {current}%")
    print()
    
    # 交互式测试
    print("命令:")
    print("  数字 (0-100): 设置亮度")
    print("  +/-: 增加/减少 10%")
    print("  on/off: 开启/关闭")
    print("  q: 退出")
    print()
    
    try:
        while True:
            cmd = input(f"亮度 [{brightness.get_brightness()}%] > ").strip().lower()
            
            if cmd == 'q' or cmd == 'quit':
                break
            elif cmd == 'on':
                brightness.turn_on()
                print("屏幕已开启")
            elif cmd == 'off':
                brightness.turn_off()
                print("屏幕已关闭（最低亮度）")
            elif cmd == '+':
                new_val = brightness.adjust(10)
                print(f"亮度: {new_val}%")
            elif cmd == '-':
                new_val = brightness.adjust(-10)
                print(f"亮度: {new_val}%")
            elif cmd.isdigit():
                val = int(cmd)
                if brightness.set_brightness(val):
                    print(f"亮度已设置为: {brightness.get_brightness()}%")
                else:
                    print("设置失败")
            elif cmd:
                print("未知命令")
                
    except KeyboardInterrupt:
        pass
    
    print("\n测试结束")


def _test_mock_brightness():
    """模拟测试（无真实硬件）"""
    print("模拟亮度变化...\n")
    
    import time
    
    mock_brightness = 50
    
    def show_bar(value: int):
        bar_len = 30
        filled = int(bar_len * value / 100)
        bar = '█' * filled + '░' * (bar_len - filled)
        print(f"\r亮度: [{bar}] {value:3d}%  ", end='', flush=True)
    
    # 渐变演示
    print("演示: 亮度渐变 0% -> 100% -> 0%")
    print()
    
    # 增加
    for i in range(0, 101, 5):
        show_bar(i)
        time.sleep(0.05)
    
    # 减少
    for i in range(100, -1, -5):
        show_bar(i)
        time.sleep(0.05)
    
    print("\n")
    print("[OK] 模拟测试完成")


if __name__ == "__main__":
    test_screen_brightness()
