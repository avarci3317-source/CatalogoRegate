#!/usr/bin/env python3
# catalogo_html.py
# Genera catalogo.html a partir del JSON de productos y un Excel (productos.xlsx).
# Incluye marcadores claros para: URLs de redes sociales y número de WhatsApp.
# Edita las constantes SOCIAL_LINKS y WHATSAPP_NUMBER más abajo.

import os
import requests
import pandas as pd
import html
import unicodedata

# -------------------------
# CONFIGURACIÓN (edita aquí)
# -------------------------

# Reemplaza las URLs por las de tu tienda (deja vacías si no quieres mostrar alguna)
SOCIAL_LINKS = {
    "facebook": "https://www.facebook.com/profile.php?id=61580491106984",   # <-- AQUI: URL Facebook
    "instagram": "https://www.instagram.com/regate_futstore",# <-- AQUI: URL Instagram
    "twitter": "https://tiktok.com/regate_futstore"          # <-- AQUI: URL Twitter/X
}

# Número de WhatsApp en formato internacional sin + ni espacios (ej: 50612345678)
WHATSAPP_NUMBER = "50670107098"  # <-- AQUI: reemplaza con tu número de WhatsApp

# URL JSON de productos (no es necesario tocar si usas la misma fuente)
URL = "https://www.maxsport.com.co/collections/zapatillas-max/products.json"

# Nombre de la tienda que aparecerá en el header
STORE_NAME = "Regate FutStore"  # <-- Cambia si quieres otro nombre

# Nombre del archivo Excel (colócalo en la misma carpeta)
EXCEL_FILENAME = "productos.xlsx"

# Nombre del archivo HTML de salida
OUTPUT_HTML = "catalogo.html"

# -------------------------
# Funciones auxiliares
# -------------------------

def normalize_text(s):
    """Normaliza texto: strip, lower, quitar acentos."""
    if not isinstance(s, str):
        s = str(s)
    s = s.strip().lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    return s

