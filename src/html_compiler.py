"""
Compilador HTML Semántico.
Convierte el árbol de elementos JSON en una estructura HTML accesible.
Utiliza URLs app:// para transmitir comandos de acciones a Python mediante el motor WebView.
"""

def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")

def generate_html(elements, window_title="Escaneo"):
    html = [
        "<!DOCTYPE html>",
        "<html lang='es'>",
        "<head>",
        "<meta charset='UTF-8'>",
        f"<title>DOM Virtual - {escape_html(window_title)}</title>",
        "<style>",
        """
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1e1e1e; color: #f0f0f0; padding: 20px; font-size: 18px; }
        h1, h2, h3 { color: #ffffff; }
        .action-details { margin: 10px 0; border: 1px solid #444; border-radius: 5px; background-color: #2b2b2b; }
        .action-summary { padding: 10px; cursor: pointer; font-weight: bold; font-size: 18px; color: #66b2ff; background-color: #333; outline: none; list-style-type: none; }
        .action-summary:focus { background-color: #444; color: #ffcc00; outline: 2px solid #ffcc00; }
        .action-menu { padding: 10px; display: flex; flex-direction: column; gap: 8px; border-top: 1px solid #444; background-color: #222; }
        .extra-action { display: block; background-color: #2c3e50; padding: 8px 12px; text-decoration: none; color: #ecf0f1; border-radius: 4px; font-weight: normal; }
        .extra-action:focus { outline: 3px solid #f1c40f; background-color: #34495e; color: #fff; }
        .static { margin: 20px 0 10px 0; border-bottom: 1px solid #555; padding-bottom: 5px; color: #ccc; }
        """
        "</style>",
        "</head>",
        "<body>",
        f"<h1>{escape_html(window_title)}</h1>",
        "<hr>"
    ]
    
    for el in elements:
        label = escape_html(el.get("label", ""))
        desc = escape_html(el.get("description", ""))
        el_type = el.get("type", "other")
        actions = el.get("actions", [])
        elem_id = el.get("id", 0)
        
        # Ignoramos si viene vacío
        if not label: continue
        
        # Combinamos label y descripción para el lector de pantalla
        label_full = f"{label} ({desc})" if desc else label
            
        if el_type == "heading_1":
            html.append(f"<h2 tabindex='0' class='static'>{label_full}</h2>")
        elif el_type == "heading_2":
            html.append(f"<h3 tabindex='0' class='static'>{label_full}</h3>")
        else:
            # Lista de opciones empaquetada en Detalles Contraíbles
            html.append("<details class='action-details'>")
            html.append(f"<summary class='action-summary'>{label_full}</summary>")
            html.append("<div class='action-menu'>")
            
            # Doble clic como acción primaria absoluta (más fiable en Windows)
            html.append(f"<a href='app://action/{elem_id}/double_click' class='extra-action'>✓ Doble Clic (Principal)</a>")
            
            if "right_click" in actions:
                html.append(f"<a href='app://action/{elem_id}/right_click' class='extra-action'>Clic Derecho</a>")
            if "click" in actions:
                html.append(f"<a href='app://action/{elem_id}/click' class='extra-action'>Clic Simple</a>")
            
            # Lógica mejorada de ARRASTRE
            if "drag" in actions:
                if el_type == "slider":
                    # Botonera de porcentajes para sliders
                    html.append("<div style='margin-top:5px; border-top:1px dashed #555; padding-top:5px;'>")
                    html.append("<span style='font-size:12px; color:#aaa;'>Saltar a: </span>")
                    for p in range(0, 101, 10):
                        html.append(f"<a href='app://action/{elem_id}/slider_{p}' class='extra-action' style='padding:2px 5px; font-size:11px;'>{p}%</a>")
                    html.append("</div>")
                else:
                    # Direcciones para elementos genéricos
                    html.append("<div style='margin-top:5px; border-top:1px dashed #555; padding-top:5px;'>")
                    html.append("<span style='font-size:12px; color:#aaa;'>Empujar: </span>")
                    html.append(f"<a href='app://action/{elem_id}/drag_up' class='extra-action'>Arriba ↑</a>")
                    html.append(f"<a href='app://action/{elem_id}/drag_down' class='extra-action'>Abajo ↓</a>")
                    html.append(f"<a href='app://action/{elem_id}/drag_left' class='extra-action'>Izquierda ←</a>")
                    html.append(f"<a href='app://action/{elem_id}/drag_right' class='extra-action'>Derecha →</a>")
                    html.append("</div>")

            if "type_text" in actions:
                html.append(f"<a href='app://action/{elem_id}/type_text' class='extra-action'>Escribir Texto</a>")
                
            html.append("</div>")
            html.append("</details>")
            
    html.append("</body></html>")
    return "\n".join(html)

