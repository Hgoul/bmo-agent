# Qué Falta / Qué Está Roto

Ejecutar `./setup.sh` y luego `python agent.py` **no** va a producir todavía
un asistente funcional. A continuación está todo lo que se interpone,
ordenado más o menos por cuánto bloquea una primera ejecución. Los puntos
1-3 son bloqueantes totales; del 4 al 11 son cosas que se comportarán mal,
no harán nada en silencio, o necesitan atención antes de meter esto en un
BMO físico.

## 1. whisper.cpp nunca se instala (bloqueante total)

`agent.py` invoca por subprocess:

```
./whisper.cpp/build/bin/whisper-cli -m ./whisper.cpp/models/ggml-base.en.bin ...
```

Ni `whisper.cpp/` ni ningún modelo `.bin` existen en este repo, y
`setup.sh` nunca los clona, compila ni descarga. Sin esto, cada grabación
se transcribe como una cadena vacía (`transcribe_audio` captura la
excepción y devuelve `""`), así que `user_text` está siempre vacío y el bot
nunca llega a escucharte de verdad — se quedará en
`"Transcription empty."` para siempre.

**Este es, con diferencia, el hueco más grande.** Ver
[03-installation-checklist.md](03-installation-checklist.md) para los pasos
de compilación manual, y [04-modernization-ideas.md](04-modernization-ideas.md)
para una alternativa con faster-whisper que evita por completo la
compilación en C++.

## 2. El README, setup.sh y config.json no coinciden en el modelo de texto

- Las instrucciones de instalación manual del `README.md` dicen:
  `ollama pull gemma:2b`
- `setup.sh` en realidad descarga: `ollama pull gemma3:1b`
- `config.json` / `DEFAULT_CONFIG` en `agent.py` usan por defecto:
  `gemma3:1b`

Si sigues el README al pie de la letra en vez de ejecutar `setup.sh`,
descargarás un modelo que Ollama nunca va a necesitar, y el agente fallará
en el primer chat con un error de Ollama de "modelo no encontrado".
**`gemma3:1b` es el que realmente está conectado en el código — trata la
línea `gemma:2b` del README como desactualizada.**

## 3. Discrepancia en el nombre de archivo de la voz BMO personalizada

`setup.sh` descarga la voz personalizada como:

```
voices/bmo-custom.onnx
voices/bmo-custom.onnx.json
```

pero la configuración de ejemplo del README te dice que pongas:

```json
"voice_model": "voices/bmo.onnx"
```

Si apuntas `config.json` a un archivo que no existe, Piper falla en
silencio — `speak()` captura la excepción y solo escribe
`"Audio Error: ..."` en la consola, así que desde la interfaz gráfica
parece que el bot está hablando (el estado cambia a `SPEAKING`, la boca se
anima) pero no sale ningún sonido. O renombras el archivo descargado a
`bmo.onnx`/`bmo.onnx.json`, o corriges `config.json` para que apunte a
`voices/bmo-custom.onnx` — elige uno de los dos y haz que coincidan.

## 4. La carpeta `error_sounds` se crea pero nunca se usa

`error_sounds_dir = "sounds/error_sounds"` está definida al principio de
`agent.py` y la carpeta la crea `setup.sh`, pero ningún camino del código
llama nunca a `get_random_sound(error_sounds_dir)`. El estado `ERROR` de
la cara tiene fotogramas de animación pero ningún sonido asociado. No es
bloqueante, solo una funcionalidad sin terminar — merece la pena o bien
conectar un sonido de error en `set_state` cuando
`state == BotStates.ERROR`, o bien eliminar la carpeta vacía.

## 5. No hay comprobaciones previas de cámara ni micrófono

No existe ninguna comprobación al arrancar que diga "cámara no encontrada"
o "no se detecta dispositivo de entrada" — solo te enteras cuando
`capture_image()` o `record_voice_*()` lanzan una excepción que se captura
y se registra en una consola que quizá no estés mirando una vez que esto
sea un BMO de plástico sellado sin monitor conectado. Antes del montaje
final, merece la pena añadir:

