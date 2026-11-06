# Guia de defensa archivo por archivo

Este inventario refleja la copia actual: ya no contiene `dist/`,
`mazegen.egg-info/` ni el archivo fuente tar.gz. Para explicaciones técnicas
completas, ve a [DOCUMENTACION_COMPLETA.md](DOCUMENTACION_COMPLETA.md); para
la presentación oral, a [guion.md](guion.md).

## Archivos de la raiz

| Archivo | Papel en el proyecto | Que explicar |
|---|---|---|
| `a_maze_ing.py` | Entrada de consola (CLI). | Argumentos, lectura de configuración, seleccion normal/interactivo y conversion de excepciones en mensajes y codigos de salida. |
| `config_parser.py` | Parser y validación inicial. | Sintaxis KEY=VALUE, comentarios completos, conversion de tipos, limites y `MazeConfig` congelado. |
| `config.txt` | Ejemplo por defecto. | Dimensiones, origen de coordenadas, extremos, modo y ruta de salida. |
| `output_writer.py` | Serializacion y escritura. | Mascara de paredes, coordenadas, ruta BFS, validación previa y errores de archivo. |
| `maze.txt` | Ejemplo de resultado generado. | Filas hexadecimales, línea vacia, entrada, salida y solución. No insertar comentarios: el formato debe conservarse. |
| `README.md` | Descripcion y documentación del paquete. | Objetivo, arquitectura, instalación, algoritmo, equipo, recursos y uso de IA documentado. |
| `TUTORIAL.md` | Manual practico. | Comandos, parametros, teclas interactivas, estructura, salida y limites. |
| `guion.md` | Exposicion breve. | Presentacion oral y preguntas técnicas frecuentes. |
| `DOCUMENTACION_COMPLETA.md` | Manual tecnico detallado. | Modelo, algoritmos, métodos, formato, pruebas, empaquetado y requisitos del subject. |
| `GUIA_ARCHIVOS.md` | Mapa de archivos. | Responsabilidad de cada archivo sin tener que recorrer el árbol a ciegas. |
| `Makefile` | Automatizacion de tareas. | Entorno virtual, instalación, ejecución, depuracion, lint, test y construcción. Usa una ruta de Python POSIX. |
| `pyproject.toml` | Metadatos de construcción e instalación. | Version, Python mínimo, dependencia Pydantic, extras de desarrollo y seleccion solo de `mazegen*`. |
| `.gitignore` | Exclusiones de Git. | Bytecode, caches, entorno virtual, build y metadatos de paquete. |
| `LICENSE.md` | Licencia MIT. | Permite reutilizar y distribuir manteniendo el aviso. No editar el texto legal para anadir comentarios. |
| `mazegen-0.1.0-py3-none-any.whl` | Wheel de la biblioteca. | Paquete binario instalable exigido; incluye la biblioteca, no la CLI ni el visualizador. |

## Paquete `mazegen`

| Archivo | Clases / funciones | Idea para defender |
|---|---|---|
| `mazegen/__init__.py` | API pública `MazeGenerator`, `Maze`, `Cell`, `Direction`, `solve_shortest_path`, `Route`, `Pattern42`. | Fachada de importacion que evita que el consumidor conozca toda la estructura interna. |
| `mazegen/types.py` | `Coordinate`. | Alias compartido para coordenadas `(x, y)`. |
| `mazegen/maze.py` | `Direction`, `Cell`, `Maze`. | Dominio e invariantes; consultar el capitulo 4 del manual completo para todos los métodos. |
| `mazegen/generator.py` | `MazeGenerator`, `Passage`. | Kruskal/Union-Find, restricciones y creacion de ciclos; capitulos 6 y 7 del manual. |
| `mazegen/pattern42.py` | `Pattern42.apply`. | Mascara de celdas bloqueadas, centrado, mínimo de tamano y extremos protegidos. |
| `mazegen/solver.py` | `solve_shortest_path`, `_build_route`, `Route`. | BFS y reconstruccion de la ruta mínima por predecesores. |

## Paquete `visualizer`

| Archivo | Clases / funciones | Idea para defender |
|---|---|---|
| `visualizer/__init__.py` | `render_maze`, `run_interactive`. | Expone el renderizador y la interfaz pública. |
| `visualizer/ascii_display.py` | `render_maze`, `_solution_cells`. | Dibuja paredes y marcadores, colores ANSI opcionales y valida que el camino suministrado sea legal. |
| `visualizer/interactive.py` | `Getch`, `VisualizerState`, `run_interactive` y manejadores. | Lectura por plataforma, estado de pantalla y transiciones de teclado; capitulo 12 del manual. |

## Pruebas

Todas se encuentran en `tests/` y usan `unittest`.

| Archivo | Contrato cubierto |
|---|---|
| `tests/test_cli.py` | Argumentos, ambos modos, resumen, errores, escritura y codigos de salida. |
| `tests/test_config_parser.py` | Formato, comentarios, conversiones, coordenadas e inmutabilidad. |
| `tests/test_generator.py` | Conectividad, árbol, ciclos, callejones, semilla y restricciones. |
| `tests/test_interactive.py` | Teclas, transiciones, regeneracion, lectura de terminal y restauracion. |
| `tests/test_maze.py` | Forma de cuadrícula, paredes, fronteras, extremos, bloqueo y conectividad. |
| `tests/test_output_writer.py` | Serializacion exacta, escritura y rechazo de modelo incoherente. |
| `tests/test_pattern42.py` | Mascara, posicion, tamanos insuficientes y solapamiento de extremos. |
| `tests/test_solver.py` | Ruta mas corta, extremos correctos y ausencia de ruta. |
| `tests/test_visualizer.py` | Dibujo ASCII, colores y validación de rutas. |

Las pruebas son una ayuda para detectar regresiones; no reemplazan la
verificacion con el analizador oficial del subject si esta disponible.

## Nota sobre archivos eliminados

`dist/`, `mazegen.egg-info/` y el tarball de distribución se quitaron porque
son artefactos regenerables o redundantes con el wheel que se conserva. El
codigo fuente y `pyproject.toml` permiten volver a construir la distribución.
