"""Placement and application of the structural 42 pattern."""

import sys

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

    @staticmethod
    def apply(maze: Maze, quiet: bool = False) -> bool:
        """Block every marked cell of the centered 42 mask.

        Args:
            maze: The maze to apply the pattern to.
            quiet: If True, don't print warning messages.

        Returns:
            True if the pattern was applied, False if omitted due to size.
        """
        if maze.width < 9 or maze.height < 7:
            if not quiet:
                print(
                    "Warning: Maze too small for the 42 pattern "
                    f"({maze.width}x{maze.height} < 9x7). Pattern omitted.",
                    file=sys.stderr,
                )
            return False
        origin_x = (maze.width - len(Pattern42.MASK[0])) // 2
        origin_y = (maze.height - len(Pattern42.MASK)) // 2
        blocked_coordinates = [
            (origin_x + pattern_x, origin_y + pattern_y)
            for pattern_y, row in enumerate(Pattern42.MASK)
            for pattern_x, marker in enumerate(row)
            if marker == "#"
        ]
        entry_overlaps = maze.entry in blocked_coordinates
        exit_overlaps = maze.exit in blocked_coordinates
        if entry_overlaps or exit_overlaps:
            raise ValueError(
                "Entry and exit coordinates cannot overlap Pattern42."
            )
        for block_x, block_y in blocked_coordinates:
            maze.block_cell(block_x, block_y)
        return True
