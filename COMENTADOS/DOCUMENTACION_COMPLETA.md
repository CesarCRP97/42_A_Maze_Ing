# Documentacion completa de A-Maze-ing

Este manual explica el proyecto tal como esta implementado en esta copia. Su
objetivo es que puedas describir el recorrido de una ejecución, justificar
las decisiones técnicas y ubicar la responsabilidad de cada archivo. No
sustituye leer el codigo: usalo para preparar una explicación que puedas
reproducir con tus propias palabras.

- [Guion oral](guion.md): versión breve para presentar el proyecto.
- [Guia de archivos](GUIA_ARCHIVOS.md): inventario y resumen por fichero.
- [Tutorial](TUTORIAL.md): instalación, ejecución y uso.
- [README](README.md): presentación pública, biblioteca, equipo y recursos.

## 1. Que hace el proyecto

A-Maze-ing genera una cuadrícula de celdas, conecta sus pasillos segun uno
de dos modos, calcula una ruta mínima y ofrece dos formas de salida:

1. **Modo normal:** guarda el laberinto en un archivo de texto con una
   representación hexadecimal de paredes, las coordenadas de los extremos y
   la ruta.
2. **Modo interactivo:** dibuja el tablero en ASCII y permite regenerarlo,
   mostrar u ocultar la solución y cambiar los colores de las paredes.

El paquete `mazegen` contiene la parte reutilizable: modelo, generador,
patron 42 y solver. La CLI, el parser de configuración, el escritor y el
visualizador son capas de la aplicación.

## 2. Arquitectura y recorrido completo

```text
config.txt
    |
    v
a_maze_ing.py -- argparse y seleccion del modo
    |
    +-- config_parser.py --> MazeConfig validado
                                |
                                v
                         MazeGenerator
                                |
                                v
                              Maze
                         /            \
                        v              v
                  solve_shortest_path  solve_shortest_path
                        |              |
                        v              v
                 output_writer     visualizer
                        |              |
                     maze.txt      terminal ASCII
```

En el flujo normal, `a_maze_ing.py` interpreta el argumento que nombra el
archivo de configuración. `parse_config` devuelve un `MazeConfig`; el CLI
crea un `MazeGenerator` con la semilla elegida y llama a `generate_perfect`
o `generate_imperfect`. `write_maze` valida otra vez el modelo, calcula la
ruta con BFS y escribe la serialización.

Con `--interactive`, la configuración se lee igual, pero el CLI llama a
`run_interactive`. Este genera y muestra el tablero, no escribe
`OUTPUT_FILE`. La tecla `R` crea un generador con semilla `None`, por lo que
cada regeneracion usa una nueva secuencia aleatoria, aunque el tablero inicial
haya usado `SEED`.

## 3. Coordenadas, celdas y paredes

### Coordenadas

La coordenada es una tupla `(x, y)`:

- `x` aumenta hacia la derecha y tiene rango `0 <= x < width`.
- `y` aumenta hacia abajo y tiene rango `0 <= y < height`.
- La cuadrícula se guarda como `cells[y][x]`, aunque las funciones de acceso
  reciben la tupla en orden `(x, y)`.
- `(0, 0)` es la celda superior izquierda.

### Direcciones y bits

`Direction` es un `IntEnum`; cada dirección también es la mascara de bit que
se usa en el archivo:

| Direccion | Delta `(dx, dy)` | Bit | Hexadecimal si solo esa pared esta cerrada |
|---|---:|---:|---:|
| Norte | `(0, -1)` | `0001` | `1` |
| Este | `(1, 0)` | `0010` | `2` |
| Sur | `(0, 1)` | `0100` | `4` |
| Oeste | `(-1, 0)` | `1000` | `8` |

Un bit a uno quiere decir que la pared esta cerrada. La mascara de una celda
se obtiene sumando los valores de sus paredes; como cada dirección tiene un
bit distinto, la suma equivale a combinar bits. Por ejemplo, norte y este
cerrados producen `1 + 2 = 3`, que se escribe como `3`. Las cuatro paredes
cerradas producen `F`; ninguna pared cerrada produce `0`.

Cada paso compartido debe estar representado de forma simetrica. Si desde una
celda el paso al este esta abierto, la pared oeste de la celda vecina también
debe estar abierta. `open_passage` y `close_passage` actualizan ambos lados
en una sola operación.

## 4. Modelo de dominio: `mazegen/maze.py`

### `Direction`

Ademas del valor binario, cada miembro calcula:

- `opposite`: la dirección que mira de vuelta desde la celda vecina.
- `delta`: el cambio de coordenadas para avanzar en esa dirección.

Estas propiedades evitan duplicar tablas de orientacion en generación,
búsqueda, dibujo y serialización.

### `Cell`

Una celda contiene `x`, `y`, el conjunto `walls` y `blocked`.

