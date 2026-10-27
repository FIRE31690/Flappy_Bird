# Flappy Bird Terminal + Gestor

Aplicación interactiva de consola desarrollada en Python que une dos partes en un solo sistema: un **minijuego Flappy Bird que se juega dentro de la terminal** y un **gestor de jugadores y partidas**. Cada partida jugada se registra automáticamente y otorga medallas, monedas y niveles. Con las monedas se compran skins que cambian el aspecto del pájaro en el juego. El sistema genera reportes y ranking, conserva los datos entre ejecuciones en JSON con protección ante archivos dañados, exporta a CSV y TXT y lleva una bitácora de eventos en un archivo de texto.

Proyecto integrador **EA01 · SENA ADSO · Ficha 3388087 · Team 1**.

---

## Tabla de Contenidos

1. [Equipo](#equipo)
2. [Requisitos](#requisitos)
3. [Instalación y ejecución](#instalación-y-ejecución)
4. [Estructura del proyecto](#estructura-del-proyecto)
5. [Arquitectura](#arquitectura)
6. [Cómo funciona el sistema: menús y opciones](#cómo-funciona-el-sistema-menús-y-opciones)
7. [El juego](#el-juego)
8. [Reglas de negocio y recompensas](#reglas-de-negocio-y-recompensas)
9. [Validaciones y manejo de errores](#validaciones-y-manejo-de-errores)
10. [Persistencia en JSON](#persistencia-en-json)
11. [Reportes y consultas](#reportes-y-consultas)
12. [Exportación a CSV y TXT](#exportación-a-csv-y-txt)
13. [Bitácora de eventos](#bitácora-de-eventos)
14. [Pruebas](#pruebas)
15. [Temas de los laboratorios en el código](#temas-de-los-laboratorios-en-el-código)
16. [Solución de problemas](#solución-de-problemas)

---

## Equipo

| Integrante |
| :--- |
| Cuellar Ospino Yohan Fernando |
| Zarate Rozo Juan Camilo |
| Posso Tuberquia Jader Alonso |
| Reyes Correa Diana Faizury |

---

## Requisitos

- **Python 3.9 o superior** (probado con Python 3.13).
- Solo usa la **biblioteca estándar**: `json`, `csv`, `pathlib`, `os`, `shutil`, `re`, `datetime`, `random`, `time`, `dataclasses`, `collections`, `types`, `unicodedata`, `curses` y `unittest`.
- **Windows:** `curses` no viene incluido en Python para Windows. Se instala una sola vez con el paquete `windows-curses` (ver la sección siguiente). En Linux y macOS no hay que instalar nada.
- Terminal de al menos **48 columnas × 24 filas** para jugar.

---

## Instalación y ejecución

Desde la carpeta raíz del proyecto (`flappy_gestor/`):

```bash
# Comandos para ejecutar Flappy Bird + Gestor en Windows y Linux

**Windows:** Abrir CMD o PowerShell, ingresar a la carpeta principal del proyecto y ejecutar los siguientes comandos:

```bash
# Instalar las dependencias (una sola vez)
pip install -r requirements.txt

# Ejecutar la aplicación completa (juego + gestor)
python main.py

# Ejecutar solo el gestor, sin el juego
python -c "from gestor.interfaz import ejecutar; ejecutar()"
```

**Linux:** Abrir la terminal, ingresar a la carpeta principal del proyecto y ejecutar los siguientes comandos:

```bash
# Instalar las dependencias (una sola vez)
python3 -m pip install -r requirements.txt

# Ejecutar la aplicación completa (juego + gestor)
python3 main.py

# Ejecutar solo el gestor, sin el juego
python3 -c "from gestor.interfaz import ejecutar; ejecutar()"
```

**Nota:** Los comandos deben ejecutarse desde la carpeta raíz `flappy_gestor`, donde se encuentra el archivo `main.py` y el archivo `requirements.txt`.
```

Al iniciar, el sistema carga los datos de `data/flappy.json`:

- Si el archivo **no existe** (primera ejecución), arranca con datos vacíos y lo crea al guardar.
- Si el archivo es **válido**, carga todos los jugadores y partidas.
- Si el archivo está **dañado**, hace una copia de respaldo `flappy.json.corrupto`, muestra un aviso y **pregunta** si se quiere empezar con datos vacíos. Si la respuesta es «no», el programa termina **sin tocar ningún archivo**.

**Variables de entorno opcionales**

| Variable | Efecto |
| :--- | :--- |
| `FLAPPY_DATOS=/otra/carpeta` | Cambia la carpeta donde se guardan `data/` y `exports/` |
| `FLAPPY_ASCII=1` | Fuerza el juego a usar solo caracteres simples (`+ - \| # =`) |
| `FLAPPY_UNICODE=1` | Fuerza el juego a usar bloques Unicode (`█ ▓ ● ✖`) |

En PowerShell se definen así: `$env:FLAPPY_ASCII=1`. En CMD: `set FLAPPY_ASCII=1`.

---

## Estructura del proyecto

```text
flappy_gestor/
├── main.py                    # Punto de entrada: llama a aplicacion.ejecutar()
├── aplicacion.py              # Menú principal: une el juego y el gestor
├── requirements.txt           # windows-curses (solo para Windows)
├── README.md                  # Este documento
├── gestor/                    # Lógica de negocio y datos
│   ├── config.py              # Rutas con pathlib (data/, exports/) y FLAPPY_DATOS
│   ├── excepciones.py         # GestorError y sus subclases
│   ├── validadores.py         # Validación de nombre, enteros, puntaje, dificultad y skin
│   ├── reglas.py              # Medallas, niveles, categorías y precios de skins
│   ├── dificultad.py          # Dificultad (base) y Facil / Normal / Dificil
│   ├── modelos.py             # Clase Jugador (propiedades) y dataclass Partida
│   ├── repositorio.py         # Colecciones de jugadores y partidas, búsquedas, filtros e integridad
│   ├── servicio.py            # Casos de uso: registrar, renombrar, bloquear, partidas, tienda
│   ├── almacenamiento.py      # Guardar y cargar JSON (escritura atómica y respaldo .corrupto)
│   ├── exportador.py          # Exportador (base), ExportadorCSV y ExportadorTXT
│   ├── reportes.py            # Ranking, resúmenes, medallas y jugadores sin partidas
│   ├── bitacora.py            # Bitácora de eventos en archivo de texto
│   └── interfaz.py            # Menú del gestor (input/print) y carga segura de datos
├── juego/                     # El juego, con el patrón Modelo-Vista-Controlador
│   ├── modelo.py              # Pajaro, Obstaculo, Tuberia, TuberiaMovil y Juego (física y colisiones)
│   ├── vista.py               # Gráficos: escena pura, colores, temas Unicode/ASCII y pantallas
│   └── controlador.py         # Lectura de teclas y bucle principal con curses
├── tests/                     # 87 pruebas automáticas (unittest)
│   ├── test_gestor.py
│   ├── test_exportador_dificultad.py
│   ├── test_juego.py
│   └── test_aplicacion.py
├── data/                      # flappy.json y bitacora.txt (se crean solos)
├── exports/                   # partidas y ranking en .csv y .txt
└── legado/
    └── Flappy_bird_pygame.py  # Prototipo original con pygame (solo como referencia)
```

---

## Arquitectura

El proyecto está organizado **por capas**. Cada capa tiene una sola responsabilidad y solo conoce a las capas de abajo:

```text
main.py
   └── aplicacion.py                 ← menú principal (interacción con el usuario)
         ├── juego/  (modelo · vista · controlador)
         └── gestor/interfaz.py      ← menú del gestor (interacción con el usuario)
                └── servicio.py      ← reglas de negocio y casos de uso
                      ├── repositorio.py   ← gestión de colecciones
                      ├── modelos.py       ← entidades del dominio
                      ├── reglas.py · dificultad.py · validadores.py
                      └── bitacora.py
               almacenamiento.py · exportador.py · reportes.py
```

| Responsabilidad | Dónde está |
| :--- | :--- |
| Interacción con el usuario | `aplicacion.py`, `gestor/interfaz.py`, `juego/controlador.py` |
| Modelos y entidades del dominio | `gestor/modelos.py`, `juego/modelo.py` |
| Reglas de negocio | `gestor/servicio.py`, `gestor/reglas.py`, `gestor/dificultad.py` |
| Gestión de colecciones | `gestor/repositorio.py` |
| Validación de datos | `gestor/validadores.py` |
| Persistencia en archivos | `gestor/almacenamiento.py`, `gestor/bitacora.py` |
| Generación de reportes y exportación | `gestor/reportes.py`, `gestor/exportador.py` |

Reglas de diseño que se respetan:

- Las clases del dominio (`Jugador`, `Servicio`, `Juego`…) **nunca usan `input()` ni `print()`**. Solo los menús hablan con el usuario.
- El juego usa `gestor.dificultad`, `gestor.reglas` y `gestor.excepciones`, pero el gestor **no conoce** al juego.
- El modelo del juego (`juego/modelo.py`) no usa `curses`: se puede probar sin abrir una pantalla.

---

## Cómo funciona el sistema: menús y opciones

### Menú principal

```text
╔══════════════════════════════╗
║   FLAPPY BIRD  ·  TERMINAL   ║
╚══════════════════════════════╝
 1. Jugar
 2. Gestor de jugadores y partidas
 3. Ver bitácora (últimos eventos)
 0. Guardar y salir
```

1. **Jugar**
   - Pide el **ID o el nombre** del jugador. Si el nombre no existe, crea al jugador en ese momento.
   - Un jugador **bloqueado** no puede jugar.
   - Pide la **dificultad** (`facil`, `normal` o `dificil`; Enter = `normal`) y muestra la skin equipada.
   - Abre el juego en la terminal. Al terminar, **registra la partida** y muestra el puntaje, la medalla, las monedas ganadas, el saldo, el nivel y si hubo **nuevo récord personal**.
   - Si el jugador sale con `Q` o `Esc`, la partida se considera abandonada y **no se registra**.
2. **Gestor de jugadores y partidas:** abre el submenú del gestor (ver abajo).
3. **Ver bitácora:** muestra los últimos 10 eventos registrados.
0. **Guardar y salir:** guarda en `data/flappy.json` y cierra. También se guarda después de cada opción y el programa sale de forma limpia con `Ctrl + C`.

### Menú del gestor (13 opciones)

| Opción | Qué hace |
| :---: | :--- |
| 1. Registrar jugador | Pide el nombre, lo valida y le asigna un ID consecutivo |
| 2. Listar jugadores | Muestra ID, nombre, estado, mejor puntaje, monedas, nivel, skin y categoría de cada jugador |
| 3. Buscar jugador por nombre | Busca jugadores cuyo nombre contenga el texto escrito (sin importar mayúsculas) |
| 4. Renombrar jugador | Cambia el nombre de un jugador, con las mismas validaciones del registro |
| 5. Bloquear / activar jugador | Alterna el estado del jugador; un jugador bloqueado no puede registrar partidas |
| 6. Registrar partida (manual) | Registra un puntaje sin jugar (útil para cargar resultados o probar reglas) |
| 7. Consultar partidas (filtros) | Filtra por jugador, dificultad y puntaje mínimo (Enter = sin filtro); los filtros se combinan |
| 8. Comprar skin | Muestra las skins con su precio y descuenta las monedas del jugador |
| 9. Equipar skin | Activa una skin que el jugador ya compró |
| 10. Reportes | Resumen general, top 5, resumen por dificultad, conteo de medallas y jugadores sin partidas |
| 11. Exportar a CSV y TXT | Genera `partidas` y `ranking` en los dos formatos dentro de `exports/` |
| 12. Verificar integridad de datos | Revisa que los datos guardados sean coherentes entre sí |
| 13. Ver bitácora | Muestra los últimos 10 eventos |
| 0. Volver | Regresa al menú principal |

Cualquier opción que no exista muestra **«Opción inválida.»** y vuelve a mostrar el menú.

---

## El juego

Flappy Bird dibujado con caracteres dentro de la terminal, usando `curses`.

| Tecla | Acción |
| :--- | :--- |
| `ESPACIO`, `W` o flecha `↑` | Saltar (también comienza la partida) |
| `P` | Pausa / continuar |
| `Q` o `Esc` | Abandonar (la partida no se registra) |

**Cómo se juega:** el pájaro cae por gravedad y sube al saltar. Cada tubería superada suma **1 punto**. La partida termina al chocar con una tubería, el techo o el suelo.

**Lo que se ve en pantalla**

- Cielo con nubes y colinas que se mueven a distinta velocidad (efecto de profundidad).
- Tuberías verdes con tapa junto al hueco y suelo de hierba y tierra que avanza.
- Pájaro con ala que aletea; su símbolo y color dependen de la skin equipada.
- Encabezado con jugador, dificultad, puntaje y **MEJOR** (el récord sube en vivo).
- Cartel de inicio, cartel de pausa, destello al chocar y pantalla final con el puntaje en número grande, la medalla, las monedas ganadas y «¡NUEVO RÉCORD!» cuando aplica.

| Skin | Unicode | ASCII | Color |
| :--- | :---: | :---: | :--- |
| clasico | `●` | `O` | amarillo |
| rojo | `●` | `R` | rojo |
| dorado | `◆` | `$` | amarillo |
| fantasma | `○` | `~` | blanco |

Al chocar, el pájaro se convierte en `✖` (`X` en modo ASCII).

**Compatibilidad:** los colores se activan solos si la terminal tiene al menos 8. Los bloques Unicode se usan si la terminal trabaja en UTF-8; si no, el juego cambia al tema ASCII.

---

## Reglas de negocio y recompensas

Definidas en `gestor/reglas.py` y `gestor/dificultad.py`.

### Dificultades

| Dificultad | Hueco entre tuberías | Velocidad (segundos por paso) | Separación entre tuberías | Multiplicador de monedas | Tuberías móviles |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `facil` | 8 filas | 0,12 | 18 columnas | ×1 | No |
| `normal` | 6 filas | 0,09 | 16 columnas | ×2 | No |
| `dificil` | 5 filas | 0,07 | 15 columnas | ×3 | Sí (el hueco sube y baja) |

### Medallas por partida

| Puntaje | Medalla |
| :--- | :--- |
| 100 o más | platino |
| 40 a 99 | oro |
| 20 a 39 | plata |
| 10 a 19 | bronce |
| menos de 10 | ninguna |

### Monedas, niveles y categorías

- **Monedas ganadas** = `(puntaje // 5) × multiplicador de la dificultad`. Ejemplo: 50 puntos en normal → `(50 // 5) × 2 = 20` monedas.
- **Nivel**, según las monedas acumuladas en toda la historia (comprar skins no baja el nivel):

  | Monedas acumuladas | 0 | 30 | 100 | 250 | 500 |
  | :--- | :---: | :---: | :---: | :---: | :---: |
  | Nivel | 1 | 2 | 3 | 4 | 5 |

- **Categoría** del jugador: `sin jugar` (0 partidas), `experto` (nivel ≥ 4 y mejor puntaje ≥ 40), `regular` (nivel ≥ 2 o mejor puntaje ≥ 10) o `novato`.
- **Récord:** el mejor puntaje del jugador se actualiza solo si la nueva partida lo supera.

### Tienda de skins

| Skin | Precio |
| :--- | :---: |
| clasico | 0 (todos la tienen) |
| rojo | 50 monedas |
| dorado | 150 monedas |
| fantasma | 300 monedas |

Reglas de la tienda: no se puede comprar sin saldo suficiente (el saldo nunca queda negativo), no se puede comprar dos veces la misma skin y no se puede equipar una skin que no se ha comprado.

---

## Validaciones y manejo de errores

### Validaciones de entrada (`gestor/validadores.py`)

| Dato | Regla |
| :--- | :--- |
| Nombre | De 3 a 15 caracteres; letras (con tildes y ñ), números, espacio o `_`; no puede repetirse (sin importar mayúsculas) |
| ID y números | Deben ser enteros |
| Puntaje | Entero entre 0 y 9999 |
| Dificultad | `facil`, `normal` o `dificil` |
| Skin | Debe existir en la tienda |

### Errores propios (`gestor/excepciones.py`)

Todos heredan de `GestorError`, así los menús los atrapan con un solo `except` y muestran un mensaje claro **sin cerrar el programa**:

| Excepción | Cuándo ocurre |
| :--- | :--- |
| `ValidacionError` | Un dato escrito por el usuario no cumple las reglas |
| `ReglaNegocioError` | La operación no está permitida (nombre repetido, jugador bloqueado, saldo insuficiente…) |
| `NoEncontradoError` | El ID del jugador no existe |
| `PersistenciaError` | No se pudo leer, guardar o exportar un archivo, o el JSON está dañado |
| `EntornoNoSoportadoError` | Falta `curses` (Windows sin `windows-curses`) o la terminal es muy pequeña |

Cuando una operación es rechazada, **el estado no cambia**: por ejemplo, una compra sin saldo no descuenta monedas ni agrega la skin.

---

## Persistencia en JSON

Los datos se guardan en `data/flappy.json` con esta estructura:

```json
{
  "jugadores": [
    { "id": 1, "nombre": "Ana", "activo": true, "mejor_puntaje": 50, "partidas_jugadas": 1,
      "monedas": 20, "monedas_totales": 20, "nivel": 1, "skins": ["clasico"], "skin_activa": "clasico" }
  ],
  "partidas": [
    { "id": 1, "jugador_id": 1, "puntaje": 50, "dificultad": "normal",
      "medalla": "oro", "monedas": 20, "fecha": "2026-10-25 10:30:00" }
  ]
}
```

El campo `nivel` es solo informativo: al cargar se recalcula a partir de `monedas_totales`.

Protecciones en `gestor/almacenamiento.py` y `gestor/interfaz.py`:

- **Guardado automático** después de cada opción del menú y al salir.
- **Escritura atómica:** primero se escribe un archivo `.tmp` y luego se reemplaza el original con `os.replace`. Si el programa se interrumpe, el archivo bueno nunca queda a medias. Un bloque `finally` borra el `.tmp` aunque haya un error.
- **Archivo inexistente:** se trata como primera ejecución y se arranca con datos vacíos.
- **Archivo dañado** (JSON mal formado, raíz que no es un objeto, campos inválidos o saldo negativo): se copia a `flappy.json.corrupto`, se avisa y se **pregunta antes de reemplazarlo**. Si la respuesta es «no», no se modifica ningún archivo.
- **Carga todo o nada:** el repositorio solo se llena si toda la lectura salió bien (bloque `else` del `try`).
- Los CSV **no** son el mecanismo de persistencia: solo sirven para exportar.

---

## Reportes y consultas

Opción **10. Reportes** del menú del gestor (`gestor/reportes.py`):

| Reporte | Contenido |
| :--- | :--- |
| Resumen general | Total de jugadores, jugadores activos, total de partidas, promedio de puntaje y monedas en circulación |
| Top 5 ranking | Jugadores ordenados por mejor puntaje (empates por nombre) con su categoría |
| Por dificultad | Para cada dificultad: número de partidas, promedio y puntaje máximo |
| Medallas | Cuántas partidas obtuvieron cada medalla |
| Jugadores sin partidas | Jugadores registrados que todavía no han jugado (diferencia de conjuntos) |

Consultas disponibles:

- **Búsqueda de jugadores** por parte del nombre (opción 3).
- **Filtro de partidas** por jugador, dificultad y puntaje mínimo, combinables (opción 7).
- **Verificación de integridad** (opción 12): detecta partidas que apuntan a jugadores inexistentes y jugadores cuyo contador de partidas o mejor puntaje no coincide con su historial.

---

## Exportación a CSV y TXT

### ¿Cómo se usa?

En el menú del gestor elige **11. Exportar a CSV y TXT**. Se generan cuatro archivos en la carpeta `exports/`:

| Archivo | Contenido |
| :--- | :--- |
| `partidas.csv` | Todas las partidas registradas |
| `ranking.csv` | Todos los jugadores ordenados por mejor puntaje |
| `partidas.txt` | Las partidas en una tabla de texto alineada |
| `ranking.txt` | El ranking en una tabla de texto alineada |

### Estructura de los archivos CSV

- **`partidas.csv`** · columnas: `id,jugador_id,jugador,puntaje,dificultad,medalla,monedas,fecha`
- **`ranking.csv`** · columnas: `posicion,nombre,mejor_puntaje,nivel,partidas`

Los CSV se guardan en **UTF-8 con BOM**, para que Excel en Windows muestre bien las tildes y la ñ. El delimitador es la coma (la clase `ExportadorCSV` también acepta `;`).

Los dos formatos comparten el mismo proceso gracias a la herencia: `Exportador` prepara la carpeta y abre el archivo, y `ExportadorCSV` y `ExportadorTXT` solo definen cómo se escribe cada formato (polimorfismo).

---

## Bitácora de eventos

Cada acción importante se anota en `data/bitacora.txt` con fecha y hora:

```text
2026-10-25 10:30:00 | Jugador registrado: Ana (id 1)
2026-10-25 10:31:12 | Partida #1: Ana hizo 50 en normal -> medalla oro, +20 monedas
2026-10-25 10:32:40 | Ana compró la skin 'rojo' por 50 monedas
```

Se registran: jugadores registrados, renombrados, bloqueados o activados, partidas y compras de skins. Si la bitácora no se puede escribir, el programa **sigue funcionando** normalmente. Se consulta con la opción 3 del menú principal o la 13 del gestor.

---

## Pruebas

El proyecto tiene **87 pruebas automáticas** con `unittest`. Las pruebas de archivos trabajan en **carpetas temporales** (`tempfile`), así nunca tocan el `data/flappy.json` real.

| Archivo | Pruebas | Qué valida |
| :--- | :---: | :--- |
| `test_gestor.py` | 37 | Validaciones, medallas, monedas, niveles y categorías; encapsulamiento de `Jugador`; reglas del servicio (nombre repetido, jugador bloqueado, tienda); búsquedas, filtros e integridad con conjuntos; bitácora; guardado y recuperación JSON; archivo inexistente, dañado o con datos inválidos; carga segura que no sobrescribe sin confirmación |
| `test_exportador_dificultad.py` | 12 | Herencia, sobrescritura con `super()` y polimorfismo de las dificultades; CSV con encabezado, BOM y delimitador; TXT; errores de escritura |
| `test_juego.py` | 31 | Gravedad y salto, colisiones, tuberías móviles, fin de partida; **un bot que juega** y supera 10 puntos en las tres dificultades; gráficos (temas, colores, animaciones, carteles, pantalla final); teclas y errores de entorno |
| `test_aplicacion.py` | 7 | Flujo completo de «Jugar» con el juego reemplazado por un doble de prueba (`unittest.mock`) |

Para ejecutar todas las pruebas:

```bash
python -m unittest discover -s tests -v
```

---

## Temas de los laboratorios en el código

### 01 · Primeros pasos con Python

| Tema | Dónde verlo |
| :--- | :--- |
| Variables, tipos, constantes por convención | `gestor/reglas.py` (`SKINS`, `_MEDALLAS`), `juego/modelo.py` (`GRAVEDAD`, `ANCHO`) |
| Operadores y expresiones | `reglas.py` (`//`, `*`), `modelos.py` (`+=`), `reportes.py` (`/`) |
| Conversiones | `validadores.validar_entero` (`int`), `juego/modelo.py` (`float`, `int`, `round`) |
| `input()`, `print()`, f-strings | `interfaz.pedir`, `aplicacion.opcion_jugar` |

### 02 · Decisiones, ciclos y colecciones

| Tema | Dónde verlo |
| :--- | :--- |
| Comparaciones y operadores lógicos (`and`, `or`, `not`) | `reglas.categoria_para` |
| `if` / `elif` / `else` | `reglas.categoria_para`, `controlador.accion_para`, `aplicacion.elegir_jugador` |
| `for` y `while` | `reglas.medalla_para`; bucles del menú y de `controlador._partida` |
| Listas, tuplas, diccionarios | `_MEDALLAS` (lista de tuplas), `SKINS`, `Jugador.skins` (tupla) |
| Conjuntos | `repositorio.verificar_integridad`, `reportes.jugadores_sin_partidas` |
| Estructuras anidadas | el JSON (diccionario con listas de diccionarios), `reportes.resumen_por_dificultad` |
| Comprensiones (lista, diccionario, conjunto) | `almacenamiento.cargar`, `reportes.resumen_por_dificultad`, `repositorio.verificar_integridad` |

### 03 · Funciones, módulos y programación orientada a objetos

| Tema | Dónde verlo |
| :--- | :--- |
| Funciones, parámetros, argumentos y retorno | `reglas.py`, `validadores.py`, `reportes.ranking` (valor por defecto) |
| Alcance de variables (`global`, local) | `interfaz._contar_accion` y `_acciones_en_sesion` |
| Módulos e importaciones | paquetes `gestor` y `juego` |
| Clases, objetos, `__init__`, `self` | `Jugador`, `Repositorio`, `Servicio`, `Juego`, `Pajaro` |
| Propiedades (`@property`, `setter`) | `Jugador.monedas` (valida), `Jugador.nivel` (calculada), `Servicio.repo` |
| Encapsulamiento | `Jugador._monedas`, `Repositorio._jugadores` con vistas de solo lectura |
| Colaboración entre clases | `Servicio` ↔ `Repositorio` ↔ `Jugador`; `Juego` ↔ `Pajaro` / `Tuberia` |

### 04 · Excepciones, archivos, persistencia y POO

| Tema | Dónde verlo |
| :--- | :--- |
| Validaciones y `raise` | `validadores.py`, `Jugador.monedas` (setter) |
| `try` / `except` / `else` / `finally` | `almacenamiento.cargar` (`else`), `almacenamiento.guardar` (`finally`), `bitacora.registrar` |
| Archivos de texto | `bitacora.py` (modo `"a"`), `ExportadorTXT` |
| `pathlib` | `config.py`, `almacenamiento.py`, `bitacora.py`, `exportador.py` |
| Persistencia JSON | `almacenamiento.py` (escritura atómica y respaldo `.corrupto`) |
| Exportación CSV | `ExportadorCSV` (UTF-8 con BOM) |
| Herencia | `GestorError` y sus hijas; `Facil / Normal / Dificil`; `Obstaculo → Tuberia → TuberiaMovil`; `ExportadorCSV / TXT` |
| Sobrescritura | `hueco()` en cada dificultad, `Tuberia.bloquea`, `TuberiaMovil.actualizar` (con `super()`), `Jugador.__str__` |
| Polimorfismo | `interfaz.op_exportar` (misma llamada, dos formatos), `Juego.tick`, `reglas.monedas_para` |
| Composición | `Servicio` tiene un `Repositorio` y una `Bitacora`; `Juego` tiene un `Pajaro` y obstáculos |

---

## Solución de problemas

| Mensaje o síntoma | Causa | Solución |
| :--- | :--- | :--- |
| «Falta el módulo curses» | Windows sin `windows-curses` | `pip install -r requirements.txt` |
| «La terminal es muy pequeña» | Ventana menor a 48 × 24 | Agrandar la ventana o reducir el tamaño de letra |
| Se ven cuadros o `?` en el juego | La terminal no muestra Unicode | Usar `FLAPPY_ASCII=1` |
| `ModuleNotFoundError: gestor` | Se ejecutó desde otra carpeta | Ejecutar desde la carpeta raíz `flappy_gestor/` |
| Aviso «Archivo dañado» al iniciar | `flappy.json` se editó mal o se cortó | Revisar la copia `data/flappy.json.corrupto` antes de responder «s» |
