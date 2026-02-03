"""
服务层 - 业务逻辑和数据管理

服务层的职责：
1. 管理业务数据（设置、宠物状态、学习记录等）
2. 提供统一的数据访问接口
3. 数据持久化（JSON/SQLite）
4. 不依赖具体的交互方式（语音/UI都可以调用）

架构位置：
    用户交互（语音/UI）
           ↓
       modes/ 模式层
           ↓
    → services/ 服务层 ←  （你在这里）
           ↓
      modules/ 硬件层
"""

from .service_manager import ServiceManager
from .settings_service import SettingsService, Settings
from .pet_service import PetService, PetState
from .schedule_service import ScheduleService, Reminder
from .study_service import StudyService, StudySession
from .command_service import CommandService, Command, CommandResult, InputSource, ControlMode

__all__ = [
    'ServiceManager',
    'SettingsService', 'Settings',
    'PetService', 'PetState',
    'ScheduleService', 'Reminder',
    'StudyService', 'StudySession',
    'CommandService', 'Command', 'CommandResult', 'InputSource', 'ControlMode',
]
