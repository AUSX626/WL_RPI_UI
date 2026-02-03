# Smart Lamp UI 接口文档

## 📌 概述

本项目后端使用 Python 服务层，UI 开发者可以通过以下方式与后端通信：

1. **Python 直接调用**（推荐，适合 Tkinter/PyQt）
2. **HTTP API**（适合 Web/Flutter/其他语言）

---

## 🚀 快速开始

### 安装依赖
```bash
cd smart_lamp_ui
pip install -r requirements/base.txt
```

### 测试服务层
```bash
python test_services.py      # 测试数据服务
python test_command_service.py  # 测试命令系统
```

---

## 📡 方式一：Python 直接调用（推荐）

```python
from smart_lamp.services import ServiceManager

# 初始化（只需要一次）
services = ServiceManager(data_dir="data")

# 之后就可以调用各种功能了
```

### 🎮 执行命令（UI 按钮点击）

```python
# 通用格式
result = services.execute("命令名", {"参数": "值"}, source="ui")

# 返回值
result.success   # bool - 是否成功
result.message   # str  - 提示消息（可以显示给用户）
result.data      # dict - 额外数据
```

### 📋 可用命令列表

| 命令 | 参数 | 说明 | 示例 |
|-----|------|------|------|
| `enter_study_mode` | 无 | 进入学习模式 | `services.execute("enter_study_mode", source="ui")` |
| `enter_pet_mode` | 无 | 进入宠物模式 | `services.execute("enter_pet_mode", source="ui")` |
| `enter_hand_follow` | 无 | 进入手势跟随 | `services.execute("enter_hand_follow", source="ui")` |
| `enter_standby` | 无 | 进入待机 | `services.execute("enter_standby", source="ui")` |
| `turn_on` | 无 | 开灯 | `services.execute("turn_on", source="ui")` |
| `turn_off` | 无 | 关灯 | `services.execute("turn_off", source="ui")` |
| `set_brightness` | `{value: 0.0-1.0}` | 设置亮度 | `services.execute("set_brightness", {"value": 0.8}, source="ui")` |
| `brightness_up` | 无 | 亮度+10% | `services.execute("brightness_up", source="ui")` |
| `brightness_down` | 无 | 亮度-10% | `services.execute("brightness_down", source="ui")` |
| `pet_interact` | `{action: "pet/play/talk"}` | 宠物互动 | `services.execute("pet_interact", {"action": "pet"}, source="ui")` |
| `start_study` | `{mode: "normal/pomodoro"}` | 开始学习 | `services.execute("start_study", {"mode": "pomodoro"}, source="ui")` |
| `end_study` | 无 | 结束学习 | `services.execute("end_study", source="ui")` |
| `start_pomodoro` | 无 | 开始番茄钟 | `services.execute("start_pomodoro", source="ui")` |
| `add_reminder` | `{content, minutes/time}` | 添加提醒 | `services.execute("add_reminder", {"content": "喝水", "minutes": 30}, source="ui")` |

---

## 📊 读取数据

### 设置
```python
# 获取所有设置
all_settings = services.settings.get_all()

# 获取单个设置
volume = services.settings.volume           # 音量 0-100
brightness = services.settings.default_brightness  # 默认亮度 0.0-1.0
pomodoro_work = services.settings.pomodoro_work    # 番茄钟时长（分钟）

# 修改设置
services.settings.set("volume", 80)
services.settings.set("default_brightness", 0.6)
```

### 宠物状态
```python
# 获取状态
mood = services.pet.current_mood.value  # "happy", "sad", "sleepy", "excited", "bored"
happiness = services.pet.happiness      # 开心度 0-100
energy = services.pet.energy            # 精力值 0-100
affection = services.pet.affection      # 亲密度 0-100

# 获取完整状态字典
pet_status = services.pet.get_status_dict()
# {
#   "name": "宝莉",
#   "mood": "happy",
#   "happiness": 75,
#   "energy": 60,
#   "affection": 45,
#   "suggested_action": "nod"
# }

# 互动
result = services.pet.interact("pet")  # 摸头
# result = {"message": "摸摸头，开心！", "effects": {...}, "mood": "happy"}
```