def extraer_productos(url):
    """Descarga JSON de productos y extrae título e imágenes (máx 3)."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print("Error descargando JSON de productos:", e)
        return []
    productos = []
    for p in data.get("products", []):
        nombre = p.get("title", "").strip()
        imagenes = [img.get("src") for img in p.get("images", [])[:3]] if p.get("images") else []
        productos.append({"nombre": nombre, "imagenes": imagenes})
    return productos

def leer_excel(ruta_excel):
    """
    Lee un Excel con columnas que contengan (insensible a mayúsculas):
    nombre / nombre_producto / Nombre
    precio / Precio
    tallas / Tallas
    Devuelve un diccionario normalizado: {nombre_normalizado: (precio, tallas)}
    """
    if not os.path.exists(ruta_excel):
        print(f"No se encontró el archivo Excel: {ruta_excel}")
        return {}
    df = pd.read_excel(ruta_excel, dtype=str)
    df = df.fillna("")
    cols = {c.lower(): c for c in df.columns}
    col_nombre = None
    for key in ["nombre", "nombre_producto", "name", "producto", "producto_nombre"]:
        if key in cols:
            col_nombre = cols[key]
            break
    col_precio = None
    for key in ["precio", "price", "cost"]:
        if key in cols:
            col_precio = cols[key]
            break
    col_tallas = None
    for key in ["tallas", "talla", "sizes"]:
        if key in cols:
            col_tallas = cols[key]
            break
    if col_nombre is None:
        print("No se encontró columna de nombre en el Excel. Encabezados esperados: Nombre, nombre_producto")
        return {}
    datos = {}
    for _, row in df.iterrows():
        nombre_raw = str(row.get(col_nombre, "")).strip()
        if not nombre_raw:
            continue
        precio_raw = str(row.get(col_precio, "")).strip() if col_precio else ""
        tallas_raw = str(row.get(col_tallas, "")).strip() if col_tallas else ""
        nombre_norm = normalize_text(nombre_raw)
        datos[nombre_norm] = (precio_raw if precio_raw else "N/D", tallas_raw if tallas_raw else "Consultar")
    return datos

def js_escape(s: str) -> str:
    """Escapa comillas simples y barras para literales JS entre comillas simples."""
    return s.replace("\\", "\\\\").replace("'", "\\'")

# -------------------------
# Generación del HTML
# -------------------------

def generar_html(productos, datos_excel, archivo=OUTPUT_HTML):
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    archivo_salida = os.path.join(ruta_actual, archivo)

    # Construcción del HTML (head + estilos)
    html_head = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(STORE_NAME)}</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>
<style>
:root{{--bg:#000;--card:#0f0f0f;--accent:#25D366;--muted:#d0d0d0;--danger:#ff3b3b;--icon-bg: rgba(255,255,255,0.02);--header-height-desktop:90px;--header-height-mobile:110px}}
*{{box-sizing:border-box}}html,body{{height:100%}}body{{margin:0;background:var(--bg);font-family:'Montserrat',sans-serif;color:#fff;-webkit-font-smoothing:antialiased}}
header{{position:fixed;top:0;left:0;width:100%;background:var(--card);display:flex;justify-content:center;align-items:center;padding:12px 18px;z-index:10000;height:var(--header-height-desktop);box-shadow:0 2px 12px rgba(0,0,0,0.6)}}
.header-inner{{width:95%;max-width:1200px;display:flex;justify-content:space-between;align-items:center;gap:12px}}
header h1{{margin:0;color:#fff;font-weight:900;letter-spacing:0.4px;font-size:clamp(20px,2.6vw+12px,36px);line-height:1.05;text-align:left;max-width:62%;overflow-wrap:break-word}}
.header-right{{display:flex;align-items:center;gap:12px;justify-content:flex-end;width:38%}}
.redes{{display:flex;gap:10px;align-items:center}}
.redes a{{color:var(--danger);text-decoration:none;display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;background:var(--icon-bg);font-size:18px}}
#toggleCarrito{{position:relative;background:var(--accent);color:#fff;padding:8px 12px;border-radius:20px;display:flex;align-items:center;gap:8px;font-weight:700;cursor:pointer;box-shadow:0 6px 18px rgba(0,0,0,0.45)}}
#toggleCarrito .badge{{background:var(--danger);color:#fff;font-weight:800;font-size:12px;padding:3px 7px;border-radius:12px;min-width:20px;text-align:center}}
#carrito{{position:fixed;top:calc(var(--header-height-desktop)+8px);right:20px;background:var(--card);border:2px solid var(--accent);padding:12px;width:360px;max-height:68vh;overflow-y:auto;border-radius:10px;transform:translateY(-8px);opacity:0;pointer-events:none;transition:all .18s ease;z-index:9999}}
#carrito.visible{{transform:translateY(0);opacity:1;pointer-events:auto}}
#carrito h3{{margin:0 0 10px;text-align:center;font-weight:800}}
#carrito ul{{list-style:none;padding:0;margin:0}}
#carrito li{{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.03)}}
#carrito .empty{{color:#bbb;text-align:center;padding:12px 0}}
.catalogo{{margin-top:calc(var(--header-height-desktop)+20px);width:95%;margin-left:auto;margin-right:auto;display:flex;flex-wrap:wrap;justify-content:space-around;gap:16px;padding-bottom:80px}}
.producto{{width:30%;background:var(--card);margin:10px;padding:16px;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.6);transition:transform .12s ease}}
.producto:hover{{transform:translateY(-6px)}}
.producto h2{{font-size:18px;color:#fff;text-align:center;margin:8px 0;font-weight:800}}
.producto .precio{{font-size:16px;color:var(--muted);text-align:center;margin:6px 0;font-weight:700}}
.producto .tallas{{font-size:14px;color:var(--muted);text-align:center;margin:6px 0}}
.swiper{{width:100%;height:280px;border-radius:10px;overflow:hidden;background:#000}}
.swiper-slide img{{width:100%;height:100%;object-fit:cover;display:block}}
.swiper-pagination{{bottom:10px!important}}
.boton{{display:flex;align-items:center;justify-content:center;gap:8px;margin:12px auto 0;padding:12px 18px;background:#fff;color:#000;border:none;border-radius:10px;cursor:pointer;font-weight:900;font-size:16px}}
@media (min-width:1200px){{header h1{{font-size:34px}} .redes a{{width:40px;height:40px;font-size:20px}}}}
@media (max-width:1024px){{.producto{{width:45%}}}}
@media (max-width:768px){{
  :root {{--header-height-mobile:110px}}
  header{{height:var(--header-height-mobile);padding:12px 10px}}
  .header-inner{{width:96%;display:flex;flex-direction:column;align-items:center;gap:8px}}
  header h1{{font-size:clamp(18px,5.0vw,30px);text-align:center;max-width:100%;margin:0;padding:0 8px;line-height:1.04;word-break:break-word}}
  .header-right{{width:100%;display:flex;justify-content:center;gap:12px;align-items:center}}
  .redes{{gap:12px}}
  .redes a{{width:56px;height:56px;font-size:26px;border-radius:12px;background:var(--icon-bg);display:flex;align-items:center;justify-content:center}}
  #toggleCarrito{{padding:12px 14px;font-size:18px;border-radius:24px}}
  #toggleCarrito .badge{{min-width:28px;padding:6px 10px;font-size:13px}}
  .catalogo{{margin-top:calc(var(--header-height-mobile)+8px) !important;display:flex !important;flex-direction:column !important;align-items:center !important;gap:16px !important;padding-bottom:120px !important;height:calc(100vh - var(--header-height-mobile)) !important;overflow-y:auto !important;scroll-snap-type:y mandatory !important;-webkit-overflow-scrolling:touch !important;flex-wrap:nowrap !important}}
  .producto{{width:94% !important;padding:16px !important;margin:0 !important;border-radius:14px !important;height:calc(100vh - var(--header-height-mobile) - 80px) !important;min-height:380px !important;max-height:calc(100vh - var(--header-height-mobile) - 60px) !important;display:flex !important;flex-direction:column !important;justify-content:flex-start !important;scroll-snap-align:start !important;box-shadow:0 10px 30px rgba(0,0,0,0.6) !important}}
  .producto h2{{font-size:22px;margin:10px 0 8px}}
  .producto .precio{{font-size:18px}}
  .producto .tallas{{font-size:16px}}
  .swiper{{height:46% !important;border-radius:12px}}
  .boton{{padding:14px 20px;font-size:17px;border-radius:12px;margin-top:auto}}
  #carrito{{width:94% !important;right:2% !important;top:calc(var(--header-height-mobile)+8px) !important;max-height:60vh !important;padding:14px !important;border-radius:14px !important}}
}}
</style>
</head>
<body>

<header>
  <div class="header-inner">
    <h1>{html.escape(STORE_NAME)}</h1>
    <div class="header-right">
      <!-- Redes sociales: coloca aquí las URLs (se rellenan dinámicamente desde Python) -->
      <div class="redes">
        <!-- FACEBOOK -->
        <a id="link-facebook" href="#" title="Facebook" target="_blank" rel="noopener noreferrer"><i class="fab fa-facebook-f"></i></a>
        <!-- INSTAGRAM -->
        <a id="link-instagram" href="#" title="Instagram" target="_blank" rel="noopener noreferrer"><i class="fab fa-instagram"></i></a>
        <!-- TWITTER -->
        <a id="link-twitter" href="#" title="Twitter" target="_blank" rel="noopener noreferrer"><i class="fab fa-twitter"></i></a>
      </div>

      <!-- Botón carrito con badge -->
      <div id="toggleCarrito" title="Ver carrito" aria-label="Ver carrito">
        <span>🛒</span>
        <span class="badge" id="cart-count">0</span>
      </div>
    </div>
  </div>
</header>

<!-- Panel carrito -->
<div id="carrito" aria-hidden="true">
  <button id="cerrarCarrito" aria-label="Cerrar carrito">✖</button>
  <h3>Carrito</h3>
  <ul id="lista-carrito"></ul>
  <div id="carrito-total" style="margin-top:12px;text-align:right;color:#ddd;font-weight:800;"></div>

  <!-- Enlace WhatsApp: href se actualizará desde JS con el número y el mensaje -->
  <a id="whatsapp" href="#" target="_blank" rel="noopener noreferrer" style="display:block;margin-top:12px;padding:12px;background:var(--accent);color:#fff;text-align:center;border-radius:8px;text-decoration:none;font-weight:800;">
    Enviar pedido por WhatsApp
  </a>
</div>

<div class="catalogo" id="catalogo">
"""

    partes = [html_head]
    contador = 0

    # Generar tarjetas solo para los modelos que están en el Excel (comparación normalizada)
    for prod in productos:
        nombre = prod.get("nombre", "")
        nombre_norm = normalize_text(nombre)
        if nombre_norm in datos_excel:
            precio, tallas = datos_excel[nombre_norm]
            nombre_esc = html.escape(nombre)
            precio_esc = html.escape(precio)
            tallas_esc = html.escape(tallas)
            nombre_js = js_escape(nombre_esc)
            precio_js = js_escape(precio_esc)
            tallas_js = js_escape(tallas_esc)
            swiper_id = f"swiper-{contador}"

            bloque = f"""
  <div class="producto">
    <h2>{nombre_esc}</h2>
    <div class="precio">Precio: ₡{precio_esc}</div>
    <div class="tallas">Tallas disponibles: {tallas_esc}</div>
    <div class="swiper" id="{swiper_id}">
      <div class="swiper-wrapper">
"""
            imagenes = prod.get("imagenes", [])
            if imagenes:
                for img in imagenes:
                    img_esc = html.escape(img)
                    bloque += f'        <div class="swiper-slide"><img src="{img_esc}" alt="{nombre_esc}"></div>\n'
            else:
                bloque += '        <div class="swiper-slide" style="display:flex;align-items:center;justify-content:center;background:#222;color:#888;">Sin imagen</div>\n'

            bloque += f"""      </div>
      <div class="swiper-pagination"></div>
    </div>
    <button class="boton" onclick="agregarCarrito('{nombre_js}', '{precio_js}', '{tallas_js}')">🛒 Agregar al carrito</button>
  </div>
"""
            partes.append(bloque)
            contador += 1

    if contador == 0:
        partes.append("""
  <div style="width:100%; text-align:center; padding:40px; color:#ddd;">
    No se encontraron productos que coincidan con el Excel.
  </div>
""")

    # Footer: scripts y lógica JS (incluye actualización de enlaces de redes y WhatsApp)
    html_footer = f"""
</div>

<script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {{
  // Inicializar Swiper para cada contenedor .swiper
  document.querySelectorAll('.swiper').forEach(function(swiperEl) {{
    new Swiper(swiperEl, {{
      loop: true,
      pagination: {{
        el: swiperEl.querySelector('.swiper-pagination'),
        clickable: true
      }},
      autoplay: {{
        delay: 3500,
        disableOnInteraction: false
      }}
    }});
  }});

  // Elementos UI
  const toggleCarrito = document.getElementById('toggleCarrito');
  const carrito = document.getElementById('carrito');
  const cerrarCarrito = document.getElementById('cerrarCarrito');
  const listaCarrito = document.getElementById('lista-carrito');
  const cartCount = document.getElementById('cart-count');
  const carritoTotal = document.getElementById('carrito-total');
  const whatsappEl = document.getElementById('whatsapp');

  // Estado simple del carrito en memoria
  let carritoItems = [];

  function actualizarUICarrito() {{
    listaCarrito.innerHTML = '';
    if (carritoItems.length === 0) {{
      listaCarrito.innerHTML = '<li class="empty">El carrito está vacío</li>';
      carritoTotal.textContent = '';
    }} else {{
      let total = 0;
      carritoItems.forEach(function(it, idx) {{
        const li = document.createElement('li');
        const cont = document.createElement('div');
        cont.style.display = 'flex';
        cont.style.justifyContent = 'space-between';
        cont.style.alignItems = 'center';
        cont.style.width = '100%';

        const spanLeft = document.createElement('span');
        spanLeft.textContent = it.nombre + ' - ₡' + it.precio + ' - ' + it.tallas;
        spanLeft.style.flex = '1';
        spanLeft.style.marginRight = '8px';

        const btn = document.createElement('button');
        btn.textContent = 'Eliminar';
        btn.style.background = '#ff3b3b';
        btn.style.color = '#fff';
        btn.style.border = 'none';
        btn.style.borderRadius = '6px';
        btn.style.padding = '6px 8px';
        btn.style.cursor = 'pointer';
        btn.onclick = function() {{
          carritoItems.splice(idx, 1);
          actualizarUICarrito();
        }};

        cont.appendChild(spanLeft);
        cont.appendChild(btn);
        li.appendChild(cont);
        listaCarrito.appendChild(li);

        const p = parseFloat(it.precio.replace(/[^0-9.-]+/g,""));
        if (!isNaN(p)) total += p;
      }});
      carritoTotal.textContent = 'Total aproximado: ₡' + total;
    }}
    cartCount.textContent = carritoItems.length;
    actualizarWhatsAppLink();
  }}

  // Función para actualizar enlace de WhatsApp con el pedido actual
  // AQUI: modifica WHATSAPP_NUMBER en la parte superior del script Python si necesitas cambiar el número
  function actualizarWhatsAppLink() {{
    const WHATSAPP_NUMBER = "{WHATSAPP_NUMBER}";
    if (!whatsappEl) return;
    if (carritoItems.length === 0) {{
      whatsappEl.href = "#";
      whatsappEl.textContent = "Carrito vacío";
      whatsappEl.classList.add('disabled');
      return;
    }}
    let mensaje = "Pedido desde {html.escape(STORE_NAME)}%0A%0A";
    carritoItems.forEach((it, idx) => {{
      const linea = `${{idx + 1}}. ${{encodeURIComponent(it.nombre)}} - ₡${{encodeURIComponent(it.precio)}} - Tallas: ${{encodeURIComponent(it.tallas)}}`;
      mensaje += linea + "%0A";
    }});
    let total = 0;
    carritoItems.forEach(it => {{
      const p = parseFloat(it.precio.replace(/[^0-9.-]+/g,""));
      if (!isNaN(p)) total += p;
    }});
    if (total > 0) {{
      mensaje += "%0A" + encodeURIComponent("Total aproximado: ₡" + total);
    }}
    const waUrl = `https://wa.me/${{WHATSAPP_NUMBER}}?text=${{mensaje}}`;
    whatsappEl.href = waUrl;
    whatsappEl.target = "_blank";
    whatsappEl.rel = "noopener noreferrer";
    whatsappEl.classList.remove('disabled');
    whatsappEl.textContent = "Enviar pedido por WhatsApp";
  }}

  // Exponer función global para botones "Agregar al carrito"
  window.agregarCarrito = function(nombre, precio, tallas) {{
    carritoItems.push({{ nombre: nombre, precio: precio, tallas: tallas }});
    actualizarUICarrito();
    // abrir carrito automáticamente al agregar
    carrito.classList.add('visible');
    carrito.setAttribute('aria-hidden', 'false');
    if (window.innerWidth <= 768) {{
      setTimeout(() => {{
        window.scrollBy({{ top: 8, behavior: 'smooth' }});
      }}, 150);
    }}
  }};

  // Toggle carrito
  toggleCarrito.addEventListener('click', () => {{
    carrito.classList.toggle('visible');
    carrito.setAttribute('aria-hidden', carrito.classList.contains('visible') ? 'false' : 'true');
  }});
  cerrarCarrito.addEventListener('click', () => {{
    carrito.classList.remove('visible');
    carrito.setAttribute('aria-hidden', 'true');
  }});

  // Inicial UI
  actualizarUICarrito();

  // -----------------------------
  // Rellenar enlaces de redes sociales (AQUI: modifica SOCIAL_LINKS en Python)
  // -----------------------------
  const socialFacebook = "{SOCIAL_LINKS.get('facebook','')}";
  const socialInstagram = "{SOCIAL_LINKS.get('instagram','')}";
  const socialTwitter = "{SOCIAL_LINKS.get('twitter','')}";

  const elFb = document.getElementById('link-facebook');
  const elIg = document.getElementById('link-instagram');
  const elTw = document.getElementById('link-twitter');

  if (elFb && socialFacebook) elFb.href = socialFacebook;
  if (elIg && socialInstagram) elIg.href = socialInstagram;
  if (elTw && socialTwitter) elTw.href = socialTwitter;

}});
</script>

</body>
</html>
"""

    partes.append(html_footer)
    html_final = "".join(partes)

    # Escribir archivo
    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write(html_final)

    print(f"Archivo generado: {archivo_salida} ({contador} productos)")

# -------------------------
# Bloque principal
# -------------------------

if __name__ == "__main__":
    try:
        productos = extraer_productos(URL)
    except Exception as e:
        print("Error al descargar productos:", e)
        productos = []

    ruta_excel = os.path.join(os.path.dirname(os.path.abspath(__file__)), EXCEL_FILENAME)
    datos_excel = leer_excel(ruta_excel)

    generar_html(productos, datos_excel, archivo=OUTPUT_HTML)
