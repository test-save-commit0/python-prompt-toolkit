from __future__ import annotations
import sys
assert sys.platform == 'win32'
from ctypes import pointer
from ..utils import SPHINX_AUTODOC_RUNNING
if not SPHINX_AUTODOC_RUNNING:
    from ctypes import windll
from ctypes.wintypes import BOOL, DWORD, HANDLE
from prompt_toolkit.win32_types import SECURITY_ATTRIBUTES
__all__ = ['wait_for_handles', 'create_win32_event']
WAIT_TIMEOUT = 258
INFINITE = -1


def wait_for_handles(handles: list[HANDLE], timeout: int=INFINITE) ->(HANDLE |
    None):
    """
    Waits for multiple handles. (Similar to 'select') Returns the handle which is ready.
    Returns `None` on timeout.
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms687025(v=vs.85).aspx

    Note that handles should be a list of `HANDLE` objects, not integers. See
    this comment in the patch by @quark-zju for the reason why:

        ''' Make sure HANDLE on Windows has a correct size

        Previously, the type of various HANDLEs are native Python integer
        types. The ctypes library will treat them as 4-byte integer when used
        in function arguments. On 64-bit Windows, HANDLE is 8-byte and usually
        a small integer. Depending on whether the extra 4 bytes are zero-ed out
        or not, things can happen to work, or break. '''

    This function returns either `None` or one of the given `HANDLE` objects.
    (The return value can be tested with the `is` operator.)
    """
    arr = (HANDLE * len(handles))(*handles)
    ret = windll.kernel32.WaitForMultipleObjects(
        len(handles),
        arr,
        BOOL(False),
        DWORD(timeout)
    )
    if ret == WAIT_TIMEOUT:
        return None
    else:
        return handles[ret]


def create_win32_event() ->HANDLE:
    """
    Creates a Win32 unnamed Event .
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms682396(v=vs.85).aspx
    """
    sa = SECURITY_ATTRIBUTES()
    sa.nLength = DWORD(sizeof(SECURITY_ATTRIBUTES))
    sa.bInheritHandle = BOOL(True)
    sa.lpSecurityDescriptor = None

    handle = windll.kernel32.CreateEventA(
        pointer(sa),
        BOOL(True),   # Manual reset event
        BOOL(False),  # Initial state = 0
        None          # Unnamed event
    )

    if handle == 0:
        raise WindowsError(windll.kernel32.GetLastError())

    return handle
