"""Domain models for maze cells and structure."""

from enum import IntEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Direction(IntEnum):
    """Cardinal directions and their hexadecimal output bits."""

    NORTH = 0b0001
    EAST = 0b0010
    SOUTH = 0b0100
    WEST = 0b1000

    @property
    def opposite(self) -> "Direction":
        """Return the direction of the adjacent cell that faces this one."""
        return {
            Direction.NORTH: Direction.SOUTH,
            Direction.EAST: Direction.WEST,
            Direction.SOUTH: Direction.NORTH,
            Direction.WEST: Direction.EAST,
        }[self]

    @property
    def delta(self) -> tuple[int, int]:
        """Return the coordinate offset associated with this direction."""
        return {
            Direction.NORTH: (0, -1),
            Direction.EAST: (1, 0),
            Direction.SOUTH: (0, 1),
            Direction.WEST: (-1, 0),
        }[self]


class Cell(BaseModel):
    """A cell identified by coordinates and bounded by four walls."""

    model_config = ConfigDict(validate_assignment=True)

    x: int = Field(ge=0)
    y: int = Field(ge=0)
    walls: set[Direction] = Field(default_factory=lambda: set(Direction))

    @property
    def wall_mask(self) -> int:
        """Return wall flags packed into the hexadecimal output mask."""
        return sum(direction.value for direction in self.walls)

    def has_wall(self, direction: Direction) -> bool:
        """Return whether this cell is closed in ``direction``."""
        return direction in self.walls


class Maze(BaseModel):
    """Mutable cell grid indexed by ``(x, y)`` coordinates."""

    model_config = ConfigDict(validate_assignment=True)

    width: int = Field(gt=0)
    height: int = Field(gt=0)
    cells: list[list[Cell]]

    @model_validator(mode="after")
    def validate_grid(self) -> "Maze":
        """Ensure that the stored cells form the declared rectangular grid."""
        if len(self.cells) != self.height:
            raise ValueError("The number of cell rows must match height.")

        for y, row in enumerate(self.cells):
            if len(row) != self.width:
                raise ValueError("Every cell row must match width.")
            for x, cell in enumerate(row):
                if (cell.x, cell.y) != (x, y):
                    raise ValueError(
                        "Cell coordinates must match their grid position."
                    )
        return self

    @classmethod
    def create(cls, width: int, height: int) -> "Maze":
        """Create a rectangular maze whose cells start fully closed."""
        return cls(
            width=width,
            height=height,
            cells=[
                [Cell(x=x, y=y) for x in range(width)]
                for y in range(height)
            ],
        )

    def cell_at(self, x: int, y: int) -> Cell:
        """Return the cell stored at ``(x, y)``."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError(f"Cell ({x}, {y}) is outside the maze bounds.")
        return self.cells[y][x]

    def neighbor_coordinates(
        self,
        x: int,
        y: int,
        direction: Direction,
    ) -> tuple[int, int] | None:
        """Return adjacent coordinates, or ``None`` at an external border."""
        self.cell_at(x, y)
        delta_x, delta_y = direction.delta
        neighbor_x, neighbor_y = x + delta_x, y + delta_y
        if 0 <= neighbor_x < self.width and 0 <= neighbor_y < self.height:
            return neighbor_x, neighbor_y
        return None

    def open_passage(self, x: int, y: int, direction: Direction) -> None:
        """Open the shared wall between a cell and its neighbor."""
        neighbor = self.neighbor_coordinates(x, y, direction)
        if neighbor is None:
            raise ValueError("An external maze border cannot be opened.")

        self.cell_at(x, y).walls.discard(direction)
        self.cell_at(*neighbor).walls.discard(direction.opposite)

    def has_coherent_walls(self) -> bool:
        """Check shared-wall symmetry and closed external borders."""
        for y, row in enumerate(self.cells):
            for x, cell in enumerate(row):
                for direction in Direction:
                    neighbor = self.neighbor_coordinates(x, y, direction)
                    if neighbor is None:
                        if not cell.has_wall(direction):
                            return False
                        continue

                    neighbor_cell = self.cell_at(*neighbor)
                    if cell.has_wall(direction) != neighbor_cell.has_wall(
                        direction.opposite
                    ):
                        return False
        return True
