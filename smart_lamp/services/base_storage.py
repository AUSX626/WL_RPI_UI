"""
数据存储基类 - JSON 文件存储
"""
import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime


class BaseStorage:
    """
    JSON 文件存储基类
    
    特点：
    - 线程安全（带锁）
    - 自动创建目录
    - 支持默认值
    - 懒加载
    """
    
    def __init__(self, file_path: str, default_data: Optional[Dict] = None):
        """
        初始化存储
        
        Args:
            file_path: JSON 文件路径
            default_data: 默认数据（文件不存在时使用）
        """
        self._path = Path(file_path)
        self._default_data = default_data or {}
        self._data: Optional[Dict] = None
        self._lock = threading.RLock()
        
        # 确保目录存在
        self._path.parent.mkdir(parents=True, exist_ok=True)
    
    @property
    def data(self) -> Dict:
        """懒加载数据"""
        if self._data is None:
            self._load()
        return self._data
    
    def _load(self):
        """从文件加载数据"""
        with self._lock:
            if self._path.exists():
                try:
                    with open(self._path, 'r', encoding='utf-8') as f:
                        self._data = json.load(f)
                    # 合并默认值（保留文件中的值，补充缺失的默认值）
                    for key, value in self._default_data.items():
                        if key not in self._data:
                            self._data[key] = value
                except (json.JSONDecodeError, IOError) as e:
                    print(f"[Storage] 加载 {self._path} 失败: {e}")
                    self._data = self._default_data.copy()
            else:
                self._data = self._default_data.copy()
                self._save()  # 创建初始文件
    
    def _save(self):
        """保存数据到文件"""
        with self._lock:
            try:
                with open(self._path, 'w', encoding='utf-8') as f:
                    json.dump(self._data, f, ensure_ascii=False, indent=2)
            except IOError as e:
                print(f"[Storage] 保存 {self._path} 失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取值"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置值并保存"""
        with self._lock:
            self.data[key] = value
            self._save()
    
    def update(self, updates: Dict[str, Any]):
        """批量更新"""
        with self._lock:
            self.data.update(updates)
            self._save()
    
    def delete(self, key: str) -> bool:
        """删除键"""
        with self._lock:
            if key in self.data:
                del self.data[key]
                self._save()
                return True
            return False
    
    def get_all(self) -> Dict:
        """获取所有数据（副本）"""
        return self.data.copy()
    
    def reload(self):
        """强制重新加载"""
        with self._lock:
            self._data = None
            self._load()


class TimestampMixin:
    """时间戳混入类"""
    
    @staticmethod
    def now_str() -> str:
        """当前时间字符串"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def today_str() -> str:
        """今日日期字符串"""
        return datetime.now().strftime("%Y-%m-%d")
    
    @staticmethod
    def parse_datetime(s: str) -> Optional[datetime]:
        """解析时间字符串"""
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None
