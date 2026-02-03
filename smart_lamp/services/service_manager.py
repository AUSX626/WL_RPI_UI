"""
服务管理器 - 统一管理所有服务

功能：
- 集中初始化所有服务
- 提供服务访问入口
- 管理服务生命周期

使用示例：
    services = ServiceManager(data_dir="data")
    
    # 访问各服务
    services.settings.set("volume", 80)
    services.pet.interact("pet")
    services.schedule.add_reminder("喝水", minutes=30)
    services.study.start_session()
"""
from typing import Optional
from pathlib import Path

from .settings_service import SettingsService
from .pet_service import PetService
from .schedule_service import ScheduleService
from .study_service import StudyService
from .command_service import CommandService, CommandServiceIntegration, InputSource, CommandResult, ControlMode


class ServiceManager:
    """
    服务管理器
    
    统一入口，集中管理所有服务实例
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化服务管理器
        
        Args:
            data_dir: 数据存储目录
        """
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[Services] 初始化服务层，数据目录: {self._data_dir}")
        
        # 初始化各服务
        self._settings: Optional[SettingsService] = None
        self._pet: Optional[PetService] = None
        self._schedule: Optional[ScheduleService] = None
        self._study: Optional[StudyService] = None
        self._command: Optional[CommandService] = None
        
        self._init_services()
    
    def _init_services(self):
        """初始化所有服务"""
        try:
            self._settings = SettingsService(str(self._data_dir))
            print("[Services] ✓ 设置服务")
        except Exception as e:
            print(f"[Services] ✗ 设置服务初始化失败: {e}")
        
        try:
            self._pet = PetService(str(self._data_dir))
            print("[Services] ✓ 宠物服务")
        except Exception as e:
            print(f"[Services] ✗ 宠物服务初始化失败: {e}")
        
        try:
            self._schedule = ScheduleService(str(self._data_dir))
            print("[Services] ✓ 日程服务")
        except Exception as e:
            print(f"[Services] ✗ 日程服务初始化失败: {e}")
        
        try:
            self._study = StudyService(str(self._data_dir))
            print("[Services] ✓ 学习服务")
        except Exception as e:
            print(f"[Services] ✗ 学习服务初始化失败: {e}")
        
        try:
            self._command = CommandService()
            print("[Services] ✓ 命令服务")
            # 注册基本处理器（不依赖 Controller）
            self._register_basic_handlers()
        except Exception as e:
            print(f"[Services] ✗ 命令服务初始化失败: {e}")
    
    def _register_basic_handlers(self):
        """注册不依赖 Controller 的基本处理器"""
        from .command_service import Command, CommandResult
        
        # 宠物互动
        def handle_pet_interact(cmd: Command) -> CommandResult:
            action = cmd.params.get("action", "pet")
            result = self._pet.interact(action)
            return CommandResult(
                success=True,
                message=result.get("message", ""),
                data=result
            )
        
        # 学习相关
        def handle_start_study(cmd: Command) -> CommandResult:
            mode = cmd.params.get("mode", "normal")
            session_id = self._study.start_session(mode=mode)
            return CommandResult(
                success=True,
                message="学习开始，加油！",
                data={"session_id": session_id}
            )
        
        def handle_end_study(cmd: Command) -> CommandResult:
            session = self._study.end_session(completed=True)
            if session:
                return CommandResult(
                    success=True,
                    message=f"学习结束，本次学习 {session.duration_minutes} 分钟",
                    data={"duration": session.duration_minutes}
                )
            return CommandResult(success=False, message="没有进行中的学习")
        
        def handle_start_pomodoro(cmd: Command) -> CommandResult:
            session_id = self._study.start_session(mode="pomodoro")
            work_time = self._settings.pomodoro_work
            return CommandResult(
                success=True,
                message=f"番茄钟开始，{work_time}分钟后提醒你休息",
                data={"session_id": session_id, "duration": work_time}
            )
        
        # 日程相关
        def handle_add_reminder(cmd: Command) -> CommandResult:
            content = cmd.params.get("content", "提醒")
            minutes = cmd.params.get("minutes")
            time_str = cmd.params.get("time")
            reminder = self._schedule.add_reminder(
                content=content,
                minutes=minutes,
                time=time_str,
            )
            # trigger_time 可能是字符串或 datetime
            if hasattr(reminder.trigger_time, 'strftime'):
                time_display = reminder.trigger_time.strftime('%H:%M')
            else:
                time_display = str(reminder.trigger_time)[:16]
            return CommandResult(
                success=True,
                message=f"好的，{time_display} 提醒你{content}",
                data={"reminder_id": reminder.id}
            )
        
        # 模式切换（占位，实际切换需要 Controller）
        def handle_switch_mode(cmd: Command) -> CommandResult:
            mode = cmd.params.get("mode", "standby")
            # TODO: 通知 Controller 切换模式
            return CommandResult(
                success=True,
                message=f"切换到 {mode} 模式",
                data={"mode": mode, "source": cmd.source.value}
            )
        
        # 亮度控制（占位）
        def handle_brightness(cmd: Command) -> CommandResult:
            value = cmd.params.get("value", 0.5)
            return CommandResult(
                success=True,
                message=f"亮度设置为 {int(float(value)*100)}%",
                data={"brightness": value}
            )
        
        def handle_turn_on(cmd: Command) -> CommandResult:
            return CommandResult(success=True, message="灯已打开")
        
        def handle_turn_off(cmd: Command) -> CommandResult:
            return CommandResult(success=True, message="灯已关闭")
        
        def handle_brightness_change(cmd: Command) -> CommandResult:
            direction = "增加" if "up" in cmd.name else "降低"
            return CommandResult(success=True, message=f"亮度已{direction}")
        
        # 注册处理器
        handlers = {
            "pet_interact": handle_pet_interact,
            "start_study": handle_start_study,
            "end_study": handle_end_study,
            "start_pomodoro": handle_start_pomodoro,
            "add_reminder": handle_add_reminder,
            "switch_mode": handle_switch_mode,
            "enter_standby": lambda c: handle_switch_mode(Command("switch_mode", {"mode": "standby"}, c.source)),
            "enter_hand_follow": lambda c: handle_switch_mode(Command("switch_mode", {"mode": "hand_follow"}, c.source)),
            "enter_pet_mode": lambda c: handle_switch_mode(Command("switch_mode", {"mode": "pet"}, c.source)),
            "enter_study_mode": lambda c: handle_switch_mode(Command("switch_mode", {"mode": "study"}, c.source)),
            "enter_settings": lambda c: handle_switch_mode(Command("switch_mode", {"mode": "settings"}, c.source)),
            "set_brightness": handle_brightness,
            "turn_on": handle_turn_on,
            "turn_off": handle_turn_off,
            "brightness_up": handle_brightness_change,
            "brightness_down": handle_brightness_change,
        }
        
        self._command.register_handlers(handlers)
        print("[Services] 基本命令处理器已注册")
    
    # ========== 服务访问器 ==========
    
    @property
    def settings(self) -> SettingsService:
        """设置服务"""
        if self._settings is None:
            raise RuntimeError("设置服务未初始化")
        return self._settings
    
    @property
    def pet(self) -> PetService:
        """宠物服务"""
        if self._pet is None:
            raise RuntimeError("宠物服务未初始化")
        return self._pet
    
    @property
    def schedule(self) -> ScheduleService:
        """日程服务"""
        if self._schedule is None:
            raise RuntimeError("日程服务未初始化")
        return self._schedule
    
    @property
    def study(self) -> StudyService:
        """学习服务"""
        if self._study is None:
            raise RuntimeError("学习服务未初始化")
        return self._study
    
    @property
    def command(self) -> CommandService:
        """命令服务"""
        if self._command is None:
            raise RuntimeError("命令服务未初始化")
        return self._command
    
    # ========== 命令快捷方法 ==========
    
    def execute(self, command_name: str, params: dict = None, source: str = "system") -> CommandResult:
        """
        执行指令的快捷方法
        
        Args:
            command_name: 指令名称
            params: 参数
            source: 来源 ("ui", "voice", "remote", "system")
        """
        source_map = {
            "ui": InputSource.UI,
            "voice": InputSource.VOICE,
            "remote": InputSource.REMOTE,
            "gesture": InputSource.GESTURE,
            "system": InputSource.SYSTEM,
        }
        return self._command.execute(
            command_name, 
            params or {}, 
            source=source_map.get(source, InputSource.SYSTEM)
        )
    
    def execute_voice(self, text: str) -> CommandResult:
        """从语音文本执行指令"""
        return self._command.execute_from_voice(text)
    
    # ========== 控制权管理 ==========
    
    def set_control_mode(self, mode: str) -> bool:
        """
        设置控制模式（UI 使用）
        
        Args:
            mode: 控制模式
                - "ui_only": 仅 UI 控制
                - "voice_only": 仅语音控制  
                - "remote_only": 仅遥控器控制
                - "ui_voice": UI + 语音
                - "ui_remote": UI + 遥控器
                - "all": 全部开放
        """
        mode_map = {
            "ui_only": ControlMode.UI_ONLY,
            "voice_only": ControlMode.VOICE_ONLY,
            "remote_only": ControlMode.REMOTE_ONLY,
            "ui_voice": ControlMode.UI_VOICE,
            "ui_remote": ControlMode.UI_REMOTE,
            "all": ControlMode.ALL,
        }
        control_mode = mode_map.get(mode, ControlMode.ALL)
        return self._command.set_control_mode(control_mode)
    
    def get_control_mode(self) -> str:
        """获取当前控制模式"""
        return self._command.control_mode.value
    
    def get_control_mode_options(self) -> dict:
        """获取所有控制模式选项（用于 UI 下拉框）"""
        return self._command.get_control_mode_options()
    
    def on_control_mode_change(self, callback):
        """监听控制模式变化"""
        self._command.on_control_mode_change(callback)
    
    def setup_controller(self, controller):
        """
        绑定主控制器，完成命令处理器注册
        
        Args:
            controller: MainController 实例
        """
        if self._command:
            self._integration = CommandServiceIntegration(
                self._command, 
                controller, 
                self
            )
            print("[Services] 命令服务已绑定控制器")
    
    # ========== 生命周期管理 ==========
    
    def start(self):
        """启动服务（启动后台任务等）"""
        # 启动日程检查
        if self._schedule:
            self._schedule.start_background_check(interval=30)
        
        # 宠物 tick
        # 可以在这里启动一个定时器定期调用 pet.tick()
        
        print("[Services] 服务已启动")
    
    def stop(self):
        """停止服务"""
        if self._schedule:
            self._schedule.stop_background_check()
        
        # 结束学习会话（如果有）
        if self._study and self._study.is_studying:
            self._study.end_session(completed=False, notes="系统关闭")
        
        print("[Services] 服务已停止")
    
    def get_all_status(self) -> dict:
        """获取所有服务状态（用于 API）"""
        return {
            "settings": self._settings.get_all() if self._settings else {},
            "pet": self._pet.get_status_dict() if self._pet else {},
            "study": {
                "is_studying": self._study.is_studying if self._study else False,
                "today_stats": self._study.get_today_stats() if self._study else {},
            },
            "schedule": {
                "active_reminders": len(self._schedule.get_active_reminders()) if self._schedule else 0,
            }
        }
