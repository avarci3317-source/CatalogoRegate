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
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>
<style>
/* Base */
:root {
  --bg: #000;
  --card: #111;
  --accent: #25D366;
  --muted: #ddd;
  --danger: #ff3b3b;
  --red-icon: #ff3b3b;
}
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); font-family:'Montserrat', sans-serif; color:#fff; -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale; }

/* Header fijo y centrado de iconos */
header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background: var(--card);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 12px 20px;
  z-index: 10000;
  box-shadow: 0 2px 10px rgba(255,255,255,0.04);
}

/* Contenedor interno para distribuir título y controles */
.header-inner {
  width: 95%;
  max-width: 1200px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Título tienda */
header h1 {
  margin: 0;
  font-size: 26px;
  color: #fff;
  text-align:left;
  font-weight: 800;
  letter-spacing: 0.6px;
}

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
  color: var(--red-icon);
  font-size: 20px;
  text-decoration: none;
  display:flex;
  align-items:center;
  justify-content:center;
  width:34px;
  height:34px;
  border-radius:6px;
  transition: transform .12s ease;
}
.redes a:hover { transform: translateY(-3px); }

/* Badge contador en el carrito */
#toggleCarrito {
  position: relative;
  background: var(--accent);
  color: #fff;
  padding: 8px 12px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 18px;
  box-shadow: 0 0 8px rgba(0,0,0,0.35);
  display:flex;
  align-items:center;
  gap:8px;
}
#toggleCarrito .badge {
  background: var(--danger);
  color: #fff;
  font-weight: 700;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 12px;
  min-width: 20px;
  text-align: center;
}

/* Carrito flotante (detalle) */
#carrito {
  position: fixed;
  top: 80px;
  right: 20px;
  background: var(--card);
  color: #fff;
  border: 2px solid var(--accent);
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
#carrito h3 { margin:0 0 10px; text-align:center; font-weight:700; }
#carrito ul { list-style:none; padding:0; margin:0; }
#carrito li { margin:8px 0; font-size:14px; color:#fff; display:flex; justify-content:space-between; gap:8px; }
#carrito .empty { color:#bbb; text-align:center; padding:12px 0; }

/* Ajustar catálogo para que no quede debajo del header */
.catalogo {
  margin-top: 120px;
  width:95%;
  margin-left:auto;
  margin-right:auto;
  display:flex;
  flex-wrap:wrap;
  justify-content:space-around;
  gap:14px;
  padding-bottom:60px;
}

.producto {
  width:30%;
  background: var(--card);
  margin:10px;
  padding:14px;
  border-radius:12px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.45);
  transition: transform .12s ease, box-shadow .12s ease;
}
.producto:hover { transform: translateY(-6px); box-shadow: 0 12px 30px rgba(0,0,0,0.6); }

.producto h2 { font-size:16px; color:#fff; text-align:center; margin:8px 0; font-weight:700; }
.producto p { text-align:center; font-size:14px; color:var(--muted); margin:6px 0; }
.swiper { width:100%; height:260px; border-radius:8px; overflow:hidden; background:#000; }
.swiper-slide img { width:100%; height:100%; object-fit:cover; display:block; }
.swiper-pagination { bottom:8px !important; }
.boton { display:flex; align-items:center; justify-content:center; gap:8px; margin:12px auto 0; padding:10px 16px; background:#fff; color:#000; border:none; border-radius:8px; cursor:pointer; font-weight:800; }

/* Responsive general */
@media (max-width: 1024px) {
  .producto { width:45%; }
}

/* Ajustes móviles: más grande y llamativo */
@media (max-width: 768px) {
  /* Header: apilar y agrandar */
  header {
    padding: 16px 12px;
  }
  .header-inner {
    width: 96%;
    flex-direction: column;
    align-items: center;
    gap: 10px;
  }
  /* Título mucho más grande y llamativo */
  header h1 {
    font-size: 34px; /* aumentado */
    text-align: center;
    font-weight: 900;
    letter-spacing: 1px;
    line-height: 1.05;
  }

  /* Iconos y carrito: más grandes y centrados debajo del título */
  .header-right {
    width: 100%;
    display:flex;
    justify-content:center;
    gap:18px;
  }
  .redes a {
    width: 52px;
    height: 52px;
    font-size: 26px;
    border-radius: 10px;
    background: rgba(255,255,255,0.02);
    display:flex;
    align-items:center;
    justify-content:center;
  }
  #toggleCarrito {
    padding: 12px 16px;
    font-size: 22px;
    border-radius: 26px;
  }
  #toggleCarrito .badge {
    min-width: 28px;
    padding: 6px 10px;
    font-size: 14px;
    border-radius: 14px;
  }

  /* Carrito: más ancho y centrado en móvil */
  #carrito {
    width: 94%;
    right: 3%;
    top: 110px;
    max-height: 62vh;
    padding: 16px;
    border-radius: 12px;
  }
  #carrito h3 { font-size: 20px; }
  #carrito li { font-size: 16px; padding: 8px 0; }

  /* Catálogo: producto ocupa todo el ancho y mayor espaciado */
  .catalogo {
    margin-top: 150px;
    gap: 18px;
    padding-bottom: 100px;
  }
  .producto {
    width: 100%;
    padding: 18px;
    margin: 8px 0;
    border-radius: 14px;
  }
  .producto h2 {
    font-size: 20px;
    margin: 12px 0 8px;
  }
  .producto p {
    font-size: 18px;
    margin: 8px 0;
  }

  /* Carrusel: más alto para ocupar pantalla */
  .swiper {
    height: 380px; /* mayor altura en móvil */
  }
  .swiper-pagination { bottom: 12px !important; }

  /* Botón agregar: más grande y táctil */
  .boton {
    padding: 14px 20px;
    font-size: 18px;
    border-radius: 10px;
  }

  /* Badge del contador más visible */
  #cart-count {
    font-size: 15px;
    padding: 6px 10px;
  }
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
  <div id="carrito-total" style="margin-top:10px; text-align:right; color:#ddd; font-weight:bold;"></div>
  <a id="whatsapp" href="#" target="_blank" style="display:block; margin-top:10px; padding:10px; background:var(--accent); color:#fff; text-align:center; border-radius:6px; text-decoration:none; font-weight:bold;">Enviar pedido por WhatsApp</a>
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

        // contenedor para mostrar nombre y botón eliminar
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

    // En móviles, desplazar la vista hacia el carrito para que el usuario lo vea
    if (window.innerWidth <= 768) {
      setTimeout(() => {
        carrito.scrollIntoView({ behavior: 'smooth', block: 'center' });
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

    # Ruta del Excel (coloca 'productos.xlsx' en la misma carpeta)
    ruta_excel = os.path.join(os.path.dirname(os.path.abspath(__file__)), "productos.xlsx")
    datos_excel = leer_excel(ruta_excel)

    generar_html(productos, datos_excel, archivo="catalogo.html")
