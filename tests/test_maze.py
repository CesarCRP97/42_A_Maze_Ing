"""Tests for the maze domain model."""

import unittest

from pydantic import ValidationError

from mazegen.maze import Cell, Direction, Maze


class CellTests(unittest.TestCase):
    def test_new_cell_starts_with_all_four_walls_closed(self) -> None:
        cell = Cell(x=2, y=3)

        self.assertEqual(cell.walls, set(Direction))
        self.assertEqual(cell.wall_mask, 0b1111)


class MazeTests(unittest.TestCase):
    def test_create_builds_a_rectangular_grid_of_closed_cells(self) -> None:
        maze = Maze.create(width=3, height=2)

        self.assertEqual(maze.width, 3)
        self.assertEqual(maze.height, 2)
        self.assertEqual(maze.cell_at(2, 1).model_dump(), {
            "x": 2,
            "y": 1,
            "walls": set(Direction),
        })

    def test_open_passage_removes_the_two_facing_walls(self) -> None:
        maze = Maze.create(width=2, height=1)

        maze.open_passage(0, 0, Direction.EAST)

        self.assertFalse(maze.cell_at(0, 0).has_wall(Direction.EAST))
        self.assertFalse(maze.cell_at(1, 0).has_wall(Direction.WEST))

    def test_rejects_a_grid_that_does_not_match_its_dimensions(self) -> None:
        with self.assertRaises(ValidationError):
            Maze(width=2, height=1, cells=[[Cell(x=0, y=0)]])

    def test_detects_incoherent_shared_walls(self) -> None:
        maze = Maze.create(width=2, height=1)
        maze.open_passage(0, 0, Direction.EAST)

        self.assertTrue(maze.has_coherent_walls())

        maze.cell_at(1, 0).walls.add(Direction.WEST)

        self.assertFalse(maze.has_coherent_walls())


if __name__ == "__main__":
    unittest.main()
