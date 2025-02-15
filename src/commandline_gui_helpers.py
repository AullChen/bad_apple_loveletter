import ctypes
from ctypes.wintypes import BOOL, DWORD


def init():
    """Attach console for Windows GUI applications"""
    kernel32 = ctypes.WinDLL('kernel32')
    ATTACH_PARENT_PROCESS = 0xFFFFFFFF
    kernel32.AttachConsole.argtypes = [DWORD]
    kernel32.AttachConsole.restype = BOOL
    kernel32.AttachConsole(ATTACH_PARENT_PROCESS)
