import os
import requests
import pandas as pd
import html
import unicodedata

# URL de productos (JSON)
URL = "https://www.maxsport.com.co/collections/zapatillas-max/products.json"

def normalize_text(s):
    """Normaliza texto: strip, lower, quitar acentos."""
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

def generar_html(productos, datos_excel, archivo="catalogo.html"):
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    archivo_salida = os.path.join(ruta_actual, archivo)

    html_head = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Regate Store - Futsal</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>
<style>
body { margin:0; background:#000; font-family:'Montserrat', sans-serif; color:#fff; }

/* Header fijo y centrado de iconos */
header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background: #111;
  display: flex;
  justify-content: center; /* centrar contenido horizontalmente */
  align-items: center;
  padding: 10px 20px;
  z-index: 10000;
  box-shadow: 0 2px 10px rgba(255,255,255,0.08);
}

/* Contenedor interno para distribuir título y controles */
.header-inner {
  width: 95%;
  max-width: 1200px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

header h1 { margin: 0; font-size: 24px; color: #fff; text-align:left; }

/* Agrupar iconos y carrito y centrar verticalmente */
.header-right {
  display:flex;
  align-items:center;
  gap:16px;
}

/* Iconos de redes centrados y en rojo */
.redes {
  display: flex;
  gap: 12px;
  align-items: center;
}
.redes a {
  color: red;
  font-size: 20px;
  text-decoration: none;
  display:flex;
  align-items:center;
  justify-content:center;
  width:34px;
  height:34px;
  border-radius:6px;
}

/* Badge contador en el carrito */
#toggleCarrito {
  position: relative;
  background: #25D366;
  color: #fff;
  padding: 8px 12px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 18px;
  box-shadow: 0 0 8px rgba(0,0,0,0.4);
  display:flex;
  align-items:center;
  gap:8px;
}
#toggleCarrito .badge {
  background: #ff3b3b;
  color: #fff;
  font-weight: bold;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 12px;
  min-width: 20px;
  text-align: center;
}

/* Carrito flotante (detalle) */
#carrito {
  position: fixed;
  top: 70px;
  right: 20px;
  background: #111;
  color: #fff;
  border: 2px solid #25D366;
  padding: 12px;
  width: 360px;
  max-height: 420px;
  overflow-y: auto;
  border-radius: 10px;
  transition: transform 0.22s ease, opacity 0.22s ease;
  transform: translateY(-10px);
  opacity: 0;
  pointer-events: none;
  z-index: 9999;
}
#carrito.visible { transform: translateY(0); opacity: 1; pointer-events: auto; }
#carrito h3 { margin:0 0 10px; text-align:center; }
#carrito ul { list-style:none; padding:0; margin:0; }
#carrito li { margin:8px 0; font-size:14px; color:#fff; display:flex; justify-content:space-between; gap:8px; }
#carrito .empty { color:#bbb; text-align:center; padding:12px 0; }

/* Ajustar catálogo para que no quede debajo del header */
.catalogo {
  margin-top: 110px;
  width:95%;
  margin-left:auto;
  margin-right:auto;
  display:flex;
  flex-wrap:wrap;
  justify-content:space-around;
  gap:12px;
  padding-bottom:60px;
}

