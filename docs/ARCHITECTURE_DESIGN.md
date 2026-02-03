# 系统架构设计文档 v2.0

> 本文档定义以 UI 为主导的系统架构，所有功能和模式以 UI 中的功能为准。
> 
> **v2.0 更新**：移除语音切换、舵机控制、灯光控制；新增串口通信模块。

---

## 🎯 核心理念

**UI 是系统的唯一入口和功能定义者**

- UI 定义所有用户可见的功能和模式
- **模式切换完全由 UI 触发**，不再支持语音唤醒切换
- Services 层负责"翻译"UI 请求，调用底层控制器
- Modules 层提供硬件抽象（串口通信、视觉、TTS）

---

## 🏗️ 四层架构（精简版）

```
┌─────────────────────────────────────────────────────────────┐
│                      UI 层 (主导者)                          │
│  ui/                                                        │
│  ├── main.py          # 主窗口，功能入口                     │
│  ├── face.py          # 眼睛动画组件（休眠/唤醒界面）         │
│  ├── mainwindow.ui    # Qt Designer 界面布局                 │
│  ├── pages/           # 各功能页面组件                       │
│  └── components/      # 可复用 UI 组件                       │
│                                                             │
│  【职责】                                                    │
│  - 定义所有用户功能（按钮、页面）                            │
│  - 接收用户输入（触摸点击）                                  │
│  - 显示系统状态和反馈                                        │
│  - 调用 Services 层执行操作                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 调用 command_service.execute_from_ui(...)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Services 层 (翻译器)                       │
│  smart_lamp/services/                                       │
│  ├── command_service.py    # 统一指令入口（核心桥梁）        │
│  ├── service_manager.py    # 服务管理器                      │
│  ├── pet_service.py        # 宠物状态管理                    │
│  ├── settings_service.py   # 设置管理                        │
│  ├── schedule_service.py   # 日程提醒                        │
│  └── study_service.py      # 学习记录                        │
│                                                             │
│  【职责】                                                    │
│  - 接收 UI 的高层指令（如 "enter_pet_mode"）                 │
│  - 翻译成 Controller 能理解的操作                            │
│  - 管理业务数据（宠物状态、学习记录等）                       │
│  - 返回结果给 UI 显示                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 调用 controller.switch_mode(...) 等
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core 层 (调度中心)                        │
│  smart_lamp/core/                                           │
│  ├── main_controller.py    # 主控制器                        │
│  ├── state_machine.py      # 状态机                          │
│  └── message_bus.py        # 消息总线（事件分发）             │
│                                                             │
│  smart_lamp/modes/                                          │
│  ├── base_mode.py          # 模式基类                        │
│  ├── standby_mode.py       # 待机模式（眼睛动画）             │
│  ├── pet_mode.py           # 宠物互动模式                    │
│  ├── study_mode.py         # 学习模式（番茄钟）              │
│  └── ...                   # 其他模式                        │
│                                                             │
│  【职责】                                                    │
│  - 管理系统状态和模式切换                                    │
│  - 协调各硬件模块                                            │
│  - 执行具体的模式逻辑                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 调用 serial.send(...), vision.detect(...) 等
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Modules 层 (硬件驱动)                      │
│  smart_lamp/modules/                                        │
│                                                             │
│  ├── serial/               # ★ 串口通信（新增）              │
│  │   ├── __init__.py                                        │
│  │   ├── serial_thread.py  # 串口收发线程                    │
│  │   └── protocol.py       # 通信协议定义                    │
│  │                                                          │
│  ├── vision/               # 视觉处理                        │
│  │   ├── camera.py         # 摄像头                          │
│  │   ├── gesture_detector.py  # 手势检测                     │
│  │   ├── face_detector.py  # 人脸检测                        │
│  │   └── vision_thread.py  # 视觉处理线程                    │
│  │                                                          │
│  ├── speaker/              # 扬声器（TTS 预留）              │
│  │   ├── __init__.py                                        │
│  │   ├── speaker_thread.py # 音频播放线程                    │
│  │   └── tts_engine.py     # TTS 引擎（预留）                │
│  │                                                          │
│  ├── ❌ servo/             # 【已删除】舵机控制               │
│  ├── ❌ voice/             # 【已删除】语音识别/唤醒          │
│  └── ❌ lighting/          # 【已删除】灯光控制               │
│                                                             │
│  【职责】                                                    │
│  - 直接操作硬件（串口、摄像头）                              │
│  - 提供硬件抽象接口给上层                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 串口通信模块设计

### 硬件配置（树莓派 CM5）

| 功能 | GPIO | 说明 |
|------|------|------|
| TX | GPIO14 | CM5 发送端 |
| RX | GPIO15 | CM5 接收端 |

### 模块结构

```
smart_lamp/modules/serial/
├── __init__.py
├── serial_thread.py      # 串口收发线程
│   ├── SerialThread       # 后台线程，持续监听
│   ├── send(data)         # 发送数据
│   ├── on_receive(callback)  # 注册接收回调
│   └── close()            # 关闭连接
│
└── protocol.py           # 通信协议定义
    ├── ProtocolFrame      # 帧结构定义
    ├── encode(cmd, data)  # 编码
    └── decode(raw)        # 解码
