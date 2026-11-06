# Guía rápida de A-Maze-ing

El programa genera laberintos, calcula la ruta más corta y permite guardar el resultado o visualizarlo en una terminal interactiva.

## 1. Instalar y arrancar

Desde la raíz del repositorio, con Python y `make` disponibles:

```bash
make install
```

Esto crea `.venv` si no existe e instala el paquete, Pydantic y las herramientas de desarrollo. El paquete declara Python >= 3.10; las comprobaciones actuales se han ejecutado con el Python de `.venv`, no con todas las versiones admitidas.

Para generar y guardar un laberinto:

```bash
make run
```

O, después de instalar, sin repetir la instalación:

```bash
.venv/bin/python a_maze_ing.py config.txt
```

El programa imprime un resumen y escribe `maze.txt`. Si el archivo existe, lo sobrescribe. Este modo no dibuja el laberinto en pantalla.

Para usar otra configuración:

```bash
.venv/bin/python a_maze_ing.py mi_config.txt
# Alternativa con Make:
make run CONFIG=mi_config.txt
```

Las rutas relativas de configuración y salida se interpretan desde el directorio donde ejecutas el comando.

## 2. Configurar el laberinto

El `config.txt` incluido contiene:

```ini
WIDTH=20
HEIGHT=10
ENTRY=0,0
EXIT=19,9
OUTPUT_FILE=maze.txt
PERFECT=False
```

| Clave | Significado |
| --- | --- |
| `WIDTH`, `HEIGHT` | Número de columnas y filas. Usa al menos 2 en cada dimensión. |
| `ENTRY` | Celda de entrada, en formato `x,y`. |
| `EXIT` | Celda de salida, distinta de la entrada. |
| `OUTPUT_FILE` | Archivo de salida; su carpeta debe existir. |
| `PERFECT` | `True`: sin ciclos, una única ruta simple entre dos celdas transitables. `False`: permite ciclos y rutas alternativas. |
| `SEED` | Entero opcional para repetir la generación con la misma configuración y versión del código. |

Las coordenadas empiezan en cero: `0,0` es la esquina superior izquierda. `x` aumenta hacia la derecha e `y` hacia abajo. Entrada y salida deben estar dentro del tablero y no coincidir con celdas bloqueadas por el patrón 42.

Puedes añadir, por ejemplo, `SEED=42`. Si omites `SEED`, la generación usa aleatoriedad sin una semilla fija. Se aceptan líneas vacías y comentarios con `#`.

El patrón 42 se forma bloqueando celdas en el centro. Necesita al menos 9 columnas y 7 filas; en tableros menores se omite. Actualmente el modo imperfecto muestra un aviso al omitirlo, mientras que el perfecto lo omite silenciosamente.

## 3. Visualización interactiva

Ejecuta desde una terminal real, no mediante una entrada redirigida:

```bash
.venv/bin/python a_maze_ing.py config.txt --interactive
```

También puedes usar `-i` en lugar de `--interactive`.

| Tecla | Acción |
| --- | --- |
| `R` | Generar otro laberinto con las mismas dimensiones, extremos y modo. |
| `S` | Mostrar u ocultar la solución. |
| `C` | Activar o desactivar los colores ANSI. |
| `Q` o `Esc` | Salir. |

No necesitas pulsar Enter. La solución y los colores están activados inicialmente. `R` genera sin semilla fija, aunque hayas configurado `SEED`.

Leyenda: `E` es entrada, `X` salida, `*` solución y `###` celda bloqueada. Los caracteres `+`, `-` y `|` dibujan los muros.

**Importante:** el modo interactivo no escribe ni actualiza `OUTPUT_FILE`. Son dos recorridos separados del programa: uno guarda y el otro visualiza. Sin semilla fija, ejecutarlos por separado puede producir laberintos distintos.

## 4. Qué hace cada parte

El flujo principal es:

```text
config.txt → config_parser.py → MazeGenerator → Maze
                                               ├─ solver → output_writer → archivo
                                               └─ solver → visualizer → terminal
```

