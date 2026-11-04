"""Tests for the structural 42 pattern."""

import unittest

from mazegen.maze import Maze
from mazegen.pattern42 import Pattern42


class Pattern42Tests(unittest.TestCase):
    def test_apply_blocks_the_centered_mask(self) -> None:
        maze = Maze.create_open(width=8, height=7)

        Pattern42.apply(maze)

        blocked_coordinates = {
            (cell.x, cell.y)
            for row in maze.cells
            for cell in row
            if cell.blocked
        }
        self.assertEqual(
            blocked_coordinates,
            {
                (0, 1),
                (2, 1),
                (4, 1),
                (5, 1),
                (6, 1),
                (0, 2),
                (2, 2),
                (6, 2),
                (0, 3),
                (1, 3),
                (2, 3),
                (4, 3),
                (5, 3),
                (6, 3),
                (2, 4),
                (4, 4),
                (2, 5),
                (4, 5),
                (5, 5),
                (6, 5),
            },
        )

    def test_apply_omits_the_pattern_below_minimum_dimensions(self) -> None:
        for width, height in ((7, 7), (8, 6)):
            with self.subTest(width=width, height=height):
                maze = Maze.create_open(width=width, height=height)

                Pattern42.apply(maze)

                self.assertFalse(
                    any(cell.blocked for row in maze.cells for cell in row)
                )


if __name__ == "__main__":
    unittest.main()
