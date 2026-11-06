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
        Pattern42.apply(maze, quiet=True)
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

    def generate_imperfect(
        self,
        width: int,
        height: int,
        entry: Coordinate,
        exit: Coordinate,
        required_open_passages: Iterable[Passage] = (),
        protected_closed_passages: Iterable[Passage] = (),
    ) -> Maze:
        """Generate a connected maze with deliberately retained cycles.

        This implements a "braided" maze generation algorithm suitable for
        Pac-Man-like games:
        - 4 corners and center are guaranteed open
        - At least 2 independent cycles (loops) for alternative routes
        - Dead-ends are minimized (braided structure)
        - Pattern42 is omitted for small mazes with warning
        """
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

        # Apply Pattern42, warning if omitted due to size
        Pattern42.apply(maze, quiet=False)

        # Normalize user constraints first so we can respect them
        user_required_open = self._normalize_passages(
            maze,
            required_open_passages,
            "Required open passages",
        )
        user_protected_closed = self._normalize_passages(
            maze,
            protected_closed_passages,
            "Protected closed passages",
        )

        # Ensure 4 corners and center are open (required for Pac-Man-like games)
        # Track these passages so they're preserved
        corner_center_passages: list[Passage] = []
        corners_and_center = [
            (0, 0),
            (width - 1, 0),
            (0, height - 1),
            (width - 1, height - 1),
            (width // 2, height // 2),
        ]
        for cx, cy in corners_and_center:
            if not maze.cell_at((cx, cy)).blocked:
                for direction in Direction:
                    neighbor = maze.neighbor_coordinates(cx, cy, direction)
                    if neighbor is None or maze.cell_at(neighbor).blocked:
                        continue
                    # Check if this passage conflicts with user's protected_closed
                    # Normalize this passage to check
                    test_passage = ((cx, cy), direction)
                    if direction in (Direction.EAST, Direction.SOUTH):
                        normalized = test_passage
                    else:
                        normalized = (neighbor, direction.opposite)
                    if normalized in user_protected_closed:
                        # User wants this passage closed, try another direction
                        continue
                    maze.open_passage(cx, cy, direction)
                    corner_center_passages.append(((cx, cy), direction))
                    break

        # Add corner/center passages to required_open so they're preserved
        corner_center_normalized = self._normalize_passages(
            maze,
            corner_center_passages,
            "Corner/center passages",
        )
        required_open = user_required_open | corner_center_normalized
        protected_closed = user_protected_closed

        if required_open & protected_closed:
            raise ValueError(
                "A passage cannot be both required open and closed."
            )

        passages: list[Passage] = []
        for row in maze.cells:
            for cell in row:
                if cell.blocked:
                    continue
                for direction in (Direction.EAST, Direction.SOUTH):
                    coordinate = (cell.x, cell.y)
                    neighbor = maze.neighbor_coordinates(
                        *coordinate,
                        direction,
                    )
                    if neighbor is None or maze.cell_at(neighbor).blocked:
                        continue
                    passages.append((coordinate, direction))
        parent = {
            (cell.x, cell.y): (cell.x, cell.y)
            for row in maze.cells
            for cell in row
            if not cell.blocked
        }
        selected_passages = set(required_open)
        for coordinate, direction in required_open:
            neighbor = maze.neighbor_coordinates(*coordinate, direction)
            if neighbor is not None:
                source_root = self._root(parent, coordinate)
                neighbor_root = self._root(parent, neighbor)
                if source_root != neighbor_root:
                    parent[source_root] = neighbor_root

        candidates: list[Passage] = []
        for passage in passages:
            if passage in selected_passages or passage in protected_closed:
                continue
            candidates.append(passage)
        random_source.shuffle(candidates)

        # First pass: connect all components (spanning tree)
        for coordinate, direction in candidates:
            neighbor = maze.neighbor_coordinates(*coordinate, direction)
            if neighbor is None:
                continue
            source_root = self._root(parent, coordinate)
            neighbor_root = self._root(parent, neighbor)
            if source_root != neighbor_root:
                parent[source_root] = neighbor_root
                selected_passages.add((coordinate, direction))

        roots = {self._root(parent, coordinate) for coordinate in parent}
        if len(roots) != 1:
            raise ValueError("Protected closed passages disconnect the maze.")

        # Second pass: add cycles to create loops (braided maze)
        # We need at least 2 independent cycles for Pac-Man-like gameplay
        cycle_candidates = [
            passage
            for passage in candidates
            if passage not in selected_passages
        ]
        cycles_added = 0
        target_cycles = max(2, len(cycle_candidates) // 10)  # At least 2 cycles

        for passage in cycle_candidates:
            if cycles_added >= target_cycles:
                break
            selected_passages.add(passage)
            cycles_added += 1

        # Third pass: add more passages to reduce dead-ends (braiding)
        # Keep about 50% of remaining passages open for braided structure
        remaining = [p for p in cycle_candidates if p not in selected_passages]
        for passage in remaining:
            # Randomly decide to keep this passage open
            if random_source.random() < 0.5:
                selected_passages.add(passage)

        # Ensure we never select ALL passages (would create fully open maze
        # triggering 3x3 check). Always leave at least one non-required passage closed.
        non_required = [p for p in passages if p not in required_open]
        if all(p in selected_passages for p in non_required):
            # Unselect a random non-required passage
            to_unselect = random_source.choice(non_required)
            selected_passages.discard(to_unselect)

        # Close all passages not selected
        for coordinate, direction in passages:
            if (coordinate, direction) not in selected_passages:
                maze.close_passage(*coordinate, direction)

        # Validate no 3x3 open areas (should not trigger now, but keep as safety)
        if self._has_3x3_open_area(maze):
            # If there's a 3x3 open area, close some passages to fix it
            self._fix_3x3_open_areas(maze, random_source)

        return Maze(
            width=width,
            height=height,
            entry=entry,
            exit=exit,
            cells=maze.cells,
        )

    def _has_3x3_open_area(self, maze: Maze) -> bool:
        """Check if maze contains any 3x3 completely open area."""
        for y in range(maze.height - 2):
            for x in range(maze.width - 2):
                # Check if all 9 cells in 3x3 area are walkable and connected
                all_open = True
                for dy in range(3):
                    for dx in range(3):
                        cell = maze.cell_at((x + dx, y + dy))
                        if cell.blocked:
                            all_open = False
                            break
                    if not all_open:
                        break
                if all_open:
                    # Check if internal passages are open (no walls between cells)
                    internal_open = True
                    for dy in range(3):
                        for dx in range(3):
                            cx, cy = x + dx, y + dy
                            cell = maze.cell_at((cx, cy))
                            # Check right neighbor
                            if dx < 2:
                                right = maze.cell_at((cx + 1, cy))
                                east_closed = (
                                    cell.has_wall(Direction.EAST)
                                    or right.has_wall(Direction.WEST)
                                )
                                if east_closed:
                                    internal_open = False
                                    break
                            # Check bottom neighbor
                            if dy < 2:
                                bottom = maze.cell_at((cx, cy + 1))
                                south_closed = (
                                    cell.has_wall(Direction.SOUTH)
                                    or bottom.has_wall(Direction.NORTH)
                                )
                                if south_closed:
                                    internal_open = False
                                    break
                        if not internal_open:
                            break
                    if internal_open:
                        return True
        return False

    def _fix_3x3_open_areas(self, maze: Maze, random_source: Random) -> None:
        """Fix any 3x3 open areas by closing some passages while preserving
        connectivity."""
        from collections import deque

        def is_fully_connected(m: Maze) -> bool:
            """Check if all walkable cells are reachable from entry."""
            reachable = {m.entry}
            pending = deque([m.entry])
            while pending:
                x, y = pending.popleft()
                cell = m.cell_at((x, y))
                for direction in Direction:
                    neighbor = m.neighbor_coordinates(x, y, direction)
                    if neighbor is None or cell.has_wall(direction):
                        continue
                    neighbor_cell = m.cell_at(neighbor)
                    if not neighbor_cell.blocked and neighbor not in reachable:
                        reachable.add(neighbor)
                        pending.append(neighbor)
            walkable_cells = sum(
                not cell.blocked for row in m.cells for cell in row
            )
            return len(reachable) == walkable_cells

        for y in range(maze.height - 2):
            for x in range(maze.width - 2):
                # Check if this 3x3 area is completely open
                all_open = True
                for dy in range(3):
                    for dx in range(3):
                        if maze.cell_at((x + dx, y + dy)).blocked:
                            all_open = False
                            break
                    if not all_open:
                        break
                if not all_open:
                    continue

                # Check internal passages
                internal_passages = []
                for dy in range(3):
                    for dx in range(3):
                        cx, cy = x + dx, y + dy
                        cell = maze.cell_at((cx, cy))
                        if dx < 2:
                            right = maze.cell_at((cx + 1, cy))
                            east_open = (
                                not cell.has_wall(Direction.EAST)
                                and not right.has_wall(Direction.WEST)
                            )
                            if east_open:
                                internal_passages.append(
                                    ((cx, cy), Direction.EAST)
                                )
                        if dy < 2:
                            bottom = maze.cell_at((cx, cy + 1))
                            south_open = (
                                not cell.has_wall(Direction.SOUTH)
                                and not bottom.has_wall(Direction.NORTH)
                            )
                            if south_open:
                                internal_passages.append(
                                    ((cx, cy), Direction.SOUTH)
                                )

                if not internal_passages:
                    continue

                # Close some random internal passages to break the 3x3 open area
                # but only if it doesn't disconnect the maze
                random_source.shuffle(internal_passages)
                # Try to close at least 1 passage, but up to 1/3 of them
                target_close = max(1, len(internal_passages) // 3)
                closed_count = 0
                for coordinate, direction in internal_passages:
                    if closed_count >= target_close:
                        break
                    if maze.cell_at(coordinate).has_wall(direction):
                        continue
                    # Temporarily close and check connectivity
                    maze.close_passage(*coordinate, direction)
                    if is_fully_connected(maze):
                        closed_count += 1
                    else:
                        # Reopen - closing this would disconnect the maze
                        maze.open_passage(*coordinate, direction)