- Una celda nueva tiene las cuatro paredes cerradas.
- `wall_mask` empaqueta las paredes en el entero hexadecimal.
- `has_wall(direction)` consulta una pared.
- `validate_assignment=True` hace que Pydantic vuelva a comprobar tipos y
  restricciones de asignacion de campos. No impide toda mutacion de los
  objetos mutables internos; el codigo debe respetar sus métodos.

### `Maze`

El modelo contiene anchura, altura, coordenadas de entrada y salida, y una
lista de filas de `Cell`. El validador `validate_grid` comprueba:

1. El número de filas y columnas coincide con las dimensiones declaradas.
2. Cada celda guarda las coordenadas correspondientes a su indice.
3. Entrada y salida estan dentro del tablero y no coinciden.
4. Los dos extremos son transitables.
5. Cada celda bloqueada conserva sus cuatro paredes cerradas.
6. Los bordes exteriores no tienen pasajes hacia fuera.
7. Las dos representaciones de cada pared interna concuerdan.
8. Todas las celdas transitables son alcanzables desde la entrada.

La conectividad se verifica con una búsqueda en anchura que ignora las celdas
bloqueadas y los pasos cerrados.

Metodos importantes:

- `create`: fabrica celdas completamente cerradas para construcción interna.
- `create_open`: abre las paredes internas y deja cerradas las fronteras.
- `cell_at`: accede a una celda y lanza `IndexError` fuera de limites.
- `neighbor_coordinates`: devuelve la coordenada vecina o `None` en un borde.
- `open_passage` / `close_passage`: cambian de manera coherente ambos lados.
- `block_cell`: bloquea una celda, cierra las paredes que la rodean y verifica
  que la operación no desconecte el resto de las celdas transitables. Si las
  desconectara, restaura las paredes anteriores y lanza `ValueError`.
- `has_coherent_walls`: comprueba fronteras y simetria.

`create` y `create_open` usan `model_construct` porque crean una estructura
interna conocida y evitan ejecutar el validador global en un estado
intermedio. Son fabricas, no una alternativa para aceptar datos externos sin
validar. Los resultados públicos de los generadores se vuelven a construir
como `Maze` validado.

### Referencia de métodos del modelo

| Simbolo | Responsabilidad |
|---|---|
| `Direction.opposite` / `Direction.delta` | Consultan la dirección opuesta y el desplazamiento de coordenadas. |
| `Cell.wall_mask` / `Cell.has_wall(direction)` | Consultan y codifican las paredes de una celda. |
| `Maze.validate_grid()` | Validador Pydantic que aplica las invariantes del modelo. |
| `Maze._is_in_bounds(coordinate)` | Comprueba los limites de una coordenada. |
| `Maze._has_closed_external_borders()` | Comprueba que ninguna pared exterior este abierta. |
| `Maze._has_closed_blocked_cells()` | Exige las cuatro paredes cerradas en celdas bloqueadas. |
| `Maze._has_symmetric_shared_walls()` | Compara los dos lados de cada pared interna. |
| `Maze._has_full_connectivity()` | BFS interno para contar celdas transitables alcanzables. |
| `Maze.create(width, height)` / `Maze.create_open(width, height)` | Fabrican cuadrícula cerrada o con pasillos internos abiertos. |
| `Maze.cell_at(coordinate)` | Devuelve celda o lanza `IndexError` si queda fuera. |
| `Maze.neighbor_coordinates(x, y, direction)` | Calcula vecina o devuelve `None` al salir del tablero. |
| `Maze.open_passage(...)` / `Maze.close_passage(...)` | Actualizan las paredes de las dos celdas adyacentes. |
| `Maze.block_cell(x, y)` | Bloquea una celda manteniendo coherencia y conectividad; restaura si la operación no es valida. |
| `Maze.has_coherent_walls()` | Comprueba fronteras y simetria entre vecinos. |

## 5. Configuracion y validación

### Formato

El archivo de configuración tiene un par `KEY=VALUE` por línea. El parser
ignora líneas vacias y líneas completas cuyo primer contenido sea `#`.
Quita espacios alrededor de claves y valores, normaliza las claves a
mayusculas y separa por el primer `=`. No reconoce comentarios al final de
una asignacion: el valor puede contener `#`.

| Clave | Obligatoria | Validacion |
|---|---|---|
| `WIDTH` | Si | Entero, como mínimo 2. |
| `HEIGHT` | Si | Entero, como mínimo 2. |
| `ENTRY` | Si | Dos enteros `x,y` dentro del tablero. |
| `EXIT` | Si | Dos enteros `x,y` dentro del tablero y distinto de `ENTRY`. |
| `OUTPUT_FILE` | Si | Se conserva como texto; el parser no comprueba que este vacio ni que la ruta sea escribible. La escritura detecta errores de ruta. |
| `PERFECT` | Si | Booleano: `true/1/yes` o `false/0/no`, sin distinguir mayusculas. |
| `SEED` | No | Entero. Si falta, se usa aleatoriedad sin semilla fija. |

