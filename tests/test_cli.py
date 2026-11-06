"""Tests for the command-line entry point."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from a_maze_ing import main


class CommandLineTests(unittest.TestCase):
    def test_prints_the_parsed_configuration_summary(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            output_file = directory / "maze.txt"
            config_file = directory / "maze.conf"
            config_file.write_text(
                "\n".join(
                    (
                        "WIDTH=3",
                        "HEIGHT=2",
                        "ENTRY=0,0",
                        "EXIT=2,1",
                        f"OUTPUT_FILE={output_file}",
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
                    f"Archivo de salida: {output_file}",
                    "Semilla: 42",
                    f"Laberinto generado y escrito en: {output_file}",
                    "",
                )
            ),
        )

    def test_generates_and_writes_an_imperfect_maze(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            output_file = directory / "maze.txt"
            config_file = directory / "maze.conf"
            config_file.write_text(
                "\n".join(
                    (
                        "WIDTH=3",
                        "HEIGHT=3",
                        "ENTRY=0,0",
                        "EXIT=2,2",
                        f"OUTPUT_FILE={output_file}",
                        "PERFECT=false",
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
            self.assertTrue(output_file.is_file())
            serialized_maze = output_file.read_text(encoding="utf-8")
            self.assertIn(
                f"Laberinto generado y escrito en: {output_file}",
                stdout.getvalue(),
            )
            self.assertIn("0,0\n2,2\n", serialized_maze)

    def test_generates_and_writes_a_perfect_maze(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            output_file = directory / "maze.txt"
            config_file = directory / "maze.conf"
            config_file.write_text(
                "\n".join(
                    (
                        "WIDTH=3",
                        "HEIGHT=3",
                        "ENTRY=0,0",
                        "EXIT=2,2",
                        f"OUTPUT_FILE={output_file}",
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
            self.assertTrue(output_file.is_file())
            serialized_maze = output_file.read_text(encoding="utf-8")
            self.assertIn(
                f"Laberinto generado y escrito en: {output_file}",
                stdout.getvalue(),
            )
            self.assertIn("0,0\n2,2\n", serialized_maze)

    def test_reports_an_output_write_failure_without_a_traceback(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            output_file = directory / "missing" / "maze.txt"
            config_file = directory / "maze.conf"
            config_file.write_text(
                "\n".join(
                    (
                        "WIDTH=3",
                        "HEIGHT=3",
                        "ENTRY=0,0",
                        "EXIT=2,2",
                        f"OUTPUT_FILE={output_file}",
                        "PERFECT=false",
                    )
                ),
                encoding="utf-8",
            )
            stderr = StringIO()

            try:
                with (
                    patch("sys.argv", ["a_maze_ing.py", str(config_file)]),
                    redirect_stderr(stderr),
                    self.assertRaises(SystemExit) as raised,
                ):
                    main()
            except OSError as error:
                self.fail(f"CLI raised an unhandled write error: {error}")

        self.assertEqual(raised.exception.code, 2)
        self.assertIn(
            "No se pudo escribir el archivo de salida",
            stderr.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
