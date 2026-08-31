# Exploración del motor de voz (TTS) y decisión final

Este documento resume una sesión de trabajo dedicada por completo a intentar
mejorar la voz de BMO — buscando algo más natural, en castellano, e
idealmente clonando la voz de una persona real — y por qué, al final, nos
quedamos con la configuración original (Piper, voz inglesa `en_GB-semaine-medium`).

No es una historia de fracaso: cada motor probado enseñó algo útil, y queda
documentado por si en el futuro alguien quiere retomarlo con más tiempo,
mejor hardware (GPU) o mejor conexión a internet.

## Motivación de partida

La petición original era: voz en español de España, con un timbre lo más
parecido posible al personaje de BMO (juguetón, no un adulto leyendo serio),
idealmente clonando la voz de una persona conocida que dio su consentimiento
explícito para ello.

Las 5 voces oficiales de Piper en `es_ES` (`davefx`, `sharvard`, `carlfm`,
`mls_10246`, `mls_9972`) se probaron primero y se descartaron por sonar
"muy malas" / poco naturales para lo que se buscaba — lo que arrancó la
búsqueda de alternativas.

## Motores probados

### 1. XTTS-v2 (Coqui / idiap fork `coqui-tts`)

- Clonación zero-shot a partir de un audio de referencia corto.
- Instalación: entorno Python aparte, requirió fijar versiones concretas de
  `torch`/`torchaudio` (2.4.1 CPU) porque las últimas versiones rompían la
  carga de audio (dependencia `torchcodec` esperando librerías CUDA
  inexistentes en esta máquina, sin GPU).
- Resultado: el acento salió **latino**, no castellano (XTTS-v2 solo tiene
  un token de idioma "es" genérico, sin distinguir variante regional), y con
  audio de referencia corto/comprimido (notas de voz de WhatsApp) el
  resultado sonaba artificial e inquietante ("da miedo").
- Conclusión: descartado por acento y calidad con este tipo de referencia.

### 2. MeloTTS (MyShell)

- Motor más ligero, generación muy rápida en CPU (~4 segundos).
- Instalación con bastantes fricciones: dependencia japonesa (`fugashi`/
  MeCab) obligatoria aunque no se usara japonés, requirió descargar un
  diccionario de 526MB solo para poder importar el paquete; conflictos de
  versión de `transformers`/`torchaudio` similares a XTTS.
- Solo trae **una voz** en español, sin elección de género/tono.
- Problemas de calidad encontrados:
  - "BMO" se pronunciaba mal ("mmo" en vez de "bimo") — se solucionó
    escribiéndole "Bimo" directamente en el texto (truco de sustitución
    fonética, no requiere tocar el modelo).
  - Palabras compuestas poco comunes ("videojuego") salían partidas en dos
    ("video - juego") porque su fonemizador usa un tokenizador BERT que
    divide palabras no reconocidas como si fueran dos palabras sueltas —
    esto sí es una limitación estructural del modelo, no arreglable con
    trucos de texto.
- Conclusión: rápido pero con techo de calidad bajo para este uso.

### 3. Chatterbox Multilingual (Resemble AI) — el motor que más se investigó

- Modelo de ~500M parámetros, clonación zero-shot, con licencia MIT.
- **Bug de silencio con el modelo general**: usando `cfg_weight=0.5`
  (valor por defecto) con frases largas o con signos de interrogación, el
  modelo no emitía correctamente el token de "fin de frase" y generaba
  hasta el tope de tokens configurado — resultado: ~1.5s de voz real
  seguidos de ~38 segundos de silencio digital puro. **Solución encontrada:
  `cfg_weight=0.0`** (recomendación que además viene en la documentación
  oficial del proyecto para estos casos).
- Con esa combinación (audio de referencia + `temperature=0.3` +
  `cfg_weight=0.0`) el resultado sonaba bien, y fue la base para construir
  una app web local (`tts_hub/`, con Gradio) para experimentar sin usar la
  terminal — con presets, generación en lote, e historial de la sesión.
- **Checkpoint específico `Chatterbox-Multilingual-es-es`** (para acento de
  España): existe en Hugging Face, pero:
  - No se carga con las clases normales del paquete (`ChatterboxMultilingualTTS`) —
    solo lo carga correctamente el código interno específico del Space de
    demo oficial (`ChatterboxTTS` de `tts.py`, con una configuración
    concreta: `strict=False` al cargar el decoder de audio, archivos
    `t3_es_es.safetensors` + `s3gen_v3.pt`).
  - Una vez cargado con ese código exacto, tenía el mismo bug de silencio
    que el modelo general — y la misma solución (`cfg_weight=0.0`) lo
    arregló también aquí.
  - Con eso funcionando, el resultado se probó y se comparó, pero al final
    no convenció lo suficiente frente a las alternativas.
- **Problema de fondo, no resuelto**: Chatterbox es un modelo pesado
  (arquitectura tipo GPT + vocoder neuronal) pensado para GPU. En este
  portátil (16 núcleos) tardaba entre 10 y 40+ segundos en generar una
  frase corta. La Raspberry Pi 5 tiene solo 4 núcleos ARM, bastante más
  lentos — es muy probable que ahí tardara 1-3+ minutos por frase, lo cual
  rompe la experiencia de un asistente conversacional en tiempo real.
