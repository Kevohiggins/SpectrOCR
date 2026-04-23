"""
Configuración global de SpectrOCR.
Carga la API key desde settings.json (se pide al usuario la primera vez).
"""

import os
import json

import sys

# Detectar si estamos en un ejecutable de PyInstaller o en Python normal
if getattr(sys, 'frozen', False):
    # Si es el .exe, la base es la carpeta donde vive el .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Si es script, la base es la del archivo config.py
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

def _load_settings():
    settings = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Migrar string simple a lista
    if "api_key" in settings and isinstance(settings["api_key"], str):
        old_value = settings.pop("api_key")
        if old_value:
            settings["api_keys"] = [{"name": "Clave Principal", "key": old_value, "active": True}]
        save_settings(settings)

    # Inyectar defaults faltantes
    if "api_keys" not in settings:
        settings["api_keys"] = []
    
    if "hotkeys" not in settings:
        settings["hotkeys"] = {
            "scan": "ctrl+shift+r",
            "model": "ctrl+shift+m",
            "settings": "ctrl+shift+o",
            "quit": "ctrl+shift+f4"
        }
        
    if "prompts" not in settings:
        settings["prompts"] = []
        
    return settings

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

def get_setting(key, default=None):
    return _load_settings().get(key, default)

def set_setting(key, value):
    settings = _load_settings()
    settings[key] = value
    save_settings(settings)

def get_active_api_key():
    settings = _load_settings()
    for k in settings.get("api_keys", []):
        if k.get("active"):
            return k.get("key", "")
    return ""
    
def get_active_prompts_text():
    settings = _load_settings()
    actives = [p.get("text", "") for p in settings.get("prompts", []) if p.get("active")]
    return "\n\n".join(actives)

ANALYSIS_PROMPT_BASE = """SOS UN ANALIZADOR DE ACCESIBILIDAD PARA WINDOWS. TU TAREA ES MAPEAR LA PANTALLA DE FORMA JERÁRQUICA Y EXHAUSTIVA.

No dejes ninguna zona de la pantalla sin identificar. Estructurá tu respuesta siguiendo este orden lógico:

1. IDENTIFICACIÓN DE CONTENEDORES (ZONAS):
- Identificá las grandes secciones de la interfaz (ej: "Barra de Tareas", "Cinta de Opciones", "Panel Lateral", "Área de Trabajo").
- Para cada sección, creá un elemento con type: "heading_1". Estos NO son clickeables, sirven para organizar el mapa.

2. DESGLOSE DE ELEMENTOS INTERACTIVOS (HIJOS):
- Dentro de cada contenedor, identificá CADA botón, ícono, enlace o campo de forma individual.
- PROHIBIDO AGRUPAR: Si hay 5 íconos en la bandeja del sistema, debés generar 5 elementos individuales. Nunca los pongas como un solo grupo.

3. CAMPOS POR ELEMENTO:
- "label": El nombre literal o funcional (ej: "Configuración", "Batería", "Cerrar"). Sin prefijos.
- "description": Estado visual exacto (ej: "conectado a WiFi Fibertel", "botón presionado", "desplegable cerrado").
- "type": button, text_field, checkbox, slider, link, icon, heading_1, text_block, other.
- "box_2d": [ymin, xmin, ymax, xmax] en escala 0 a 1000. El centro debe caer justo sobre el elemento.
- "actions": Lista de acciones entre ["click", "double_click", "right_click", "drag", "type_text"].

REGLAS DE ORO:
- IDIOMA: Únicamente español.
- FORMATO: Devolvé solo el array JSON. Sin texto introductorio ni explicaciones.
- INTEGRIDAD: Mapeá de arriba hacia abajo y de izquierda a derecha. No omitas ninguna zona visual interactiva.
"""
