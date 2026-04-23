"""
Controlador de mouse.
Ejecuta acciones de clic, doble clic, clic derecho y arrastre en las posiciones
indicadas por Gemini.
"""

import time
import pyautogui

# Configurar pyautogui
pyautogui.FAILSAFE = False  
pyautogui.PAUSE = 0.05

def _safe_coords(element):
    """Obtiene coordenadas seguras para cualquier acción de mouse."""
    w, h = pyautogui.size()
    x = max(2, min(w - 2, int(element.get("abs_x", w // 2))))
    y = max(2, min(h - 2, int(element.get("abs_y", h // 2))))
    return x, y

def click_element(element):
    """Hace clic izquierdo en el centro del elemento."""
    x, y = _safe_coords(element)
    pyautogui.click(x, y)

def double_click_element(element):
    """Hace doble clic en el centro del elemento."""
    x, y = _safe_coords(element)
    pyautogui.doubleClick(x, y)

def right_click_element(element):
    """Hace clic derecho en el centro del elemento."""
    x, y = _safe_coords(element)
    pyautogui.rightClick(x, y)

def drag_slider(element, percentage):
    """Arrastra un slider a una posición porcentual."""
    percentage = max(0, min(100, percentage))
    start_x, start_y = _safe_coords(element)
    elem_width = element.get("width", 100)
    left_edge = start_x - elem_width // 2
    target_x = left_edge + int(elem_width * percentage / 100)
    
    pyautogui.moveTo(start_x, start_y)
    time.sleep(0.1)
    pyautogui.mouseDown()
    time.sleep(0.05)
    pyautogui.moveTo(target_x, start_y, duration=0.2)
    pyautogui.mouseUp()

def drag_element(element, offset_x, offset_y):
    """Arrastra un elemento por un offset dado."""
    start_x, start_y = _safe_coords(element)
    pyautogui.moveTo(start_x, start_y)
    time.sleep(0.1)
    pyautogui.mouseDown()
    time.sleep(0.05)
    pyautogui.moveTo(start_x + offset_x, start_y + offset_y, duration=0.2)
    pyautogui.mouseUp()

def move_to_element(element):
    """Mueve el mouse al centro del elemento sin hacer clic."""
    x, y = _safe_coords(element)
    pyautogui.moveTo(x, y)

