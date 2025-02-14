# main.py
import win32con
import win32gui
import win32api
import pygame
import time
import struct
import os
import threading
import commandline_gui_helpers
import letter



# 窗口配置
WND_CLASS = "BadApple"
MAX_WINDOWS = 155
BASE_WIDTH = 64
BASE_HEIGHT = 48
FUDGE_X = 15  # 窗口尺寸修正值
FUDGE_Y = 8

# 播放设置
PLAYBACK_SPEED = 47.0  # 1.0 = 正常速度，0.5 = 半速，2.0 = 双倍速
SYNC_TOLERANCE = 0.01  # 音视频同步容差（秒）


class WinCoords:
    """窗口坐标和尺寸容器"""
    __slots__ = ('x', 'y', 'w', 'h')

    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h


class DeferredWindow:
    """延迟更新的窗口对象"""

    def __init__(self, hwnd, x=10, y=10, w=200, h=100):
        self.hwnd = hwnd
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.visible = True

    def set_pos(self, x, y):
        """设置窗口位置"""
        if self.x != x or self.y != y:
            self.x, self.y = x, y
            win32gui.SetWindowPos(
                self.hwnd, None, x, y, 0, 0,
                win32con.SWP_NOZORDER | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
            )

    def set_size(self, w, h):
        """设置窗口尺寸"""
        if self.w != w or self.h != h:
            self.w, self.h = w, h
            win32gui.SetWindowPos(
                self.hwnd, None, 0, 0, w, h,
                win32con.SWP_NOZORDER | win32con.SWP_NOMOVE | win32con.SWP_NOACTIVATE
            )

    def set_visible(self, visible):
        """设置可见性"""
        if self.visible != visible:
            self.visible = visible
            cmd = win32con.SW_SHOW if visible else win32con.SW_HIDE
            win32gui.ShowWindow(self.hwnd, cmd)


def wnd_proc(hwnd, msg, wparam, lparam):
    """窗口消息处理"""
    if msg == win32con.WM_CLOSE:
        print("WM_CLOSE received")
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


def register_window_class():
    """注册窗口类"""
    wc = win32gui.WNDCLASS()
    wc.hInstance = win32api.GetModuleHandle(None)
    wc.lpszClassName = WND_CLASS
    wc.lpfnWndProc = wnd_proc
    wc.hbrBackground = win32gui.CreateSolidBrush(0xFFFFFF)
    win32gui.RegisterClass(wc)


def load_frames():
    """加载帧数据"""
    path = os.path.join("../assets", "boxes.bin")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required data file {path} missing!")

    with open(path, "rb") as f:
        data = f.read()

    frames = []
    for i in range(0, len(data), 4):
        if i + 4 > len(data):
            break
        x, y, w, h = struct.unpack('4B', data[i:i+4])
        if w == 0 or h == 0:
            frames.append(None)
        else:
            frames.append(WinCoords(x, y, w, h))
    return frames


def bad_apple():
    # 初始化控制台
    commandline_gui_helpers.init()

    # 注册窗口类
    register_window_class()

    try:
        # 加载帧数据
        frames = load_frames()
    except Exception as e:
        print(f"Error loading frames: {e}")
        return

    # 创建窗口
    windows = []
    for _ in range(MAX_WINDOWS):
        hwnd = win32gui.CreateWindowEx(
            win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW,
            WND_CLASS,
            "Bad Apple!!",
            win32con.WS_OVERLAPPEDWINDOW,
            10, 10, 200, 100,
            None, None, None, None
        )
        windows.append(DeferredWindow(hwnd))

    # 计算屏幕适配比例
    screen_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    screen_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    ratio_x = screen_width / BASE_WIDTH
    ratio_y = screen_height / BASE_HEIGHT

    # 初始化音频
    pygame.mixer.init()
    pygame.mixer.music.load(os.path.join("../assets", "bad apple.ogg"))
    start_time = time.time()
    pygame.mixer.music.play()
    time.sleep(3)

    # 主循环
    frame_index = 0
    audio_start = time.time()
    last_frame_time = audio_start
    try:
        while frame_index < len(frames):
            # 处理Windows消息
            win32gui.PumpWaitingMessages()

            # 计算经过的音频时间
            audio_elapsed = time.time() - audio_start
            
            # 计算目标视频帧（根据速度调整）
            target_frame = int(audio_elapsed * 30 * PLAYBACK_SPEED)
            
            # 同步检查
            if abs(frame_index - target_frame) > MAX_WINDOWS * SYNC_TOLERANCE:
                frame_index = target_frame  # 强制同步

            # 更新窗口状态
            for i in range(MAX_WINDOWS):
                idx = frame_index + i
                if idx >= len(frames):
                    continue

                coords = frames[idx]
                if coords is None:
                    windows[i].set_visible(False)
                    continue

                # 计算实际位置和尺寸
                x = int(coords.x * ratio_x)
                y = int(coords.y * ratio_y)
                w = int(coords.w * ratio_x) + FUDGE_X
                h = int(coords.h * ratio_y) + FUDGE_Y

                windows[i].set_pos(x, y)
                windows[i].set_size(w, h)
                windows[i].set_visible(True)

            # 精确帧率控制
            now = time.time()
            frame_duration = (1 / 30) / PLAYBACK_SPEED
            sleep_time = max(0, frame_duration - (now - last_frame_time))
            time.sleep(sleep_time)
            last_frame_time = now

            frame_index += MAX_WINDOWS
            time.sleep(1/30 - 0.005)  # 补偿处理时间

    finally:
        # 清理资源
        pygame.mixer.quit()
        for window in windows:
            win32gui.DestroyWindow(window.hwnd)


def main():
    letter_thread = threading.Thread(target=letter.start)
    letter_thread.start()
    time.sleep(37)
    bad_apple()
    letter_thread.join()  # 等待 letter.start() 完成
    


if __name__ == "__main__":
    main()
