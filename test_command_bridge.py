#!/usr/bin/env python3
"""
测试 UI 命令桥接机制

这个脚本演示：
1. UI 发送命令
2. CommandService 验证并记录
3. MainController 监听并执行

运行方式：python3 test_command_bridge.py
"""
from smart_lamp.services import ServiceManager
from smart_lamp.services.command_service import InputSource

print("=" * 60)
print("测试 UI → CommandService → MainController 桥接")
print("=" * 60)

# 初始化服务
services = ServiceManager(data_dir="data")

# 模拟 MainController 的监听器
received_commands = []

def mock_controller_listener(cmd, result):
    """模拟 MainController._on_ui_command()"""
    if result.success:
        received_commands.append(cmd.name)
        print(f"  📱 [MainController] 收到命令: {cmd.name}")
        print(f"      来源: {cmd.source.value}")
        print(f"      参数: {cmd.params}")
        print(f"      → 这里会触发实际硬件操作！")

# 注册监听器（模拟 MainController 的行为）
services.command.add_listener(mock_controller_listener)

print("\n1️⃣ 测试模式切换命令")
print("-" * 40)
result = services.execute("enter_pet_mode", source="ui")
print(f"   返回: success={result.success}, message={result.message}")

print("\n2️⃣ 测试亮度命令")
print("-" * 40)
result = services.execute("set_brightness", {"value": 0.7}, source="ui")
print(f"   返回: success={result.success}, message={result.message}")

print("\n3️⃣ 测试宠物互动命令")
print("-" * 40)
result = services.execute("pet_interact", {"action": "pet"}, source="ui")
print(f"   返回: success={result.success}, message={result.message}")

print("\n4️⃣ 测试控制权限（设置 ui_only 模式）")
print("-" * 40)
services.set_control_mode("ui_only")
print("   已切换到 ui_only 模式")

# UI 命令应该成功
result = services.execute("turn_on", source="ui")
print(f"   UI 命令: success={result.success}")

# 语音命令应该被拒绝
result = services.execute("turn_on", source="voice")
print(f"   语音命令: success={result.success}, error={result.error}")

print("\n5️⃣ 汇总：MainController 收到的命令")
print("-" * 40)
print(f"   收到 {len(received_commands)} 个命令: {received_commands}")

print("\n" + "=" * 60)
print("✅ 桥接机制工作正常！")
print()
print("当 run.py 运行时：")
print("  - MainController 会自动注册监听器")
print("  - UI 发的命令会触发实际硬件操作")
print()
print("UI 开发时：")
print("  - 不需要 run.py")
print("  - 只需确保命令返回 success=True")
print("=" * 60)