### 学习统计
```python
# 是否正在学习
is_studying = services.study.is_studying

# 今日统计
today = services.study.get_today_stats()
# {"total_minutes": 120, "session_count": 4, "pomodoro_count": 5}

# 目标进度
progress = services.study.get_goal_progress()
# {"goal": 120, "actual": 45.5, "progress": 0.38}
```

### 日程提醒
```python
# 获取所有提醒
reminders = services.schedule.get_all_reminders()

# 添加提醒
services.schedule.add_reminder("喝水", minutes=30)
services.schedule.add_reminder("吃药", time="08:00", repeat="daily")

# 删除提醒
services.schedule.delete_reminder(reminder_id)
```

---

## 🖼️ UI 示例代码（Tkinter）

```python
import tkinter as tk
from smart_lamp.services import ServiceManager

class SmartLampUI:
    def __init__(self):
        self.services = ServiceManager(data_dir="data")
        self.root = tk.Tk()
        self.root.title("智能台灯")
        self.setup_ui()
    
    def setup_ui(self):
        # 模式按钮
        tk.Button(self.root, text="🐾 宠物模式", 
                  command=self.enter_pet_mode).pack(pady=5)
        tk.Button(self.root, text="📚 学习模式",
                  command=self.enter_study_mode).pack(pady=5)
        
        # 亮度滑块
        self.brightness_var = tk.DoubleVar(value=0.8)
        tk.Scale(self.root, from_=0, to=1, resolution=0.1,
                 variable=self.brightness_var, orient="horizontal",
                 command=self.on_brightness_change).pack()
        
        # 宠物状态显示
        self.mood_label = tk.Label(self.root, text="心情: --")
        self.mood_label.pack()
        
        # 定时刷新状态
        self.update_status()
    
    def enter_pet_mode(self):
        result = self.services.execute("enter_pet_mode", source="ui")
        print(result.message)
    
    def enter_study_mode(self):
        result = self.services.execute("enter_study_mode", source="ui")
        print(result.message)
    
    def on_brightness_change(self, value):
        self.services.execute("set_brightness", {"value": float(value)}, source="ui")
    
    def update_status(self):
        # 更新宠物状态
        mood = self.services.pet.current_mood.value
        happiness = self.services.pet.happiness
        self.mood_label.config(text=f"心情: {mood} ({happiness}%)")
        
        # 每秒刷新
        self.root.after(1000, self.update_status)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SmartLampUI()
    app.run()
```

---

## 🔄 监听事件（可选）

如果 UI 需要响应后端事件（如提醒触发、宠物状态变化）：

```python
# 监听设置变化
services.settings.on_change(lambda key, old, new: 
    print(f"设置变化: {key} = {new}"))

# 监听提醒触发
services.schedule.on_trigger(lambda reminder:
    show_notification(reminder.content))

# 监听命令执行
services.command.add_listener(lambda cmd, result:
    print(f"命令: {cmd.name} -> {result.message}"))
```

---

## 📁 数据文件位置

```
data/
├── settings.json      # 用户设置
├── pet_state.json     # 宠物状态
├── study_records.json # 学习记录
└── reminders.json     # 提醒列表
```

---

## 🎛️ 控制权管理（重要！）

UI 可以设置谁有权控制设备，防止多个输入源冲突。

### 可用的控制模式

| 模式 | 说明 | 允许的输入源 |
|-----|------|------------|
| `ui_only` | 仅 UI 控制 | UI、系统、定时器 |
| `voice_only` | 仅语音控制 | 语音、系统、定时器 |
| `remote_only` | 仅遥控器控制 | 遥控器、系统、定时器 |
| `ui_voice` | UI + 语音 | UI、语音、系统、定时器 |
| `ui_remote` | UI + 遥控器 | UI、遥控器、系统、定时器 |
| `all` | 全部开放（默认） | 所有输入源 |

