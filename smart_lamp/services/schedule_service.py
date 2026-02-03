"""
日程/提醒服务 - 管理定时任务和提醒

功能：
- 添加/删除/查询提醒
- 一次性提醒和重复提醒
- 提醒触发检测
- 持久化存储

使用示例：
    schedule = ScheduleService(data_dir="data")
    
    # 添加提醒
    schedule.add_reminder("喝水", minutes=30)
    schedule.add_reminder("吃药", time="08:00", repeat="daily")
    
    # 检查触发
    triggered = schedule.check_triggers()
    for reminder in triggered:
        print(f"提醒: {reminder.content}")
"""
import time
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path
from enum import Enum
import uuid

from .base_storage import BaseStorage, TimestampMixin


class RepeatType(str, Enum):
    """重复类型"""
    NONE = "none"           # 一次性
    DAILY = "daily"         # 每天
    WEEKLY = "weekly"       # 每周
    HOURLY = "hourly"       # 每小时
    CUSTOM = "custom"       # 自定义间隔（分钟）


@dataclass
class Reminder:
    """提醒数据结构"""
    id: str = ""                        # 唯一ID
    content: str = ""                   # 提醒内容
    trigger_time: str = ""              # 触发时间 (格式: "YYYY-MM-DD HH:MM:SS" 或 "HH:MM")
    repeat: str = "none"                # 重复类型
    repeat_interval: int = 0            # 自定义重复间隔（分钟）
    enabled: bool = True                # 是否启用
    created_at: str = ""                # 创建时间
    last_triggered: str = ""            # 上次触发时间
    trigger_count: int = 0              # 触发次数
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Reminder':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ScheduleService(TimestampMixin):
    """
    日程/提醒服务
    """
    
    def __init__(self, data_dir: str = "data"):
        """初始化日程服务"""
        self._storage = BaseStorage(
            file_path=Path(data_dir) / "reminders.json",
            default_data={"reminders": []}
        )
        self._reminders: List[Reminder] = []
        self._load_reminders()
        
        self._callbacks: List[Callable[[Reminder], None]] = []
        self._lock = threading.RLock()
        
        # 检查线程
        self._running = False
        self._check_thread: Optional[threading.Thread] = None
    
    def _load_reminders(self):
        """加载提醒列表"""
        data = self._storage.get("reminders", [])
        self._reminders = [Reminder.from_dict(r) for r in data]
    
    def _save_reminders(self):
        """保存提醒列表"""
        self._storage.set("reminders", [r.to_dict() for r in self._reminders])
    
    # ========== 提醒管理 ==========
    
    def add_reminder(
        self,
        content: str,
        time: str = None,
        minutes: int = None,
        repeat: str = "none",
        repeat_interval: int = 0
    ) -> Reminder:
        """
        添加提醒
        
        Args:
            content: 提醒内容
            time: 触发时间 (格式: "HH:MM" 或 "YYYY-MM-DD HH:MM")
            minutes: 多少分钟后触发
            repeat: 重复类型
            repeat_interval: 自定义重复间隔（分钟）
            
        Returns:
            创建的提醒对象
        """
        # 计算触发时间
        if minutes:
            trigger_dt = datetime.now() + timedelta(minutes=minutes)
            trigger_time = trigger_dt.strftime("%Y-%m-%d %H:%M:%S")
        elif time:
            # 如果只有时间（HH:MM），添加今天的日期
            if len(time) <= 5:
                today = datetime.now().strftime("%Y-%m-%d")
                trigger_time = f"{today} {time}:00"
                # 如果时间已过，设为明天
                if datetime.strptime(trigger_time, "%Y-%m-%d %H:%M:%S") < datetime.now():
                    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                    trigger_time = f"{tomorrow} {time}:00"
            else:
                trigger_time = time
        else:
            raise ValueError("必须指定 time 或 minutes")
        
        reminder = Reminder(
            id=str(uuid.uuid4())[:8],
            content=content,
            trigger_time=trigger_time,
            repeat=repeat,
            repeat_interval=repeat_interval,
            enabled=True,
            created_at=self.now_str(),
        )
        
        with self._lock:
            self._reminders.append(reminder)
            self._save_reminders()
        
        print(f"[Schedule] 添加提醒: {content} @ {trigger_time}")
        return reminder
    
    def remove_reminder(self, reminder_id: str) -> bool:
        """删除提醒"""
        with self._lock:
            for i, r in enumerate(self._reminders):
                if r.id == reminder_id:
                    del self._reminders[i]
                    self._save_reminders()
                    print(f"[Schedule] 删除提醒: {reminder_id}")
                    return True
        return False
    
    def get_reminder(self, reminder_id: str) -> Optional[Reminder]:
        """获取提醒"""
        for r in self._reminders:
            if r.id == reminder_id:
                return r
        return None
    
    def get_all_reminders(self) -> List[Reminder]:
        """获取所有提醒"""
        return self._reminders.copy()
    
    def get_active_reminders(self) -> List[Reminder]:
        """获取所有启用的提醒"""
        return [r for r in self._reminders if r.enabled]
    
    def enable_reminder(self, reminder_id: str, enabled: bool = True) -> bool:
        """启用/禁用提醒"""
        with self._lock:
            for r in self._reminders:
                if r.id == reminder_id:
                    r.enabled = enabled
                    self._save_reminders()
                    return True
        return False
    
    def clear_all(self):
        """清空所有提醒"""
        with self._lock:
            self._reminders.clear()
            self._save_reminders()
    
    # ========== 触发检测 ==========
    
    def check_triggers(self) -> List[Reminder]:
        """
        检查哪些提醒应该触发
        
        Returns:
            需要触发的提醒列表
        """
        now = datetime.now()
        triggered = []
        
        with self._lock:
            for reminder in self._reminders:
                if not reminder.enabled:
                    continue
                
                trigger_dt = self.parse_datetime(reminder.trigger_time)
                if trigger_dt is None:
                    continue
                
                # 检查是否到达触发时间
                if now >= trigger_dt:
                    # 检查是否已经触发过（防止重复触发）
                    if reminder.last_triggered:
                        last_triggered = self.parse_datetime(reminder.last_triggered)
                        # 如果上次触发在1分钟内，跳过
                        if last_triggered and (now - last_triggered).seconds < 60:
                            continue
                    
                    triggered.append(reminder)
                    
                    # 更新触发状态
                    reminder.last_triggered = self.now_str()
                    reminder.trigger_count += 1
                    
                    # 处理重复
                    self._handle_repeat(reminder, now)
            
            if triggered:
                self._save_reminders()
        
        return triggered
    
    def _handle_repeat(self, reminder: Reminder, now: datetime):
        """处理重复提醒"""
        repeat = RepeatType(reminder.repeat)
        
        if repeat == RepeatType.NONE:
            # 一次性提醒，触发后禁用
            reminder.enabled = False
        
        elif repeat == RepeatType.DAILY:
            # 每天，设置明天同一时间
            old_dt = self.parse_datetime(reminder.trigger_time)
            if old_dt:
                new_dt = old_dt + timedelta(days=1)
                reminder.trigger_time = new_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        elif repeat == RepeatType.WEEKLY:
            # 每周
            old_dt = self.parse_datetime(reminder.trigger_time)
            if old_dt:
                new_dt = old_dt + timedelta(weeks=1)
                reminder.trigger_time = new_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        elif repeat == RepeatType.HOURLY:
            # 每小时
            new_dt = now + timedelta(hours=1)
            reminder.trigger_time = new_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        elif repeat == RepeatType.CUSTOM:
            # 自定义间隔
            if reminder.repeat_interval > 0:
                new_dt = now + timedelta(minutes=reminder.repeat_interval)
                reminder.trigger_time = new_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # ========== 后台检查 ==========
    
    def start_background_check(self, interval: float = 30.0):
        """启动后台检查线程"""
        if self._running:
            return
        
        self._running = True
        self._check_thread = threading.Thread(
            target=self._background_loop,
            args=(interval,),
            daemon=True,
            name="ScheduleCheck"
        )
        self._check_thread.start()
        print(f"[Schedule] 后台检查已启动，间隔 {interval} 秒")
    
    def stop_background_check(self):
        """停止后台检查"""
        self._running = False
        if self._check_thread and self._check_thread.is_alive():
            self._check_thread.join(timeout=2)
    
    def _background_loop(self, interval: float):
        """后台检查循环"""
        while self._running:
            triggered = self.check_triggers()
            
            for reminder in triggered:
                # 触发回调
                for callback in self._callbacks:
                    try:
                        callback(reminder)
                    except Exception as e:
                        print(f"[Schedule] 回调执行失败: {e}")
            
            time.sleep(interval)
    
    def on_trigger(self, callback: Callable[[Reminder], None]):
        """注册触发回调"""
        self._callbacks.append(callback)
