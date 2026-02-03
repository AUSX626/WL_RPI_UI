"""
命令服务 - 统一处理来自各输入源的指令

功能：
- 统一指令格式
- 支持多种输入源（UI、语音、遥控器、手势）
- 指令优先级管理
- 指令历史记录

使用示例：
    cmd = CommandService()
    
    # 注册指令处理器
    cmd.register_handler("switch_mode", handle_mode_switch)
    
    # 执行指令（来自任意输入源）
    cmd.execute("switch_mode", {"mode": "study"}, source="voice")
    cmd.execute("set_brightness", {"value": 0.8}, source="ui")
"""
import time
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from collections import deque


class InputSource(str, Enum):
    """输入源类型"""
    UI = "ui"              # UI 界面点击
    VOICE = "voice"        # 语音指令
    GESTURE = "gesture"    # 手势识别
    REMOTE = "remote"      # 遥控器/网络
    SCHEDULE = "schedule"  # 定时任务
    SYSTEM = "system"      # 系统内部


class ControlMode(str, Enum):
    """控制模式 - 决定哪个输入源有控制权"""
    UI_ONLY = "ui_only"           # 仅 UI 控制
    VOICE_ONLY = "voice_only"     # 仅语音控制
    REMOTE_ONLY = "remote_only"   # 仅遥控器控制
    UI_VOICE = "ui_voice"         # UI + 语音
    UI_REMOTE = "ui_remote"       # UI + 遥控器
    ALL = "all"                   # 全部开放（默认）
    

