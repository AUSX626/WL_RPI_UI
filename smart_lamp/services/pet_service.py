"""
宠物状态服务 - 管理桌宠的"灵魂"

功能：
- 情绪值管理（开心度、精力值、亲密度）
- 心情计算
- 互动效果
- 时间流逝影响
- 状态持久化

使用示例：
    pet = PetService(data_dir="data")
    
    # 获取心情
    mood = pet.current_mood  # "happy", "sleepy", "sad" 等
    
    # 互动
    pet.interact("pet")  # 摸头
    pet.interact("play") # 玩耍
    
    # 时间流逝
    pet.tick(minutes=5)
"""
import time
import random
import threading
from dataclasses import dataclass, asdict, fields
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path
from enum import Enum

from .base_storage import BaseStorage, TimestampMixin


class Mood(str, Enum):
    """心情枚举"""
    EXCITED = "excited"      # 兴奋
    HAPPY = "happy"          # 开心
    NORMAL = "normal"        # 普通
    BORED = "bored"          # 无聊
    SAD = "sad"              # 难过
    SLEEPY = "sleepy"        # 困倦
    ANGRY = "angry"          # 生气


@dataclass
class PetState:
    """
    宠物状态数据结构
    """
    # ===== 基础属性 =====
    name: str = "宝莉"
    
    # ===== 情绪值 (0-100) =====
    happiness: int = 50        # 开心度
    energy: int = 80           # 精力值
    affection: int = 30        # 亲密度（好感度）
    satiety: int = 70          # 饱腹感（可选，如果有喂食功能）
    
    # ===== 性格特征 (0.0-1.0) =====
    trait_active: float = 0.7      # 活泼程度
    trait_clingy: float = 0.5      # 粘人程度
    trait_sleepy: float = 0.3      # 贪睡程度
    trait_curious: float = 0.6     # 好奇程度
    
    # ===== 统计数据 =====
    total_interactions: int = 0    # 总互动次数
    total_play_time: int = 0       # 总玩耍时长（秒）
    last_interaction: str = ""     # 最后互动时间
    created_at: str = ""           # 创建时间
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PetState':
        valid_fields = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


