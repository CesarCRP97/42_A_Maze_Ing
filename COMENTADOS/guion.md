# Guion de defensa de A-Maze-ing

Para el detalle de cada clase, funcion, prueba y requisito del subject,
consulta [DOCUMENTACION_COMPLETA.md](DOCUMENTACION_COMPLETA.md).

## Presentación

Buenos días. Voy a presentar **A-Maze-ing**, un proyecto en Python que genera
laberintos, calcula una ruta mínima entre una entrada y una salida, permite
guardar el resultado en un formato compacto y ofrece una visualización ASCII
interactiva en la terminal.

La decisión de diseño más importante es separar responsabilidades. El
ejecutable coordina el flujo; el parser valida los datos de entrada; el
paquete `mazegen` contiene el modelo, la generación y la búsqueda; el escritor
define el formato de salida; y el visualizador se ocupa exclusivamente de la
presentación. Esto facilita probar cada parte de manera aislada y reutilizar
la biblioteca sin tener que ejecutar toda la aplicación.

## Flujo de ejecución

El usuario inicia el programa con un archivo `KEY=VALUE`. El parser convierte
ese archivo en una configuración inmutable, comprueba los campos obligatorios,
las dimensiones, las coordenadas y que entrada y salida sean distintas. Si
hay datos incorrectos, el programa informa del problema antes de generar
nada.

Con una configuración válida, el CLI ofrece dos recorridos. El modo normal
elige la estrategia y guarda el laberinto. El modo interactivo genera y
presenta el laberinto en pantalla; permite regenerar, mostrar u ocultar la
solución y cambiar los colores. Mantenerlos separados evita que la
visualización modifique accidentalmente el archivo de salida.

## Modelo del laberinto

El dominio se representa mediante una cuadrícula de celdas. Cada celda tiene
coordenadas, cuatro paredes y un indicador para las celdas bloqueadas. Las
direcciones son valores enumerados y también corresponden a bits, por lo que
se puede convertir cada combinación de paredes en un dígito hexadecimal.

El modelo `Maze` valida las invariantes que necesita el resto del sistema:
forma rectangular, coordenadas consistentes, extremos dentro del tablero y
transitables, bordes exteriores cerrados, paredes compartidas simétricas y
conectividad de todas las celdas transitables. Además, abrir o cerrar un paso
actualiza ambos lados de la pared. La ventaja es que estas reglas viven en un
solo lugar, en vez de repetirse en cada algoritmo.

## Generación perfecta

Una generación perfecta conecta las celdas transitables sin ciclos. El
algoritmo parte de los pasos internos abiertos y los mezcla aleatoriamente.
Con una estructura Union-Find comprueba si dos celdas pertenecen ya al mismo
componente: si es así, cerrar ese paso evita un ciclo; si no, unir los
componentes conserva la conectividad. El resultado es un árbol de expansión,
por lo que existe un único camino simple entre cualquier par de celdas
transitables.

La semilla se entrega al generador aleatorio local. Con la misma semilla y
los mismos parámetros se obtiene una generación reproducible, algo útil para
depurar y para explicar resultados durante una demostración.

## Generación imperfecta

La modalidad imperfecta mantiene la conectividad, pero deja abiertos pasos
adicionales para crear ciclos y rutas alternativas. Después trata los
callejones sin salida y evita áreas 3 por 3 completamente abiertas. Al final
verifica condiciones del resultado —entre ellas, ciclos suficientes y un
límite de callejones—; si las restricciones solicitadas hacen imposible
cumplirlas, devuelve un error explícito en lugar de producir un laberinto que
incumpla el contrato.

Esta estrategia es distinta de limitarse a abrir paredes al azar: se
conservan las restricciones de pasos y se comprueba la conectividad antes de
aceptar la estructura.

## Patrón 42 y búsqueda de ruta

El patrón 42 se aplica como una máscara de celdas bloqueadas centrada en el
tablero. Se omite con un aviso cuando no cabe, y se rechaza si coincide con
la entrada o la salida. Es parte de la topología real: el solver y el
renderizador la reconocen como no transitable.

Para resolver el laberinto, BFS explora por niveles con una cola. Como todos
los pasos tienen el mismo coste, la primera vez que alcanza la salida ya ha
encontrado un camino de longitud mínima. Los predecesores registrados durante
la búsqueda permiten reconstruir la secuencia de direcciones. Si no hay
conexión, el resultado es `None`.

## Escritura y visualización

El escritor valida el modelo, calcula la ruta mínima y serializa cada celda
como un dígito hexadecimal con los bits de las paredes. A continuación escribe
una línea vacía, las coordenadas de entrada y salida, y la ruta expresada con
letras cardinales. Esta representación es compacta y permite comprobar tanto
la estructura como la solución.

El visualizador ASCII muestra paredes, entrada, salida, celdas bloqueadas y,
si está activada, la ruta. Los colores ANSI son opcionales. La vista
interactiva conserva un estado explícito y maneja cada tecla como una
transición; además, restaura la configuración de terminal en el flujo de
salida, incluso si se interrumpe.

## Calidad y pruebas

Las pruebas se organizan por responsabilidad: parser, modelo, generación,
patrón, solver, escritura, CLI y visualizador. En vez de depender solamente
de una imagen aleatoria esperada, muchas pruebas comprueban propiedades:
conectividad, simetría de paredes, número de pasos y ciclos, validez de la
ruta, formato serializado y comportamiento de errores. `Makefile` reúne las
tareas habituales de instalación, lint, pruebas y empaquetado.

Para demostrarlo se puede ejecutar `make run` para generar un archivo y
`python a_maze_ing.py config.txt --interactive` desde una terminal real para
probar los controles. `SEED` permite repetir la generación.

## Decisiones y límites

La solución prioriza módulos pequeños, modelos validados y errores visibles.
Pydantic se usa para la validación de datos, mientras que los algoritmos
siguen siendo Python estándar. La distribución `mazegen` empaqueta la
biblioteca reutilizable; el CLI y el visualizador son capas de la aplicación.
La salida interactiva no escribe el archivo configurado: son modos separados.
La entrada interactiva requiere una terminal y el modo de colores depende de
que esta interprete secuencias ANSI.

## Cierre

En resumen, el proyecto cubre el ciclo completo: configura, modela, genera,
resuelve, serializa y representa un laberinto. Su valor no está solo en
producir un dibujo, sino en mantener invariantes verificables y exponer cada
función mediante módulos y pruebas independientes. Gracias.

## Preguntas que pueden hacer

**¿Por qué BFS?** Porque el laberinto es un grafo sin pesos; BFS garantiza la
ruta con menor número de pasos.

**¿Qué diferencia hay entre perfecto e imperfecto?** El perfecto es un árbol
sin ciclos y tiene una única ruta simple entre dos celdas transitables. El
imperfecto conserva ciclos y, por tanto, caminos alternativos.

**¿Cómo se comprueba la reproducibilidad?** Se pasa una semilla al objeto
`Random` usado por el generador y se comprueban resultados y propiedades con
semillas fijas en las pruebas.

**¿Por qué validar en el modelo y en el parser?** El parser valida la entrada
del usuario; el modelo protege las invariantes internas aunque se construya
un laberinto desde otra parte del código.

**¿Qué representa un dígito hexadecimal?** Cada bit indica si una de las
cuatro paredes de la celda permanece cerrada. La orientación concreta de los
bits está definida por `Direction`.
