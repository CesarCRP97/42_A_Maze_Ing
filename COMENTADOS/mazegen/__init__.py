"""Reusable package for maze generation.

Defensa: este archivo presenta una API pública pequeña y estable. Reexporta
el generador, el modelo, el solver y el patrón para que quien instale
``mazegen`` pueda utilizar sus funciones sin depender de detalles internos.
"""

from mazegen.generator import MazeGenerator
from mazegen.maze import Maze, Cell, Direction
from mazegen.solver import solve_shortest_path, Route
from mazegen.pattern42 import Pattern42

__all__ = [
    "MazeGenerator",
    "Maze",
    "Cell",
    "Direction",
    "solve_shortest_path",
    "Route",
    "Pattern42",
]
