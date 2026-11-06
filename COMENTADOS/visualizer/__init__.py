"""ASCII rendering utilities for maze visualization.

Defensa: esta fachada expone el renderizador y el modo interactivo como
interfaz pública, manteniendo separados los detalles de dibujo y de lectura
de teclado.
"""

from .ascii_display import render_maze
from .interactive import run_interactive

__all__ = ["render_maze", "run_interactive"]
