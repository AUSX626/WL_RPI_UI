#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI 通信示例

演示如何让 UI 与后端服务通信

方式1: 直接调用（同进程，推荐用于本地 GUI）
方式2: HTTP API（跨进程/跨设备，用于 Web/手机App）
"""
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# 方式 1: 直接调用（本地 GUI 推荐）
# ============================================================

def demo_direct_call():
    """
    直接调用服务层
    
    适用于: PyQt、Tkinter 等本地 GUI
    优点: 简单、快速、无需启动 HTTP 服务
    """
    print("\n" + "=" * 60)
    print("方式 1: 直接调用服务层")
    print("=" * 60)
    
    from smart_lamp.services import ServiceManager
    
    # 初始化服务（这就是 UI 需要的后端）
    services = ServiceManager(data_dir="data")
    
    # ===== 模拟 UI 操作 =====
    
    # UI: 显示宠物状态
    print("\n[UI] 获取宠物状态:")
    pet_status = services.pet.get_status_dict()
    print(f"  名字: {pet_status['name']}")
    print(f"  心情: {pet_status['mood']}")
    print(f"  开心度: {pet_status['happiness']}")
    
    # UI: 用户点击"摸头"按钮
    print("\n[UI] 用户点击: 摸头")
    result = services.pet.interact("pet")
    print(f"  宠物说: {result['message']}")
    print(f"  新心情: {result['mood']}")
    
    # UI: 获取设置
    print("\n[UI] 获取设置:")
    print(f"  音量: {services.settings.volume}")
    print(f"  亮度: {services.settings.default_brightness}")
    
    # UI: 修改设置
    print("\n[UI] 用户调整音量滑块到 60")
    services.settings.set("volume", 60)
    print(f"  新音量: {services.settings.volume}")
    
    # UI: 开始学习
    print("\n[UI] 用户点击: 开始学习")
    session_id = services.study.start_session("pomodoro")
    print(f"  会话ID: {session_id}")
    
    # UI: 查看今日统计
    print("\n[UI] 查看今日学习统计:")
    today = services.study.get_today_stats()
    print(f"  今日学习: {today['total_minutes']} 分钟")
    
    # UI: 添加提醒
    print("\n[UI] 用户添加提醒: 30分钟后喝水")
    reminder = services.schedule.add_reminder("喝水", minutes=30)
    print(f"  提醒ID: {reminder.id}")
    print(f"  触发时间: {reminder.trigger_time}")
    
    return services


# ============================================================
# 方式 2: HTTP API（Web/手机App）
# ============================================================

def demo_http_api():
    """
    通过 HTTP API 调用
    
    适用于: Web 前端、手机 App、其他设备
    需要: pip install fastapi uvicorn requests
    """
    print("\n" + "=" * 60)
    print("方式 2: HTTP API 调用")
    print("=" * 60)
    
    try:
        import requests
    except ImportError:
        print("请先安装 requests: pip install requests")
        return
    
    API_BASE = "http://localhost:8080/api"
    
    # 检查服务器是否运行
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=2)
        if resp.status_code != 200:
            print("API 服务器未运行，请先启动")
            return
    except:
        print("API 服务器未运行")
        print("\n要启动 API 服务器，运行:")
        print("  python test_api_server.py")
        return
    
    # ===== 模拟 UI 请求 =====
    
    # GET 宠物状态
    print("\n[UI] GET /api/pet")
    resp = requests.get(f"{API_BASE}/pet")
    print(f"  响应: {resp.json()}")
    
    # POST 互动
    print("\n[UI] POST /api/pet/interact")
    resp = requests.post(f"{API_BASE}/pet/interact", json={"action": "pet"})
    print(f"  响应: {resp.json()}")
    
    # GET 设置
    print("\n[UI] GET /api/settings")
    resp = requests.get(f"{API_BASE}/settings")
    print(f"  响应: {resp.json()}")
    
    # PUT 修改设置
    print("\n[UI] PUT /api/settings/volume")
    resp = requests.put(f"{API_BASE}/settings/volume", json={"value": 70})
    print(f"  响应: {resp.json()}")


# ============================================================
# 方式 3: 简单的 Tkinter GUI 示例
# ============================================================

def demo_tkinter_gui():
    """
    简单的 Tkinter GUI 示例
    
    展示如何创建一个简单的桌宠控制界面
    """
    print("\n" + "=" * 60)
    print("方式 3: Tkinter GUI 示例")
    print("=" * 60)
    
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except ImportError:
        print("Tkinter 不可用")
        return
    
    from smart_lamp.services import ServiceManager
    
    # 初始化服务
    services = ServiceManager(data_dir="data")
    
    # 创建窗口
    root = tk.Tk()
    root.title("智能桌宠控制面板")
    root.geometry("400x500")
    
    # ===== 宠物状态区域 =====
    pet_frame = ttk.LabelFrame(root, text="🐾 宠物状态", padding=10)
    pet_frame.pack(fill="x", padx=10, pady=5)
    
    # 状态标签
    mood_var = tk.StringVar(value=f"心情: {services.pet.current_mood.value}")
    happiness_var = tk.StringVar(value=f"开心度: {services.pet.happiness}")
    energy_var = tk.StringVar(value=f"精力值: {services.pet.energy}")
    
    ttk.Label(pet_frame, textvariable=mood_var).pack(anchor="w")
    ttk.Label(pet_frame, textvariable=happiness_var).pack(anchor="w")
    ttk.Label(pet_frame, textvariable=energy_var).pack(anchor="w")
    
    def update_pet_display():
        """更新宠物状态显示"""
        mood_var.set(f"心情: {services.pet.current_mood.value}")
        happiness_var.set(f"开心度: {services.pet.happiness}")
        energy_var.set(f"精力值: {services.pet.energy}")
    
    # 互动按钮
    btn_frame = ttk.Frame(pet_frame)
    btn_frame.pack(fill="x", pady=5)
    
    def interact(action):
        result = services.pet.interact(action)
        messagebox.showinfo("宠物说", result['message'])
        update_pet_display()
    
    ttk.Button(btn_frame, text="摸头 🖐️", command=lambda: interact("pet")).pack(side="left", padx=2)
    ttk.Button(btn_frame, text="玩耍 🎾", command=lambda: interact("play")).pack(side="left", padx=2)
    ttk.Button(btn_frame, text="表扬 👏", command=lambda: interact("praise")).pack(side="left", padx=2)
    
    # ===== 设置区域 =====
    settings_frame = ttk.LabelFrame(root, text="⚙️ 设置", padding=10)
    settings_frame.pack(fill="x", padx=10, pady=5)
    
    # 音量滑块
    ttk.Label(settings_frame, text="音量:").pack(anchor="w")
    volume_var = tk.IntVar(value=services.settings.volume)
    
    def on_volume_change(val):
        services.settings.set("volume", int(float(val)))
    
    volume_scale = ttk.Scale(settings_frame, from_=0, to=100, variable=volume_var, 
                              command=on_volume_change)
    volume_scale.pack(fill="x")
    
    # 亮度滑块
    ttk.Label(settings_frame, text="默认亮度:").pack(anchor="w")
    brightness_var = tk.DoubleVar(value=services.settings.default_brightness)
    
    def on_brightness_change(val):
        services.settings.set("default_brightness", float(val))
    
    brightness_scale = ttk.Scale(settings_frame, from_=0.0, to=1.0, variable=brightness_var,
                                  command=on_brightness_change)
    brightness_scale.pack(fill="x")
    
    # ===== 学习区域 =====
    study_frame = ttk.LabelFrame(root, text="📚 学习", padding=10)
    study_frame.pack(fill="x", padx=10, pady=5)
    
    study_status_var = tk.StringVar(value="未在学习")
    ttk.Label(study_frame, textvariable=study_status_var).pack(anchor="w")
    
    today_stats = services.study.get_today_stats()
    today_var = tk.StringVar(value=f"今日学习: {today_stats['total_minutes']:.1f} 分钟")
    ttk.Label(study_frame, textvariable=today_var).pack(anchor="w")
    
    def start_study():
        services.study.start_session("pomodoro")
        study_status_var.set("学习中... 🍅")
    
    def end_study():
        session = services.study.end_session()
        if session:
            study_status_var.set(f"已学习 {session.duration_minutes:.1f} 分钟")
            today = services.study.get_today_stats()
            today_var.set(f"今日学习: {today['total_minutes']:.1f} 分钟")
        else:
            study_status_var.set("未在学习")
    
    study_btn_frame = ttk.Frame(study_frame)
    study_btn_frame.pack(fill="x", pady=5)
    ttk.Button(study_btn_frame, text="开始学习", command=start_study).pack(side="left", padx=2)
    ttk.Button(study_btn_frame, text="结束学习", command=end_study).pack(side="left", padx=2)
    
    # ===== 提醒区域 =====
    reminder_frame = ttk.LabelFrame(root, text="⏰ 提醒", padding=10)
    reminder_frame.pack(fill="x", padx=10, pady=5)
    
    reminder_entry = ttk.Entry(reminder_frame)
    reminder_entry.pack(fill="x")
    reminder_entry.insert(0, "喝水")
    
    def add_reminder():
        content = reminder_entry.get()
        if content:
            reminder = services.schedule.add_reminder(content, minutes=30)
            messagebox.showinfo("提醒已添加", f"将在 30 分钟后提醒: {content}")
    
    ttk.Button(reminder_frame, text="30分钟后提醒", command=add_reminder).pack(pady=5)
    
    # 运行
    print("启动 Tkinter GUI...")
    root.mainloop()


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 60)
    print("    UI 通信示例")
    print("=" * 60)
    print("\n选择演示模式:")
    print("  1. 直接调用服务层（命令行演示）")
    print("  2. HTTP API 调用（需要先启动服务器）")
    print("  3. Tkinter GUI 示例")
    print("  q. 退出")
    
    while True:
        choice = input("\n请选择 (1/2/3/q): ").strip()
        
        if choice == "1":
            demo_direct_call()
        elif choice == "2":
            demo_http_api()
        elif choice == "3":
            demo_tkinter_gui()
            break  # GUI 会阻塞，退出后结束
        elif choice.lower() == "q":
            break
        else:
            print("无效选择")


if __name__ == "__main__":
    main()
