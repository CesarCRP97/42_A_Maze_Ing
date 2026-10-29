_Este proyecto ha sido realizado por aarellan y crubio-p_

# A-Maze-ing



Generador y visualizador de laberintos en Python.

Este proyecto propone una estructura modular para crear, configurar y representar laberintos de forma reutilizable, con un ejecutable principal, un módulo de generación y una capa de visualización.

## Descripción general

La idea principal es separar claramente la lógica del laberinto, la configuración del programa y la salida visual o textual para mantener el proyecto escalable y fácil de mantener.

- Generación del laberinto
- Validación de configuración
- Escritura del resultado final
- Visualización en terminal o gráfica
- Estructura reutilizable como paquete Python

## Estructura del proyecto

```text
a_maze_ing/
├── a_maze_ing.py              # Archivo ejecutable principal
│                              # Ejemplo: python3 a_maze_ing.py config.txt
├── config.txt                 # Configuración por defecto del proyecto
├── Makefile                   # Comandos obligatorios: install, run, debug, clean, lint
├── LICENSE.md                 # Licencia de reutilización
├── README.md                  # Documentación del proyecto
├── pyproject.toml             # Configuración del paquete reutilizable
├── .gitignore                 # Archivos y artefactos generados por Python
│
├── mazegen/                   # Módulo reutilizable (compilable como mazegen-*.whl)
│   ├── __init__.py            # Expone la clase MazeGenerator
│   ├── generator.py           # Lógica de generación (Prim, DFS, etc.)
│   ├── maze.py                # Estructura del laberinto
│   └── utils.py               # Ruta mínima (BFS/A*) y conversión de datos
│
├── visualizer/                # Módulo de visualización
│   ├── __init__.py
│   ├── ascii_display.py       # Renderizado en terminal ASCII (interactivo)
│   └── mlx_display.py         # Opcional: renderizado con MiniLibX
│
├── config_parser.py           # Validador de ficheros KEY=VALUE
├── output_writer.py           # Generador del resultado final en formato hexadecimal + coordenadas + ruta
├── tests/                     # Tests con pytest
│                              # No se entregan, pero el Makefile debe pasar linting
└──
```

## Módulos principales

### `mazegen/`
Contiene la lógica central para generar y manipular el laberinto. Está pensado para ser reutilizable y exportable como paquete.

### `visualizer/`
Responsable de representar el laberinto en distintos formatos, principalmente por consola o mediante una interfaz gráfica opcional.

### `config_parser.py`
Se encarga de validar y procesar la configuración del archivo `config.txt`.

### `output_writer.py`
Genera la salida final del proyecto en un formato legible y útil para análisis o visualización posterior.

## Flujo esperado

1. El usuario ejecuta el programa principal.
2. Se carga la configuración desde `config.txt`.
3. Se genera el laberinto con la estrategia deseada.
4. Se calcula la ruta mínima si corresponde.
5. Se imprime o escribe el resultado final.

## Uso rápido

```bash
python3 a_maze_ing.py config.txt
```

## Comandos recomendados

```bash
make install
make run
make debug
make clean
make lint
```

## Objetivo del proyecto

Crear una base sólida para un sistema de generación y resolución de laberintos, con una arquitectura limpia, documentación útil y posibilidad de reutilización del módulo principal.

---

Proyecto en fase de diseño inicial. La estructura puede adaptarse según se avance en la implementación.

## Cuaderno de bitácora

### Día 1

División de trabajo y empezamos fuerte:

```text
CÉSAR:      Clases Maze y Cell

ALEX:       Parseo (Que lea del config.txt y devuelva un objeto con todos los settings)
```

