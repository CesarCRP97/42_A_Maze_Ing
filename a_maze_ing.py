"""Temporary command-line entry point for the A-Maze-ing project."""

from __future__ import annotations

import argparse

from config_parser import ConfigError, parse_config


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
        parse_config(args.config)
    except ConfigError as error:
        parser.error(str(error))

    print("Configuración válida.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