### 使用方法

```python
# 获取所有可用的控制模式（用于下拉框）
options = services.get_control_mode_options()
# {'ui_only': '仅 UI 控制', 'voice_only': '仅语音控制', ...}

# 获取当前控制模式
current = services.get_control_mode()  # "all"

# 设置控制模式
services.set_control_mode("ui_only")      # 只允许 UI 控制
services.set_control_mode("ui_voice")     # 允许 UI 和语音
services.set_control_mode("all")          # 全部开放

# 监听控制模式变化
services.on_control_mode_change(lambda mode: 
    print(f"控制模式变为: {mode.value}"))
```

### UI 示例：控制模式切换下拉框

```python
import tkinter as tk
from tkinter import ttk

# 创建下拉框
control_mode_var = tk.StringVar(value="all")
options = services.get_control_mode_options()

combo = ttk.Combobox(root, textvariable=control_mode_var, 
                     values=list(options.keys()))
combo.pack()

# 绑定切换事件
def on_mode_change(event):
    mode = control_mode_var.get()
    services.set_control_mode(mode)
    print(f"已切换到: {options[mode]}")

combo.bind("<<ComboboxSelected>>", on_mode_change)
```

### 被拒绝时的处理

当输入源被禁止时，`execute()` 返回：
```python
result = services.execute("turn_on", source="voice")  # 在 ui_only 模式下

result.success  # False
result.error    # "SOURCE_NOT_ALLOWED"
result.message  # "当前控制模式(ui_only)不允许 voice 控制"
```

---

## ❓ 常见问题

### Q: UI 发送的命令如何被执行？

**重要架构理解：**

```
┌─────────────────────────────────────────────────────────────────┐
│                    命令执行流程                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   UI (Tkinter/Web)           ServiceManager          MainController
│   ────────────────           ──────────────          ──────────────
│                                                                 │
│   用户点击                                                       │
│   "学习模式" ──────►  execute("enter_study_mode")                │
│                              │                                  │
│                              ▼                                  │
│                      CommandService                             │
│                      - 验证权限                                  │
│                      - 记录日志                                  │
│                      - 返回 result                              │
│                              │                                  │
│                              │ add_listener() 监听              │
│                              ▼                                  │
│                      MainController._on_ui_command()            │
│                      - 切换状态机                                │
│                      - 启动摄像头/舵机                           │
│                      - 真正执行动作！                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**所以：**
- UI 只管发命令，不管怎么执行
- `ServiceManager` 管数据和权限
- `MainController` (run.py) 管硬件执行

### Q: UI 开发时怎么测试命令是否正确？

```python
# test_ui_logic.py
from smart_lamp.services import ServiceManager

services = ServiceManager(data_dir="data")

# 测试命令格式是否正确
result = services.execute("enter_study_mode", source="ui")
print(result.success)   # True = 命令格式正确
print(result.message)   # "切换到学习模式"

# 测试参数是否正确
result = services.execute("set_brightness", {"value": 0.5}, source="ui")
print(result.success)   # True = 参数正确

# 测试无效命令
result = services.execute("invalid_command", source="ui")
print(result.success)   # False
print(result.error)     # "UNKNOWN_COMMAND"
```

**关键点：**
- 命令返回 `success=True` 表示**命令格式正确、权限通过**
- **不代表**硬件已执行（需要 run.py 运行）
- UI 开发时只需确保命令格式正确即可

### Q: 如何获取当前模式？
```python
# 目前需要通过 MainController，后续会添加到 services
# 临时方案：在 UI 中自己维护当前模式状态
```

### Q: 如何播放动画？
```python
# 获取建议动作
action = services.pet.get_mood_action()  # "nod", "jump", "yawn" 等
# UI 根据 action 播放对应动画
```

### Q: 数据多久保存一次？
自动保存，每次修改后立即写入 JSON 文件。

---

## 📞 联系

有问题请联系后端开发者，或在仓库提 Issue。
