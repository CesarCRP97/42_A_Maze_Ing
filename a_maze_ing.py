"""Command-line entry point for the A-Maze-ing project."""

from __future__ import annotations

import argparse
import sys

from config_parser import ConfigError, MazeConfig, parse_config
from mazegen.generator import MazeGenerator
from output_writer import write_maze
from visualizer import run_interactive


def _run_interactive_mode(config: MazeConfig) -> int:
    """Run the interactive maze visualizer."""
    try:
        run_interactive(
            width=config.width,
            height=config.height,
            entry=config.entry,
            exit=config.exit,
            perfect=config.perfect,
            seed=config.seed,
        )
    except KeyboardInterrupt:
        pass
    except Exception as error:
        print(f"Error en modo interactivo: {error}", file=sys.stderr)
        return 1
    return 0


def _run_generation_mode(config: MazeConfig) -> int:
    """Run the standard maze generation mode."""
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
        print(
            f"No se pudo escribir el archivo de salida: {error}",
            file=sys.stderr,
        )
        raise SystemExit(2)

    lines.append(f"Laberinto generado y escrito en: {config.output_file}")
    print("\n".join(lines))
    return 0


def main() -> int:
    """Main entry point for the A-Maze-ing maze generator."""
    parser = argparse.ArgumentParser(
        description="Generador de laberintos A-Maze-ing",
    )
    parser.add_argument(
        "config",
        help="Ruta al archivo de configuración KEY=VALUE",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Ejecutar visualizador interactivo en terminal",
    )

    args = parser.parse_args()

    try:
        config = parse_config(args.config)
    except ConfigError as error:
        parser.error(str(error))

    if args.interactive:
        return _run_interactive_mode(config)
    return _run_generation_mode(config)


if __name__ == "__main__":
    raise SystemExit(main())
