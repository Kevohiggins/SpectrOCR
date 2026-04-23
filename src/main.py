"""
Punto de entrada principal para el Cursor Virtual HTML.
Utiliza wx.html2 para generar el DOM semántico interceptable de forma oculta y nativa.
Desaparecen las combinaciones tediosas de control flechas, dejando que NVDA lea natural.
"""

import sys
import os
import threading
import time
import wx
import webbrowser
import ctypes
from pynput import keyboard as pynput_keyboard

from config import get_setting, set_setting, get_active_api_key, _load_settings, save_settings
from screenshot import capture_active_window
from gemini_client import analyze_screenshot
from html_compiler import generate_html
from ui import BrowserFrame, SettingsBrowserFrame, WelcomeBrowserFrame
import mouse_controller
import speech
import settings_ui


class AccessibleOCRApp(wx.App):
    def OnInit(self):
        self._scanning = False
        self._elements = []
        
        # Crear los frames (inicialmente ocultos)
        self.frame = BrowserFrame(self.on_browser_action)
        self.settings_frame = SettingsBrowserFrame(self.rebind_hotkeys)
        
        # Listener de hotkeys de pynput
        self.hotkey_listener = None
        
        # Evitar que la app se cierre al ocultar ventanas
        self.SetExitOnFrameDelete(False)
        
        api_key = get_active_api_key()
        if not api_key:
            # Primera ejecución: Mostrar Bienvenida Web
            import welcome_ui
            self.welcome_frame = WelcomeBrowserFrame(self.on_welcome_finish)
            self.welcome_frame.load_html(welcome_ui.generate_welcome_html())
        else:
            self.start_normal_operation()
            
        return True

    def on_welcome_finish(self, success):
        if success:
            # Continuar normalmente, pero fuera del flujo del evento para evitar bloqueos
            wx.CallAfter(self.start_normal_operation)
        else:
            # Cerrado sin configurar, salir por completo
            wx.CallAfter(self.ExitMainLoop)

    def start_normal_operation(self):
        # Iniciar listener de hotkeys
        self.init_hotkeys()
        speech.play_startup_sound()
        speech.say("¡Bienvenido a SpectrOCR!")

    def shutdown(self):
        speech.play_shutdown_sound()
        time.sleep(0.4)
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        os._exit(0)

    def init_hotkeys(self):
        self.rebind_hotkeys()

    def _to_pynput_str(self, hk_str):
        """Convierte 'ctrl+shift+r' a '<ctrl>+<shift>+r' para pynput."""
        parts = hk_str.lower().split('+')
        new_parts = []
        for p in parts:
            p = p.strip()
            # En pynput, tanto los modificadores como las teclas especiales 
            # (F1-F12, space, etc) deben ir entre <> si tienen nombre largo.
            if len(p) > 1:
                new_parts.append(f"<{p}>")
            else:
                new_parts.append(p)
        return "+".join(new_parts)

    def rebind_hotkeys(self):
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        
        from config import _load_settings
        hotkeys = _load_settings().get("hotkeys", {})
        
        # Definir el mapa de funciones
        def on_press(func):
            return lambda: wx.CallAfter(func)

        def on_scan():
            threading.Thread(target=self._scan, daemon=True).start()

        hk_map = {
            self._to_pynput_str(hotkeys.get("scan", "ctrl+shift+r")): on_scan,
            self._to_pynput_str(hotkeys.get("model", "ctrl+shift+m")): on_press(self.toggle_model),
            self._to_pynput_str(hotkeys.get("settings", "ctrl+shift+o")): on_press(self.open_settings),
            self._to_pynput_str(hotkeys.get("manual", "ctrl+shift+h")): on_press(self.open_manual),
            self._to_pynput_str(hotkeys.get("quit", "ctrl+shift+f4")): on_press(self.shutdown)
        }
        
        try:
            self.hotkey_listener = pynput_keyboard.GlobalHotKeys(hk_map)
            self.hotkey_listener.start()
        except Exception as e:
            print(f"Error al iniciar hotkeys: {e}")

    def open_settings(self):
        # Cargar los ajustes actuales antes de mostrar la ventana
        self.settings_frame.load_html(settings_ui.generate_settings_html())
        self.settings_frame.Show()
        self.settings_frame.Raise()
        speech.say("Abriendo ajustes.")

    def open_manual(self):
        from config import BASE_DIR
        # Intentar en la raíz y en _internal (por el layout de PyInstaller)
        paths = [
            os.path.join(BASE_DIR, "manual.html"),
            os.path.join(BASE_DIR, "_internal", "manual.html")
        ]
        
        found_path = None
        for p in paths:
            if os.path.exists(p):
                found_path = p
                break
        
        if found_path:
            webbrowser.open(f'file:///{found_path}')
            speech.say("Abriendo manual de usuario.")
        else:
            speech.say("No se encontró el archivo del manual.")

    def on_browser_action(self, elem_id, action_name):
        """Callback llamado cuando el usuario aprieta un botón en la ventana web virtual."""
        speech.play_sound('action')
        
        # Buscar el elemento en nuestra memoria 
        target_el = None
        for el in self._elements:
            if el.get("id") == elem_id:
                target_el = el
                break
                
        if not target_el: return
        
        # Lanzar en segundo plano para que wxWidgets termine de cerrar la UI real instantáneamente
        def _execute():
            # Damos 400ms para asegurar que el sistema operativo reasigne el foco limpio a la app de fondo
            time.sleep(0.4)
            try:
                if action_name == "click":
                    mouse_controller.click_element(target_el)
                elif action_name == "double_click":
                    mouse_controller.double_click_element(target_el)
                elif action_name == "right_click":
                    mouse_controller.right_click_element(target_el)
                elif action_name.startswith("slider_"):
                    # Extraer el porcentaje del comando (ej: slider_50 -> 50)
                    try:
                        percent = int(action_name.split("_")[1])
                        mouse_controller.drag_slider(target_el, percent)
                    except: pass
                elif action_name == "drag_up":
                    mouse_controller.drag_element(target_el, 0, -150)
                elif action_name == "drag_down":
                    mouse_controller.drag_element(target_el, 0, 150)
                elif action_name == "drag_left":
                    mouse_controller.drag_element(target_el, -150, 0)
                elif action_name == "drag_right":
                    mouse_controller.drag_element(target_el, 150, 0)
                elif action_name == "type_text":
                    mouse_controller.click_element(target_el)
            except Exception as e:
                speech.say("Fallo crítico en puntero de mouse.")
                print(f"Error en acción de mouse: {e}")
                
        threading.Thread(target=_execute, daemon=True).start()

    def _scan(self):
        if self._scanning: return
        self._scanning = True
        
        speech.play_sound('start')

        try:
            image, window_info = capture_active_window()
            if image is None:
                speech.say("Error, ventana no capturada.")
                speech.play_sound('error')
                return

            elements = analyze_screenshot(image, window_info)

            if not elements:
                speech.play_sound('error')
                speech.say("Listado vacío. Intentá de nuevo.")
                return

            speech.play_sound('success')
            self._elements = elements
            
            # Traducir los elementos json a una página web DOM en caliente
            title = window_info.get("title", "Ventana Anónima")
            html = generate_html(elements, title)
            
            # Cargar y despertar la ventana (debe hacerse a través del hilo UI de WX)
            wx.CallAfter(self.frame.load_html, html)
            speech.say("Cursor virtual listo. Navege todo.")
            
        except ValueError as ve:
            if str(ve) == "QUOTA_EXCEEDED":
                speech.play_sound('error')
                speech.say("Alcanzaste tu límite. Probá con otro modelo o intentá más tarde.")
            else:
                print("Error:", ve)
                speech.play_sound('error')
        except Exception as e:
            print("Error fatal de análisis:", e)
            speech.play_sound('error')
        finally:
            self._scanning = False

    def toggle_model(self):
        self.models = [
            "gemini-2.5-flash-lite",
            "gemini-3.1-flash-lite-preview"
        ]
        current = get_setting("model", "gemini-2.5-flash-lite")
        if current in self.models:
            idx = (self.models.index(current) + 1) % len(self.models)
        else:
            idx = 0
            
        new_model = self.models[idx]
        set_setting("model", new_model)
        
        # Sonido de cambio de engranaje para diferenciar el modelo
        speech.play_sound('action')
        name_spoken = new_model.replace("gemini-", "").replace("-", " ")
        speech.say(f"Modelo cambiado a: {name_spoken}")


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    import os
    # Obtenemos la ruta absoluta del script actual
    script = os.path.abspath(sys.argv[0])
    # Preparamos los argumentos con comillas por si hay espacios
    params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
    
    try:
        # Re-lanza usando la ruta absoluta del script y los parámetros originales
        # sys.executable apunta al python.exe (ya sea del sistema o del venv)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        return True
    except Exception as e:
        print(f"Error al intentar elevar privilegios: {e}")
        return False

def main():
    # Verificar si somos admin
    if not is_admin():
        if run_as_admin():
            sys.exit(0)
        else:
            # Si el usuario cancela el UAC, avisar o cerrar
            print("Se requieren permisos de administrador.")
            sys.exit(1)
            
    app = AccessibleOCRApp(False)
    app.MainLoop()

if __name__ == "__main__":
    main()
