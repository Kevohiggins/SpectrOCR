"""
Módulo de accesibilidad híbrido (Voz + Sonidos).
Utiliza accessible_output2 para conectarse a lectores de pantalla nativos (NVDA, JAWS) o SAPI5,
garantizando lectura no bloqueante nativa.
Incluye winsound para alertas de estado rápidas.
"""

import winsound
import threading

# Intentamos cargar auto de accessible_output2 de forma tolerante a fallos
try:
    from accessible_output2.outputs.auto import Auto
    _speaker = Auto()
except Exception as e:
    print(f"Alerta: No se pudo iniciar accessible_output2. Fallback a print. ({e})")
    _speaker = None

def play_sound(sound_type):
    """
    Reproduce un sonido de sistema sin bloquear.
    'start': Bip inicial de escaneo.
    'success': Bip de escaneo finalizado.
    'error': Bip de error.
    """
    def _play():
        if sound_type == 'start':
            winsound.Beep(800, 150)
        elif sound_type == 'success':
            winsound.Beep(1200, 150)
            winsound.Beep(1600, 200)
        elif sound_type == 'error':
            winsound.Beep(300, 300)
        elif sound_type == 'action':
            winsound.Beep(1000, 100)
            
    threading.Thread(target=_play, daemon=True).start()

def play_startup_sound():
    try:
        winsound.Beep(1000, 150)
        winsound.Beep(1500, 150)
    except:
        pass

def play_shutdown_sound():
    try:
        winsound.Beep(1000, 150)
        winsound.Beep(600, 150)
    except:
        pass

def say(text, interrupt=True):
    """
    Habla usando accessible_output2. Se gestiona en el hardware de voz de forma asíncrona.
    """
    if _speaker:
        _speaker.output(text, interrupt)
    else:
        print(f"VOZ (fallback): {text}")
