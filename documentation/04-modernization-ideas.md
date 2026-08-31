# Ideas de Modernización

Estos son componentes que ya *funcionan* en el código actual pero que
tienen mejores opciones a mediados de 2026, más una capacidad
(reconocimiento de hablante) que todavía no existe y habría que añadir
desde cero. Nada de esto es necesario para conseguir un primer BMO
funcional — trátalo como un backlog del que ir tirando una vez que la base
descrita en
[03-installation-checklist.md](03-installation-checklist.md) funcione de
forma fiable.

## 1. Búsqueda web: scraping de DuckDuckGo → una API de búsqueda real

**Actual:** `duckduckgo_search.DDGS` (agent.py) hace scraping del frontend
HTML de DuckDuckGo — no es una API oficial. Es gratis y no necesita clave,
lo cual encaja con el mensaje de "sin costes de API" del README, pero es
inherentemente frágil: DDG puede limitar o bloquear tráfico de scraping sin
avisar, y el mantenedor ya ha renombrado el paquete una vez
(`duckduckgo_search` → `ddgs`) precisamente por los cambios constantes del
lado de DDG. `agent.py` actualmente suprime el aviso de obsolescencia que
te avisaría de esto
(`warnings.filterwarnings(..., module="duckduckgo_search")`).

**Opciones, más o menos en orden de esfuerzo:**

- **Arreglo mínimo, sin cambiar el comportamiento:** `pip install ddgs` y
  cambiar el import a `from ddgs import DDGS` — misma API, nombre
  mantenido activamente. Mantiene la propiedad de "sin clave de API".
- **Más rápido y fiable, con una pequeña contrapartida:** una API de
  búsqueda real con capa gratuita — p. ej. Brave Search API. Cambia la
  pureza de "cero claves de API, 100% offline" por SLAs de disponibilidad
  reales y respuestas en JSON en lugar de HTML raspado, lo cual también es
  simplemente más rápido por consulta.
