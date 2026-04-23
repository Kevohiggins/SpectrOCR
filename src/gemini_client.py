"""
Cliente de Gemini API con Structured Outputs.
Envía capturas de pantalla al modelo y recibe JSON estructurado garantizado.
"""

import io
import json
import enum
import re
from typing import Optional

from google import genai
from google.genai import types
from PIL import Image

from config import ANALYSIS_PROMPT_BASE, get_setting, get_active_api_key, get_active_prompts_text


def _init_client():
    """Inicializa el cliente de Gemini con la API key activa del settings."""
    api_key = get_active_api_key()
    if not api_key:
        raise ValueError(
            "API Key no configurada.\n"
            "Abre Settings para agregarla."
        )
    return genai.Client(api_key=api_key)

def validate_api_key(api_key):
    """Verifica si una API key es válida haciendo una llamada ligera al servidor."""
    if not api_key:
        return False, "La clave está vacía."
    
    try:
        # Usamos un cliente temporal
        temp_client = genai.Client(api_key=api_key)
        # Intentamos listar modelos (es gratis y rápido)
        # Solo necesitamos ver que la petición no tire error, con uno alcanza
        for _ in temp_client.models.list(config={'page_size': 1}):
            break
        return True, ""
    except Exception as e:
        msg = str(e).lower()
        if "401" in msg or "invalid" in msg or "unauthorized" in msg:
            return False, "Clave de API inválida o no autorizada."
        elif "quota" in msg:
            # Si el error es de cuota, la clave ES válida
            return True, ""
        else:
            return False, f"Error de conexión: {str(e)}"

# --- Schema para Structured Output ---
ELEMENT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "label": types.Schema(type=types.Type.STRING),
        "type": types.Schema(type=types.Type.STRING),
        "box_2d": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.INTEGER),
            description="[ymin, xmin, ymax, xmax] scaled 0 to 1000",
        ),
        "description": types.Schema(
            type=types.Type.STRING,
            description="Brief visual description: icon appearance, state (e.g. '40% full'), or colors if no text is present."
        ),
        "actions": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
        ),
    },
    required=["label", "type", "box_2d", "actions", "description"],
)

RESPONSE_SCHEMA = types.Schema(
    type=types.Type.ARRAY,
    items=ELEMENT_SCHEMA,
)

def _clean_json_response(text):
    text = text.strip()
    
    # Remover posibles bloques de "thinking" si el modelo los inyecta
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    
    # Si el modelo rodeó el JSON con texto, intentamos encontrar el array [ ... ]
    match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
    if match:
        text = match.group(0)
    
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

def analyze_screenshot(image, window_info):
    client = _init_client()
    model = get_setting("model", "gemini-2.5-flash-lite")

    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    # Ensamblar prompt completo
    final_prompt = ANALYSIS_PROMPT_BASE
    extra_prompts = get_active_prompts_text()
    if extra_prompts:
        final_prompt += "\n\nCRITICAL USER REQUESTS (OVERRIDE DEFAULT LOGIC IF CONFLICTING):\n" + extra_prompts

    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            data=img_bytes.read(),
                            mime_type="image/png",
                        ),
                        types.Part.from_text(text=final_prompt),
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=2048,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
                # Solo aplicar thinking_config si es un modelo de razonamiento explícito
                thinking_config=types.ThinkingConfig(
                    include_thoughts=False,
                    thinking_budget=0
                ) if (hasattr(types, "ThinkingConfig") and "thinking" in str(model).lower()) else None
            ),
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
            print(f"[Gemini ERROR] LÍMITE DE CUOTA: {e}")
            raise ValueError("QUOTA_EXCEEDED")
        print(f"[Gemini ERROR] Error al comunicarse con la API: {e}")
        return []

    raw_text = response.text
    if not raw_text:
        print("[Gemini ERROR] Respuesta vacía del modelo")
        return []

    try:
        elements = json.loads(raw_text)
    except json.JSONDecodeError:
        cleaned = _clean_json_response(raw_text)
        try:
            elements = json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"[Gemini ERROR] No se pudo parsear JSON: {e}")
            print(f"[DEBUG LOG] Respuesta cruda (primeros 500 chars): {raw_text[:500]}")
            return []

    if not isinstance(elements, list):
        return []

    # Map box_2d to absolute screen coordinates
    win_x = window_info.get("x", 0)
    win_y = window_info.get("y", 0)
    win_w = window_info.get("width", 1000)
    win_h = window_info.get("height", 1000)

    for i, elem in enumerate(elements):
        elem["id"] = i + 1
        box = elem.get("box_2d", [])
        
        try:
            if len(box) == 4:
                # Asegurar que sean enteros por si el modelo devuelve strings
                ymin, xmin, ymax, xmax = [int(v) for v in box]
                # Centro relativo en pixels (Volvemos a la matemática simple)
                rel_cx = ((xmin + xmax) / 2) * (win_w / 1000.0)
                rel_cy = ((ymin + ymax) / 2) * (win_h / 1000.0)
                elem["abs_x"] = int(win_x + rel_cx)
                elem["abs_y"] = int(win_y + rel_cy)
                elem["width"] = int((xmax - xmin) * (win_w / 1000.0))
            else:
                raise ValueError("Box malformado")
        except:
            elem["abs_x"] = win_x + (win_w // 2)
            elem["abs_y"] = win_y + (win_h // 2)
            elem["width"] = 0

    return elements
