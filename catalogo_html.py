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
        imagenes = [img["src"] for img in p["images"]] if p["images"] else []
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
.producto { 
  width:30%; 
  background:#111; 
  margin:10px; 
  padding:10px; 
  position:relative; 
  border-radius:10px;
  box-shadow:0 0 20px rgba(255,255,255,0.2);
  border:2px solid transparent;
  background-image: linear-gradient(#111, #111), 
    linear-gradient(45deg, turquoise, fuchsia, yellow, white, green);
  background-origin: border-box;
  background-clip: content-box, border-box;
  animation: borderAnim 5s linear infinite;
}
@keyframes borderAnim {
  0% { background-image: linear-gradient(#111, #111), linear-gradient(45deg, turquoise, fuchsia, yellow, white, green); }
  100% { background-image: linear-gradient(#111, #111), linear-gradient(405deg, turquoise, fuchsia, yellow, white, green); }
}
.producto h2 { font-size:16px; color:#fff; text-align:center; }
.producto p { text-align:center; font-size:14px; color:#fff; }
.swiper { width:100%; height:250px; }
.swiper-slide img { width:100%; height:auto; display:block; }
.swiper-pagination { bottom:5px !important; }
h1 { text-align:center; color:#fff; font-size:32px; margin-top:20px; font-weight:bold; }
.boton { 
  display:flex; 
  align-items:center; 
  justify-content:center; 
  gap:8px; 
  margin:10px auto; 
  padding:10px 20px; 
  background:#fff; 
  color:#000; 
  border:none; 
  border-radius:5px; 
  cursor:pointer; 
  font-weight:bold; 
  font-family:'Montserrat', sans-serif; 
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.boton:hover { transform: scale(1.1); box-shadow:0 0 15px #fff; }

/* Carrito flotante abajo */
#carrito {
  position:fixed; bottom:20px; right:20px; background:#111; color:#fff;
  border:2px solid #25D366; padding:15px; border-radius:10px;
  width:250px; max-height:300px; overflow-y:auto; box-shadow:0 0 15px rgba(255,255,255,0.5);
}
#carrito h3 { margin:0 0 10px; text-align:center; }
#carrito ul { list-style:none; padding:0; margin:0; }
#carrito li { margin:5px 0; font-size:14px; }
#whatsapp { display:block; margin-top:10px; padding:10px; background:#25D366; color:#fff; text-align:center; border-radius:5px; text-decoration:none; font-weight:bold; }
#whatsapp:hover { background:#20b858; }
</style>
</head>
<body>

<h1>Regate Store - Futsal</h1>
<div id="carrito">
  <h3>🛒 Carrito</h3>
  <ul id="lista-carrito"></ul>
  <a id="whatsapp" href="#" target="_blank">Enviar pedido por WhatsApp</a>
</div>

<div class="catalogo">
"""

    for idx, prod in enumerate(productos):
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
// Inicialización global de Swiper
var swiper = new Swiper('.swiper', {
  loop: true,
  pagination: { el: '.swiper-pagination', clickable: true },
  autoplay: { delay: 2000, disableOnInteraction: false }
});

function agregarCarrito(nombre, precio, tallas) {
  const lista = document.getElementById('lista-carrito');
  const item = document.createElement('li');
  item.textContent = nombre + " - $" + precio + " - Tallas: " + tallas;
  lista.appendChild(item);

  let productos = [];
  document.querySelectorAll('#lista-carrito li').forEach(li => productos.push(li.textContent));
  const mensaje = encodeURIComponent("Hola, quiero comprar:\n" + productos.join("\\n"));
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
    if productos:
        generar_html(productos, datos_excel)
    else:
        print("⚠️ No se encontraron productos.")
