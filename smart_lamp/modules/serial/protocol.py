"""
串口通信协议定义

【框架预留】具体协议格式按需定义
"""

from dataclasses import dataclass
from typing import Optional, Any
from enum import Enum


class CommandType(str, Enum):
    """命令类型"""
    # 调试命令
    DEBUG_ECHO = "echo"          # 回显测试
    DEBUG_STATUS = "status"      # 状态查询
    
    # 预留扩展
    # ACTION = "action"          # 动作指令
    # POSITION = "pos"           # 位置数据


@dataclass
class ProtocolFrame:
    """
    协议帧结构
    
    【框架预留】可根据实际需求扩展：
    - 帧头/帧尾
    - 校验和
    - 序列号
    """
    cmd: CommandType
    data: Optional[Any] = None
    
    def encode(self) -> bytes:
        """
        编码为字节数据
        
        简单格式: CMD:DATA\n
        """
        if self.data is not None:
            return f"{self.cmd.value}:{self.data}\n".encode('utf-8')
        else:
            return f"{self.cmd.value}\n".encode('utf-8')
    
    @classmethod
    def decode(cls, raw: bytes) -> Optional['ProtocolFrame']:
        """
        从字节数据解码
        
        Args:
            raw: 原始字节数据
            
        Returns:
            解析后的帧，解析失败返回 None
        """
        try:
            text = raw.decode('utf-8').strip()
            if ':' in text:
                cmd_str, data = text.split(':', 1)
            else:
                cmd_str = text
                data = None
            
            cmd = CommandType(cmd_str)
            return cls(cmd=cmd, data=data)
        except (ValueError, UnicodeDecodeError):
            return None


# 便捷函数
def encode(cmd: CommandType, data: Any = None) -> bytes:
    """编码命令"""
    return ProtocolFrame(cmd=cmd, data=data).encode()


def decode(raw: bytes) -> Optional[ProtocolFrame]:
    """解码命令"""
    return ProtocolFrame.decode(raw)


# ==================== 独立测试 ====================
def test_protocol():
    """
    独立测试协议帧
    
    测试编码和解码功能
    """
    print("=" * 50)
    print("串口协议 - 独立测试")
    print("=" * 50)
    print()
    
    # 测试编码
    print("--- 测试编码 ---")
    
    test_cases = [
        (CommandType.DEBUG_ECHO, None),
        (CommandType.DEBUG_ECHO, "hello"),
        (CommandType.DEBUG_STATUS, None),
        (CommandType.DEBUG_STATUS, "mode=pet"),
    ]
    
    encoded_results = []
    for cmd, data in test_cases:
        frame = ProtocolFrame(cmd=cmd, data=data)
        encoded = frame.encode()
        encoded_results.append(encoded)
        print(f"  {frame} -> {encoded}")
    
    print()
    
    # 测试解码
    print("--- 测试解码 ---")
    
    for encoded in encoded_results:
        decoded = ProtocolFrame.decode(encoded)
        print(f"  {encoded} -> {decoded}")
    
    print()
    
    # 测试无效输入
    print("--- 测试无效输入 ---")
    
    invalid_cases = [
        b"invalid_command\n",
        b"\xff\xfe\xfd",
        b"",
        b":",
    ]
    
    for invalid in invalid_cases:
        result = ProtocolFrame.decode(invalid)
        status = "✗ 解析失败（预期）" if result is None else f"? 意外成功: {result}"
        print(f"  {invalid} -> {status}")
    
    print()
    
    # 测试便捷函数
    print("--- 测试便捷函数 ---")
    
    encoded = encode(CommandType.DEBUG_ECHO, "test")
    print(f"  encode(DEBUG_ECHO, 'test') = {encoded}")
    
    decoded = decode(encoded)
    print(f"  decode({encoded}) = {decoded}")
    
    print()
    print("[OK] 协议测试完成")


if __name__ == "__main__":
    test_protocol()
