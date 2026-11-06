# Guía de defensa archivo por archivo

Esta copia mantiene el código ejecutable y añade notas de defensa a los
módulos Python y a los archivos de configuración en los que los comentarios
no alteran el formato. El guion oral completo está en [guion.md](guion.md).

## Raíz

- `a_maze_ing.py`: punto de entrada. Explicar cómo separa el modo de
  generación del interactivo y cómo convierte errores en mensajes y códigos
  de salida.
- `config_parser.py`: convierte el archivo `KEY=VALUE` en una configuración
  validada e inmutable; mencionar claves obligatorias, tipos, coordenadas y
  límites.
- `config.txt`: ejemplo de parámetros. Explicar dimensiones, coordenadas
  desde cero, modo `PERFECT` y destino de salida.
- `output_writer.py`: serializa máscaras hexadecimales, extremos y ruta
  mínima; falla si no existe ruta válida.
- `maze.txt`: resultado ya generado. No se insertan comentarios porque cada
  línea forma parte del formato de intercambio que debe poder consumirse
  directamente.
- `README.md`: presentación, arquitectura e instrucciones generales. Remite
  a los guiones añadidos para preparar la defensa.
- `TUTORIAL.md`: pasos de uso, parámetros, interacción y formato; sirve para
  explicar cómo probar el programa desde una terminal.
- `Makefile`: automatiza entorno, instalación, ejecución, depuración, lint,
  pruebas y construcción del paquete.
- `pyproject.toml`: declara la construcción con setuptools, los requisitos,
  dependencias de ejecución/desarrollo y qué paquete se distribuye.
- `.gitignore`: excluye cachés, entornos locales y artefactos generados, no
  archivos fuente.
- `LICENSE.md`: licencia MIT. Se conserva sin anotaciones para no cambiar el
  texto legal; basta explicar que permite reutilización bajo sus condiciones.
- `mazegen-0.1.0-py3-none-any.whl`: distribución binaria instalable; no es
  editable como texto. La guía explica su función sin alterar su contenido.
- `mazegen-0.1.0.tar.gz`: archivo comprimido de distribución fuente; se
  conserva íntegro por ser un artefacto de empaquetado.

## Paquete `mazegen`

- `mazegen/__init__.py`: define la fachada y los símbolos públicos que
  expone la biblioteca.
- `mazegen/types.py`: centraliza el alias `Coordinate`, evitando convenciones
  diferentes en módulos distintos.
- `mazegen/maze.py`: define `Direction`, `Cell` y `Maze`; concentra las
  invariantes de paredes, límites y conectividad.
- `mazegen/generator.py`: implementa los modos perfecto e imperfecto,
  semilla reproducible, restricciones de pasajes y comprobaciones del
  resultado.
- `mazegen/pattern42.py`: ubica la máscara, comprueba que quepa y evita
  bloquear los extremos.
- `mazegen/solver.py`: usa BFS para hallar una ruta mínima y reconstruirla
  mediante predecesores.

## Paquete `visualizer`

- `visualizer/__init__.py`: expone las funciones públicas de dibujo e
  interacción.
- `visualizer/ascii_display.py`: representa paredes, extremos, bloqueos y
  solución; valida los movimientos antes de dibujarlos.
- `visualizer/interactive.py`: gestiona lectura de teclado multiplataforma,
  estado de interfaz, regeneración y restauración del terminal.

## Pruebas

- `tests/test_cli.py`: comprueba salida, errores, códigos y selección de
  modos del programa principal.
- `tests/test_config_parser.py`: prueba parsing, conversiones y rechazo de
  configuraciones no válidas.
- `tests/test_generator.py`: comprueba propiedades estructurales de ambas
  estrategias y las restricciones sobre pasos.
- `tests/test_interactive.py`: prueba teclas, cambios de estado y entrada de
  terminal sin interacción manual.
- `tests/test_maze.py`: demuestra validaciones e invariantes del modelo.
- `tests/test_output_writer.py`: fija el formato exacto y verifica escritura
  del resultado.
- `tests/test_pattern42.py`: comprueba máscara, dimensiones y extremos.
- `tests/test_solver.py`: verifica camino mínimo y casos sin solución.
- `tests/test_visualizer.py`: prueba dibujo, colores y validación de rutas.

## Archivos de metadatos y distribuciones generadas

- `mazegen.egg-info/PKG-INFO`: metadatos de la distribución; se genera a
  partir del proyecto y se deja intacto para no falsear la información del
  paquete.
- `mazegen.egg-info/SOURCES.txt`: inventario de archivos fuente incluidos en
  el paquete.
- `mazegen.egg-info/dependency_links.txt`: metadatos de enlaces de
  dependencias; está vacío porque no hay enlaces adicionales.
- `mazegen.egg-info/requires.txt`: dependencias de ejecución y extras de
  desarrollo.
- `mazegen.egg-info/top_level.txt`: declara el nombre de paquete de nivel
  superior, `mazegen`.
- `dist/mazegen-0.1.0-py3-none-any.whl`: copia del wheel generada en la
  carpeta de distribución; se mantiene binaria.
- `dist/mazegen-0.1.0.tar.gz`: copia del archivo fuente empaquetado; se
  mantiene comprimida.

Los formatos de salida, la licencia, los metadatos de construcción y los
binarios no se modifican con comentarios porque eso podría invalidarlos. Su
explicación para la defensa queda recogida aquí.