.producto { width:30%; background:#111; margin:10px; padding:12px; border-radius:10px; box-shadow:0 0 12px rgba(255,255,255,0.03); }
.producto h2 { font-size:16px; color:#fff; text-align:center; margin:8px 0; }
.producto p { text-align:center; font-size:14px; color:#ddd; margin:6px 0; }
.swiper { width:100%; height:250px; border-radius:8px; overflow:hidden; background:#000; }
.swiper-slide img { width:100%; height:100%; object-fit:cover; display:block; }
.swiper-pagination { bottom:8px !important; }
.boton { display:flex; align-items:center; justify-content:center; gap:8px; margin:10px auto 0; padding:10px 16px; background:#fff; color:#000; border:none; border-radius:6px; cursor:pointer; font-weight:bold; }

/* Responsive */
@media (max-width: 1024px) { .producto { width:45%; } }
@media (max-width: 768px) { .producto { width:100%; } #carrito { width:92%; right:4%; top:90px; max-height:60%; } }
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
  <div id="carrito-total" style="margin-top:10px; text-align:right; color:#ddd; font-weight:bold;"></div>
  <a id="whatsapp" href="#" target="_blank" style="display:block; margin-top:10px; padding:10px; background:#25D366; color:#fff; text-align:center; border-radius:5px; text-decoration:none; font-weight:bold;">Enviar pedido por WhatsApp</a>
</div>

<div class="catalogo">
"""
    partes = [html_head]
    contador = 0

    # Mostrar SOLO los modelos que están en el Excel (comparación normalizada)
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
      <p>Precio: ₡{precio_esc}</p>
      <p>Tallas disponibles: {tallas_esc}</p>
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
  // Inicializar Swiper para cada contenedor .swiper
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

  // Estado simple del carrito en memoria
  let carritoItems = [];

  function actualizarUICarrito() {
    // actualizar lista
    listaCarrito.innerHTML = '';
    if (carritoItems.length === 0) {
      listaCarrito.innerHTML = '<li class="empty">El carrito está vacío</li>';
      carritoTotal.textContent = '';
    } else {
      let total = 0;
      carritoItems.forEach(function(it, idx) {
        const li = document.createElement('li');
        li.textContent = it.nombre + ' - ₡' + it.precio + ' - ' + it.tallas;
        // botón eliminar
        const btn = document.createElement('button');
        btn.textContent = 'Eliminar';
        btn.style.marginLeft = '8px';
        btn.style.background = '#ff3b3b';
        btn.style.color = '#fff';
        btn.style.border = 'none';
        btn.style.borderRadius = '6px';
        btn.style.padding = '4px 8px';
        btn.style.cursor = 'pointer';
        btn.onclick = function() {
          carritoItems.splice(idx, 1);
          actualizarUICarrito();
        };
        // contenedor para mostrar nombre y botón
        const cont = document.createElement('div');
        cont.style.display = 'flex';
        cont.style.justifyContent = 'space-between';
        cont.style.alignItems = 'center';
        cont.style.width = '100%';
        const spanLeft = document.createElement('span');
        spanLeft.textContent = it.nombre + ' - ₡' + it.precio + ' - ' + it.tallas;
        cont.appendChild(spanLeft);
        cont.appendChild(btn);
        li.innerHTML = '';
        li.appendChild(cont);
        listaCarrito.appendChild(li);

        // intentar sumar precio si es numérico
        const p = parseFloat(it.precio.replace(/[^0-9.-]+/g,""));
        if (!isNaN(p)) total += p;
      });
      carritoTotal.textContent = 'Total aproximado: ₡' + total;
    }
    // actualizar badge
    cartCount.textContent = carritoItems.length;
  }

  // Exponer función global para botones "Agregar al carrito"
  window.agregarCarrito = function(nombre, precio, tallas) {
    carritoItems.push({ nombre: nombre, precio: precio, tallas: tallas });
    actualizarUICarrito();
    // abrir carrito automáticamente al agregar
    carrito.classList.add('visible');
    carrito.setAttribute('aria-hidden', 'false');
  };

  toggleCarrito.addEventListener('click', () => {
    carrito.classList.toggle('visible');
    carrito.setAttribute('aria-hidden', carrito.classList.contains('visible') ? 'false' : 'true');
  });

  cerrarCarrito.addEventListener('click', () => {
    carrito.classList.remove('visible');
    carrito.setAttribute('aria-hidden', 'true');
  });

  // Inicial UI
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

# Bloque principal
if __name__ == "__main__":
    try:
        productos = extraer_productos(URL)
    except Exception as e:
        print("Error al descargar productos:", e)
        productos = []

    ruta_excel = os.path.join(os.path.dirname(os.path.abspath(__file__)), "productos.xlsx")
    datos_excel = leer_excel(ruta_excel)

    generar_html(productos, datos_excel, archivo="catalogo.html")