- Cámara habilitada vía `raspi-config` (o `camera_auto_detect=1` en
  `/boot/firmware/config.txt`) y conectada físicamente — verificar con
  `rpicam-hello --list-cameras`.
- Micrófono detectado — verificar con `arecord -l` / `python -c "import
  sounddevice as sd; print(sd.query_devices())"`.

## 6. La palabra de activación es "Hey Jarvis", no "BMO"

`setup.sh` descarga el modelo estándar de openWakeWord `hey_jarvis_v0.1.onnx`
como `wakeword.onnx`. Entrenar un modelo personalizado de "Hey BMO" (o la
frase que quieras) es un paso manual aparte usando el notebook de
entrenamiento de openWakeWord — el README lo menciona pero `setup.sh` no lo
automatiza. Hasta que eso no se haga, el BMO físico responderá a
"Hey Jarvis".

## 7. Todavía no existe reconocimiento de voz/hablante

Merece la pena señalarlo explícitamente ya que "reconoce voces" es uno de
los objetivos que mencionaste. Hoy en día el pipeline tiene:

- **Detección de palabra de activación** (openWakeWord) — detecta una
  *frase*, no a una persona.
- **Voz a texto** (whisper.cpp) — transcribe *qué* se dijo.

Ninguna de las dos identifica *quién* está hablando. Actualmente no hay
ningún paso de embeddings de hablante / registro (enrollment) en ningún
sitio de `agent.py`. Si quieres que BMO reconozca las voces de personas
concretas (por ejemplo, saludarte por tu nombre, o responder solo a
familiares registrados), es un componente nuevo que hay que añadir — ver
[04-modernization-ideas.md](04-modernization-ideas.md) para un boceto
concreto.

## 8. El lanzador `.desktop` tiene rutas fijas (hardcoded)

`be-more-agent.desktop` apunta a `/home/pi/be-more-agent/...` en `Exec`,
`Path` e `Icon`. Solo funcionará sin modificar si la cuenta de usuario de
la Pi es literalmente `pi` y el repo está clonado exactamente en esa ruta.
Hay que editarlo en cada despliegue (o sustituirlo — ver punto 9).

## 9. No hay servicio systemd para un despliegue headless/kiosco

La entrada `.desktop` asume una sesión de escritorio con un lanzador de
aplicaciones y una persona haciendo clic en un icono. Un BMO sellado
dentro de una carcasa con pantalla pero sin teclado/ratón normalmente
querría una unidad `systemd` que ejecute `start_agent.sh` automáticamente
al arrancar y lo reinicie si falla. Ver la checklist de instalación para un
archivo de unidad de ejemplo.

## 10. Las dependencias no tienen versiones fijadas

`requirements.txt` no fija ninguna versión. Por ahora está bien, pero dos
de estos paquetes (`onnxruntime` y la dependencia opcional
`tflite-runtime` de openWakeWord) tienen un historial de romper las builds
de wheels para ARM/Pi entre versiones — merece la pena fijar versiones que
funcionen en cuanto tengas un setup que ande bien, para que un
`pip install -r requirements.txt` dentro de seis meses no rompa de repente
la build en la Pi.

## 11. `duckduckgo_search` está obsoleto (todavía no roto, pero con los días contados)

El import (`from duckduckgo_search import DDGS`) todavía funciona hoy, pero
el paquete ha sido renombrado a `ddgs` por el mismo mantenedor, y
`agent.py` suprime explícitamente el `RuntimeWarning` que normalmente te
avisaría de esto (`warnings.filterwarnings(... module="duckduckgo_search")`).
Seguirá funcionando un tiempo, pero tiene los días contados. Ver
[04-modernization-ideas.md](04-modernization-ideas.md).
