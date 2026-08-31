# Estado Actual: Puesta en Marcha en Ubuntu (Dev)

Este documento resume, desde cero, todo lo que se ha hecho sobre el
proyecto BMO en **esta fase de desarrollo en un portátil con Ubuntu**
(antes de pasar a la Raspberry Pi 5 física): qué cambió en el código
respecto al original, qué se instaló en el sistema y por qué, y un
problema de hardware (micrófono) que apareció y se resolvió por el
camino.

Los documentos [01](01-code-walkthrough.md) a
[04](04-modernization-ideas.md) describen el código **tal como se
recibió originalmente** y lo que le faltaba. Este documento describe
**lo que se hizo a partir de esa base** para tener un `agent.py`
funcionando de verdad, primero en un entorno de escritorio Ubuntu
(x86_64) como banco de pruebas, antes del despliegue final en la Pi 5
(ARM64).

## 1. Por qué Ubuntu primero y no directo en la Pi

Desarrollar y depurar directamente en la Raspberry Pi es más lento
(compilaciones, menos RAM/CPU, sin teclado/pantalla cómodos muchas
veces) y complica separar "esto falla por el código" de "esto falla
por ser hardware ARM limitado". La estrategia ha sido: dejar el
pipeline completo (wake word → grabar → transcribir → LLM → hablar)
funcionando de forma fiable en un portátil x86_64 con Ubuntu, y solo
después migrar a la Pi 5, donde en teoría solo quedará por resolver lo
específico de esa placa (cámara `rpicam-still`, arquitectura ARM,
recursos más limitados).

## 2. Cambios de código respecto al original

El repo no tiene historial de git, así que esta tabla se basa en
comparar el `agent.py` actual con lo que describían
[01-code-walkthrough.md](01-code-walkthrough.md) y
[02-whats-missing.md](02-whats-missing.md) sobre el código *tal como
se recibió*.

| Punto de `02-whats-missing.md` | Antes | Ahora | Dónde en `agent.py` |
|---|---|---|---|
| #1 STT: whisper.cpp nunca se instala | `subprocess.run(["./whisper.cpp/build/bin/whisper-cli", ...])` — binario/modelo inexistentes, transcripción siempre vacía | `faster_whisper.WhisperModel("base.en", device="cpu", compute_type="int8")` cargado en memoria una vez al arrancar; `transcribe_audio()` lo llama directamente, sin subprocess | `agent.py:264` (carga), `agent.py:783-795` (uso) |
| #4 `error_sounds` se crea pero no se usa | Carpeta creada por `setup.sh`, ningún código la reproducía | `set_state()` lanza un sonido aleatorio de esa carpeta en un hilo aparte cada vez que el estado pasa a `ERROR` | `agent.py:411-414` |
| #11 `duckduckgo_search` obsoleto | `from duckduckgo_search import DDGS`, con el aviso de obsolescencia silenciado a propósito | `from ddgs import DDGS` (el paquete renombrado, mismo mantenedor, misma API) | `agent.py:44` |
| #3 (parcial) nombre de la voz Piper no coincide | El README apuntaba a `voices/bmo.onnx`, `setup.sh` descargaba `bmo-custom.onnx` | `DEFAULT_CONFIG["voice_model"]` y `config.json` apuntan ambos a `piper/en_GB-semaine-medium.onnx` (la voz por defecto que sí se descarga) — **la voz personalizada de BMO todavía no se ha entrenado/instalado**, esto solo resuelve la ruta rota, no añade la voz final | `agent.py:63`, `config.json` |

Puntos que **siguen igual que en el original** (documentados pero no
tocados todavía, porque son específicos de la Pi o no bloquean las
pruebas en Ubuntu):

- `capture_image()` sigue llamando a `rpicam-still` directamente — en
  Ubuntu esto falla (no existe el binario), lo cual está bien porque
  no hay cámara conectada al portátil. Ver la tarea pendiente #7 más
  abajo.
- La palabra de activación sigue siendo la de `hey_jarvis_v0.1.onnx`
  ("Hey Jarvis"), no una "Hey BMO" entrenada a medida (punto #6 de
  `02-whats-missing.md`).
