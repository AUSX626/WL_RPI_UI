#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务层测试脚本
测试各服务是否正常工作
"""
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from smart_lamp.services import ServiceManager


def test_settings_service():
    """测试设置服务"""
    print("\n" + "=" * 50)
    print("测试设置服务")
    print("=" * 50)
    
    from smart_lamp.services.settings_service import SettingsService
    
    settings = SettingsService(data_dir="data")
    
    # 获取默认值
    print(f"默认音量: {settings.volume}")
    print(f"默认亮度: {settings.default_brightness}")
    print(f"唤醒词: {settings.wake_word}")
    
    # 修改设置
    print("\n修改音量为 80...")
    settings.set("volume", 80)
    print(f"新音量: {settings.volume}")
    
    # 测试回调
    def on_change(key, old, new):
        print(f"  [回调] {key}: {old} -> {new}")
    
    settings.on_change(on_change)
    
    print("\n修改亮度为 0.6...")
    settings.set("default_brightness", 0.6)
    
    # 获取所有设置
    print("\n所有设置:")
    for k, v in settings.get_all().items():
        print(f"  {k}: {v}")
    
    print("\n✓ 设置服务测试通过")


def test_pet_service():
    """测试宠物服务"""
    print("\n" + "=" * 50)
    print("测试宠物服务")
    print("=" * 50)
    
    from smart_lamp.services.pet_service import PetService
    
    pet = PetService(data_dir="data")
    
    # 查看状态
    print(f"宠物名字: {pet.name}")
    print(f"当前心情: {pet.current_mood.value}")
    print(f"开心度: {pet.happiness}")
    print(f"精力值: {pet.energy}")
    print(f"亲密度: {pet.affection}")
    
    # 互动
    print("\n摸头...")
    result = pet.interact("pet")
    print(f"  回复: {result['message']}")
    print(f"  效果: {result['effects']}")
    
    print("\n玩耍...")
    result = pet.interact("play")
    print(f"  回复: {result['message']}")
    print(f"  新心情: {result['mood']}")
    
    # 获取动作
    action = pet.get_mood_action()
    print(f"\n建议动作: {action}")
    
    print("\n✓ 宠物服务测试通过")


def test_schedule_service():
    """测试日程服务"""
    print("\n" + "=" * 50)
    print("测试日程服务")
    print("=" * 50)
    
    from smart_lamp.services.schedule_service import ScheduleService
    
    schedule = ScheduleService(data_dir="data")
    
    # 清空旧提醒
    schedule.clear_all()
    
    # 添加提醒
    print("添加提醒: 1分钟后喝水")
    r1 = schedule.add_reminder("喝水", minutes=1)
    print(f"  ID: {r1.id}")
    print(f"  触发时间: {r1.trigger_time}")
    
    print("\n添加每日提醒: 08:00 吃药")
    r2 = schedule.add_reminder("吃药", time="08:00", repeat="daily")
    print(f"  ID: {r2.id}")
    
    # 查看所有提醒
    print("\n所有提醒:")
    for r in schedule.get_all_reminders():
        print(f"  [{r.id}] {r.content} @ {r.trigger_time} ({r.repeat})")
    
    # 注册触发回调
    def on_trigger(reminder):
        print(f"  [触发] {reminder.content}")
    
    schedule.on_trigger(on_trigger)
    
    print("\n✓ 日程服务测试通过")


def test_study_service():
    """测试学习服务"""
    print("\n" + "=" * 50)
    print("测试学习服务")
    print("=" * 50)
    
    from smart_lamp.services.study_service import StudyService
    import time
    
    study = StudyService(data_dir="data")
    
    # 开始学习
    print("开始学习会话...")
    session_id = study.start_session(mode="pomodoro")
    print(f"  会话ID: {session_id}")
    
    # 模拟学习
    print("\n模拟学习 2 秒...")
    time.sleep(2)
    
    # 添加番茄
    study.add_pomodoro()
    print(f"  当前时长: {study.get_current_duration():.1f} 分钟")
    
    # 结束学习
    print("\n结束学习会话...")
    session = study.end_session(completed=True)
    print(f"  时长: {session.duration_minutes} 分钟")
    print(f"  番茄数: {session.pomodoro_count}")
    
    # 查看统计
    print("\n今日统计:")
    today = study.get_today_stats()
    print(f"  总时长: {today['total_minutes']} 分钟")
    print(f"  会话数: {today['session_count']}")
    
    print("\n目标进度:")
    progress = study.get_goal_progress()
    print(f"  目标: {progress['goal']} 分钟")
    print(f"  完成: {progress['actual']:.1f} 分钟")
    print(f"  进度: {progress['progress']*100:.1f}%")
    
    print("\n✓ 学习服务测试通过")


def test_service_manager():
    """测试服务管理器"""
    print("\n" + "=" * 50)
    print("测试服务管理器")
    print("=" * 50)
    
    services = ServiceManager(data_dir="data")
    
    print("\n访问各服务:")
    print(f"  设置.音量: {services.settings.volume}")
    print(f"  宠物.心情: {services.pet.current_mood.value}")
    print(f"  学习.正在学习: {services.study.is_studying}")
    print(f"  日程.活跃提醒数: {len(services.schedule.get_active_reminders())}")
    
    print("\n获取全部状态:")
    status = services.get_all_status()
    print(f"  设置项数: {len(status['settings'])}")
    print(f"  宠物心情: {status['pet'].get('mood', 'N/A')}")
    
    print("\n✓ 服务管理器测试通过")


def main():
    """主测试函数"""
    print("=" * 50)
    print("    服务层测试")
    print("=" * 50)
    
    try:
        test_settings_service()
        test_pet_service()
        test_schedule_service()
        test_study_service()
        test_service_manager()
        
        print("\n" + "=" * 50)
        print("    ✓ 所有测试通过！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
