import os
import requests
import pandas as pd
import html
import unicodedata

# URL de productos (JSON)
URL = "https://www.maxsport.com.co/collections/zapatillas-max/products.json"

def normalize_text(s):
    if not isinstance(s, str):
        s = str(s)
    s = s.strip().lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    return s

def extraer_productos(url):
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    productos = []
    for p in data.get("products", []):
        nombre = p.get("title", "").strip()
        imagenes = [img.get("src") for img in p.get("images", [])[:3]] if p.get("images") else []
        productos.append({
            "nombre": nombre,
            "imagenes": imagenes
        })
    return productos

def leer_excel(ruta_excel):
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
    return s.replace("\\", "\\\\").replace("'", "\\'")

def generar_html(productos, datos_excel, archivo="catalogo.html"):
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    archivo_salida = os.path.join(ruta_actual, archivo)

    html_head = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1"> <!-- clave para responsive -->
<title>Regate Store - Futsal</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>
<style>
:root{
  --bg:#000; --card:#0f0f0f; --accent:#25D366; --muted:#d0d0d0; --danger:#ff3b3b; --icon-bg: rgba(255,255,255,0.02);
  --header-height-desktop: 90px; --header-height-mobile: 140px;
}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--bg);font-family:'Montserrat',sans-serif;color:#fff;-webkit-font-smoothing:antialiased}

