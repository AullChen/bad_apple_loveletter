"""
    Bad Apple!! Visualizer
    This script implements a visual representation of the "Bad Apple!!" music video using multiple windows.
    It synchronizes the visual frames with the audio playback and adjusts the window positions and sizes accordingly.
"""

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

# Window configuration
WND_CLASS = "BadApple"
MAX_WINDOWS = 155
BASE_WIDTH = 64
BASE_HEIGHT = 48
FUDGE_X = 15
FUDGE_Y = 8

# Playback settings
PLAYBACK_SPEED = 47.0
SYNC_TOLERANCE = 0.01


class WinCoords:
    """Container for window coordinates and dimensions"""
    __slots__ = ('x', 'y', 'w', 'h')

    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h


class DeferredWindow:
    """Window object with deferred updates"""

    def __init__(self, hwnd, x=10, y=10, w=200, h=100):
        self.hwnd = hwnd
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.visible = True

    def set_pos(self, x, y):
        """Set window position"""
        if self.x != x or self.y != y:
            self.x, self.y = x, y
            win32gui.SetWindowPos(
                self.hwnd, None, x, y, 0, 0,
                win32con.SWP_NOZORDER | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
            )

    def set_size(self, w, h):
        """Set window size"""
        if self.w != w or self.h != h:
            self.w, self.h = w, h
            win32gui.SetWindowPos(
                self.hwnd, None, 0, 0, w, h,
                win32con.SWP_NOZORDER | win32con.SWP_NOMOVE | win32con.SWP_NOACTIVATE
            )

    def set_visible(self, visible):
        """Set visibility"""
        if self.visible != visible:
            self.visible = visible
            cmd = win32con.SW_SHOW if visible else win32con.SW_HIDE
            win32gui.ShowWindow(self.hwnd, cmd)


def wnd_proc(hwnd, msg, wparam, lparam):
    """Window message handler"""
    if msg == win32con.WM_CLOSE:
        print("WM_CLOSE received")
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


def register_window_class():
    """Register window class"""
    wc = win32gui.WNDCLASS()
    wc.hInstance = win32api.GetModuleHandle(None)
    wc.lpszClassName = WND_CLASS
    wc.lpfnWndProc = wnd_proc
    wc.hbrBackground = win32gui.CreateSolidBrush(0xFFFFFF)
    win32gui.RegisterClass(wc)


def load_frames():
    """Load frame data"""
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
    # Initialize console
    commandline_gui_helpers.init()

    # Register window class
    register_window_class()

    try:
        # Load frame data
        frames = load_frames()
    except Exception as e:
        print(f"Error loading frames: {e}")
        return

    # Create windows
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

    # Calculate screen adaptation ratio
    screen_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    screen_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    ratio_x = screen_width / BASE_WIDTH
    ratio_y = screen_height / BASE_HEIGHT

    # Initialize audio
    pygame.mixer.init()
    pygame.mixer.music.load(os.path.join("../assets", "bad apple.ogg"))
    start_time = time.time()
    pygame.mixer.music.play()
    time.sleep(3)

    # Main loop
    frame_index = 0
    audio_start = time.time()
    last_frame_time = audio_start
    try:
        while frame_index < len(frames):
            # Handle Windows messages
            win32gui.PumpWaitingMessages()

            audio_elapsed = time.time() - audio_start
            target_frame = int(audio_elapsed * 30 * PLAYBACK_SPEED)
            
            # Sync check
            if abs(frame_index - target_frame) > MAX_WINDOWS * SYNC_TOLERANCE:
                frame_index = target_frame

            # Update window states
            for i in range(MAX_WINDOWS):
                idx = frame_index + i
                if idx >= len(frames):
                    continue

                coords = frames[idx]
                if coords is None:
                    windows[i].set_visible(False)
                    continue

                # Calculate actual position and size
                x = int(coords.x * ratio_x)
                y = int(coords.y * ratio_y)
                w = int(coords.w * ratio_x) + FUDGE_X
                h = int(coords.h * ratio_y) + FUDGE_Y

                windows[i].set_pos(x, y)
                windows[i].set_size(w, h)
                windows[i].set_visible(True)

            # Precise frame rate control
            now = time.time()
            frame_duration = (1 / 30) / PLAYBACK_SPEED
            sleep_time = max(0, frame_duration - (now - last_frame_time))
            time.sleep(sleep_time)
            last_frame_time = now

            frame_index += MAX_WINDOWS
            time.sleep(1/30 - 0.005)

    finally:
        # Clean up resources
        pygame.mixer.quit()
        for window in windows:
            win32gui.DestroyWindow(window.hwnd)


def main():
    """Show letter first then play bad apple"""
    letter_thread = threading.Thread(target=letter.start)
    letter_thread.start()
    time.sleep(37)
    bad_apple()
    letter_thread.join()
    


if __name__ == "__main__":
    main()