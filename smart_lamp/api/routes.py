"""
API 路由 - FastAPI 版本
"""
from typing import Any, Dict, List, Optional


def register_routes(app):
    """注册所有路由到 FastAPI 应用"""
    from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
    from pydantic import BaseModel
    
    from .server import get_controller, get_services, emit_event, register_event_callback
    
    # ============== 数据模型 ==============
    
    class ModeRequest(BaseModel):
        mode: str
    
    class BrightnessRequest(BaseModel):
        brightness: float
    
    class SettingRequest(BaseModel):
        value: Any
    
    class ReminderRequest(BaseModel):
        content: str
        time: Optional[str] = None
        minutes: Optional[int] = None
        repeat: str = "none"
    
    class InteractRequest(BaseModel):
        action: str
    
    # ============== 系统状态 ==============
    
    @app.get("/api/status")
    async def get_status():
        """获取系统状态"""
        controller = get_controller()
        services = get_services()
        
        if not controller:
            return {"error": "系统未初始化"}
        
        return {
            "state": controller.state_machine.state.name,
            "brightness": controller._lighting.current_brightness if controller._lighting else 0,
            "is_running": controller.running,
            "pet": services.pet.get_status_dict() if services else {},
        }
    
    @app.get("/api/health")
    async def health_check():
        """健康检查"""
        return {"status": "ok", "message": "API 运行正常"}
    
    # ============== 模式控制 ==============
    
    @app.get("/api/modes")
    async def get_modes():
        """获取所有可用模式"""
        controller = get_controller()
        
        modes = [
            {"id": "hand_follow", "name": "手势跟随", "icon": "✋", "description": "灯头跟随手部移动"},
            {"id": "pet", "name": "桌宠互动", "icon": "🐾", "description": "与桌宠互动玩耍"},
            {"id": "brightness", "name": "亮度调节", "icon": "💡", "description": "调节灯光亮度"},
            {"id": "study", "name": "学习模式", "icon": "📚", "description": "专注学习，番茄钟"},
            {"id": "settings", "name": "设置", "icon": "⚙️", "description": "系统设置"},
        ]
        
        current = controller.state_machine.state.name if controller else "STANDBY"
        
        return {
            "modes": modes,
            "current": current,
        }
    
    @app.post("/api/mode")
    async def set_mode(req: ModeRequest):
        """切换模式"""
        controller = get_controller()
        
        if not controller:
            raise HTTPException(status_code=500, detail="系统未初始化")
        
        # TODO: 实现模式切换
        # success = controller.switch_mode(req.mode)
        
        return {
            "success": True,
            "message": f"切换到 {req.mode} 模式",
            "current_mode": controller.state_machine.state.name,
        }
    
    # ============== 亮度控制 ==============
    
    @app.get("/api/brightness")
    async def get_brightness():
        """获取当前亮度"""
        controller = get_controller()
        
        if controller and controller._lighting:
            return {
                "brightness": controller._lighting.current_brightness,
                "is_on": controller._lighting.is_on,
            }
        
        return {"brightness": 0, "is_on": False}
    
    @app.post("/api/brightness")
    async def set_brightness(req: BrightnessRequest):
        """设置亮度"""
        controller = get_controller()
        
        if not controller or not controller._lighting:
            raise HTTPException(status_code=500, detail="亮度控制器未初始化")
        
        # 验证范围
        brightness = max(0.0, min(1.0, req.brightness))
        success = controller._lighting.set(brightness)
        
        # 触发事件
        emit_event("brightness_changed", {"brightness": brightness})
        
        return {
            "success": success,
            "brightness": brightness,
        }
    
    @app.post("/api/brightness/on")
    async def turn_on():
        """开灯"""
        controller = get_controller()
        services = get_services()
        
        if controller and controller._lighting:
            brightness = services.settings.default_brightness if services else 0.8
            controller._lighting.on(brightness)
            return {"success": True, "brightness": brightness}
        
        raise HTTPException(status_code=500, detail="亮度控制器未初始化")
    
    @app.post("/api/brightness/off")
    async def turn_off():
        """关灯"""
        controller = get_controller()
        
        if controller and controller._lighting:
            controller._lighting.off()
            return {"success": True}
        
        raise HTTPException(status_code=500, detail="亮度控制器未初始化")
    
    # ============== 设置 ==============
    
    @app.get("/api/settings")
    async def get_settings():
        """获取所有设置"""
        services = get_services()
        
        if not services:
            return {}
        
        return services.settings.get_all()
    
    @app.put("/api/settings")
    async def update_settings(settings: dict):
        """批量更新设置"""
        services = get_services()
        
        if not services:
            raise HTTPException(status_code=500, detail="服务未初始化")
        
        success = services.settings.update(settings)
        
        return {"success": success}
    
    @app.get("/api/settings/{key}")
    async def get_setting(key: str):
        """获取单个设置"""
        services = get_services()
        
        if not services:
            raise HTTPException(status_code=500, detail="服务未初始化")
        
        value = services.settings.get(key)
        
        return {"key": key, "value": value}
    
    @app.put("/api/settings/{key}")
    async def update_setting(key: str, req: SettingRequest):
        """更新单个设置"""
        services = get_services()
        
        if not services:
            raise HTTPException(status_code=500, detail="服务未初始化")
        
        success = services.settings.set(key, req.value)
        
        if not success:
            raise HTTPException(status_code=400, detail=f"设置 {key} 更新失败")
        
        return {"success": True, "key": key, "value": req.value}
    
    # ============== 宠物 ==============
    
    @app.get("/api/pet")
    async def get_pet_status():
        """获取宠物状态"""
        services = get_services()
        
        if not services:
            return {}
        
        return services.pet.get_status_dict()
    
    @app.post("/api/pet/interact")
    async def pet_interact(req: InteractRequest):
        """与宠物互动"""
        services = get_services()
        
        if not services:
            raise HTTPException(status_code=500, detail="服务未初始化")
        
        result = services.pet.interact(req.action)
        
        # 触发事件
        emit_event("pet_interact", result)
        
        return result
    
    @app.get("/api/pet/action")
    async def get_pet_action():
        """获取宠物建议动作"""
        services = get_services()
        
        if not services:
            return {"action": "idle"}
        
        action = services.pet.get_mood_action()
        mood = services.pet.current_mood.value
        
        return {"action": action, "mood": mood}
    
    # ============== 学习/番茄钟 ==============
    
    @app.get("/api/study/status")
    async def get_study_status():
        """获取学习状态"""
        services = get_services()
        
        if not services:
            return {"is_studying": False}
        
        return {
            "is_studying": services.study.is_studying,
            "current_duration": services.study.get_current_duration(),
            "today_stats": services.study.get_today_stats(),
            "goal_progress": services.study.get_goal_progress(),
        }
    
    @app.post("/api/study/start")
    async def start_study(mode: str = "study"):
        """开始学习"""
        services = get_services()
        
        if not services:
            raise HTTPException(status_code=500, detail="服务未初始化")
        
        session_id = services.study.start_session(mode=mode)
        
        emit_event("study_started", {"session_id": session_id, "mode": mode})
        
        return {"success": True, "session_id": session_id}
    
    @app.post("/api/study/end")
    async def end_study(completed: bool = True):
        """结束学习"""
        services = get_services()
        
        if not services:
            raise HTTPException(status_code=500, detail="服务未初始化")
        
        session = services.study.end_session(completed=completed)
        
        if session:
            emit_event("study_ended", {"duration": session.duration_minutes})
            return {
                "success": True,
                "duration_minutes": session.duration_minutes,
                "pomodoro_count": session.pomodoro_count,
            }
        
        return {"success": False, "message": "没有活跃的学习会话"}
    
    @app.get("/api/study/stats")
    async def get_study_stats():
        """获取学习统计"""
        services = get_services()
        
        if not services:
            return {}
        
        return {
            "today": services.study.get_today_stats(),
            "week": services.study.get_week_stats(),
            "total": services.study.get_total_stats(),
        }
    
    # ============== 提醒 ==============
    
    @app.get("/api/reminders")
    async def get_reminders():
        """获取所有提醒"""
        services = get_services()
        
        if not services:
            return {"reminders": []}
        
        reminders = services.schedule.get_all_reminders()
        
        return {
            "reminders": [r.to_dict() for r in reminders],
            "active_count": len(services.schedule.get_active_reminders()),
        }
    
    @app.post("/api/reminders")
    async def add_reminder(req: ReminderRequest):
        """添加提醒"""
        services = get_services()
        
        if not services:
            raise HTTPException(status_code=500, detail="服务未初始化")
        
        try:
            reminder = services.schedule.add_reminder(
                content=req.content,
                time=req.time,
                minutes=req.minutes,
                repeat=req.repeat,
            )
            return {"success": True, "reminder": reminder.to_dict()}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.delete("/api/reminders/{reminder_id}")
    async def delete_reminder(reminder_id: str):
        """删除提醒"""
        services = get_services()
        
        if not services:
            raise HTTPException(status_code=500, detail="服务未初始化")
        
        success = services.schedule.remove_reminder(reminder_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="提醒不存在")
        
        return {"success": True}
    
    # ============== WebSocket ==============
    
    # WebSocket 连接管理
    ws_connections: List[WebSocket] = []
    
    @app.websocket("/ws/events")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket 事件订阅"""
        await websocket.accept()
        ws_connections.append(websocket)
        
        try:
            # 发送欢迎消息
            await websocket.send_json({
                "type": "connected",
                "message": "已连接到事件流"
            })
            
            # 保持连接
            while True:
                data = await websocket.receive_text()
                # 可以处理客户端发来的消息
                
        except WebSocketDisconnect:
            ws_connections.remove(websocket)
    
    # 注册事件推送回调
    async def push_to_websockets(event_type: str, data: Any):
        """推送事件到所有 WebSocket 连接"""
        import json
        message = json.dumps({"type": event_type, "data": data})
        
        for ws in ws_connections[:]:  # 使用副本遍历
            try:
                await ws.send_text(message)
            except:
                ws_connections.remove(ws)
    
    # 注意：由于 asyncio 的限制，这里需要特殊处理
    # register_event_callback(push_to_websockets)
    
    print("[API] FastAPI 路由注册完成")
