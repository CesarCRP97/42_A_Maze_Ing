"""Tests for configuration parsing and model validation."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pydantic import BaseModel, ValidationError

from config_parser import ConfigError, MazeConfig, parse_config


class MazeConfigTests(unittest.TestCase):
    def test_parse_config_returns_an_immutable_pydantic_model(self) -> None:
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
                    )
                ),
                encoding="utf-8",
            )

            config = parse_config(config_file)

        self.assertIsInstance(config, MazeConfig)
        self.assertIsInstance(config, BaseModel)
        self.assertEqual(config.entry, (0, 0))
        with self.assertRaises(ValidationError):
            config.width = 4

    def test_invalid_boolean_raises_config_error(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            config_file = Path(temporary_directory) / "invalid.conf"
            config_file.write_text(
                "\n".join(
                    (
                        "WIDTH=3",
                        "HEIGHT=2",
                        "ENTRY=0,0",
                        "EXIT=2,1",
                        "OUTPUT_FILE=maze.txt",
                        "PERFECT=perhaps",
                    )
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ConfigError, "Invalid boolean value: 'perhaps'"
            ):
                parse_config(config_file)


if __name__ == "__main__":
    unittest.main()