/* Header */
header{position:fixed;top:0;left:0;width:100%;background:var(--card);display:flex;justify-content:center;align-items:center;padding:14px 20px;z-index:10000;height:var(--header-height-desktop);box-shadow:0 2px 12px rgba(0,0,0,0.6)}
.header-inner{width:95%;max-width:1200px;display:flex;justify-content:space-between;align-items:center}
header h1{margin:0;font-size:28px;color:#fff;font-weight:900;letter-spacing:0.6px}

/* Right group */
.header-right{display:flex;align-items:center;gap:16px}
.redes{display:flex;gap:12px;align-items:center}
.redes a{color:var(--danger);text-decoration:none;display:flex;align-items:center;justify-content:center;width:40px;height:40px;border-radius:10px;background:var(--icon-bg);transition:transform .12s ease;font-size:20px}
.redes a:hover{transform:translateY(-4px);box-shadow:0 8px 20px rgba(0,0,0,0.6)}

#toggleCarrito{position:relative;background:var(--accent);color:#fff;padding:8px 12px;border-radius:22px;display:flex;align-items:center;gap:8px;font-weight:700;cursor:pointer;box-shadow:0 6px 18px rgba(0,0,0,0.45)}
#toggleCarrito .badge{background:var(--danger);color:#fff;font-weight:800;font-size:12px;padding:3px 7px;border-radius:14px;min-width:22px;text-align:center}

/* Carrito panel */
#carrito{position:fixed;top:calc(var(--header-height-desktop) + 8px);right:20px;background:var(--card);border:2px solid var(--accent);padding:14px;width:380px;max-height:68vh;overflow-y:auto;border-radius:12px;transform:translateY(-8px);opacity:0;pointer-events:none;transition:all .18s ease;z-index:9999}
#carrito.visible{transform:translateY(0);opacity:1;pointer-events:auto}
#carrito h3{margin:0 0 10px;text-align:center;font-weight:800}
#carrito ul{list-style:none;padding:0;margin:0}
#carrito li{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.03)}
#carrito .empty{color:#bbb;text-align:center;padding:12px 0}

/* Catalogo (desktop/tablet default) */
.catalogo{margin-top:calc(var(--header-height-desktop) + 20px);width:95%;margin-left:auto;margin-right:auto;display:flex;flex-wrap:wrap;justify-content:space-around;gap:16px;padding-bottom:80px}

/* Producto tarjeta */
.producto{width:30%;background:var(--card);margin:10px;padding:16px;border-radius:14px;box-shadow:0 8px 24px rgba(0,0,0,0.6);transition:transform .12s ease}
.producto:hover{transform:translateY(-6px)}
.producto h2{font-size:18px;color:#fff;text-align:center;margin:8px 0;font-weight:800}
.producto .precio{font-size:16px;color:var(--muted);text-align:center;margin:6px 0;font-weight:700}
.producto .tallas{font-size:14px;color:var(--muted);text-align:center;margin:6px 0}
.swiper{width:100%;height:280px;border-radius:10px;overflow:hidden;background:#000}
.swiper-slide img{width:100%;height:100%;object-fit:cover;display:block}
.swiper-pagination{bottom:10px!important}
.boton{display:flex;align-items:center;justify-content:center;gap:8px;margin:12px auto 0;padding:12px 18px;background:#fff;color:#000;border:none;border-radius:10px;cursor:pointer;font-weight:900;font-size:16px}

/* Desktop adjustments */
@media (min-width:1200px){ header h1{font-size:30px} .redes a{width:40px;height:40px;font-size:20px} }
@media (max-width:1024px){ .producto{width:45%} }

/* MOBILE: UNA COLUMNA FORZADA + SCROLL SNAP (reglas con !important para evitar override) */
@media (max-width:768px){
  :root { --header-height: var(--header-height-mobile); }
  header{height:var(--header-height-mobile);padding:18px 12px}
  .header-inner{width:96%;flex-direction:column;align-items:center;gap:12px}
  header h1{font-size:44px;line-height:1.02;text-align:center;font-weight:900;letter-spacing:1px}
  .header-right{width:100%;display:flex;justify-content:center;gap:20px}
  .redes{gap:18px}
  .redes a{width:72px;height:72px;font-size:34px;border-radius:14px;background:var(--icon-bg);display:flex;align-items:center;justify-content:center}
  #toggleCarrito{padding:14px 18px;font-size:22px;border-radius:30px;box-shadow:0 12px 30px rgba(0,0,0,0.6)}
  #toggleCarrito .badge{min-width:34px;padding:8px 12px;font-size:14px;border-radius:18px;font-weight:900}

  /* CONTENEDOR: UNA COLUMNA y scroll-snap (forzado) */
  .catalogo{
    margin-top:calc(var(--header-height-mobile) + 10px) !important;
    display:flex !important;
    flex-direction:column !important;
    align-items:center !important;
    gap:18px !important;
    padding-bottom:120px !important;
    height:calc(100vh - var(--header-height-mobile)) !important;
    overflow-y:auto !important;
    scroll-snap-type:y mandatory !important;
    -webkit-overflow-scrolling:touch !important;
    flex-wrap:nowrap !important;
  }

  /* TARJETA: ocupa casi toda la altura visible para mostrar 1 modelo y "peek" del siguiente */
  .producto{
    width:94% !important;
    padding:18px !important;
    margin:0 !important;
    border-radius:16px !important;
    height:calc(100vh - var(--header-height-mobile) - 80px) !important;
    min-height:420px !important;
    max-height:calc(100vh - var(--header-height-mobile) - 60px) !important;
    display:flex !important;
    flex-direction:column !important;
    justify-content:flex-start !important;
    scroll-snap-align:start !important;
    box-shadow:0 12px 36px rgba(0,0,0,0.6) !important;
  }

  .producto h2{font-size:26px;margin:12px 0 8px}
  .producto .precio{font-size:20px}
  .producto .tallas{font-size:18px}

  .swiper{height:48% !important;border-radius:12px}
  .boton{padding:16px 22px;font-size:18px;border-radius:12px;margin-top:auto}

  #carrito{width:94% !important;right:2% !important;top:calc(var(--header-height-mobile) + 8px) !important;max-height:60vh !important;padding:16px !important;border-radius:14px !important}
}

/* Very small devices */
@media (max-width:420px){
  header h1{font-size:52px}
  .redes a{width:80px;height:80px;font-size:36px}
  #toggleCarrito{font-size:24px;padding:16px 20px}
  #toggleCarrito .badge{min-width:36px;padding:8px 14px;font-size:16px}
  .swiper{height:52%}
  .producto h2{font-size:28px}
  .producto .precio{font-size:22px}
  .boton{font-size:20px;padding:18px 24px}
}
</style>
</head>
<body>

<header>
  <div class="header-inner">
    <h1>Regate Store - Futsal</h1>
    <div class="header-right">
      <div class="redes" aria-hidden="false">
        <a href="#" title="Facebook"><i class="fab fa-facebook-f"></i></a>
        <a href="#" title="Instagram"><i class="fab fa-instagram"></i></a>
        <a href="#" title="Twitter"><i class="fab fa-twitter"></i></a>
      </div>
      <div id="toggleCarrito" title="Ver carrito" aria-label="Ver carrito">
        <span>🛒</span>
        <span class="badge" id="cart-count">0</span>
      </div>
    </div>
  </div>
</header>

<div id="carrito" aria-hidden="true">
  <button id="cerrarCarrito" aria-label="Cerrar carrito">✖</button>
  <h3>Carrito</h3>
  <ul id="lista-carrito"></ul>
  <div id="carrito-total" style="margin-top:12px;text-align:right;color:#ddd;font-weight:800;"></div>
  <a id="whatsapp" href="#" target="_blank" style="display:block;margin-top:12px;padding:12px;background:var(--accent);color:#fff;text-align:center;border-radius:8px;text-decoration:none;font-weight:800;">Enviar pedido por WhatsApp</a>
</div>

<div class="catalogo" id="catalogo">
"""
    partes = [html_head]
    contador = 0

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
                    bloque += f'          <div class="swiper-slide"><img src="{img_esc}" alt="{nombre_esc}"></div>\n'
            else:
                bloque += '          <div class="swiper-slide" style="display:flex;align-items:center;justify-content:center;background:#222;color:#888;">Sin imagen</div>\n'

            bloque += f"""        </div>
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

    html_footer = """
</div>

<script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.swiper').forEach(function(swiperEl) {
    new Swiper(swiperEl, {
      loop: true,
      pagination: {
        el: swiperEl.querySelector('.swiper-pagination'),
        clickable: true
      },
      autoplay: {
        delay: 3500,
        disableOnInteraction: false
      }
    });
  });

  const toggleCarrito = document.getElementById('toggleCarrito');
  const carrito = document.getElementById('carrito');
  const cerrarCarrito = document.getElementById('cerrarCarrito');
  const listaCarrito = document.getElementById('lista-carrito');
  const cartCount = document.getElementById('cart-count');
  const carritoTotal = document.getElementById('carrito-total');
  const catalogo = document.getElementById('catalogo');

  let carritoItems = [];

  function actualizarUICarrito() {
    listaCarrito.innerHTML = '';
    if (carritoItems.length === 0) {
      listaCarrito.innerHTML = '<li class="empty">El carrito está vacío</li>';
      carritoTotal.textContent = '';
    } else {
      let total = 0;
      carritoItems.forEach(function(it, idx) {
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
        btn.onclick = function() {
          carritoItems.splice(idx, 1);
          actualizarUICarrito();
        };
        cont.appendChild(spanLeft);
        cont.appendChild(btn);
        li.appendChild(cont);
        listaCarrito.appendChild(li);
        const p = parseFloat(it.precio.replace(/[^0-9.-]+/g,""));
        if (!isNaN(p)) total += p;
      });
      carritoTotal.textContent = 'Total aproximado: ₡' + total;
    }
    cartCount.textContent = carritoItems.length;
  }

  window.agregarCarrito = function(nombre, precio, tallas) {
    carritoItems.push({ nombre: nombre, precio: precio, tallas: tallas });
    actualizarUICarrito();
    carrito.classList.add('visible');
    carrito.setAttribute('aria-hidden', 'false');
    if (window.innerWidth <= 768) {
      setTimeout(() => {
        // pequeño ajuste para mantener "peek" visible
        window.scrollBy({ top: 8, behavior: 'smooth' });
      }, 150);
    }
  };

  toggleCarrito.addEventListener('click', () => {
    carrito.classList.toggle('visible');
    carrito.setAttribute('aria-hidden', carrito.classList.contains('visible') ? 'false' : 'true');
  });

  cerrarCarrito.addEventListener('click', () => {
    carrito.classList.remove('visible');
    carrito.setAttribute('aria-hidden', 'true');
  });

  if (window.innerWidth <= 768) {
    catalogo.style.scrollBehavior = 'smooth';
  }

  actualizarUICarrito();
});
</script>

</body>
</html>
"""
    partes.append(html_footer)
    html_final = "".join(partes)

    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write(html_final)

    print(f"Archivo generado: {archivo_salida} ({contador} productos)")

if __name__ == "__main__":
    try:
        productos = extraer_productos(URL)
    except Exception as e:
        print("Error al descargar productos:", e)
        productos = []
    ruta_excel = os.path.join(os.path.dirname(os.path.abspath(__file__)), "productos.xlsx")
    datos_excel = leer_excel(ruta_excel)
    generar_html(productos, datos_excel, archivo="catalogo.html")
