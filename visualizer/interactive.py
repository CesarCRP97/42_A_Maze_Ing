"""Interactive terminal-based maze visualizer (cross-platform)."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, replace

from mazegen.generator import MazeGenerator
from mazegen.maze import Direction, Maze
from mazegen.solver import solve_shortest_path
from mazegen.types import Coordinate
from visualizer.ascii_display import render_maze


# Cross-platform getch implementation
class Getch:
    """Cross-platform single character input."""

    def __init__(self) -> None:
        if os.name == "nt":
            import msvcrt

            self._getch = msvcrt.getch
        else:
            import termios

            self._fd = sys.stdin.fileno()
            self._old_settings = termios.tcgetattr(  # type: ignore
                self._fd
            )

    def __call__(self) -> bytes:
        if os.name == "nt":
            return self._getch()
        import termios
        import tty

        try:
            tty.setraw(self._fd)  # type: ignore[attr-defined]
            return sys.stdin.read(1).encode()
        finally:
            termios.tcsetattr(  # type: ignore[attr-defined]
                self._fd,
                termios.TCSADRAIN,  # type: ignore[attr-defined]
                self._old_settings,
            )

    def __enter__(self) -> "Getch":
        return self

    def __exit__(self, *args: object) -> None:
        pass


@dataclass(frozen=True)
class VisualizerState:
    """Immutable state for the interactive visualizer."""

    maze: Maze
    solution: list[Direction] | None
    show_solution: bool
    use_color: bool
    generator: MazeGenerator
    config_width: int
    config_height: int
    config_entry: Coordinate
    config_exit: Coordinate
    config_perfect: bool
    config_seed: int | None
    last_action: str = ""


# Synthwave color palette (ANSI 256-color codes)
COLOR_PALETTE = {
    "synthwave_cyan": 51,
    "synthwave_magenta": 198,
    "synthwave_yellow": 226,
    "synthwave_pink": 201,
    "synthwave_purple": 141,
    "synthwave_orange": 208,
    "synthwave_green": 82,
    "synthwave_blue": 75,
    "white": 15,
    "gray": 244,
    "dark_gray": 238,
    "red": 196,
    "green": 46,
    "blue": 39,
    "yellow": 226,
    "magenta": 201,
    "cyan": 51,
}

# Ordered list for cycling through colors
COLOR_OPTIONS = [
    COLOR_PALETTE["synthwave_cyan"],
    COLOR_PALETTE["synthwave_magenta"],
    COLOR_PALETTE["synthwave_yellow"],
    COLOR_PALETTE["synthwave_pink"],
    COLOR_PALETTE["synthwave_purple"],
    COLOR_PALETTE["synthwave_orange"],
    COLOR_PALETTE["synthwave_green"],
    COLOR_PALETTE["synthwave_blue"],
    COLOR_PALETTE["white"],
    COLOR_PALETTE["gray"],
    COLOR_PALETTE["red"],
    COLOR_PALETTE["green"],
    COLOR_PALETTE["blue"],
    COLOR_PALETTE["cyan"],
    COLOR_PALETTE["magenta"],
    COLOR_PALETTE["yellow"],
]

# Current color indices (for cycling)
_color_indices = {
    "wall": 0,
    "path": 1,
    "entry": 2,
    "exit": 3,
    "blocked": 4,
    "pattern42": 5,
}


def _cycle_color(name: str) -> int:
    """Return the next color in the cycle for the given element."""
    idx = _color_indices[name]
    _color_indices[name] = (idx + 1) % len(COLOR_OPTIONS)
    return COLOR_OPTIONS[_color_indices[name]]


def _get_color(name: str) -> int:
    """Get current color for element."""
    return COLOR_OPTIONS[_color_indices[name]]


def _build_initial_state(
    generator: MazeGenerator,
    width: int,
    height: int,
    entry: Coordinate,
    exit: Coordinate,
    perfect: bool,
    seed: int | None,
) -> VisualizerState:
    """Generate initial maze and build state."""
    if perfect:
        maze = generator.generate_perfect(width, height, entry, exit)
    else:
        maze = generator.generate_imperfect(width, height, entry, exit)
    solution = solve_shortest_path(maze)
    return VisualizerState(
        maze=maze,
        solution=solution,
        show_solution=True,
        use_color=True,
        generator=generator,
        config_width=width,
        config_height=height,
        config_entry=entry,
        config_exit=exit,
        config_perfect=perfect,
        config_seed=seed,
    )


def _regenerate_maze(state: VisualizerState) -> VisualizerState:
    """Generate a new maze with the same configuration (new random seed)."""
    new_generator = MazeGenerator(seed=None)  # None = random seed
    if state.config_perfect:
        maze = new_generator.generate_perfect(
            state.config_width,
            state.config_height,
            state.config_entry,
            state.config_exit,
        )
    else:
        maze = new_generator.generate_imperfect(
            state.config_width,
            state.config_height,
            state.config_entry,
            state.config_exit,
        )
    solution = solve_shortest_path(maze)
    return replace(
        state,
        maze=maze,
        solution=solution,
        generator=new_generator,
        last_action="Nuevo laberinto generado",
    )


def _toggle_solution(state: VisualizerState) -> VisualizerState:
    """Toggle solution visibility."""
    action = "mostrada" if not state.show_solution else "ocultada"
    return replace(
        state,
        show_solution=not state.show_solution,
        last_action=f"Solución {action}",
    )


def _toggle_color_mode(state: VisualizerState) -> VisualizerState:
    """Toggle color mode on/off."""
    action = "activados" if not state.use_color else "desactivados"
    return replace(
        state,
        use_color=not state.use_color,
        last_action=f"Colores {action}",
    )


def _clear_screen() -> None:
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="")


def _render_state(state: VisualizerState) -> str:
    """Render the current state to a string."""
    maze_str = render_maze(
        maze=state.maze,
        solution=state.solution if state.show_solution else None,
        show_solution=state.show_solution,
        use_color=state.use_color,
    )

    mode_str = "Perfecto" if state.config_perfect else "Imperfecto"
    gen_seed = state.generator.seed
    seed_str = str(gen_seed) if gen_seed else "aleatoria"

    help_lines = [
        "",
        f"Modo: {mode_str} | Tamaño: "
        f"{state.config_width}x{state.config_height} | Semilla: {seed_str}",
        "",
        "Controles:",
        "  R - Regenerar laberinto (nueva semilla)",
        "  S - Mostrar/Ocultar solución",
        "  C - Toggle colores ON/OFF",
        "  Q - Salir",
        "",
    ]

    if state.last_action:
        help_lines.insert(0, f"→ {state.last_action}")
        help_lines.insert(1, "")

    return maze_str + "\n" + "\n".join(help_lines)


def _handle_key(state: VisualizerState, key: bytes) -> VisualizerState | None:
    """Handle keyboard input. Returns new state or None to quit."""
    key_str = key.decode("utf-8", errors="ignore").lower()

    if key_str in ("q", "\x1b"):  # q or ESC
        return None
    if key_str == "r":
        return _regenerate_maze(state)
    if key_str == "s":
        return _toggle_solution(state)
    if key_str == "c":
        return _toggle_color_mode(state)
    return state


def run_interactive(
    width: int,
    height: int,
    entry: Coordinate,
    exit: Coordinate,
    perfect: bool,
    seed: int | None = None,
) -> None:
    """Run the interactive maze visualizer (cross-platform)."""
    getch = Getch()

    # Build initial state
    generator = MazeGenerator(seed=seed)
    state = _build_initial_state(
        generator, width, height, entry, exit, perfect, seed
    )

    # Main loop
    try:
        while True:
            _clear_screen()
            output = _render_state(state)
            print(output, end="")
            sys.stdout.flush()

            key = getch()
            new_state = _handle_key(state, key)
            if new_state is None:
                break
            state = new_state
    except KeyboardInterrupt:
        pass
    finally:
        _clear_screen()
        print("¡Hasta luego!")


if __name__ == "__main__":
    # Demo run
    run_interactive(
        width=20,
        height=10,
        entry=(0, 0),
        exit=(19, 9),
        perfect=False,
        seed=42,
    )
