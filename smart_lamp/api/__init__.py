"""
API 层 - 为前端提供 HTTP/WebSocket 接口

架构说明：
    前端 (Web/App) <---HTTP/WS---> API层 <---> 服务层 <---> 硬件层

使用方法：
    1. 在 MainController 中启用 API：
       api_enabled = config.get('api', {}).get('enabled', False)
    
    2. 前端通过 HTTP 请求访问：
       GET  /api/status      - 获取系统状态
       POST /api/mode        - 切换模式
       GET  /api/settings    - 获取设置
       PUT  /api/settings    - 更新设置
       ...
    
    3. 实时推送通过 WebSocket：
       WS /ws/events         - 事件订阅
"""

from .server import create_app, init_api
from .routes import register_routes

__all__ = ['create_app', 'init_api', 'register_routes']
