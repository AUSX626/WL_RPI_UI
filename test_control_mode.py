#!/usr/bin/env python3
"""控制权管理测试"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from smart_lamp.services import ServiceManager

def main():
    services = ServiceManager(data_dir='data')

    print('\n' + '=' * 50)
    print('    控制权管理测试')
    print('=' * 50)

    # 查看所有控制模式选项
    print('\n可用的控制模式:')
    for mode, desc in services.get_control_mode_options().items():
        print(f'  {mode}: {desc}')

    # 默认是全部开放
    print(f'\n当前控制模式: {services.get_control_mode()}')

    # 测试：全部开放时
    print('\n--- 测试：全部开放 ---')
    r1 = services.execute('turn_on', source='ui')
    print(f'  UI 开灯: {r1.message}')
    r2 = services.execute_voice('开灯')
    print(f'  语音 开灯: {r2.message}')
    r3 = services.execute('turn_on', source='remote')
    print(f'  遥控器 开灯: {r3.message}')

    # 切换到 仅 UI 控制
    print('\n--- 切换到: 仅 UI 控制 ---')
    services.set_control_mode('ui_only')
    print(f'  当前模式: {services.get_control_mode()}')

    r1 = services.execute('turn_on', source='ui')
    print(f'  UI 开灯: [OK] {r1.message}')
    r2 = services.execute_voice('开灯')
    print(f'  语音 开灯: [BLOCKED] {r2.error}')
    r3 = services.execute('turn_on', source='remote')
    print(f'  遥控器 开灯: [BLOCKED] {r3.error}')

    # 切换到 UI + 语音
    print('\n--- 切换到: UI + 语音 ---')
    services.set_control_mode('ui_voice')
    print(f'  当前模式: {services.get_control_mode()}')

    r1 = services.execute('turn_on', source='ui')
    print(f'  UI 开灯: [OK] {r1.message}')
    r2 = services.execute_voice('开灯')
    print(f'  语音 开灯: [OK] {r2.message}')
    r3 = services.execute('turn_on', source='remote')
    print(f'  遥控器 开灯: [BLOCKED] {r3.error}')

    # 切换回全部开放
    print('\n--- 切换回: 全部开放 ---')
    services.set_control_mode('all')
    r3 = services.execute('turn_on', source='remote')
    print(f'  遥控器 开灯: [OK] {r3.message}')

    print('\n' + '=' * 50)
    print('    测试完成')
    print('=' * 50)

if __name__ == '__main__':
    main()
