"""
学习统计服务 - 记录和统计学习数据

功能：
- 记录学习时长
- 统计日/周/月数据
- 番茄钟统计
- 专注度分析

使用示例：
    study = StudyService(data_dir="data")
    
    # 开始学习
    session_id = study.start_session()
    
    # 结束学习
    study.end_session(session_id)
    
    # 查看统计
    today = study.get_today_stats()
    print(f"今日学习: {today['total_minutes']} 分钟")
"""
import time
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path
import uuid

from .base_storage import BaseStorage, TimestampMixin


@dataclass
class StudySession:
    """学习会话"""
    id: str = ""
    start_time: str = ""
    end_time: str = ""
    duration_minutes: float = 0.0
    mode: str = "study"              # "study", "pomodoro"
    completed: bool = False          # 是否正常完成
    pomodoro_count: int = 0          # 完成的番茄数
    distraction_count: int = 0       # 分心次数
    notes: str = ""                  # 备注
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StudySession':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class StudyService(TimestampMixin):
    """
    学习统计服务
    """
    
    def __init__(self, data_dir: str = "data"):
        """初始化学习服务"""
        self._storage = BaseStorage(
            file_path=Path(data_dir) / "study_records.json",
            default_data={
                "sessions": [],
                "daily_goals": {},    # 每日目标 {"2024-01-01": 120}
                "total_stats": {
                    "total_sessions": 0,
                    "total_minutes": 0,
                    "total_pomodoros": 0,
                    "longest_session": 0,
                    "current_streak": 0,   # 连续学习天数
                    "best_streak": 0,
                }
            }
        )
        
        self._sessions: List[StudySession] = []
        self._load_sessions()
        
        self._lock = threading.RLock()
        
        # 当前活跃的学习会话
        self._active_session: Optional[StudySession] = None
        self._session_start_time: Optional[float] = None
    
    def _load_sessions(self):
        """加载学习记录"""
        data = self._storage.get("sessions", [])
        self._sessions = [StudySession.from_dict(s) for s in data]
    
    def _save_sessions(self):
        """保存学习记录"""
        self._storage.set("sessions", [s.to_dict() for s in self._sessions])
    
    # ========== 学习会话管理 ==========
    
    def start_session(self, mode: str = "study") -> str:
        """
        开始学习会话
        
        Args:
            mode: 学习模式 ("study", "pomodoro")
            
        Returns:
            会话ID
        """
        if self._active_session:
            # 自动结束上一个会话
            self.end_session()
        
        session_id = str(uuid.uuid4())[:8]
        
        self._active_session = StudySession(
            id=session_id,
            start_time=self.now_str(),
            mode=mode,
        )
        self._session_start_time = time.time()
        
        print(f"[Study] 开始学习会话: {session_id} ({mode})")
        return session_id
    
    def end_session(self, completed: bool = True, notes: str = "") -> Optional[StudySession]:
        """
        结束学习会话
        
        Args:
            completed: 是否正常完成
            notes: 备注
            
        Returns:
            结束的会话对象
        """
        if not self._active_session:
            return None
        
        session = self._active_session
        
        # 计算时长
        if self._session_start_time:
            duration_seconds = time.time() - self._session_start_time
            session.duration_minutes = round(duration_seconds / 60, 1)
        
        session.end_time = self.now_str()
        session.completed = completed
        session.notes = notes
        
        # 保存
        with self._lock:
            self._sessions.append(session)
            self._save_sessions()
            self._update_total_stats(session)
        
        print(f"[Study] 结束学习会话: {session.id}, 时长: {session.duration_minutes} 分钟")
        
        # 清理
        self._active_session = None
        self._session_start_time = None
        
        return session
    
    def add_pomodoro(self):
        """增加番茄计数"""
        if self._active_session:
            self._active_session.pomodoro_count += 1
    
    def add_distraction(self):
        """增加分心计数"""
        if self._active_session:
            self._active_session.distraction_count += 1
    
    def get_current_duration(self) -> float:
        """获取当前会话时长（分钟）"""
        if self._session_start_time:
            return (time.time() - self._session_start_time) / 60
        return 0.0
    
    @property
    def is_studying(self) -> bool:
        """是否正在学习"""
        return self._active_session is not None
    
    @property
    def active_session(self) -> Optional[StudySession]:
        """当前活跃会话"""
        return self._active_session
    
    # ========== 统计查询 ==========
    
    def get_today_stats(self) -> Dict[str, Any]:
        """获取今日统计"""
        today = self.today_str()
        return self._get_date_stats(today)
    
    def get_week_stats(self) -> Dict[str, Any]:
        """获取本周统计"""
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        
        total_minutes = 0
        total_sessions = 0
        total_pomodoros = 0
        daily_data = {}
        
        for i in range(7):
            date = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
            day_stats = self._get_date_stats(date)
            daily_data[date] = day_stats
            total_minutes += day_stats["total_minutes"]
            total_sessions += day_stats["session_count"]
            total_pomodoros += day_stats["pomodoro_count"]
        
        return {
            "total_minutes": total_minutes,
            "total_sessions": total_sessions,
            "total_pomodoros": total_pomodoros,
            "daily_data": daily_data,
            "average_minutes": total_minutes / 7,
        }
    
    def get_month_stats(self) -> Dict[str, Any]:
        """获取本月统计"""
        today = datetime.now()
        month_start = today.replace(day=1)
        days_in_month = (month_start.replace(month=month_start.month % 12 + 1, day=1) - timedelta(days=1)).day
        
        total_minutes = 0
        total_sessions = 0
        study_days = 0
        
        for i in range(days_in_month):
            date = (month_start + timedelta(days=i)).strftime("%Y-%m-%d")
            if datetime.strptime(date, "%Y-%m-%d") > today:
                break
            day_stats = self._get_date_stats(date)
            total_minutes += day_stats["total_minutes"]
            total_sessions += day_stats["session_count"]
            if day_stats["total_minutes"] > 0:
                study_days += 1
        
        return {
            "total_minutes": total_minutes,
            "total_sessions": total_sessions,
            "study_days": study_days,
            "average_minutes": total_minutes / max(study_days, 1),
        }
    
    def _get_date_stats(self, date: str) -> Dict[str, Any]:
        """获取指定日期的统计"""
        sessions = [s for s in self._sessions if s.start_time.startswith(date)]
        
        total_minutes = sum(s.duration_minutes for s in sessions)
        pomodoro_count = sum(s.pomodoro_count for s in sessions)
        
        return {
            "date": date,
            "total_minutes": total_minutes,
            "session_count": len(sessions),
            "pomodoro_count": pomodoro_count,
            "completed_count": len([s for s in sessions if s.completed]),
        }
    
    def get_total_stats(self) -> Dict[str, Any]:
        """获取总统计"""
        return self._storage.get("total_stats", {})
    
    def _update_total_stats(self, session: StudySession):
        """更新总统计"""
        stats = self._storage.get("total_stats", {})
        
        stats["total_sessions"] = stats.get("total_sessions", 0) + 1
        stats["total_minutes"] = stats.get("total_minutes", 0) + session.duration_minutes
        stats["total_pomodoros"] = stats.get("total_pomodoros", 0) + session.pomodoro_count
        
        if session.duration_minutes > stats.get("longest_session", 0):
            stats["longest_session"] = session.duration_minutes
        
        # 更新连续学习天数
        self._update_streak(stats)
        
        self._storage.set("total_stats", stats)
    
    def _update_streak(self, stats: Dict):
        """更新连续学习天数"""
        today = self.today_str()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 检查今天是否有学习
        today_sessions = [s for s in self._sessions if s.start_time.startswith(today)]
        if not today_sessions:
            return
        
        # 检查昨天是否有学习
        yesterday_sessions = [s for s in self._sessions if s.start_time.startswith(yesterday)]
        
        if yesterday_sessions:
            # 连续
            stats["current_streak"] = stats.get("current_streak", 0) + 1
        else:
            # 断了，从1开始
            stats["current_streak"] = 1
        
        if stats["current_streak"] > stats.get("best_streak", 0):
            stats["best_streak"] = stats["current_streak"]
    
    # ========== 目标管理 ==========
    
    def set_daily_goal(self, minutes: int, date: str = None):
        """设置每日目标"""
        date = date or self.today_str()
        daily_goals = self._storage.get("daily_goals", {})
        daily_goals[date] = minutes
        self._storage.set("daily_goals", daily_goals)
    
    def get_daily_goal(self, date: str = None) -> int:
        """获取每日目标"""
        date = date or self.today_str()
        daily_goals = self._storage.get("daily_goals", {})
        return daily_goals.get(date, 120)  # 默认2小时
    
    def get_goal_progress(self, date: str = None) -> Dict[str, Any]:
        """获取目标完成进度"""
        date = date or self.today_str()
        goal = self.get_daily_goal(date)
        stats = self._get_date_stats(date)
        actual = stats["total_minutes"]
        
        return {
            "goal": goal,
            "actual": actual,
            "progress": min(1.0, actual / goal) if goal > 0 else 0,
            "remaining": max(0, goal - actual),
            "completed": actual >= goal,
        }
