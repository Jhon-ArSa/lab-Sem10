"""Servidor HTTP ligero para la interfaz web de Agregados del Valle."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from models import Agregado, Arena, Grava
from utils.exceptions import NotFoundError, ValidationError

BASE_DIR = Path(__file__).parent
WEB_DIR = BASE_DIR / "web"
DATA_FILE = BASE_DIR / "inventario.json"
TIPOS = {"arena": Arena, "grava": Grava}


def cargar_inventario() -> dict[int, Agregado]:
    inventario: dict[int, Agregado] = {}
    if DATA_FILE.exists():
        try:
            registros = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            for item in registros:
                clase = TIPOS[item["tipo"]]
                producto = clase(item["id"], item["nombre"], item["precio_m3"], item["stock_m3"], item["origen"])
                inventario[producto.id] = producto
        except (ValueError, KeyError, TypeError):
            raise RuntimeError("inventario.json tiene datos invalidos; corrige o elimina el archivo.")
    return inventario


inventario = cargar_inventario()
siguiente_id = max(inventario, default=0) + 1


def serializar(producto: Agregado) -> dict:
    return {
        "id": producto.id,
        "tipo": "arena" if isinstance(producto, Arena) else "grava",
        "nombre": producto.nombre,
        "precio_m3": producto.precio_m3,
        "stock_m3": producto.stock_m3,
        "origen": producto.origen,
    }


def guardar_inventario() -> None:
    temporal = DATA_FILE.with_suffix(".tmp")
    temporal.write_text(json.dumps([serializar(p) for p in inventario.values()], ensure_ascii=False, indent=2), encoding="utf-8")
    temporal.replace(DATA_FILE)


class ApiHandler(BaseHTTPRequestHandler):
    def responder(self, status: int, contenido: dict | list, tipo: str = "application/json; charset=utf-8") -> None:
        cuerpo = json.dumps(contenido, ensure_ascii=False).encode("utf-8") if tipo.startswith("application/json") else contenido
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def leer_json(self) -> dict:
        tamano = int(self.headers.get("Content-Length", "0"))
        if tamano > 10000:
            raise ValidationError("La solicitud es demasiado grande.")
        return json.loads(self.rfile.read(tamano).decode("utf-8"))

    def do_GET(self) -> None:
        ruta = urlparse(self.path).path
        if ruta == "/api/products":
            self.responder(200, [serializar(p) for p in inventario.values()])
            return
        archivo = WEB_DIR / ("index.html" if ruta == "/" else ruta.lstrip("/"))
        if not archivo.is_file() or WEB_DIR not in archivo.resolve().parents:
            self.responder(404, {"error": "Recurso no encontrado."})
            return
        mime = "text/html; charset=utf-8" if archivo.suffix == ".html" else "text/css; charset=utf-8" if archivo.suffix == ".css" else "application/javascript; charset=utf-8"
        self.responder(200, archivo.read_bytes(), mime)

    def do_POST(self) -> None:
        global siguiente_id
        try:
            data = self.leer_json()
            ruta = urlparse(self.path).path
            if ruta == "/api/products":
                tipo = str(data.get("tipo", "")).strip().lower()
                if tipo not in TIPOS:
                    raise ValidationError("Selecciona arena o grava.")
                nombre = str(data.get("nombre", "")).strip()
                origen = str(data.get("origen", "")).strip()
                if not nombre or not origen:
                    raise ValidationError("Nombre y origen son obligatorios.")
                precio = float(data.get("precio_m3", 0))
                stock = float(data.get("stock_m3", -1))
                producto = TIPOS[tipo](siguiente_id, nombre, precio, stock, origen)
                inventario[siguiente_id] = producto
                siguiente_id += 1
                guardar_inventario()
                self.responder(201, serializar(producto))
                return
            if ruta == "/api/quote":
                producto_id = int(data.get("producto_id", 0))
                producto = inventario.get(producto_id)
                if producto is None:
                    raise NotFoundError(f"No existe el agregado con ID {producto_id}.")
                cantidad = float(data.get("cantidad_m3", 0))
                distancia = float(data.get("distancia_km", -1))
                if cantidad <= 0 or distancia < 0:
                    raise ValidationError("Ingresa una cantidad positiva y distancia no negativa.")
                if cantidad > producto.stock_m3:
                    raise ValidationError(f"Stock insuficiente. Disponible: {producto.stock_m3:g} m3.")
                material = producto.calcular_precio_final(cantidad)
                flete = producto.calcular_flete(cantidad, distancia)
                self.responder(200, {"material": material, "flete": flete, "total": material + flete, "producto": producto.nombre, "cantidad_m3": cantidad})
                return
            self.responder(404, {"error": "Recurso no encontrado."})
        except NotFoundError as error:
            self.responder(404, {"error": str(error)})
        except (ValidationError, ValueError, TypeError, json.JSONDecodeError) as error:
            self.responder(400, {"error": str(error) or "Revisa los datos ingresados."})

    def log_message(self, formato: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {formato % args}")


if __name__ == "__main__":
    servidor = ThreadingHTTPServer(("127.0.0.1", 8000), ApiHandler)
    print("Agregados del Valle disponible en http://127.0.0.1:8000")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()
