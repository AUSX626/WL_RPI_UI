"""
串口通信模块

提供与外部设备的串口通信功能。
GPIO14 -> TX, GPIO15 -> RX
"""

from .serial_thread import SerialThread
from .protocol import CommandType, ProtocolFrame

__all__ = ['SerialThread', 'CommandType', 'ProtocolFrame']
