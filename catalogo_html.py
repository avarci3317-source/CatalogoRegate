#!/usr/bin/env python3
import os
import requests
import pandas as pd
import html
import unicodedata

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILENAME = os.path.join(BASE_DIR, "productos.xlsx")
OUTPUT_HTML = os.path.join(BASE_DIR, "catalogo.html")

STORE_NAME = "TenisFutsalCR"
WHATSAPP_NUMBER = "50671012718"
URL = "https://www.maxsport.com.co/collections/zapatillas-max/products.json"


def normalize_text(s):
    if not isinstance(s, str):
        s = str(s)
    s = s.strip().lower()
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c))


def formatear_precio(valor):
    try:
        return f"{int(float(valor)):,}".replace(",", ".")
    except:
        return valor


def extraer_productos():
    try:
        data = requests.get(URL).json()
    except:
        return []

    productos = []
    for p in data.get("products", []):
        imagenes = []
        for img in p.get("images", []):
            src = img.get("src")
            if src:
                if src.startswith("//"):
                    src = "https:" + src
                imagenes.append(src)

        productos.append({
            "nombre": p.get("title", ""),
            "imagenes": imagenes[:5]
        })
    return productos


def leer_excel():
    if not os.path.exists(EXCEL_FILENAME):
        print("⚠️ No se encontró productos.xlsx")
        return {}

    df = pd.read_excel(EXCEL_FILENAME, dtype=str).fillna("")
    df.columns = df.columns.str.lower().str.strip()

    datos = {}
    for _, row in df.iterrows():
        nombre = normalize_text(row.get("nombre_producto", ""))
        datos[nombre] = {
            "tallas": row.get("tallas", ""),
            "ps": formatear_precio(row.get("precio_sugerido", "")),
            "pm": formatear_precio(row.get("precio_mayorista", ""))
        }
    return datos


def generar_html(productos, datos):

    html_out = f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{STORE_NAME}</title>

<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css"/>

<style>
body{{margin:0;background:#000;color:#fff;font-family:Montserrat}}

header{{position:fixed;top:0;width:100%;background:#111;padding:15px;text-align:center;font-size:28px;font-weight:900;z-index:999}}

.catalogo{{margin-top:90px;display:grid;grid-template-columns:repeat(3,1fr);gap:20px;padding:20px}}

.producto{{background:#111;border-radius:14px;overflow:hidden}}

.swiper{{width:100%;height:300px}}
.swiper img{{width:100%;height:100%;object-fit:cover}}

.zoom-container{{position:relative;overflow:hidden;cursor:zoom-in}}
.zoom-container img{{width:100%;height:100%;object-fit:cover;transition:transform 0.1s ease}}

.info{{padding:15px;text-align:center}}

.ps{{color:#aaa;font-size:14px}}
.pm{{color:#25D366;font-size:20px;font-weight:700}}

.tallas{{font-size:13px;color:#ccc}}

button{{margin-top:10px;padding:12px;width:100%;background:#fff;border:none;font-weight:800;cursor:pointer;border-radius:8px}}

@media(max-width:900px){{
.catalogo{{grid-template-columns:1fr 1fr}}
}}

@media(max-width:600px){{
.catalogo{{grid-template-columns:1fr}}
.swiper{{height:260px}}
}}
</style>
</head>

<body>

<header>{STORE_NAME}</header>

<div class="catalogo">
"""

    contador = 0

    for prod in productos:
        nombre = prod["nombre"]
        norm = normalize_text(nombre)

        if norm in datos:
            d = datos[norm]
            swiper_id = f"swiper-{contador}"

            html_out += f"""
<div class="producto">

<div class="swiper" id="{swiper_id}">
<div class="swiper-wrapper">
"""

            for img in prod["imagenes"]:
                html_out += f"""
<div class="swiper-slide">
  <div class="zoom-container">
    <img src="{img}" 
         onmousemove="zoom(event,this)" 
         onmouseleave="resetZoom(this)">
  </div>
</div>
"""

            html_out += f"""
</div>
<div class="swiper-pagination"></div>
</div>

<div class="info">
<h2>{html.escape(nombre)}</h2>

<div class="ps">Precio: ₡{d['ps']}</div>
<div class="pm">Precio Mayorista: ₡{d['pm']}</div>

<div class="tallas">Tallas: {html.escape(d['tallas'])}</div>

<button onclick="comprar('{html.escape(nombre)}','{d['pm']}','{d['tallas']}')">
Comprar por WhatsApp
</button>

</div>
</div>
"""
            contador += 1

    html_out += f"""
</div>

<script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>

<script>
document.querySelectorAll('.swiper').forEach(el=>{{
new Swiper(el,{{
loop:true,
pagination:{{el:el.querySelector('.swiper-pagination'),clickable:true}},
autoplay:{{delay:2500}}
}});
}});

function zoom(e, img){{
  const rect = img.getBoundingClientRect();

  const x = (e.clientX - rect.left) / rect.width * 100;
  const y = (e.clientY - rect.top) / rect.height * 100;

  img.style.transformOrigin = x + "% " + y + "%";
  img.style.transform = "scale(2)";
}}

function resetZoom(img){{
  img.style.transform = "scale(1)";
}}

function comprar(nombre, precio, tallas){{
let msg = `Hola, quiero este modelo: ${{nombre}}%0APrecio Mayorista: ₡${{precio}}%0ATallas: ${{tallas}}`
window.open("https://wa.me/{WHATSAPP_NUMBER}?text="+msg)
}}
</script>

</body>
</html>
"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_out)

    print("🔥 Catálogo PRO listo (zoom corregido)")


if __name__ == "__main__":
    productos = extraer_productos()
    datos = leer_excel()
    generar_html(productos, datos)