Si una clave se repite, el diccionario conserva el ultimo valor. Claves
desconocidas se guardan al leer, pero no se utilizan. `MazeConfig` es un
modelo Pydantic congelado: el CLI recibe un conjunto de parametros ya
convertido y no puede reasignar sus atributos.

`ConfigError` diferencia problemas de configuración de otros errores de
ejecución. El CLI los presenta mediante `argparse`, con un mensaje de uso y
codigo de salida de error. Las validaciones posteriores del generador
protegen la API aunque se llame directamente sin usar el parser.

### Referencia de funciones de entrada y salida

| Simbolo | Responsabilidad |
|---|---|
| `ConfigError` | Excepcion de parsing y configuración. |
| `MazeConfig` | Modelo Pydantic congelado para los parametros convertidos. |
| `_parse_bool(value)` | Convierte las representaciones booleanas admitidas o lanza `ConfigError`. |
| `_parse_coords(value)` | Convierte exactamente dos enteros separados por coma a `Coordinate`. |
| `parse_config(filepath)` | Lee y valida archivo, tipos, campos obligatorios, limites y extremos; devuelve `MazeConfig`. |
| `_run_interactive_mode(config)` | Pasa parametros al visualizador e informa fallos interactivos. |
| `_run_generation_mode(config)` | Genera segun `perfect`, guarda la salida y muestra el resumen. |
| `_main()` | Define argumentos con `argparse`, carga configuración y selecciona el flujo. |
| `main()` | Frontera para presentar errores inesperados sin traceback. |
| `serialize_maze(maze)` | Devuelve el texto completo del archivo en memoria. |
| `write_maze(maze, output_file)` | Serializa y escribe UTF-8 en la ruta indicada. |
| `_format_coordinate(coordinate)` | Produce la forma `x,y`. |
| `_serialize_route(route)` | Convierte direcciones `Direction` a letras cardinales. |

## 6. Generacion perfecta: Kruskal y Union-Find

Un laberinto perfecto es un grafo conectado sin ciclos: entre cualquier par
de celdas transitables existe exactamente un camino simple. En el proyecto,
las celdas transitables son vertices y los pasos abiertos son aristas.

### Proceso implementado

1. Validar dimensiones y coordenadas.
2. Crear una cuadrícula con todos los pasos internos abiertos y las
   fronteras exteriores cerradas.
3. Aplicar el patron 42, excluyendo sus celdas bloqueadas del grafo.
4. Normalizar las restricciones de pasos obligatorios y paredes protegidas.
5. Crear un conjunto Union-Find con un componente por celda transitable.
6. Unir primero los pasos que el consumidor exige dejar abiertos. Si estos
   forman un ciclo, se rechaza la peticion, porque no se puede mantener un
   árbol perfecto con ese ciclo obligatorio.
7. Enumerar una sola vez cada paso interno (este y sur) y mezclar el orden.
8. Para cada paso restante, buscar las raices de los dos extremos. Si son
   distintas, abrirlo de forma que conecte los componentes; si son iguales,
   cerrarlo porque crearia un ciclo. Una pared protegida se cierra siempre.
9. Comprobar que todas las celdas transitables pertenecen a un solo
   componente.
10. Construir y validar el `Maze` final.

Union-Find usa un mapa `parent` y `_root` para seguir padres hasta la raiz.
La implementacion no aplica compresion de caminos ni union por rango, por lo
que no se debe atribuirle la cota optimizada clasica de Union-Find. La
barajada usa `random.Random(seed)`: con la misma versión del codigo y los
mismos parametros, una semilla reproduce el orden de decisiones.

### Restricciones de pasos

Las funciones publicas reciben `required_open_passages` y
`protected_closed_passages`, iterables de `((x, y), Direction)`.
`_normalize_passages` comprueba que:

- La dirección es un miembro de `Direction`.
- La celda inicial y su vecina estan dentro del tablero.
- El paso no toca una celda bloqueada.
- El paso no apunta hacia fuera.
- Una misma pared tenga una representación canonica: este o sur.

Si un paso aparece en los dos conjuntos, se rechaza. Si las paredes
protegidas impiden conectar todo el tablero, el generador también falla de
forma explicita.

### Referencia de métodos del generador

| Simbolo | Responsabilidad |
|---|---|
| `MazeGenerator(seed)` | Modelo congelado que almacena la semilla. |
| `_validate_request(...)` | Valida dimensiones y extremos antes de construir la cuadrícula. |
| `_new_open_maze(...)` | Delegacion a `Maze.create_open`. |
| `_root(parent, coordinate)` | Sigue enlaces `parent` hasta encontrar la raiz Union-Find. |
| `_normalize_passages(...)` | Comprueba restricciones y normaliza cada paso en orientacion este/sur. |
| `_close_perfect_maze(...)` | Procesa las aristas con Kruskal y deja un árbol conectado. |
| `generate_perfect(...)` | Orquesta validación, patron, restricciones y árbol perfecto. |
| `generate_imperfect(...)` | Orquesta conectividad, ciclos, braiding, reparación 3x3 y chequeos finales. |
| `_has_3x3_open_area(maze)` | Busca un bloque 3x3 sin bloqueos y sin paredes internas. |
| `_fix_3x3_open_areas(...)` | Cierra una arista opcional segura en cada bloque 3x3 totalmente abierto. |

