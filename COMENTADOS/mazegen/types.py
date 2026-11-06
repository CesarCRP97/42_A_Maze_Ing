"""Shared types for mazegen.

Defensa: ``Coordinate`` fija la convención común de coordenadas ``(x, y)``.
Un alias único evita discrepancias entre el parser, el modelo, el generador y
la interfaz, y hace explícito el contrato de las funciones públicas.
"""

from typing import TypeAlias


Coordinate: TypeAlias = tuple[int, int]