| Archivo o módulo | Responsabilidad |
| --- | --- |
| `a_maze_ing.py` | Lee los argumentos con argparse, carga la configuración y elige generación o interacción. |
| `config_parser.py` | Lee `KEY=VALUE`, convierte tipos y comprueba claves, coordenadas y valores. Devuelve un `MazeConfig` inmutable de Pydantic. |
| `mazegen/types.py` | Define el tipo compartido de coordenadas. |
| `mazegen/maze.py` | Define `Cell`, `Maze` y `Direction`. Representa celdas, paredes y bloqueos; comprueba estructura, muros compartidos, bordes cerrados y conectividad. |
| `mazegen/generator.py` | Genera el tablero. El modo perfecto selecciona conexiones sin ciclos mediante Union-Find; el imperfecto conecta las celdas, añade ciclos e intenta reducir callejones y eliminar áreas 3×3 completamente abiertas. |
| `mazegen/pattern42.py` | Coloca el patrón 42 centrado mediante celdas bloqueadas. |
| `mazegen/solver.py` | Usa BFS: explora por distancia y reconstruye una ruta mínima de entrada a salida. Devuelve direcciones, o `None` si no hay ruta. |
| `output_writer.py` | Revalida el laberinto, calcula su solución y escribe la representación hexadecimal. |
| `visualizer/ascii_display.py` | Convierte el laberinto y una ruta opcional en texto ASCII con colores opcionales. |
| `visualizer/interactive.py` | Lee teclas y gestiona regeneración, solución visible y colores. |
| `mazegen/__init__.py` | Expone la API reutilizable: generador, modelos, solver y patrón. |
| `tests/` | Contiene las pruebas ejecutadas con unittest. |
| `pyproject.toml` | Declara dependencias y empaquetado de `mazegen`; el paquete no incluye la CLI ni `visualizer`. |
| `Makefile` | Agrupa instalación, ejecución, depuración, análisis y pruebas. |

## 5. Cómo leer el archivo generado

La salida contiene:

1. `HEIGHT` filas con `WIDTH` dígitos hexadecimales por fila.
2. Una línea vacía.
3. Coordenadas de entrada.
4. Coordenadas de salida.
5. Ruta mínima como letras `N`, `E`, `S`, `W`.

Cada dígito representa las paredes cerradas de una celda: norte vale 1, este 2, sur 4 y oeste 8. Un bit activado significa **pared**, no paso. `F` indica las cuatro paredes cerradas y `0` ninguna. Las coordenadas designan celdas de entrada y salida; los bordes exteriores permanecen cerrados.

## 6. Comprobar y depurar

```bash
make test    # Pruebas unitarias
make lint    # Flake8 y mypy
make check   # Lint y pruebas
make debug   # Arranque bajo el depurador pdb
.venv/bin/python a_maze_ing.py --help
```

Estos objetivos de Make, salvo `clean`, dependen de la instalación. En `pdb`, `n` avanza, `s` entra en una función, `c` continúa y `q` termina.

`make clean` elimina cachés y artefactos de construcción, pero también `dist/` y `*.egg-info`, actualmente versionados: puede dejar eliminaciones visibles en Git. No lo necesitas para ejecutar el programa.

## 7. Validaciones y límites

El parser rechaza dimensiones menores que 2 antes de generar o abrir el visualizador. La CLI muestra un error de configuración, sin traceback, y termina con código 2.

La API de generación imperfecta admite un tablero 2×2 con todos sus pasos internos obligatoriamente abiertos. En tableros mayores, la reparación de áreas 3×3 conserva los pasos obligatorios y solo cierra un paso opcional por área completamente abierta. Si las restricciones fuerzan los doce pasos internos de un área 3×3, son incompatibles con esa regla y se rechazan con `ValueError`.

Las pruebas automatizadas reducen el riesgo de regresiones, pero no garantizan ausencia de fallos. La comprobación de tipos para Windows tampoco sustituye una ejecución real en Windows.

## 8. Paquete reutilizable

El código de `mazegen` se distribuye como wheel y archivo fuente en `dist/`. Desde el repositorio instalado, puedes reconstruir ambos con:

```bash
.venv/bin/python -m build --no-isolation
```

El wheel instala la biblioteca, no la aplicación completa. Para utilizar la CLI y el visualizador, conserva el repositorio y sigue los pasos anteriores.
