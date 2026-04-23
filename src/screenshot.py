"""
Módulo de captura de pantalla.
Captura la ventana activa y devuelve la imagen PIL junto con las coordenadas de la ventana.
"""

import ctypes
import ctypes.wintypes
from PIL import ImageGrab


# --- Win32 API para obtener la ventana activa y su rect ---
user32 = ctypes.windll.user32


def _get_foreground_window_rect():
    """Obtiene el handle y el rectángulo de la ventana activa."""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None, None

    rect = ctypes.wintypes.RECT()
    # DwmGetWindowAttribute para obtener el rect real (sin sombras en Win10/11)
    DWMWA_EXTENDED_FRAME_BOUNDS = 9
    try:
        dwmapi = ctypes.windll.dwmapi
        result = dwmapi.DwmGetWindowAttribute(
            hwnd,
            DWMWA_EXTENDED_FRAME_BOUNDS,
            ctypes.byref(rect),
            ctypes.sizeof(rect),
        )
        if result != 0:
            # Fallback a GetWindowRect
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
    except Exception:
        user32.GetWindowRect(hwnd, ctypes.byref(rect))

    return hwnd, rect


def _get_window_title(hwnd):
    """Obtiene el título de una ventana dado su handle."""
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def capture_active_window():
    """
    Captura la ventana activa del sistema.
    
    Returns:
        tuple: (image, window_info) donde:
            - image: PIL.Image de la captura
            - window_info: dict con 'x', 'y', 'width', 'height', 'title', 'hwnd'
            Retorna (None, None) si falla.
    """
    hwnd, rect = _get_foreground_window_rect()
    if hwnd is None or rect is None:
        return None, None

    left = rect.left
    top = rect.top
    right = rect.right
    bottom = rect.bottom

    # Validar dimensiones
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        return None, None

    # Capturar la región de la pantalla
    try:
        image = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
    except Exception:
        return None, None

    title = _get_window_title(hwnd)

    window_info = {
        "x": left,
        "y": top,
        "width": width,
        "height": height,
        "title": title,
        "hwnd": hwnd,
    }

    return image, window_info
