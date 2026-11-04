"""CLI para gestionar el inventario de una empresa de agregados."""

import json
from pathlib import Path

from models import Agregado, Arena, Grava
from utils.exceptions import NotFoundError, ValidationError
from utils.formatters import formato_dinero
from utils.validators import validar_numero, validar_texto

ARCHIVO_INVENTARIO = Path(__file__).parent / "inventario.json"
TIPOS_PRODUCTO = {"arena": Arena, "grava": Grava}


def cargar_inventario() -> dict[int, Agregado]:
    """Carga desde el archivo compartido con la interfaz web."""
    if not ARCHIVO_INVENTARIO.exists():
        return {}

    try:
        registros = json.loads(ARCHIVO_INVENTARIO.read_text(encoding="utf-8"))
        inventario = {}
        for registro in registros:
            clase = TIPOS_PRODUCTO[registro["tipo"]]
            producto = clase(
                registro["id"],
                registro["nombre"],
                registro["precio_m3"],
                registro["stock_m3"],
                registro["origen"],
            )
            inventario[producto.id] = producto
        return inventario
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise ValidationError(
            f"No se pudo leer {ARCHIVO_INVENTARIO.name}: {error}"
        ) from error


def guardar_inventario(inventario: dict[int, Agregado]) -> None:
    """Guarda los productos en el formato compartido con la interfaz web."""
    registros = []
    for producto in inventario.values():
        registros.append(
            {
                "id": producto.id,
                "tipo": "arena" if isinstance(producto, Arena) else "grava",
                "nombre": producto.nombre,
                "precio_m3": producto.precio_m3,
                "stock_m3": producto.stock_m3,
                "origen": producto.origen,
            }
        )

    temporal = ARCHIVO_INVENTARIO.with_suffix(".tmp")
    temporal.write_text(
        json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporal.replace(ARCHIVO_INVENTARIO)


def mostrar_menu() -> str:
    print("\n=== AGREGADOS DEL VALLE | GESTI?N DE INVENTARIO ===")
    print("1. Registrar agregado")
    print("2. Listar inventario")
    print("3. Cotizar producto y flete")
    print("4. Salir")
    return input("Opci?n: ").strip()


def pedir_datos_producto(inventario: dict[int, Agregado], siguiente_id: int) -> int:
    tipo = validar_texto(input("Tipo (arena/grava): ")).lower()
    nombre = validar_texto(input("Nombre comercial: "))
    precio = validar_numero(input("Precio por m? (COP): "), minimo=1)
    stock = validar_numero(input("Stock disponible (m?): "), minimo=0)
    origen = validar_texto(input("Origen del material: "))

    if tipo == "arena":
        producto = Arena(siguiente_id, nombre, precio, stock, origen)
    elif tipo == "grava":
        producto = Grava(siguiente_id, nombre, precio, stock, origen)
    else:
        raise ValidationError("El tipo debe ser 'arena' o 'grava'.")

    inventario[siguiente_id] = producto
    guardar_inventario(inventario)
    print(f"Registrado: {producto}")
    return siguiente_id + 1


def listar_inventario(inventario: dict[int, Agregado]) -> None:
    if not inventario:
        print("El inventario est? vac?o.")
        return
    print("\n--- Inventario ---")
    for producto in inventario.values():
        print(producto)


def cotizar(inventario: dict[int, Agregado]) -> None:
    if not inventario:
        print("No hay productos para cotizar.")
        return
    producto_id = int(validar_numero(input("ID del agregado: "), tipo=int, minimo=1))
    producto = inventario.get(producto_id)
    if producto is None:
        raise NotFoundError(f"No existe un agregado con ID {producto_id}.")
    cantidad = validar_numero(input("Cantidad (m?): "), minimo=0.01)
    distancia = validar_numero(input("Distancia de entrega (km): "), minimo=0)
    if cantidad > producto.stock_m3:
        raise ValidationError(
            f"Stock insuficiente. Disponible: {producto.stock_m3:g} m?."
        )
    subtotal = producto.calcular_precio_final(cantidad)
    flete = producto.calcular_flete(cantidad, distancia)
    print(f"Material: {formato_dinero(subtotal)}")
    print(f"Flete:    {formato_dinero(flete)}")
    print(f"Total:    {formato_dinero(subtotal + flete)}")


def main() -> None:
    try:
        inventario = cargar_inventario()
    except ValidationError as error:
        print(f"Error al cargar el inventario: {error}")
        return
    siguiente_id = max(inventario, default=0) + 1
    print("Sistema de cotizaci?n e inventario iniciado.")
    try:
        while True:
            try:
                opcion = mostrar_menu()
                if opcion == "1":
                    siguiente_id = pedir_datos_producto(inventario, siguiente_id)
                elif opcion == "2":
                    listar_inventario(inventario)
                elif opcion == "3":
                    cotizar(inventario)
                elif opcion == "4":
                    print("Cerrando el sistema.")
                    break
                else:
                    raise ValidationError("Selecciona una opci?n entre 1 y 4.")
            except ValidationError as error:
                print(f"Error de validaci?n: {error}")
            except NotFoundError as error:
                print(f"No encontrado: {error}")
            except (ValueError, EOFError) as error:
                print(f"Entrada inv?lida: {error}")
            else:
                continue
            finally:
                # Punto de cierre por iteraci?n; no se mantienen recursos abiertos.
                pass
    finally:
        print("Sesi?n finalizada.")


if __name__ == "__main__":
    main()
