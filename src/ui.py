"""
Interfaz WebView para renderizado local de Cursor Virtual.
Abre una ventana usando el motor HTML nativo del sistema operativo incrustado en wxPython,
para que NVDA y otros lectores lo exploren en Modo Navegación (Browse Mode).
"""

import wx
import wx.html2

class BrowserFrame(wx.Frame):
    def __init__(self, action_callback):
        super().__init__(None, title="SpectrOCR - Cursor Virtual", size=(800, 600))
        self.action_callback = action_callback

        sizer = wx.BoxSizer(wx.VERTICAL)
        # Utilizar Edge Chromium backend (el mejor para accesibilidad en Windows actual)
        try:
            self.browser = wx.html2.WebView.New(self, backend=wx.html2.WEBVIEW_BACKEND_EDGE)
        except Exception:
            # Fallback en caso de que Edge falte (raro en Win10/11)
            self.browser = wx.html2.WebView.New(self)
            
        sizer.Add(self.browser, 1, wx.EXPAND)
        self.SetSizer(sizer)

        # Vincular intercepción de clics
        self.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self.on_navigate, self.browser)
        
        # Cerrar esconde la ventana en lugar de destruirla del todo si queremos reciclarla
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def load_html(self, html_content):
        # El WebView requiere establecer el contenido mediante string
        self.browser.SetPage(html_content, "")
        if self.IsIconized():
            self.Iconize(False)
        self.Show()
        self.Raise()
        
        # Forzar violento del foco de Windows para apps en segundo plano
        import ctypes
        hwnd = self.GetHandle()
        ctypes.windll.user32.AllowSetForegroundWindow(-1)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        
        self.browser.SetFocus()

    def on_navigate(self, event):
        url = event.GetURL()
        # Escuchamos el esquema que inyectamos en html_compiler
        if url.startswith("app://action/"):
            event.Veto() # detiene el intento de abrir página
            
            parts = url.replace("app://action/", "").split("/")
            if len(parts) >= 2:
                elem_id = int(parts[0])
                action_name = parts[1]
                
                # Cerrar y reportar la acción al sistema primario (main)
                self.Hide()
                self.action_callback(elem_id, action_name)
        else:
            # URLs normales o setup base, dejar correr
            event.Skip()

    def on_close(self, event):
        event.Veto()
        self.Hide()
        # Liberar foco al sistema


import urllib.parse
import json
from config import get_setting, set_setting, _load_settings, save_settings
from gemini_client import validate_api_key
import json
import urllib.parse
import speech

class SettingsBrowserFrame(wx.Frame):
    def __init__(self, rebuild_hotkeys_callback):
        super().__init__(None, title="SpectrOCR - Configuración", size=(900, 700))
        self.rebuild_hotkeys_callback = rebuild_hotkeys_callback

        sizer = wx.BoxSizer(wx.VERTICAL)
        try:
            self.browser = wx.html2.WebView.New(self, backend=wx.html2.WEBVIEW_BACKEND_EDGE)
        except Exception:
            self.browser = wx.html2.WebView.New(self)
            
        sizer.Add(self.browser, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self.on_navigate, self.browser)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
    def load_html(self, html_content):
        self.browser.SetPage(html_content, "")
        if self.IsIconized():
            self.Iconize(False)
        self.Show()
        self.Raise()
        import ctypes
        hwnd = self.GetHandle()
        ctypes.windll.user32.AllowSetForegroundWindow(-1)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        self.browser.SetFocus()

    def on_navigate(self, event):
        url = event.GetURL()
        if url.startswith("app://settings/"):
            event.Veto() 
            parsed = urllib.parse.urlparse(url)
            action = parsed.path.strip("/")
            qs = urllib.parse.parse_qs(parsed.query)
            
            if action == "save_all":
                data_json = qs.get("data", ["{}"])[0]
                try:
                    new_settings = json.loads(data_json)
                    
                    # Validar la API Key activa antes de guardar
                    active_key = ""
                    for k in new_settings.get("api_keys", []):
                        if k.get("active"):
                            active_key = k.get("key")
                            break
                    
                    if active_key:
                        with wx.BusyCursor():
                            valid, err = validate_api_key(active_key)
                        if not valid:
                            wx.MessageBox(f"La clave activa no es válida:\n{err}", "Error de API", wx.OK | wx.ICON_WARNING)
                            return

                    save_settings(new_settings)
                    
                    speech.play_sound('action')
                    speech.say("Ajustes guardados correctamente.")
                    
                    # Cerrar la ventana como pidió el usuario
                    self.Hide()
                    
                    # Reconstruir los atajos con la nueva config
                    self.rebuild_hotkeys_callback()
                except Exception as e:
                    print("Error al guardar ajustes:", e)
                    speech.play_sound('error')
                    speech.say("Hubo un problema al intentar guardar los cambios.")
                
        elif url.startswith("http"):
            event.Veto()
            import webbrowser
            webbrowser.open(url)
        else:
            event.Skip()

    def on_close(self, event):
        event.Veto()
        self.Hide()

class WelcomeBrowserFrame(wx.Frame):
    def __init__(self, on_finish_callback):
        super().__init__(None, title="Configuración Inicial de SpectrOCR", size=(700, 600), style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        self.on_finish_callback = on_finish_callback
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        # Utilizar Edge Chromium backend
        try:
            self.browser = wx.html2.WebView.New(self, backend=wx.html2.WEBVIEW_BACKEND_EDGE)
        except Exception:
            self.browser = wx.html2.WebView.New(self)
            
        sizer.Add(self.browser, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        self.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self.on_navigate, self.browser)
        self.Bind(wx.html2.EVT_WEBVIEW_NEWWINDOW, self.on_new_window, self.browser)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Center()

    def load_html(self, html_content):
        self.browser.SetPage(html_content, "")
        self.Show()
        self.Raise()
        self.browser.SetFocus()

    def on_navigate(self, event):
        url = event.GetURL()
        if url.startswith("app://welcome/save"):
            event.Veto()
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            
            name = qs.get("name", ["Clave Principal"])[0]
            key = qs.get("key", [""])[0]
            
            if key:
                # Validar antes de guardar
                with wx.BusyCursor():
                    is_valid, err = validate_api_key(key)
                
                if not is_valid:
                    wx.MessageBox(f"La clave de API no es válida:\n{err}\n\nRevisala y volvé a intentar.", "Error de Configuración", wx.OK | wx.ICON_WARNING)
                    return

                settings = _load_settings()
                settings["api_keys"] = [{"name": name, "key": key, "active": True}]
                save_settings(settings)
                
                speech.play_sound('action')
                speech.say("Bienvenido a SpectrOCR. Configuración guardada.")
                self.on_finish_callback(True)
                self.Destroy() 
        elif url.startswith("http"):
            event.Veto()
            import webbrowser
            webbrowser.open(url)
        else:
            event.Skip()

    def on_new_window(self, event):
        url = event.GetURL()
        if url.startswith("http"):
            import webbrowser
            webbrowser.open(url)
        event.Veto() # Evitar que se abra una ventana interna

    def on_close(self, event):
        # Si cierran sin guardar en la primera ejecución, cerrar la app
        self.on_finish_callback(False)
        self.Destroy()