## 7. Generacion imperfecta y requisitos jugables

La generación imperfecta parte igualmente de todas las conexiones internas
posibles y del mismo patron. Su finalidad es conservar conectividad, crear
rutas alternativas y evitar una zona 3x3 totalmente abierta.

### Etapas

1. Validar la peticion, aplicar el patron 42 y normalizar restricciones.
2. Enumerar cada posible conexion una vez, en dirección este o sur.
3. Inicializar Union-Find y unir las conexiones obligatorias.
4. Barajar conexiones candidatas que no esten protegidas.
5. Aplicar Kruskal aleatorizado para elegir un árbol de expansion que conecte
   todas las celdas transitables.
6. Las aristas candidatas rechazadas por Kruskal conectarian celdas ya
   conectadas; abrirlas crea ciclos. Se selecciona un mínimo objetivo de dos
   y se consideran algunas restantes con probabilidad 1/2.
7. Cerrar todos los pasos no seleccionados.
8. Recorrer conexiones opcionales cerradas: si uno de sus extremos tiene
   grado uno (tres paredes cerradas), abrir la conexion para eliminar ese
   callejon sin salida sin desconectar el tablero.
9. Detectar cuadrados 3x3 transitables totalmente abiertos y cerrar dentro
   de ellos un paso opcional cuyos extremos tengan grado suficiente.
10. Verificar el número de ciclos y el número de callejones antes de devolver
    el modelo validado.

El número ciclomático de un grafo conectado es `E - V + 1`, donde `E` es el
número de pasos abiertos y `V` el número de celdas transitables. El codigo
exige como mínimo dos ciclos independientes; un árbol tiene cero y un árbol
con una sola arista extra tiene uno. Abrir una arista de ciclo no rompe la
conectividad. Cerrar una arista en una zona 3x3 con rutas alternativas la
reduce en uno, conservando el mínimo establecido.

El grado de una celda transitable es el número de pasajes abiertos que
inciden en ella; con paredes coherentes se puede contar como `4 - len(walls)`.
Un callejon es una celda de grado uno, es decir, con tres paredes cerradas.
El codigo rechaza mas de dos callejones. En configuraciones sin restricciones,
las pruebas comprueban que la estrategia actual los elimina; no presentes
esto como una garantía universal para cualquier conjunto de paredes
protegidas. El modo imperfecto puede rechazar peticiones imposibles, como un
tablero demasiado pequeno para contener dos ciclos.

### Zona 3x3

Un cuadrado 3x3 tiene nueve celdas y doce conexiones internas posibles.
`_has_3x3_open_area` primero descarta cuadrados con bloqueos y luego revisa
ambos lados de cada pared compartida. Si encuentra los doce pasos abiertos,
`_fix_3x3_open_areas` escoge una conexion que no sea obligatoria y cuyos
extremos no se conviertan en callejones; la cierra. Si no existe ninguna
conexion segura, se produce un error explicito. No es simplemente un limite
al tamano del tablero: controla que no exista ese bloque local totalmente
abierto.

## 8. Patron 42

`Pattern42.MASK` es una mascara rectangular de 8 columnas por 7 filas; `#`
indica celdas bloqueadas. Se coloca centrada, dejando al menos un margen:
por eso el mínimo es 10x9. La mascara tiene 26 celdas marcadas.

- Si el tablero es menor, `apply` imprime un aviso a `stderr` y devuelve
  `False`; la generación continua sin el dibujo.
- Si entrada o salida cae sobre una celda marcada, se lanza `ValueError`.
- Para cada `#`, se llama a `Maze.block_cell`, que conserva la simetria de
  paredes y comprueba la conectividad.
- Si cabe, devuelve `True`.

La forma deja transitable el centro, incluso con anchuras pares o impares. El
patron forma parte de la topologia, no es una capa grafica: solver y
generador no pueden atravesar sus celdas. La salida representa estas celdas
con `F`, porque tienen sus cuatro paredes cerradas.

## 9. Solver: BFS

`solve_shortest_path` trata el laberinto como un grafo no ponderado. Inicia
una cola con la entrada, marca la entrada visitada y explora sus vecinos en
el orden de `Direction`. Un vecino se acepta solo si esta dentro, no fue
visitado, la pared esta abierta y la celda no esta bloqueada.

