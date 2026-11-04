"""Jerarqu?a de productos vendidos por volumen."""

from __future__ import annotations

from abc import ABC, abstractmethod

from utils.exceptions import ValidationError


class Agregado(ABC):
    """Producto base con precio por metro c?bico y stock."""

    def __init__(
        self, producto_id: int, nombre: str, precio_m3: float,
        stock_m3: float, origen: str,
    ) -> None:
        self._id = producto_id
        self.nombre = nombre
        self.precio_m3 = precio_m3
        self.stock_m3 = stock_m3
        self.origen = origen

    @property
    def id(self) -> int:
        return self._id

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ValidationError("El nombre no puede estar vac?o.")
        self._nombre = valor.strip()

    @property
    def precio_m3(self) -> float:
        return self._precio_m3

    @precio_m3.setter
    def precio_m3(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool) or valor <= 0:
            raise ValidationError("El precio por m? debe ser mayor que cero.")
        self._precio_m3 = float(valor)

    @property
    def stock_m3(self) -> float:
        return self._stock_m3

    @stock_m3.setter
    def stock_m3(self, valor: float) -> None:
        if not isinstance(valor, (int, float)) or isinstance(valor, bool) or valor < 0:
            raise ValidationError("El stock no puede ser negativo.")
        self._stock_m3 = float(valor)

    @property
    def origen(self) -> str:
        return self._origen

    @origen.setter
    def origen(self, valor: str) -> None:
        if not isinstance(valor, str) or not valor.strip():
            raise ValidationError("El origen del material es obligatorio.")
        self._origen = valor.strip()

    @abstractmethod
    def calcular_precio_final(self, cantidad_m3: float) -> float:
        """Calcula el precio del material seg?n el tipo de agregado."""

    def calcular_flete(self, cantidad_m3: float, distancia_km: float) -> float:
        if cantidad_m3 <= 0 or distancia_km < 0:
            raise ValidationError("Cantidad debe ser positiva y distancia no negativa.")
        tarifa_km_m3 = 900.0
        return cantidad_m3 * distancia_km * tarifa_km_m3

    def __str__(self) -> str:
        return (
            f"ID {self.id} | {self.__class__.__name__}: {self.nombre} | "
            f"{self.precio_m3:,.0f} COP/m? | Stock: {self.stock_m3:g} m? | "
            f"Origen: {self.origen}"
        )


class Arena(Agregado):
    """Arena con descuento por volumen en pedidos grandes."""

    def calcular_precio_final(self, cantidad_m3: float) -> float:
        if cantidad_m3 <= 0:
            raise ValidationError("La cantidad debe ser mayor que cero.")
        descuento = 0.05 if cantidad_m3 >= 20 else 0.0
        return self.precio_m3 * cantidad_m3 * (1 - descuento)


class Grava(Agregado):
    """Grava/piedra triturada con recargo de procesamiento."""

    def calcular_precio_final(self, cantidad_m3: float) -> float:
        if cantidad_m3 <= 0:
            raise ValidationError("La cantidad debe ser mayor que cero.")
        recargo_procesamiento = 0.08
        return self.precio_m3 * cantidad_m3 * (1 + recargo_procesamiento)
