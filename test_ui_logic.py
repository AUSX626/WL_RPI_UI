#!/usr/bin/env python3
"""
UI 逻辑测试（无需硬件）

演示 UI 如何在没有树莓派/摄像头/舵机的情况下测试所有业务逻辑
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from smart_lamp.services import ServiceManager


def main():
    print("=" * 50)
    print("  UI 逻辑测试（无硬件）")
    print("=" * 50)

    # 初始化（不需要硬件）
    services = ServiceManager(data_dir="data")

    # 模拟 UI 操作
    print("\n[UI] 用户点击'学习模式'按钮")
    r = services.execute("enter_study_mode", source="ui")
    print(f"  → {r.message}")

    print("\n[UI] 用户拖动亮度滑块到 70%")
    r = services.execute("set_brightness", {"value": 0.7}, source="ui")
    print(f"  → {r.message}")

    print("\n[UI] 用户点击宠物，摸头")
    r = services.execute("pet_interact", {"action": "pet"}, source="ui")
    print(f"  → {r.message}")
    print(f"  → 宠物心情: {services.pet.current_mood.value}")

    print("\n[UI] 用户开始番茄钟")
    r = services.execute("start_pomodoro", source="ui")
    print(f"  → {r.message}")

    print("\n[UI] 读取今日学习统计")
    stats = services.study.get_today_stats()
    print(f"  → 今日学习: {stats}")

    print("\n[UI] 读取宠物完整状态")
    pet = services.pet.get_status_dict()
    print(f"  → 宠物状态: {pet}")

    print("\n[UI] 设置控制模式为'仅UI'")
    services.set_control_mode("ui_only")
    print(f"  → 当前模式: {services.get_control_mode()}")

    print("\n[UI] 尝试语音控制（应被拒绝）")
    r = services.execute_voice("开灯")
    print(f"  → 结果: {r.error}")

    print("\n" + "=" * 50)
    print("  ✅ 所有逻辑都能测试，不需要硬件！")
    print("=" * 50)


if __name__ == "__main__":
    main()