- Se probó también **Chatterbox-Nano/Turbo** (variante distilada, más
  rápida) pero es **solo inglés** — su clase (`ChatterboxTurboTTS`) ni
  siquiera tiene parámetro de idioma, así que quedó descartada de raíz para
  este proyecto.

### 4. Pocket TTS (Kyutai)

- Modelo mucho más pequeño (100M parámetros), pensado explícitamente para
  CPU/dispositivos con pocos recursos — el candidato más prometedor para
  encajar en la Raspberry Pi.
- Velocidad real medida: generación de una frase corta en **0.6 segundos**
  (frente a los 10-40s+ de Chatterbox) — justo lo que se buscaba.
- Bug de corte encontrado y resuelto: por defecto no recorta el audio de
  referencia (`truncate=False`); con nuestro audio de referencia de 57
  segundos sin recortar, generaba frases carentes de sentido de menos de
  medio segundo. Con `truncate=True` (recorta a 30s de forma inteligente,
  no un corte manual a lo bruto) el resultado salió con la duración
  correcta.
- Con el modelo pequeño por defecto (`language="spanish"`, que ni siquiera
  es una opción oficial válida del paquete) la voz clonada sonaba muy
  robótica, cortada y con pronunciación rara.
- Existe una variante de mayor calidad, `spanish_24l` (24 capas), pero sus
  pesos con clonación de voz están en un repositorio de Hugging Face con
  acceso restringido ("gated"). Tras aceptar los términos y autenticarse
  con un token, la descarga de esos pesos concretos seguía fallando — el
  propio código de la librería traga el error real (con un `except
  Exception` genérico) y cae de forma silenciosa a una versión sin
  clonación, así que no fue posible diagnosticar la causa exacta sin acceso
  al backend de Hugging Face/Kyutai. Después de una descarga fallida de 17
  minutos (~672MB) con conexión inestable, se decidió no seguir insistiendo
  por aquí.

## Lecciones técnicas generales (aplicables a cualquier motor futuro)

- **Cada motor pesado necesita su propio entorno virtual** — intentar
  compartir uno solo entre XTTS/MeloTTS/Chatterbox/Pocket TTS provocó
  conflictos constantes de versión de `torch`, `torchaudio` y
  `transformers`.
- **El espacio en disco es el cuello de botella real** en este portátil:
  cada modelo pesa entre 0.5 y 3GB, y se llegó a estar por debajo de 5GB
  libres varias veces. Limpiar la caché de pip (`pip cache purge`) y los
  entornos/modelos ya no usados fue necesario repetidamente.
- **`cfg_weight` / parámetros de "guía"**: en más de un motor, un valor por
  defecto demasiado alto en este tipo de parámetro causaba generaciones
  rotas (silencio, cortes) con frases largas o con signos de interrogación
  — bajarlo a 0 fue la solución en los casos que se pudieron arreglar.
- **Los repos "gated" de Hugging Face no dan acceso automático**: aceptar
  los términos en la web no siempre basta ni es inmediato; a veces requiere
  aprobación manual por parte del equipo que publica el modelo.
- **Nunca pegar tokens de acceso directamente en comandos de terminal**:
  el clasificador de seguridad de Claude Code bloqueó varios intentos por
  esta razón — la forma correcta es guardarlo en un archivo local y
  leerlo desde el script.

## Decisión final

Se descarta, por ahora, cualquier motor de clonación de voz para el uso
final en la Raspberry Pi, por la combinación de: calidad insuficiente
(MeloTTS, Pocket TTS con el modelo pequeño), acento incorrecto (XTTS-v2),
o velocidad inviable para un dispositivo de 4 núcleos ARM (Chatterbox).

**BMO se queda con la configuración original: Piper, voz inglesa
`en_GB-semaine-medium`.** Se confirmó funcionando de principio a fin dentro
de `agent.py` (palabra de activación → escucha → transcripción → LLM →
voz), en varios turnos de conversación seguidos, sin errores.

La voz española de Piper (`es_ES-davefx-medium`) se dejó descargada dentro
de `piper/` por si se quiere retomar en el futuro, pero **no está activada**
— `config.json` sigue apuntando a la voz inglesa original.

## Qué queda disponible para retomar esto más adelante

- `documentation/bmoaudios/` contiene todas las muestras de audio generadas
  durante esta exploración (XTTS, MeloTTS, Chatterbox en varias
  configuraciones, Pocket TTS), útiles para comparar si se retoma el tema.
- La app web local (`tts_hub/`) que se construyó para Chatterbox, junto con
  los entornos virtuales de cada motor, se eliminaron al final de la
  sesión para liberar espacio en disco — habría que reinstalarlos desde
  cero si se retoma esa vía.
- El hallazgo del `cfg_weight=0` y el `truncate=True` son reutilizables
  directamente si se retoma Chatterbox o Pocket TTS en el futuro.