class PetService(TimestampMixin):
    """
    宠物状态服务
    
    管理宠物的情绪、互动、时间流逝等
    """
    
    # 互动效果配置
    INTERACTION_EFFECTS = {
        "pet": {"happiness": 5, "affection": 2, "energy": -1},       # 摸头
        "play": {"happiness": 10, "affection": 3, "energy": -8},     # 玩耍
        "talk": {"happiness": 3, "affection": 1, "energy": -1},      # 聊天
        "feed": {"happiness": 5, "satiety": 20, "energy": 5},        # 喂食
        "praise": {"happiness": 8, "affection": 4, "energy": 0},     # 表扬
        "scold": {"happiness": -15, "affection": -5, "energy": 0},   # 责骂
        "ignore": {"happiness": -3, "affection": -2, "energy": 1},   # 忽视
    }
    
    # 心情对应的动作
    MOOD_ACTIONS = {
        Mood.EXCITED: ["jump", "spin", "wag"],
        Mood.HAPPY: ["nod", "bounce", "smile"],
        Mood.NORMAL: ["idle", "look_around"],
        Mood.BORED: ["yawn", "sigh", "fidget"],
        Mood.SAD: ["droop", "whimper"],
        Mood.SLEEPY: ["yawn", "nod_off", "stretch"],
        Mood.ANGRY: ["shake", "huff"],
    }
    
    def __init__(self, data_dir: str = "data"):
        """初始化宠物服务"""
        default_state = PetState(created_at=self.now_str())
        
        self._storage = BaseStorage(
            file_path=Path(data_dir) / "pet_state.json",
            default_data=default_state.to_dict()
        )
        self._state = PetState.from_dict(self._storage.data)
        self._callbacks: List[Callable[[str, Any], None]] = []
        self._lock = threading.RLock()
        
        # 上次 tick 时间
        self._last_tick_time = time.time()
    
    # ========== 状态访问 ==========
    
    @property
    def state(self) -> PetState:
        """获取宠物状态"""
        return self._state
    
    @property
    def happiness(self) -> int:
        return self._state.happiness
    
    @property
    def energy(self) -> int:
        return self._state.energy
    
    @property
    def affection(self) -> int:
        return self._state.affection
    
    @property
    def name(self) -> str:
        return self._state.name
    
    @property
    def current_mood(self) -> Mood:
        """
        根据属性计算当前心情
        
        优先级：sleepy > sad > bored > excited > happy > normal
        """
        h = self._state.happiness
        e = self._state.energy
        a = self._state.affection
        
        # 精力不足 -> 困倦
        if e < 20:
            return Mood.SLEEPY
        
        # 开心度很低 -> 难过
        if h < 25:
            return Mood.SAD
        
        # 开心度较低且亲密度低 -> 无聊
        if h < 40 and a < 40:
            return Mood.BORED
        
        # 开心度很高 -> 兴奋
        if h > 85 and e > 60:
            return Mood.EXCITED
        
        # 开心度较高 -> 开心
        if h > 55:
            return Mood.HAPPY
        
        return Mood.NORMAL
    
    def get_mood_action(self) -> str:
        """获取当前心情对应的随机动作"""
        mood = self.current_mood
        actions = self.MOOD_ACTIONS.get(mood, ["idle"])
        return random.choice(actions)
    
    def get_status_dict(self) -> Dict[str, Any]:
        """获取状态字典（用于 API）"""
        return {
            "name": self._state.name,
            "mood": self.current_mood.value,
            "happiness": self._state.happiness,
            "energy": self._state.energy,
            "affection": self._state.affection,
            "total_interactions": self._state.total_interactions,
            "last_interaction": self._state.last_interaction,
        }
    
    # ========== 互动 ==========
    
    def interact(self, action: str) -> Dict[str, Any]:
        """
        与宠物互动
        
        Args:
            action: 互动类型 ("pet", "play", "talk", "feed", "praise", etc.)
            
        Returns:
            互动结果 {"success": bool, "effects": {...}, "mood": str, "message": str}
        """
        effects = self.INTERACTION_EFFECTS.get(action)
        
        if not effects:
            return {
                "success": False,
                "message": f"未知的互动类型: {action}"
            }
        
        with self._lock:
            # 应用效果
            applied = {}
            for attr, delta in effects.items():
                if hasattr(self._state, attr):
                    old_val = getattr(self._state, attr)
                    new_val = max(0, min(100, old_val + delta))
                    setattr(self._state, attr, new_val)
                    applied[attr] = {"old": old_val, "new": new_val, "delta": delta}
            
            # 更新统计
            self._state.total_interactions += 1
            self._state.last_interaction = self.now_str()
            
            # 保存
            self._save()
            
            # 通知
            self._notify("interact", {"action": action, "effects": applied})
        
        # 生成回复消息
        mood = self.current_mood
        message = self._generate_response(action, mood)
        
        return {
            "success": True,
            "action": action,
            "effects": applied,
            "mood": mood.value,
            "message": message,
        }
    
    def _generate_response(self, action: str, mood: Mood) -> str:
        """生成互动回复"""
        responses = {
            ("pet", Mood.HAPPY): ["嘿嘿，好舒服~", "摸摸头，开心！", "喵~"],
            ("pet", Mood.SLEEPY): ["嗯...困了...", "让我再睡会儿..."],
            ("play", Mood.EXCITED): ["太好玩了！再来！", "耶！我最喜欢玩了！"],
            ("play", Mood.SLEEPY): ["好累...让我休息会儿吧", "玩不动了..."],
            ("talk", Mood.HAPPY): ["和你聊天真开心！", "嗯嗯，我在听呢！"],
            ("praise", Mood.HAPPY): ["嘿嘿，谢谢夸奖！", "我会继续努力的！"],
            ("feed", Mood.HAPPY): ["好吃！谢谢主人！", "吃饱了，好满足~"],
        }
        
        key = (action, mood)
        if key in responses:
            return random.choice(responses[key])
        
        # 默认回复
        default = {
            Mood.HAPPY: "开心~",
            Mood.EXCITED: "太棒了！",
            Mood.NORMAL: "嗯。",
            Mood.BORED: "好无聊啊...",
            Mood.SAD: "唔...",
            Mood.SLEEPY: "好困...",
        }
        return default.get(mood, "...")
    
    # ========== 时间流逝 ==========
    
    def tick(self, minutes: float = None):
        """
        时间流逝，属性自然变化
        
        Args:
            minutes: 流逝的分钟数，None 则自动计算
        """
        now = time.time()
        
        if minutes is None:
            elapsed_seconds = now - self._last_tick_time
            minutes = elapsed_seconds / 60.0
        
        self._last_tick_time = now
        
        if minutes < 0.1:
            return  # 忽略太短的间隔
        
        with self._lock:
            # 精力随时间恢复（休息时）
            self._state.energy = min(100, self._state.energy + int(minutes * 0.5))
            
            # 开心度缓慢下降（需要互动维持）
            self._state.happiness = max(0, self._state.happiness - int(minutes * 0.1))
            
            # 亲密度非常缓慢下降
            if minutes > 60:  # 超过1小时没互动
                self._state.affection = max(0, self._state.affection - 1)
            
            # 饱腹感下降
            self._state.satiety = max(0, self._state.satiety - int(minutes * 0.2))
            
            self._save()
    
    # ========== 设置 ==========
    
    def set_name(self, name: str):
        """设置宠物名字"""
        with self._lock:
            self._state.name = name
            self._save()
            self._notify("name_changed", name)
    
    def set_trait(self, trait: str, value: float):
        """设置性格特征"""
        trait_key = f"trait_{trait}"
        if hasattr(self._state, trait_key):
            with self._lock:
                setattr(self._state, trait_key, max(0.0, min(1.0, value)))
                self._save()
    
    # ========== 内部方法 ==========
    
    def _save(self):
        """保存状态"""
        self._storage.update(self._state.to_dict())
    
    def _notify(self, event: str, data: Any):
        """触发回调"""
        for callback in self._callbacks:
            try:
                callback(event, data)
            except Exception as e:
                print(f"[Pet] 回调执行失败: {e}")
    
    def on_event(self, callback: Callable[[str, Any], None]):
        """注册事件回调"""
        self._callbacks.append(callback)
