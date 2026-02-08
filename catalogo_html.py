import os
import requests
import pandas as pd

URL = "https://www.maxsport.com.co/collections/zapatillas-max/products.json"

def extraer_productos(url):
    resp = requests.get(url)
    data = resp.json()
    productos = []
    for p in data["products"]:
        nombre = p["title"]
        # Tomar máximo 3 imágenes por producto
        imagenes = [img["src"] for img in p["images"][:3]] if p["images"] else []
        productos.append({
            "nombre": nombre,
            "imagenes": imagenes
        })
    return productos

def generar_html(productos, datos_excel, archivo="catalogo.html"):
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    archivo_salida = os.path.join(ruta_actual, archivo)

    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Regate Store - Futsal</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css"/>
<style>
body { margin:0; background:#000; font-family:'Montserrat', sans-serif; color:#fff; }
.catalogo { width:95%; margin:30px auto; display:flex; flex-wrap:wrap; justify-content:space-around; }
.producto { width:30%; background:#111; margin:10px; padding:10px; border-radius:10px; box-shadow:0 0 20px rgba(255,255,255,0.2); }
.producto h2 { font-size:16px; color:#fff; text-align:center; }
.producto p { text-align:center; font-size:14px; color:#fff; }
.swiper { width:100%; height:250px; }
.swiper-slide img { width:100%; height:auto; display:block; }
.swiper-pagination { bottom:5px !important; }
h1 { text-align:center; color:#fff; font-size:32px; margin-top:20px; font-weight:bold; }
.boton { display:flex; align-items:center; justify-content:center; gap:8px; margin:10px auto; padding:10px 20px; background:#fff; color:#000; border:none; border-radius:5px; cursor:pointer; font-weight:bold; }
.boton:hover { transform: scale(1.1); box-shadow:0 0 15px #fff; }

/* Carrito flotante */
#carrito {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) scale(0);
  background: #111;
  color: #fff;
  border: 2px solid #25D366;
  padding: 20px;
  width: 350px;
  max-height: 400px;
  overflow-y: auto;
  box-shadow: 0 0 20px rgba(255,255,255,0.5);
  border-radius: 10px;
  transition: transform 0.3s ease;
  z-index: 9999;
}
#carrito.visible { transform: translate(-50%, -50%) scale(1); }
#carrito h3 { margin:0 0 10px; text-align:center; }
#carrito ul { list-style:none; padding:0; margin:0; }
#carrito li { margin:5px 0; font-size:14px; }
#whatsapp { display:block; margin-top:10px; padding:10px; background:#25D366; color:#fff; text-align:center; border-radius:5px; text-decoration:none; font-weight:bold; }
#whatsapp:hover { background:#20b858; }

/* Botón flotante carrito */
#toggleCarrito {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: #25D366;
  color: #fff;
  padding: 15px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 22px;
  box-shadow: 0 0 10px rgba(0,0,0,0.5);
  z-index: 10000;
}

/* Botón cerrar dentro del carrito */
#cerrarCarrito {
  position: absolute;
  top: 10px;
  right: 10px;
  background: #f00;
  color: #fff;
  border: none;
  border-radius: 50%;
  width: 25px;
  height: 25px;
  cursor: pointer;
  font-weight: bold;
}

/* Responsive */
@media (max-width: 1024px) {
  .producto { width:45%; }
}
@media (max-width: 768px) {
  .producto { width:90%; }
  #carrito {
    width: 90%;
    max-height: 80%;
  }
}
</style>
</head>
<body>

<h1>Regate Store - Futsal</h1>

<div id="toggleCarrito">🛒</div>
<div id="carrito">
  <button id="cerrarCarrito">✖</button>
  <h3>Carrito</h3>
  <ul id="lista-carrito"></ul>
  <a id="whatsapp" href="#" target="_blank">Enviar pedido por WhatsApp</a>
</div>

<div class="catalogo">
"""

    # Generar productos dinámicamente
    for prod in productos:
        if prod["nombre"] in datos_excel:
            precio, tallas = datos_excel[prod["nombre"]]
            html += f"""
            <div class="producto">
              <h2>{prod['nombre']}</h2>
              <p>Precio: ${precio}</p>
              <p>Tallas disponibles: {tallas}</p>
              <div class="swiper">
                <div class="swiper-wrapper">
            """
            for img in prod["imagenes"]:
                html += f'<div class="swiper-slide"><img src="{img}" alt="{prod["nombre"]}"></div>'
            html += f"""
                </div>
                <div class="swiper-pagination"></div>
              </div>
              <button class="boton" onclick="agregarCarrito('{prod['nombre']}', '{precio}', '{tallas}')">🛒 Agregar al carrito</button>
            </div>
            """

    html += """
</div>

<script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
<script>
document.querySelectorAll('.swiper').forEach(function(swiperEl) {
  new Swiper(swiperEl, {
    loop: true,
    pagination: { el: swiperEl.querySelector('.swiper-pagination'), clickable: true },
    autoplay: { delay: 2500, disableOnInteraction: false }
  });
});

// Abrir carrito
document.getElementById('toggleCarrito').addEventListener('click', () => {
  document.getElementById('carrito').classList.add('visible');
});

// Cerrar carrito
document.getElementById('cerrarCarrito').addEventListener('click', () => {
  document.getElementById('carrito').classList.remove('visible');
});

function agregarCarrito(nombre, precio, tallas) {
  const lista = document.getElementById('lista-carrito');
  const item = document.createElement('li');
  item.textContent = nombre + " - $" + precio + " - Tallas: " + tallas;
  lista.appendChild(item);

  let productos = [];
  document.querySelectorAll('#lista-carrito li').forEach(li => productos.push(li.textContent));
  const mensaje = encodeURIComponent("Hola, quiero comprar:\\n" + productos.join("\\n"));
  document.getElementById('whatsapp').href = "https://wa.me/573001112233?text=" + mensaje;
}
</script>
</body>
</html>
"""

    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Catálogo generado: {archivo_salida}")

if __name__ == "__main__":
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    archivo_excel = os.path.join(ruta_actual, "productos.xlsx")

    df = pd.read_excel(archivo_excel, sheet_name="Catalogo")
    datos_excel = {row["nombre_producto"]: (row["precio"], row["tallas"]) for _, row in df.iterrows()}

    productos = extraer_productos(URL)
    generar_html(productos, datos_excel)