```

### 配置项（config/config.yaml）

```yaml
serial:
  enabled: true
  port: "/dev/ttyAMA0"     # CM5 默认串口
  baudrate: 115200
  timeout: 1.0
  # GPIO 配置（通过 dtoverlay 启用）
  # dtoverlay=uart0,txd0=14,rxd0=15
```

### 预留接口

```python
# serial_thread.py 骨架

import threading
import serial
from typing import Callable, Optional

class SerialThread:
    """
    串口通信线程
    
    GPIO14 -> TX (发送)
    GPIO15 -> RX (接收)
    """
    
    def __init__(self, port: str = "/dev/ttyAMA0", baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self._serial: Optional[serial.Serial] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_receive: Optional[Callable[[bytes], None]] = None
    
    def start(self):
        """启动串口线程"""
        # TODO: 实现
        pass
    
    def stop(self):
        """停止串口线程"""
        # TODO: 实现
        pass
    
    def send(self, data: bytes):
        """发送数据"""
        # TODO: 实现
        pass
    
    def on_receive(self, callback: Callable[[bytes], None]):
        """注册接收回调"""
        self._on_receive = callback
    
    def _run(self):
        """线程主循环"""
        # TODO: 实现
        pass
```

---

## 📱 UI 页面与模式映射

根据 UI 的侧边栏按钮，系统有以下页面/模式：

| 侧边栏按钮 | UI 页面 | 对应模式/功能 | Modules 组合 | 摄像头 |
|-----------|---------|--------------|-------------|:------:|
| `pushButton_5` (Mode) | `Page_Mode` | 模式选择面板 | - | - |
| `pushButton` (Light) | `Page_LightControl` | 屏幕亮度控制 | - (UI 直接控制) | - |
| `pushButton_2` (Pet) | `Page_PetInteraction` | 宠物互动模式 | vision + speaker | ✅ |
| `pushButton_3` (Learning) | `Page_Learning` | 学习/番茄钟模式 | vision + speaker | ✅ |
| `pushButton_6` (Reminders) | `Page_Reminders` | 日程提醒管理 | speaker | - |
| `pushButton_7` (System) | `Page_System` | 系统设置 | serial (调试接口) | - |
| `pushButton_4` (Sleep) | `page_face` | 休眠/待机 | vision | ✅ |

### Page_Mode 中的核心模式

| 按钮 | 模式名 | 说明 | Modules 组合 | 摄像头 |
|------|--------|------|-------------|:------:|
| `pushButton_standby` | 待机模式 | 进入休眠界面（眼睛动画） | vision | ✅ |
| `pushButton_handfollow` | 手势跟随 | 检测手部位置并跟随 | vision + serial | ✅ |
| `pushButton_petmode` | 宠物模式 | 宠物互动 | vision + speaker | ✅ |
| `pushButton_studymode` | 学习模式 | 番茄钟计时、专注检测 | vision + speaker | ✅ |
| `pushButton_settings` | 设置 | 进入设置页面 | - | - |
| `pushButton_switchmode` | 模式切换 | 通用模式切换入口 | - | - |

---

## 🎮 模式与 Modules 组合

### 模式定义

```python
# modes/base_mode.py

class BaseMode:
    """模式基类"""
    
    name: str = "base"
    
    def __init__(self, controller):
        self.controller = controller
        self.modules = controller.modules  # 访问所有 modules
    
    def start(self):
        """进入模式时调用"""
        raise NotImplementedError
    
    def stop(self):
        """退出模式时调用"""
        raise NotImplementedError
    
    def update(self):
        """模式运行中的更新逻辑（可选）"""
        pass
```

### 各模式的 Modules 组合

#### 1. 待机模式 (StandbyMode)
```python
class StandbyMode(BaseMode):
    """
    待机模式 - 显示眼睛动画，检测特定手势唤醒
    
    使用的 Modules:
    - vision: 手势检测（用于唤醒）
    
    【框架预留】具体唤醒手势待后续完善
    """
    name = "standby"
    
    def start(self):
        # 通知 UI 显示 page_face（眼睛动画）
        self.controller.emit_event("ui:show_face")
        # 启动视觉检测，用于手势唤醒
        self.modules.vision.start()
        self.modules.vision.on_gesture(self._on_gesture_detected)
    
    def stop(self):
        self.modules.vision.stop()
    
    def _on_gesture_detected(self, gesture):
        """检测到特定手势时唤醒"""
        # TODO: 定义具体唤醒手势
        if gesture == "wake_up_gesture":
            self.controller.emit_event("ui:wake_up")
```

#### 2. 宠物互动模式 (PetMode)
```python
class PetMode(BaseMode):
    """
    宠物互动模式 - 识别手势/人脸，做出响应
    
    使用的 Modules:
    - vision: 手势识别、人脸检测
    - speaker: TTS 语音反馈（预留）
    - serial: 发送动作指令到外部设备（预留）
    
    【框架预留】具体交互逻辑待后续完善
    """
    name = "pet"
    
    def start(self):
        # 启动视觉检测
        self.modules.vision.start()
        self.modules.vision.on_gesture(self._on_gesture)
        self.modules.vision.on_face(self._on_face)
    
    def stop(self):
        self.modules.vision.stop()
    
    def _on_gesture(self, gesture):
        """手势识别回调"""
        # TODO: 定义宠物互动手势
        pass
    
    def _on_face(self, face_data):
        """人脸检测回调"""
        # TODO: 人脸跟随/表情识别
        pass
```

#### 3. 学习模式 (StudyMode)
```python
class StudyMode(BaseMode):
    """
    学习模式 - 番茄钟计时、专注检测、休息提醒
    
    使用的 Modules:
    - vision: 专注度检测（人脸/姿态）
    - speaker: 播放提醒音（预留）
    
    使用的 Services:
    - study_service: 记录学习时长
    
    【框架预留】专注检测逻辑待后续完善
    """
    name = "study"
    
    def start(self):
        # 启动番茄钟计时
        self.controller.services.study.start_session()
        # 启动视觉检测（专注度监测）
        self.modules.vision.start()
        self.modules.vision.on_face(self._on_face)
    
    def stop(self):
        self.modules.vision.stop()
        self.controller.services.study.end_session()
    
    def _on_face(self, face_data):
        """人脸检测回调 - 用于专注度监测"""
        # TODO: 检测用户是否在看屏幕、是否走神等
        pass
    
    def on_pomodoro_complete(self):
        # TODO: 播放完成提示音
        pass
```

#### 4. 手势跟随模式 (HandFollowMode)
```python
class HandFollowMode(BaseMode):
    """
    手势跟随模式 - 检测手部位置，发送给外部设备
    
    使用的 Modules:
    - vision: 手部检测
    - serial: 发送位置数据到外部控制器
    """
    name = "hand_follow"
    
    def start(self):
        self.modules.vision.start()
        self.modules.vision.on_hand(self._on_hand)
    
    def stop(self):
        self.modules.vision.stop()
    
    def _on_hand(self, hand_data):
        """手部位置回调"""
        x, y = hand_data.get("x"), hand_data.get("y")
        # 通过串口发送位置
        # self.modules.serial.send(f"POS:{x},{y}".encode())
        pass
```

---

## 📦 数据存储设计

### 数据目录结构

```
data/
├── settings.json       # 系统设置（默认配置 + 用户修改）
├── pet_state.json      # 宠物状态（个性化数据）
├── study_records.json  # 学习记录
└── reminders.json      # 日程提醒
```

### 默认配置 vs 用户数据

| 文件 | 类型 | 说明 |
|------|------|------|
| `config/config.yaml` | 默认配置 | 系统级配置，不随用户改变 |
| `config/config.default.yaml` | 出厂配置 | 恢复出厂设置时使用 |
| `data/settings.json` | 用户配置 | 用户修改的个性化设置 |
| `data/pet_state.json` | 用户数据 | 宠物状态（随交互变化） |
| `data/study_records.json` | 用户数据 | 学习历史记录 |
| `data/reminders.json` | 用户数据 | 用户添加的提醒 |

### settings.json 结构（精简版）

```json
{
  // === 音频设置 ===
  "volume": 80,
  "speech_rate": 1.0,
  "voice_name": "zh-CN-XiaoxiaoNeural",
  
  // === 番茄钟设置 ===
  "pomodoro_work": 25,
  "pomodoro_short_break": 5,
  "pomodoro_long_break": 15,
  "pomodoro_rounds": 4,
  
  // === 宠物设置 ===
  "pet_name": "宝莉",
  "pet_personality": "活泼",
  "pet_idle_action_interval": 60,
  
  // === 系统设置 ===
  "language": "zh-CN",
  "debug_mode": false,
  "auto_update": true,
  
  // === 【已删除】以下配置不再使用 ===
  // "default_brightness": 0.6,      // 灯光相关
  // "wake_word": "宝莉",            // 语音唤醒相关
  // "wake_sensitivity": 0.8,        // 语音唤醒相关
  // "listening_timeout": 10.0,      // 语音唤醒相关
}
```

### pet_state.json 结构

```json
{
  "name": "宝莉",
  
  // 状态值 (0-100)
  "happiness": 100,
  "energy": 31,
  "affection": 63,
  "satiety": 70,
  
  // 性格特征 (0.0-1.0)
  "trait_active": 0.7,
  "trait_clingy": 0.5,
  "trait_sleepy": 0.3,
  "trait_curious": 0.6,
  
  // 统计
  "total_interactions": 14,
  "total_play_time": 0,
  "last_interaction": "2026-01-06 10:28:03",
  "created_at": "2025-12-27 16:32:59"
}
```

---

## 📁 最终目录结构

```
bubble_wheel_sys/
├── run.py                  # 后端主入口（无 UI 运行）
├── run_ui.py               # UI 主入口（带 UI 运行）★ 主要入口
│
├── ui/                     # UI 层（从 UI-main 迁移）
│   ├── __init__.py
│   ├── main.py             # 主窗口
│   ├── mainwindow.ui       # Qt Designer 文件
│   ├── components/
│   │   ├── __init__.py
│   │   └── face.py         # 眼睛动画
│   ├── pages/
│   │   └── __init__.py
│   ├── fonts/
│   └── icons/
│
├── smart_lamp/
│   ├── __init__.py
│   │
│   ├── core/               # 调度层
│   │   ├── __init__.py
│   │   ├── main_controller.py
│   │   ├── state_machine.py
│   │   └── message_bus.py
│   │
│   ├── modes/              # 模式实现
│   │   ├── __init__.py
│   │   ├── base_mode.py
│   │   ├── standby_mode.py     # 待机模式
│   │   ├── pet_mode.py         # 宠物互动
│   │   ├── study_mode.py       # 学习模式
│   │   └── hand_follow_mode.py # 手势跟随
│   │
│   ├── modules/            # 硬件驱动（精简版）
│   │   ├── __init__.py
│   │   │
│   │   ├── serial/         # ★ 串口通信（新增）
│   │   │   ├── __init__.py
│   │   │   ├── serial_thread.py
│   │   │   └── protocol.py
│   │   │
│   │   ├── vision/         # 视觉处理（保留）
│   │   │   ├── __init__.py
│   │   │   ├── camera.py
│   │   │   ├── gesture_detector.py
│   │   │   ├── face_detector.py
│   │   │   └── vision_thread.py
│   │   │
│   │   ├── speaker/        # 扬声器（预留）
│   │   │   ├── __init__.py
│   │   │   ├── speaker_thread.py
│   │   │   └── tts_engine.py
│   │   │
│   │   ├── ❌ servo/       # 【删除】
│   │   ├── ❌ voice/       # 【删除】
│   │   └── ❌ lighting/    # 【删除】
│   │
│   ├── services/           # 服务层
│   │   ├── __init__.py
│   │   ├── command_service.py
│   │   ├── service_manager.py
│   │   ├── pet_service.py
│   │   ├── settings_service.py
│   │   ├── schedule_service.py
│   │   └── study_service.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config_loader.py
│       └── logger.py
│
├── config/
│   ├── config.yaml         # 系统配置
│   ├── config.default.yaml # 出厂默认配置
│   └── actions.yaml        # 动作定义（如有）
│
├── data/                   # 用户数据（个性化）
│   ├── settings.json
│   ├── pet_state.json
│   ├── study_records.json
│   └── reminders.json
│
└── requirements/
    └── requirements.txt    # 需添加 PyQt5, pyserial
```

---

## ✅ 执行清单（更新版）

### 阶段一：清理代码
- [ ] 删除 `smart_lamp/modules/voice/` 目录
- [ ] 删除 `smart_lamp/modules/servo/` 目录
- [ ] 删除 `smart_lamp/modules/lighting/` 目录
- [ ] 移除 `main_controller.py` 中对 voice/servo/lighting 的引用
- [ ] 移除 `settings.json` 中已废弃的配置项

### 阶段二：新增串口模块
- [ ] 创建 `smart_lamp/modules/serial/__init__.py`
- [ ] 创建 `smart_lamp/modules/serial/serial_thread.py`（骨架）
- [ ] 创建 `smart_lamp/modules/serial/protocol.py`（骨架）
- [ ] 在 `config/config.yaml` 中添加串口配置

### 阶段三：迁移 UI
- [ ] 移动 `UI-main/main.py` → `ui/main.py`
- [ ] 移动 `UI-main/face.py` → `ui/components/face.py`
- [ ] 移动 `UI-main/mainwindow.ui` → `ui/mainwindow.ui`
- [ ] 复制 `UI-main/fonts/` → `ui/fonts/`
- [ ] 复制 `UI-main/icons/` → `ui/icons/`
- [ ] 修改导入路径

### 阶段四：重构模式
- [ ] 更新 `modes/` 下各模式，使用新的 modules 组合
- [ ] 移除模式中对 servo/voice/lighting 的依赖
- [ ] 添加串口调用接口（预留）

### 阶段五：更新依赖
- [ ] 添加 `PyQt5` 到 `requirements.txt`
- [ ] 确认 `pyserial` 已在依赖中

### 阶段六：删除旧代码
- [ ] 删除 `UI-main/SERVICE/` 目录
- [ ] 可选：删除整个 `UI-main/` 目录

---

## 🔆 屏幕亮度控制

屏幕亮度控制在 UI 层直接实现，通过系统 API 控制树莓派屏幕背光。

### 实现方式（UI 层）

```python
# ui/utils/brightness.py

import subprocess
from pathlib import Path

class ScreenBrightness:
    """
    树莓派屏幕亮度控制
    
    通过 /sys/class/backlight/ 控制背光
    """
    
    # 常见的背光路径
    BACKLIGHT_PATHS = [
        "/sys/class/backlight/rpi_backlight/brightness",
        "/sys/class/backlight/10-0045/brightness",
    ]
    
    def __init__(self):
        self._path = self._find_backlight_path()
        self._max_brightness = self._get_max_brightness()
    
    def _find_backlight_path(self):
        """查找可用的背光控制路径"""
        for path in self.BACKLIGHT_PATHS:
            if Path(path).exists():
                return path
        return None
    
    def _get_max_brightness(self):
        """获取最大亮度值"""
        if self._path:
            max_path = self._path.replace("brightness", "max_brightness")
            try:
                with open(max_path) as f:
                    return int(f.read().strip())
            except:
                pass
        return 255  # 默认值
    
    def set_brightness(self, value: int):
        """设置亮度 (0-100)"""
        if not self._path:
            print("[WARN] 未找到背光控制路径")
            return
        
        # 转换为实际值
        actual = int(value / 100 * self._max_brightness)
        actual = max(1, min(self._max_brightness, actual))  # 限制范围
        
        try:
            with open(self._path, 'w') as f:
                f.write(str(actual))
        except PermissionError:
            # 需要 sudo 权限，使用 subprocess
            subprocess.run(['sudo', 'sh', '-c', f'echo {actual} > {self._path}'])
    
    def get_brightness(self) -> int:
        """获取当前亮度 (0-100)"""
        if not self._path:
            return 100
        try:
            with open(self._path) as f:
                actual = int(f.read().strip())
                return int(actual / self._max_brightness * 100)
        except:
            return 100
```

### UI 中的调用

```python
# ui/main.py 中的亮度控制按钮绑定

from ui.utils.brightness import ScreenBrightness

class RobotWindow(QMainWindow):
    def __init__(self):
        # ...
        self.brightness = ScreenBrightness()
    
    def setup_light_control(self):
        # 亮度增加
        btn_up = self.findChild(QPushButton, "pushButton_brightup")
        btn_up.clicked.connect(lambda: self._adjust_brightness(10))
        
        # 亮度降低
        btn_down = self.findChild(QPushButton, "pushButton_brightdown")
        btn_down.clicked.connect(lambda: self._adjust_brightness(-10))
    
    def _adjust_brightness(self, delta: int):
        current = self.brightness.get_brightness()
        new_value = max(10, min(100, current + delta))
        self.brightness.set_brightness(new_value)
```

---

## 📋 框架预留功能清单

以下功能目前只搭建框架，待后续完善：

| 功能 | 位置 | 状态 | 说明 |
|------|------|:----:|------|
| 待机手势唤醒 | `modes/standby_mode.py` | 🔲 框架 | 需定义具体唤醒手势 |
| 宠物互动手势 | `modes/pet_mode.py` | 🔲 框架 | 需定义互动手势 |
| 专注度检测 | `modes/study_mode.py` | 🔲 框架 | 需定义检测逻辑 |
| TTS 语音合成 | `modules/speaker/` | 🔲 框架 | 需选择 TTS 引擎 |
| 串口通信协议 | `modules/serial/` | 🔲 框架 | 调试接口，按需实现 |

---

*文档版本: v2.1 | 更新日期: 2026-02-02*