Al descubrir un vecino, registra `predecessors[vecino] = (actual, direccion)`
y lo anade a la cola. Cuando se extrae la salida, `_build_route` sigue los
predecesores hacia atras, acumula direcciones, y finalmente invierte la
lista. BFS explora por número creciente de pasos; por eso la primera ruta
encontrada tiene longitud mínima. No necesariamente es la única ruta mínima
si el grafo tiene ciclos.

Complejidad: `O(V + E)` tiempo y `O(V)` memoria en el grafo alcanzable. Si se
agota la cola antes de llegar a la salida, devuelve `None`.

## 10. Serializacion y formato de `maze.txt`

`serialize_maze` convierte primero el modelo a datos y lo valida creando un
nuevo `Maze`. Luego calcula BFS; si no hay ruta, lanza `ValueError`. Cada
fila se convierte a una cadena de digitos hexadecimales en orden `x`, y las
filas se escriben en orden `y`.

El formato es:

```text
<una fila de digitos hexadecimales por fila del tablero>

<entrada x,y>
<salida x,y>
<ruta minima usando N/E/S/W>
```

El serializador termina con un salto de línea. La ruta vacia sería valida si
entrada y salida coincidieran, pero ambos modelos prohiben esa condicion.
`write_maze` escribe UTF-8 y deja que errores de archivo se propaguen para que
el CLI los convierta en mensajes apropiados.

Prueba mental con una cuadrícula abierta de 2x2:

```text
93
C6

0,0
1,1
ES
```

La celda `(0,0)` tiene norte y oeste cerrados por el borde: `1 + 8 = 9`.
La celda `(1,0)` tiene norte y este cerrados: `1 + 2 = 3`. BFS devuelve `ES`
en este ejemplo por el orden de las direcciones. El archivo real
`maze.txt` contiene el ejemplo 20x10 configurado en `config.txt`.

## 11. Representacion ASCII

`render_maze` crea dos líneas por fila y una ultima línea para el borde sur:

- En las líneas horizontales usa `---` para pared norte/sur y espacios para
  pasaje.
- En las líneas interiores usa `|` para pared oeste/este.
- Cada celda muestra `E`, `X`, `###`, `*` o espacios, con prioridad para
  entrada y salida, luego bloqueo y luego solución.
- `paint` aplica codigos ANSI solo cuando `use_color=True`.
- `wall_color` selecciona un color ANSI de la paleta de 256 colores.

Antes de renderizar, `_solution_cells` recorre la secuencia suministrada
desde la entrada. Rechaza elementos que no sean `Direction`, pasos que salgan
del tablero, paredes cerradas, celdas bloqueadas y rutas que no terminen en
la salida. Devuelve el conjunto de celdas visitadas para dibujar `*`.

Si `solution=None`, solo se considera visitada la entrada. El llamador puede
usar `show_solution=False` para ocultar el trazo. Aunque no se pinte el
camino, se valida la ruta si se entrega una solución no nula.

### Referencia del renderizador

| Simbolo | Responsabilidad |
|---|---|
| `render_maze(...)` | Valida la solución, crea segmentos y devuelve el tablero como texto. |
| `paint(text, color)` | Funcion local que aplica ANSI o deja texto plano. |
| `_solution_cells(maze, solution)` | Recorre y valida la secuencia de movimientos, y devuelve sus coordenadas. |

## 12. Interaccion de terminal

`Getch` adapta la lectura de una tecla a la plataforma:

- En Windows importa `msvcrt` y usa `getch`.
- En POSIX conserva los atributos del terminal, activa temporalmente el modo
  raw con `tty` y los restaura mediante `termios` en un `finally`.

`VisualizerState` es un `dataclass(frozen=True)` que agrupa el laberinto, su
ruta, opciones de visualizacion, parametros originales y ultimo mensaje. La
inmutabilidad del contenedor facilita crear estados nuevos con
`dataclasses.replace`; no convierte en inmutable el objeto mutable `Maze`
que contiene.

| Tecla | Accion de `_handle_key` |
|---|---|
| `R` | Genera otro tablero sin semilla fija y recalcula la ruta. |
| `S` | Invierte `show_solution`. |
| `C` | Avanza circularmente por `COLOR_OPTIONS`. |
| `N` | Invierte `use_color`. |
| `Q`, Escape, Ctrl-C | Devuelve `None` para salir. |
| Otra tecla | Devuelve el mismo estado. |

`run_interactive` genera el estado inicial, limpia y dibuja la pantalla,
imprime y vacia stdout, lee una tecla y cambia de estado. El bloque `finally`
limpia la pantalla y muestra la despedida incluso al interrumpir. El modo
requiere una terminal compatible; el renderizado de color depende de que esta
interprete ANSI.

### Referencia de la interfaz