- `requirements.txt` sigue sin versiones fijadas (punto #10) — ver la
  sección 4.6 sobre qué versiones se han instalado *de hecho* y por
  qué no se han fijado todavía.
- El lanzador `.desktop` y el archivo de unidad `systemd` (puntos #8 y
  #9) siguen pendientes — son cosas de despliegue en la Pi física, no
  aplican a probar en un portátil.

Cambios en `config.json` que no vienen de `02-whats-missing.md` sino
de las pruebas de esta fase:

- `"input_sample_rate": 44100` — antes era `null` (autodetección).
  Se fijó explícitamente tras confirmar que 44100 Hz es el sample rate
  que el micrófono de este portátil (`ALC256 Analog`) acepta sin
  problemas.
- `"camera_rotation": 180` — ya estaba así en el `config.json` de este
  repo (el valor por defecto en el código es `0`); probablemente
  pensado para cómo quedará montada la cámara dentro de la carcasa
  física de BMO, pero no se ha podido verificar aún porque la cámara
  todavía no está conectada (tarea #7).

## 3. Todo lo que se ha instalado en el sistema, y por qué

Sistema: **Ubuntu 24.04.4 LTS**, Python 3.12.3, arquitectura x86_64.

### 3.1 Paquetes de sistema (`apt`)

Los mismos que pide [03-installation-checklist.md](03-installation-checklist.md)
para la Pi (Ubuntu y Raspberry Pi OS son ambos derivados de Debian, así
que los mismos paquetes `apt` sirven en los dos):

```
python3-tk python3-dev libasound2-dev portaudio19-dev \
liblapack-dev libblas-dev cmake build-essential espeak-ng git
```

`libasound2-dev` y `portaudio19-dev` son los que hacen falta para que
`sounddevice` compile/enlace correctamente contra ALSA — sin ellos,
`pip install sounddevice` instala un wheel genérico que luego falla
al abrir el micrófono real.

### 3.2 Ollama (motor de los LLMs locales)

Instalado con el script oficial:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Versión instalada: **0.32.5** (la última disponible al momento de
instalar; Ollama no tiene un concepto de "versión estable fijada" que
tenga sentido fijar a mano — el instalador oficial siempre trae la
última). Se eligió Ollama (en vez de, por ejemplo, montar
`llama.cpp` a pelo) porque:

- Ya era la dependencia asumida por el código original (`import
  ollama`, `ollama.chat(...)` en `agent.py`) — no es una decisión que
  hayamos tomado nosotros desde cero, sino la que ya traía el
  proyecto.
- Gestiona la descarga, cuantización y carga/descarga de modelos en
  RAM automáticamente (`keep_alive`), lo cual encaja con el patrón que
  ya usa `agent.py` para no dejar el modelo ocupando memoria tras
  cerrar la app.

Modelos descargados (`ollama pull ...`), ambos ya eran los valores por
defecto en `DEFAULT_CONFIG` del código original, no algo que hayamos
cambiado:

| Modelo | Tamaño en disco | Uso |
|---|---|---|
| `gemma3:1b` | 815 MB | `text_model` — chat de texto normal |
| `moondream` | 1.7 GB | `vision_model` — se usa cuando hay una foto adjunta |

Por qué estos y no otros (razonamiento ya recogido en
[04-modernization-ideas.md](04-modernization-ideas.md) §5, que
aplicamos también aquí): son modelos pequeños pensados para correr
bien en hardware modesto (la Pi 5 de 8GB es el objetivo final), y
`gemma3:1b` en concreto rinde a un ritmo cómodamente conversacional
incluso en ese hardware limitado — no había motivo para probar algo
más grande solo para el portátil de desarrollo, ya que el cuello de
botella real es la Pi, no este equipo.

### 3.3 faster-whisper (voz a texto)

En vez de compilar `whisper.cpp` (lo que pedía el código original, ver
sección 2 de este documento), se optó directamente por
`faster-whisper`, tal como recomendaba
[04-modernization-ideas.md](04-modernization-ideas.md) §2:

- Se instala con `pip install faster-whisper` — sin `cmake`, sin
  compilar C++, un punto menos de fallo en la instalación.
- Usa el modelo **`base.en`** (`WHISPER_MODEL_SIZE` en
  `agent.py:55`), en CPU, con `compute_type="int8"` (cuantizado a
  8 bits) — el mismo equilibrio velocidad/precisión que ya
  recomendaba la documentación original, ahora aplicado a
  faster-whisper en vez de a whisper.cpp. `int8` reduce uso de RAM y
  acelera la inferencia en CPU, a cambio de una pérdida de precisión
  mínima, algo que tiene sentido tanto en este portátil como
  (sobre todo) en la Pi 5.

Versiones exactas instaladas (`pip freeze`):

```
faster-whisper==1.2.1
ctranslate2==4.8.1        # motor de inferencia que usa faster-whisper por debajo
onnxruntime==1.28.0
```

### 3.4 Piper TTS (texto a voz) — build x86_64

`setup.sh` solo descarga el binario de Piper cuando detecta
`aarch64` (la Pi). Para poder probar en este portátil x86_64, se
instaló manualmente el binario equivalente de la **misma versión**
que ya usa el proyecto (`2023.11.14-2`, la última release del
repositorio original `rhasspy/piper` antes de que se archivara en
octubre de 2025 — ver el razonamiento completo de licencias en
[04-modernization-ideas.md](04-modernization-ideas.md) §3), pero
compilado para `x86_64` en vez de `aarch64`. Confirmado con `file
piper/piper`: ELF de 64 bits x86-64, no de ARM.

Se mantuvo la misma versión (y no el fork activo `piper1-gpl`) por el
mismo motivo que ya explica el documento de modernización: cambiar de
fork implicaría pasar de licencia MIT a GPL-3.0, y no hay ningún bug o
funcionalidad concreta que lo justifique todavía.

Voz instalada: `en_GB-semaine-medium.onnx` (la voz por defecto que
`setup.sh` ya descargaba como *fallback*) — la voz personalizada de
BMO (`bmo-custom.onnx`) todavía no se ha entrenado ni descargado, así
que por ahora BMO habla con este acento británico neutro por defecto.

### 3.5 openWakeWord (palabra de activación)

Ya estaba en el código original; en esta fase se verificó que detecta
correctamente de forma standalone en este portátil (`test_wakeword.py`,
creado durante las pruebas, es un script mínimo que escucha por el
micro 15s y muestra las puntuaciones de detección en vivo — útil para
depurar el wake word sin tener que levantar la app completa). Sigue
usando el modelo por defecto `hey_jarvis_v0.1.onnx` ("Hey Jarvis"), no
uno de "Hey BMO" entrenado a medida.

Versión instalada: `openwakeword==0.4.0`, backend ONNX (no
`tflite-runtime`) — siguiendo la recomendación de
[04-modernization-ideas.md](04-modernization-ideas.md) §4 de preferir
ONNX explícitamente por su historial de wheels rotas de TFLite en ARM
(aquí en x86_64 no aplicaría ese problema concreto, pero se mantiene
la misma configuración que se usará luego en la Pi, para no tener dos
configuraciones distintas entre entornos).

### 3.6 Entorno Python (venv + `pip`)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Importante sobre las versiones:** `requirements.txt` no fija ninguna
versión concreta (esto ya estaba señalado como pendiente en
[02-whats-missing.md](02-whats-missing.md) punto #10, y sigue sin
resolverse). Esto significa que las versiones instaladas abajo **no
son una elección deliberada nuestra entre varias opciones** — son,
simplemente, las últimas versiones compatibles con Python 3.12
disponibles en el momento de instalar. Se listan aquí a modo de
registro de qué hay instalado ahora mismo, no como una decisión
razonada versión por versión:

```
sounddevice==0.5.5
numpy==2.5.1
scipy==1.18.0
openwakeword==0.4.0
onnxruntime==1.28.0
ollama==0.6.2          # cliente Python, no el binario de Ollama
ddgs==9.14.4
Pillow==12.3.0
faster-whisper==1.2.1
ctranslate2==4.8.1
```

Dado que ya hay una base que funciona de forma fiable en este entorno,
tiene sentido fijar estas versiones exactas en `requirements.txt`
pronto (tal como recomienda el punto #10 de `02-whats-missing.md`),
para que una instalación futura en la Pi 5 no se lleve versiones más
nuevas y potencialmente incompatibles sin que nos demos cuenta.

## 4. El problema del micrófono (resuelto hoy)

Durante la primera prueba end-to-end completa, el pipeline funcionaba
(wake word → grabar → whisper → Ollama → Piper), pero la transcripción
salía vacía o sin sentido la mayoría de las veces. Inspeccionando
directamente el `input.wav` que graba `agent.py` en cada turno (en vez
de asumir), se encontró que el audio capturado era **ruido/estática
muy fuerte y constante**, sin la voz reconocible.

**Causa raíz:** en la tarjeta de sonido (`ALC256 Analog`, tarjeta
ALSA 1), dos controles de ganancia de entrada estaban al máximo:

| Control | Valor encontrado | Equivale a |
|---|---|---|
| `Mic Boost Volume` | 3 / 3 (máximo) | +30 dB |
| `Capture Volume` | 63 / 63 (máximo) | +30 dB |

Es decir, ~60 dB de ganancia combinada — suficiente para saturar
cualquier micrófono de portátil con el ruido ambiente normal de una
habitación, produciendo la estática grabada. Esto es un problema de
configuración de hardware/ALSA muy conocido en el chip Realtek ALC256
(común en muchos portátiles), no un fallo del código de `agent.py` ni
de cómo está configurado `sounddevice`.

**Arreglo aplicado**, vía `amixer` sobre la tarjeta 1:

```bash
amixer -c 1 cset numid=8 0    # Mic Boost Volume: 3 -> 0 (sin boost extra)
amixer -c 1 cset numid=6 40   # Capture Volume: 63 -> 40 (de 63 posibles)
sudo alsactl store            # persiste los valores para que sobrevivan a un reinicio
```

Se llegó a `40` iterando: `35` daba cero saturación pero algo bajo de
volumen; `50` volvía a saturar levemente en sílabas fuertes; `40` es
el punto intermedio que quedó con 0.000% de muestras saturadas y
transcripción limpia en las pruebas. Si en el futuro el audio vuelve a
sonar débil o saturado, este es el sitio donde tocar (`amixer -c 1
cget numid=6` para ver el valor actual).

## 5. Estado de las tareas de esta fase

| # | Tarea | Estado |
|---|---|---|
| 1 | Entorno Python (venv) + paquetes de sistema en Ubuntu | ✅ Hecho |
| 2 | Aplicar arreglos rápidos de `02-whats-missing.md` | ✅ Hecho (ver sección 2) |
| 3 | STT: whisper.cpp o faster-whisper en Ubuntu | ✅ Hecho — se eligió faster-whisper |
| 4 | Piper TTS (build x86_64) + arreglar ruta de `voice_model` | ✅ Hecho |
| 5 | openWakeWord detectando la palabra de activación standalone | ✅ Hecho |
| 6 | Ejecutar `agent.py` de punta a punta en Ubuntu (bucle de voz completo) | 🔄 En curso — pipeline funcionando, mic arreglado, pendiente de una confirmación final |
| 7 | Simular/mockear la captura de cámara para pruebas en Ubuntu | ⏳ Pendiente |
| 8 | Migrar a la Raspberry Pi 5 para la integración con el hardware físico | ⏳ Pendiente |

## 6. Próximos pasos

1. Confirmar una ejecución completa y estable de `agent.py` en Ubuntu
   (tarea #6) con la ganancia del micrófono ya corregida.
2. Tarea #7: como `capture_image()` llama directamente a
   `rpicam-still` (que no existe fuera de la Pi), hace falta un
   *stub* para poder probar el flujo de "hacer una foto" en Ubuntu sin
   cámara real — por ejemplo, devolver una imagen de prueba fija en
   vez de lanzar el subprocess cuando `rpicam-still` no esté
   disponible.
3. Fijar versiones en `requirements.txt` (sección 3.6) antes de dar
   por buena esta base, para que el traslado a la Pi 5 sea
   reproducible.
4. Tarea #8: mover todo esto a la Raspberry Pi 5 física, donde faltará
   resolver lo específico de esa placa (cámara vía `rpicam-still`,
   posibles diferencias de ALSA/ganancia de micrófono como la de la
   sección 4 pero en ese hardware, y arquitectura ARM64 en vez de
   x86_64).
