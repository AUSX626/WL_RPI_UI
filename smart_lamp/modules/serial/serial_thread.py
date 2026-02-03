"""
串口通信线程

GPIO14 -> TX (发送)
GPIO15 -> RX (接收)

【框架预留】作为调试接口，具体协议按需实现
"""

import threading
import time
from typing import Callable, Optional
from queue import Queue

try:
    import serial
except ImportError:
    serial = None
    print("[WARN] pyserial 未安装，串口功能不可用")


class SerialThread:
    """
    串口通信线程
    
    使用方法:
        serial_thread = SerialThread(port="/dev/ttyAMA0", baudrate=115200)
        serial_thread.on_receive(lambda data: print(f"收到: {data}"))
        serial_thread.start()
        
        serial_thread.send(b"Hello")
        
        serial_thread.stop()
    """
    
    def __init__(
        self,
        port: str = "/dev/ttyAMA0",
        baudrate: int = 115200,
        timeout: float = 1.0
    ):
        """
        初始化串口线程
        
        Args:
            port: 串口设备路径
            baudrate: 波特率
            timeout: 读取超时时间（秒）
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        
        self._serial: Optional['serial.Serial'] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_receive_callback: Optional[Callable[[bytes], None]] = None
        self._send_queue: Queue = Queue()
        
    def start(self) -> bool:
        """
        启动串口线程
        
        Returns:
            是否成功启动
        """
        if serial is None:
            print("[ERROR] pyserial 未安装，无法启动串口")
            return False
            
        if self._running:
            print("[WARN] 串口线程已在运行")
            return True
        
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            print(f"[OK] 串口已打开: {self.port} @ {self.baudrate}")
        except serial.SerialException as e:
            print(f"[ERROR] 无法打开串口 {self.port}: {e}")
            return False
        
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        
        return True
    
    def stop(self):
        """停止串口线程"""
        self._running = False
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        
        if self._serial and self._serial.is_open:
            self._serial.close()
            print("[OK] 串口已关闭")
        
        self._serial = None
        self._thread = None
    
    def send(self, data: bytes) -> bool:
        """
        发送数据
        
        Args:
            data: 要发送的字节数据
            
        Returns:
            是否成功发送
        """
        if not self._running or not self._serial:
            print("[WARN] 串口未启动，无法发送")
            return False
        
        self._send_queue.put(data)
        return True
    
    def on_receive(self, callback: Callable[[bytes], None]):
        """
        注册接收回调
        
        Args:
            callback: 接收到数据时的回调函数，参数为接收到的字节数据
        """
        self._on_receive_callback = callback
    
    def _run(self):
        """线程主循环"""
        while self._running:
            try:
                # 处理发送队列
                while not self._send_queue.empty():
                    data = self._send_queue.get_nowait()
                    if self._serial and self._serial.is_open:
                        self._serial.write(data)
                        self._serial.flush()
                
                # 读取数据
                if self._serial and self._serial.is_open and self._serial.in_waiting > 0:
                    data = self._serial.read(self._serial.in_waiting)
                    if data and self._on_receive_callback:
                        try:
                            self._on_receive_callback(data)
                        except Exception as e:
                            print(f"[ERROR] 串口接收回调异常: {e}")
                
                # 短暂休眠，避免 CPU 占用过高
                time.sleep(0.01)
                
            except Exception as e:
                print(f"[ERROR] 串口线程异常: {e}")
                time.sleep(0.1)
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running
    
    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._serial is not None and self._serial.is_open


# ==================== 独立测试 ====================
def test_serial_thread():
    """
    独立测试串口线程
    
    测试方式：
    1. 使用真实串口（需要硬件）
    2. 使用回环测试（TX 连接 RX）
    3. 使用 socat 虚拟串口
    
    创建虚拟串口对（Linux）:
        socat -d -d pty,raw,echo=0 pty,raw,echo=0
    """
    import time
    
    print("=" * 50)
    print("串口线程 - 独立测试")
    print("=" * 50)
    print()
    
    # 检查 pyserial
    if serial is None:
        print("[ERROR] pyserial 未安装，请运行: pip install pyserial")
        return
    
    # 选择测试模式
    print("测试模式:")
    print("  1. 模拟模式（无需硬件）")
    print("  2. 真实串口测试")
    print()
    
    choice = input("请选择 [1]: ").strip() or "1"
    
    if choice == "1":
        _test_mock_mode()
    else:
        _test_real_serial()


def _test_mock_mode():
    """模拟模式测试"""
    print("\n--- 模拟模式测试 ---")
    print("测试 SerialThread 的基本功能（不连接真实硬件）\n")
    
    # 支持直接运行和模块运行两种方式
    try:
        from .protocol import CommandType, ProtocolFrame
    except ImportError:
        from protocol import CommandType, ProtocolFrame
    
    # 创建线程（不启动）
    st = SerialThread(port="/dev/ttyAMA0", baudrate=115200)
    print(f"[OK] SerialThread 创建成功")
    print(f"     端口: {st.port}")
    print(f"     波特率: {st.baudrate}")
    print(f"     运行状态: {st.is_running}")
    print(f"     连接状态: {st.is_connected}")
    
    # 测试回调注册
    received_data = []
    def on_receive(data: bytes):
        received_data.append(data)
        print(f"[收到] {data}")
    
    st.on_receive(on_receive)
    print(f"[OK] 回调注册成功")
    
    # 测试协议帧
    print("\n--- 测试协议帧 ---")
    frame = ProtocolFrame(cmd=CommandType.DEBUG_ECHO, data="Hello")
    encoded = frame.encode()
    print(f"编码: {frame} -> {encoded}")
    
    decoded = ProtocolFrame.decode(encoded)
    print(f"解码: {encoded} -> {decoded}")
    
    print("\n[OK] 模拟测试完成")


def _test_real_serial():
    """真实串口测试"""
    import time
    
    print("\n--- 真实串口测试 ---")
    
    # 列出可用串口
    try:
        from serial.tools import list_ports
        ports = list(list_ports.comports())
        if ports:
            print("可用串口:")
            for p in ports:
                print(f"  - {p.device}: {p.description}")
        else:
            print("未检测到可用串口")
    except Exception:
        pass
    
    port = input("\n请输入串口路径 [/dev/ttyAMA0]: ").strip() or "/dev/ttyAMA0"
    baudrate = int(input("请输入波特率 [115200]: ").strip() or "115200")
    
    # 创建并启动
    st = SerialThread(port=port, baudrate=baudrate)
    
    def on_receive(data: bytes):
        try:
            text = data.decode('utf-8')
            print(f"\n[收到] {text.strip()}")
        except UnicodeDecodeError:
            print(f"\n[收到] {data.hex()}")
        print("输入命令 > ", end="", flush=True)
    
    st.on_receive(on_receive)
    
    if not st.start():
        print("启动失败")
        return
    
    print("\n串口已启动，输入内容发送，输入 'quit' 退出")
    print("提示: 如果使用回环测试，发送的内容会原样返回")
    print()
    
    try:
        while True:
            text = input("输入命令 > ")
            if text.lower() == 'quit':
                break
            if text:
                st.send((text + "\n").encode('utf-8'))
    except KeyboardInterrupt:
        pass
    finally:
        st.stop()
        print("\n测试结束")


if __name__ == "__main__":
    test_serial_thread()
