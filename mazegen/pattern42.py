"""Placement and application of the structural 42 pattern."""

from mazegen.maze import Maze


class Pattern42:
    """Block the fixed 42 mask at the center of a maze."""

    MASK = (
        "#.#.###",
        "#.#...#",
        "###.###",
        "..#.#..",
        "..#.###",
    )

    @classmethod
    def apply(cls, maze: Maze) -> None:
        """Block every marked cell of the centered 42 mask."""
        if maze.width < 8 or maze.height < 7:
            return
        origin_x = (maze.width - len(cls.MASK[0])) // 2
        origin_y = (maze.height - len(cls.MASK)) // 2
        for pattern_y, row in enumerate(cls.MASK):
            for pattern_x, marker in enumerate(row):
                if marker == "#":
                    maze.block_cell(origin_x + pattern_x, origin_y + pattern_y)
