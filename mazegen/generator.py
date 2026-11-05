"""Maze generation strategies and public facade."""

from collections.abc import Iterable
from random import Random
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict

from mazegen.maze import Direction, Maze
from mazegen.pattern42 import Pattern42
from mazegen.types import Coordinate


Passage: TypeAlias = tuple[Coordinate, Direction]


class MazeGenerator(BaseModel):
    """Generate mazes with an optional reproducible random seed."""

    model_config = ConfigDict(frozen=True)

    seed: int | None = None

    @staticmethod
    def _validate_request(
        width: int,
        height: int,
        entry: Coordinate,
        exit: Coordinate,
    ) -> None:
        """Validate dimensions and endpoint coordinates for generation."""
        if width < 2 or height < 2:
            raise ValueError("Maze dimensions must be at least 2 by 2.")
        if entry == exit:
            raise ValueError("Entry and exit coordinates must be distinct.")

        for name, coordinate in (("Entry", entry), ("Exit", exit)):
            x, y = coordinate
            if not (0 <= x < width and 0 <= y < height):
                raise ValueError(
                    f"{name} coordinates must be inside the maze."
                )

    @staticmethod
    def _new_open_maze(width: int, height: int) -> Maze:
        """Create the open maze grid that generation will close."""
        return Maze.create_open(width, height)

    def _close_perfect_maze(
        self,
        maze: Maze,
        random_source: Random,
        required_open_passages: frozenset[Passage] = frozenset(),
        protected_closed_passages: frozenset[Passage] = frozenset(),
    ) -> None:
        """Close cycles while preserving one path between walkable cells."""
        parent = {
            (cell.x, cell.y): (cell.x, cell.y)
            for row in maze.cells
            for cell in row
            if not cell.blocked
        }
        for coordinate, direction in required_open_passages:
            neighbor = maze.neighbor_coordinates(*coordinate, direction)
            if neighbor is None:
                raise ValueError(
                    "Required passages cannot face outside the maze."
                )
            source_root = self._root(parent, coordinate)
            neighbor_root = self._root(parent, neighbor)
            if source_root == neighbor_root:
                raise ValueError("Required open passages form a cycle.")
            parent[source_root] = neighbor_root

        passages: list[tuple[Coordinate, Direction]] = []

        for row in maze.cells:
            for cell in row:
                coordinate = (cell.x, cell.y)
                if cell.blocked:
                    continue
                for direction in (Direction.EAST, Direction.SOUTH):
                    neighbor = maze.neighbor_coordinates(
                        *coordinate,
                        direction,
                    )
                    if neighbor is None or cell.has_wall(direction):
                        continue
                    if not maze.cell_at(neighbor).blocked:
                        passages.append((coordinate, direction))

        random_source.shuffle(passages)
        for coordinate, direction in passages:
            neighbor = maze.neighbor_coordinates(*coordinate, direction)
            if neighbor is None:
                continue
            passage = (coordinate, direction)
            if passage in required_open_passages:
                continue
            if passage in protected_closed_passages:
                maze.close_passage(*coordinate, direction)
                continue
            source_root = self._root(parent, coordinate)
            neighbor_root = self._root(parent, neighbor)
            if source_root == neighbor_root:
                maze.close_passage(*coordinate, direction)
                continue
            parent[source_root] = neighbor_root

        roots = {self._root(parent, coordinate) for coordinate in parent}
        if len(roots) != 1:
            raise ValueError("Protected closed passages disconnect the maze.")

    @staticmethod
    def _normalize_passages(
        maze: Maze,
        passages: Iterable[Passage],
        constraint_name: str,
    ) -> frozenset[Passage]:
        """Validate passages and give each shared wall one representation."""
        normalized: set[Passage] = set()
        for coordinate, direction in passages:
            if not isinstance(direction, Direction):
                raise ValueError(f"{constraint_name} must use a Direction.")
            try:
                neighbor = maze.neighbor_coordinates(*coordinate, direction)
            except (IndexError, TypeError):
                raise ValueError(
                    f"{constraint_name} must start inside the maze."
                ) from None
            if neighbor is None:
                raise ValueError(
                    f"{constraint_name} cannot face outside the maze."
                )
            source_cell = maze.cell_at(coordinate)
            neighbor_cell = maze.cell_at(neighbor)
            if source_cell.blocked or neighbor_cell.blocked:
                raise ValueError(
                    f"{constraint_name} cannot touch blocked cells."
                )
            if direction in (Direction.EAST, Direction.SOUTH):
                normalized.add((coordinate, direction))
            else:
                normalized.add((neighbor, direction.opposite))
        return frozenset(normalized)

    @staticmethod
    def _root(
        parent: dict[Coordinate, Coordinate],
        coordinate: Coordinate,
    ) -> Coordinate:
        """Return the root of a Union-Find component."""
        while parent[coordinate] != coordinate:
            coordinate = parent[coordinate]
        return coordinate

    def generate_perfect(
        self,
        width: int,
        height: int,
        entry: Coordinate,
        exit: Coordinate,
        required_open_passages: Iterable[Passage] = (),
        protected_closed_passages: Iterable[Passage] = (),
    ) -> Maze:
        """Generate a perfect maze while honoring explicit wall constraints."""
        self._validate_request(width, height, entry, exit)
        random_source = Random(self.seed)
        open_maze = self._new_open_maze(width, height)
        maze = Maze(
            width=width,
            height=height,
            entry=entry,
            exit=exit,
            cells=open_maze.cells,
        )
        Pattern42.apply(maze)
        required_open = self._normalize_passages(
            maze,
            required_open_passages,
            "Required open passages",
        )
        protected_closed = self._normalize_passages(
            maze,
            protected_closed_passages,
            "Protected closed passages",
        )
        if required_open & protected_closed:
            raise ValueError(
                "A passage cannot be both required open and closed."
            )
        self._close_perfect_maze(
            maze,
            random_source,
            required_open,
            protected_closed,
        )
        return Maze(
            width=width,
            height=height,
            entry=entry,
            exit=exit,
            cells=maze.cells,
        )
