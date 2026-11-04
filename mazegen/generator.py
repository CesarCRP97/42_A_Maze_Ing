"""Maze generation strategies and public facade."""

from random import Random

from pydantic import BaseModel, ConfigDict

from mazegen.maze import Direction, Maze
from mazegen.pattern42 import Pattern42
from mazegen.types import Coordinate


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
    ) -> None:
        """Close cycles while preserving one path between walkable cells."""
        parent = {
            (cell.x, cell.y): (cell.x, cell.y)
            for row in maze.cells
            for cell in row
            if not cell.blocked
        }
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
            source_root = self._root(parent, coordinate)
            neighbor_root = self._root(parent, neighbor)
            if source_root == neighbor_root:
                maze.close_passage(*coordinate, direction)
                continue
            parent[source_root] = neighbor_root

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
    ) -> Maze:
        """Generate a connected acyclic maze for the given endpoints."""
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
        self._close_perfect_maze(maze, random_source)
        return Maze(
            width=width,
            height=height,
            entry=entry,
            exit=exit,
            cells=maze.cells,
        )
