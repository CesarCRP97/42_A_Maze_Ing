"""Tests for the structural 42 pattern."""

import unittest

from mazegen.maze import Maze
from mazegen.pattern42 import Pattern42


class Pattern42Tests(unittest.TestCase):
    def test_apply_blocks_the_centered_mask(self) -> None:
        maze = Maze.create_open(width=9, height=7)

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
                (1, 1),
                (3, 1),
                (5, 1),
                (6, 1),
                (7, 1),
                (1, 2),
                (3, 2),
                (7, 2),
                (1, 3),
                (2, 3),
                (3, 3),
                (5, 3),
                (6, 3),
                (7, 3),
                (3, 4),
                (5, 4),
                (3, 5),
                (5, 5),
                (6, 5),
                (7, 5),
            },
        )

    def test_apply_omits_the_pattern_below_minimum_dimensions(self) -> None:
        for width, height in ((7, 7), (8, 7), (8, 6)):
            with self.subTest(width=width, height=height):
                maze = Maze.create_open(width=width, height=height)

                Pattern42.apply(maze)

                self.assertFalse(
                    any(cell.blocked for row in maze.cells for cell in row)
                )

    def test_apply_rejects_an_endpoint_inside_the_pattern(self) -> None:
        open_maze = Maze.create_open(width=9, height=7)
        maze = Maze(
            width=9,
            height=7,
            entry=(1, 1),
            exit=(8, 6),
            cells=open_maze.cells,
        )

        with self.assertRaisesRegex(
            ValueError,
            "Entry and exit coordinates cannot overlap Pattern42.",
        ):
            Pattern42.apply(maze)

        has_blocked_cells = any(
            cell.blocked for row in maze.cells for cell in row
        )
        self.assertFalse(has_blocked_cells)


if __name__ == "__main__":
    unittest.main()