| Simbolo | Responsabilidad |
|---|---|
| `Getch.__init__()` | Selecciona la implementacion de entrada segun plataforma y conserva atributos POSIX. |
| `Getch.__call__()` | Lee un byte/tecla; en POSIX restaura el terminal en `finally`. |
| `Getch.__enter__()` / `Getch.__exit__()` | Permiten usar el lector como context manager; `__exit__` no tiene limpieza adicional. |
| `VisualizerState` | Agrupa el tablero, solución, configuración y opciones visuales. |
| `_cycle_wall_color(state)` | Avanza circularmente en la paleta. |
| `_build_initial_state(...)` | Genera el primer tablero y calcula BFS. |
| `_regenerate_maze(state)` | Genera un tablero nuevo sin semilla y recalcula la ruta. |
| `_toggle_solution(state)` / `_toggle_color_mode(state)` | Cambian una opcion y el mensaje de estado. |
| `_clear_screen()` | Escribe la secuencia ANSI para limpiar y posicionar el cursor. |
| `_render_state(state)` | Compone tablero, modo, semilla y controles. |
| `_handle_key(state, key)` | Traduce una tecla a accion o a peticion de salida. |
| `run_interactive(...)` | Ejecuta el bucle, y garantiza limpieza final de terminal. |

## 13. CLI y errores

`argparse` requiere una ruta de configuración y acepta `-i/--interactive`.
El argumento de configuración es necesario también en modo interactivo:
las dimensiones, los extremos, la estrategia y la semilla se leen del mismo
archivo.

- Configuracion invalida: `parser.error`, mensaje de uso y salida 2.
- Error de parametros del generador: mensaje y salida 2.
- Error al serializar o escribir: mensaje y salida 2.
- Error inesperado en el limite principal: mensaje sin traceback y salida 1.
- Error del modo interactivo: mensaje y retorno 1; Ctrl-C se considera una
  salida controlada.
- Tuberia cerrada o codificacion de salida no soportada: se intenta reportar
  el problema y se devuelve salida de error.

Los errores se capturan en la frontera adecuada: el parser transforma
fallos de lectura y sintaxis a `ConfigError`; el generador usa `ValueError`
para solicitudes inviables; el escritor deja subir errores de ruta; y el CLI
traduce estas excepciones a mensajes de usuario.

## 14. Pruebas

Las pruebas usan `unittest` y se ejecutan con:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

La suite se organiza por contratos:

| Archivo | Que verifica |
|---|---|
| `test_cli.py` | Argumentos, resumen de configuración, ambos modos, errores, salida y escritura. |
| `test_config_parser.py` | Sintaxis, comentarios, conversion, campos, limites e inmutabilidad. |
| `test_generator.py` | Conectividad, ciclos, perfeccion, callejones, semillas y restricciones de paredes. |
| `test_interactive.py` | Transiciones de teclas, regeneracion, representación, lectura real y restauracion del terminal. |
| `test_maze.py` | Dimensiones, celdas, extremos, fronteras, simetria, conectividad y bloqueo. |
| `test_output_writer.py` | Texto hexadecimal exacto, escritura y rechazo de modelos incoherentes. |
| `test_pattern42.py` | Posicion, centro transitable, dimensiones pequenas y extremos bloqueados. |
| `test_solver.py` | Camino mínimo, extremos y caso no alcanzable. |
| `test_visualizer.py` | Caracteres, solución, colores y validación de movimientos. |

Las pruebas de generador comparan propiedades y usan semillas fijas; no
dependen exclusivamente de que la generación aleatoria se vea igual en cada
ejecución. Las pruebas de CLI para tuberias y nombres con byte nulo dependen
de detalles del sistema operativo; conviene ejecutarlas en el entorno de
entrega. Una prueba verde no equivale por si sola a cumplir todo el subject:
también hay que revisar las condiciones funcionales y probar el artefacto con
el analizador proporcionado por la escuela, si esta disponible.

## 15. Dependencias, instalación y empaquetado

`pyproject.toml` define:

- Nombre y versión: `mazegen` 0.1.0.
- Python mínimo: 3.10.
- Dependencia de ejecución: Pydantic 2.
- Dependencias de desarrollo: flake8, mypy, pytest, build, setuptools y
  wheel.
- Backend: setuptools; búsqueda de paquetes limitada a `mazegen*`.

Por eso el wheel entrega la biblioteca `mazegen`, pero no instala la CLI ni
el visualizador. El wheel de raiz satisface la entrega de paquete ya
construido. Las carpetas `dist/`, `mazegen.egg-info/` y el tarball redundante
se quitaron de esta copia; setuptools/build puede regenerar los artefactos.

Comandos de Make:

| Objetivo | Funcion |
|---|---|
| `venv` | Crea el entorno virtual si no existe. |
| `install` | Instala el proyecto en editable y los extras de desarrollo. |
| `run` | Ejecuta el CLI con `CONFIG` (por defecto `config.txt`). |
| `debug` | Ejecuta el CLI dentro de `pdb`. |
| `clean` | Elimina caches Python, mypy, pytest y `build`; no borra el wheel. |
| `lint` | Ejecuta flake8 y mypy con los flags del subject. |
| `test` | Ejecuta unittest discovery. |
| `demo` | Ejecuta la demostracion visual de pruebas. |
| `check` | Agrupa lint y tests. |
| `package` | Construye wheel y sdist usando `build`. |

