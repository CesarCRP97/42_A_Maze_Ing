"""Tests for the command-line entry point."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from a_maze_ing import main


class CommandLineTests(unittest.TestCase):
    def test_prints_the_parsed_configuration_summary(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            config_file = Path(temporary_directory) / "maze.conf"
            config_file.write_text(
                "\n".join(
                    (
                        "WIDTH=3",
                        "HEIGHT=2",
                        "ENTRY=0,0",
                        "EXIT=2,1",
                        "OUTPUT_FILE=maze.txt",
                        "PERFECT=true",
                        "SEED=42",
                    )
                ),
                encoding="utf-8",
            )
            stdout = StringIO()

            with (
                patch("sys.argv", ["a_maze_ing.py", str(config_file)]),
                redirect_stdout(stdout),
            ):
                exit_code = main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            stdout.getvalue(),
            "\n".join(
                (
                    "Configuración cargada:",
                    "Tamaño: 3x2",
                    "Entrada: 0,0",
                    "Salida: 2,1",
                    "Perfecto: sí",
                    "Archivo de salida: maze.txt",
                    "Semilla: 42",
                    "",
                )
            ),
        )


if __name__ == "__main__":
    unittest.main()
