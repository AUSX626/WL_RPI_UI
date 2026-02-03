# UI-main 融合方案

> 本文档说明如何将 `UI-main` 文件夹中的 PyQt5 界面代码整合到主项目中。

---

## 📋 现状分析

### 主项目结构 (`bubble_wheel_sys/`)
```
bubble_wheel_sys/
├── run.py              # 主入口（后端服务）
├── smart_lamp/         # 核心业务逻辑
├── ui/                 # UI 模块（目前为空）
├── config/             # 配置文件
├── data/               # 数据文件
└── ...
```

### UI-main 结构
```
UI-main/
├── main.py             # UI 主程序入口
├── face.py             # 眼睛动画组件
├── mainwindow.ui       # Qt Designer UI 文件
├── fonts/              # 字体资源
├── icons/              # 图标资源
└── SERVICE/            # ⚠️ 后端服务的完整副本
    ├── smart_lamp/     # 与主项目 smart_lamp/ 重复
    ├── config/
    ├── data/
    └── ...
```

### 关键发现

1. **SERVICE 是重复代码**  
   `UI-main/SERVICE/` 包含了一套完整的后端代码，和主项目根目录下的 `smart_lamp/` 几乎完全一致。这是为了让 UI 能够独立运行而复制的。

2. **UI 依赖后端服务**  
   `main.py` 中导入了：
   ```python
   from SERVICE.smart_lamp.services.service_manager import ServiceManager
   from SERVICE.smart_lamp.services.command_service import CommandServiceIntegration
   ```

3. **主项目 ui/ 目录为空**  
   主项目预留了 `ui/` 目录，但尚未实现。

---

## 🎯 融合目标

1. 将 UI 代码移入主项目的 `ui/` 目录
2. **删除重复的 SERVICE 副本**，让 UI 直接使用主项目的 `smart_lamp/` 模块
3. 统一入口，支持：
   - `python run.py` — 启动后端服务
   - `python run_ui.py` — 启动 UI 界面
   - 或两者一起启动

---

## 🔧 融合步骤

### 第一阶段：移动 UI 文件

| 原路径 | 目标路径 |
|--------|----------|
| `UI-main/main.py` | `ui/main.py` |
| `UI-main/face.py` | `ui/components/face.py` |
| `UI-main/mainwindow.ui` | `ui/mainwindow.ui` |
| `UI-main/fonts/` | `ui/fonts/` |
| `UI-main/icons/` | `ui/icons/` |

### 第二阶段：修改导入路径

**原来的导入 (UI-main/main.py):**
```python
from face import FaceWidget
from SERVICE.smart_lamp.services.service_manager import ServiceManager
from SERVICE.smart_lamp.services.command_service import CommandServiceIntegration
from SERVICE.smart_lamp.utils import setup_logger
```

**修改后 (ui/main.py):**
```python
from ui.components.face import FaceWidget
from smart_lamp.services.service_manager import ServiceManager
from smart_lamp.services.command_service import CommandServiceIntegration
from smart_lamp.utils import setup_logger
```

### 第三阶段：更新资源路径

`main.py` 中使用 `resource_path()` 函数定位资源文件，需要调整基础路径：

```python
# 修改前
def resource_path(relative_path):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# 修改后（指向 ui/ 目录）
def resource_path(relative_path):
    ui_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(ui_dir, relative_path)
```

数据目录也需要调整：
```python
# 修改前
services_data_dir = resource_path(os.path.join("SERVICE", "data"))

# 修改后（使用项目根目录的 data/）
services_data_dir = os.path.join(PROJECT_ROOT, "data")
```

### 第四阶段：创建 UI 启动入口

更新 `run_ui.py`：

```python
#!/usr/bin/env python3
"""
智能台灯 - UI 启动入口
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtWidgets import QApplication
from ui.main import RobotWindow

def main():
    app = QApplication(sys.argv)
    window = RobotWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

### 第五阶段：清理

1. **删除 `UI-main/SERVICE/` 目录**（已被主项目替代）
2. **可选**：删除整个 `UI-main/` 目录（所有有用文件已移至 `ui/`）
3. 更新 `.gitignore` 如有需要

---

## 📁 融合后的目录结构

```
bubble_wheel_sys/
├── run.py              # 后端主入口
├── run_ui.py           # UI 主入口
├── smart_lamp/         # 核心业务逻辑（唯一）
├── ui/                 # UI 模块
│   ├── __init__.py
│   ├── main.py         # UI 主窗口
│   ├── main_window.py  # (可合并或保留)
│   ├── mainwindow.ui   # Qt Designer 文件
│   ├── components/
│   │   ├── __init__.py
│   │   └── face.py     # 眼睛动画组件
│   ├── pages/
│   │   └── __init__.py
│   ├── fonts/          # 字体资源
│   └── icons/          # 图标资源
├── config/
├── data/
└── ...
```

---

## ⚠️ 注意事项

### 1. PyQt5 依赖
确保 `requirements.txt` 包含：
```
PyQt5>=5.15.0
```

### 2. 数据目录统一
融合后，UI 和后端共用同一个 `data/` 目录，需要确保：
- 两者不会同时写入同一文件造成冲突
- 可考虑使用文件锁或数据库

### 3. 配置文件统一
同理，`config/config.yaml` 也需要统一，UI 相关配置可以添加一个 `ui:` 节点：
```yaml
ui:
  fullscreen: true
  show_debug: false
```

### 4. 进程通信（如需分离运行）
如果 UI 和后端需要作为独立进程运行，可以通过以下方式通信：
- HTTP API（项目已有 `api/server.py`）
- Unix Socket
- 共享文件 + 文件监听

---

## 📝 执行清单

- [ ] 移动 `UI-main/main.py` → `ui/main.py`
- [ ] 移动 `UI-main/face.py` → `ui/components/face.py`
- [ ] 移动 `UI-main/mainwindow.ui` → `ui/mainwindow.ui`
- [ ] 复制 `UI-main/fonts/` → `ui/fonts/`
- [ ] 复制 `UI-main/icons/` → `ui/icons/`
- [ ] 修改 `ui/main.py` 中的导入路径
- [ ] 修改 `ui/main.py` 中的资源路径
- [ ] 更新 `run_ui.py` 启动脚本
- [ ] 添加 PyQt5 到 `requirements.txt`
- [ ] 测试 UI 启动
- [ ] 删除 `UI-main/` 目录（确认无误后）

---

## 🚀 验证命令

融合完成后，使用以下命令验证：

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装 PyQt5（如未安装）
pip install PyQt5

# 启动 UI
python run_ui.py

# 或使用 make
make run-ui
```