El Makefile usa la ruta de ejecutable `.venv/bin/python`, habitual en
entornos POSIX. En Windows puede ser necesario ejecutar directamente el
Python del entorno (`.venv\\Scripts\\python.exe`) o adaptar el Makefile al
shell usado. Explica este detalle si la defensa se realiza en Windows; no
afirmes que todos los comandos de Make son multiplataforma tal cual.

## 16. Archivos y responsabilidades

Consulta [GUIA_ARCHIVOS.md](GUIA_ARCHIVOS.md) para el inventario completo.
Resumen:

- `a_maze_ing.py`: CLI y coordinacion.
- `config_parser.py`: carga, conversion y validación de parametros.
- `config.txt`: valores de ejemplo para una ejecución.
- `output_writer.py`: formato hexadecimal y archivo de salida.
- `mazegen/`: modelo, generación, patron y solver reutilizables.
- `visualizer/`: dibujo ASCII y entrada interactiva.
- `tests/`: pruebas automatizadas.
- `README.md`: presentación, decisiones, paquete, equipo y recursos.
- `TUTORIAL.md`: instrucciones practicas.
- `guion.md`: exposicion oral y preguntas frecuentes.
- `GUIA_ARCHIVOS.md`: mapa de ficheros.
- `pyproject.toml`: declaracion de paquete y dependencias.
- `Makefile`: tareas de desarrollo.
- `.gitignore`: evita versionar caches, bytecode, entornos locales y
  artefactos temporales.
- `LICENSE.md`: licencia MIT, conservada intacta.
- `mazegen-0.1.0-py3-none-any.whl`: wheel preconstruido de la biblioteca.
- `maze.txt`: ejemplo del resultado, generado con la configuración incluida.

## 17. Comprobacion frente al subject (sin bonus)

Esta tabla ayuda a contestar con precision. Describe el codigo actual; no es
una certificacion automatica del evaluador.

| Requisito | Estado que puedes explicar |
|---|---|
| Python 3.10 o posterior | Declarado en `pyproject.toml`; usa anotaciones compatibles con ese mínimo. |
| `a_maze_ing.py config.txt` | Es la forma normal documentada; acepta opcionalmente `-i/--interactive`. |
| Archivo KEY=VALUE y config por defecto | `config_parser.py` y `config.txt`. |
| Semilla reproducible | `random.Random(seed)` en las dos estrategias; `R` regenerar usa `None`. |
| Paredes en bordes y simetria | Validacion de `Maze`, ademas de mutadores de pasos compartidos. |
| Conectividad | Validada por el modelo; las celdas bloqueadas del 42 se excluyen. |
| Modo perfecto sin ciclos | Arbol de expansion aleatorio; valida las paredes protegidas y los pasos requeridos. |
| Modo no perfecto con rutas alternativas | Exige al menos dos ciclos independientes y como máximo dos callejones; algunas restricciones pueden hacerlo inviable. |
| Evitar zonas completamente abiertas 3x3 | Se detectan y reparan o se lanza un error si no hay reparación segura. |
| 42 visible por celdas cerradas | Mascara 8x7 aplicada al modelo. Si no cabe, se avisa y se omite. |
| Archivo de salida hexadecimal, extremos y ruta | `output_writer.py`; las paredes codifican N=1, E=2, S=4, W=8. |
| Visualizacion y controles | ASCII, entrada/salida, solución y controles R/S/C/N/Q/Esc/Ctrl-C. |
| Biblioteca reutilizable y wheel en raiz | Paquete `mazegen`, API exportada y wheel `mazegen-0.1.0-py3-none-any.whl`. |
| Documentacion de uso y licencia | README, tutorial, manual y LICENSE.md. |
| Bonus | No es necesario defenderlo como obligatorio. La animacion no esta implementada; tampoco se debe prometer cero callejones para toda configuración restringida. |

La omision del patron 42 se reporta con un mensaje `Warning` a `stderr`, no
como una excepcion fatal. Al explicarlo, di que se avisa y se continua sin el
patron cuando la dimension no permite colocarlo.

## 18. Preguntas técnicas frecuentes

**Por que usar un grafo?** Cada celda transitable es un vertice y cada paso
abierto es una arista. Con esta abstraccion se pueden formular conectividad,
ciclos y rutas de manera precisa.

**Por que Kruskal para el modo perfecto?** Permite empezar con todas las
conexiones posibles y elegir un árbol conectando componentes distintas.
Cerrar las aristas que conectarian una componente consigo misma impide ciclos.

**Que hace Union-Find?** Mantiene componentes conexas: `_root` obtiene la raiz
de una celda; al unir dos raices se combinan sus componentes. El codigo lo
usa para decidir si abrir una arista mantiene el árbol o formaria un ciclo.

