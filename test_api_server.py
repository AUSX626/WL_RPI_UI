#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 服务器启动脚本

启动 HTTP API 服务器，供前端调用

使用方法：
    python test_api_server.py
    
然后前端可以访问:
    http://localhost:8080/api/status
    http://localhost:8080/api/pet
    http://localhost:8080/api/settings
    ...
"""
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    print("=" * 60)
    print("    API 服务器")
    print("=" * 60)
    
    # 检查依赖
    try:
        import fastapi
        import uvicorn
        print("✓ FastAPI 可用")
    except ImportError:
        print("✗ FastAPI 未安装")
        print("\n请先安装依赖:")
        print("  pip install fastapi uvicorn")
        return 1
    
    # 初始化服务层
    from smart_lamp.services import ServiceManager
    services = ServiceManager(data_dir="data")
    
    # 创建一个模拟的 controller（因为我们只是测试 API）
    class MockController:
        def __init__(self, services):
            self.services = services
            self._lighting = None
            self._running = True
            
            # 模拟状态机
            class MockStateMachine:
                class MockState:
                    name = "STANDBY"
                state = MockState()
            self.state_machine = MockStateMachine()
        
        @property
        def running(self):
            return self._running
    
    mock_controller = MockController(services)
    
    # 初始化 API
    from smart_lamp.api.server import init_api, create_app
    
    init_api(mock_controller)
    app = create_app()
    
    # 启动服务器
    print("\n" + "-" * 60)
    print("API 服务器启动中...")
    print("-" * 60)
    print("\n可用的 API 端点:")
    print("  GET  http://localhost:8080/api/health    - 健康检查")
    print("  GET  http://localhost:8080/api/status    - 系统状态")
    print("  GET  http://localhost:8080/api/pet       - 宠物状态")
    print("  POST http://localhost:8080/api/pet/interact - 与宠物互动")
    print("  GET  http://localhost:8080/api/settings  - 获取设置")
    print("  PUT  http://localhost:8080/api/settings  - 更新设置")
    print("  GET  http://localhost:8080/api/study/status - 学习状态")
    print("  POST http://localhost:8080/api/study/start  - 开始学习")
    print("  POST http://localhost:8080/api/study/end    - 结束学习")
    print("  GET  http://localhost:8080/api/reminders    - 获取提醒")
    print("  POST http://localhost:8080/api/reminders    - 添加提醒")
    print("\n按 Ctrl+C 停止服务器")
    print("-" * 60 + "\n")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
