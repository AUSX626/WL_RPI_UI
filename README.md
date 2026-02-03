# 🏮 智能台灯控制系统 v3.0

> 基于树莓派 CM5 的智能交互台灯，PyQt5 触摸屏 UI + 视觉交互。

---

## ✨ 功能概览

### 🎯 四大模式

| 模式 | 功能 | 说明 |
|------|------|------|
| **😴 待机模式** | 低功耗待机，显示表情 | 检测到手势时唤醒 |
| **🖐️ 手部跟随** | 台灯头部跟随手部移动 | 通过串口发送位置数据 |
| **🐱 桌宠模式** | 宠物互动，表情动作 | 支持触摸、喂食等交互 |
| **📚 学习模式** | 番茄钟、专注检测 | 护眼提醒、学习统计 |

### 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    UI 层 (PyQt5)                        │
│     触摸屏界面、表情显示、模式切换、设置页面            │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                   Services 服务层                        │
│   SettingsService  PetService  StudyService  等         │
│              (数据持久化到 data/*.json)                  │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                    Core 核心层                           │
│     MainController  StateMachine  MessageBus            │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                   Modules 模块层                         │
│    VisionThread    SerialThread    SpeakerThread        │
│     (摄像头)        (GPIO串口)       (TTS预留)           │
└─────────────────────────────────────────────────────────┘
```


---

## 🚀 快速部署

### 1. 克隆项目

```bash
cd ~
git clone <your-repo> smart_lamp
cd smart_lamp
```

### 2. 一键安装

```bash
# 运行安装脚本
bash scripts/install.sh

# 或手动安装
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements/requirements.txt
```

### 3. 配置

```bash
# 复制配置模板
cp config/config.default.yaml config/config.yaml

# 编辑配置（可选）
nano config/config.yaml
```

### 4. 运行

```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动 UI（推荐）
python run_ui.py

# 调试模式
python run_ui.py --debug

# 仅启动 UI，不启动后端
python run_ui.py --no-backend
```

---

## 📁 项目结构

```
smart_lamp/
├── config/                     # 配置文件
│   ├── config.default.yaml     # 配置模板
│   ├── config.yaml             # 用户配置
│   └── actions.yaml            # 动作定义
│
├── data/                       # 持久化数据
│   ├── settings.json           # 用户设置
│   ├── pet_state.json          # 宠物状态
│   ├── study_records.json      # 学习记录
│   └── reminders.json          # 提醒列表
│
├── smart_lamp/                 # 核心代码
│   ├── core/                   # 核心模块
│   │   ├── main_controller.py  # 主控制器
│   │   ├── state_machine.py    # 状态机
│   │   └── message_bus.py      # 消息总线
│   │
│   ├── modes/                  # 功能模式
│   │   ├── base_mode.py        # 模式基类
│   │   ├── hand_follow_mode.py # 手部跟随
│   │   ├── pet_mode.py         # 桌宠模式
│   │   └── brightness_mode.py  # 亮度调节
│   │
│   ├── modules/                # 硬件模块
│   │   ├── vision/             # 视觉 (摄像头、手势、人脸)
│   │   ├── serial/             # 串口通信 (GPIO14/15)
│   │   └── speaker/            # 语音播报 (TTS预留)
│   │
│   ├── services/               # 服务层
│   │   ├── settings_service.py # 设置管理
│   │   ├── pet_service.py      # 宠物数据
│   │   ├── study_service.py    # 学习记录
│   │   └── schedule_service.py # 定时任务
│   │
│   └── utils/                  # 工具函数
│       ├── config_loader.py    # 配置加载
│       ├── kinematics.py       # 运动学计算
│       └── logger.py           # 日志
│
├── ui/                         # UI 界面
│   ├── main.py                 # 主窗口 (RobotWindow)
│   ├── mainwindow.ui           # Qt Designer 界面
│   ├── components/             # UI 组件
│   │   └── face.py             # 表情组件 (FaceWidget)
│   ├── utils/
│   │   └── brightness.py       # 屏幕亮度控制
│   ├── fonts/                  # 字体文件
│   └── icons/                  # 图标资源
│
├── run_ui.py                   # UI 启动入口 ⭐
├── run.py                      # 后端启动入口
├── requirements/               # 依赖文件
└── systemd/                    # 系统服务配置
```

---

## 🔧 硬件配置

### 树莓派 CM5 引脚

| 功能 | GPIO | 说明 |
|------|------|------|
| 串口 TX | GPIO14 | 发送数据到外部控制器 |
| 串口 RX | GPIO15 | 接收外部控制器数据 |
| 摄像头 | CSI | 官方摄像头模块 |
| 触摸屏 | DSI | 官方 7 寸触摸屏 |

### 串口配置

```yaml
# config/config.yaml
serial:
  port: "/dev/ttyAMA0"
  baudrate: 115200
```

---

## 🧪 模块测试

每个模块都支持独立测试：

```bash
# 激活虚拟环境
source .venv/bin/activate

# 测试串口协议
python -m smart_lamp.modules.serial.protocol

# 测试串口通信
python -m smart_lamp.modules.serial.serial_thread

# 测试屏幕亮度
python -m ui.utils.brightness

# 测试亮度调节模式
python -m smart_lamp.modes.brightness_mode

# 测试手部跟随模式
python -m smart_lamp.modes.hand_follow_mode

# 测试桌宠模式
python -m smart_lamp.modes.pet_mode
```

---

## ⚙️ 开机自启动

### 配置 systemd 服务

```bash
# 复制服务文件
sudo cp systemd/smart-lamp.service /etc/systemd/system/

# 编辑服务文件（修改路径和用户名）
sudo nano /etc/systemd/system/smart-lamp.service

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable smart-lamp
sudo systemctl start smart-lamp

# 查看状态
sudo systemctl status smart-lamp

# 查看日志
journalctl -u smart-lamp -f
```

### 服务文件示例

```ini
[Unit]
Description=Smart Lamp Control System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smart_lamp
Environment="PATH=/home/pi/smart_lamp/.venv/bin"
Environment="DISPLAY=:0"
ExecStart=/home/pi/smart_lamp/.venv/bin/python run_ui.py
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
```

---

## 📊 数据存储

用户数据自动保存到 `data/` 目录：

| 文件 | 内容 |
|------|------|
| `settings.json` | 音量、亮度、护眼设置等 |
| `pet_state.json` | 宠物名字、心情、亲密度 |
| `study_records.json` | 学习时长、番茄钟统计 |
| `reminders.json` | 提醒/闹钟列表 |

数据通过 `BaseStorage` 类管理，调用 `set()` 时自动持久化。

---

## 🛠️ 开发指南

### 添加新模式

1. 创建模式文件 `smart_lamp/modes/my_mode.py`:

```python
from .base_mode import BaseMode

class MyMode(BaseMode):
    MODE_NAME = "我的模式"
    
    def on_enter(self):
        self._print("进入我的模式")
    
    def on_exit(self):
        self._print("退出我的模式")
    
    def update(self, frame=None, voice_text=None) -> bool:
        # 主循环逻辑，frame 为摄像头帧
        return True  # 返回 False 退出模式

# 独立测试
if __name__ == "__main__":
    # 添加测试代码
    pass
```

2. 在 UI 中添加模式切换按钮

### 添加新服务

```python
from .base_storage import BaseStorage

class MyService:
    def __init__(self, data_dir="data"):
        self._storage = BaseStorage(
            file_path=f"{data_dir}/my_data.json",
            default_data={"key": "default_value"}
        )
    
    @property
    def key(self):
        return self._storage.get("key")
    
    def set_key(self, value):
        self._storage.set("key", value)  # 自动保存
```

---

## 🐛 故障排除

| 问题 | 解决方案 |
|------|----------|
| 摄像头打开失败 | `sudo usermod -a -G video $USER` 后重启 |
| 串口无权限 | `sudo usermod -a -G dialout $USER` 后重启 |
| UI 无法显示 | 确保设置 `DISPLAY=:0` 环境变量 |
| PyQt5 安装失败 | `sudo apt install python3-pyqt5` |
| 亮度控制无效 | 检查 `/sys/class/backlight/` 是否存在 |

---

## 📦 依赖列表

```
# 基础
numpy
PyYAML
pyserial

# UI
PyQt5>=5.15.0

# 视觉
opencv-python-headless
mediapipe

# 工具
loguru
```

---

## 📜 版本历史

### v3.0.0 (2026-02)
- 🎨 PyQt5 触摸屏 UI 集成
- 🔌 串口通信模块 (GPIO14/15)
- 📱 屏幕亮度控制
- 🗂️ 服务层数据持久化
- 🧹 移除舵机/语音唤醒模块

### v2.0.0 (2024-12)
- ✨ 三大交互模式
- 🗣️ 唤醒词+语音控制

### v1.0.0 (2024-12)
- 初始版本

---

## 📝 TODO

- [ ] 完善手势唤醒检测
- [ ] 学习模式专注检测
- [ ] 宠物互动动画
- [ ] TTS 语音播报

---

**Made with ❤️ for Raspberry Pi CM5**