**Por que BFS y no DFS?** Ambas pueden encontrar un camino, pero BFS explora
por distancia y garantiza el mínimo número de pasos en un grafo no ponderado.

**Por que comprobar conectividad en `Maze` si el generador ya conecta?** El
modelo también se puede construir desde otras llamadas o bibliotecas. El
validador protege el contrato en la frontera del dominio.

**Que evita paredes incoherentes?** Los métodos `open_passage` y
`close_passage` actualizan la pared de ambas celdas. El validador comprueba
que no haya una discrepancia.

**Que pasa si la entrada se superpone con el 42?** El generador lanza
`ValueError`; el CLI informa que no pudo generar y termina con error.

**Como se garantiza que la ruta serializada sea valida?** El escritor vuelve
a validar el modelo y obtiene la ruta con BFS antes de serializarla.

**Se guarda la ruta en el modelo?** No. Se calcula al serializar o construir
el estado visual y se representa como una lista de `Direction`.

**Que significa una celda con `F`?** Los cuatro bits de pared estan cerrados.
En el patron 42, `F` identifica una celda bloqueada; una pared cerrada no
significa por si sola que la celda este bloqueada.

**Por que hay una ruta distinta al repetir ejecución?** Si no hay `SEED`, el
generador recibe `None` y usa aleatoriedad del sistema. Con semilla fija se
reproduce para los mismos parametros y la misma versión del algoritmo.

**El wheel contiene el programa entero?** No. El descubrimiento de paquetes
incluye solo `mazegen*`; la CLI y el visualizador requieren el repositorio.

**Que mejorariasí** Se puede proponer mejorar la estructura Union-Find con
compresion de caminos y union por rango, robustecer la compatibilidad del
Makefile con Windows y ampliar pruebas de conformidad automatizada contra
el analizador del subject. Presentalo como mejoras futuras, no como
funcionalidades existentes.

## 19. Como preparar una defensa demostrable

1. Explica el modelo: dibuja dos celdas y muestra las dos representaciones
   de una pared compartida.
2. Ejecuta `python a_maze_ing.py config.txt` y ensena el archivo resultante.
3. Cambia temporalmente `SEED` en una copia de configuración para demostrar
   reproducibilidad, sin sobrescribir el ejemplo que quieras conservar.
4. Ejecuta `python a_maze_ing.py config.txt --interactive`; prueba `S`, `C`,
   `N`, `R` y salida.
5. Describe el árbol de expansion con Union-Find y luego el BFS que encuentra
   la ruta mínima.
6. Ejecuta las pruebas y lint en el entorno de evaluación.
7. Prepara una modificacion pequena: cambiar un color, agregar una validación
   de configuración o adaptar un test. Explica el efecto antes y despues.
8. Si dispones del analizador oficial, valida con el mismo `config.txt` que
   produjo el archivo. No sustituyas esa comprobación por una captura visual.

## 20. Guion oral ampliado

> A-Maze-ing es un generador de laberintos con dos topologias: una perfecta,
> que es un árbol y por tanto no tiene ciclos, y otra con ciclos, que mantiene
> rutas alternativas. El programa lee un archivo de configuración, modela
> cada celda con cuatro paredes, aplica una mascara 42, genera el tablero y
> encuentra una ruta mínima mediante BFS.
>
> He separado el proyecto en capas. El parser valida la entrada y devuelve
> una configuración inmutable; `mazegen` contiene el modelo y los algoritmos;
> el escritor crea el archivo hexadecimal; y el visualizador se ocupa de la
> salida ASCII e interacción. Asi puedo reutilizar y probar la biblioteca
> sin depender de la interfaz.
>
> En el modo perfecto parto de los pasos posibles, los mezclo con una semilla
> y uso Union-Find para abrir solo conexiones entre componentes diferentes.
> En el modo imperfecto primero construyo conectividad y luego dejo pasos
> adicionales abiertos para crear al menos dos ciclos. Tambien reduzco
> callejones y reparo cuadrados 3x3 totalmente abiertos; si unas restricciones
> impiden cumplir las condiciones, informo el error en vez de devolver un
> resultado invalido.
>
> BFS recorre los pasos abiertos con una cola, registra predecesores y
> reconstruye la ruta al alcanzar la salida. Como cada paso cuesta lo mismo,
> esa ruta tiene el menor número de movimientos. El escritor guarda cada
> celda como un digito hexadecimal: norte vale 1, este 2, sur 4 y oeste 8;
> despues escribe entrada, salida y la ruta con letras.
>
> Las pruebas comprueban contratos, no solo una imagen concreta: conectividad,
> paredes simetricas, ciclos, restricciones, serialización y controles de
> terminal. La biblioteca se empaqueta como `mazegen`; el README, el tutorial
> y la licencia explican su reutilización. Para la demostracion puedo ejecutar
> el modo normal y el interactivo. Gracias.
