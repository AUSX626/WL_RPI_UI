"""
设置服务 - 管理所有用户设置

功能：
- 加载/保存用户设置
- 提供统一的设置访问接口
- 支持设置变更通知（回调）
- 支持设置验证

使用示例：
    settings = SettingsService(data_dir="data")
    
    # 获取设置
    volume = settings.volume
    brightness = settings.default_brightness
    
    # 修改设置
    settings.set("volume", 80)
    
    # 监听变更
    settings.on_change(lambda key, old, new: print(f"{key}: {old} -> {new}"))
"""
import threading
from dataclasses import dataclass, field, asdict, fields
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path

from .base_storage import BaseStorage


@dataclass
class Settings:
    """
    设置数据结构
    
    所有设置项都定义在这里，方便类型提示和默认值管理
    """
    
    # ===== 音频设置 =====
    volume: int = 70                    # 音量 0-100
    speech_rate: float = 1.0            # TTS 语速 0.5-2.0
    voice_name: str = "zh-CN-XiaoxiaoNeural"  # TTS 语音
    
    # ===== 亮度设置 =====
    default_brightness: float = 0.8     # 默认亮度 0.0-1.0
    auto_brightness: bool = False       # 自动亮度调节
    min_brightness: float = 0.1         # 最低亮度
    max_brightness: float = 1.0         # 最高亮度
    
    # ===== 护眼设置 =====
    eye_care_enabled: bool = True       # 护眼提醒开关
    eye_care_interval: int = 30         # 护眼提醒间隔（分钟）
    eye_care_duration: int = 5          # 建议休息时长（分钟）
    
    # ===== 学习/番茄钟设置 =====
    pomodoro_work: int = 25             # 番茄钟工作时长（分钟）
    pomodoro_short_break: int = 5       # 短休息时长（分钟）
    pomodoro_long_break: int = 15       # 长休息时长（分钟）
    pomodoro_rounds: int = 4            # 多少个番茄后长休息
    
    # ===== 睡眠设置 =====
    auto_sleep_enabled: bool = False    # 自动睡眠模式
    sleep_time: str = "22:00"           # 睡眠时间
    wake_time: str = "07:00"            # 唤醒时间
    sleep_brightness: float = 0.05      # 睡眠模式亮度
    sleep_dim_duration: int = 30        # 渐暗时长（分钟）
    
    # ===== 唤醒设置 =====
    wake_word: str = "宝莉"             # 唤醒词
    wake_sensitivity: float = 0.8       # 唤醒灵敏度 0.0-1.0
    listening_timeout: float = 10.0     # 监听超时（秒）
    
    # ===== 宠物设置 =====
    pet_name: str = "宝莉"              # 宠物名字
    pet_personality: str = "活泼"       # 性格类型
    pet_idle_action_interval: int = 60  # 闲置动作间隔（秒）
    
    # ===== 系统设置 =====
    language: str = "zh-CN"             # 语言
    debug_mode: bool = False            # 调试模式
    auto_update: bool = True            # 自动更新
    
    def to_dict(self) -> Dict[str, Any]:
        """转为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        """从字典创建"""
        # 只取有效字段
        valid_fields = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


class SettingsService:
    """
    设置服务
    
    职责：
    - 加载/保存设置到 JSON 文件
    - 提供类型安全的设置访问
    - 设置变更通知
    - 设置验证
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化设置服务
        
        Args:
            data_dir: 数据目录
        """
        self._storage = BaseStorage(
            file_path=Path(data_dir) / "settings.json",
            default_data=Settings().to_dict()
        )
        self._settings = Settings.from_dict(self._storage.data)
        self._callbacks: List[Callable[[str, Any, Any], None]] = []
        self._lock = threading.RLock()
    
    # ========== 通用访问方法 ==========
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取设置项"""
        return getattr(self._settings, key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """
        设置单个配置项
        
        Args:
            key: 配置键名
            value: 配置值
            
        Returns:
            是否成功
        """
        if not hasattr(self._settings, key):
            print(f"[Settings] 未知设置项: {key}")
            return False
        
        # 验证值
        if not self._validate(key, value):
            return False
        
        with self._lock:
            old_value = getattr(self._settings, key)
            if old_value == value:
                return True  # 值未变化
            
            # 更新内存
            setattr(self._settings, key, value)
            
            # 保存到文件
            self._storage.set(key, value)
            
            # 触发回调
            self._notify_change(key, old_value, value)
        
        return True
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有设置"""
        return self._settings.to_dict()
    
    def update(self, settings: Dict[str, Any]) -> bool:
        """
        批量更新设置
        
        Args:
            settings: 设置字典
            
        Returns:
            是否全部成功
        """
        success = True
        for key, value in settings.items():
            if not self.set(key, value):
                success = False
        return success
    
    def reset(self, key: Optional[str] = None):
        """
        重置设置
        
        Args:
            key: 要重置的键，None 表示全部重置
        """
        default = Settings()
        
        if key:
            if hasattr(default, key):
                self.set(key, getattr(default, key))
        else:
            # 全部重置
            with self._lock:
                self._settings = default
                self._storage.update(default.to_dict())
    
    # ========== 变更通知 ==========
    
    def on_change(self, callback: Callable[[str, Any, Any], None]):
        """
        注册设置变更回调
        
        Args:
            callback: 回调函数 callback(key, old_value, new_value)
        """
        self._callbacks.append(callback)
    
    def _notify_change(self, key: str, old_value: Any, new_value: Any):
        """触发变更回调"""
        for callback in self._callbacks:
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                print(f"[Settings] 回调执行失败: {e}")
    
    # ========== 值验证 ==========
    
    def _validate(self, key: str, value: Any) -> bool:
        """验证设置值"""
        validators = {
            'volume': lambda v: isinstance(v, int) and 0 <= v <= 100,
            'speech_rate': lambda v: isinstance(v, (int, float)) and 0.5 <= v <= 2.0,
            'default_brightness': lambda v: isinstance(v, (int, float)) and 0.0 <= v <= 1.0,
            'min_brightness': lambda v: isinstance(v, (int, float)) and 0.0 <= v <= 1.0,
            'max_brightness': lambda v: isinstance(v, (int, float)) and 0.0 <= v <= 1.0,
            'eye_care_interval': lambda v: isinstance(v, int) and v > 0,
            'pomodoro_work': lambda v: isinstance(v, int) and 1 <= v <= 120,
            'pomodoro_short_break': lambda v: isinstance(v, int) and 1 <= v <= 60,
            'pomodoro_long_break': lambda v: isinstance(v, int) and 1 <= v <= 60,
            'listening_timeout': lambda v: isinstance(v, (int, float)) and v > 0,
            'wake_sensitivity': lambda v: isinstance(v, (int, float)) and 0.0 <= v <= 1.0,
        }
        
        if key in validators:
            if not validators[key](value):
                print(f"[Settings] 值验证失败: {key}={value}")
                return False
        
        return True
    
    # ========== 便捷属性（常用设置直接访问） ==========
    
    @property
    def volume(self) -> int:
        return self._settings.volume
    
    @property
    def speech_rate(self) -> float:
        return self._settings.speech_rate
    
    @property
    def default_brightness(self) -> float:
        return self._settings.default_brightness
    
    @property
    def eye_care_enabled(self) -> bool:
        return self._settings.eye_care_enabled
    
    @property
    def eye_care_interval(self) -> int:
        return self._settings.eye_care_interval
    
    @property
    def pomodoro_work(self) -> int:
        return self._settings.pomodoro_work
    
    @property
    def pomodoro_short_break(self) -> int:
        return self._settings.pomodoro_short_break
    
    @property
    def wake_word(self) -> str:
        return self._settings.wake_word
    
    @property
    def listening_timeout(self) -> float:
        return self._settings.listening_timeout
    
    @property
    def pet_name(self) -> str:
        return self._settings.pet_name
    
    @property
    def debug_mode(self) -> bool:
        return self._settings.debug_mode
