"""Temporary command-line entry point for the A-Maze-ing project."""

from __future__ import annotations

import argparse

from config_parser import ConfigError, parse_config
from mazegen.generator import MazeGenerator
from output_writer import write_maze


def main() -> int:
    """Validate a configuration file until maze generation is implemented."""
    parser = argparse.ArgumentParser(
        description="Generador de laberintos A-Maze-ing",
    )
    parser.add_argument(
        "config",
        help="Ruta al archivo de configuración KEY=VALUE",
    )
    args = parser.parse_args()

    try:
        config = parse_config(args.config)
    except ConfigError as error:
        parser.error(str(error))

    lines = [
        "Configuración cargada:",
        f"Tamaño: {config.width}x{config.height}",
        f"Entrada: {config.entry[0]},{config.entry[1]}",
        f"Salida: {config.exit[0]},{config.exit[1]}",
        f"Perfecto: {'sí' if config.perfect else 'no'}",
        f"Archivo de salida: {config.output_file}",
    ]
    if config.seed is not None:
        lines.append(f"Semilla: {config.seed}")
    generator = MazeGenerator(seed=config.seed)
    if config.perfect:
        maze = generator.generate_perfect(
            config.width,
            config.height,
            config.entry,
            config.exit,
        )
    else:
        maze = generator.generate_imperfect(
            config.width,
            config.height,
            config.entry,
            config.exit,
        )
    try:
        write_maze(maze, config.output_file)
    except OSError as error:
        parser.error(f"No se pudo escribir el archivo de salida: {error}")
    lines.append(f"Laberinto generado y escrito en: {config.output_file}")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
