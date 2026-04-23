# SpectrOCR

SpectrOCR es una herramienta de accesibilidad desarrollada en Python que utiliza Inteligencia Artificial para dar vista a lo inaccesible. Captura ventanas de aplicaciones que no son compatibles con lectores de pantalla y las transforma en una interfaz web virtual perfectamente navegable.

Creditos: Este proyecto es una alternativa personal inspirada en el flujo de trabajo de Viewpoint, desarrollado por Nibble Nerds.

---

## Funcionalidades Principales

* IA de Google (Gemini): Utiliza modelos optimizados (Lite) para procesar capturas de pantalla y reconocer elementos de interfaz.
* Navegacion Web Virtual: Genera una capa transparente donde el usuario puede navegar con el cursor virtual (flechas, H para encabezados, etc.).
* Interaccion Real: Al presionar Enter sobre un elemento detectado, el programa realiza el clic (izquierdo, derecho o doble) en la aplicación original.
* Salida de Voz: Integrado con accessible-output2 para una respuesta inmediata con NVDA, Jieshuo o cualquier lector compatible.

---

## Atajos de Teclado Globales

* Control + Shift + R: Escanear ventana actual.
* Control + Shift + M: Rotar entre modelos de IA (Gemini Lite).
* Control + Shift + O: Configuracion (Claves API y Atajos).
* Control + Shift + H: Abrir manual de usuario.
* Control + Shift + F4: Cerrar SpectrOCR.

---

## Nota Importante: Cortina de Pantalla
Si utilizas la Cortina de Pantalla (Screen Curtain) activa, la IA recibira una imagen vacia y podria alucinar elementos inexistentes. Se recomienda desactivarla brevemente durante el escaneo para obtener resultados precisos.

---

## Instalacion para Desarrolladores

1. Clona el repositorio:
   git clone https://github.com/KevOHiggins/SpectrOCR.git
2. Instala las dependencias:
   pip install -r requirements.txt
3. Ejecuta el programa principal.

---

## Apoyo al Proyecto
Si esta herramienta te resulta util, podes colaborar para mantener las APIs de IA:

* PayPal: https://www.paypal.com/paypalme/KevOHiggins
* Mercado Pago (Argentina): https://link.mercadopago.com.ar/kevohiggins

SpectrOCR - 2026