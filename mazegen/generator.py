"""Maze generation strategies and public facade."""

from random import Random

from pydantic import BaseModel, ConfigDict

from mazegen.maze import Direction, Maze
from mazegen.types import Coordinate


class MazeGenerator(BaseModel):
    """Generate mazes with an optional reproducible random seed."""

    model_config = ConfigDict(frozen=True)

    seed: int | None = None

    @staticmethod
    def _shuffled_directions(random_source: Random) -> list[Direction]:
        """Return cardinal directions in a random order."""
        directions = list(Direction)
        random_source.shuffle(directions)
        return directions

    @staticmethod
    def _validate_request(
        width: int,
        height: int,
        entry: Coordinate,
        exit: Coordinate,
    ) -> None:
        """Validate dimensions and endpoint coordinates for generation."""
        if width <= 0 or height <= 0:
            raise ValueError("Maze dimensions must be positive.")
        if entry == exit:
            raise ValueError("Entry and exit coordinates must be distinct.")

        for name, coordinate in (("Entry", entry), ("Exit", exit)):
            x, y = coordinate
            if not (0 <= x < width and 0 <= y < height):
                raise ValueError(
                    f"{name} coordinates must be inside the maze."
                )

    @staticmethod
    def _new_closed_maze(width: int, height: int) -> Maze:
        """Create the closed maze grid that generation will carve."""
        return Maze.create(width, height)

    def _unvisited_neighbors(
        self,
        maze: Maze,
        coordinate: Coordinate,
        visited: set[Coordinate],
        random_source: Random,
    ) -> list[tuple[Direction, Coordinate]]:
        """Return unvisited adjacent cells in a random direction order."""
        x, y = coordinate
        neighbors: list[tuple[Direction, Coordinate]] = []
        for direction in self._shuffled_directions(random_source):
            neighbor = maze.neighbor_coordinates(x, y, direction)
            if neighbor is not None and neighbor not in visited:
                neighbors.append((direction, neighbor))
        return neighbors

    def _carve_perfect_maze(
        self,
        maze: Maze,
        entry: Coordinate,
        random_source: Random,
    ) -> None:
        """Carve a spanning tree through the closed maze using DFS."""
        visited = {entry}
        pending = [entry]

        while pending:
            coordinate = pending[-1]
            neighbors = self._unvisited_neighbors(
                maze,
                coordinate,
                visited,
                random_source,
            )
            if not neighbors:
                pending.pop()
                continue

            direction, neighbor = neighbors[0]
            maze.open_passage(*coordinate, direction)
            visited.add(neighbor)
            pending.append(neighbor)

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
        maze = self._new_closed_maze(width, height)
        self._carve_perfect_maze(maze, entry, random_source)
        return Maze(
            width=width,
            height=height,
            entry=entry,
            exit=exit,
            cells=maze.cells,
        )
