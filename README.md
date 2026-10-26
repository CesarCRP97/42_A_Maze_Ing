### PRIMERA IDEA DE ESTRUCTURA ###

a_maze_ing/
├── a_maze_ing.py              # PUNTUALIZACIÓN: Archivo ejecutable obligatorio (python3 a_maze_ing.py config.txt)
├── config.txt                 # Archivo de configuración por defecto obligatorio en el repo
├── Makefile                   # Reglas obligatorias: install, run, debug, clean, lint
├── LICENSE.md                 # Licencia legal obligatoria para reutilización de software
├── README.md                  # Documentación obligatoria con formato y secciones específicas
├── pyproject.toml             # Archivo para compilar el paquete reutilizable
├── .gitignore                 # Artifacts de Python out
│
├── mazegen/                   # MÓDULO REUTILIZABLE (Lo que se compila a mazegen-*.whl)
│   ├── __init__.py            # Expone la clase 'MazeGenerator'
│   ├── generator.py           # Lógica de generación (Prim, DFS, etc.)
│   ├── maze.py                # Clase/estructura del laberinto
│   └── utils.py               # Generación de la ruta mínima (BFS/A*) y conversión
│
├── visualizer/                # MÓDULO DE VISUALIZACIÓN
│   ├── __init__.py
│   ├── ascii_display.py       # Renderizado en terminal ASCII (interactivo)
│   └── mlx_display.py         # Opcional: Renderizado en MiniLibX si os venís arriba
│
├── config_parser.py           # Validador de KEY=VALUE de config.txt
├── output_writer.py           # Generador del txt final en formato hexadecimal + coords + ruta
└── tests/                     # Tests con pytest (no se entregan, pero el Makefile debe pasar linting)