class CommandPriority(int, Enum):
    """指令优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3  # 紧急（如：关机、紧急停止）


@dataclass
class Command:
    """指令数据结构"""
    name: str                           # 指令名称
    params: Dict[str, Any] = field(default_factory=dict)  # 参数
    source: InputSource = InputSource.SYSTEM  # 来源
    priority: CommandPriority = CommandPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    
    def __repr__(self):
        return f"Command({self.name}, source={self.source.value}, params={self.params})"


@dataclass
class CommandResult:
    """指令执行结果"""
    success: bool
    message: str = ""
    data: Any = None
    error: Optional[str] = None


# 指令处理器类型
CommandHandler = Callable[[Command], CommandResult]


class CommandService:
    """
    命令调度服务
    
    职责：
    - 接收来自各输入源的指令
    - 按优先级排队执行
    - 记录指令历史
    - 支持指令拦截/过滤
    """
    
    # ========== 预定义指令 ==========
    COMMANDS = {
        # 模式切换
        "switch_mode": "切换模式",
        "enter_standby": "进入待机",
        "enter_hand_follow": "进入手势跟随",
        "enter_pet_mode": "进入宠物模式",
        "enter_study_mode": "进入学习模式",
        "enter_settings": "进入设置",
        
        # 亮度控制
        "set_brightness": "设置亮度",
        "turn_on": "开灯",
        "turn_off": "关灯",
        "brightness_up": "亮度增加",
        "brightness_down": "亮度降低",
        
        # 宠物互动
        "pet_interact": "宠物互动",
        "pet_feed": "喂食",
        "pet_play": "玩耍",
        "pet_talk": "聊天",
        
        # 学习相关
        "start_study": "开始学习",
        "end_study": "结束学习",
        "start_pomodoro": "开始番茄钟",
        "pause_pomodoro": "暂停番茄钟",
        "skip_break": "跳过休息",
        
        # 日程相关
        "add_reminder": "添加提醒",
        "list_reminders": "查看提醒",
        "delete_reminder": "删除提醒",
        
        # 系统
        "shutdown": "关机",
        "restart": "重启",
        "sleep": "休眠",
        "wake_up": "唤醒",
    }
    
    # 语音指令映射（语音关键词 → 指令名）
    VOICE_MAPPINGS = {
        # 模式切换
        "手势模式": "enter_hand_follow",
        "跟随模式": "enter_hand_follow",
        "跟着我": "enter_hand_follow",
        "宠物模式": "enter_pet_mode",
        "陪我玩": "enter_pet_mode",
        "学习模式": "enter_study_mode",
        "开始学习": "start_study",
        "专注模式": "enter_study_mode",
        "设置": "enter_settings",
        "待机": "enter_standby",
        "休息": "enter_standby",
        
        # 亮度
        "开灯": "turn_on",
        "关灯": "turn_off",
        "亮一点": "brightness_up",
        "暗一点": "brightness_down",
        "最亮": ("set_brightness", {"value": 1.0}),
        "最暗": ("set_brightness", {"value": 0.1}),
        
        # 宠物
        "摸摸头": ("pet_interact", {"action": "pet"}),
        "玩游戏": ("pet_interact", {"action": "play"}),
        "聊天": ("pet_interact", {"action": "talk"}),
        
        # 番茄钟
        "番茄钟": "start_pomodoro",
        "暂停": "pause_pomodoro",
        "结束学习": "end_study",
        
        # 系统
        "关机": "shutdown",
        "重启": "restart",
        "晚安": "sleep",
        "早安": "wake_up",
    }
    
    def __init__(self, history_size: int = 100):
        """
        初始化命令服务
        
        Args:
            history_size: 历史记录大小
        """
        self._handlers: Dict[str, CommandHandler] = {}
        self._history: deque = deque(maxlen=history_size)
        self._interceptors: List[Callable[[Command], Optional[Command]]] = []
        self._listeners: List[Callable[[Command, CommandResult], None]] = []
        self._lock = threading.RLock()
        
        # 指令队列（按优先级）
        self._queue: List[Command] = []
        self._processing = False
        
        # ===== 控制权管理 =====
        self._control_mode: ControlMode = ControlMode.ALL  # 默认全部开放
        self._control_mode_callbacks: List[Callable[[ControlMode], None]] = []
        
        # 控制模式对应的允许输入源
        self._allowed_sources: Dict[ControlMode, set] = {
            ControlMode.UI_ONLY: {InputSource.UI, InputSource.SYSTEM, InputSource.SCHEDULE},
            ControlMode.VOICE_ONLY: {InputSource.VOICE, InputSource.SYSTEM, InputSource.SCHEDULE},
            ControlMode.REMOTE_ONLY: {InputSource.REMOTE, InputSource.SYSTEM, InputSource.SCHEDULE},
            ControlMode.UI_VOICE: {InputSource.UI, InputSource.VOICE, InputSource.SYSTEM, InputSource.SCHEDULE},
            ControlMode.UI_REMOTE: {InputSource.UI, InputSource.REMOTE, InputSource.SYSTEM, InputSource.SCHEDULE},
            ControlMode.ALL: {InputSource.UI, InputSource.VOICE, InputSource.GESTURE, 
                             InputSource.REMOTE, InputSource.SCHEDULE, InputSource.SYSTEM},
        }
        
        print("[Command] 命令服务初始化完成")
    
    # ========== 控制权管理 ==========
    
    @property
    def control_mode(self) -> ControlMode:
        """获取当前控制模式"""
        return self._control_mode
    
    def set_control_mode(self, mode: ControlMode) -> bool:
        """
        设置控制模式
        
        Args:
            mode: 控制模式
            
        Returns:
            是否成功
        """
        if mode == self._control_mode:
            return True
        
        old_mode = self._control_mode
        self._control_mode = mode
        
        print(f"[Command] 控制模式切换: {old_mode.value} → {mode.value}")
        
        # 通知监听器
        for callback in self._control_mode_callbacks:
            try:
                callback(mode)
            except Exception as e:
                print(f"[Command] 控制模式回调错误: {e}")
        
        return True
    
    def on_control_mode_change(self, callback: Callable[[ControlMode], None]):
        """监听控制模式变化"""
        self._control_mode_callbacks.append(callback)
    
    def is_source_allowed(self, source: InputSource) -> bool:
        """检查输入源是否被允许"""
        allowed = self._allowed_sources.get(self._control_mode, set())
        return source in allowed
    
    def get_allowed_sources(self) -> List[str]:
        """获取当前允许的输入源列表"""
        allowed = self._allowed_sources.get(self._control_mode, set())
        return [s.value for s in allowed]
    
    def get_control_mode_options(self) -> Dict[str, str]:
        """获取所有控制模式选项（用于 UI 显示）"""
        return {
            ControlMode.UI_ONLY.value: "仅 UI 控制",
            ControlMode.VOICE_ONLY.value: "仅语音控制",
            ControlMode.REMOTE_ONLY.value: "仅遥控器控制",
            ControlMode.UI_VOICE.value: "UI + 语音",
            ControlMode.UI_REMOTE.value: "UI + 遥控器",
            ControlMode.ALL.value: "全部开放",
        }
    
    # ========== 指令注册 ==========
    
    def register_handler(self, command_name: str, handler: CommandHandler):
        """
        注册指令处理器
        
        Args:
            command_name: 指令名称
            handler: 处理函数 (Command) -> CommandResult
        """
        self._handlers[command_name] = handler
        print(f"[Command] 注册处理器: {command_name}")
    
    def register_handlers(self, handlers: Dict[str, CommandHandler]):
        """批量注册处理器"""
        for name, handler in handlers.items():
            self.register_handler(name, handler)
    
    # ========== 指令执行 ==========
    
    def execute(
        self,
        command_name: str,
        params: Dict[str, Any] = None,
        source: InputSource = InputSource.SYSTEM,
        priority: CommandPriority = CommandPriority.NORMAL,
    ) -> CommandResult:
        """
        执行指令
        
        Args:
            command_name: 指令名称
            params: 参数字典
            source: 输入源
            priority: 优先级
            
        Returns:
            CommandResult
        """
        cmd = Command(
            name=command_name,
            params=params or {},
            source=source,
            priority=priority,
        )
        
        return self._execute_command(cmd)
    
    def execute_from_voice(self, text: str) -> CommandResult:
        """
        从语音文本解析并执行指令
        
        Args:
            text: 语音识别文本
            
        Returns:
            CommandResult
        """
        # 查找匹配的语音指令
        cmd_info = self._parse_voice_command(text)
        
        if cmd_info is None:
            return CommandResult(
                success=False,
                message=f"未识别的指令: {text}",
                error="UNKNOWN_COMMAND"
            )
        
        command_name, params = cmd_info
        
        return self.execute(
            command_name=command_name,
            params=params,
            source=InputSource.VOICE,
        )
    
    def execute_from_ui(self, command_name: str, params: Dict[str, Any] = None) -> CommandResult:
        """从 UI 执行指令"""
        return self.execute(command_name, params, source=InputSource.UI)
    
    def execute_from_remote(self, command_name: str, params: Dict[str, Any] = None) -> CommandResult:
        """从遥控器/网络执行指令"""
        return self.execute(command_name, params, source=InputSource.REMOTE)
    
    def _execute_command(self, cmd: Command) -> CommandResult:
        """内部执行指令"""
        with self._lock:
            # 0. 控制权检查
            if not self.is_source_allowed(cmd.source):
                result = CommandResult(
                    success=False,
                    message=f"当前控制模式({self._control_mode.value})不允许 {cmd.source.value} 控制",
                    error="SOURCE_NOT_ALLOWED"
                )
                print(f"[Command] 拒绝: {cmd.source.value} 无控制权")
                self._notify_listeners(cmd, result)
                return result
            
            # 1. 拦截器处理
            for interceptor in self._interceptors:
                modified = interceptor(cmd)
                if modified is None:
                    # 被拦截，不执行
                    result = CommandResult(
                        success=False,
                        message="指令被拦截",
                        error="INTERCEPTED"
                    )
                    self._notify_listeners(cmd, result)
                    return result
                cmd = modified
            
            # 2. 查找处理器
            handler = self._handlers.get(cmd.name)
            
            if handler is None:
                result = CommandResult(
                    success=False,
                    message=f"未注册的指令: {cmd.name}",
                    error="NO_HANDLER"
                )
                self._notify_listeners(cmd, result)
                return result
            
            # 3. 执行
            try:
                print(f"[Command] 执行: {cmd}")
                result = handler(cmd)
            except Exception as e:
                result = CommandResult(
                    success=False,
                    message=f"执行失败: {str(e)}",
                    error=str(e)
                )
            
            # 4. 记录历史
            self._history.append((cmd, result))
            
            # 5. 通知监听器
            self._notify_listeners(cmd, result)
            
            return result
    
    def _parse_voice_command(self, text: str) -> Optional[tuple]:
        """
        解析语音指令
        
        Returns:
            (command_name, params) 或 None
        """
        text = text.strip()
        
        # 精确匹配
        if text in self.VOICE_MAPPINGS:
            mapping = self.VOICE_MAPPINGS[text]
            if isinstance(mapping, str):
                return (mapping, {})
            else:
                return mapping  # (cmd_name, params)
        
        # 模糊匹配
        for keyword, mapping in self.VOICE_MAPPINGS.items():
            if keyword in text:
                if isinstance(mapping, str):
                    return (mapping, {})
                else:
                    return mapping
        
        # 尝试提取参数（如 "亮度调到80"）
        import re
        
        # 亮度数值
        match = re.search(r'亮度.*?(\d+)', text)
        if match:
            value = int(match.group(1))
            if value > 1:
                value = value / 100  # 假设是百分比
            return ("set_brightness", {"value": value})
        
        # 提醒时间
        match = re.search(r'(\d+)分钟后提醒我(.+)', text)
        if match:
            minutes = int(match.group(1))
            content = match.group(2).strip()
            return ("add_reminder", {"minutes": minutes, "content": content})
        
        return None
    
    # ========== 拦截器和监听器 ==========
    
    def add_interceptor(self, interceptor: Callable[[Command], Optional[Command]]):
        """
        添加指令拦截器
        
        拦截器返回 None 表示拦截该指令，返回 Command 表示继续执行（可修改）
        """
        self._interceptors.append(interceptor)
    
    def add_listener(self, listener: Callable[[Command, CommandResult], None]):
        """添加指令执行监听器（用于日志、统计等）"""
        self._listeners.append(listener)
    
    def _notify_listeners(self, cmd: Command, result: CommandResult):
        """通知所有监听器"""
        for listener in self._listeners:
            try:
                listener(cmd, result)
            except Exception as e:
                print(f"[Command] 监听器错误: {e}")
    
    # ========== 历史记录 ==========
    
    def get_history(self, limit: int = 10) -> List[tuple]:
        """获取最近的指令历史"""
        return list(self._history)[-limit:]
    
    def get_available_commands(self) -> Dict[str, str]:
        """获取所有可用指令"""
        return {
            name: desc 
            for name, desc in self.COMMANDS.items() 
            if name in self._handlers
        }
    
    def get_voice_commands(self) -> Dict[str, str]:
        """获取语音指令列表"""
        result = {}
        for keyword, mapping in self.VOICE_MAPPINGS.items():
            cmd_name = mapping if isinstance(mapping, str) else mapping[0]
            desc = self.COMMANDS.get(cmd_name, cmd_name)
            result[keyword] = desc
        return result


class CommandServiceIntegration:
    """
    命令服务与主控制器的集成
    
    把 CommandService 和 MainController/ServiceManager 连接起来
    """
    
    def __init__(self, command_service: CommandService, controller, services):
        """
        Args:
            command_service: 命令服务实例
            controller: MainController 实例
            services: ServiceManager 实例
        """
        self.cmd = command_service
        self.controller = controller
        self.services = services
        
        self._register_all_handlers()
    
    def _register_all_handlers(self):
        """注册所有指令处理器"""
        
        # ===== 模式切换 =====
        self.cmd.register_handler("switch_mode", self._handle_switch_mode)
        self.cmd.register_handler("enter_standby", 
            lambda c: self._handle_switch_mode(Command("switch_mode", {"mode": "standby"})))
        self.cmd.register_handler("enter_hand_follow",
            lambda c: self._handle_switch_mode(Command("switch_mode", {"mode": "hand_follow"})))
        self.cmd.register_handler("enter_pet_mode",
            lambda c: self._handle_switch_mode(Command("switch_mode", {"mode": "pet"})))
        self.cmd.register_handler("enter_study_mode",
            lambda c: self._handle_switch_mode(Command("switch_mode", {"mode": "study"})))
        self.cmd.register_handler("enter_settings",
            lambda c: self._handle_switch_mode(Command("switch_mode", {"mode": "settings"})))
        
        # ===== 亮度控制 =====
        self.cmd.register_handler("set_brightness", self._handle_set_brightness)
        self.cmd.register_handler("turn_on", self._handle_turn_on)
        self.cmd.register_handler("turn_off", self._handle_turn_off)
        self.cmd.register_handler("brightness_up", self._handle_brightness_up)
        self.cmd.register_handler("brightness_down", self._handle_brightness_down)
        
        # ===== 宠物互动 =====
        self.cmd.register_handler("pet_interact", self._handle_pet_interact)
        
        # ===== 学习相关 =====
        self.cmd.register_handler("start_study", self._handle_start_study)
        self.cmd.register_handler("end_study", self._handle_end_study)
        self.cmd.register_handler("start_pomodoro", self._handle_start_pomodoro)
        
        # ===== 日程相关 =====
        self.cmd.register_handler("add_reminder", self._handle_add_reminder)
        
        print("[Command] 所有处理器注册完成")
    
    # ========== 处理器实现 ==========
    
    def _handle_switch_mode(self, cmd: Command) -> CommandResult:
        """处理模式切换"""
        mode = cmd.params.get("mode", "standby")
        
        # TODO: 调用 controller 的模式切换方法
        # self.controller.switch_mode(mode)
        
        return CommandResult(
            success=True,
            message=f"切换到 {mode} 模式",
            data={"mode": mode, "source": cmd.source.value}
        )
    
    def _handle_set_brightness(self, cmd: Command) -> CommandResult:
        """设置亮度"""
        value = cmd.params.get("value", 0.5)
        value = max(0.0, min(1.0, float(value)))
        
        if self.controller and hasattr(self.controller, '_lighting'):
            self.controller._lighting.set(value)
        
        return CommandResult(
            success=True,
            message=f"亮度设置为 {int(value*100)}%",
            data={"brightness": value}
        )
    
    def _handle_turn_on(self, cmd: Command) -> CommandResult:
        """开灯"""
        brightness = self.services.settings.default_brightness if self.services else 0.8
        
        if self.controller and hasattr(self.controller, '_lighting'):
            self.controller._lighting.on(brightness)
        
        return CommandResult(success=True, message="灯已打开")
    
    def _handle_turn_off(self, cmd: Command) -> CommandResult:
        """关灯"""
        if self.controller and hasattr(self.controller, '_lighting'):
            self.controller._lighting.off()
        
        return CommandResult(success=True, message="灯已关闭")
    
    def _handle_brightness_up(self, cmd: Command) -> CommandResult:
        """亮度增加"""
        step = cmd.params.get("step", 0.1)
        
        if self.controller and hasattr(self.controller, '_lighting'):
            current = self.controller._lighting.current_brightness
            new_value = min(1.0, current + step)
            self.controller._lighting.set(new_value)
            return CommandResult(
                success=True, 
                message=f"亮度增加到 {int(new_value*100)}%",
                data={"brightness": new_value}
            )
        
        return CommandResult(success=False, message="亮度控制器不可用")
    
    def _handle_brightness_down(self, cmd: Command) -> CommandResult:
        """亮度降低"""
        step = cmd.params.get("step", 0.1)
        
        if self.controller and hasattr(self.controller, '_lighting'):
            current = self.controller._lighting.current_brightness
            new_value = max(0.1, current - step)
            self.controller._lighting.set(new_value)
            return CommandResult(
                success=True,
                message=f"亮度降低到 {int(new_value*100)}%",
                data={"brightness": new_value}
            )
        
        return CommandResult(success=False, message="亮度控制器不可用")
    
    def _handle_pet_interact(self, cmd: Command) -> CommandResult:
        """宠物互动"""
        action = cmd.params.get("action", "pet")
        
        if self.services:
            result = self.services.pet.interact(action)
            return CommandResult(
                success=True,
                message=result.get("message", ""),
                data=result
            )
        
        return CommandResult(success=False, message="宠物服务不可用")
    
    def _handle_start_study(self, cmd: Command) -> CommandResult:
        """开始学习"""
        mode = cmd.params.get("mode", "normal")
        
        if self.services:
            session_id = self.services.study.start_session(mode=mode)
            return CommandResult(
                success=True,
                message="学习开始，加油！",
                data={"session_id": session_id}
            )
        
        return CommandResult(success=False, message="学习服务不可用")
    
    def _handle_end_study(self, cmd: Command) -> CommandResult:
        """结束学习"""
        if self.services:
            session = self.services.study.end_session(completed=True)
            if session:
                return CommandResult(
                    success=True,
                    message=f"学习结束，本次学习 {session.duration_minutes} 分钟",
                    data={"duration": session.duration_minutes}
                )
        
        return CommandResult(success=False, message="没有进行中的学习")
    
    def _handle_start_pomodoro(self, cmd: Command) -> CommandResult:
        """开始番茄钟"""
        if self.services:
            session_id = self.services.study.start_session(mode="pomodoro")
            work_time = self.services.settings.pomodoro_work
            return CommandResult(
                success=True,
                message=f"番茄钟开始，{work_time}分钟后提醒你休息",
                data={"session_id": session_id, "duration": work_time}
            )
        
        return CommandResult(success=False, message="学习服务不可用")
    
    def _handle_add_reminder(self, cmd: Command) -> CommandResult:
        """添加提醒"""
        content = cmd.params.get("content", "提醒")
        minutes = cmd.params.get("minutes")
        time_str = cmd.params.get("time")
        
        if self.services:
            reminder = self.services.schedule.add_reminder(
                content=content,
                minutes=minutes,
                time=time_str,
            )
            return CommandResult(
                success=True,
                message=f"好的，{reminder.trigger_time.strftime('%H:%M')} 提醒你{content}",
                data={"reminder_id": reminder.id}
            )
        
        return CommandResult(success=False, message="日程服务不可用")
