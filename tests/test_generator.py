"""Tests for perfect maze generation."""

from random import Random
import unittest

from pydantic import ValidationError

from mazegen.generator import MazeGenerator
from mazegen.maze import Direction, Maze


def count_open_internal_passages(maze: Maze) -> int:
    """Count internal passages once by looking east and south."""
    return sum(
        not cell.has_wall(direction)
        for row in maze.cells
        for cell in row
        for direction in (Direction.EAST, Direction.SOUTH)
    )


def wall_masks(maze: Maze) -> list[list[int]]:
    """Return a comparison-friendly representation of maze walls."""
    return [[cell.wall_mask for cell in row] for row in maze.cells]


class MazeGeneratorTests(unittest.TestCase):
    def test_generator_is_an_immutable_pydantic_model(self) -> None:
        generator = MazeGenerator(seed=42)

        with self.assertRaises(ValidationError):
            generator.seed = 7

    def test_initializes_an_open_maze(self) -> None:
        maze = MazeGenerator._new_open_maze(2, 2)

        self.assertFalse(maze.cell_at((0, 0)).has_wall(Direction.EAST))
        self.assertFalse(maze.cell_at((0, 0)).has_wall(Direction.SOUTH))
        self.assertTrue(maze.cell_at((0, 0)).has_wall(Direction.NORTH))
        self.assertTrue(maze.cell_at((0, 0)).has_wall(Direction.WEST))

    def test_closes_an_open_maze_to_a_perfect_maze(self) -> None:
        generator = MazeGenerator(seed=42)
        maze = generator._new_open_maze(3, 2)

        generator._close_perfect_maze(maze, Random(generator.seed))

        self.assertTrue(maze.has_coherent_walls())
        self.assertEqual(count_open_internal_passages(maze), 5)

    def test_generates_a_connected_acyclic_maze(self) -> None:
        maze = MazeGenerator(seed=42).generate_perfect(3, 2, (0, 0), (2, 1))

        self.assertEqual(maze.entry, (0, 0))
        self.assertEqual(maze.exit, (2, 1))
        self.assertTrue(maze.has_coherent_walls())
        self.assertEqual(
            count_open_internal_passages(maze),
            maze.width * maze.height - 1,
        )

    def test_generates_a_perfect_maze_around_pattern42(self) -> None:
        maze = MazeGenerator(seed=42).generate_perfect(9, 7, (0, 0), (8, 6))
        walkable_cells = sum(
            not cell.blocked for row in maze.cells for cell in row
        )
        open_passages = count_open_internal_passages(maze)

        self.assertEqual(
            sum(cell.blocked for row in maze.cells for cell in row),
            20,
        )
        self.assertEqual(open_passages, walkable_cells - 1)

    def test_preserves_explicit_open_and_closed_passages(self) -> None:
        maze = MazeGenerator(seed=42).generate_perfect(
            3,
            2,
            (0, 0),
            (2, 1),
            required_open_passages=[((0, 0), Direction.EAST)],
            protected_closed_passages=[((0, 0), Direction.SOUTH)],
        )

        self.assertFalse(maze.cell_at((0, 0)).has_wall(Direction.EAST))
        self.assertTrue(maze.cell_at((0, 0)).has_wall(Direction.SOUTH))
        self.assertEqual(count_open_internal_passages(maze), 5)

    def test_rejects_a_cycle_in_required_open_passages(self) -> None:
        generator = MazeGenerator()

        with self.assertRaisesRegex(
            ValueError,
            "Required open passages form a cycle.",
        ):
            generator.generate_perfect(
                2,
                2,
                (0, 0),
                (1, 1),
                required_open_passages=[
                    ((0, 0), Direction.EAST),
                    ((1, 0), Direction.SOUTH),
                    ((0, 1), Direction.EAST),
                    ((0, 0), Direction.SOUTH),
                ],
            )

    def test_rejects_one_passage_with_conflicting_constraints(self) -> None:
        generator = MazeGenerator()

        with self.assertRaisesRegex(
            ValueError,
            "A passage cannot be both required open and closed.",
        ):
            generator.generate_perfect(
                2,
                2,
                (0, 0),
                (1, 1),
                required_open_passages=[((1, 0), Direction.WEST)],
                protected_closed_passages=[((0, 0), Direction.EAST)],
            )

    def test_rejects_protected_passages_that_disconnect_the_maze(self) -> None:
        generator = MazeGenerator()

        with self.assertRaisesRegex(
            ValueError,
            "Protected closed passages disconnect the maze.",
        ):
            generator.generate_perfect(
                2,
                2,
                (0, 0),
                (1, 1),
                protected_closed_passages=[
                    ((0, 0), Direction.EAST),
                    ((0, 0), Direction.SOUTH),
                ],
            )

    def test_rejects_an_endpoint_overlapping_pattern42(self) -> None:
        generator = MazeGenerator()

        with self.assertRaisesRegex(
            ValueError,
            "Entry and exit coordinates cannot overlap Pattern42.",
        ):
            generator.generate_perfect(9, 7, (1, 1), (8, 6))

    def test_generates_a_loop_enabled_maze_with_a_cycle(self) -> None:
        maze = MazeGenerator(seed=42).generate_imperfect(3, 3, (0, 0), (2, 2))

        self.assertGreater(
            count_open_internal_passages(maze),
            maze.width * maze.height - 1,
        )

    def test_preserves_cyclic_open_and_protected_closed_passages(self) -> None:
        required_open = [
            ((0, 0), Direction.EAST),
            ((1, 0), Direction.SOUTH),
            ((0, 1), Direction.EAST),
            ((0, 0), Direction.SOUTH),
        ]
        protected_closed = [((2, 1), Direction.SOUTH)]

        maze = MazeGenerator(seed=42).generate_imperfect(
            3,
            3,
            (0, 0),
            (2, 2),
            required_open_passages=required_open,
            protected_closed_passages=protected_closed,
        )

        for coordinate, direction in required_open:
            with self.subTest(passage=(coordinate, direction)):
                self.assertFalse(maze.cell_at(coordinate).has_wall(direction))
        for coordinate, direction in protected_closed:
            with self.subTest(passage=(coordinate, direction)):
                self.assertTrue(maze.cell_at(coordinate).has_wall(direction))

    def test_preserves_pattern42_connectivity_and_boundaries(self) -> None:
        maze = MazeGenerator(seed=42).generate_imperfect(9, 7, (0, 0), (8, 6))

        self.assertEqual(
            sum(cell.blocked for row in maze.cells for cell in row),
            20,
        )
        self.assertTrue(maze._has_full_connectivity())
        self.assertTrue(maze._has_symmetric_shared_walls())
        self.assertTrue(maze._has_closed_external_borders())

    def test_same_seed_produces_the_same_wall_layout(self) -> None:
        first = MazeGenerator(seed=42).generate_perfect(4, 3, (0, 0), (3, 2))
        second = MazeGenerator(seed=42).generate_perfect(4, 3, (0, 0), (3, 2))

        self.assertEqual(wall_masks(first), wall_masks(second))

    def test_rejects_single_row_or_column_mazes(self) -> None:
        generator = MazeGenerator()

        for request in ((1, 3, (0, 0), (0, 2)), (3, 1, (0, 0), (2, 0))):
            with self.subTest(request=request):
                with self.assertRaisesRegex(
                    ValueError,
                    "Maze dimensions must be at least 2 by 2.",
                ):
                    generator.generate_perfect(*request)

    def test_rejects_invalid_generation_requests(self) -> None:
        generator = MazeGenerator()
        invalid_requests = (
            (0, 1, (0, 0), (0, 0)),
            (2, 1, (0, 0), (0, 0)),
            (2, 1, (-1, 0), (1, 0)),
            (2, 1, (0, 0), (2, 0)),
        )

        for request in invalid_requests:
            with self.subTest(request=request):
                with self.assertRaises(ValueError):
                    generator.generate_perfect(*request)


if __name__ == "__main__":
    unittest.main()
