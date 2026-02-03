#!/usr/bin/env python3
"""命令服务测试"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from smart_lamp.services import ServiceManager

def main():
    print("=" * 50)
    print("    命令服务测试")
    print("=" * 50)
    
    # 初始化
    services = ServiceManager(data_dir='data')
    
    print('\n===== 可用的语音指令 =====')
    voice_cmds = services.command.get_voice_commands()
    for keyword, desc in list(voice_cmds.items())[:15]:
        print(f'  说 "{keyword}" → {desc}')
    
    print('\n===== 测试语音指令解析 =====')
    test_phrases = [
        '开灯',
        '关灯', 
        '亮度调到80',
        '亮一点',
        '摸摸头',
        '学习模式',
        '番茄钟',
        '10分钟后提醒我喝水',
        '待机',
    ]
    
    for phrase in test_phrases:
        result = services.execute_voice(phrase)
        status = '✓' if result.success else '✗'
        msg = result.message if result.success else result.error
        print(f'  [{status}] "{phrase}" → {msg}')
    
    print('\n===== 测试 UI 指令 =====')
    # 模拟 UI 点击
    result = services.execute("enter_study_mode", source="ui")
    print(f'  UI 点击 "学习模式": {result.message}')
    
    result = services.execute("set_brightness", {"value": 0.6}, source="ui")
    print(f'  UI 设置亮度 60%: {result.message}')
    
    result = services.execute("pet_interact", {"action": "play"}, source="ui")
    print(f'  UI 点击 "玩耍": {result.message}')
    
    print('\n===== 测试完成 =====')

if __name__ == "__main__":
    main()
