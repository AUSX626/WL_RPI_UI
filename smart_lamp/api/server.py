"""
API 服务器 - FastAPI/Flask 实现

支持两种模式：
1. FastAPI（推荐，支持 WebSocket）
2. Flask（备选，更轻量）

会自动检测可用的框架
"""
import threading
from typing import Optional, Any, Dict, Callable
import json


# 全局引用
_controller = None
_services = None
_event_callbacks = []


def init_api(controller):
    """
    初始化 API，注入控制器引用
    
    Args:
        controller: MainController 实例
    """
    global _controller, _services
    _controller = controller
    _services = controller.services


def get_controller():
    """获取控制器引用"""
    return _controller


def get_services():
    """获取服务管理器引用"""
    return _services


def register_event_callback(callback: Callable[[str, Any], None]):
    """注册事件回调（用于 WebSocket 推送）"""
    _event_callbacks.append(callback)


def emit_event(event_type: str, data: Any):
    """触发事件（推送到所有客户端）"""
    for callback in _event_callbacks:
        try:
            callback(event_type, data)
        except Exception as e:
            print(f"[API] 事件回调失败: {e}")


# ============== 尝试使用 FastAPI ==============

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    
    HAS_FASTAPI = True
    print("[API] 使用 FastAPI")
    
except ImportError:
    HAS_FASTAPI = False
    print("[API] FastAPI 不可用，尝试 Flask")


# ============== 尝试使用 Flask ==============

if not HAS_FASTAPI:
    try:
        from flask import Flask, jsonify, request
        from flask_cors import CORS
        
        HAS_FLASK = True
        print("[API] 使用 Flask")
        
    except ImportError:
        HAS_FLASK = False
        print("[API] Flask 也不可用，API 功能禁用")


# ============== FastAPI 实现 ==============

if HAS_FASTAPI:
    
    def create_app() -> FastAPI:
        """创建 FastAPI 应用"""
        app = FastAPI(
            title="智能桌宠 API",
            description="智能台灯/桌宠控制接口",
            version="1.0.0"
        )
        
        # CORS 配置（允许前端跨域访问）
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 注册路由
        from .routes import register_routes
        register_routes(app)
        
        return app
    
    
    def run_server(app: FastAPI, host: str = "0.0.0.0", port: int = 8080):
        """运行服务器（阻塞）"""
        uvicorn.run(app, host=host, port=port, log_level="warning")
    
    
    def run_server_background(app: FastAPI, host: str = "0.0.0.0", port: int = 8080) -> threading.Thread:
        """在后台线程运行服务器"""
        thread = threading.Thread(
            target=run_server,
            args=(app, host, port),
            daemon=True,
            name="APIServer"
        )
        thread.start()
        print(f"[API] 服务器启动: http://{host}:{port}")
        return thread


# ============== Flask 实现（备选） ==============

elif HAS_FLASK:
    
    def create_app() -> Flask:
        """创建 Flask 应用"""
        app = Flask(__name__)
        CORS(app)  # 允许跨域
        
        # 注册路由
        from .routes_flask import register_routes_flask
        register_routes_flask(app)
        
        return app
    
    
    def run_server(app: Flask, host: str = "0.0.0.0", port: int = 8080):
        """运行服务器（阻塞）"""
        app.run(host=host, port=port, threaded=True)
    
    
    def run_server_background(app: Flask, host: str = "0.0.0.0", port: int = 8080) -> threading.Thread:
        """在后台线程运行服务器"""
        thread = threading.Thread(
            target=run_server,
            args=(app, host, port),
            daemon=True,
            name="APIServer"
        )
        thread.start()
        print(f"[API] 服务器启动: http://{host}:{port}")
        return thread


# ============== 无框架可用 ==============

else:
    
    def create_app():
        raise RuntimeError("没有可用的 Web 框架，请安装 fastapi 或 flask")
    
    def run_server(*args, **kwargs):
        raise RuntimeError("没有可用的 Web 框架")
    
    def run_server_background(*args, **kwargs):
        raise RuntimeError("没有可用的 Web 框架")
