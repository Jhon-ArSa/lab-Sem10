"""Excepciones espec?ficas del dominio."""


class ValidationError(ValueError):
    """Dato de entrada o estado que incumple las reglas del negocio."""


class NotFoundError(LookupError):
    """Elemento solicitado que no existe en el inventario."""
