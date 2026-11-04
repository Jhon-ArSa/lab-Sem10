"""Formato de valores monetarios para la CLI."""


def formato_dinero(valor: float) -> str:
    return f"$ {valor:,.0f} COP"
