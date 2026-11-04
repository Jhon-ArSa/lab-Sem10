"""Funciones para normalizar y validar datos del usuario."""

from utils.exceptions import ValidationError


def validar_numero(
    valor: str, tipo: type = float, minimo: float = 0,
    maximo: float | None = None,
) -> float | int:
    try:
        numero = tipo(valor.strip())
    except (ValueError, AttributeError) as error:
        raise ValidationError(f"Formato num?rico inv?lido: {valor!r}.") from error
    if numero < minimo or (maximo is not None and numero > maximo):
        limite = f" y {maximo}" if maximo is not None else ""
        raise ValidationError(f"El valor debe estar entre {minimo}{limite}.")
    return numero


def validar_texto(valor: str) -> str:
    texto = valor.strip()
    if not texto:
        raise ValidationError("El texto no puede estar vac?o.")
    return texto