- **Opción nativa para LLMs:** Tavily u otras APIs de "búsqueda pensada
  para agentes" devuelven fragmentos ya resumidos y listos para el LLM,
  lo que permitiría eliminar el actual proceso en dos pasos ("buscar →
  llamada de resumen aparte a Ollama") y fundirlo en uno solo.
- **100% offline, más infraestructura:** autoalojar SearXNG. Mantiene la
  filosofía 100% local del proyecto pero añade un segundo servicio que
  ejecutar en la Pi junto a Ollama — probablemente más carga de RAM/CPU de
  la que compensa en una Pi 5 que ya está corriendo un LLM y un modelo de
  visión.

Dada la identidad "100% local, sin nube" del proyecto, el término medio
pragmático es: renombrar a `ddgs` ahora (coste cero), y solo recurrir a una
API de pago/con clave si el scraping de DDG empieza a fallar de verdad en
la práctica.

## 2. Voz a texto: whisper.cpp → faster-whisper (o quedarse con whisper.cpp)

**Actual:** el código espera un binario `whisper.cpp` compilado + un
modelo `.bin` de ggml (ver punto 3 de la checklist) — y ninguno de los dos
lo instala `setup.sh`, así que esto hay que montarlo desde cero de todas
formas.

Ya que hay que configurarlo sí o sí, merece la pena decidir entre:

- **whisper.cpp** (lo que el código asume actualmente): C/C++, necesita
  `cmake` + un paso de compilación, uso de memoria plano
  independientemente de la duración del audio, algo por detrás de
  faster-whisper en velocidad bruta específicamente en hardware Pi.
- **faster-whisper**: simple `pip install faster-whisper` (usa
  CTranslate2 por debajo), sin compilar nada, y los benchmarks
  generalmente lo muestran por delante de whisper.cpp en la Pi 5 para
  clips cortos/de voz en vivo (que es exactamente este caso de uso —
  comandos de voz cortos, no grabaciones largas). Usa más RAM por sesión
  que el perfil plano de whisper.cpp, pero para audio corto tipo comando
  (esto no es transcribir grabaciones de una hora) eso no supone ningún
  problema en una Pi 5 de 8GB.

Para una instalación desde cero, donde "sin paso de compilación en C++"
también significa "una cosa menos que pueda romperse durante la
instalación", **faster-whisper es la opción por defecto más atractiva**
aquí. Cambiarlo significa sustituir la llamada
`subprocess.run([...])` de `transcribe_audio()` por una llamada a
`WhisperModel(...).transcribe(...)` — un cambio pequeño y contenido, no una
reescritura. `tiny.en` o `base.en` son los tamaños que se mantienen
capaces de tiempo real en la Pi 5 en cualquiera de los dos casos.

## 3. Piper TTS: fijar la última versión MIT, o pasar al fork GPL mantenido

**Nota importante sobre licencias:** el repo original `rhasspy/piper` (del
que `setup.sh` descarga actualmente una release binaria, y del que la
sección de doble licencia del README asume implícitamente que es MIT) fue
**archivado por su propietario en octubre de 2025** y ahora es de solo
lectura. El desarrollo activo se trasladó a `OHF-Voice/piper1-gpl`,
mantenido por la Open Home Foundation — y, de forma crítica,
**ese fork es GPL-3.0, no MIT**.

Esto importa específicamente para este proyecto porque `LICENSE`
actualmente dice que "todo el código fuente está licenciado bajo la
Licencia MIT" — eso es cierto para `agent.py`, pero si migras Piper al
nuevo fork mantenido, estarías distribuyendo un componente GPL-3.0 junto a
él, lo cual tiene implicaciones sobre cómo se puede licenciar/distribuir
el proyecto entero en conjunto.

**Dos caminos razonables:**

- **Quedarse con la release binaria archivada de `rhasspy/piper`** (la que
  `setup.sh` ya fija: `2023.11.14-2`). Está congelada pero funcional,
  licenciada bajo MIT, y la voz BMO personalizada de este proyecto ya se
  afinó (fine-tuned) contra el formato de Piper — no hay ninguna razón de
  compatibilidad para cambiar.
- **Pasar a `piper1-gpl`** solo si necesitas una corrección de bug o
  funcionalidad que haya llegado desde el archivado — y si lo haces,
  actualiza honestamente la sección de licencias de `LICENSE`/`README.md`
  para reflejar la dependencia GPL-3.0.

No hace falta ningún cambio de código en ninguno de los dos casos, salvo
que necesites específicamente algo del nuevo fork — esto es una decisión
de licencias/mantenimiento, no un bloqueo técnico.

## 4. Backend de openWakeWord: preferir ONNX explícitamente sobre TFLite en la Pi

openWakeWord soporta tanto backend de inferencia ONNX como TFLite. En
Linux, TFLite ha sido históricamente el predeterminado, pero
`tflite-runtime` tiene un historial recurrente de wheels ARM rotas o
ausentes específicamente para Raspberry Pi (más recientemente, con
instalaciones fallando por completo a principios de 2026). El ecosistema
en general se está moviendo hacia ONNX precisamente por esto, y pruebas
tempranas en la Pi 5 han mostrado que ONNX usa *menos* CPU que TFLite ahí
también.

**Acción:** al instalar/configurar openWakeWord, selecciona explícitamente
el backend/modelo ONNX en lugar de confiar en el predeterminado de la
plataforma, y si te topas con un fallo de instalación de
`tflite-runtime`, ese es el problema conocido — cambia a ONNX en vez de
depurar la wheel de TFLite.

## 5. Elección de LLMs: las opciones actuales ya son razonables, con margen

`gemma3:1b` (texto) y `moondream` (visión) son opciones sólidas para una
Pi 5 de 8GB — benchmarks recientes muestran a `gemma3:1b` corriendo a
~18-22 tokens/seg en la Pi 5, lo cual es cómodamente conversacional. No
hace falta cambiar nada ahí.

Vale la pena conocerlo, sin que sea necesario cambiar a ello:

- Si `moondream` (por defecto, ~1.8B aprox.) se nota pesado o lento
  corriendo a la vez que todo lo demás, `granite3.2-vision:2b` es una
  alternativa de tamaño comparable que merece la pena probar (A/B).
- Si más adelante quieres un modelo notablemente más grande (p. ej. un
  modelo de texto de 4B, o un modelo de visión mayor) para mejores
  respuestas, el **Raspberry Pi AI HAT+ 2** oficial (disponible desde
  principios de 2026, chip Hailo-10H, ~40 TOPS INT4) es un acelerador de
  hardware conectable que se reporta que da una aceleración de inferencia
  de 5-10x sobre la Pi 5 solo-CPU — merece la pena tenerlo en mente como
  vía de mejora de hardware si BMO alguna vez se nota lento, más que algo
  que planear desde el primer día.

## 6. Capacidad nueva: reconocimiento real de voz/hablante

Este es el único hueco que no es "herramienta vieja, herramienta nueva" —
es una funcionalidad que sencillamente no existe en el código actual (ver
[02-whats-missing.md](02-whats-missing.md) punto 7) y que habría que
añadir.

**Objetivo:** que BMO reconozca *quién* está hablando (no solo *qué* dijo),
por ejemplo para saludar a la gente por su nombre o personalizar
respuestas por cada miembro de la familia registrado.

**Enfoque sugerido — embeddings de voz + similitud coseno, totalmente
offline:**

- **Resemblyzer**: ligero, `pip install resemblyzer`, convierte un clip
  corto de audio en un vector de embedding de longitud fija con pocas
  líneas de código. Buena primera aproximación — rápido, bajo consumo de
  recursos, suficiente para las voces registradas de una familia pequeña.
- **SpeechBrain (ECAPA-TDNN)**: más pesado (PyTorch), notablemente más
  preciso para verificación de hablante si la precisión de Resemblyzer no
  resulta suficiente en la práctica — merece la pena probarlo solo si la
  opción ligera se queda corta, ya que es una dependencia mucho más
  grande para una Pi.

**Boceto de integración** (no requiere reestructurar el pipeline
existente, encaja justo después de que `record_voice_*()` ya produzca un
WAV):

1. **Registro (enrollment, una vez por persona):** grabar unos segundos de
   la voz de cada persona, calcular y guardar su embedding (p. ej. en un
   pequeño `voices_enrolled.json` que mapee nombre → vector de embedding).
2. **En tiempo de ejecución:** después de que
   `record_voice_adaptive()`/`record_voice_ptt()` produzca `input.wav` y
   *antes* (o en paralelo a) enviarlo a whisper para transcribir, calcular
   su embedding y compararlo por similitud coseno contra los perfiles
   registrados. Por encima de cierto umbral de similitud → hablante
   identificado; por debajo → "voz desconocida".
3. **Usar el resultado:** propagar el nombre identificado hasta el mensaje
   de usuario de `chat_and_respond()` (p. ej. anteponiendo
   `[Speaker: Laura]` al texto transcrito, o inyectándolo dinámicamente en
   `system_prompt_extras`) para que el LLM pueda personalizar las
   respuestas, o usarlo para restringir ciertas herramientas/acciones a
   personas concretas.

Esto es aditivo — no toca la detección de palabra de activación ni la
transcripción, solo añade un paso en paralelo que consume el mismo archivo
WAV grabado que ya se produce hoy en día.
